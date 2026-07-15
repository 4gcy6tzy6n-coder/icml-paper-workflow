# Expected Session Transcript

This transcript shows evidence-first intake and the mandatory report-and-presentation
workflow for one sample ICML paper.

## User Prompt

```text
Use the icml-paper-to-report-deck skill on ~/papers/attention-paper.pdf.
Create the workspace under .work/attention-paper and complete every gate.
```

## Expected Flow

### Environment and Initialization

```bash
$ uv run paperflow doctor
All required tools available.

$ uv run paperflow init ~/papers/attention-paper.pdf .work/attention-paper
Initialized: /path/to/.work/attention-paper
Stage: initialized
Next: paperflow parse .work/attention-paper
```

### Parse, Then Evidence

```bash
$ uv run paperflow parse .work/attention-paper
Parser used: pymupdf
Next: run paperflow build-evidence, complete the Skill requirements interview.

$ uv run paperflow build-evidence .work/attention-paper
Evidence map built: 87 references
Semantic packet: .work/attention-paper/source/semantic-packet.md
Next: complete the Skill requirements interview.
```

The Skill verifies both evidence outputs before asking any requirements question.

### Field-level intake

The Skill asks exactly one question at a time. A representative full exchange is:

1. **Q:** What will you use the report and presentation for?
   **A:** A graduate machine-learning reading group.
2. **Q:** What outcome should the audience leave with?
   **A:** Understand the contribution, evidence, and limitations well enough to discuss
   follow-up work.
3. **Q:** What is the audience role?
   **A:** Graduate students.
4. **Q:** What background can I assume?
   **A:** Core machine learning and Transformer fundamentals.
5. **Q:** How familiar are they with this topic?
   **A:** Intermediate.
6. **Q:** What is the report's purpose?
   **A:** A durable paper-reading report for preparation and review.
7. **Q:** What rendered page range should the report meet?
   **A:** 8–10 pages.
8. **Q:** What Chinese-character range should it meet?
   **A:** 7,500–9,000 Chinese characters.
9. **Q:** Which report topics should receive the most attention?
   **A:** The gating method, headline results, ablations, and limitations.
10. **Q:** Which topics should be de-emphasized?
    **A:** A paper-by-paper retelling of related work.
11. **Q:** What technical depth do you want?
    **A:** Deep, but explain equations in prose.
12. **Q:** What narrative structure do you prefer?
    **A:** Problem → gap → method → evidence → limitations.
13. **Q:** In what reading context will the report be used?
    **A:** Before and after the live reading group.
14. **Q:** What is the presentation's purpose?
    **A:** Lead a concise live discussion.
15. **Q:** What talk duration should it support?
    **A:** 18 minutes.
16. **Q:** What slide range should it meet?
    **A:** 12–14 slides.
17. **Q:** Which presentation topics should receive priority?
    **A:** Motivation, method flow, two result slides, one limitation slide, and discussion.
18. **Q:** What is the speaking context?
    **A:** Live, with questions held until the end.
19. **Q:** Should English technical terms be preserved?
    **A:** Yes.
20. **Q:** What translation convention should I follow?
    **A:** Chinese narrative, with method, dataset, and metric names in English.
21. **Q:** What visual direction should both artifacts use?
    **A:** Restrained academic styling with high information hierarchy.
22. **Q:** Are there brand requirements?
    **A:** No.
23. **Q:** Are there accessibility requirements?
    **A:** High contrast and no color-only encodings.
24. **Q:** What citation detail do you expect?
    **A:** Every substantive claim should trace to paper evidence; show compact source
    footers on slides.
25. **Q:** Are there any additional constraints?
    **A:** Do not overstate performance or hide unfavorable results.

The Skill then explains the fixed v1 policy: Chinese output; both report and presentation;
QMD, DOCX, report PDF, PPTX, slides PDF, and speaker notes; original figures only; no web
research; fixed PaperFlow template/names; and `dist/<paper-slug>` delivery. The user did not
accept a recommended default, so `assumptions` is empty.

### Complete summary

The Skill shows the complete schema-mapped summary: source identity; use case; all audience
fields; both purposes; the 8–10-page and 7,500–9,000-character report targets; report focus,
de-emphasis, depth, narrative, and reading context; the 18-minute and 12–14-slide
presentation targets; presentation focus and speaking context; language and terminology;
visual, brand, and accessibility settings; evidence and citation policy; all six fixed
formats; fixed output/naming policy; constraints; and the empty assumptions list.

### Explicit confirmation

The Skill asks: “Is this complete summary correct, and may I seal it for this PDF?”
The user answers: “Yes, confirm and seal exactly this summary.”

### Digest and Write

The Skill sets `confirmation.status=confirmed` and `confirmation.confirmed_at`, then calls
the production `compute_requirements_digest` helper for
`confirmation.content_sha256`. Only after that calculation does it write
`source/authoring-requirements.json` with the project JSON writer.

```bash
$ uv run paperflow validate-requirements .work/attention-paper
Requirements validation: PASS
Stage: requirements_ready
Next: author source/paper-ir.json and run paperflow validate-ir.
```

For same-PDF resume validation, the Skill checks the source digest and current sealed file;
it never trusts the stage by itself.

### Paper IR Authoring

Only now does the Skill read the requirements, semantic packet, parsed markdown, and page
images and author `source/paper-ir.json`.

```bash
$ uv run paperflow validate-ir .work/attention-paper
Paper IR valid.
Evidence coverage: 100%
Stage: ir_ready
```

### Report and Storyboard Authoring

The report is authored to the confirmed 8–10-page and 7,500–9,000-character targets. The
storyboard is authored to the confirmed 12–14-slide and 18-minute targets. Focus,
de-emphasis, audience, terminology, citations, visual rules, and constraints govern both.

```bash
$ uv run paperflow scaffold-report .work/attention-paper
$ uv run paperflow validate-report .work/attention-paper
Report validation: PASS
Stage: report_ready

$ uv run paperflow render-report .work/attention-paper
Report rendered successfully.

$ uv run paperflow validate-storyboard .work/attention-paper
Storyboard validation: PASS
Stage: storyboard_ready

$ uv run paperflow render-slides .work/attention-paper
Stage: rendered
```

### Content and Visual QA

```bash
$ uv run paperflow qa-content .work/attention-paper
Content QA: PASS
Stage: content_qa_passed

$ uv run paperflow render-preview .work/attention-paper
$ uv run paperflow validate-visual-review .work/attention-paper
Visual review: PASS
Stage: visual_qa_passed
```

The content QA record includes the measured Chinese-character, report-page, and slide
counts and checks each against the confirmed ranges.

### Finalization

```bash
$ uv run paperflow finalize .work/attention-paper
Finalized: dist/attention-is-all-you-need/
  report/academic-report.qmd
  report/academic-report.docx
  report/academic-report.pdf
  slides/presentation.pptx
  slides/presentation.pdf
  slides/speaker-notes.md
  source/authoring-requirements.json
Final manifest: qa/final-manifest.json
```

The final manifest records the sealed requirements digest and `valid: true`.
