import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from paperflow.cli import app
from paperflow.manifest import load_manifest
from paperflow.models.common import WorkflowStage
from paperflow.models.document import ParsedDocument, TextBlock
from paperflow.util.hashing import sha256_file
from paperflow.util.jsonio import read_json, write_json
from tests.fixtures.make_authoring_requirements import make_authoring_requirements
from tests.fixtures.make_sample_pdf import make_sample_pdf

runner = CliRunner()
FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "paperflow 0.1.0"


def test_init_command(tmp_path) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4 dummy content\n")
    ws = tmp_path / ".work" / "test-paper"

    result = runner.invoke(app, ["init", str(pdf), str(ws)])
    assert result.exit_code == 0
    assert "Initialized:" in result.stdout
    assert "Stage: initialized" in result.stdout


def test_status_command(tmp_path) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4 dummy content\n")
    ws = tmp_path / ".work" / "test-paper"

    runner.invoke(app, ["init", str(pdf), str(ws)])

    result = runner.invoke(app, ["status", str(ws)])
    assert result.exit_code == 0
    assert "Stage: initialized" in result.stdout


def test_status_command_json(tmp_path) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4 dummy content\n")
    ws = tmp_path / ".work" / "test-paper"

    runner.invoke(app, ["init", str(pdf), str(ws)])

    result = runner.invoke(app, ["status", str(ws), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["stage"] == "initialized"
    assert len(data["source_sha256"]) == 64


def test_parse_persists_extracted_assets(tmp_path: Path) -> None:
    pdf = tmp_path / "paper.pdf"
    make_sample_pdf(pdf)
    workspace = tmp_path / ".work" / "test-paper"

    assert runner.invoke(app, ["init", str(pdf), str(workspace)]).exit_code == 0
    result = runner.invoke(app, ["parse", str(workspace)])

    assert result.exit_code == 0
    document = read_json(workspace / "source" / "parsed-document.json")
    assert document["assets"]
    assert (workspace / "assets" / "page-images" / "page-001.png").exists()


def test_parse_prefers_mineru_api_and_keeps_canonical_outputs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from paperflow.ingest.mineru_api_parser import MinerUApiParser

    pdf = tmp_path / "paper.pdf"
    make_sample_pdf(pdf)
    workspace = tmp_path / ".work" / "api-paper"

    def fake_parse(
        self: MinerUApiParser, pdf_path: Path, workspace_path: Path
    ) -> ParsedDocument:
        source_dir = workspace_path / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        markdown_path = source_dir / "parsed-paper.md"
        markdown_path.write_text(
            "API parsed text\n<!-- p01-b001 -->", encoding="utf-8"
        )
        return ParsedDocument(
            parser_name="mineru_api",
            pdf_sha256=sha256_file(pdf_path),
            page_count=1,
            markdown_path=str(markdown_path),
            blocks=[
                TextBlock(id="p01-b001", page=1, order=0, text="API parsed text")
            ],
        )

    monkeypatch.setenv("MINERU_API_KEY", "test-key")
    monkeypatch.setattr(MinerUApiParser, "parse", fake_parse)

    assert runner.invoke(app, ["init", str(pdf), str(workspace)]).exit_code == 0
    result = runner.invoke(app, ["parse", str(workspace)])

    assert result.exit_code == 0
    document = read_json(workspace / "source" / "parsed-document.json")
    assert document["parser_name"] == "mineru_api"
    assert document["blocks"][0]["id"] == "p01-b001"
    assert document["assets"]


def _parsed_requirements_workspace(tmp_path: Path) -> Path:
    pdf = tmp_path / "requirements-paper.pdf"
    make_sample_pdf(pdf)
    workspace = tmp_path / ".work" / "requirements-paper"
    assert runner.invoke(app, ["init", str(pdf), str(workspace)]).exit_code == 0
    assert runner.invoke(app, ["parse", str(workspace)]).exit_code == 0
    return workspace


def test_validate_requirements_advances_stage(tmp_path: Path) -> None:
    workspace = _parsed_requirements_workspace(tmp_path)
    manifest = load_manifest(workspace)
    write_json(
        workspace / "source" / "authoring-requirements.json",
        make_authoring_requirements(manifest.source_sha256),
    )
    result = runner.invoke(app, ["validate-requirements", str(workspace)])
    assert result.exit_code == 0
    assert "Requirements validation: PASS" in result.stdout
    assert load_manifest(workspace).stage == WorkflowStage.REQUIREMENTS_READY
    qa = read_json(workspace / "qa" / "requirements-validation.json")
    assert qa["passed"] is True


def test_validate_requirements_missing_file_keeps_parsed_stage(
    tmp_path: Path,
) -> None:
    workspace = _parsed_requirements_workspace(tmp_path)
    result = runner.invoke(app, ["validate-requirements", str(workspace)])
    assert result.exit_code == 4
    assert "REQ_FILE_MISSING" in result.stdout
    assert load_manifest(workspace).stage == WorkflowStage.PARSED
    qa = read_json(workspace / "qa" / "requirements-validation.json")
    assert qa["passed"] is False


def test_validate_requirements_digest_mismatch_keeps_parsed_stage(
    tmp_path: Path,
) -> None:
    workspace = _parsed_requirements_workspace(tmp_path)
    manifest = load_manifest(workspace)
    data = make_authoring_requirements(manifest.source_sha256)
    data["visual"]["style"] = "changed after confirmation"
    write_json(workspace / "source" / "authoring-requirements.json", data)
    result = runner.invoke(app, ["validate-requirements", str(workspace)])
    assert result.exit_code == 4
    assert "REQ_CONFIRMATION_DIGEST_MISMATCH" in result.stdout
    assert load_manifest(workspace).stage == WorkflowStage.PARSED


def test_validate_ir_rejects_parsed_stage(tmp_path: Path) -> None:
    workspace = _parsed_requirements_workspace(tmp_path)
    result = runner.invoke(app, ["validate-ir", str(workspace)])
    assert result.exit_code == 1
    assert result.exception is not None
    assert "requirements_ready" in str(result.exception)
    assert load_manifest(workspace).stage == WorkflowStage.PARSED


def test_validate_ir_accepts_requirements_ready_stage(tmp_path: Path) -> None:
    workspace = _parsed_requirements_workspace(tmp_path)
    manifest = load_manifest(workspace)
    write_json(
        workspace / "source" / "authoring-requirements.json",
        make_authoring_requirements(manifest.source_sha256),
    )
    requirements_result = runner.invoke(
        app, ["validate-requirements", str(workspace)]
    )
    assert requirements_result.exit_code == 0

    write_json(
        workspace / "source" / "paper-ir.json",
        read_json(FIXTURES / "valid-paper-ir.json"),
    )
    result = runner.invoke(app, ["validate-ir", str(workspace)])

    assert result.exit_code == 0
    assert "Paper IR valid." in result.stdout
    assert load_manifest(workspace).stage == WorkflowStage.IR_READY
