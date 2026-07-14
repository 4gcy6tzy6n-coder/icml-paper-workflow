# Installation

## Prerequisites

### macOS

```bash
# Python and uv
brew install python@3.12 uv

# Node.js and pnpm
brew install node
corepack enable
corepack prepare pnpm@latest --activate

# Rendering tools
brew install quarto
brew install libreoffice
brew install poppler

# Optional: Higher-quality PDF parsing
pip install magic-pdf     # MinerU CLI
pip install 'markitdown[pdf]'  # MarkItDown
```

### Linux (Ubuntu/Debian)

```bash
# Python and uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Node.js and pnpm
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install nodejs -y
corepack enable
corepack prepare pnpm@latest --activate

# Rendering tools
# Quarto: https://quarto.org/docs/download/
apt-get install libreoffice
apt-get install poppler-utils
```

## Project Setup

```bash
git clone <repo-url>
cd icml-paper-workflow
uv sync --extra dev
pnpm install
```

## Verify Installation

```bash
uv run paperflow doctor
```

Expected output:

```
Python:        3.12.x   ✓
uv:            0.x.x    ✓
Node.js:       22.x     ✓
pnpm:          11.x     ✓
PyMuPDF:       1.x.x    ✓
Quarto:        1.x      ✓
LibreOffice:   24.x     ✓
Poppler:       24.x     ✓
MinerU:        (optional) ✓/✗
MarkItDown:    (optional) ✗
All required tools available.
```

## Troubleshooting

- **Quarto not found**: Install from https://quarto.org/docs/download/
- **LibreOffice not found**: Install with `brew install libreoffice` or `apt-get install libreoffice`
- **Poppler not found**: Install with `brew install poppler` or `apt-get install poppler-utils`
- **MinerU not found**: Install with `pip install magic-pdf`. The pipeline falls back to PyMuPDF if unavailable.
