import type PptxGenJS from "pptxgenjs";
import type { SlideSpec } from "../models.js";
import type { SlideContext } from "./index.js";
import { SLIDE, FONTS, COLORS } from "../theme.js";

export function renderTakeawaySlide(
  pptx: PptxGenJS,
  slide: PptxGenJS.Slide,
  spec: SlideSpec,
  _context: SlideContext
): void {
  slide.background = { fill: COLORS.primary };

  slide.addText("Key Takeaways", {
    x: SLIDE.marginX,
    y: 1.2,
    w: SLIDE.width - 2 * SLIDE.marginX,
    h: 1.0,
    fontSize: FONTS.titleSizeMax,
    fontFace: FONTS.titleFace,
    color: "FFFFFF",
    bold: true,
    align: "center",
  });

  const points = spec.body_lines.slice(0, 3);
  const startY = 2.5;

  points.forEach((point, i) => {
    const y = startY + i * 1.2;

    slide.addText(`${i + 1}.`, {
      x: SLIDE.marginX + 1.0,
      y,
      w: 0.6,
      h: 0.7,
      fontSize: FONTS.bodySize + 4,
      fontFace: FONTS.bodyFace,
      color: "FFFFFF",
      bold: true,
    });

    slide.addText(point, {
      x: SLIDE.marginX + 1.8,
      y,
      w: SLIDE.width - 2 * SLIDE.marginX - 2.8,
      h: 0.7,
      fontSize: FONTS.bodySize,
      fontFace: FONTS.bodyFace,
      color: "E8ECF0",
      valign: "middle",
    });
  });

  slide.addText(spec.source_footer, {
    x: SLIDE.marginX,
    y: SLIDE.footerY,
    w: SLIDE.width - 2 * SLIDE.marginX,
    h: SLIDE.footerH,
    fontSize: FONTS.footerSize,
    color: "A0A8B4",
    align: "center",
  });
}
