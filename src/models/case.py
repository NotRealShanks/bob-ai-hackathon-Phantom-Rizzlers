"""
models/case.py — CaseRecord dataclass and CaseStatus enum.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class CaseStatus(str, Enum):
    OPEN = "Open"
    UNDER_REVIEW = "Under Review"
    REPORT_PREPARED = "Report Prepared"
    RESOLVED = "Resolved"


@dataclass
class CaseRecord:
    id: str
    created_at: str
    updated_at: str
    reporter_role: str
    situation_summary: str
    situation_category: str           # may be empty string if AI unavailable
    severity: str                     # "LOW" | "MODERATE" | "HIGH" | "URGENT_SAFETY_CONCERN"
    immediate_safety_concern: bool
    ai_assessment_json: str           # raw JSON string; empty string if AI unavailable
    deterministic_signals_json: str   # raw JSON string
    recommended_actions_json: str     # raw JSON string (array)
    safety_signals_json: str          # raw JSON string (array of SignalItem dicts)
    case_status: CaseStatus
    report_status: str                # "Not Generated" | "Draft Generated" | "Submitted"
    reporter_notes: str               # empty string if none provided
    report_draft_md: str              # empty string until generated
