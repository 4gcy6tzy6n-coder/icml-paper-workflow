from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WorkspacePaths:
    root: Path

    @property
    def source_dir(self) -> Path:
        return self.root / "source"

    @property
    def assets_dir(self) -> Path:
        return self.root / "assets"

    @property
    def report_dir(self) -> Path:
        return self.root / "report"

    @property
    def slides_dir(self) -> Path:
        return self.root / "slides"

    @property
    def qa_dir(self) -> Path:
        return self.root / "qa"

    @property
    def parsed_document(self) -> Path:
        return self.source_dir / "parsed-document.json"

    @property
    def parsed_markdown(self) -> Path:
        return self.source_dir / "parsed-paper.md"

    @property
    def document_structure(self) -> Path:
        return self.source_dir / "document-structure.json"

    @property
    def authoring_requirements(self) -> Path:
        return self.source_dir / "authoring-requirements.json"

    @property
    def paper_ir(self) -> Path:
        return self.source_dir / "paper-ir.json"

    @property
    def evidence_map(self) -> Path:
        return self.source_dir / "evidence-map.json"

    @property
    def report_qmd(self) -> Path:
        return self.report_dir / "academic-report.qmd"

    @property
    def report_docx(self) -> Path:
        return self.report_dir / "academic-report.docx"

    @property
    def report_pdf(self) -> Path:
        return self.report_dir / "academic-report.pdf"

    @property
    def storyboard(self) -> Path:
        return self.slides_dir / "storyboard.json"

    @property
    def deck_pptx(self) -> Path:
        return self.slides_dir / "presentation.pptx"

    @property
    def deck_pdf(self) -> Path:
        return self.slides_dir / "presentation.pdf"

    @property
    def notes_markdown(self) -> Path:
        return self.slides_dir / "speaker-notes.md"

    @property
    def manifest(self) -> Path:
        return self.root / "manifest.json"

    @property
    def final_manifest(self) -> Path:
        return self.qa_dir / "final-manifest.json"

    def create_directories(self) -> None:
        for path in (
            self.source_dir,
            self.assets_dir / "figures",
            self.assets_dir / "tables",
            self.assets_dir / "page-images",
            self.report_dir,
            self.slides_dir,
            self.qa_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)
