from paperflow.models.authoring_requirements import PositiveRange
from paperflow.models.common import Severity
from paperflow.models.qa import ValidationIssue
from paperflow.models.slides import Storyboard

_NON_ASSERTION_TITLES = {
    "Introduction", "Related Work", "Method", "Methods",
    "Experiments", "Results", "Conclusion",
    "引言", "相关工作", "方法", "实验", "结果", "结论",
}


def validate_storyboard(
    storyboard: Storyboard,
    target_slides: PositiveRange | None = None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    _check_slide_count(storyboard, issues, target_slides)
    _check_duplicate_ids(storyboard, issues)
    _check_body_lines(storyboard, issues)
    _check_notes_and_footer(storyboard, issues)

    return issues


def _check_slide_count(
    storyboard: Storyboard,
    issues: list[ValidationIssue],
    target_slides: PositiveRange | None,
) -> None:
    count = len(storyboard.slides)
    if count < 6 or count > 40:
        issues.append(
            ValidationIssue(
                code="SLIDES_COUNT_OUT_OF_RANGE",
                severity=Severity.ERROR,
                message=f"Slide count {count} is out of allowed range (6–40).",
            )
        )
    if target_slides is not None and not (
        target_slides.minimum <= count <= target_slides.maximum
    ):
        issues.append(
            ValidationIssue(
                code="PRESENTATION_SLIDE_TARGET_MISSED",
                severity=Severity.ERROR,
                message=(
                    f"Storyboard has {count} slides; confirmed target "
                    f"{target_slides.minimum}–{target_slides.maximum}."
                ),
                location="slides/storyboard.json",
            )
        )


def _check_duplicate_ids(
    storyboard: Storyboard, issues: list[ValidationIssue]
) -> None:
    slide_ids = [s.slide_id for s in storyboard.slides]
    if len(slide_ids) != len(set(slide_ids)):
        issues.append(
            ValidationIssue(
                code="SLIDE_DUPLICATE_ID",
                severity=Severity.ERROR,
                message="Duplicate slide IDs found.",
            )
        )


def _check_body_lines(
    storyboard: Storyboard, issues: list[ValidationIssue]
) -> None:
    for slide in storyboard.slides:
        if len(slide.body_lines) > 6:
            issues.append(
                ValidationIssue(
                    code="SLIDE_TOO_MANY_BODY_LINES",
                    severity=Severity.WARNING,
                    message=f"Slide '{slide.slide_id}' has {len(slide.body_lines)} "
                    f"body lines (max 6).",
                    location=slide.slide_id,
                )
            )

        total_text = slide.assertion_title + slide.takeaway + "".join(slide.body_lines)
        if len(total_text) > 520:
            issues.append(
                ValidationIssue(
                    code="SLIDE_TOO_MUCH_TEXT",
                    severity=Severity.WARNING,
                    message=f"Slide '{slide.slide_id}' has {len(total_text)} "
                    f"visible text characters (max 520).",
                    location=slide.slide_id,
                )
            )


def _check_notes_and_footer(
    storyboard: Storyboard, issues: list[ValidationIssue]
) -> None:
    for slide in storyboard.slides:
        if len(slide.speaker_notes) < 20:
            issues.append(
                ValidationIssue(
                    code="SLIDE_MISSING_NOTES",
                    severity=Severity.ERROR,
                    message=f"Slide '{slide.slide_id}' speaker notes too short "
                    f"({len(slide.speaker_notes)} chars, min 20).",
                    location=slide.slide_id,
                )
            )

        if not slide.source_footer.strip():
            issues.append(
                ValidationIssue(
                    code="SLIDE_MISSING_SOURCE_FOOTER",
                    severity=Severity.ERROR,
                    message=f"Slide '{slide.slide_id}' is missing source footer.",
                    location=slide.slide_id,
                )
            )

        purpose_lower = slide.purpose.lower()
        if any(
            kw in purpose_lower
            for kw in ("result", "headline", "ablation", "finding")
        ):
            issues.append(
                ValidationIssue(
                    code="SLIDE_RESULT_WITHOUT_NUMERIC_EVIDENCE",
                    severity=Severity.WARNING,
                    message=f"Result slide '{slide.slide_id}' should validate "
                    f"numeric evidence separately.",
                    location=slide.slide_id,
                )
            )
