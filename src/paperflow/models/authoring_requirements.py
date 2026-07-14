from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, StringConstraints, model_validator

NonBlankStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Sha256Str = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
ReportFormat = Literal["qmd", "docx", "report_pdf"]
PresentationFormat = Literal["pptx", "slides_pdf", "speaker_notes"]
DeliveryFormat = ReportFormat | PresentationFormat


class PositiveRange(BaseModel):
    minimum: int = Field(ge=1)
    maximum: int = Field(ge=1)

    @model_validator(mode="after")
    def ordered(self) -> PositiveRange:
        if self.minimum > self.maximum:
            raise ValueError("minimum must not exceed maximum")
        return self


class SourceRequirements(BaseModel):
    pdf_sha256: Sha256Str
    title: NonBlankStr


class AudienceRequirements(BaseModel):
    role: NonBlankStr
    background: NonBlankStr
    subject_familiarity: Literal["beginner", "intermediate", "advanced", "mixed"]


class UseCaseRequirements(BaseModel):
    scenario: NonBlankStr
    desired_outcome: NonBlankStr
    audience: AudienceRequirements


class ReportRequirements(BaseModel):
    required: bool
    purpose: NonBlankStr | None = None
    target_pages: PositiveRange | None = None
    target_chinese_characters: PositiveRange | None = None
    formats: list[ReportFormat] = Field(default_factory=list)
    focus_topics: list[NonBlankStr] = Field(default_factory=list)
    de_emphasized_topics: list[NonBlankStr] = Field(default_factory=list)
    technical_depth: Literal["overview", "balanced", "deep"] | None = None
    narrative_preference: NonBlankStr | None = None
    reading_context: NonBlankStr | None = None

    @model_validator(mode="after")
    def complete_when_required(self) -> ReportRequirements:
        values = (
            self.purpose,
            self.target_pages,
            self.target_chinese_characters,
            self.technical_depth,
            self.narrative_preference,
            self.reading_context,
        )
        if self.required and (any(value is None for value in values) or not self.formats):
            raise ValueError("enabled report settings must be complete")
        return self


class PresentationRequirements(BaseModel):
    required: bool
    purpose: NonBlankStr | None = None
    duration_minutes: int | None = Field(default=None, ge=1)
    target_slides: PositiveRange | None = None
    formats: list[PresentationFormat] = Field(default_factory=list)
    focus_topics: list[NonBlankStr] = Field(default_factory=list)
    speaker_notes_required: bool | None = None
    speaking_context: NonBlankStr | None = None

    @model_validator(mode="after")
    def complete_when_required(self) -> PresentationRequirements:
        values = (
            self.purpose,
            self.duration_minutes,
            self.target_slides,
            self.speaker_notes_required,
            self.speaking_context,
        )
        if self.required and (any(value is None for value in values) or not self.formats):
            raise ValueError("enabled presentation settings must be complete")
        return self


class LanguageRequirements(BaseModel):
    locale: Literal["zh-CN"]
    preserve_english_terms: bool
    translation_preferences: NonBlankStr


class VisualRequirements(BaseModel):
    style: NonBlankStr
    template_path: NonBlankStr | None = None
    brand_requirements: list[NonBlankStr] = Field(default_factory=list)
    accessibility_requirements: list[NonBlankStr] = Field(default_factory=list)


class EvidencePolicyRequirements(BaseModel):
    allow_web_research: bool
    allow_generated_result_figures: bool
    prefer_original_figures: bool
    citation_expectations: NonBlankStr


class DeliverableRequirements(BaseModel):
    formats: list[DeliveryFormat] = Field(min_length=1)
    output_location: NonBlankStr
    naming_requirements: NonBlankStr


class ConfirmationRequirements(BaseModel):
    status: Literal["confirmed"]
    confirmed_at: datetime
    content_sha256: Sha256Str


class AuthoringRequirements(BaseModel):
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

    @model_validator(mode="after")
    def formats_match_enabled_outputs(self) -> AuthoringRequirements:
        expected: set[str] = set()
        if self.report.required:
            expected.update(self.report.formats)
        if self.presentation.required:
            expected.update(self.presentation.formats)
        if set(self.deliverables.formats) != expected:
            raise ValueError("deliverable formats must match enabled output formats")
        return self


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
