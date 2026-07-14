from pathlib import Path

import fitz  # type: ignore[import-untyped]

from paperflow.models.document import ParsedDocument, TextBlock
from paperflow.util.hashing import sha256_file
from paperflow.util.jsonio import write_json


class PyMuPDFParser:
    name: str = "pymupdf"

    def available(self) -> bool:
        try:
            import fitz  # noqa: F401

            return True
        except ImportError:
            return False

    def parse(self, pdf_path: Path, workspace: Path) -> ParsedDocument:
        pdf_sha256 = sha256_file(pdf_path)
        doc = fitz.open(str(pdf_path))
        warnings: list[str] = []
        page_count = doc.page_count
        fitz_version = fitz.version[0]

        blocks: list[TextBlock] = []
        block_idx = 0

        for page_num in range(page_count):
            page = doc[page_num]
            page_blocks = page.get_text("blocks", sort=True)

            page_block_count = 0
            for raw in page_blocks:
                text = raw[4] if isinstance(raw, (tuple, list)) else ""
                if isinstance(text, str):
                    text = text.strip()
                if not text:
                    continue
                page_block_count += 1
                block_id = f"p{page_num + 1:02d}-b{block_idx + 1:03d}"
                bbox_raw: tuple[float, ...] | None = None
                if isinstance(raw, (tuple, list)) and len(raw) >= 4:
                    bbox_raw = (float(raw[0]), float(raw[1]), float(raw[2]), float(raw[3]))
                bbox: tuple[float, float, float, float] | None = None
                if bbox_raw is not None and len(bbox_raw) == 4:
                    bbox = (
                        float(bbox_raw[0]),
                        float(bbox_raw[1]),
                        float(bbox_raw[2]),
                        float(bbox_raw[3]),
                    )

                blocks.append(
                    TextBlock(
                        id=block_id,
                        page=page_num + 1,
                        order=block_idx,
                        text=text,
                        bbox=bbox,
                    )
                )
                block_idx += 1

            if page_block_count == 0:
                warnings.append(
                    f"Page {page_num + 1}: no extractable text blocks found"
                )

        doc.close()

        # Write Markdown with page anchors
        source_dir = workspace / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        md_path = source_dir / "parsed-paper.md"

        md_lines: list[str] = []
        last_page = 0
        for block in blocks:
            if block.page != last_page:
                md_lines.append(f"<!-- page:{block.page} -->\n")
                last_page = block.page
            page_id = f"<!-- {block.id} -->"
            md_lines.append(block.text + "\n" + page_id)

        md_path.write_text("\n\n".join(md_lines), encoding="utf-8")

        # Build and save parsed document
        parsed = ParsedDocument(
            parser_name=self.name,
            parser_version=fitz_version,
            pdf_sha256=pdf_sha256,
            title_guess=self._guess_title(blocks),
            page_count=page_count,
            markdown_path=str(md_path),
            blocks=blocks,
            warnings=warnings,
        )

        parsed_doc_path = source_dir / "parsed-document.json"
        write_json(parsed_doc_path, parsed.model_dump(mode="json"))

        return parsed

    @staticmethod
    def _guess_title(blocks: list[TextBlock]) -> str | None:
        for block in blocks[:3]:
            text = block.text.strip()
            if 20 < len(text) < 200 and not text.startswith("Abstract"):
                return text
        return None
