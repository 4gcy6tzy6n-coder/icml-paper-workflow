from pydantic import BaseModel, Field


class WorkflowConfig(BaseModel):
    output_language: str = "zh-CN"
    audience: str = "graduate"
    talk_minutes: int = Field(default=15, ge=5, le=60)
    report_target_pages: int = Field(default=8, ge=4, le=30)
    min_slides: int = Field(default=13, ge=6, le=40)
    max_slides: int = Field(default=15, ge=6, le=40)
    allow_web_research: bool = False
    allow_generated_result_figures: bool = False
    preferred_parser_order: list[str] = Field(
        default_factory=lambda: ["mineru", "markitdown", "pymupdf"]
    )
    preserve_english_terms: bool = True
