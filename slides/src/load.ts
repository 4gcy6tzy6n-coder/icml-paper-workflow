import fs from "node:fs";
import path from "node:path";
import { StoryboardSchema, PaperIRSchema } from "./models.js";
import type { Storyboard, PaperIR } from "./models.js";

export function loadStoryboard(workspace: string): Storyboard {
  const storyboardPath = path.join(workspace, "slides", "storyboard.json");
  if (!fs.existsSync(storyboardPath)) {
    throw new Error(`Storyboard not found: ${storyboardPath}`);
  }
  const raw = JSON.parse(fs.readFileSync(storyboardPath, "utf-8"));
  return StoryboardSchema.parse(raw);
}

export function loadPaperIR(workspace: string): PaperIR {
  const irPath = path.join(workspace, "source", "paper-ir.json");
  if (!fs.existsSync(irPath)) {
    throw new Error(`Paper IR not found: ${irPath}`);
  }
  const raw = JSON.parse(fs.readFileSync(irPath, "utf-8"));
  return PaperIRSchema.parse(raw);
}

export function validateAssetPath(
  workspace: string,
  assetRelativePath: string
): string {
  const normalized = path.normalize(assetRelativePath);
  if (path.isAbsolute(normalized)) {
    throw new Error(
      `Absolute asset paths are not allowed: ${assetRelativePath}`
    );
  }
  if (normalized.startsWith("..") || normalized.includes("/../")) {
    throw new Error(
      `Asset path must not escape workspace: ${assetRelativePath}`
    );
  }
  const fullPath = path.resolve(workspace, normalized);
  const wsRoot = path.resolve(workspace);
  if (!fullPath.startsWith(wsRoot)) {
    throw new Error(`Asset path escapes workspace: ${assetRelativePath}`);
  }
  if (!fs.existsSync(fullPath)) {
    throw new Error(`Asset not found: ${fullPath}`);
  }
  return fullPath;
}
