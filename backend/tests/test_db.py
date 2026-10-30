from app import db as db_module
from app.schemas import HumanReview


def test_messages_are_saved_in_order(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    db_module.init_db()
    db_module.save_message("case-x", "user", "hello")
    db_module.save_message("case-x", "assistant", "what temperature?")
    msgs = db_module.get_messages("case-x")
    assert [m["role"] for m in msgs] == ["user", "assistant"]
    assert msgs[1]["content"] == "what temperature?"


def test_reviews_are_saved(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    db_module.init_db()
    db_module.save_review(
        "case-x", HumanReview(reviewer="Aalia", decision="hold", notes="check")
    )
    assert db_module.get_reviews("case-x")[0]["decision"] == "hold"