"""Verify golden paper expectation files are valid and scoring works."""

from pathlib import Path

import yaml

from paperflow.qa.golden import (
    GoldenScore,
    score_cross_artifact_consistency,
    score_deck_structure,
    score_evidence_traceability,
    score_paper_ir_coverage,
    score_report_completeness,
    score_visual_qa,
)

GOLDEN_DIR = Path(__file__).parent.parent / "golden"


def test_expectation_files_exist() -> None:
    expectations = GOLDEN_DIR / "expectations"
    yaml_files = list(expectations.glob("*.yaml"))
    assert len(yaml_files) == 3, f"Expected 3 golden expectations, found {len(yaml_files)}"


def test_expectation_files_are_valid_yaml() -> None:
    expectations = GOLDEN_DIR / "expectations"
    for yf in expectations.glob("*.yaml"):
        data = yaml.safe_load(yf.read_text(encoding="utf-8"))
        assert "expected" in data
        assert "quality_targets" in data
        assert "source_pdf_sha256" in data


def test_golden_score_perfect_paper() -> None:
    score = GoldenScore(
        paper_label="test",
        paper_ir_coverage=35.0,
        evidence_traceability=20.0,
        report_completeness=15.0,
        deck_story_structure=10.0,
        cross_artifact_consistency=10.0,
        visual_qa_editability=10.0,
    )
    assert score.total == 100.0
    assert score.passed is True


def test_golden_score_borderline() -> None:
    score = GoldenScore(
        paper_label="test",
        paper_ir_coverage=30.0,
        evidence_traceability=17.0,
        report_completeness=13.0,
        deck_story_structure=8.0,
        cross_artifact_consistency=8.0,
        visual_qa_editability=8.0,
    )
    assert score.total == 84.0
    assert score.passed is False


def test_scoring_functions_produce_valid_range() -> None:
    cov = score_paper_ir_coverage(True, 1.0)
    assert 0 <= cov <= 35

    ev = score_evidence_traceability(50, 25)
    assert 0 <= ev <= 20

    rep = score_report_completeness(16)
    assert 0 <= rep <= 15

    deck = score_deck_structure(14)
    assert 0 <= deck <= 10

    cross = score_cross_artifact_consistency(True, True, True)
    assert 0 <= cross <= 10

    vis = score_visual_qa(True, 1)
    assert 0 <= vis <= 10
