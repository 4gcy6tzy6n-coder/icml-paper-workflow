from pydantic import BaseModel, Field

from paperflow.models.common import AssetType


class TextBlock(BaseModel):
    id: str
    page: int = Field(ge=1)
    order: int = Field(ge=0)
    section_path: list[str] = Field(default_factory=list)
    text: str = Field(min_length=1)
    bbox: tuple[float, float, float, float] | None = None


class DocumentAsset(BaseModel):
    id: str
    asset_type: AssetType
    page: int = Field(ge=1)
    label: str | None = None
    caption: str | None = None
    file_path: str
    bbox: tuple[float, float, float, float] | None = None


class ParsedDocument(BaseModel):
    parser_name: str
    parser_version: str | None = None
    pdf_sha256: str
    title_guess: str | None = None
    page_count: int = Field(ge=1)
    markdown_path: str
    blocks: list[TextBlock]
    assets: list[DocumentAsset] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
