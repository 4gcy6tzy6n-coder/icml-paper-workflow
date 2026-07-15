import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from paperflow.cli import app
from paperflow.manifest import load_manifest
from paperflow.models.authoring_requirements import compute_requirements_digest
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


def _build_evidence(workspace: Path) -> None:
    result = runner.invoke(app, ["build-evidence", str(workspace)])
    assert result.exit_code == 0, result.stdout


def _requirements_ready_workspace(tmp_path: Path) -> Path:
    workspace = _parsed_requirements_workspace(tmp_path)
    _build_evidence(workspace)
    manifest = load_manifest(workspace)
    write_json(
        workspace / "source" / "authoring-requirements.json",
        make_authoring_requirements(manifest.source_sha256),
    )
    result = runner.invoke(app, ["validate-requirements", str(workspace)])
    assert result.exit_code == 0, result.stdout
    return workspace


def test_validate_requirements_advances_stage(tmp_path: Path) -> None:
    workspace = _parsed_requirements_workspace(tmp_path)
    _build_evidence(workspace)
    manifest = load_manifest(workspace)
    write_json(
        workspace / "source" / "authoring-requirements.json",
        make_authoring_requirements(manifest.source_sha256),
    )
    result = runner.invoke(app, ["validate-requirements", str(workspace)])
    assert result.exit_code == 0
    assert "Requirements validation: PASS" in result.stdout
    sealed_manifest = load_manifest(workspace)
    assert sealed_manifest.stage == WorkflowStage.REQUIREMENTS_READY
    assert (
        sealed_manifest.validated_requirements_content_sha256
        == read_json(workspace / "source" / "authoring-requirements.json")[
            "confirmation"
        ]["content_sha256"]
    )
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
    _build_evidence(workspace)
    manifest = load_manifest(workspace)
    data = make_authoring_requirements(manifest.source_sha256)
    data["visual"]["style"] = "changed after confirmation"
    write_json(workspace / "source" / "authoring-requirements.json", data)
    result = runner.invoke(app, ["validate-requirements", str(workspace)])
    assert result.exit_code == 4
    assert "REQ_CONFIRMATION_DIGEST_MISMATCH" in result.stdout
    assert load_manifest(workspace).stage == WorkflowStage.PARSED


def test_validate_requirements_requires_evidence_outputs(tmp_path: Path) -> None:
    workspace = _parsed_requirements_workspace(tmp_path)
    manifest = load_manifest(workspace)
    write_json(
        workspace / "source" / "authoring-requirements.json",
        make_authoring_requirements(manifest.source_sha256),
    )

    result = runner.invoke(app, ["validate-requirements", str(workspace)])

    assert result.exit_code == 4
    assert "build-evidence" in result.stdout
    assert "REQ_EVIDENCE" in result.stdout
    assert load_manifest(workspace).stage == WorkflowStage.PARSED


def test_validate_ir_rejects_parsed_stage(tmp_path: Path) -> None:
    workspace = _parsed_requirements_workspace(tmp_path)
    result = runner.invoke(app, ["validate-ir", str(workspace)])
    assert result.exit_code == 1
    assert result.exception is not None
    assert "requirements_ready" in str(result.exception)
    assert load_manifest(workspace).stage == WorkflowStage.PARSED


def test_validate_ir_accepts_requirements_ready_stage(tmp_path: Path) -> None:
    workspace = _requirements_ready_workspace(tmp_path)

    write_json(
        workspace / "source" / "paper-ir.json",
        read_json(FIXTURES / "valid-paper-ir.json"),
    )
    result = runner.invoke(app, ["validate-ir", str(workspace)])

    assert result.exit_code == 0
    assert "Paper IR valid." in result.stdout
    assert load_manifest(workspace).stage == WorkflowStage.IR_READY


def _write_valid_ir(workspace: Path) -> None:
    write_json(
        workspace / "source" / "paper-ir.json",
        read_json(FIXTURES / "valid-paper-ir.json"),
    )


def test_validate_ir_rejects_valid_but_edited_requirements(tmp_path: Path) -> None:
    workspace = _requirements_ready_workspace(tmp_path)
    _write_valid_ir(workspace)
    path = workspace / "source" / "authoring-requirements.json"
    data = read_json(path)
    data["visual"]["style"] = "newly reconfirmed but not workflow-validated"
    data["confirmation"]["content_sha256"] = compute_requirements_digest(data)
    write_json(path, data)

    result = runner.invoke(app, ["validate-ir", str(workspace)])

    assert result.exit_code == 4
    assert "REQ_VALIDATED_DIGEST_MISMATCH" in result.stdout
    assert load_manifest(workspace).stage == WorkflowStage.REQUIREMENTS_READY


def test_validate_ir_rejects_deleted_requirements(tmp_path: Path) -> None:
    workspace = _requirements_ready_workspace(tmp_path)
    _write_valid_ir(workspace)
    (workspace / "source" / "authoring-requirements.json").unlink()

    result = runner.invoke(app, ["validate-ir", str(workspace)])

    assert result.exit_code == 4
    assert "REQ_FILE_MISSING" in result.stdout
    assert load_manifest(workspace).stage == WorkflowStage.REQUIREMENTS_READY


def test_validate_ir_rejects_malformed_requirements(tmp_path: Path) -> None:
    workspace = _requirements_ready_workspace(tmp_path)
    _write_valid_ir(workspace)
    (workspace / "source" / "authoring-requirements.json").write_text(
        "{", encoding="utf-8"
    )

    result = runner.invoke(app, ["validate-ir", str(workspace)])

    assert result.exit_code == 4
    assert "REQ_JSON_INVALID" in result.stdout
    assert load_manifest(workspace).stage == WorkflowStage.REQUIREMENTS_READY


def test_validate_ir_rejects_wrong_pdf_requirements_substitution(tmp_path: Path) -> None:
    workspace = _requirements_ready_workspace(tmp_path)
    _write_valid_ir(workspace)
    write_json(
        workspace / "source" / "authoring-requirements.json",
        make_authoring_requirements("b" * 64),
    )

    result = runner.invoke(app, ["validate-ir", str(workspace)])

    assert result.exit_code == 4
    assert "REQ_SOURCE_MISMATCH" in result.stdout
    assert load_manifest(workspace).stage == WorkflowStage.REQUIREMENTS_READY


def test_failed_revalidation_keeps_existing_requirements_seal(tmp_path: Path) -> None:
    workspace = _requirements_ready_workspace(tmp_path)
    original = load_manifest(workspace).validated_requirements_content_sha256
    path = workspace / "source" / "authoring-requirements.json"
    data = read_json(path)
    data["visual"]["style"] = "edited without confirmation"
    write_json(path, data)

    result = runner.invoke(app, ["validate-requirements", str(workspace)])

    assert result.exit_code == 4
    manifest = load_manifest(workspace)
    assert manifest.stage == WorkflowStage.REQUIREMENTS_READY
    assert manifest.validated_requirements_content_sha256 == original


@pytest.mark.parametrize(
    ("command", "stage"),
    [
        ("validate-ir", WorkflowStage.REQUIREMENTS_READY),
        ("scaffold-report", WorkflowStage.IR_READY),
        ("validate-report", WorkflowStage.IR_READY),
        ("render-report", WorkflowStage.REPORT_READY),
        ("validate-storyboard", WorkflowStage.REPORT_READY),
        ("render-slides", WorkflowStage.STORYBOARD_READY),
        ("qa-content", WorkflowStage.RENDERED),
        ("render-preview", WorkflowStage.CONTENT_QA_PASSED),
        ("validate-visual-review", WorkflowStage.CONTENT_QA_PASSED),
        ("finalize", WorkflowStage.VISUAL_QA_PASSED),
    ],
)
def test_every_downstream_boundary_revalidates_requirements(
    tmp_path: Path, command: str, stage: WorkflowStage
) -> None:
    workspace = _requirements_ready_workspace(tmp_path)
    manifest_path = workspace / "manifest.json"
    manifest_data = read_json(manifest_path)
    manifest_data["stage"] = stage.value
    write_json(manifest_path, manifest_data)
    (workspace / "source" / "authoring-requirements.json").unlink()

    result = runner.invoke(app, [command, str(workspace)])

    assert result.exit_code == 4
    assert "REQ_FILE_MISSING" in result.stdout


def test_render_slides_does_not_forward_pnpm_separator_as_workspace(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from paperflow.util.commands import CommandResult

    workspace = _requirements_ready_workspace(tmp_path)
    manifest_path = workspace / "manifest.json"
    manifest = read_json(manifest_path)
    manifest["stage"] = WorkflowStage.STORYBOARD_READY.value
    write_json(manifest_path, manifest)

    captured: list[str] = []

    def fake_run_command(
        args: list[str], cwd: Path | None = None, timeout_s: int = 600
    ) -> CommandResult:
        del cwd, timeout_s
        captured.extend(args)
        (workspace / "slides" / "presentation.pptx").write_bytes(b"pptx")
        (workspace / "slides" / "speaker-notes.md").write_text(
            "notes", encoding="utf-8"
        )
        return CommandResult(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("paperflow.util.commands.run_command", fake_run_command)

    result = runner.invoke(app, ["render-slides", str(workspace)])

    assert result.exit_code == 0, result.stdout
    assert captured == ["pnpm", "paperflow:render-slides", str(workspace)]


def _write_report_pdf(path: Path, pages: int) -> None:
    import fitz

    document = fitz.open()
    for _ in range(pages):
        document.new_page()
    document.save(path)
    document.close()


def test_off_target_content_qa_supports_report_correction_and_rerender(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from paperflow.models.qa import RenderResult

    workspace = _requirements_ready_workspace(tmp_path)
    requirements_path = workspace / "source" / "authoring-requirements.json"
    requirements = read_json(requirements_path)
    requirements["report"]["target_chinese_characters"] = {
        "minimum": 1,
        "maximum": 20,
    }
    requirements["report"]["target_pages"] = {"minimum": 2, "maximum": 2}
    requirements["confirmation"]["content_sha256"] = compute_requirements_digest(
        requirements
    )
    write_json(requirements_path, requirements)
    assert (
        runner.invoke(app, ["validate-requirements", str(workspace)]).exit_code == 0
    )

    _write_valid_ir(workspace)
    write_json(
        workspace / "slides" / "storyboard.json",
        read_json(FIXTURES / "valid-storyboard.json"),
    )
    (workspace / "report" / "academic-report.qmd").write_text(
        "# 中文报告", encoding="utf-8"
    )
    _write_report_pdf(workspace / "report" / "academic-report.pdf", 1)
    manifest_path = workspace / "manifest.json"
    manifest = read_json(manifest_path)
    manifest["stage"] = WorkflowStage.RENDERED.value
    write_json(manifest_path, manifest)

    failed_qa = runner.invoke(app, ["qa-content", str(workspace)])
    assert failed_qa.exit_code == 4
    assert "REPORT_PAGE_TARGET_MISSED" in failed_qa.stdout
    assert load_manifest(workspace).stage == WorkflowStage.RENDERED

    def corrected_render(_: Path) -> RenderResult:
        _write_report_pdf(workspace / "report" / "academic-report.pdf", 2)
        return RenderResult(success=True, output_paths=["academic-report.pdf"])

    monkeypatch.setattr("paperflow.report.renderer.render_report", corrected_render)
    rerender = runner.invoke(app, ["render-report", str(workspace)])
    assert rerender.exit_code == 0, rerender.stdout
    assert load_manifest(workspace).stage == WorkflowStage.RENDERED

    corrected_qa = runner.invoke(app, ["qa-content", str(workspace)])
    assert corrected_qa.exit_code == 0, corrected_qa.stdout
    assert load_manifest(workspace).stage == WorkflowStage.CONTENT_QA_PASSED


def test_finalize_cli_rejects_arbitrary_dist_override(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["finalize", str(tmp_path / "workspace"), "--dist", str(tmp_path / "custom")],
    )

    assert result.exit_code == 2
    help_result = runner.invoke(app, ["finalize", "--help"])
    assert help_result.exit_code == 0
    assert "--dist" not in help_result.stdout
