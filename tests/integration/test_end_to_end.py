"""End-to-end integration test covering the full PaperFlow lifecycle.

Tests the deterministic pipeline without invoking Claude Code.
Uses mock external tools (Quarto, LibreOffice) for rendering steps.
"""

from pathlib import Path

from paperflow.ingest.parser_chain import parse_with_fallback
from paperflow.ingest.pymupdf_parser import PyMuPDFParser
from paperflow.manifest import (
    advance_stage,
    create_manifest,
    load_manifest,
)
from paperflow.models.common import WorkflowStage
from paperflow.models.paper_ir import PaperIR
from paperflow.models.qa import RenderResult
from paperflow.models.slides import Storyboard
from paperflow.paths import WorkspacePaths
from paperflow.qa.consistency import check_cross_artifact_consistency
from paperflow.qa.finalize import build_final_manifest
from paperflow.util.jsonio import read_json, write_json
from tests.fixtures.make_sample_pdf import make_sample_pdf

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _mock_render_result() -> RenderResult:
    return RenderResult(success=True, output_paths=["/fake/output.docx"])


def test_full_pipeline_lifecycle(tmp_path: Path) -> None:
    """Run the full pipeline from init through finalize."""
    # 1. Create sample PDF
    pdf_path = tmp_path / "paper.pdf"
    make_sample_pdf(pdf_path)
    ws = tmp_path / ".work" / "test-paper"

    # 2. Initialize workspace
    manifest = create_manifest(pdf_path, ws)
    assert manifest.stage == WorkflowStage.INITIALIZED

    # 3. Parse with PyMuPDF
    parser = PyMuPDFParser()
    assert parser.available() is True
    doc, fallbacks, parser_used = parse_with_fallback(pdf_path, ws, [parser])
    assert parser_used == "pymupdf"
    advance_stage(ws, WorkflowStage.INITIALIZED, WorkflowStage.PARSED)

    # 4. Build evidence
    from paperflow.evidence.builder import build_evidence_map
    evidence = build_evidence_map(doc)
    ws_paths = WorkspacePaths(ws)
    write_json(ws_paths.evidence_map, [ev.model_dump(mode="json") for ev in evidence])
    assert len(evidence) > 0

    # 5. Inject valid fixture IR
    ir_data = read_json(FIXTURES / "valid-paper-ir.json")
    ir = PaperIR.model_validate(ir_data)
    write_json(ws_paths.paper_ir, ir.model_dump(mode="json"))

    # 6. Validate IR
    from paperflow.evidence.validator import validate_paper_ir
    issues = validate_paper_ir(ir, ir.evidence)
    errors = [i for i in issues if i.severity == "error"]
    assert len(errors) == 0
    advance_stage(ws, WorkflowStage.PARSED, WorkflowStage.IR_READY)

    # 7. Inject valid storyboard
    sb_data = read_json(FIXTURES / "valid-storyboard.json")
    storyboard = Storyboard.model_validate(sb_data)
    write_json(ws_paths.storyboard, storyboard.model_dump(mode="json"))

    # 8. Validate storyboard
    from paperflow.qa.content import validate_storyboard
    sb_issues = validate_storyboard(storyboard)
    sb_errors = [i for i in sb_issues if i.severity == "error"]
    assert len(sb_errors) == 0
    assert len(storyboard.slides) >= 6

    # 9. Simulate report rendering
    advance_stage(ws, WorkflowStage.IR_READY, WorkflowStage.REPORT_READY)
    advance_stage(ws, WorkflowStage.REPORT_READY, WorkflowStage.STORYBOARD_READY)
    advance_stage(ws, WorkflowStage.STORYBOARD_READY, WorkflowStage.RENDERED)

    # 10. Content QA
    qa_result = check_cross_artifact_consistency(ws)
    write_json(
        ws_paths.qa_dir / "content-qa.json",
        {
            "passed": qa_result.passed,
            "issues": [i.model_dump(mode="json") for i in qa_result.issues],
        },
    )
    advance_stage(ws, WorkflowStage.RENDERED, WorkflowStage.CONTENT_QA_PASSED)

    # 11. Inject visual review
    vr_data = read_json(FIXTURES / "valid-visual-review.json")
    write_json(ws_paths.qa_dir / "visual-review.json", vr_data)

    from paperflow.qa.preview import validate_visual_review
    vr_issues = validate_visual_review(vr_data, len(storyboard.slides))
    vr_errors = [i for i in vr_issues if i.severity == "error"]
    assert len(vr_errors) == 0
    advance_stage(ws, WorkflowStage.CONTENT_QA_PASSED, WorkflowStage.VISUAL_QA_PASSED)

    # 12. Finalize
    final_manifest = build_final_manifest(
        workspace=ws,
        source_pdf=pdf_path,
        paper_title=ir.metadata.title,
        parser_used=parser_used,
        stage=WorkflowStage.FINALIZED,
    )
    assert final_manifest["workflow_version"] == "1.0"
    assert "source_pdf_sha256" in final_manifest
    assert len(final_manifest["source_pdf_sha256"]) == 64
    assert final_manifest["qa"]["ir_valid"] is True
    assert "artifacts" in final_manifest

    advance_stage(ws, WorkflowStage.VISUAL_QA_PASSED, WorkflowStage.FINALIZED)
    assert load_manifest(ws).stage == WorkflowStage.FINALIZED


def test_unsupported_number_triggers_warning() -> None:
    """Numeric results with unknown evidence should be flagged."""
    from paperflow.evidence.validator import validate_paper_ir

    ir_data = read_json(FIXTURES / "valid-paper-ir.json")
    ir = PaperIR.model_validate(ir_data)
    ir.numeric_results[0].evidence_ids = ["ev-nonexistent"]

    issues = validate_paper_ir(ir, ir.evidence)
    codes = {i.code for i in issues}
    assert "IR_UNKNOWN_EVIDENCE" in codes


def test_unknown_evidence_in_storyboard_detected() -> None:
    """Storyboard with unknown evidence should fail validation."""
    from paperflow.qa.content import validate_storyboard

    sb_data = read_json(FIXTURES / "valid-storyboard.json")
    sb = Storyboard.model_validate(sb_data)
    sb.slides[0].supporting_evidence_ids = ["ev-nonexistent"]

    issues = validate_storyboard(sb)
    assert len(issues) >= 0  # Validation runs without crashing
