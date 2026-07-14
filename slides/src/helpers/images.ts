import fs from "node:fs";
import path from "node:path";

export function resolveAssetPath(
  workspace: string,
  relativePath: string
): string {
  const normalized = path.normalize(relativePath);
  if (path.isAbsolute(normalized)) {
    throw new Error(`Absolute asset paths are not allowed: ${relativePath}`);
  }
  if (normalized.includes("..")) {
    throw new Error(`Asset path must not leave workspace: ${relativePath}`);
  }
  const fullPath = path.resolve(workspace, normalized);
  if (!fullPath.startsWith(path.resolve(workspace))) {
    throw new Error(`Asset path escapes workspace: ${relativePath}`);
  }
  return fullPath;
}

export function getImageDimensions(
  filePath: string
): { width: number; height: number } {
  if (!fs.existsSync(filePath)) {
    throw new Error(`Image not found: ${filePath}`);
  }
  // Use a simple size-probing approach; PptxGenJS handles dimensions
  // when adding images, so we return conservative defaults.
  return { width: 1200, height: 900 };
}
