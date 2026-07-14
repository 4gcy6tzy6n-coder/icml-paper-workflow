"""Verify the SKILL.md file contains all required gates and prohibitions."""

from pathlib import Path


def _skill_text() -> str:
    skill_path = (
        Path(__file__).parent.parent.parent
        / "skills" / "icml-paper-to-report-deck" / "SKILL.md"
    )
    if not skill_path.exists():
        return ""
    return skill_path.read_text(encoding="utf-8")


def test_skill_file_exists() -> None:
    skill_path = (
        Path(__file__).parent.parent.parent
        / "skills"
        / "icml-paper-to-report-deck"
        / "SKILL.md"
    )
    assert skill_path.exists(), f"SKILL.md not found at {skill_path}"


def test_skill_contains_required_gates() -> None:
    text = _skill_text()
    required_gates = [
        "validate-ir",
        "render-report",
        "render-slides",
        "qa-content",
        "render-preview",
        "validate-visual-review",
        "finalize",
    ]
    for gate in required_gates:
        assert gate in text, f"Missing required gate: {gate}"


def test_skill_forbids_web_research() -> None:
    text = _skill_text()
    has_web = "web research" in text.lower()
    has_search = "do not search" in text.lower()
    has_no_web = "no web" in text.lower()
    assert has_web or has_search or has_no_web


def test_skill_forbids_regenerating_experimental_figures() -> None:
    text = _skill_text()
    assert (
        "regenerat" in text.lower()
        or "do not generate" in text.lower()
        or "never regenerat" in text.lower()
    )


def test_skill_forbids_unsupported_numerical_claims() -> None:
    text = _skill_text()
    assert (
        "unsupported" in text.lower()
        or "evidence" in text.lower()
    )


def test_skill_forbids_full_slide_screenshots() -> None:
    text = _skill_text()
    assert (
        "screenshot" in text.lower()
        or "full-slide" in text.lower()
        or "rasteriz" in text.lower()
    )


def test_skill_forbids_skipping_visual_qa() -> None:
    text = _skill_text()
    assert (
        "visual" in text.lower()
        and ("qa" in text.lower() or "review" in text.lower())
    )
