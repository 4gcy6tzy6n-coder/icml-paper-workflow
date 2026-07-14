import type PptxGenJS from "pptxgenjs";
import type { SlideSpec } from "../models.js";
import type { SlideContext } from "./index.js";
import { SLIDE, FONTS, COLORS } from "../theme.js";

export function renderMethodFlowSlide(
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

  const boxCount = Math.min(spec.body_lines.length, 5);
  const boxW = (SLIDE.width - 2 * SLIDE.marginX - (boxCount - 1) * 0.3) / boxCount;
  const boxY = SLIDE.marginY + 1.5;
  const boxH = 3.5;

  spec.body_lines.slice(0, boxCount).forEach((line, i) => {
    const x = SLIDE.marginX + i * (boxW + 0.3);

    slide.addShape("rect" as any, {
      x,
      y: boxY,
      w: boxW,
      h: boxH,
      fill: { color: COLORS.surface },
      line: { color: COLORS.primary, width: 1.5 },
      rectRadius: 0.1,
    });

    slide.addText(line, {
      x: x + 0.15,
      y: boxY + 0.2,
      w: boxW - 0.3,
      h: boxH - 0.4,
      fontSize: FONTS.bodySize,
      fontFace: FONTS.bodyFace,
      color: COLORS.text,
      align: "center",
      valign: "middle",
    });

    if (i < boxCount - 1) {
      slide.addText("→", {
        x: x + boxW,
        y: boxY + boxH / 2 - 0.2,
        w: 0.3,
        h: 0.4,
        fontSize: FONTS.bodySize + 4,
        color: COLORS.primary,
        align: "center",
      });
    }
  });

  slide.addText(spec.takeaway, {
    x: SLIDE.marginX,
    y: boxY + boxH + 0.3,
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
