from pathlib import Path

import fitz
import pytest

from paperflow.models.authoring_requirements import compute_requirements_digest
from paperflow.models.common import WorkflowStage
from paperflow.qa.finalize import (
    build_final_manifest,
    create_slug,
    finalize_workspace,
)
from paperflow.util.jsonio import read_json, write_json
from tests.fixtures.make_authoring_requirements import make_authoring_requirements

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_create_slug_from_english_title() -> None:
    slug = create_slug("Attention Is All You Need")
    assert slug == "attention-is-all-you-need"


def test_create_slug_limits_length() -> None:
    long_title = "A" * 200
    slug = create_slug(long_title)
    assert len(slug) <= 80


def test_finalize_fails_on_missing_artifacts(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "source").mkdir()
    (ws / "report").mkdir()
    (ws / "slides").mkdir()
    (ws / "qa").mkdir()

    with pytest.raises(FileNotFoundError):
        finalize_workspace(ws, tmp_path / "dist")


def test_build_final_manifest_includes_checksums(tmp_path: Path) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    manifest = build_final_manifest(
        workspace=tmp_path,
        source_pdf=pdf,
        paper_title="Test Paper",
        parser_used="pymupdf",
        stage=WorkflowStage.FINALIZED,
    )
    assert manifest["workflow_version"] == "1.0"
    assert "source_pdf_sha256" in manifest
    assert len(manifest["source_pdf_sha256"]) == 64


def test_build_final_manifest_records_visual_fix_cycle_count(tmp_path: Path) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    (tmp_path / "qa").mkdir()
    write_json(
        tmp_path / "qa" / "visual-review.json",
        {
            "schema_version": "1.0",
            "inspection_pass": 2,
            "reviewed_slide_count": 11,
            "issues": [],
            "fixes_applied": ["layout correction"],
            "rerendered": True,
            "final_pass": True,
        },
    )

    manifest = build_final_manifest(
        workspace=tmp_path,
        source_pdf=pdf,
        paper_title="Test Paper",
        parser_used="pymupdf",
        stage=WorkflowStage.FINALIZED,
    )

    assert manifest["qa"]["visual_fix_cycle_count"] == 2


def test_finalize_copies_sealed_requirements_and_audits_them(tmp_path: Path) -> None:
    ws = _complete_workspace_with_report_pages(
        tmp_path,
        target_pages=(1, 1),
        actual_pages=1,
    )
    requirements = read_json(ws / "source" / "authoring-requirements.json")

    outputs = finalize_workspace(ws, tmp_path / "dist")
    output_root = next(path.parent.parent for path in outputs if path.name == "final-manifest.json")

    assert (output_root / "source" / "authoring-requirements.json").exists()
    final = read_json(output_root / "qa" / "final-manifest.json")
    assert output_root == tmp_path / "dist" / "test-paper"
    assert final["paper_title"] == "Test Paper"
    assert final["requirements"] == {
        "content_sha256": requirements["confirmation"]["content_sha256"],
        "valid": True,
    }


def test_finalize_copies_optional_report_reference_doc(tmp_path: Path) -> None:
    ws = _complete_workspace_with_report_pages(
        tmp_path,
        target_pages=(1, 1),
        actual_pages=1,
    )
    reference_doc = ws / "report" / "compact-reference.docx"
    reference_doc.write_bytes(b"reference-doc")

    outputs = finalize_workspace(ws, tmp_path / "dist")
    output_root = next(
        path.parent.parent for path in outputs if path.name == "final-manifest.json"
    )

    copied = output_root / "report" / "compact-reference.docx"
    assert copied.read_bytes() == b"reference-doc"
    final = read_json(output_root / "qa" / "final-manifest.json")
    assert "report/compact-reference.docx" in final["artifacts"]


def _complete_workspace_with_report_pages(
    tmp_path: Path,
    *,
    target_pages: tuple[int, int],
    actual_pages: int,
) -> Path:
    ws = tmp_path / "finalization-workspace"
    for directory in ("source", "report", "slides", "qa"):
        (ws / directory).mkdir(parents=True, exist_ok=True)
    (ws / "source" / "input.pdf").write_bytes(b"%PDF-1.4")
    requirements = make_authoring_requirements("a" * 64)
    requirements["report"]["target_pages"] = {
        "minimum": target_pages[0],
        "maximum": target_pages[1],
    }
    requirements["report"]["target_chinese_characters"] = {
        "minimum": 1,
        "maximum": 20,
    }
    requirements["confirmation"]["content_sha256"] = compute_requirements_digest(
        requirements
    )
    write_json(ws / "source" / "authoring-requirements.json", requirements)
    write_json(
        ws / "manifest.json",
        {
            "workflow_version": "1.0",
            "stage": "visual_qa_passed",
            "source_pdf": "paper.pdf",
            "source_sha256": "a" * 64,
            "validated_requirements_content_sha256": requirements["confirmation"][
                "content_sha256"
            ],
            "workspace": str(ws),
            "config": {},
        },
    )
    (ws / "report" / "academic-report.qmd").write_text("# 中文报告", encoding="utf-8")
    (ws / "report" / "academic-report.docx").write_bytes(b"docx")
    report_pdf = fitz.open()
    for _ in range(actual_pages):
        report_pdf.new_page()
    report_pdf.save(ws / "report" / "academic-report.pdf")
    report_pdf.close()
    (ws / "slides" / "presentation.pptx").write_bytes(b"pptx")
    (ws / "slides" / "presentation.pdf").write_bytes(b"pdf")
    (ws / "slides" / "speaker-notes.md").write_text("notes", encoding="utf-8")
    write_json(
        ws / "slides" / "storyboard.json",
        read_json(FIXTURES / "valid-storyboard.json"),
    )
    return ws


def test_finalize_rejects_off_target_report_pdf(tmp_path: Path) -> None:
    workspace = _complete_workspace_with_report_pages(
        tmp_path,
        target_pages=(2, 2),
        actual_pages=1,
    )

    with pytest.raises(ValueError, match="REPORT_PAGE_TARGET_MISSED"):
        finalize_workspace(workspace, tmp_path / "dist")
