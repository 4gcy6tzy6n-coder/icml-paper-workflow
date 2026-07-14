import fs from "node:fs";
import path from "node:path";
import type { Storyboard } from "./models.js";

export function exportSpeakerNotes(
  storyboard: Storyboard,
  workspace: string
): string {
  const lines: string[] = [];
  lines.push("# Speaker Notes\n");

  for (const slide of storyboard.slides) {
    lines.push(`## ${slide.slide_id} — ${slide.assertion_title}\n`);
    lines.push(slide.speaker_notes);
    lines.push("");
    lines.push(`Sources: ${slide.source_footer}`);
    lines.push("");
  }

  const content = lines.join("\n");
  const outPath = path.join(workspace, "slides", "speaker-notes.md");
  const outDir = path.dirname(outPath);
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }
  fs.writeFileSync(outPath, content, "utf-8");
  return outPath;
}
