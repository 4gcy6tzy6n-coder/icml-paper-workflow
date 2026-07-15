---
name: icml-paper-to-report-deck
description: Use when converting one local English machine-learning research paper PDF into a source-grounded Chinese academic report and presentation.
---

# ICML Paper to Report and Deck

Convert one English ICML-style paper PDF into a source-grounded Chinese academic report (`.qmd`, `.docx`, `.pdf`) and an editable Chinese presentation (`.pptx`, `.pdf`, speaker notes), with shared evidence, deterministic rendering, and mandatory content/visual QA.

## Trigger Conditions

Use this skill when:
- The user provides a research paper PDF and asks for the PaperFlow report-and-deck workflow.
- The user says "paperflow", "paper to report", "paper to slides", or references ICML/NeurIPS/ML conference paper conversion.
- The input is one local PDF file and the output language is Chinese.

## Accepted Input

- One local PDF file (English, ICML-style conference paper).
- Output language is fixed to `zh-CN`.
- Graduate-student audience and a 15-minute, 13–15-slide talk are recommendations only.
  They govern authoring only if the user explicitly accepts them and they are persisted.

## Required Environment Check

Before starting, verify the environment:

```bash
uv run paperflow doctor
```

All required tools (Python, uv, Node, pnpm, Quarto, LibreOffice, Poppler, PyMuPDF) must be available. Optional tools (MinerU, MarkItDown) improve parsing quality but are not required.

## Workflow

### 1. Workspace Initialization

```bash
uv run paperflow init <path/to/paper.pdf> .work/<paper-name>
```

This copies the PDF into the workspace, creates directories, and initializes the state machine at `INITIALIZED`.

### 2. Parse and Evidence Generation

```bash
uv run paperflow parse .work/<paper-name>
```

This runs the parser chain (MinerU → MarkItDown → PyMuPDF fallback), extracts text blocks, renders page images, detects figures/tables, and builds the evidence map. On success, advances to `PARSED`.

```bash
uv run paperflow build-evidence .work/<paper-name>
```

Generates `source/evidence-map.json` and `source/semantic-packet.md`.

### 3. Authoring Requirements Intake

Read `references/requirements-intake.md` completely. Ask one question at a time, resolve all fixed and adaptive topics, present the complete summary, and obtain explicit confirmation. Then write `source/authoring-requirements.json` and run:

```bash
uv run paperflow validate-requirements .work/<paper-name>
```

Do not begin Paper IR authoring until this command passes and the workspace reaches `REQUIREMENTS_READY`. Every later PaperFlow CLI boundary revalidates the exact sealed requirements. Both report and slide authoring must read `source/authoring-requirements.json` and `source/paper-ir.json`.

Use confirmed use_case.audience role, background, and familiarity for explanation depth
and examples; do not assume a graduate-student audience. If language.preserve_english_terms is false, follow language.translation_preferences
instead of retaining English terms by default. Use confirmed visual.style, brand, and
accessibility fields for both artifacts; any built-in layout or palette is subordinate.

### 4. Paper IR Authoring

**Read the following files:**

1. `source/semantic-packet.md` — metadata guesses, evidence index, asset registry
2. `source/parsed-paper.md` — full paper text with block anchors
3. `assets/page-images/page-*.png` — page images for visual inspection

**Author `source/paper-ir.json`:**

Follow the instructions in `references/paper-ir-authoring.md`:

- Extract metadata, research problem, contributions, method overview, method components, experimental setup, numeric results, findings, and limitations.
- Every claim must reference at least one valid `evidence_id`.
- Distinguish `author_stated` from `analyst_inferred` claims.
- Do not invent facts, numbers, or external background.
- Do not claim SOTA unless the paper explicitly does.
- Do not omit unfavorable results.

Write to `source/paper-ir.draft.json`, review against evidence, then rename to `source/paper-ir.json`.

### 5. IR Validation Loop

```bash
uv run paperflow validate-ir .work/<paper-name>
```

On failure (exit code 4), read the errors in `qa/ir-validation.json`, fix `source/paper-ir.json`, and retry. Repeat until zero errors. On success, advances to `IR_READY`.

### 6. Report Outline and Full Prose

**Two-stage writing:**

**Stage A — Outline:**
```bash
uv run paperflow scaffold-report .work/<paper-name>
```

This creates a `report/report-outline.json` with 16 planned sections.

**Stage B — Full prose:**

Write `report/academic-report.qmd` following `references/report-style.md`:

- Use the confirmed `report.target_chinese_characters` and `report.target_pages` ranges.
- In operational terms: use confirmed report.target_chinese_characters and confirmed report.target_pages;
  never replace them with a project recommendation.
- Apply the confirmed report purpose, focus/de-emphasis, depth, narrative, reading context,
  audience, terminology, visual, citation, constraint, and assumption fields.
- Use full paragraphs, not bullet points.
- Every substantive paragraph must end with: `<!-- evidence: ev-pXX-bYYY -->`
- If `language.preserve_english_terms` is true, preserve English technical terms as directed;
  otherwise translate them according to `language.translation_preferences`.
- Distinguish author statements from analyst inferences.
- Include 2–5 original figures/tables using relative paths.

Validate the report:
```bash
uv run paperflow validate-report .work/<paper-name>
```

On success, advances to `REPORT_READY`.

### 7. Storyboard Authoring

Write `slides/storyboard.json` following `references/slide-storytelling.md`:

- Use the confirmed `presentation.target_slides` and `presentation.duration_minutes`.
- In operational terms: use confirmed presentation.target_slides and confirmed presentation.duration_minutes;
  never replace them with a project recommendation.
- Apply the confirmed presentation purpose, focus, speaking context, audience, terminology,
  visual, citation, constraint, and assumption fields.
- Every slide title must be an assertion, not a section label.
- 2–5 body lines per slide (max 6).
- Maximum 520 characters of visible text per slide.
- Speaker notes minimum 20 characters per slide.
- Every slide except title/Q&A must have evidence.
- Result slides require evidence tied to a `NumericResult`.

Validate the storyboard:
```bash
uv run paperflow validate-storyboard .work/<paper-name>
```

On success, advances to `STORYBOARD_READY`.

### 8. Deterministic Render

**Report rendering:**
```bash
uv run paperflow render-report .work/<paper-name>
```

Uses Quarto → DOCX, then LibreOffice → PDF.

**Slides rendering:**
```bash
uv run paperflow render-slides .work/<paper-name>
```

Generates `slides/presentation.pptx` and `slides/speaker-notes.md`. PPTX text, titles, captions, labels, and shapes remain editable. Full-slide screenshots are forbidden.

On success, advances to `RENDERED`.

### 9. Content QA

```bash
uv run paperflow qa-content .work/<paper-name>
```

Checks:
- Cross-artifact consistency (contributions, datasets, baselines, metrics, numeric results, limitations).
- Evidence reference validity.
- Placeholder detection.
- Selected asset usage.
- Confirmed report Chinese-character/page ranges and presentation slide range when the
  corresponding artifacts are available.

On success, advances to `CONTENT_QA_PASSED`.

If content QA reports `REPORT_PDF_MISSING` or `REPORT_PAGE_TARGET_MISSED`, correct the
report source or render settings, rerun `paperflow render-report` while the workspace
remains at `RENDERED`, and rerun `paperflow qa-content`. Do not edit QA output to bypass
the confirmed range.

### 10. Visual QA with Mandatory Fix Cycle

**Step 1 — Render previews:**
```bash
uv run paperflow render-preview .work/<paper-name>
```

Generates `qa/slide-images/slide-NNN.png` and `qa/contact-sheet.png`.

**Step 2 — Inspect:**

Read `qa/contact-sheet.png` and each `qa/slide-images/slide-NNN.png`. Check for issues listed in `references/qa-rubrics.md`.

**Step 3 — Write review:**

Create `qa/visual-review.json` with inspection results. Record at least one inspection pass. If no issue is found, inspect again more carefully.

**Step 4 — Fix and re-render:**

If issues are found, fix the storyboard or layout configuration, then:
```bash
uv run paperflow render-slides .work/<paper-name>
uv run paperflow render-preview .work/<paper-name>
```
Update `visual-review.json` with `rerendered: true`.

**Step 5 — Final validation:**
```bash
uv run paperflow validate-visual-review .work/<paper-name>
```

On success, advances to `VISUAL_QA_PASSED`.

### 11. Finalization

```bash
uv run paperflow finalize .work/<paper-name>
```

Copies the fixed report and presentation artifact set plus the sealed requirements audit
record to `dist/<paper-slug>/`. It writes `qa/final-manifest.json` with checksums, tool
versions, QA results, and requirements digest/validity.

### 12. Failure and Resume

- If any command fails, read the error message and fix the source artifacts (not the QA files).
- The state machine prevents running commands out of order.
- Resume from the current valid stage: check `uv run paperflow status .work/<paper-name>`.

### 13. Completion Message

When finalization succeeds, report:
- Confirmation that `validate-requirements` passed and the confirmed requirements governed both artifacts.
- Paper title and slug.
- Output paths under `dist/<paper-slug>/`.
- Evidence coverage percentage.
- Quality scores.
- Any non-blocking warnings.

## Critical Prohibitions

- **NO web research** — do not search for external context about the paper.
- **NO regenerating experimental figures** — use only original paper figures.
- **NO unsupported numerical claims** — every number must trace to evidence.
- **NO full-slide screenshots** — PPTX text must remain editable.
- **NO skipping visual QA** — at least one fix-and-reverify cycle is required.
- **NO external LLM API** — Claude Code performs semantic work; Python/TypeScript is deterministic.
