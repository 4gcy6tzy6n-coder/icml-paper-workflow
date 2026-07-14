import type PptxGenJS from "pptxgenjs";
import type { SlideSpec } from "../models.js";
import type { SlideContext } from "./index.js";
import { SLIDE, FONTS, COLORS } from "../theme.js";

export function renderComparisonSlide(
  pptx: PptxGenJS,
  slide: PptxGenJS.Slide,
  spec: SlideSpec,
  _context: SlideContext
): void {
  slide.background = { fill: COLORS.background };

  slide.addText(spec.assertion_title, {
    x: SLIDE.marginX,
    y: SLIDE.marginY,
    w: SLIDE.width - 2 * SLIDE.marginX,
    h: 1.0,
    fontSize: FONTS.titleSize,
    fontFace: FONTS.titleFace,
    color: COLORS.text,
    bold: true,
  });

  const items = spec.body_lines.slice(0, 3);
  const tableY = SLIDE.marginY + 1.3;
  const rowH = 0.6;

  const rows: { text: string; options: object }[][] = [];
  rows.push([
    { text: "Method", options: { fontSize: FONTS.bodySize, fontFace: FONTS.bodyFace, color: COLORS.text, bold: true } },
    { text: "Result", options: { fontSize: FONTS.bodySize, fontFace: FONTS.bodyFace, color: COLORS.text, bold: true } },
  ]);

  items.forEach((line, i) => {
    const parts = line.split(/\s{2,}/);
    const method = parts[0] || `Method ${i + 1}`;
    const result = parts[1] || "";
    rows.push([
      { text: method, options: { fontSize: FONTS.bodySizeMin, fontFace: FONTS.bodyFace, color: COLORS.text } },
      { text: result, options: { fontSize: FONTS.bodySizeMin, fontFace: FONTS.bodyFace, color: COLORS.primary, bold: true } },
    ]);
  });

  slide.addTable(rows, {
    x: SLIDE.marginX,
    y: tableY,
    w: SLIDE.width - 2 * SLIDE.marginX,
    border: { type: "solid", color: COLORS.muted, pt: 0.5 },
    rowH: rowH,
    colW: [(SLIDE.width - 2 * SLIDE.marginX) / 2, (SLIDE.width - 2 * SLIDE.marginX) / 2],
  });

  slide.addText(spec.takeaway, {
    x: SLIDE.marginX,
    y: tableY + rows.length * rowH + 0.3,
    w: SLIDE.width - 2 * SLIDE.marginX,
    h: 0.5,
    fontSize: FONTS.bodySize,
    fontFace: FONTS.bodyFace,
    color: COLORS.muted,
    italic: true,
  });

  slide.addText(spec.source_footer, {
    x: SLIDE.marginX,
    y: SLIDE.footerY,
    w: SLIDE.width - 2 * SLIDE.marginX,
    h: SLIDE.footerH,
    fontSize: FONTS.footerSize,
    color: COLORS.muted,
  });
}
