import json
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from paperflow.models.authoring_requirements import (
    AuthoringRequirements,
    compute_requirements_digest,
)
from paperflow.models.common import Severity
from paperflow.models.paper_ir import EvidenceRef
from paperflow.models.qa import ValidationIssue
from paperflow.util.jsonio import read_json

_EVIDENCE_MAP_ADAPTER = TypeAdapter(list[EvidenceRef])


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
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
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
    if compute_requirements_digest(raw) != requirements.confirmation.content_sha256:
        issues.append(
            _error(
                "REQ_CONFIRMATION_DIGEST_MISMATCH",
                "Requirements changed after confirmation.",
                "confirmation.content_sha256",
            )
        )
    return (requirements if not issues else None), issues


def validate_evidence_outputs(
    evidence_map_path: Path,
    semantic_packet_path: Path,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not evidence_map_path.exists():
        issues.append(
            _error(
                "REQ_EVIDENCE_MAP_MISSING",
                "Evidence map is missing; run paperflow build-evidence before intake.",
                str(evidence_map_path),
            )
        )
    else:
        try:
            evidence = read_json(evidence_map_path)
        except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
            issues.append(
                _error(
                    "REQ_EVIDENCE_MAP_INVALID",
                    f"Evidence map cannot be read; rerun paperflow build-evidence: {exc}",
                    str(evidence_map_path),
                )
            )
        else:
            if not isinstance(evidence, list):
                issues.append(
                    _error(
                        "REQ_EVIDENCE_MAP_INVALID",
                        "Evidence map must be a JSON list; rerun paperflow build-evidence.",
                        str(evidence_map_path),
                    )
                )
            elif not evidence:
                issues.append(
                    _error(
                        "REQ_EVIDENCE_MAP_EMPTY",
                        "Evidence map has no usable records; rerun paperflow "
                        "build-evidence and inspect the parsed source.",
                        str(evidence_map_path),
                    )
                )
            else:
                try:
                    _EVIDENCE_MAP_ADAPTER.validate_python(evidence)
                except ValidationError as exc:
                    issues.append(
                        _error(
                            "REQ_EVIDENCE_MAP_INVALID",
                            "Evidence map contains malformed records; rerun "
                            f"paperflow build-evidence: {exc}",
                            str(evidence_map_path),
                        )
                    )

    if not semantic_packet_path.exists():
        issues.append(
            _error(
                "REQ_EVIDENCE_PACKET_MISSING",
                "Semantic packet is missing; run paperflow build-evidence before intake.",
                str(semantic_packet_path),
            )
        )
    else:
        try:
            packet = semantic_packet_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            issues.append(
                _error(
                    "REQ_EVIDENCE_PACKET_INVALID",
                    f"Semantic packet cannot be read; rerun paperflow build-evidence: {exc}",
                    str(semantic_packet_path),
                )
            )
        else:
            if not packet.strip():
                issues.append(
                    _error(
                        "REQ_EVIDENCE_PACKET_INVALID",
                        "Semantic packet is empty; rerun paperflow build-evidence.",
                        str(semantic_packet_path),
                    )
                )
    return issues


def load_validated_requirements(
    path: Path,
    expected_source_sha256: str,
    validated_content_sha256: str | None,
) -> tuple[AuthoringRequirements | None, list[ValidationIssue]]:
    requirements, issues = validate_requirements_file(path, expected_source_sha256)
    if validated_content_sha256 is None:
        issues.append(
            _error(
                "REQ_VALIDATED_DIGEST_MISSING",
                "Workflow has no validated requirements seal; rerun "
                "paperflow validate-requirements.",
                "manifest.validated_requirements_content_sha256",
            )
        )
    elif requirements is not None:
        current_digest = requirements.confirmation.content_sha256
        if current_digest != validated_content_sha256:
            issues.append(
                _error(
                    "REQ_VALIDATED_DIGEST_MISMATCH",
                    "Current requirements differ from the workflow-validated content; "
                    "review, reconfirm, and rerun paperflow validate-requirements.",
                    "manifest.validated_requirements_content_sha256",
                )
            )
    return (requirements if not issues else None), issues
