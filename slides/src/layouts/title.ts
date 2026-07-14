import type PptxGenJS from "pptxgenjs";
import type { SlideSpec } from "../models.js";
import type { SlideContext } from "./index.js";
import { SLIDE, FONTS, COLORS } from "../theme.js";
import { makeTextRun } from "../helpers/text.js";

export function renderTitleSlide(
  pptx: PptxGenJS,
  slide: PptxGenJS.Slide,
  spec: SlideSpec,
  _context: SlideContext
): void {
  slide.background = { fill: COLORS.primary };

  slide.addText(spec.assertion_title, {
    x: SLIDE.marginX,
    y: 2.0,
    w: SLIDE.width - 2 * SLIDE.marginX,
    h: 1.5,
    fontSize: FONTS.titleSizeMax,
    fontFace: FONTS.titleFace,
    color: "FFFFFF",
    bold: true,
    align: "center",
    valign: "middle",
  });

  slide.addText(spec.takeaway, {
    x: SLIDE.marginX,
    y: 3.8,
    w: SLIDE.width - 2 * SLIDE.marginX,
    h: 0.8,
    fontSize: FONTS.bodySize,
    fontFace: FONTS.bodyFace,
    color: "E8ECF0",
    align: "center",
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
