# QA Rubrics

## Content QA Checklist

### Evidence Coverage
- [ ] Every Paper IR claim references at least one valid evidence ID.
- [ ] 100% of evidence IDs in claims exist in the evidence map.
- [ ] No placeholder text remains in any artifact.

### Cross-Artifact Consistency
- [ ] Report and slides list the same contributions.
- [ ] Report and slides reference the same datasets, baselines, and metrics.
- [ ] Headline numeric results match between report and slides.
- [ ] Limitations list matches between report and slides.
- [ ] All selected assets are used or explicitly marked unused.

### Placeholder Scan
Regex: `(?i)\b(TODO|TBD|XXXX|lorem ipsum|placeholder|insert (figure|text)|待补充|示例文本)\b`

## Visual QA Checklist

Inspect each slide image in `qa/slide-images/slide-NNN.png`:

- [ ] No overlapping elements (text on text, text on figure).
- [ ] No text overflow (text does not extend beyond its container).
- [ ] No edge clipping (content within slide margins).
- [ ] Adequate contrast (text readable on background).
- [ ] No tiny text (< 8 pt rendered).
- [ ] Even spacing between blocks.
- [ ] Proper alignment of multi-element layouts.
- [ ] Images not distorted (aspect ratio preserved).
- [ ] No low-resolution assets (< 150 DPI effective).
- [ ] Footer does not collide with body content.
- [ ] No excessive density (slides are scannable in 5 seconds).
- [ ] No large empty space imbalance.
- [ ] Correct assets used (verify figure/table matches storyboard).

## Visual Review Schema

```json
{
  "schema_version": "1.0",
  "inspection_pass": 1,
  "reviewed_slide_count": 15,
  "issues": [],
  "fixes_applied": [],
  "rerendered": false,
  "final_pass": false
}
```

### Issue Types
`overlap`, `text_overflow`, `edge_clipping`, `low_contrast`, `tiny_text`,
`uneven_spacing`, `poor_alignment`, `distorted_image`, `low_resolution_asset`,
`footer_collision`, `excessive_density`, `empty_space_imbalance`,
`incorrect_asset`, `other`

### Validation Rules
- All slides must be reviewed.
- `inspection_pass >= 1` required.
- Before final pass, at least one re-render must have occurred.
- `rerendered` must be `true` for final acceptance.
- `final_pass` must be `true`.
- No error-severity issue may remain.
- Any warning must have a corresponding fix or explicit accepted-risk rationale.
