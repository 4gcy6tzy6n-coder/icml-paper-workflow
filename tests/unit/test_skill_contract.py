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


def _requirements_reference_text() -> str:
    path = (
        Path(__file__).parent.parent.parent
        / "skills"
        / "icml-paper-to-report-deck"
        / "references"
        / "requirements-intake.md"
    )
    return path.read_text(encoding="utf-8") if path.exists() else ""


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
        "validate-requirements",
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


def test_skill_requires_authoring_intake_gate() -> None:
    text = _skill_text().lower()
    assert "requirements-intake.md" in text
    assert "validate-requirements" in text
    assert "authoring-requirements.json" in text
    assert text.index("validate-requirements") < text.index("validate-ir")


def test_intake_reference_has_required_behavior() -> None:
    text = _requirements_reference_text().lower()
    phrases = [
        "one question at a time",
        "adaptive follow-up",
        "explicit confirmation",
        "do not author",
        "content_sha256",
        "pdf_sha256",
        "never request or persist",
        "do not write a markdown requirements copy",
    ]
    for phrase in phrases:
        assert phrase in text


def test_intake_reference_covers_all_core_topics() -> None:
    text = _requirements_reference_text().lower()
    topics = [
        "use scenario",
        "target audience",
        "report",
        "presentation",
        "content priorities",
        "technical depth",
        "language",
        "visual",
        "template",
        "evidence",
    ]
    for topic in topics:
        assert topic in text


def test_intake_reference_closes_pressure_bypasses() -> None:
    text = _requirements_reference_text().lower()
    pressure_terms = [
        "urgency",
        "defaults",
        "ambiguity",
        "resume state",
        "skip questions",
    ]
    for term in pressure_terms:
        assert term in text
    assert "one question at a time" in text
    assert "explicit confirmation" in text
