
import asyncio
import json
import logging
import re
from datetime import datetime
from typing import AsyncIterator, List, Tuple

from app.llm_client import call_nemotron
from app.rules import evaluate_batch
from app.schemas import BatchInfo, ReviewReport

logger = logging.getLogger(__name__)

Event = Tuple[str, dict]

FIELDS = (
    "product_type",
    "quantity",
    "prepared_at",
    "storage_temperature",
    "storage_history",
    "packaging_condition",
)

STATUSES = {"confirmed", "inferred", "unknown"}


def _unknown() -> dict:
    return {"value": None, "status": "unknown"}


def _parse_json(raw_output: str) -> dict:
    """Parse JSON, including JSON wrapped in Markdown fences."""
    text = raw_output.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    data = json.loads(text)

    if not isinstance(data, dict):
        raise ValueError("Nemotron must return a JSON object.")

    return data


def _has_explicit_datetime(value: str) -> bool:
    """
    Require an explicit ISO-style date and time.

    Do not silently infer a date for time-only values.
    """
    match = re.fullmatch(
        r"\d{4}-\d{2}-\d{2}[ T]\d{1,2}:\d{2}"
        r"(?::\d{2})?",
        value.strip(),
    )

    if not match:
        return False

    try:
        datetime.fromisoformat(value.strip())
        return True
    except ValueError:
        return False


def _normalize_batch(data: dict) -> dict:
    """
    Normalize model output to the existing BatchInfo schema.

    Plain strings remain inferred, never automatically confirmed.
    """
    normalized = {}

    for field in FIELDS:
        item = data.get(field)

        if isinstance(item, dict):
            value = item.get("value")
            status = item.get("status", "unknown")

            if status not in STATUSES:
                status = "unknown"

        elif isinstance(item, str):
            value = item
            status = "inferred"

        else:
            normalized[field] = _unknown()
            continue

        if not isinstance(value, str) or not value.strip():
            normalized[field] = _unknown()
            continue

        value = value.strip()

        if value.lower() in {
            "unknown",
            "missing",
            "not provided",
            "null",
            "none",
            "n/a",
        }:
            normalized[field] = _unknown()
            continue

        # A preparation time without an explicit date is unresolved.
        if field == "prepared_at" and not _has_explicit_datetime(value):
            normalized[field] = _unknown()
            continue

        if status == "unknown":
            normalized[field] = _unknown()
            continue

        normalized[field] = {
            "value": value,
            "status": status,
        }

    return normalized


def extract_batch(message: str, history=None) -> BatchInfo:
    """Extract structured food-batch evidence with Nemotron."""
    history = history or []

    system_prompt = """
You are FoodRescue Sentinel's food donation evidence extractor.

Your only task is to extract information supplied by the donor.

Use previous USER messages and the latest USER message.
Previous assistant messages are not evidence.

Return ONLY a valid JSON object containing exactly these fields:

product_type
quantity
prepared_at
storage_temperature
storage_history
packaging_condition

Every field MUST contain an object with:
"value": string or null
"status": "confirmed", "inferred", or "unknown"

IMPORTANT RULES:

1. Explicitly stated facts may be marked confirmed.
2. Missing facts must use null and unknown.
3. Never invent quantities, dates, temperatures, or storage details.
4. prepared_at must contain an explicit date AND time.
5. Normalize an explicit preparation date/time to
   YYYY-MM-DD HH:MM.
6. If the donor gives only a time, prepared_at must be unknown.
7. If the latest user message corrects an earlier fact,
   use the latest explicit correction.
8. Never treat previous assistant responses as evidence.
9. Never approve food for distribution.
10. Never invent food-safety thresholds.
11. Return JSON only, without Markdown or explanation.

Example:

{
  "product_type": {
    "value": "cooked biryani",
    "status": "confirmed"
  },
  "quantity": {
    "value": "100 plates",
    "status": "confirmed"
  },
  "prepared_at": {
    "value": "2026-10-30 14:00",
    "status": "confirmed"
  },
  "storage_temperature": {
    "value": "4 degrees Celsius",
    "status": "confirmed"
  },
  "storage_history": {
    "value": "refrigerated",
    "status": "confirmed"
  },
  "packaging_condition": {
    "value": null,
    "status": "unknown"
  }
}
"""

    messages = [
        {"role": "system", "content": system_prompt}
    ]

    for item in history:
        if (
            isinstance(item, dict)
            and item.get("role") == "user"
            and isinstance(item.get("content"), str)
        ):
            messages.append({
                "role": "user",
                "content": item["content"],
            })

    messages.append({
        "role": "user",
        "content": message,
    })

    raw_output = call_nemotron(messages)
    data = _parse_json(raw_output)
    normalized = _normalize_batch(data)

    return BatchInfo.model_validate(normalized)


def _missing_evidence(batch: BatchInfo, results: list) -> list[str]:
    """Collect missing fields and unresolved rule checks."""
    missing = []

    for field in FIELDS:
        tracked = getattr(batch, field)

        if tracked.status != "confirmed" or not tracked.value:
            missing.append(field)

    for result in results:
        if result.passed is not True and result.rule not in missing:
            missing.append(result.rule)

    return missing


def _workflow_status(results: list, missing: list[str]) -> str:
    """Determine a conservative human-review workflow status."""

    # Match the actual time-window rule name in the backend.
    if any(
        result.rule == "time_window_within_limit"
        and result.passed is False
        for result in results
    ):
        return "urgent_review_or_hold"

    if missing or any(result.passed is not True for result in results):
        return "more_information_required"

    return "ready_for_human_review"


async def run_agent(
    case_id: str,
    message: str,
    history: List[dict] = None,
) -> AsyncIterator[Event]:
    """
    FoodRescue Sentinel AI agent.

    Compatible with the existing FastAPI SSE contract.

    Events:
    thought
    tool_call
    tool_result
    rule_check
    question
    final_report
    """
    history = history or []

    yield "thought", {
        "text": "Extracting food-batch evidence with Nemotron."
    }

    extraction_failed = False

    try:
        # The NVIDIA client uses synchronous requests.
        # Run it in a thread to avoid blocking FastAPI.
        batch = await asyncio.to_thread(
            extract_batch,
            message,
            history,
        )

    except Exception:
        logger.exception("Food-batch extraction failed")
        extraction_failed = True

        yield "thought", {
            "text": (
                "AI extraction could not be completed. "
                "The batch requires manual review."
            )
        }

        batch = BatchInfo.model_validate({
            field: _unknown() for field in FIELDS
        })

    yield "tool_call", {
        "tool": "evaluate_batch",
        "input": batch.model_dump(),
    }

    results = evaluate_batch(batch)

    yield "tool_result", {
        "tool": "evaluate_batch",
        "result": "Deterministic rule evaluation completed.",
    }

    for result in results:
        yield "rule_check", {
            "rule": result.rule,
            "passed": result.passed,
            "message": result.message,
        }

    missing = _missing_evidence(batch, results)
    concerns = []
    for result in results:
        if result.passed is False:
            concerns.append({
                "text": result.message,
                "source": result.source or "Internal rule evaluation",
        })

    status = _workflow_status(results, missing)

    if extraction_failed:
        status = "more_information_required"

    if missing:
        if extraction_failed:
            question = (
                "The AI could not extract the batch information. "
                "Please retry or provide the details for manual review."
            )
        else:
            field_names = [
                field.replace("_", " ")
                for field in missing
            ]
            question = (
                "Please provide or clarify: "
                + ", ".join(field_names)
                + "."
            )

        yield "question", {
            "text": question
        }

    if status == "urgent_review_or_hold":
        summary = (
            "The food donation batch requires urgent human review "
            "or a hold because the configured time-window check failed."
        )
        next_step = (
            "Hold the batch and request an authorized human review "
            "before any distribution decision."
        )

    elif extraction_failed:
        summary = (
            "AI extraction was unavailable. The batch information "
            "could not be verified and requires manual review."
        )
        next_step = (
            "Retry extraction or have an authorized reviewer "
            "collect and assess the batch information."
        )

    elif status == "more_information_required":
        summary = (
            "The food donation batch requires additional evidence "
            "before it can proceed to human review."
        )
        next_step = (
            "Collect missing evidence and repeat the deterministic "
            "checks before requesting human review."
        )

    else:
        summary = (
            "The supplied batch evidence passed the configured "
            "checks and is ready for human review. "
            "This is not a food-safety certification."
        )
        next_step = (
            "Submit the batch to an authorized human reviewer "
            "for the final decision."
        )

    report = ReviewReport(
        case_id=case_id,
        summary=summary,
        batch=batch,
        missing_evidence=missing,
        concerns=concerns,
        references=[],
        next_step=next_step,
        workflow_status=status,
    )

    yield "final_report", report.model_dump()
