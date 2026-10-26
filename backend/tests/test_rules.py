from datetime import datetime

from app import rules
from app.rules import decide_status, detect_condition, elapsed_hours, evaluate_batch
from app.schemas import BatchInfo

FIELDS = ["product_type", "quantity", "prepared_at",
          "storage_temperature", "storage_history", "packaging_condition"]

HEADER = ("food_keyword,storage_condition,max_hours,clock_starts,"
          "source_document,section,link,quote,date_checked")

NOW = datetime(2026, 10, 24, 22, 0)  # 4 hours after the 18:00 default


def make_batch(**overrides):
    base = {f: {"value": "x", "status": "confirmed"} for f in FIELDS}
    base["product_type"] = {"value": "cooked veg biryani", "status": "confirmed"}
    base["prepared_at"] = {"value": "18:00", "status": "confirmed"}
    base.update(overrides)
    return BatchInfo.model_validate(base)


def make_row(**kw):
    # TEST ROWS ONLY. These numbers are not food-safety claims.
    base = dict(keyword="biryani", condition="any", max_hours=2.0,
                clock_starts="cooking finished", source_document="TEST DOC",
                section="TEST SECTION", link="https://example.com",
                quote="", date_checked="2026-10-24")
    base.update(kw)
    return rules.WindowRule(**base)


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


def test_no_limit_configured_does_not_invent_one(monkeypatch):
    monkeypatch.setattr(rules, "LIMITS", [])
    results = evaluate_batch(make_batch(), NOW)
    window = [r for r in results if r.rule == "time_window_within_limit"][0]
    assert window.passed is None
    assert decide_status(results) == "ready_for_human_review"


def test_exceeded_limit_is_urgent_and_cites_source(monkeypatch):
    monkeypatch.setattr(rules, "LIMITS", [make_row(max_hours=2.0)])
    results = evaluate_batch(make_batch(), NOW)
    window = [r for r in results if r.rule == "time_window_within_limit"][0]
    assert window.passed is False
    assert window.source == "TEST DOC, TEST SECTION"
    assert decide_status(results) == "urgent_review_or_hold"


def test_within_limit_passes(monkeypatch):
    monkeypatch.setattr(rules, "LIMITS", [make_row(max_hours=6.0)])
    results = evaluate_batch(make_batch(), NOW)
    window = [r for r in results if r.rule == "time_window_within_limit"][0]
    assert window.passed is True


def test_condition_specific_limit_needs_matching_condition(monkeypatch):
    monkeypatch.setattr(rules, "LIMITS", [make_row(condition="refrigerated", max_hours=2.0)])
    batch = make_batch(storage_history={"value": "kept at room temperature", "status": "confirmed"})
    window = [r for r in evaluate_batch(batch, NOW) if r.rule == "time_window_within_limit"][0]
    assert window.passed is None  # no refrigerated evidence, so no verdict


def test_unconfirmed_condition_means_no_verdict(monkeypatch):
    monkeypatch.setattr(rules, "LIMITS", [make_row(condition="room", max_hours=2.0)])
    window = [r for r in evaluate_batch(make_batch(), NOW) if r.rule == "time_window_within_limit"][0]
    assert window.passed is None


def test_detect_condition():
    fridge = make_batch(storage_history={"value": "stored in the fridge", "status": "confirmed"})
    assert detect_condition(fridge) == "refrigerated"
    guess = make_batch(storage_history={"value": "stored in the fridge", "status": "inferred"})
    assert detect_condition(guess) is None


def test_loader_skips_rows_without_source(tmp_path):
    p = tmp_path / "w.csv"
    p.write_text(HEADER + "\nbiryani,room,2,cooking finished,,,,,\n", encoding="utf-8")
    limits, warnings = rules.load_limits(p)
    assert limits == []
    assert len(warnings) == 1


def test_loader_accepts_complete_row(tmp_path):
    p = tmp_path / "w.csv"
    p.write_text(
        HEADER + "\nbiryani,room,2,cooking finished,TEST DOC,Sec 1,https://example.com,,2026-10-24\n",
        encoding="utf-8",
    )
    limits, warnings = rules.load_limits(p)
    assert warnings == []
    assert limits[0].keyword == "biryani"
    assert limits[0].max_hours == 2.0