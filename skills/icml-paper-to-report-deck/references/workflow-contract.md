# Workflow Contract

## State Machine

The workflow progresses through these exact stages:

```
INITIALIZED -> PARSED -> REQUIREMENTS_READY -> IR_READY -> REPORT_READY -> STORYBOARD_READY -> RENDERED -> CONTENT_QA_PASSED -> VISUAL_QA_PASSED -> FINALIZED
```

Each stage transition is enforced by the `paperflow` CLI. Attempting a command at the wrong stage exits with code 2.

## Commands

| Stage | Command | Action |
|-------|---------|--------|
| Any | `paperflow init PDF WORKSPACE` | Initialize workspace |
| INITIALIZED | `paperflow parse WORKSPACE` | Parse PDF, extract assets |
| PARSED | Skill completes the requirements interview | Ask one question at a time and obtain explicit confirmation |
| PARSED | `paperflow validate-requirements WORKSPACE` | Validate `authoring-requirements.json` -> REQUIREMENTS_READY |
| REQUIREMENTS_READY | Skill authors `paper-ir.json` | Semantic interpretation from confirmed requirements and evidence |
| REQUIREMENTS_READY | `paperflow validate-ir WORKSPACE` | Validate IR -> IR_READY |
| IR_READY | (Claude authors report and storyboard) | Prose and slide design |
| IR_READY | `paperflow scaffold-report WORKSPACE` | Create report outline |
| REPORT_READY | `paperflow render-report WORKSPACE` | Render DOCX/PDF |
| REPORT_READY | (Claude authors `storyboard.json`) | Slide design |
| STORYBOARD_READY | `paperflow render-slides WORKSPACE` | Render PPTX |
| RENDERED | `paperflow qa-content WORKSPACE` | Content QA |
| CONTENT_QA_PASSED | `paperflow render-preview WORKSPACE` | Preview images |
| CONTENT_QA_PASSED | (Claude writes `visual-review.json`) | Visual inspection |
| VISUAL_QA_PASSED | `paperflow finalize WORKSPACE` | Copy to dist/ |

## Idempotency

- Rerunning a command at its valid stage is safe.
- Commands at invalid stages produce exit code 2 and do not modify the workspace.
- No command silently overwrites user-authored artifacts.
