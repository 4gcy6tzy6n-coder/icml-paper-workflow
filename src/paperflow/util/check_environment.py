"""Check the PaperFlow runtime environment."""

import shutil
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class ToolCheck:
    name: str
    required: bool
    available: bool
    version: str | None
    action: str


def _get_version(args: list[str]) -> str | None:
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=30
        )
        return (result.stdout or result.stderr).strip().split("\n")[0][:80]
    except Exception:
        return None


def check_environment() -> list[ToolCheck]:
    checks: list[ToolCheck] = []

    # Python
    checks.append(
        ToolCheck(
            name="Python",
            required=True,
            available=True,
            version=sys.version.split()[0],
            action="",
        )
    )

    # uv
    uv_version = _get_version(["uv", "--version"])
    checks.append(
        ToolCheck(
            name="uv",
            required=True,
            available=shutil.which("uv") is not None,
            version=uv_version,
            action="Install from https://astral.sh/uv" if not uv_version else "",
        )
    )

    # Node.js
    node_version = _get_version(["node", "--version"])
    checks.append(
        ToolCheck(
            name="Node.js",
            required=True,
            available=shutil.which("node") is not None,
            version=node_version,
            action="Install from https://nodejs.org/" if not node_version else "",
        )
    )

    # pnpm
    pnpm_version = _get_version(["pnpm", "--version"])
    checks.append(
        ToolCheck(
            name="pnpm",
            required=True,
            available=shutil.which("pnpm") is not None,
            version=pnpm_version,
            action="Run: corepack enable && corepack prepare pnpm@latest --activate"
            if not pnpm_version
            else "",
        )
    )

    # PyMuPDF
    try:
        import fitz  # type: ignore[import-untyped]
        checks.append(
            ToolCheck(
                name="PyMuPDF",
                required=True,
                available=True,
                version=fitz.version[0],
                action="",
            )
        )
    except ImportError:
        checks.append(
            ToolCheck(
                name="PyMuPDF",
                required=True,
                available=False,
                version=None,
                action="Run: pip install pymupdf",
            )
        )

    # Quarto
    quarto_version = _get_version(["quarto", "--version"])
    checks.append(
        ToolCheck(
            name="Quarto",
            required=True,
            available=shutil.which("quarto") is not None,
            version=quarto_version,
            action="Install from https://quarto.org/docs/download/"
            if not quarto_version
            else "",
        )
    )

    # LibreOffice
    lo_version = _get_version(["soffice", "--version"])
    checks.append(
        ToolCheck(
            name="LibreOffice",
            required=True,
            available=shutil.which("soffice") is not None,
            version=lo_version,
            action="Install: brew install libreoffice"
            if not lo_version
            else "",
        )
    )

    # Poppler
    poppler_version = _get_version(["pdftoppm", "-v"])
    checks.append(
        ToolCheck(
            name="Poppler",
            required=True,
            available=shutil.which("pdftoppm") is not None,
            version=poppler_version,
            action="Install: brew install poppler"
            if not poppler_version
            else "",
        )
    )

    # MinerU (optional)
    mineru_available = shutil.which("magic-pdf") is not None or shutil.which("mineru") is not None
    if not mineru_available:
        try:
            import magic_pdf  # type: ignore[import-untyped] # noqa: F401
            mineru_available = True
        except ImportError:
            pass

    checks.append(
        ToolCheck(
            name="MinerU",
            required=False,
            available=mineru_available,
            version=_get_version(["magic-pdf", "--version"]) if mineru_available else None,
            action="Optional: pip install magic-pdf",
        )
    )

    # MarkItDown (optional)
    markitdown_available = False
    try:
        import markitdown  # type: ignore[import-not-found] # noqa: F401
        markitdown_available = True
    except ImportError:
        pass

    checks.append(
        ToolCheck(
            name="MarkItDown",
            required=False,
            available=markitdown_available,
            version=None,
            action="Optional: pip install 'markitdown[pdf]'",
        )
    )

    return checks
