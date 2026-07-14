import type PptxGenJS from "pptxgenjs";
import type { SlideSpec } from "../models.js";
import type { SlideContext } from "./index.js";
import { SLIDE, FONTS, COLORS } from "../theme.js";

export function renderLimitationsSlide(
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

  const items = spec.body_lines.slice(0, 5);
  const startY = SLIDE.marginY + 1.3;
  const itemH = 1.0;

  items.forEach((line, i) => {
    const y = startY + i * itemH;

    slide.addShape("rect" as any, {
      x: SLIDE.marginX,
      y,
      w: 0.08,
      h: 0.08,
      fill: { color: COLORS.danger },
    });

    slide.addText(line, {
      x: SLIDE.marginX + 0.25,
      y,
      w: SLIDE.width - 2 * SLIDE.marginX - 0.25,
      h: itemH - 0.1,
      fontSize: FONTS.bodySize,
      fontFace: FONTS.bodyFace,
      color: COLORS.text,
      valign: "top",
    });
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
