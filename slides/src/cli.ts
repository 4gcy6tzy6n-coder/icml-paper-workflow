import path from "node:path";
import { loadStoryboard } from "./load.js";
import { renderDeckFromWorkspace } from "./render.js";
import { exportSpeakerNotes } from "./notes.js";

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error("Usage: pnpm paperflow:render-slides -- WORKSPACE");
    process.exit(1);
  }
  const workspace = path.resolve(args[0]);

  console.error(`Rendering slides for: ${workspace}`);
  await renderDeckFromWorkspace(workspace);

  const storyboard = loadStoryboard(workspace);
  const notesPath = exportSpeakerNotes(storyboard, workspace);

  console.error(`PPTX: ${path.join(workspace, "slides", "presentation.pptx")}`);
  console.error(`Notes: ${notesPath}`);
}

main().catch((err) => {
  console.error("Render failed:", err.message);
  process.exit(1);
});
