import path from "node:path";
import type PptxGenJS from "pptxgenjs";
import type { SlideSpec } from "../models.js";
import type { SlideContext } from "./index.js";
import { SLIDE, FONTS, COLORS } from "../theme.js";
import { resolveAssetPath } from "../helpers/images.js";

export function renderAssertionFigureSlide(
  pptx: PptxGenJS,
  slide: PptxGenJS.Slide,
  spec: SlideSpec,
  context: SlideContext
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

  const figY = SLIDE.marginY + 1.1;
  const figH = SLIDE.height - figY - 1.6;

  if (spec.visual_asset_ids.length > 0) {
    const assetPath = resolveAssetPath(
      context.workspace,
      `assets/figures/${spec.visual_asset_ids[0]}.png`
    );
    slide.addImage({
      path: assetPath,
      x: SLIDE.marginX,
      y: figY,
      w: SLIDE.width - 2 * SLIDE.marginX,
      h: figH,
      sizing: { type: "contain", w: SLIDE.width - 2 * SLIDE.marginX, h: figH },
    });
  }

  slide.addText(spec.takeaway, {
    x: SLIDE.marginX,
    y: SLIDE.height - 1.5,
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
