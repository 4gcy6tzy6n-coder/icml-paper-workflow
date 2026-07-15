# PaperFlow

Convert one ICML-style research paper PDF into a source-grounded Chinese academic report (`.qmd`, `.docx`, `.pdf`) and an editable Chinese presentation (`.pptx`, `.pdf`, speaker notes).

**Key properties:**
- All claims trace back to source evidence blocks in the PDF.
- Report and slides share the same canonical `paper-ir.json` — no independent reinterpretation.
- PPTX text, captions, and shapes remain editable; full-slide screenshots are forbidden.
- Claude Code performs semantic work (interpretation, prose, storyboard); Python/TypeScript tools are strictly deterministic.
- No external LLM API key required.

## Quick Start

```bash
git clone <repo-url>
cd icml-paper-workflow
uv sync --extra dev
pnpm install
uv run paperflow doctor

# Start a Claude Code session and use the skill:
claude
```

In Claude Code, instruct:

```
Use the icml-paper-to-report-deck skill on /absolute/path/to/paper.pdf.
Create the workspace under .work/<paper-name>.
Use Chinese for the report and slides, preserve English technical terms,
and complete every validation and visual QA gate.
```

## How It Works

After parsing and evidence extraction, the project skill asks one requirements question at a time. It covers the fixed core topics, asks paper-specific follow-ups, presents one complete summary, and requires explicit confirmation before writing source/authoring-requirements.json.

    paperflow validate-requirements WORKSPACE

The report and presentation both consume the confirmed authoring requirements and the canonical paper-ir.json. A parsed workspace cannot validate a Paper IR until requirements validation reaches requirements_ready.

```
paper.pdf
  │
  ├─[parse + build-evidence]──→ parsed document + evidence map
  │
  ├─[project skill]──→ one-question-at-a-time requirements intake
  │                    → explicit confirmation
  │                    → source/authoring-requirements.json
  │
  ├─[validate-requirements]──→ REQUIREMENTS_READY
  │
  ├─[project skill]──→ paper-ir.json (canonical interpretation)
  │
  ├─[validate-ir]──→ IR ready
  │
  ├─[Claude]─→ report.qmd + storyboard.json
  │
  ├─[render-report]──→ academic-report.docx + .pdf
  ├─[render-slides]──→ presentation.pptx + speaker-notes.md
  │
  ├─[qa-content]─────→ cross-artifact consistency
  ├─[visual-qa]──────→ slide inspection + fix cycle
  │
  └─[finalize]───────→ dist/<paper-slug>/
```

## Requirements

- Python 3.11+, uv
- Node.js 20+, pnpm
- Quarto (`brew install quarto`)
- LibreOffice (`brew install libreoffice`)
- Poppler (`brew install poppler`)
- Optional: MinerU Precision Extract API token in `MINERU_API_KEY`
- Optional: MinerU CLI (`pip install magic-pdf`)
- Optional: MarkItDown (`pip install 'markitdown[pdf]'`)

## Commands

```bash
paperflow init PDF WORKSPACE          # Initialize workspace
paperflow parse WORKSPACE             # Parse PDF (MinerU API→local fallbacks)
paperflow build-evidence WORKSPACE    # Build evidence map
paperflow validate-requirements WORKSPACE  # Validate confirmed requirements
paperflow validate-ir WORKSPACE       # Validate Paper IR
paperflow scaffold-report WORKSPACE   # Create report outline
paperflow validate-report WORKSPACE   # Validate report QMD
paperflow render-report WORKSPACE     # Render DOCX + PDF
paperflow validate-storyboard WORKSPACE  # Validate storyboard
paperflow render-slides WORKSPACE     # Render PPTX + notes
paperflow qa-content WORKSPACE        # Cross-artifact QA
paperflow render-preview WORKSPACE    # Slide preview images
paperflow validate-visual-review WORKSPACE  # Visual review gate
paperflow finalize WORKSPACE          # Copy to dist/
paperflow status WORKSPACE            # Show current stage
paperflow doctor                     # Check environment
paperflow version                    # Print version
```

When `MINERU_API_KEY` is set, `paperflow parse` uploads the source PDF through
MinerU's signed-upload API and saves the raw result archive and extracted JSON
under `WORKSPACE/source/mineru-api/`. The credential is read only from the
process environment and is not written to workspace artifacts.

## Development

```bash
make install     # uv sync + pnpm install
make test        # pytest + vitest
make lint        # ruff + mypy + tsc
make check       # test + lint
make doctor      # environment check
```
