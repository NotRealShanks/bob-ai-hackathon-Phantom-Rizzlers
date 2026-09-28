"""
services/case_service.py — SQLite CRUD operations for COSM cases.

All persistence goes through database.get_connection().
This module serialises/deserialises Python dataclasses to/from JSON strings
for storage in the SQLite TEXT columns.
"""

from __future__ import annotations

import dataclasses
import json
import secrets
from datetime import datetime, timezone
from typing import List, Optional

import database
from models.assessment import AIAssessment, CombinedAssessment, DeterministicResult, SignalItem
from models.case import CaseRecord, CaseStatus


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _dataclass_to_dict(obj) -> dict:
    """
    Recursively convert a dataclass (and any nested dataclasses) to a plain dict.
    Handles lists of dataclasses (e.g. safety_signals: List[SignalItem]).
    """
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        result = {}
        for f in dataclasses.fields(obj):
            value = getattr(obj, f.name)
            result[f.name] = _dataclass_to_dict(value)
        return result
    if isinstance(obj, list):
        return [_dataclass_to_dict(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _dataclass_to_dict(v) for k, v in obj.items()}
    return obj


def _serialise(obj) -> str:
    """Serialise a dataclass or list to a JSON string."""
    return json.dumps(_dataclass_to_dict(obj), ensure_ascii=False)


def _row_to_case(row) -> CaseRecord:
    """Convert a sqlite3.Row to a CaseRecord, with safe defaults for nullable columns."""
    return CaseRecord(
        id=row["id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        reporter_role=row["reporter_role"],
        situation_summary=row["situation_summary"],
        situation_category=row["situation_category"] or "",
        severity=row["severity"],
        immediate_safety_concern=bool(row["immediate_safety_concern"]),
        ai_assessment_json=row["ai_assessment_json"] or "",
        deterministic_signals_json=row["deterministic_signals_json"] or "",
        recommended_actions_json=row["recommended_actions_json"] or "[]",
        safety_signals_json=row["safety_signals_json"] or "[]",
        case_status=CaseStatus(row["case_status"]),
        report_status=row["report_status"] or "Not Generated",
        reporter_notes=row["reporter_notes"] or "",
        report_draft_md=row["report_draft_md"] or "",
    )


def _now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_case_id() -> str:
    """Generate a unique case ID in the format CASE-YYYYMMDD-HHMMSS-xxxx."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    suffix = secrets.token_hex(2)  # 4 hex chars
    return f"CASE-{ts}-{suffix}"


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

def create_case(
    reporter_role: str,
    situation_summary: str,
    combined: CombinedAssessment,
    reporter_notes: str = "",
) -> CaseRecord:
    """
    Persist a new case to SQLite and return the full CaseRecord.
    Truncates situation_summary to 2000 characters before storing.
    """
    now = _now_iso()
    case_id = _new_case_id()
    summary_safe = situation_summary[:2000]

    # Extract safety signals — prefer AI signals, fall back to deterministic warning signs
    ai = combined.ai
    det = combined.deterministic

    safety_signals = ai.safety_signals if ai.safety_signals else []
    recommended_actions = ai.recommended_actions if ai.recommended_actions else []

    # Build JSON strings
    ai_json = _serialise(ai) if not ai.error_note or ai.safety_signals else ""
    det_json = _serialise(det)
    signals_json = _serialise(safety_signals)
    actions_json = json.dumps(recommended_actions, ensure_ascii=False)

    row = (
        case_id,
        now,
        now,
        reporter_role,
        summary_safe,
        ai.situation_category,
        combined.final_severity,
        1 if combined.immediate_safety_concern else 0,
        ai_json,
        det_json,
        actions_json,
        signals_json,
        CaseStatus.OPEN.value,
        "Not Generated",
        reporter_notes,
        "",
    )

    sql = """
        INSERT INTO cases (
            id, created_at, updated_at, reporter_role, situation_summary,
            situation_category, severity, immediate_safety_concern,
            ai_assessment_json, deterministic_signals_json,
            recommended_actions_json, safety_signals_json,
            case_status, report_status, reporter_notes, report_draft_md
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    with database.get_connection() as conn:
        conn.execute(sql, row)
        conn.commit()

    return get_case(case_id)


def get_case(case_id: str) -> Optional[CaseRecord]:
    """Return the CaseRecord for the given id, or None if not found."""
    with database.get_connection() as conn:
        row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    if row is None:
        return None
    return _row_to_case(row)


def list_cases(
    limit: int = 50,
    status_filter: Optional[str] = None,
) -> List[CaseRecord]:
    """
    Return up to `limit` cases ordered by created_at DESC.
    If status_filter is provided, filter by case_status.
    """
    with database.get_connection() as conn:
        if status_filter:
            rows = conn.execute(
                "SELECT * FROM cases WHERE case_status = ? ORDER BY created_at DESC LIMIT ?",
                (status_filter, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM cases ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [_row_to_case(r) for r in rows]


def update_case_status(case_id: str, new_status: str) -> CaseRecord:
    """
    Update case_status and updated_at for the given case.
    Returns the updated CaseRecord.
    Raises ValueError if case_id not found.
    """
    existing = get_case(case_id)
    if existing is None:
        raise ValueError(f"Case not found: {case_id}")

    now = _now_iso()
    with database.get_connection() as conn:
        conn.execute(
            "UPDATE cases SET case_status = ?, updated_at = ? WHERE id = ?",
            (new_status, now, case_id),
        )
        conn.commit()

    return get_case(case_id)


def save_report_draft(case_id: str, draft_md: str) -> None:
    """
    Store the generated markdown report draft in report_draft_md.
    Set report_status = "Draft Generated" and update updated_at.
    """
    now = _now_iso()
    with database.get_connection() as conn:
        conn.execute(
            "UPDATE cases SET report_draft_md = ?, report_status = ?, updated_at = ? WHERE id = ?",
            (draft_md, "Draft Generated", now, case_id),
        )
        conn.commit()
