from typing import Literal

from pydantic import BaseModel, Field

from paperflow.models.common import SourceType


class EvidenceRef(BaseModel):
    id: str = Field(pattern=r"^ev-p\d{2,4}-b\d{3,5}(-[a-z])?$")
    page: int = Field(ge=1)
    block_id: str
    section: str | None = None
    figure_or_table: str | None = None
    source_text: str = Field(min_length=1, max_length=2000)


class ClaimBase(BaseModel):
    id: str
    statement: str = Field(min_length=5)
    evidence_ids: list[str] = Field(min_length=1)
    source_type: SourceType = SourceType.AUTHOR_STATED


class Contribution(ClaimBase):
    novelty: str | None = None


class Finding(BaseModel):
    id: str
    claim: str = Field(min_length=5)
    importance: Literal["headline", "supporting", "secondary"]
    evidence_ids: list[str] = Field(min_length=1)
    source_type: SourceType


class NumericResult(BaseModel):
    id: str
    metric: str
    value_text: str
    comparison_text: str | None = None
    direction: Literal["higher_better", "lower_better", "neutral"]
    evidence_ids: list[str] = Field(min_length=1)


class Limitation(ClaimBase):
    implication: str | None = None


class PaperMetadata(BaseModel):
    title: str
    authors: list[str] = Field(min_length=1)
    venue: str = "ICML"
    year: int | None = None
    abstract: str


class ResearchProblem(BaseModel):
    context: str
    practical_problem: str
    technical_problem: str
    existing_gap: str
    research_question: str
    evidence_ids: list[str] = Field(min_length=1)


class MethodComponent(BaseModel):
    id: str
    name: str
    purpose: str
    mechanism: str
    input_text: str | None = None
    output_text: str | None = None
    evidence_ids: list[str] = Field(min_length=1)


class ExperimentalSetup(BaseModel):
    datasets: list[str]
    baselines: list[str]
    metrics: list[str]
    implementation_summary: str
    evidence_ids: list[str] = Field(min_length=1)


class PaperIR(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    metadata: PaperMetadata
    research_problem: ResearchProblem
    contributions: list[Contribution] = Field(min_length=1)
    method_overview: str
    method_components: list[MethodComponent] = Field(min_length=1)
    experimental_setup: ExperimentalSetup
    numeric_results: list[NumericResult] = Field(min_length=1)
    findings: list[Finding] = Field(min_length=1)
    limitations: list[Limitation] = Field(min_length=1)
    evidence: list[EvidenceRef] = Field(min_length=1)
    selected_asset_ids: list[str] = Field(default_factory=list)
