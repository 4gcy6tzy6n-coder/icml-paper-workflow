from typing import Literal

from pydantic import BaseModel, Field

from paperflow.models.common import SlideLayout


class SlideSpec(BaseModel):
    slide_id: str
    purpose: str
    assertion_title: str
    takeaway: str
    supporting_evidence_ids: list[str] = Field(min_length=1)
    visual_asset_ids: list[str] = Field(default_factory=list)
    layout: SlideLayout
    body_lines: list[str] = Field(default_factory=list, max_length=6)
    source_footer: str
    speaker_notes: str = Field(min_length=20)


class Storyboard(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    title: str
    language: str = "zh-CN"
    talk_minutes: int = Field(default=15, ge=5, le=60)
    slides: list[SlideSpec] = Field(min_length=6, max_length=40)
