from pathlib import Path
from typing import Protocol

from paperflow.models.document import ParsedDocument


class DocumentParser(Protocol):
    name: str

    def available(self) -> bool:
        ...

    def parse(self, pdf_path: Path, workspace: Path) -> ParsedDocument:
        ...
