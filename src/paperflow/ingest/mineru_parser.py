"""MinerU parser adapter.

MinerU is an optional high-quality PDF parser. This adapter attempts to invoke
the MinerU CLI (`mineru` or `magic-pdf`) when available, and normalizes its
output into our ParsedDocument schema.

Installation: pip install magic-pdf
Docs: https://github.com/opendatalab/MinerU
"""

import shutil
from pathlib import Path

from paperflow.errors import ExternalToolError
from paperflow.models.document import ParsedDocument, TextBlock
from paperflow.util.commands import run_command
from paperflow.util.hashing import sha256_file

_MINERU_COMMANDS = ["mineru", "magic-pdf"]


class MinerUParser:
    name: str = "mineru"

    def available(self) -> bool:
        """Check if any known MinerU CLI binary is on PATH."""
        return any(shutil.which(cmd) for cmd in _MINERU_COMMANDS)

    def _find_command(self) -> str:
        for cmd in _MINERU_COMMANDS:
            if shutil.which(cmd):
                return cmd
        raise ExternalToolError(
            "MinerU is not installed. Install it with: "
            "pip install magic-pdf"
        )

    def parse(self, pdf_path: Path, workspace: Path) -> ParsedDocument:
        pdf_sha256 = sha256_file(pdf_path)
        output_dir = workspace / "source" / "mineru"
        output_dir.mkdir(parents=True, exist_ok=True)

        cmd = self._find_command()

        result = run_command(
            [cmd, "-p", str(pdf_path), "-o", str(output_dir)],
            timeout_s=600,
        )

        if result.returncode != 0:
            raise ExternalToolError(
                f"MinerU ({cmd}) failed with exit code {result.returncode}:\n"
                f"{result.stderr}"
            )

        blocks = self._parse_mineru_output(output_dir)

        md_path = workspace / "source" / "parsed-paper.md"
        md_content = self._build_markdown(blocks)
        md_path.write_text(md_content, encoding="utf-8")

        return ParsedDocument(
            parser_name=f"mineru+{cmd}",
            parser_version=None,
            pdf_sha256=pdf_sha256,
            page_count=max((b.page for b in blocks), default=1),
            markdown_path=str(md_path),
            blocks=blocks,
            warnings=[],
        )

    @staticmethod
    def _parse_mineru_output(output_dir: Path) -> list[TextBlock]:
        """Parse MinerU output directory into TextBlock list.

        MinerU typically produces markdown files per page or a single merged
        markdown. We look for both patterns.
        """
        blocks: list[TextBlock] = []
        md_files = sorted(output_dir.rglob("*.md"))

        if not md_files:
            raise ExternalToolError(
                "MinerU produced no markdown output files in "
                f"{output_dir}"
            )

        block_idx = 0
        for md_file in md_files:
            page_num = 1
            parts = md_file.stem.split("_")
            for part in parts:
                if part.isdigit():
                    page_num = int(part)
                    break

            content = md_file.read_text(encoding="utf-8")
            if content.strip():
                block_id = f"p{page_num:02d}-b{block_idx + 1:03d}"
                blocks.append(
                    TextBlock(
                        id=block_id,
                        page=page_num,
                        order=block_idx,
                        text=content.strip(),
                    )
                )
                block_idx += 1

        return blocks

    @staticmethod
    def _build_markdown(blocks: list[TextBlock]) -> str:
        lines: list[str] = []
        last_page = 0
        for block in blocks:
            if block.page != last_page:
                lines.append(f"<!-- page:{block.page} -->\n")
                last_page = block.page
            lines.append(block.text + f"\n<!-- {block.id} -->")
        return "\n\n".join(lines)
