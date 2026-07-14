import type { SlideSpec } from "../models.js";
import type PptxGenJS from "pptxgenjs";
import { renderTitleSlide } from "./title.js";
import { renderAssertionFigureSlide } from "./assertionFigure.js";
import { renderTwoColumnSlide } from "./twoColumn.js";
import { renderMethodFlowSlide } from "./methodFlow.js";
import { renderResultHighlightSlide } from "./resultHighlight.js";
import { renderComparisonSlide } from "./comparison.js";
import { renderLimitationsSlide } from "./limitations.js";
import { renderTakeawaySlide } from "./takeaway.js";

export type SlideContext = {
  workspace: string;
  themeName?: string;
};

export type LayoutRenderer = (
  pptx: PptxGenJS,
  slide: PptxGenJS.Slide,
  spec: SlideSpec,
  context: SlideContext
) => void;

const layoutMap: Record<string, LayoutRenderer> = {
  title: renderTitleSlide,
  assertion_figure: renderAssertionFigureSlide,
  two_column: renderTwoColumnSlide,
  method_flow: renderMethodFlowSlide,
  result_highlight: renderResultHighlightSlide,
  comparison: renderComparisonSlide,
  limitations: renderLimitationsSlide,
  takeaway: renderTakeawaySlide,
};

export function getLayoutRenderer(layout: string): LayoutRenderer {
  const renderer = layoutMap[layout];
  if (!renderer) {
    throw new Error(`Unknown slide layout: ${layout}`);
  }
  return renderer;
}
