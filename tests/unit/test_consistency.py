from paperflow.models.paper_ir import (
    Contribution,
    EvidenceRef,
    NumericResult,
)
from paperflow.qa.consistency import (
    check_contribution_consistency,
    check_numeric_alignment,
    check_placeholders,
)


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
