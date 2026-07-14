export const SLIDE = {
  width: 13.333,
  height: 7.5,
  marginX: 0.6,
  marginY: 0.45,
  footerY: 7.08,
  footerH: 0.2,
} as const;

export const COLORS = {
  background: "F7F8FA",
  surface: "FFFFFF",
  text: "172033",
  muted: "5B6577",
  primary: "253B80",
  secondary: "2A7F9E",
  accent: "D97706",
  danger: "B42318",
} as const;

export const FONTS = {
  titleFace: "Aptos Display",
  bodyFace: "Aptos",
  monoFace: "Consolas",
  titleSize: 30,
  titleSizeMin: 28,
  titleSizeMax: 34,
  bodySize: 18,
  bodySizeMin: 16,
  bodySizeMax: 20,
  footerSize: 9,
  monoSize: 15,
} as const;

export const SPACING = {
  minBlockGap: 0.35,
  minOuterMargin: 0.5,
} as const;

export interface Box {
  x: number;
  y: number;
  w: number;
  h: number;
}
