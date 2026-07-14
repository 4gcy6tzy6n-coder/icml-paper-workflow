# Authoring Requirements Intake

## Hard Gate

Ask one question at a time after parse and evidence generation. Do not author `paper-ir.json`, report prose, storyboard content, or rendered artifacts until `paperflow validate-requirements` passes.

Do not let urgency, defaults, ambiguity, resume state, or a request to skip questions bypass the one-question-at-a-time intake or explicit confirmation. Treat a `PARSED` workspace or partial answers as unresolved requirements, not as approval.

## Fixed Core Topics

Cover use scenario, target audience, report, presentation, content priorities, technical depth, language, visual direction, template and brand constraints, and evidence and delivery boundaries.

## Adaptive Follow-up

Ask an adaptive follow-up for ambiguity, contradiction, or a paper-specific choice. Recommend a default only when the user does not know, explain its effect, and record it as an assumption only after acceptance.

## Summary and Explicit Confirmation

Show one complete summary after every topic is resolved. Require explicit confirmation. Do not treat silence, earlier partial approvals, urgency, or a request to proceed without questions as confirmation.

## JSON and Digest

After confirmation, write only `source/authoring-requirements.json`. Do not write a Markdown requirements copy. Copy `source.pdf_sha256` from `manifest.json`. Use `compute_requirements_digest` for `confirmation.content_sha256`. Run `validate-requirements` and continue only after PASS.

## Resume and Safety

Reuse a valid confirmed record only for the same PDF. Do not treat resume state alone as confirmation. Re-interview unresolved or invalid fields and reconfirm edits. Never request or persist credentials, API keys, tokens, passwords, or unrelated personal information.
