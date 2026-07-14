"""Quality scoring for golden paper evaluation."""

from dataclasses import dataclass, field


@dataclass
class GoldenScore:
    paper_label: str
    paper_ir_coverage: float = 0.0       # max 35
    evidence_traceability: float = 0.0    # max 20
    report_completeness: float = 0.0      # max 15
    deck_story_structure: float = 0.0     # max 10
    cross_artifact_consistency: float = 0.0  # max 10
    visual_qa_editability: float = 0.0    # max 10
    notes: list[str] = field(default_factory=list)

    @property
    def total(self) -> float:
        return (
            self.paper_ir_coverage
            + self.evidence_traceability
            + self.report_completeness
            + self.deck_story_structure
            + self.cross_artifact_consistency
            + self.visual_qa_editability
        )

    @property
    def passed(self) -> bool:
        return self.total >= 85.0


def score_paper_ir_coverage(
    ir_validation_passed: bool,
    evidence_coverage: float,
) -> float:
    """Score Paper IR factual coverage (max 35 points)."""
    if not ir_validation_passed:
        return 0.0
    return 35.0 * evidence_coverage


def score_evidence_traceability(
    evidence_map_count: int,
    claim_count: int,
) -> float:
    """Score evidence traceability (max 20 points)."""
    if claim_count == 0:
        return 0.0
    ratio = min(evidence_map_count / max(1, claim_count * 2), 1.0)
    return 20.0 * ratio


def score_report_completeness(
    sections_present: int,
    required_sections: int = 16,
) -> float:
    """Score report completeness (max 15 points)."""
    return 15.0 * (sections_present / required_sections)


def score_deck_structure(
    slide_count: int,
    min_slides: int = 13,
    max_slides: int = 15,
) -> float:
    """Score deck story structure (max 10 points)."""
    if slide_count < min_slides:
        return 10.0 * (slide_count / min_slides)
    if slide_count > max_slides:
        return 10.0 * max(0.5, (max_slides - (slide_count - max_slides)) / max_slides)
    return 10.0


def score_cross_artifact_consistency(
    contributions_match: bool,
    metrics_match: bool,
    limitations_match: bool,
) -> float:
    """Score cross-artifact consistency (max 10 points)."""
    score = 0.0
    if contributions_match:
        score += 4.0
    if metrics_match:
        score += 3.0
    if limitations_match:
        score += 3.0
    return score


def score_visual_qa(
    visual_review_passed: bool,
    fix_cycles: int = 0,
) -> float:
    """Score visual QA and editability (max 10 points)."""
    if not visual_review_passed:
        return 0.0
    base = 8.0 if fix_cycles > 0 else 5.0
    return min(10.0, base + min(fix_cycles, 2))
