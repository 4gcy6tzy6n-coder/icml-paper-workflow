from pathlib import Path

import pytest

from paperflow.errors import InvalidStageError
from paperflow.manifest import (
    advance_stage,
    create_manifest,
    load_manifest,
)
from paperflow.models.common import WorkflowStage


def test_create_and_load_manifest(tmp_path: Path) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4 dummy content\n")
    ws = tmp_path / ".work" / "test-paper"

    manifest = create_manifest(pdf, ws)
    assert manifest.stage == WorkflowStage.INITIALIZED
    assert manifest.source_pdf == str(pdf.resolve())
    assert len(manifest.source_sha256) == 64


def test_advance_allowed_transition(tmp_path: Path) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4 dummy content\n")
    ws = tmp_path / ".work" / "test-paper"

    create_manifest(pdf, ws)

    updated = advance_stage(ws, WorkflowStage.INITIALIZED, WorkflowStage.PARSED)
    assert updated.stage == WorkflowStage.PARSED


def test_advance_forbidden_transition_leaves_manifest_unchanged(tmp_path: Path) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4 dummy content\n")
    ws = tmp_path / ".work" / "test-paper"

    create_manifest(pdf, ws)
    original = load_manifest(ws)

    with pytest.raises(InvalidStageError):
        advance_stage(ws, WorkflowStage.INITIALIZED, WorkflowStage.IR_READY)

    reloaded = load_manifest(ws)
    assert reloaded.stage == original.stage
    assert reloaded.source_sha256 == original.source_sha256


def test_advance_wrong_expected_stage_fails(tmp_path: Path) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4 dummy content\n")
    ws = tmp_path / ".work" / "test-paper"

    create_manifest(pdf, ws)

    with pytest.raises(InvalidStageError):
        advance_stage(ws, WorkflowStage.PARSED, WorkflowStage.IR_READY)


def test_full_transition_chain(tmp_path: Path) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4 dummy content\n")
    ws = tmp_path / ".work" / "test-paper"

    create_manifest(pdf, ws)
    transitions = [
        (WorkflowStage.INITIALIZED, WorkflowStage.PARSED),
        (WorkflowStage.PARSED, WorkflowStage.REQUIREMENTS_READY),
        (WorkflowStage.REQUIREMENTS_READY, WorkflowStage.IR_READY),
        (WorkflowStage.IR_READY, WorkflowStage.REPORT_READY),
        (WorkflowStage.REPORT_READY, WorkflowStage.STORYBOARD_READY),
        (WorkflowStage.STORYBOARD_READY, WorkflowStage.RENDERED),
        (WorkflowStage.RENDERED, WorkflowStage.CONTENT_QA_PASSED),
        (WorkflowStage.CONTENT_QA_PASSED, WorkflowStage.VISUAL_QA_PASSED),
        (WorkflowStage.VISUAL_QA_PASSED, WorkflowStage.FINALIZED),
    ]
    for expected, target in transitions:
        result = advance_stage(ws, expected, target)
        assert result.stage == target
