from datetime import datetime

from app import rules
from app.rules import decide_status, elapsed_hours, evaluate_batch
from app.schemas import BatchInfo

FIELDS = ["product_type", "quantity", "prepared_at",
          "storage_temperature", "storage_history", "packaging_condition"]


def make_batch(**overrides):
    base = {f: {"value": "x", "status": "confirmed"} for f in FIELDS}
    base["product_type"] = {"value": "cooked veg biryani", "status": "confirmed"}
    base["prepared_at"] = {"value": "18:00", "status": "confirmed"}
    base.update(overrides)
    return BatchInfo.model_validate(base)


NOW = datetime(2026, 10, 24, 22, 0)


def test_elapsed_hours_same_day():
    assert elapsed_hours("18:00", NOW) == 4.0


def test_elapsed_hours_crosses_midnight():
    assert elapsed_hours("23:00", NOW) == 23.0


def test_missing_temperature_needs_info():
    batch = make_batch(storage_temperature={"value": None, "status": "unknown"})
    results = evaluate_batch(batch, NOW)
    failed = [r.rule for r in results if r.passed is False]
    assert "storage_temperature_present" in failed
    assert decide_status(results) == "more_information_required"


def test_inferred_value_is_not_enough():
    batch = make_batch(storage_history={"value": "maybe covered", "status": "inferred"})
    assert decide_status(evaluate_batch(batch, NOW)) == "more_information_required"


def test_complete_batch_is_ready_for_review():
    assert decide_status(evaluate_batch(make_batch(), NOW)) == "ready_for_human_review"


def test_no_limit_configured_does_not_invent_one():
    results = evaluate_batch(make_batch(), NOW)
    window = [r for r in results if r.rule == "time_window_within_limit"][0]
    assert window.passed is None


def test_exceeded_limit_is_urgent(monkeypatch):
    # 2.0 here is a TEST number only. It is not a food-safety claim.
    monkeypatch.setitem(rules.SAFE_WINDOW_HOURS, "biryani", 2.0)
    results = evaluate_batch(make_batch(), NOW)
    assert decide_status(results) == "urgent_review_or_hold"