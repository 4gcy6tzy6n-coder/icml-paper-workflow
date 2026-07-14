import fs from "node:fs";
import path from "node:path";
import PptxGenJS from "pptxgenjs";
import type { Storyboard, PaperIR } from "./models.js";
import { loadStoryboard, loadPaperIR } from "./load.js";
import { getLayoutRenderer } from "./layouts/index.js";

export type RenderDeckOptions = {
  workspace: string;
  outputPath: string;
  themeName?: string;
};

export async function renderDeck(
  storyboard: Storyboard,
  paperIR: PaperIR,
  options: RenderDeckOptions
): Promise<void> {
  const pptx = new PptxGenJS();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "PaperFlow";
  pptx.subject = storyboard.title;
  pptx.title = storyboard.title;

  for (const slideSpec of storyboard.slides) {
    const slide = pptx.addSlide();
    const renderer = getLayoutRenderer(slideSpec.layout);
    renderer(pptx, slide, slideSpec, {
      workspace: options.workspace,
      themeName: options.themeName,
    });
  }

  const outDir = path.dirname(options.outputPath);
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }

  const tmpPath = options.outputPath + ".tmp";
  await pptx.writeFile({ fileName: tmpPath });
  fs.renameSync(tmpPath, options.outputPath);
}

export async function renderDeckFromWorkspace(
  workspace: string
): Promise<void> {
  const storyboard = loadStoryboard(workspace);
  const paperIR = loadPaperIR(workspace);

  const outputPath = path.join(workspace, "slides", "presentation.pptx");
  await renderDeck(storyboard, paperIR, { workspace, outputPath });
}
