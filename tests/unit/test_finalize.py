from pathlib import Path

import pytest

from paperflow.models.common import WorkflowStage
from paperflow.qa.finalize import (
    build_final_manifest,
    create_slug,
    finalize_workspace,
)


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
