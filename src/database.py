"""
database.py — SQLite connection and schema initialisation for COSM.

The database file (cosm.db) is stored in the same directory as this module (src/).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

_DB_PATH = Path(__file__).parent / "cosm.db"

_CREATE_CASES_SQL = """
CREATE TABLE IF NOT EXISTS cases (
    id                          TEXT PRIMARY KEY,
    created_at                  TEXT NOT NULL,
    updated_at                  TEXT NOT NULL,
    reporter_role               TEXT NOT NULL,
    situation_summary           TEXT NOT NULL,
    situation_category          TEXT,
    severity                    TEXT NOT NULL,
    immediate_safety_concern    INTEGER NOT NULL DEFAULT 0,
    ai_assessment_json          TEXT,
    deterministic_signals_json  TEXT,
    recommended_actions_json    TEXT,
    safety_signals_json         TEXT,
    case_status                 TEXT NOT NULL DEFAULT 'Open',
    report_status               TEXT NOT NULL DEFAULT 'Not Generated',
    reporter_notes              TEXT,
    report_draft_md             TEXT
);
"""


def init_db() -> None:
    """
    Create the cases table if it does not exist.
    Called once at application startup (before page routing).
    Safe to call multiple times (uses CREATE TABLE IF NOT EXISTS).
    """
    with get_connection() as conn:
        conn.execute(_CREATE_CASES_SQL)
        conn.commit()


def get_connection() -> sqlite3.Connection:
    """
    Return a new SQLite connection to cosm.db.
    Caller is responsible for closing or using as a context manager.
    Row factory is set to sqlite3.Row so columns are accessible by name.
    """
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn
