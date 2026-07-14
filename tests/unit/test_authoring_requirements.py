import pytest
from pydantic import ValidationError

from paperflow.models.authoring_requirements import (
    AuthoringRequirements,
    compute_requirements_digest,
)
from tests.fixtures.make_authoring_requirements import make_authoring_requirements


def test_complete_requirements_validate_and_digest_is_stable() -> None:
    data = make_authoring_requirements("a" * 64)
    requirements = AuthoringRequirements.model_validate(data)
    assert compute_requirements_digest(requirements) == data["confirmation"]["content_sha256"]


def test_confirmation_metadata_is_excluded_from_digest() -> None:
    data = make_authoring_requirements("a" * 64)
    digest = compute_requirements_digest(data)
    data["confirmation"]["confirmed_at"] = "2026-07-15T00:00:00Z"
    assert compute_requirements_digest(data) == digest


def test_content_edit_changes_digest() -> None:
    data = make_authoring_requirements("a" * 64)
    digest = data["confirmation"]["content_sha256"]
    data["report"]["purpose"] = "Changed after confirmation"
    assert compute_requirements_digest(data) != digest


def test_blank_required_text_is_rejected() -> None:
    data = make_authoring_requirements("a" * 64)
    data["use_case"]["scenario"] = " "
    with pytest.raises(ValidationError):
        AuthoringRequirements.model_validate(data)


def test_inverted_page_or_slide_range_is_rejected() -> None:
    data = make_authoring_requirements("a" * 64)
    data["presentation"]["target_slides"] = {"minimum": 15, "maximum": 13}
    with pytest.raises(ValidationError):
        AuthoringRequirements.model_validate(data)


def test_enabled_report_requires_formats() -> None:
    data = make_authoring_requirements("a" * 64)
    data["report"]["formats"] = []
    data["deliverables"]["formats"] = ["pptx", "slides_pdf", "speaker_notes"]
    with pytest.raises(ValidationError):
        AuthoringRequirements.model_validate(data)
