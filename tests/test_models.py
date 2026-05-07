import pytest
from pydantic import ValidationError

from src.models import ClassifierOutput, RawProspect


def test_raw_prospect_minimal():
    rp = RawProspect(full_name="Ada Lovelace", source="manual_csv")
    assert rp.full_name == "Ada Lovelace"
    assert rp.candidate_categories == []
    assert rp.source_context == {}


def test_classifier_output_validates_score_bounds():
    with pytest.raises(ValidationError):
        ClassifierOutput(
            services_thesis_fit=6,
            ai_literacy=3,
            operator_depth=3,
            check_size_fit=3,
            warm_intro_accessibility=3,
            composite_score=18,
            tier="2",
            rationale="x",
            confidence="medium",
        )


def test_classifier_output_validates_tier_enum():
    with pytest.raises(ValidationError):
        ClassifierOutput(
            services_thesis_fit=3,
            ai_literacy=3,
            operator_depth=3,
            check_size_fit=3,
            warm_intro_accessibility=3,
            composite_score=15,
            tier="0",  # invalid
            rationale="x",
            confidence="medium",
        )


def test_classifier_output_composite_min():
    """composite_score must be >= 5."""
    with pytest.raises(ValidationError):
        ClassifierOutput(
            services_thesis_fit=1,
            ai_literacy=1,
            operator_depth=1,
            check_size_fit=1,
            warm_intro_accessibility=1,
            composite_score=4,
            tier="drop",
            rationale="x",
            confidence="low",
        )


def test_canonical_name_used_for_dedupe_key_via_utils():
    from src.utils.names import canonicalize

    assert canonicalize("Dr. María García-Lopez Jr.") == "maria garcia-lopez"
    assert canonicalize("DANIEL DINES") == "daniel dines"
    assert canonicalize("  Justin   Welsh  ") == "justin welsh"
