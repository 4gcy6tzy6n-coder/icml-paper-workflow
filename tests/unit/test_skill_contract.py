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


def _expected_session_text() -> str:
    path = (
        Path(__file__).parent.parent.parent
        / "skills"
        / "icml-paper-to-report-deck"
        / "examples"
        / "expected-session.md"
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


def test_intake_reference_maps_every_schema_field_and_execution_step() -> None:
    text = _requirements_reference_text()
    fields = [
        "schema_version",
        "source.pdf_sha256",
        "source.title",
        "use_case.scenario",
        "use_case.desired_outcome",
        "use_case.audience.role",
        "use_case.audience.background",
        "use_case.audience.subject_familiarity",
        "report.required",
        "report.purpose",
        "report.target_pages",
        "report.target_chinese_characters",
        "report.formats",
        "report.focus_topics",
        "report.de_emphasized_topics",
        "report.technical_depth",
        "report.narrative_preference",
        "report.reading_context",
        "presentation.required",
        "presentation.purpose",
        "presentation.duration_minutes",
        "presentation.target_slides",
        "presentation.formats",
        "presentation.focus_topics",
        "presentation.speaker_notes_required",
        "presentation.speaking_context",
        "language.locale",
        "language.preserve_english_terms",
        "language.translation_preferences",
        "visual.style",
        "visual.template_path",
        "visual.brand_requirements",
        "visual.accessibility_requirements",
        "evidence_policy.allow_web_research",
        "evidence_policy.allow_generated_result_figures",
        "evidence_policy.prefer_original_figures",
        "evidence_policy.citation_expectations",
        "deliverables.formats",
        "deliverables.output_location",
        "deliverables.naming_requirements",
        "user_constraints",
        "assumptions",
        "confirmation.status",
        "confirmation.confirmed_at",
        "confirmation.content_sha256",
    ]
    for field in fields:
        assert field in text, f"Missing schema mapping: {field}"
    ordered_steps = [
        "build-evidence",
        "complete summary",
        "explicit confirmation",
        "compute_requirements_digest",
        "authoring-requirements.json",
        "validate-requirements",
        "same-PDF resume validation",
    ]
    positions: list[int] = []
    cursor = 0
    for step in ordered_steps:
        position = text.find(step, cursor)
        assert position >= 0, f"Missing ordered step: {step}"
        positions.append(position)
        cursor = position + len(step)
    assert positions == sorted(positions)
    assert "If " in text and "then ask" in text


def test_expected_session_demonstrates_complete_intake_before_ir() -> None:
    text = _expected_session_text()
    ordered_markers = [
        "build-evidence",
        "Field-level intake",
        "Complete summary",
        "Explicit confirmation",
        "compute_requirements_digest",
        "authoring-requirements.json",
        "validate-requirements",
        "Stage: requirements_ready",
        "Paper IR Authoring",
    ]
    positions = [text.find(marker) for marker in ordered_markers]
    assert all(position >= 0 for position in positions)
    assert positions == sorted(positions)
    assert "same-PDF resume validation" in text


def test_skill_uses_confirmed_targets_instead_of_fixed_authoring_mandates() -> None:
    root = Path(__file__).parent.parent.parent / "skills" / "icml-paper-to-report-deck"
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    report = (root / "references" / "report-style.md").read_text(encoding="utf-8")
    slides = (root / "references" / "slide-storytelling.md").read_text(encoding="utf-8")
    combined = f"{skill}\n{report}\n{slides}"
    assert "confirmed report.target_chinese_characters" in combined
    assert "confirmed report.target_pages" in combined
    assert "confirmed presentation.target_slides" in combined
    assert "confirmed presentation.duration_minutes" in combined
    assert "Target 7,000–10,000" not in combined
    assert "13–15 slides for a 15-minute talk" not in combined


def test_skill_supports_confirmed_non_graduate_audience() -> None:
    root = Path(__file__).parent.parent.parent / "skills" / "icml-paper-to-report-deck"
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            root / "SKILL.md",
            root / "references" / "report-style.md",
            root / "references" / "slide-storytelling.md",
        )
    ).lower()
    assert "confirmed use_case.audience" in combined
    assert "do not assume a graduate-student audience" in combined


def test_skill_respects_false_preserve_english_terms() -> None:
    text = _skill_text().lower()
    assert "if language.preserve_english_terms is false" in text
    assert "follow language.translation_preferences" in text


def test_skill_subordinates_palette_to_confirmed_visual_direction() -> None:
    root = Path(__file__).parent.parent.parent / "skills" / "icml-paper-to-report-deck"
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            root / "SKILL.md",
            root / "references" / "report-style.md",
            root / "references" / "slide-storytelling.md",
        )
    ).lower()
    assert "confirmed visual.style" in combined
    assert "palette is only a recommendation" in combined
    assert "confirmed visual direction takes precedence" in combined
