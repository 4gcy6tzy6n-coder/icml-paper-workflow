import shutil
from pathlib import Path

from paperflow.errors import ExternalToolError
from paperflow.models.document import ParsedDocument


class MinerUParser:
    name: str = "mineru"

    def available(self) -> bool:
        return shutil.which("mineru") is not None

    def parse(self, pdf_path: Path, workspace: Path) -> ParsedDocument:
        raise ExternalToolError(
            "MinerU is not installed. Install it with: "
            "pip install magic-pdf or follow instructions at "
            "https://github.com/opendatalab/MinerU"
        )
