from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from app.schemas import BatchInfo, WorkflowStatus

# ---------------------------------------------------------------
# SAFE WINDOW LIMITS (hours since preparation).
# EMPTY ON PURPOSE. Real numbers must come from an approved guideline,
# added by the knowledge lead with the source written next to each one.
# Example of the format:  "rice": 2.0,   # Source: <document name, section>
# ---------------------------------------------------------------
SAFE_WINDOW_HOURS: dict = {}

REQUIRED_FIELDS = [
    "product_type",
    "quantity",
    "prepared_at",
    "storage_temperature",
    "storage_history",
    "packaging_condition",
]


@dataclass
class RuleResult:
    rule: str
    passed: Optional[bool]  # True = ok, False = problem, None = could not check
    message: str


def lookup_window(product_type: Optional[str]) -> Optional[float]:
    """Find the configured limit whose keyword appears in the product name."""
    if not product_type:
        return None
    name = product_type.lower()
    for keyword, hours in SAFE_WINDOW_HOURS.items():
        if keyword.lower() in name:
            return hours
    return None


def elapsed_hours(value: str, now: datetime) -> Optional[float]:
    """Hours between the preparation time and now. Accepts '18:00' or a full date-time."""
    try:
        start = datetime.fromisoformat(value.strip())
    except ValueError:
        try:
            t = datetime.strptime(value.strip(), "%H:%M").time()
        except ValueError:
            return None
        start = datetime.combine(now.date(), t)
        if start > now:  # time of day is later than now, so it was yesterday
            start -= timedelta(days=1)
    return max(0.0, (now - start).total_seconds() / 3600)


def check_field(batch: BatchInfo, field: str) -> RuleResult:
    item = getattr(batch, field)
    rule = f"{field}_present"
    if item.status == "unknown" or not item.value:
        return RuleResult(rule, False, f"{field} is missing.")
    if item.status == "inferred":
        return RuleResult(rule, False, f"{field} is only inferred and needs confirmation.")
    return RuleResult(rule, True, f"{field} is confirmed.")


def check_time_window(batch: BatchInfo, now: datetime) -> RuleResult:
    rule = "time_window_within_limit"
    prepared = batch.prepared_at
    if prepared.status == "unknown" or not prepared.value:
        return RuleResult(rule, None, "Preparation time unknown, so elapsed time cannot be computed.")
    hours = elapsed_hours(prepared.value, now)
    if hours is None:
        return RuleResult(rule, None, f"Could not read the preparation time '{prepared.value}'.")
    limit = lookup_window(batch.product_type.value)
    if limit is None:
        return RuleResult(
            rule, None,
            f"{hours:.1f} h since preparation. No approved time limit is configured for this product type.",
        )
    ok = hours <= limit
    return RuleResult(rule, ok, f"{hours:.1f} h since preparation; configured limit is {limit:g} h.")


def evaluate_batch(batch: BatchInfo, now: Optional[datetime] = None) -> List[RuleResult]:
    now = now or datetime.now()
    results = [check_field(batch, f) for f in REQUIRED_FIELDS]
    results.append(check_time_window(batch, now))
    return results


def decide_status(results: List[RuleResult]) -> WorkflowStatus:
    """Workflow status only. This is NOT a safety verdict."""
    for r in results:
        if r.rule == "time_window_within_limit" and r.passed is False:
            return "urgent_review_or_hold"
    if any(r.passed is False for r in results):
        return "more_information_required"
    return "ready_for_human_review"