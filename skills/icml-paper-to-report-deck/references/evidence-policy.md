# Evidence Policy

## Evidence-Required Claim Classes

Every claim in the Paper IR must reference at least one valid `evidence_id`:

- **Contributions**: Novelty claims must be grounded in the paper text.
- **Findings**: Headline, supporting, and secondary findings each require evidence.
- **Numeric Results**: Every reported number must cite its source block.
- **Limitations**: Both author-stated and analyst-inferred limitations need evidence.
- **Method Components**: Each component's purpose and mechanism must be traceable.
- **Research Problem**: Context and gap statements must reference source blocks.
- **Experimental Setup**: Datasets, baselines, and metrics lists must be verifiable.

## Author-Stated vs Analyst-Inferred

- **author_stated**: The paper explicitly states this claim. Use for direct quotes, explicit comparisons, and labeled limitations.
- **analyst_inferred**: You deduce this from the paper's results or methodology. Always label these explicitly. Never present an inference as an author statement.

## Numeric Claim Rules

- Do not convert relative improvements to absolute unless the paper does so.
- Do not claim SOTA unless the paper explicitly makes that claim.
- Preserve the paper's own error bars, confidence intervals, and significance tests.
- When the paper reports a range, cite both bounds; do not cherry-pick the best value.

## Quote Length Limits

- Evidence source text is capped at 2000 characters per entry.
- Longer blocks are split deterministically with `-a`, `-b` suffixes.
- Always prefer the most specific block for a given claim.

## Citing Figures, Tables, and Pages

- Use `ev-pNN-bMMM` for text block evidence.
- Reference figures via `selected_asset_ids` with IDs like `fig-p04-001`.
- Reference tables via `selected_asset_ids` with IDs like `tbl-p05-001`.
- Page-level references use `page-pNN` asset IDs.
