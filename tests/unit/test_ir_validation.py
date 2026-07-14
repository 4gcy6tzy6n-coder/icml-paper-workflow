from paperflow.evidence.validator import validate_paper_ir
from paperflow.models.paper_ir import (
    Contribution,
    EvidenceRef,
    ExperimentalSetup,
    Finding,
    Limitation,
    MethodComponent,
    NumericResult,
    PaperIR,
    PaperMetadata,
    ResearchProblem,
)


def _valid_ir() -> PaperIR:
    return PaperIR(
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
        contributions=[
            Contribution(
                id="c-1",
                statement="A novel method for attention.",
                evidence_ids=["ev-p01-b001"],
            )
        ],
        method_overview="An overview of the method.",
        method_components=[
            MethodComponent(
                id="mc-1",
                name="Attention Module",
                purpose="Improve accuracy",
                mechanism="Dynamic head selection",
                evidence_ids=["ev-p01-b001"],
            )
        ],
        experimental_setup=ExperimentalSetup(
            datasets=["CIFAR-100"],
            baselines=["Baseline A"],
            metrics=["Accuracy"],
            implementation_summary="Implemented in PyTorch.",
            evidence_ids=["ev-p01-b002"],
        ),
        numeric_results=[
            NumericResult(
                id="nr-1",
                metric="Accuracy",
                value_text="87.4%",
                direction="higher_better",
                evidence_ids=["ev-p01-b002"],
            )
        ],
        findings=[
            Finding(
                id="f-1",
                claim="Method improves accuracy.",
                importance="headline",
                evidence_ids=["ev-p01-b002"],
                source_type="author_stated",
            )
        ],
        limitations=[
            Limitation(
                id="l-1",
                statement="Only tested on one dataset.",
                evidence_ids=["ev-p01-b003"],
                source_type="author_stated",
            )
        ],
        evidence=[
            EvidenceRef(
                id="ev-p01-b001",
                page=1,
                block_id="p01-b001",
                source_text="Abstract text here.",
            ),
            EvidenceRef(
                id="ev-p01-b002",
                page=1,
                block_id="p01-b002",
                source_text="Results show 87.4%.",
            ),
            EvidenceRef(
                id="ev-p01-b003",
                page=1,
                block_id="p01-b003",
                source_text="A limitation is that...",
            ),
        ],
    )


def test_valid_ir_passes() -> None:
    ir = _valid_ir()
    issues = validate_paper_ir(ir, _valid_ir().evidence)
    errors = [i for i in issues if i.severity == "error"]
    assert len(errors) == 0


def test_duplicate_contribution_id_detected() -> None:
    ir = _valid_ir()
    ir.contributions.append(
        Contribution(
            id="c-1",
            statement="Duplicate ID.",
            evidence_ids=["ev-p01-b001"],
        )
    )
    issues = validate_paper_ir(ir, ir.evidence)
    codes = {i.code for i in issues}
    assert "IR_DUPLICATE_ID" in codes


def test_unknown_evidence_detected() -> None:
    ir = _valid_ir()
    ir.contributions[0].evidence_ids.append("ev-nonexistent")
    issues = validate_paper_ir(ir, ir.evidence)
    codes = {i.code for i in issues}
    assert "IR_UNKNOWN_EVIDENCE" in codes


def test_empty_required_section_detected() -> None:
    ir = _valid_ir()
    ir.contributions = []
    issues = validate_paper_ir(ir, ir.evidence)
    error_codes = {i.code for i in issues if i.severity == "error"}
    assert "IR_EMPTY_REQUIRED_SECTION" in error_codes


def test_numeric_without_evidence_detected() -> None:
    ir = _valid_ir()
    ir.numeric_results[0].evidence_ids = ["ev-nonexistent"]
    issues = validate_paper_ir(ir, ir.evidence)
    codes = {i.code for i in issues}
    assert "IR_UNKNOWN_EVIDENCE" in codes
