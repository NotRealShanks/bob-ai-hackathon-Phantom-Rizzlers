"""
models/assessment.py — Data classes for AI and deterministic assessment results.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class SignalItem:
    signal: str
    explanation: str
    severity: str   # "informational" | "concerning" | "serious"


@dataclass
class AIAssessment:
    concern_level: str           # "LOW" | "MODERATE" | "HIGH" | "URGENT_SAFETY_CONCERN"
    situation_category: str      # e.g. "Grooming", "Sextortion", "Cyberbullying", "General Concern"
    confidence: str              # "LOW" | "MODERATE" | "HIGH"
    uncertainty_note: str        # e.g. "Assessment is based only on the description provided."
    situation_summary: str       # 2–3 sentence neutral summary of the reported situation
    safety_signals: List[SignalItem]
    why_this_matters: str        # plain-language explanation for a non-expert parent
    recommended_actions: List[str]
    actions_to_avoid: List[str]
    evidence_guidance: List[str]
    reporting_guidance: List[str]
    escalation_guidance: str
    legal_context_note: str      # framed as "potentially relevant", never definitive
    disclaimer: str              # must always be non-empty
    error_note: str = ""         # non-empty string if the AI call failed or was unavailable


@dataclass
class DeterministicResult:
    """
    Direct rename of AnalysisResult from analyzer.py.
    All fields are identical; only the class name changes.
    """
    risk_level: str              # "Low" | "Medium" | "High" | "Critical"
    risk_score: int              # 0–100
    warning_signs: List = field(default_factory=list)     # List[WarningSigns] from safety_rules
    legal_mappings: List = field(default_factory=list)    # List[LegalMapping] from safety_rules
    preservation_steps: List[str] = field(default_factory=list)
    summary: str = ""
    input_type: str = "unknown"  # "behavioural" | "chat"


# Severity mapping from deterministic risk_level to AI concern_level vocabulary
DETERMINISTIC_TO_SEVERITY = {
    "Low":      "LOW",
    "Medium":   "MODERATE",
    "High":     "HIGH",
    "Critical": "URGENT_SAFETY_CONCERN",
}

# Severity ordering for taking the higher of two levels
SEVERITY_ORDER = {
    "LOW": 0,
    "MODERATE": 1,
    "HIGH": 2,
    "URGENT_SAFETY_CONCERN": 3,
}


@dataclass
class CombinedAssessment:
    """
    Merges AI assessment + deterministic safety-rules result into one object
    consumed by pages and case_service.
    """
    ai: AIAssessment
    deterministic: DeterministicResult
    immediate_safety_concern: bool

    @property
    def final_severity(self) -> str:
        """
        Returns the higher of ai.concern_level and the mapped deterministic level.
        If immediate_safety_concern is True, returns at minimum "HIGH".
        """
        ai_level = SEVERITY_ORDER.get(self.ai.concern_level, 0)
        det_level = SEVERITY_ORDER.get(
            DETERMINISTIC_TO_SEVERITY.get(self.deterministic.risk_level, "LOW"), 0
        )
        combined = max(ai_level, det_level)
        # Ensure immediate safety concern is never hidden
        if self.immediate_safety_concern:
            combined = max(combined, SEVERITY_ORDER["HIGH"])
        return list(SEVERITY_ORDER.keys())[combined]
