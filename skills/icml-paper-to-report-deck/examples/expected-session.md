# Expected Session Transcript

This documents an expected Claude Code session using the skill on a sample ICML paper.

## User Prompt

```
Use the icml-paper-to-report-deck skill on ~/papers/attention-paper.pdf.
Create the workspace under .work/attention-paper.
Use Chinese for the report and slides, preserve English technical terms,
and complete every validation and visual QA gate.
```

## Expected Flow

### Environment Check
```bash
$ uv run paperflow doctor
Python:        3.12.13  ✓
uv:            0.5.x    ✓
Node.js:       22.x     ✓
pnpm:          11.x     ✓
PyMuPDF:       1.28.x   ✓
Quarto:        1.x      ✓
LibreOffice:   24.x     ✓
Poppler:       24.x     ✓
MinerU:        (optional) ✗
MarkItDown:    (optional) ✗
All required tools available.
```

### Initialization
```bash
$ uv run paperflow init ~/papers/attention-paper.pdf .work/attention-paper
Initialized: /path/to/.work/attention-paper
Stage: initialized
Next: paperflow parse .work/attention-paper
```

### Parsing
```bash
$ uv run paperflow parse .work/attention-paper
Parser used: pymupdf
Warnings: 0
Next semantic step: read source/parsed-paper.md and write source/paper-ir.json
```

### Evidence Building
```bash
$ uv run paperflow build-evidence .work/attention-paper
Evidence map built: 87 references
Semantic packet: .work/attention-paper/source/semantic-packet.md
Next: Author source/paper-ir.json, then run `paperflow validate-ir`.
```

### Paper IR Authoring
Claude reads semantic packet, parsed markdown, and page images. Authors `paper-ir.json`.

### IR Validation
```bash
$ uv run paperflow validate-ir .work/attention-paper
Paper IR valid.
Evidence coverage: 100%
Stage: ir_ready
Next: author report/report-outline.json and report/academic-report.qmd.
```

### Report Authoring
Claude scaffolds report outline, then writes full prose in `academic-report.qmd`.

### Storyboard Authoring
Claude designs 14-slide storyboard with assertion titles.

### Rendering
```bash
$ uv run paperflow render-report .work/attention-paper
Report rendered: academic-report.docx, academic-report.pdf

$ uv run paperflow render-slides .work/attention-paper
Slides rendered: presentation.pptx, speaker-notes.md
```

### Content QA
```bash
$ uv run paperflow qa-content .work/attention-paper
Content QA: PASS
Evidence references: 100%
Report/deck contribution alignment: PASS
Numeric result alignment: PASS
Placeholder scan: PASS
Stage: content_qa_passed
```

### Visual QA
Claude renders previews, inspects slide images, finds minor text overflow on slide 7, fixes storyboard, re-renders, and validates.

```bash
$ uv run paperflow validate-visual-review .work/attention-paper
Visual review: PASS
Fix cycles: 1
Stage: visual_qa_passed
```

### Finalization
```bash
$ uv run paperflow finalize .work/attention-paper
Finalized: dist/attention-is-all-you-need/
  report/academic-report.docx
  report/academic-report.pdf
  slides/presentation.pptx
  slides/presentation.pdf
  slides/speaker-notes.md
Final manifest: qa/final-manifest.json
```
