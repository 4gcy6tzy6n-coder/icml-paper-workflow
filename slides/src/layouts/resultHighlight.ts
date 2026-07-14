import type PptxGenJS from "pptxgenjs";
import type { SlideSpec } from "../models.js";
import type { SlideContext } from "./index.js";
import { SLIDE, FONTS, COLORS } from "../theme.js";

export function renderResultHighlightSlide(
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

  const body = spec.body_lines.join("\n") || spec.takeaway;
  slide.addText(body, {
    x: SLIDE.marginX + 0.5,
    y: SLIDE.marginY + 1.3,
    w: SLIDE.width - 2 * SLIDE.marginX - 1.0,
    h: 1.5,
    fontSize: FONTS.bodySize + 2,
    fontFace: FONTS.bodyFace,
    color: COLORS.text,
    align: "center",
    valign: "middle",
  });

  slide.addShape("rect" as any, {
    x: SLIDE.width / 2 - 2.5,
    y: SLIDE.marginY + 3.2,
    w: 5.0,
    h: 0.06,
    fill: { color: COLORS.primary },
  });

  slide.addText(spec.takeaway, {
    x: SLIDE.marginX,
    y: SLIDE.marginY + 3.5,
    w: SLIDE.width - 2 * SLIDE.marginX,
    h: 1.0,
    fontSize: FONTS.bodySize,
    fontFace: FONTS.bodyFace,
    color: COLORS.muted,
    italic: true,
    align: "center",
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
