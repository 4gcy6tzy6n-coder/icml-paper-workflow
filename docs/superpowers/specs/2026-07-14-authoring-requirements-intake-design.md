# Authoring Requirements Intake Design

**Date:** 2026-07-14
**Status:** Approved for implementation
**Scope:** Extend the existing `icml-paper-to-report-deck` skill with a mandatory, validated requirements interview before semantic authoring begins.

## Goal

PaperFlow must ask the user for complete report and presentation requirements, summarize those requirements, obtain explicit confirmation, and validate a canonical JSON record before it authors `paper-ir.json`, the Chinese report, or the slide storyboard.

## User Experience

The deterministic PDF parse and evidence build run first. The skill then reads the paper title, abstract, section structure, and asset registry so that its questions can refer to the actual paper without interpreting it into deliverables.

The interview follows these rules:

1. Ask exactly one question at a time.
2. Cover every fixed core topic before completion.
3. Ask adaptive follow-up questions when an answer is ambiguous, internally inconsistent, or suggests a paper-specific priority.
4. Recommend project defaults when the user does not know an answer, but label every accepted default as an assumption.
5. Do not author the Paper IR, report prose, storyboard, or rendered artifacts while any required answer remains unresolved.
6. Present a complete requirements summary after the interview.
7. Write the canonical JSON only after the user explicitly confirms that summary.

The fixed core topics are:

- use scenario and desired outcome;
- target audience and prior knowledge;
- report purpose, target length, formats, and reading context;
- presentation purpose, duration, target slide count, and speaker-note needs;
- content priorities and topics to de-emphasize;
- desired technical depth;
- output language and English-term preservation;
- visual direction;
- template, brand, and institutional constraints;
- evidence, citation, external-research, figure-use, delivery-format, and output-location boundaries.

## Workflow Architecture

Add `requirements_ready` as a first-class workflow stage:

```text
initialized -> parsed -> requirements_ready -> ir_ready -> report_ready
            -> storyboard_ready -> rendered -> content_qa_passed
            -> visual_qa_passed -> finalized
```

The `parsed -> requirements_ready` transition occurs only through a successful `paperflow validate-requirements WORKSPACE` command. `paperflow validate-ir` must require `requirements_ready`; it must not accept `parsed`.

The skill remains responsible for the conversational interview and adaptive questioning. The CLI is deterministic: it validates the saved requirements, writes a QA result, and advances the state. PaperFlow will not add a duplicate terminal questionnaire.

## Canonical Requirements Record

The single persisted intake artifact is:

```text
WORKSPACE/source/authoring-requirements.json
```

No Markdown copy is generated. The JSON is the canonical requirements source for the Paper IR, report, storyboard, QA, resumption, and audit.

The Pydantic model contains the following top-level fields:

- `schema_version`: fixed workflow schema version.
- `source`: PDF SHA-256 and paper title.
- `use_case`: scenario, desired outcome, audience role, audience background, and subject familiarity.
- `report`: required flag, purpose, target pages, target Chinese-character range, formats, focus topics, de-emphasized topics, technical depth, and narrative preference.
- `presentation`: required flag, purpose, duration in minutes, target slide range, focus topics, speaker-note requirement, and speaking context.
- `language`: locale, English-term preservation, and translation preferences.
- `visual`: style description, optional template path, brand requirements, and accessibility requirements.
- `evidence_policy`: external-research permission, generated-result-figure permission, original-figure preference, and citation expectations.
- `deliverables`: requested output formats and output-location requirements.
- `user_constraints`: additional explicit constraints.
- `assumptions`: defaults or interpretations accepted by the user.
- `confirmation`: status, confirmation time, and content digest.

Required free-text values must be non-blank. Numeric ranges must be positive, ordered, and internally consistent. Report and presentation details are required when their corresponding `required` flag is true. The default project configuration may be recommended, but it is not silently substituted for a missing answer.

## Confirmation Integrity

`confirmation.status` must equal `confirmed`. `confirmation.content_sha256` is the SHA-256 of a canonical JSON serialization of every requirements field except `confirmation`. The validator recomputes the digest.

The requirements module exposes one deterministic canonicalization and digest function. The skill calls that project helper after explicit user confirmation, and validation calls the same helper when checking the saved record; the conversational model does not construct the digest independently.

Any content edit after confirmation causes a digest mismatch and invalidates the record. The skill must then show the revised summary and obtain a new explicit confirmation before replacing the confirmation time and digest.

The source PDF digest in `source.pdf_sha256` must equal the digest in `manifest.json`. A requirements record cannot be reused for a different paper.

## Components

The implementation adds or changes these bounded units:

- A requirements model module defines the schema and cross-field validation only.
- A requirements validator verifies source identity, confirmation integrity, and semantic completeness and returns structured validation issues.
- `WorkspacePaths` exposes the canonical requirements path.
- The workflow state and transition map include `requirements_ready`.
- The CLI command validates the record, writes `qa/requirements-validation.json`, and advances the state only on success.
- The existing project skill gains an intake section and a focused reference describing question order, adaptive follow-ups, summary construction, confirmation, and resumption.
- README and architecture documentation describe the new gate and command.

The report and slide renderers do not interpret the requirements independently. Semantic authoring reads both `authoring-requirements.json` and the canonical `paper-ir.json` so the two deliverables remain aligned.

## Failure and Recovery

Validation fails with exit code 4 and leaves the stage unchanged when:

- the requirements file is missing or malformed;
- a required answer is blank or absent;
- report or slide ranges are invalid or contradictory;
- confirmation is missing or not explicit;
- the content digest does not match;
- the source PDF digest does not match the workspace manifest;
- a required output has incomplete settings.

The CLI prints actionable next steps and writes the same issues to `qa/requirements-validation.json`. It never repairs or invents answers.

On resume, the skill reads any existing JSON. A valid confirmed record may proceed without repeating the interview. An incomplete or invalid record left by an interrupted, older, or manually edited workflow is treated as a draft: the skill continues from the first unresolved topic, shows a fresh summary, and requires confirmation again. The current skill does not deliberately persist a new draft before confirmation.

Credentials, API keys, tokens, passwords, and unrelated personal information must never be requested or persisted in the requirements record.

## Testing Strategy

Automated coverage must include:

- model acceptance of a complete requirements record;
- rejection of blank fields, invalid numeric ranges, and incomplete enabled deliverables;
- confirmation digest generation and mismatch detection;
- source PDF digest mismatch detection;
- the `parsed -> requirements_ready -> ir_ready` happy path;
- unchanged stage and exit code 4 for missing, malformed, incomplete, unconfirmed, edited-after-confirmation, and wrong-paper records;
- refusal by `validate-ir` to run from `parsed`;
- success of the existing downstream lifecycle after requirements validation;
- skill contract checks for one-question-at-a-time behavior, all core topics, adaptive follow-ups, explicit summary confirmation, JSON-only persistence, and prohibition of semantic authoring before the gate;
- documentation contract checks for the new command and state.

## Acceptance Criteria

The feature is complete when:

1. A parsed workspace cannot advance to Paper IR validation without a valid, confirmed requirements record.
2. The skill reliably gathers every core topic one question at a time and performs paper-specific follow-up where needed.
3. The user sees and explicitly confirms the full summary before JSON persistence.
4. Confirmed requirements are bound to both their exact content and the exact source PDF.
5. A valid record advances the workflow to `requirements_ready`, after which the existing report-and-deck pipeline completes normally.
6. Unit, CLI, integration, skill-contract, lint, and type checks pass.

## Out of Scope

- A standalone intake skill.
- A terminal-based interactive questionnaire.
- A Markdown requirements summary file.
- Web research during intake.
- Silent defaults or automatic confirmation.
- Changes to the semantic meaning of Paper IR evidence claims.
