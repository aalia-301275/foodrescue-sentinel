import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional

from app.schemas import HumanReview, ReviewReport

DB_PATH = Path(__file__).resolve().parent.parent / "sentinel.db"


@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS cases (
                case_id TEXT PRIMARY KEY,
                report_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                reviewer TEXT NOT NULL,
                decision TEXT NOT NULL,
                notes TEXT,
                reviewed_at TEXT DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )"""
        )


def save_report(report: ReviewReport):
    with db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO cases (case_id, report_json) VALUES (?, ?)",
            (report.case_id, report.model_dump_json()),
        )


def get_report(case_id: str) -> Optional[ReviewReport]:
    with db() as conn:
        row = conn.execute(
            "SELECT report_json FROM cases WHERE case_id = ?", (case_id,)
        ).fetchone()
    return ReviewReport.model_validate_json(row["report_json"]) if row else None


def list_reports() -> List[ReviewReport]:
    with db() as conn:
        rows = conn.execute(
            "SELECT report_json FROM cases ORDER BY created_at DESC"
        ).fetchall()
    return [ReviewReport.model_validate_json(r["report_json"]) for r in rows]


def save_review(case_id: str, review: HumanReview):
    with db() as conn:
        conn.execute(
            "INSERT INTO reviews (case_id, reviewer, decision, notes) VALUES (?, ?, ?, ?)",
            (case_id, review.reviewer, review.decision, review.notes),
        )


def get_reviews(case_id: str) -> list:
    with db() as conn:
        rows = conn.execute(
            "SELECT reviewer, decision, notes, reviewed_at FROM reviews "
            "WHERE case_id = ? ORDER BY id",
            (case_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def save_message(case_id: str, role: str, content: str):
    with db() as conn:
        conn.execute(
            "INSERT INTO messages (case_id, role, content) VALUES (?, ?, ?)",
            (case_id, role, content),
        )


def get_messages(case_id: str) -> list:
    with db() as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE case_id = ? ORDER BY id",
            (case_id,),
        ).fetchall()
    return [dict(r) for r in rows]