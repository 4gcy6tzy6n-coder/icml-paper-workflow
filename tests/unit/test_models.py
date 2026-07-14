import pytest
from pydantic import ValidationError

from paperflow.models.paper_ir import EvidenceRef, Finding, PaperIR


def test_finding_requires_evidence() -> None:
    with pytest.raises(ValidationError):
        Finding(
            id="finding-1",
            claim="Method A improves accuracy.",
            importance="headline",
            evidence_ids=[],
            source_type="author_stated",
        )


def test_evidence_id_format() -> None:
    ref = EvidenceRef(
        id="ev-p03-b002",
        page=3,
        block_id="p03-b002",
        source_text="Accuracy improves by 4.1 points.",
    )
    assert ref.id == "ev-p03-b002"


def test_evidence_id_invalid_rejected() -> None:
    with pytest.raises(ValidationError):
        EvidenceRef(
            id="bad-format",
            page=3,
            block_id="p03-b002",
            source_text="Accuracy improves by 4.1 points.",
        )


def test_paper_ir_requires_contributions() -> None:
    from paperflow.models.paper_ir import (
        ExperimentalSetup,
        MethodComponent,
        PaperMetadata,
        ResearchProblem,
    )

    with pytest.raises(ValidationError):
        PaperIR(
            metadata=PaperMetadata(
                title="Test Paper",
                authors=["Author One"],
                abstract="An abstract.",
            ),
            research_problem=ResearchProblem(
                context="ctx",
                practical_problem="pp",
                technical_problem="tp",
                existing_gap="gap",
                research_question="rq",
                evidence_ids=["ev-p01-b001"],
            ),
            contributions=[],
            method_overview="overview",
            method_components=[
                MethodComponent(
                    id="mc-1",
                    name="Method",
                    purpose="p",
                    mechanism="m",
                    evidence_ids=["ev-p01-b001"],
                )
            ],
            experimental_setup=ExperimentalSetup(
                datasets=["DS1"],
                baselines=["BL1"],
                metrics=["ACC"],
                implementation_summary="impl",
                evidence_ids=["ev-p01-b001"],
            ),
            numeric_results=[],
            findings=[],
            limitations=[],
            evidence=[],
        )
