from pathlib import Path

from paperflow.errors import ExternalToolError
from paperflow.models.document import ParsedDocument


class MarkItDownParser:
    name: str = "markitdown"

    def available(self) -> bool:
        try:
            import markitdown  # noqa: F401

            return True
        except ImportError:
            return False

    def parse(self, pdf_path: Path, workspace: Path) -> ParsedDocument:
        raise ExternalToolError(
            "MarkItDown PDF support requires `pip install 'markitdown[pdf]'`. "
            "MarkItDown is an optional adapter; PyMuPDF is the required fallback."
        )
