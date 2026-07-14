import json
from pathlib import Path

from pydantic import ValidationError

from paperflow.models.authoring_requirements import (
    AuthoringRequirements,
    compute_requirements_digest,
)
from paperflow.models.common import Severity
from paperflow.models.qa import ValidationIssue
from paperflow.util.jsonio import read_json


def _error(code: str, message: str, location: str) -> ValidationIssue:
    return ValidationIssue(
        code=code,
        severity=Severity.ERROR,
        message=message,
        location=location,
    )


def validate_requirements_file(
    path: Path, expected_source_sha256: str
) -> tuple[AuthoringRequirements | None, list[ValidationIssue]]:
    if not path.exists():
        return None, [_error("REQ_FILE_MISSING", f"Requirements not found: {path}", str(path))]
    try:
        raw = read_json(path)
    except (json.JSONDecodeError, OSError) as exc:
        return None, [
            _error("REQ_JSON_INVALID", f"Cannot read requirements JSON: {exc}", str(path))
        ]
    try:
        requirements = AuthoringRequirements.model_validate(raw)
    except ValidationError as exc:
        return None, [
            _error("REQ_SCHEMA_INVALID", f"Invalid requirements schema: {exc}", str(path))
        ]

    issues: list[ValidationIssue] = []
    if requirements.source.pdf_sha256 != expected_source_sha256:
        issues.append(
            _error(
                "REQ_SOURCE_MISMATCH",
                "Requirements belong to another PDF.",
                "source.pdf_sha256",
            )
        )
    if compute_requirements_digest(requirements) != requirements.confirmation.content_sha256:
        issues.append(
            _error(
                "REQ_CONFIRMATION_DIGEST_MISMATCH",
                "Requirements changed after confirmation.",
                "confirmation.content_sha256",
            )
        )
    return (requirements if not issues else None), issues
