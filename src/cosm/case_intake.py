
"""
Case intake and validation for the Child Online Safety Monitor.

Development uses fictional, synthetic case information only.
This module validates reported information; it does not determine
whether abuse or a criminal offence has occurred.
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict, field_validator


class ReporterRole(str, Enum):
    PARENT = "parent"
    TEACHER = "teacher"
    CHILD_PROTECTION_WORKER = "child_protection_worker"
    NGO_WORKER = "ngo_worker"
    OTHER = "other"


class CaseStatus(str, Enum):
    INTAKE = "intake"
    UNDER_REVIEW = "under_review"
    CLOSED = "closed"


class Case(BaseModel):
    """Validated, non-identifying case record."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    case_id: str = Field(
        default_factory=lambda: f"COSM-{uuid4().hex[:12].upper()}"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    reporter_role: ReporterRole

    reported_behavior: str = Field(
        min_length=10,
        max_length=5000,
        description="Fictional or non-identifying behavioral description."
    )

    observed_changes: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    timeline: str = Field(
        min_length=3,
        max_length=1000,
        description="Approximate timeline without identifying details."
    )

    mock_chat_excerpt: str | None = Field(
        default=None,
        max_length=3000,
        description="Optional synthetic excerpt; never upload real sensitive material."
    )

    status: CaseStatus = CaseStatus.INTAKE

    @field_validator("observed_changes")
    @classmethod
    def validate_observed_changes(cls, values):
        cleaned = []

        for value in values:
            value = value.strip()

            if not value:
                raise ValueError("Observed changes cannot contain empty entries.")

            if len(value) > 300:
                raise ValueError("Each observed change must be 300 characters or fewer.")

            cleaned.append(value)

        return cleaned

    @field_validator("mock_chat_excerpt")
    @classmethod
    def validate_mock_excerpt(cls, value):
        if value is not None and not value.strip():
            raise ValueError("Mock excerpt must be non-empty when provided.")

        return value


def create_case(
    reporter_role: ReporterRole,
    reported_behavior: str,
    timeline: str,
    observed_changes: list[str] | None = None,
    mock_chat_excerpt: str | None = None,
) -> Case:
    """
    Create a validated case.

    The caller must ensure that submitted information is fictional
    or appropriately de-identified.
    """

    return Case(
        reporter_role=reporter_role,
        reported_behavior=reported_behavior,
        timeline=timeline,
        observed_changes=observed_changes or [],
        mock_chat_excerpt=mock_chat_excerpt,
    )