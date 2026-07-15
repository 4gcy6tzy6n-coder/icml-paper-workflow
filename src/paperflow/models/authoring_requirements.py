from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

NonBlankStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Sha256Str = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
ReportFormat = Literal["qmd", "docx", "report_pdf"]
PresentationFormat = Literal["pptx", "slides_pdf", "speaker_notes"]
DeliveryFormat = ReportFormat | PresentationFormat


class RequirementsModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PositiveRange(RequirementsModel):
    minimum: int = Field(ge=1)
    maximum: int = Field(ge=1)

    @model_validator(mode="after")
    def ordered(self) -> PositiveRange:
        if self.minimum > self.maximum:
            raise ValueError("minimum must not exceed maximum")
        return self


class SourceRequirements(RequirementsModel):
    pdf_sha256: Sha256Str
    title: NonBlankStr


class AudienceRequirements(RequirementsModel):
    role: NonBlankStr
    background: NonBlankStr
    subject_familiarity: Literal["beginner", "intermediate", "advanced", "mixed"]


class UseCaseRequirements(RequirementsModel):
    scenario: NonBlankStr
    desired_outcome: NonBlankStr
    audience: AudienceRequirements


class ReportRequirements(RequirementsModel):
    required: Literal[True]
    purpose: NonBlankStr
    target_pages: PositiveRange
    target_chinese_characters: PositiveRange
    formats: tuple[Literal["qmd"], Literal["docx"], Literal["report_pdf"]]
    focus_topics: list[NonBlankStr] = Field(default_factory=list)
    de_emphasized_topics: list[NonBlankStr] = Field(default_factory=list)
    technical_depth: Literal["overview", "balanced", "deep"]
    narrative_preference: NonBlankStr
    reading_context: NonBlankStr


class PresentationRequirements(RequirementsModel):
    required: Literal[True]
    purpose: NonBlankStr
    duration_minutes: int = Field(ge=1)
    target_slides: PositiveRange
    formats: tuple[
        Literal["pptx"],
        Literal["slides_pdf"],
        Literal["speaker_notes"],
    ]
    focus_topics: list[NonBlankStr] = Field(default_factory=list)
    speaker_notes_required: Literal[True]
    speaking_context: NonBlankStr


class LanguageRequirements(RequirementsModel):
    locale: Literal["zh-CN"]
    preserve_english_terms: bool
    translation_preferences: NonBlankStr


class VisualRequirements(RequirementsModel):
    style: NonBlankStr
    template_path: None = None
    brand_requirements: list[NonBlankStr] = Field(default_factory=list)
    accessibility_requirements: list[NonBlankStr] = Field(default_factory=list)


class EvidencePolicyRequirements(RequirementsModel):
    allow_web_research: Literal[False]
    allow_generated_result_figures: Literal[False]
    prefer_original_figures: Literal[True]
    citation_expectations: NonBlankStr


class DeliverableRequirements(RequirementsModel):
    formats: tuple[
        Literal["qmd"],
        Literal["docx"],
        Literal["report_pdf"],
        Literal["pptx"],
        Literal["slides_pdf"],
        Literal["speaker_notes"],
    ]
    output_location: Literal["dist/<paper-slug>"]
    naming_requirements: Literal["paperflow-standard"]


class ConfirmationRequirements(RequirementsModel):
    status: Literal["confirmed"]
    confirmed_at: datetime
    content_sha256: Sha256Str


class AuthoringRequirements(RequirementsModel):
    schema_version: Literal["1.0"] = "1.0"
    source: SourceRequirements
    use_case: UseCaseRequirements
    report: ReportRequirements
    presentation: PresentationRequirements
    language: LanguageRequirements
    visual: VisualRequirements
    evidence_policy: EvidencePolicyRequirements
    deliverables: DeliverableRequirements
    user_constraints: list[NonBlankStr] = Field(default_factory=list)
    assumptions: list[NonBlankStr] = Field(default_factory=list)
    confirmation: ConfirmationRequirements

RequirementsInput = AuthoringRequirements | Mapping[str, Any]


def canonical_requirements_content(data: RequirementsInput) -> dict[str, Any]:
    payload = (
        data.model_dump(mode="json")
        if isinstance(data, AuthoringRequirements)
        else dict(data)
    )
    return {key: value for key, value in payload.items() if key != "confirmation"}


def compute_requirements_digest(data: RequirementsInput) -> str:
    canonical = json.dumps(
        canonical_requirements_content(data),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
