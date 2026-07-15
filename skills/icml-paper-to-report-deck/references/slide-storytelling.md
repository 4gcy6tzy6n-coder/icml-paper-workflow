# Slide Storytelling Guide

## Example Structure (Recommendation Only)

Read the confirmed `presentation.target_slides` and
`presentation.duration_minutes` from `source/authoring-requirements.json`. Use this
15-slide outline only when it fits those confirmed values. Also apply the confirmed
purpose, focus topics, speaking context, audience, terminology, visual, citation,
constraint, and assumption fields.

Use the confirmed `use_case.audience` and do not assume a graduate-student audience. If
`language.preserve_english_terms` is false, follow `language.translation_preferences` in
titles, labels, and notes.

| # | Purpose | Layout |
|---|---------|--------|
| 1 | Title slide | title |
| 2 | One-sentence message | title |
| 3 | Why the problem matters | two_column |
| 4 | What prior approaches miss | two_column |
| 5 | Contributions | assertion_figure |
| 6 | Method overview | method_flow |
| 7 | Core component I | assertion_figure |
| 8 | Core component II | assertion_figure |
| 9 | Experimental setup | two_column |
| 10 | Headline result | result_highlight |
| 11 | Ablation / mechanism | result_highlight |
| 12 | Additional finding | comparison |
| 13 | Limitations | limitations |
| 14 | Three takeaways | takeaway |
| 15 | Q&A | title |

## Assertion Titles

- Every slide title must be a **conclusion or assertion**, not a section label.
- Bad: "Introduction", "Method", "Results", "Conclusion"
- Good: "Standard attention fails on long sequences", "Dynamic head selection reduces FLOPs by 29%"

## Body Text Rules

- **2–5 visible lines per slide** (recommended maximum 6).
- **Maximum 520 characters** of visible text (excluding notes and footer).
- Explanations and details move to speaker notes.
- One primary message per slide.

## Visual Assets

- Use original paper figures where available.
- Never regenerate experimental charts with an image model.
- Do not reuse the same layout more than three consecutive times.

## Color Scheme

- The dark-title/light-content palette is only a recommendation.
- Confirmed visual direction takes precedence: derive colors and emphasis from confirmed
  `visual.style`, `visual.brand_requirements`, and `visual.accessibility_requirements`.
- Do not use fake logos or decorative AI imagery.

## Evidence

- Every slide except title and Q&A must have at least one evidence reference.
- Title slide evidence may reference abstract evidence.
- Q&A slide may reuse headline finding evidence.
- Result slides require evidence tied to a `NumericResult`.

## Speaker Notes

- Minimum 20 characters per slide.
- Explain the slide's message and supporting evidence.
- Include the source footer text for provenance.
