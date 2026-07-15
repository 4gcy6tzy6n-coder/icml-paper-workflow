# Authoring Requirements Intake

## Hard Gate and Evidence Prerequisite

Run `paperflow parse` and `paperflow build-evidence` first. Confirm that both
`source/evidence-map.json` and `source/semantic-packet.md` exist. Ask one question at a time
only after those deterministic evidence outputs exist. Do not author `paper-ir.json`,
report prose, storyboard content, or rendered artifacts until
`paperflow validate-requirements` passes.

Do not let urgency, defaults, ambiguity, resume state, or a request to skip questions
bypass the one-question-at-a-time intake or explicit confirmation. Treat a `PARSED`
workspace or partial answers as unresolved requirements, not approval. Fixed v1 pipeline
values below are policies, not questions and not user-selectable alternatives.

## Ordered Field-Level Interview and Checklist

Work through this order. Record an answer only after it is unambiguous. Recommend a
project default only when the user does not know, explain its effect, and add the accepted
recommendation to `assumptions`.

The fixed core topics are use scenario, target audience, report, presentation, content priorities,
technical depth, language, visual direction, template policy, and evidence,
citation, and delivery boundaries.

1. **Source identity (read, do not ask).** Map the manifest digest to
   `source.pdf_sha256`, the parsed paper title to `source.title`, and set
   `schema_version` to `1.0`. Never copy a digest from another workspace.
2. **Use and audience.** Ask the use scenario and intended decision or learning outcome;
   map them to `use_case.scenario` and `use_case.desired_outcome`. Then ask, separately,
   for `use_case.audience.role`, `use_case.audience.background`, and
   `use_case.audience.subject_familiarity` (`beginner`, `intermediate`, `advanced`, or
   `mixed`).
3. **Report.** Explain that `report.required` is fixed to `true`. Ask one question each
   for `report.purpose`, `report.target_pages`, `report.target_chinese_characters`,
   `report.focus_topics`, `report.de_emphasized_topics`, `report.technical_depth`,
   `report.narrative_preference`, and `report.reading_context`. Set `report.formats` to the
   fixed ordered list `qmd`, `docx`, `report_pdf`.
4. **Presentation.** Explain that `presentation.required` and
   `presentation.speaker_notes_required` are fixed to `true`. Ask one question each for
   `presentation.purpose`, `presentation.duration_minutes`,
   `presentation.target_slides`, `presentation.focus_topics`, and
   `presentation.speaking_context`. Set `presentation.formats` to the fixed ordered list
   `pptx`, `slides_pdf`, `speaker_notes`.
5. **Language and terminology.** Set `language.locale` to `zh-CN`. Ask whether English
   technical terms should be retained and map the answer to
   `language.preserve_english_terms`; then ask for `language.translation_preferences`.
6. **Visual direction.** Ask for `visual.style`. Explain that v1 uses the PaperFlow
   template and set `visual.template_path` to `null`. Ask whether brand rules exist. If
   the answer is yes, then ask for each rule and map the list to
   `visual.brand_requirements`; otherwise use an empty list. Ask whether accessibility
   rules exist. If yes, then ask for each rule and map them to
   `visual.accessibility_requirements`; otherwise use an empty list.
7. **Evidence and citations.** Explain the fixed source-grounding policy:
   `evidence_policy.allow_web_research=false`,
   `evidence_policy.allow_generated_result_figures=false`, and
   `evidence_policy.prefer_original_figures=true`. Ask for the desired citation detail and
   map it to `evidence_policy.citation_expectations`.
8. **Delivery.** Explain that the linear v1 pipeline always produces both artifacts. Set
   `deliverables.formats` to `qmd`, `docx`, `report_pdf`, `pptx`, `slides_pdf`,
   `speaker_notes`; set `deliverables.output_location` to `dist/<paper-slug>`; and set
   `deliverables.naming_requirements` to `paperflow-standard`. These fields document the
   finalizer's fixed behavior and are not arbitrary path or naming inputs.
9. **Constraints and assumptions.** Ask for any remaining explicit `user_constraints`.
   Review every recommended default or interpretation already accepted and store only
   those items in `assumptions`. Empty lists are valid after the user says there are none.

## Conditional and Adaptive Follow-Up

If a range is vague, then ask for explicit positive minimum and maximum values. If report
pages and Chinese-character targets appear inconsistent, then ask which constraint has
priority and revise both before continuing. If presentation duration and slide range
conflict, then ask which should govern. If a focus topic is also de-emphasized, then ask
the user to resolve the contradiction. If an answer names a paper-specific method,
experiment, figure, audience need, brand rule, accessibility need, or citation style, then
ask the smallest follow-up needed to make the corresponding field executable.

## Complete Summary Mapping

After all questions and conditional branches are resolved, show one complete summary in
the same field order as the JSON schema. The complete summary must show every fixed value,
every range, every empty or populated list, all constraints, and all assumptions. It must
make clear how report and presentation choices will govern both artifacts.

## Explicit Confirmation

Ask one final question: whether the complete summary is correct and may be sealed. Require
an explicit confirmation. Silence, earlier partial approvals, urgency, or a request to
proceed without questions does not count. On edits, update the summary and ask again. Map
the accepted answer to `confirmation.status=confirmed` and the current timestamp to
`confirmation.confirmed_at`.

## Digest, File Write, and Validation

After confirmation, import the production helper
`paperflow.models.authoring_requirements.compute_requirements_digest`. Build the full
mapping, set `confirmation.status` and `confirmation.confirmed_at`, calculate
`confirmation.content_sha256 = compute_requirements_digest(mapping)`, and then write only
`source/authoring-requirements.json` with `paperflow.util.jsonio.write_json`. Do not write a Markdown requirements copy and do not calculate the digest with an ad hoc serializer.

Run:

```bash
uv run paperflow validate-requirements .work/<paper-name>
```

Continue only after PASS and `Stage: requirements_ready`. A failure is actionable: fix the
source answers, show a revised complete summary, obtain explicit confirmation again,
regenerate the digest with the production helper, write the file, and rerun validation.

## Same-PDF Resume Validation and Safety

For same-PDF resume validation, first compare `source.pdf_sha256` with
`manifest.source_sha256`, then validate the current JSON and its stored workflow seal. At
`PARSED` or `REQUIREMENTS_READY`, rerun `paperflow validate-requirements`; at later stages,
the next PaperFlow CLI boundary performs the same sealed loader check. A missing, malformed,
edited, re-confirmed-but-not-revalidated, or wrong-PDF file is not reusable. Resume the
interview at the first unresolved field and reconfirm any revision.

Never request or persist credentials, API keys, tokens, passwords, or unrelated personal
information.
