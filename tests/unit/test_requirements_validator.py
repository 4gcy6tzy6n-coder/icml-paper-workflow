from pathlib import Path

from paperflow.requirements.validator import (
    validate_evidence_outputs,
    validate_requirements_file,
)
from paperflow.util.jsonio import write_json
from tests.fixtures.make_authoring_requirements import make_authoring_requirements


def test_valid_file_returns_model_and_no_issues(tmp_path: Path) -> None:
    path = tmp_path / "requirements.json"
    write_json(path, make_authoring_requirements("a" * 64))
    requirements, issues = validate_requirements_file(path, "a" * 64)
    assert requirements is not None
    assert issues == []


def test_missing_file_returns_req_file_missing(tmp_path: Path) -> None:
    _, issues = validate_requirements_file(tmp_path / "missing.json", "a" * 64)
    assert {issue.code for issue in issues} == {"REQ_FILE_MISSING"}


def test_malformed_json_returns_req_json_invalid(tmp_path: Path) -> None:
    path = tmp_path / "requirements.json"
    path.write_text("{", encoding="utf-8")
    _, issues = validate_requirements_file(path, "a" * 64)
    assert {issue.code for issue in issues} == {"REQ_JSON_INVALID"}


def test_invalid_utf8_returns_req_json_invalid(tmp_path: Path) -> None:
    path = tmp_path / "requirements.json"
    path.write_bytes(b"\xff")
    _, issues = validate_requirements_file(path, "a" * 64)
    assert {issue.code for issue in issues} == {"REQ_JSON_INVALID"}


def test_wrong_pdf_returns_req_source_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "requirements.json"
    write_json(path, make_authoring_requirements("b" * 64))
    _, issues = validate_requirements_file(path, "a" * 64)
    assert {issue.code for issue in issues} == {"REQ_SOURCE_MISMATCH"}


def test_content_edit_returns_digest_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "requirements.json"
    data = make_authoring_requirements("a" * 64)
    data["visual"]["style"] = "changed"
    write_json(path, data)
    _, issues = validate_requirements_file(path, "a" * 64)
    assert {issue.code for issue in issues} == {"REQ_CONFIRMATION_DIGEST_MISMATCH"}


def test_unknown_field_returns_schema_invalid(tmp_path: Path) -> None:
    path = tmp_path / "requirements.json"
    data = make_authoring_requirements("a" * 64)
    data["visual"]["reviewer_note"] = "added after confirmation"
    write_json(path, data)
    _, issues = validate_requirements_file(path, "a" * 64)
    assert {issue.code for issue in issues} == {"REQ_SCHEMA_INVALID"}


def test_surrounding_whitespace_edit_returns_digest_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "requirements.json"
    data = make_authoring_requirements("a" * 64)
    data["visual"]["style"] = " 清晰、克制、学术化 "
    write_json(path, data)
    _, issues = validate_requirements_file(path, "a" * 64)
    assert {issue.code for issue in issues} == {"REQ_CONFIRMATION_DIGEST_MISMATCH"}


def test_schema_error_returns_req_schema_invalid(tmp_path: Path) -> None:
    path = tmp_path / "requirements.json"
    data = make_authoring_requirements("a" * 64)
    data["use_case"]["scenario"] = ""
    write_json(path, data)
    _, issues = validate_requirements_file(path, "a" * 64)
    assert {issue.code for issue in issues} == {"REQ_SCHEMA_INVALID"}


def test_empty_evidence_map_is_not_an_intake_prerequisite(tmp_path: Path) -> None:
    evidence_map = tmp_path / "evidence-map.json"
    semantic_packet = tmp_path / "semantic-packet.md"
    write_json(evidence_map, [])
    semantic_packet.write_text("# Semantic packet", encoding="utf-8")

    issues = validate_evidence_outputs(evidence_map, semantic_packet)

    assert {issue.code for issue in issues} == {"REQ_EVIDENCE_MAP_EMPTY"}


def test_malformed_evidence_records_are_not_an_intake_prerequisite(
    tmp_path: Path,
) -> None:
    evidence_map = tmp_path / "evidence-map.json"
    semantic_packet = tmp_path / "semantic-packet.md"
    write_json(evidence_map, [{"id": "not-a-usable-evidence-record"}])
    semantic_packet.write_text("# Semantic packet", encoding="utf-8")

    issues = validate_evidence_outputs(evidence_map, semantic_packet)

    assert {issue.code for issue in issues} == {"REQ_EVIDENCE_MAP_INVALID"}
