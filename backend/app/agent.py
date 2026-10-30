import asyncio
from typing import AsyncIterator, List, Tuple

from app.rules import decide_status, evaluate_batch
from app.schemas import BatchInfo, ReviewReport

Event = Tuple[str, dict]


def _unknown() -> dict:
    return {"value": None, "status": "unknown"}


async def run_agent(case_id: str, message: str, history: List[dict]) -> AsyncIterator[Event]:
    """PLACEHOLDER agent. The AI lead replaces the inside of this function.

    Contract: yield (event_name, data_dict) pairs. Allowed event names:
    thought, tool_call, tool_result, rule_check, question, final_report.
    The last event must be final_report, with data shaped like ReviewReport.
    `history` is a list of {"role": "user"|"assistant", "content": str}.
    """
    yield "thought", {"text": "Reading the donor's message."}
    await asyncio.sleep(0.4)

    batch = BatchInfo.model_validate({
        "product_type": {"value": message[:80], "status": "inferred"},
        "quantity": _unknown(),
        "prepared_at": _unknown(),
        "storage_temperature": _unknown(),
        "storage_history": _unknown(),
        "packaging_condition": _unknown(),
    })

    results = evaluate_batch(batch)
    for r in results:
        yield "rule_check", {"rule": r.rule, "passed": r.passed, "message": r.message}
        await asyncio.sleep(0.2)

    missing = [r.rule.replace("_present", "") for r in results if r.passed is False]
    if missing:
        yield "question", {"text": "Please provide: " + ", ".join(missing)}

    report = ReviewReport(
        case_id=case_id,
        summary=f"Placeholder summary for: {message[:80]}",
        batch=batch,
        missing_evidence=missing,
        concerns=[],
        references=[],
        next_step="Collect the missing information, then send to a human reviewer.",
        workflow_status=decide_status(results),
    )
    yield "final_report", report.model_dump()