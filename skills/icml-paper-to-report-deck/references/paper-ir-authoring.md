# Paper IR Authoring Instructions

## Sequence

1. Read `source/semantic-packet.md` for metadata, evidence index, and asset registry.
2. Read `source/parsed-paper.md` for full paper text with block anchors.
3. Inspect `assets/page-images/page-*.png` for figures and tables that text parsing may have missed.
4. Draft `source/paper-ir.draft.json` using the schema.
5. Check **every claim** against at least one evidence block. Re-read the source text.
6. Rename draft to `source/paper-ir.json`.
7. Run `paperflow validate-ir <workspace>`.
8. Fix validation errors. Re-run validation until it passes with zero errors.

## What to Extract

### Metadata
- Title, authors, venue (default "ICML"), year, abstract.
- Copy author names exactly as printed.

### Research Problem
- Context: the broader domain.
- Practical problem: what real-world issue motivates this work.
- Technical problem: the specific technical challenge.
- Existing gap: what prior work does not address.
- Research question: what this paper sets out to answer.

### Contributions
- List 2–5 specific contributions.
- Include novelty assessment.
- Ground each in author-stated claims.

### Method Overview and Components
- Write a concise method overview (2–3 sentences).
- List each key component with its purpose, mechanism, inputs, and outputs.
- Preserve mathematical notation; do not paraphrase equations into prose if the equation is informative.

### Experimental Setup
- Extract datasets, baselines, and metrics lists exactly as named.
- Summarize implementation details.

### Numeric Results
- Extract headline numbers with metric names, values, and comparison text.
- Mark direction: higher_better, lower_better, or neutral.
- Quote the source text for each number.

### Findings
- Classify each finding as headline, supporting, or secondary.
- Distinguish author-stated from analyst-inferred.

### Limitations
- Extract author-stated limitations verbatim.
- You may add analyst-inferred limitations, but label them explicitly.
- Include implications where the paper discusses them.

## What NOT to Do

- Do not infer venue awards or "excellent paper" status unless the PDF states it.
- Do not claim SOTA unless the paper explicitly supports it.
- Do not convert relative improvements to absolute incorrectly.
- Do not omit unfavorable results.
- Do not treat appendix-only findings as main findings without labeling.
- Do not add external background facts in v1.
- Do not invent evidence IDs; use only IDs from the evidence map.
