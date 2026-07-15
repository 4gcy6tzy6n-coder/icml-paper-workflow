from pathlib import Path

import fitz

from paperflow.models.authoring_requirements import compute_requirements_digest
from paperflow.models.paper_ir import (
    Contribution,
    EvidenceRef,
    NumericResult,
)
from paperflow.qa.consistency import (
    check_contribution_consistency,
    check_cross_artifact_consistency,
    check_numeric_alignment,
    check_placeholders,
)
from paperflow.util.jsonio import read_json, write_json
from tests.fixtures.make_authoring_requirements import make_authoring_requirements

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _sample_evidence() -> list[EvidenceRef]:
    return [
        EvidenceRef(
            id="ev-p01-b001",
            page=1,
            block_id="p01-b001",
            source_text="Method A improves accuracy.",
        ),
        EvidenceRef(
            id="ev-p01-b002",
            page=1,
            block_id="p01-b002",
            source_text="Accuracy: 87.4%.",
        ),
    ]


def _sample_contributions() -> list[Contribution]:
    return [
        Contribution(
            id="c-1",
            statement="A novel attention mechanism.",
            evidence_ids=["ev-p01-b001"],
        ),
    ]


def _sample_results() -> list[NumericResult]:
    return [
        NumericResult(
            id="nr-1",
            metric="Accuracy",
            value_text="87.4%",
            direction="higher_better",
            evidence_ids=["ev-p01-b002"],
        ),
    ]


def test_contribution_check_passes_for_match() -> None:
    issues = check_contribution_consistency(
        _sample_contributions(),
        ["novel attention"],
    )
    errors = [i for i in issues if i.severity == "error"]
    assert len(errors) == 0


def test_contribution_check_detects_missing_keyword() -> None:
    issues = check_contribution_consistency(
        _sample_contributions(),
        ["parallel training"],
    )
    codes = {i.code for i in issues}
    assert "CONTRIBUTION_KEYWORD_MISMATCH" in codes


def test_numeric_alignment_passes() -> None:
    issues = check_numeric_alignment(
        _sample_results(),
        {"Accuracy"},
    )
    errors = [i for i in issues if i.severity == "error"]
    assert len(errors) == 0


def test_numeric_alignment_detects_missing_metric() -> None:
    issues = check_numeric_alignment(
        _sample_results(),
        {"F1 Score"},
    )
    codes = {i.code for i in issues}
    assert "METRIC_MISMATCH" in codes


def test_placeholder_scanner_finds_todos() -> None:
    text = "This is a TODO item that needs fixing."
    issues = check_placeholders(text, "test-section")
    assert len(issues) > 0
    assert any(i.code == "REPORT_PLACEHOLDER_TEXT" for i in issues)


def test_placeholder_scanner_passes_clean_text() -> None:
    text = "This is a clean paragraph with no placeholders."
    issues = check_placeholders(text, "test-section")
    assert len(issues) == 0


def _workspace_with_missed_confirmed_targets(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    source = workspace / "source"
    report = workspace / "report"
    slides = workspace / "slides"
    source.mkdir(parents=True)
    report.mkdir()
    slides.mkdir()

    write_json(source / "paper-ir.json", read_json(FIXTURES / "valid-paper-ir.json"))
    requirements = make_authoring_requirements("a" * 64)
    requirements["report"]["target_chinese_characters"] = {
        "minimum": 100,
        "maximum": 120,
    }
    requirements["report"]["target_pages"] = {"minimum": 2, "maximum": 3}
    requirements["presentation"]["target_slides"] = {
        "minimum": 7,
        "maximum": 8,
    }
    requirements["confirmation"]["content_sha256"] = compute_requirements_digest(
        requirements
    )
    write_json(source / "authoring-requirements.json", requirements)

    (report / "academic-report.qmd").write_text(
        "# 标题\n\n只有少量中文。", encoding="utf-8"
    )
    pdf = fitz.open()
    pdf.new_page()
    pdf.save(report / "academic-report.pdf")
    pdf.close()
    write_json(slides / "storyboard.json", read_json(FIXTURES / "valid-storyboard.json"))
    return workspace


def test_content_qa_enforces_confirmed_report_character_target(tmp_path: Path) -> None:
    result = check_cross_artifact_consistency(
        _workspace_with_missed_confirmed_targets(tmp_path)
    )
    issue = next(
        item for item in result.issues if item.code == "REPORT_CHARACTER_TARGET_MISSED"
    )
    assert issue.severity == "error"
    assert "confirmed target 100–120" in issue.message


def test_content_qa_enforces_confirmed_report_page_target(tmp_path: Path) -> None:
    result = check_cross_artifact_consistency(
        _workspace_with_missed_confirmed_targets(tmp_path)
    )
    issue = next(item for item in result.issues if item.code == "REPORT_PAGE_TARGET_MISSED")
    assert issue.severity == "error"
    assert "confirmed target 2–3" in issue.message


def test_content_qa_enforces_confirmed_presentation_slide_target(tmp_path: Path) -> None:
    result = check_cross_artifact_consistency(
        _workspace_with_missed_confirmed_targets(tmp_path)
    )
    issue = next(
        item for item in result.issues if item.code == "PRESENTATION_SLIDE_TARGET_MISSED"
    )
    assert issue.severity == "error"
    assert "confirmed target 7–8" in issue.message


def test_content_qa_requires_rendered_report_pdf(tmp_path: Path) -> None:
    workspace = _workspace_with_missed_confirmed_targets(tmp_path)
    (workspace / "report" / "academic-report.pdf").unlink()

    result = check_cross_artifact_consistency(workspace)

    issue = next(item for item in result.issues if item.code == "REPORT_PDF_MISSING")
    assert issue.severity == "error"
    assert "render-report" in issue.message
