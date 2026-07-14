from pathlib import Path

from paperflow.errors import ExternalToolError
from paperflow.ingest.base import DocumentParser
from paperflow.models.document import ParsedDocument


class FakeDocumentParser:
    """Test double implementing the DocumentParser protocol."""

    name: str

    def __init__(self, name: str, available: bool, should_fail: bool = False) -> None:
        self.name = name
        self._available = available
        self._should_fail = should_fail

    def available(self) -> bool:
        return self._available

    def parse(self, pdf_path: Path, workspace: Path) -> ParsedDocument:
        if self._should_fail:
            raise ExternalToolError(f"Parser '{self.name}' failed intentionally")
        return ParsedDocument(
            parser_name=self.name,
            pdf_sha256="0" * 64,
            page_count=1,
            markdown_path=str(workspace / "source" / "parsed-paper.md"),
            blocks=[],
        )


def select_parser_chain(config: object) -> list[DocumentParser]:
    """Select available parsers in preferred order from config."""
    from paperflow.ingest.markitdown_parser import MarkItDownParser
    from paperflow.ingest.mineru_api_parser import MinerUApiParser
    from paperflow.ingest.mineru_parser import MinerUParser
    from paperflow.ingest.pymupdf_parser import PyMuPDFParser

    all_parsers: list[DocumentParser] = [
        MinerUApiParser(),
        MinerUParser(),
        MarkItDownParser(),
        PyMuPDFParser(),
    ]
    name_to_parser = {p.name: p for p in all_parsers}

    configured_order = getattr(
        config, "preferred_parser_order", ["mineru", "markitdown", "pymupdf"]
    )
    order = list(dict.fromkeys(["mineru_api", *configured_order]))

    chain: list[DocumentParser] = []
    for name in order:
        parser = name_to_parser.get(name)
        if parser and parser.available():
            chain.append(parser)

    return chain


def parse_with_fallback(
    pdf_path: Path,
    workspace: Path,
    chain: list[DocumentParser],
) -> tuple[ParsedDocument, list[str], str]:
    """Try each parser in chain; return first success. Raises ExternalToolError if all fail."""
    errors: list[str] = []
    attempted: list[str] = []

    for parser in chain:
        if not parser.available():
            continue
        try:
            doc = parser.parse(pdf_path, workspace)
            fallback_names = attempted  # parsers we fell back FROM (failed before this one)
            return doc, fallback_names, parser.name
        except Exception as exc:
            attempted.append(parser.name)
            errors.append(f"{parser.name}: {exc}")

    raise ExternalToolError(
        "All parsers failed.\n" + "\n".join(f"- {e}" for e in errors)
    )
