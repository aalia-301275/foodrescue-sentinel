import csv
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

from app.schemas import BatchInfo, WorkflowStatus

# The knowledge lead fills this file. Every row needs a source.
LIMITS_CSV = Path(__file__).resolve().parent.parent / "data" / "safe_windows.csv"

CSV_COLUMNS = [
    "food_keyword",
    "storage_condition",
    "max_hours",
    "clock_starts",
    "source_document",
    "section",
    "link",
    "quote",
    "date_checked",
]
VALID_CONDITIONS = {"hot", "room", "refrigerated", "any"}

REQUIRED_FIELDS = [
    "product_type",
    "quantity",
    "prepared_at",
    "storage_temperature",
    "storage_history",
    "packaging_condition",
]


@dataclass
class WindowRule:
    keyword: str
    condition: str
    max_hours: float
    clock_starts: str
    source_document: str
    section: str
    link: str
    quote: str
    date_checked: str

    def citation(self) -> str:
        return f"{self.source_document}, {self.section}"


@dataclass
class RuleResult:
    rule: str
    passed: Optional[bool]  # True = ok, False = problem, None = could not check
    message: str
    source: Optional[str] = None
    link: Optional[str] = None


def _row_problem(row: dict) -> Optional[str]:
    if not row["food_keyword"]:
        return "food_keyword is empty"
    if row["storage_condition"].lower() not in VALID_CONDITIONS:
        return "storage_condition must be one of: hot, room, refrigerated, any"
    try:
        hours = float(row["max_hours"])
    except ValueError:
        return "max_hours is not a number"
    if hours <= 0:
        return "max_hours must be above 0"
    for col in ("source_document", "section", "link"):
        if not row[col]:
            return f"{col} is empty (every limit needs a source)"
    return None


def load_limits(path: Path = LIMITS_CSV) -> Tuple[List[WindowRule], List[str]]:
    """Read the limits file. Rows without a complete source are skipped with a warning."""
    limits: List[WindowRule] = []
    warnings: List[str] = []
    if not path.exists():
        return limits, [f"Limits file not found: {path.name}"]
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return limits, [f"{path.name} is empty."]
        reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]
        missing = [c for c in CSV_COLUMNS if c not in reader.fieldnames]
        if missing:
            return limits, [f"{path.name} is missing columns: {', '.join(missing)}"]
        for line_no, raw in enumerate(reader, start=2):
            row = {k: (v or "").strip() for k, v in raw.items() if k}
            if not any(row.values()):
                continue  # blank line
            problem = _row_problem(row)
            if problem:
                warnings.append(f"Row {line_no} skipped: {problem}")
                continue
            limits.append(
                WindowRule(
                    keyword=row["food_keyword"].lower(),
                    condition=row["storage_condition"].lower(),
                    max_hours=float(row["max_hours"]),
                    clock_starts=row["clock_starts"],
                    source_document=row["source_document"],
                    section=row["section"],
                    link=row["link"],
                    quote=row["quote"],
                    date_checked=row["date_checked"],
                )
            )
    return limits, warnings


LIMITS, LIMIT_WARNINGS = load_limits()


def reload_limits():
    """Re-read the CSV without restarting the server."""
    global LIMITS, LIMIT_WARNINGS
    LIMITS, LIMIT_WARNINGS = load_limits()


def detect_condition(batch: BatchInfo) -> Optional[str]:
    """Work out hot / room / refrigerated from CONFIRMED storage text only.
    This is a keyword heuristic. The agent should ask the donor directly."""
    texts = []
    for item in (batch.storage_history, batch.storage_temperature):
        if item.status == "confirmed" and item.value:
            texts.append(item.value.lower())
    text = " ".join(texts)
    if not text:
        return None
    if any(w in text for w in ("refrigerat", "fridge", "chilled", "cold storage", "cold room")):
        return "refrigerated"
    if any(w in text for w in ("hot-held", "hot held", "hot box", "hotbox", "kept hot", "warmer")):
        return "hot"
    if any(w in text for w in ("room temp", "ambient", "outdoor", "outside")):
        return "room"
    return None


def find_limit(
    product_type: Optional[str],
    condition: Optional[str],
    limits: Optional[List[WindowRule]] = None,
) -> Tuple[Optional[WindowRule], str]:
    """Return (matching rule, reason). If several match, the strictest (lowest hours) wins."""
    limits = LIMITS if limits is None else limits
    if not product_type:
        return None, "Product type unknown."
    name = product_type.lower()
    matches = [r for r in limits if r.keyword in name]
    if not matches:
        return None, "No approved time limit is configured for this product type."
    specific = [r for r in matches if condition and r.condition == condition]
    generic = [r for r in matches if r.condition == "any"]
    candidates = specific or generic
    if not candidates:
        if condition is None:
            return None, "Limits for this product depend on storage condition, which is not confirmed."
        return None, f"No approved limit for this product under '{condition}' storage."
    return min(candidates, key=lambda r: r.max_hours), ""


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
    condition = detect_condition(batch)
    limit, reason = find_limit(batch.product_type.value, condition)
    if limit is None:
        return RuleResult(rule, None, f"{hours:.1f} h since preparation. {reason}")
    ok = hours <= limit.max_hours
    message = (
        f"{hours:.1f} h since preparation; limit {limit.max_hours:g} h "
        f"({limit.condition} storage). Source clock starts: {limit.clock_starts or 'not stated'}."
    )
    return RuleResult(rule, ok, message, source=limit.citation(), link=limit.link)


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