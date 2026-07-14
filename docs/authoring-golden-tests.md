# Authoring Golden Tests

This guide describes how to set up and validate golden papers for PaperFlow v1 quality scoring.

## Selecting Golden Papers

Choose three ICML-style papers from the following categories:

1. **Theoretical / Optimization-heavy** — A paper with mathematical proofs, convergence guarantees, or complexity bounds. Example: a paper on regret bounds for online learning.

2. **Empirical / Multimodal** — A paper with extensive experiments on image-text or multimodal benchmarks. Example: a new vision-language model with results on COCO, Flickr30K.

3. **Systems / LLM Infrastructure** — A paper on distributed training, inference optimization, or LLM serving. Example: a new attention kernel or KV-cache optimization.

Selection criteria:
- Official or author-hosted PDF available
- Contains figures and tables
- At least one ablation study
- Explicit limitations section (or enough scope for analyst inference)
- Manageable length (8–12 pages typical)

## Setup

1. Place the PDF in `tests/golden/<category>/paper.pdf`.
2. Ensure PDFs are gitignored if redistribution is restricted:
   ```
   # .gitignore
   tests/golden/*/paper.pdf
   ```
3. Run through the full pipeline:
   ```bash
   uv run paperflow init tests/golden/<category>/paper.pdf --output .work/golden-<category>
   uv run paperflow parse .work/golden-<category>
   # Claude Code authors paper-ir.json
   uv run paperflow validate-ir .work/golden-<category>
   # Continue through full pipeline...
   ```

## Authoring Expectations

For each golden paper, fill in `tests/golden/expectations/<category>.yaml`:

```yaml
source_pdf_sha256: "<actual sha256>"
paper_slug: "<paper slug>"

expected:
  contribution_count: 3
  contribution_keywords: ["keyword1", "keyword2"]
  datasets: ["Dataset1", "Dataset2"]
  baselines: ["Baseline1"]
  metrics: ["Accuracy", "F1"]
  headline_numeric_results:
    - metric: "Accuracy"
      value_text: "87.4%"
  required_figure_labels: ["Figure 1"]
  author_stated_limitations_min: 1

quality_targets:
  evidence_coverage: 1.0
  report_required_sections: 16
  slide_count_min: 13
  slide_count_max: 15
```

## Scoring

The weighted scoring rubric (max 100 points):

| Category | Max Points |
|----------|-----------|
| Paper IR factual coverage | 35 |
| Evidence traceability | 20 |
| Report completeness | 15 |
| Deck story structure | 10 |
| Cross-artifact consistency | 10 |
| Visual QA and editability | 10 |

**Release threshold:** Every paper must score ≥ 85 with no hard gate failures.

## Recording Sessions

For each Claude Code semantic session, record:
- Model name and date
- Skill version used
- Intervention notes
- Issues encountered
- Final scores
