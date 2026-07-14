from typing import Literal

from pydantic import BaseModel, Field


class ReportSectionPlan(BaseModel):
    section_id: str
    title: str
    purpose: str
    evidence_ids: list[str] = Field(default_factory=list)
    target_words: int = Field(ge=80, le=1500)


class ReportOutline(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    title: str
    sections: list[ReportSectionPlan] = Field(min_length=10, max_length=20)
