
import pytest
from pydantic import ValidationError

from src.cosm.case_intake import (
    Case,
    CaseStatus,
    ReporterRole,
    create_case,
)


def make_valid_case():
    return create_case(
        reporter_role=ReporterRole.PARENT,
        reported_behavior=(
            "A fictional student has become unusually "
            "secretive about online conversations."
        ),
        timeline="Observed over approximately two weeks.",
        observed_changes=["Changed communication habits"],
    )


def test_case_creation():
    case = make_valid_case()

    assert isinstance(case, Case)
    assert case.reporter_role == ReporterRole.PARENT
    assert case.status == CaseStatus.INTAKE


def test_case_reference_is_generated():
    case = make_valid_case()

    assert case.case_id.startswith("COSM-")
    assert len(case.case_id) == 17


def test_case_references_are_unique():
    first = make_valid_case()
    second = make_valid_case()

    assert first.case_id != second.case_id


def test_case_rejects_short_behavior_description():
    with pytest.raises(ValidationError):
        create_case(
            reporter_role=ReporterRole.PARENT,
            reported_behavior="Too short",
            timeline="One week",
        )


def test_case_rejects_invalid_reporter_role():
    with pytest.raises(ValidationError):
        Case(
            reporter_role="unknown_role",
            reported_behavior="A sufficiently long fictional description.",
            timeline="One week",
        )


def test_case_rejects_unexpected_fields():
    with pytest.raises(ValidationError):
        Case(
            reporter_role="parent",
            reported_behavior="A sufficiently long fictional description.",
            timeline="One week",
            child_name="Not permitted",
        )


def test_case_rejects_empty_observed_change():
    with pytest.raises(ValidationError):
        create_case(
            reporter_role=ReporterRole.PARENT,
            reported_behavior="A sufficiently long fictional description.",
            timeline="One week",
            observed_changes=["   "],
        )


def test_case_defaults_to_intake_status():
    case = make_valid_case()

    assert case.status == CaseStatus.INTAKE


def test_case_has_utc_timestamp():
    case = make_valid_case()

    assert case.created_at.tzinfo is not None
    assert case.created_at.utcoffset().total_seconds() == 0