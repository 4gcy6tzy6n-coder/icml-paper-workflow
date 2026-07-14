import type PptxGenJS from "pptxgenjs";
import type { SlideSpec } from "../models.js";
import type { SlideContext } from "./index.js";
import { SLIDE, FONTS, COLORS } from "../theme.js";

export function renderTwoColumnSlide(
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

  const colW = (SLIDE.width - 2 * SLIDE.marginX - 0.4) / 2;
  const bodyY = SLIDE.marginY + 1.2;

  const lines = spec.body_lines.slice(0, 4);
  slide.addText(
    lines.map((line) => ({
      text: line,
      options: {
        fontSize: FONTS.bodySize,
        fontFace: FONTS.bodyFace,
        color: COLORS.text,
        bullet: true,
        breakType: "after" as const,
      },
    })),
    {
      x: SLIDE.marginX,
      y: bodyY,
      w: colW,
      h: SLIDE.height - bodyY - 1.2,
      valign: "top",
    }
  );

  slide.addText(spec.takeaway, {
    x: SLIDE.marginX + colW + 0.4,
    y: bodyY,
    w: colW,
    h: 1.5,
    fontSize: FONTS.bodySize,
    fontFace: FONTS.bodyFace,
    color: COLORS.secondary,
    bold: true,
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
