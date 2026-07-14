from paperflow.models.common import SlideLayout
from paperflow.models.slides import SlideSpec, Storyboard
from paperflow.qa.content import validate_storyboard


def _make_slide(slide_id: str, purpose: str) -> SlideSpec:
    return SlideSpec(
        slide_id=slide_id,
        purpose=purpose,
        assertion_title=f"Assertion for {slide_id}",
        takeaway=f"Takeaway for {slide_id}.",
        supporting_evidence_ids=["ev-p01-b001"],
        layout=SlideLayout.TWO_COLUMN,
        body_lines=["Line 1", "Line 2"],
        source_footer="Test Paper, ICML 2024",
        speaker_notes=f"Speaker notes for {slide_id} with enough characters to pass the minimum.",
    )


def _valid_storyboard() -> Storyboard:
    purposes = [
        "Title",
        "Problem statement",
        "Gap analysis",
        "Contributions",
        "Method overview",
        "Key component",
    ]
    return Storyboard(
        title="Test Paper",
        language="zh-CN",
        talk_minutes=15,
        slides=[_make_slide(f"slide-{i + 1:02d}", p) for i, p in enumerate(purposes)],
    )


def test_valid_storyboard_passes() -> None:
    issues = validate_storyboard(_valid_storyboard())
    errors = [i for i in issues if i.severity == "error"]
    assert len(errors) == 0


def test_slide_count_out_of_range_detected() -> None:
    sb = _valid_storyboard()
    sb.slides = sb.slides[:1]
    issues = validate_storyboard(sb)
    codes = {i.code for i in issues}
    assert "SLIDES_COUNT_OUT_OF_RANGE" in codes


def test_too_many_body_lines_detected() -> None:
    sb = _valid_storyboard()
    sb.slides[0].body_lines = ["1", "2", "3", "4", "5", "6", "7"]
    issues = validate_storyboard(sb)
    codes = {i.code for i in issues}
    assert "SLIDE_TOO_MANY_BODY_LINES" in codes


def test_missing_notes_detected() -> None:
    sb = _valid_storyboard()
    sb.slides[0].speaker_notes = ""
    issues = validate_storyboard(sb)
    codes = {i.code for i in issues}
    assert "SLIDE_MISSING_NOTES" in codes


def test_missing_source_footer_detected() -> None:
    sb = _valid_storyboard()
    sb.slides[0].source_footer = ""
    issues = validate_storyboard(sb)
    codes = {i.code for i in issues}
    assert "SLIDE_MISSING_SOURCE_FOOTER" in codes


def test_result_slide_without_numeric_evidence_detected() -> None:
    sb = _valid_storyboard()
    sb.slides[0].purpose = "Headline result"
    issues = validate_storyboard(sb)
    codes = {i.code for i in issues}
    assert "SLIDE_RESULT_WITHOUT_NUMERIC_EVIDENCE" in codes
