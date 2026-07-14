# Slide Storytelling Guide

## Default Structure (15-Minute Talk, 13–15 Slides)

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

- Title, conclusion, and Q&A slides may use dark backgrounds.
- Content slides remain light (`F7F8FA` background).
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
