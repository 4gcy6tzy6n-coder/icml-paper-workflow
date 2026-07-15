# Architecture

## Overview

PaperFlow is a hybrid semantic-deterministic pipeline. Claude Code performs the semantic work (paper interpretation, prose writing, storyboard design, visual review). Deterministic Python and TypeScript tools handle parsing, schema validation, rendering, evidence validation, and workspace management.

## Responsibility Boundaries

```
models/         Schemas only. No I/O, no external processes.
ingest/         PDF→structured document conversion. No interpretation.
evidence/       Stable source units and evidence reference validation.
report/         Deterministic scaffold/render/validate. Claude writes prose.
slides/         Deterministic PPTX generation. Claude writes storyboard.
qa/             Cross-artifact checks and preview/finalization.
util/           Shared helpers (JSON I/O, hashing, commands).
```

## State Machine

```
INITIALIZED -> PARSED -> REQUIREMENTS_READY -> IR_READY -> REPORT_READY
    -> STORYBOARD_READY -> RENDERED -> CONTENT_QA_PASSED
    -> VISUAL_QA_PASSED -> FINALIZED
```

Each transition is enforced by the `paperflow` CLI. Invalid transitions exit with code 2 and do not modify the workspace.

## Authoring Requirements Gate

The project skill owns conversational intake and asks one question at a time. Deterministic code validates source/authoring-requirements.json; it does not interview the user or invent missing answers. confirmation.content_sha256 binds the confirmation to canonical requirements content, and source.pdf_sha256 binds the record to manifest.json. Missing, invalid, edited, or wrong-paper requirements produce qa/requirements-validation.json and leave the workflow stage unchanged.

## Canonical Data Flow

```
  parsed-paper.md + evidence-map.json  ← Deterministic extraction
                   │
                   ▼
  one-question-at-a-time requirements intake  ← Project skill
                   │ explicit confirmation
                   ▼
  source/authoring-requirements.json
                   │ paperflow validate-requirements
                   ▼
             REQUIREMENTS_READY
                   │
                   ▼
             paper-ir.json  ← Project skill authors (canonical)
                   │ paperflow validate-ir
                   ▼
                IR_READY
                   │
           ┌───────┴───────┐
           ▼               ▼
       report.qmd     storyboard.json  ← Project skill authors
           │               │
           ▼               ▼
       .docx/.pdf       .pptx/.pdf     ← Deterministic renderers
```

No renderer may independently reinterpret the source paper.

## Key Design Decisions

- **Shared IR**: Report and slides consume the same `paper-ir.json`, ensuring consistency.
- **Stable evidence IDs**: Text block IDs (`p01-b001`) are deterministic across parse runs.
- **Atomic writes**: All JSON writes use `.tmp` → rename pattern.
- **Editable PPTX**: Layouts position text/shapes programmatically; no rasterized slides.
- **Optional parsers**: When `MINERU_API_KEY` exists, the MinerU API signed-upload
  flow is preferred and its raw JSON is retained for auditability. Local MinerU
  and MarkItDown remain optional; PyMuPDF is the hard floor.
