import { FONTS } from "../theme.js";

export function truncateText(text: string, maxChars: number): string {
  if (text.length <= maxChars) return text;
  return text.slice(0, maxChars - 3) + "...";
}

export function splitLines(text: string, maxCharsPerLine: number): string[] {
  const words = text.split(/\s+/);
  const lines: string[] = [];
  let current = "";

  for (const word of words) {
    if ((current + " " + word).trim().length > maxCharsPerLine && current) {
      lines.push(current.trim());
      current = word;
    } else {
      current = current ? current + " " + word : word;
    }
  }
  if (current) lines.push(current.trim());
  return lines;
}

export interface TextRunOptions {
  text: string;
  fontSize?: number;
  fontFace?: string;
  color?: string;
  bold?: boolean;
  italic?: boolean;
}

export function makeTextRun(opts: TextRunOptions) {
  return {
    text: opts.text,
    options: {
      fontSize: opts.fontSize ?? FONTS.bodySize,
      fontFace: opts.fontFace ?? FONTS.bodyFace,
      color: opts.color ?? "172033",
      bold: opts.bold ?? false,
      italic: opts.italic ?? false,
    },
  };
}
