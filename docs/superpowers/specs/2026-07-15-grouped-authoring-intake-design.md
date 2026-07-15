# Grouped Authoring Intake Design

**Date:** 2026-07-15
**Status:** Approved design
**Selected approach:** Adaptive three-to-five-round grouped intake (Approach A)

## Goal

Reduce the PaperFlow authoring-requirements interview from roughly 25 field-level
questions to a normal successful path of three to five conversation rounds. Each round
collects a coherent group of related requirements. The final complete-summary confirmation
counts as one of those rounds.

The change must preserve the complete requirements schema, explicit confirmation,
PDF-bound digest, validation gate, and downstream report and presentation behavior.

## Round Definition and Budget

A round is one grouped assistant prompt followed by one substantive user response. The
Skill uses no more than four information-collection rounds before the complete-summary
confirmation, and targets three to five total rounds on a normal successful path.

- Three rounds: use when the user has already supplied a detailed brief and only two
  grouped prompts are needed before confirmation.
- Four rounds: use as the normal path—three grouped prompts followed by confirmation.
- Five rounds: use when one grouped supplemental prompt is needed to resolve omissions or
  contradictions before confirmation.

If the user rejects or edits the final summary, the Skill must show the revised summary
and obtain confirmation again. This correction cycle is a confirmation-integrity
exception, not a reason to restart the interview or repeat resolved questions.

## Conversation Contract

### Round group 1: purpose, audience, and language context

Collect the use scenario, desired outcome, audience role, audience background, subject
familiarity, English-term preference, and translation preference in one compact numbered
prompt.

### Round group 2: report and presentation constraints

Collect report purpose, page and Chinese-character ranges, reading context, presentation
purpose, duration, slide range, and speaking context in one compact numbered prompt. State
fixed output formats and the required speaker notes as policy rather than asking the user
to choose them.

### Round group 3: content, style, evidence, and delivery boundaries

Collect focus topics, de-emphasized topics, technical depth, narrative preference, visual
style, brand and accessibility requirements, citation expectations, user constraints, and
accepted assumptions. State the fixed evidence, template, delivery, and naming policies
without turning them into questions.

### Optional supplemental round

Ask one consolidated supplemental prompt only when a required value remains missing,
ambiguous, contradictory, or non-executable. Include only unresolved items. Never repeat
fields already answered explicitly or derivable from the user's supplied brief.

### Final confirmation round

Show a complete schema-mapped summary containing source identity, all fixed values, every
user-supplied value, ranges, populated or empty lists, constraints, and assumptions. Ask
for one explicit confirmation that the summary may be sealed for the current PDF.

## Adaptive Behavior

Before each prompt, mark fields already resolved by the user's initial request or earlier
responses. Merge or skip groups when doing so preserves clarity, while keeping the normal
successful path within three to five rounds. Accept a natural-language response or a
numbered response; do not require the user to reproduce field names.

Do not silently invent missing values. When the user does not know a value, include a
concise recommendation and its effect in the next unresolved-items prompt. Persist a
recommendation only after the user accepts it, and record it in `assumptions`.

Retain the existing contradiction checks for page and character targets, duration and
slide targets, focus versus de-emphasis, and paper-specific terms. Resolve all detected
issues in the optional supplemental round whenever possible.

## Data Flow and Boundaries

The deterministic pipeline remains unchanged:

1. Parse the PDF and build evidence.
2. Conduct grouped conversational intake.
3. Present and explicitly confirm the complete summary.
4. Write only `source/authoring-requirements.json` using the existing production digest
   helper and JSON writer.
5. Run `paperflow validate-requirements` and continue only at `REQUIREMENTS_READY`.

No requirements schema, CLI command, digest algorithm, workflow stage, MinerU integration,
report authoring logic, or presentation authoring logic changes in this feature.

## Resume and Error Handling

- Reuse a valid confirmed record for the same PDF without re-interviewing the user.
- For an incomplete or invalid record, ask only for unresolved fields and reconfirm the
  complete revised summary.
- Never bypass explicit confirmation because of urgency or a request to skip questions.
- Never request or persist credentials, API keys, tokens, passwords, or unrelated personal
  information.
- Treat non-answers as unresolved; do not seal incomplete requirements merely to satisfy
  the target round count.

## Documentation and Examples

Update the project Skill, requirements-intake reference, expected-session example, README,
architecture overview, and active workflow contract to describe grouped intake. Historical
design and implementation-plan files remain historical; this specification supersedes
their one-question-at-a-time interaction rule.

The expected-session example must demonstrate a successful four-round exchange: three
grouped information rounds and one complete-summary confirmation.

## Testing

Contract tests must verify that:

- the Skill targets three to five total rounds and counts confirmation as a round;
- the three required information groups are present;
- known fields are skipped rather than asked again;
- at most one consolidated supplemental round is used on the normal path;
- every existing schema field remains mapped;
- adaptive contradiction handling and explicit confirmation remain mandatory;
- JSON-only persistence, digest generation, validation ordering, resume safety, and secret
  handling remain unchanged;
- the expected-session example demonstrates grouped intake before Paper IR authoring.

Run the focused Skill contract tests first, followed by the full project verification
suite. No generated report or presentation regression is expected because the sealed JSON
interface is unchanged.

## Acceptance Criteria

1. A normal cooperative user completes requirements intake and confirmation in three to
   five rounds.
2. The default example completes in four rounds.
3. Each prompt groups related fields and accepts one information-rich response.
4. The Skill never repeats known fields and uses only one supplemental grouped prompt on
   the normal path.
5. The same complete, confirmed `authoring-requirements.json` contract continues to govern
   both report and presentation generation.
