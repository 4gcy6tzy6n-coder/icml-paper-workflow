import type { Box } from "../theme.js";
import { SLIDE, SPACING, COLORS } from "../theme.js";

export function containImage(
  imageWidthPx: number,
  imageHeightPx: number,
  box: Box
): Box {
  const aspect = imageWidthPx / imageHeightPx;
  const boxAspect = box.w / box.h;

  if (aspect > boxAspect) {
    const h = box.w / aspect;
    return { x: box.x, y: box.y + (box.h - h) / 2, w: box.w, h };
  } else {
    const w = box.h * aspect;
    return { x: box.x + (box.w - w) / 2, y: box.y, w, h: box.h };
  }
}

export function estimateFontSize(
  text: string,
  box: { w: number; h: number },
  preferred: number,
  minimum: number
): number {
  // Box dimensions are in inches. Convert pt to inches for comparison.
  const charWidthIn = (preferred / 72) * 0.55;
  const charsPerLine = box.w / Math.max(0.01, charWidthIn);
  const linesNeeded = Math.ceil(text.length / charsPerLine);
  const lineHeightIn = (preferred * 1.3) / 72;
  const totalHeightIn = linesNeeded * lineHeightIn;

  if (totalHeightIn <= box.h) return preferred;

  const ratio = box.h / totalHeightIn;
  return Math.max(minimum, Math.floor(preferred * ratio));
}

export function assertInsideSlide(box: Box): void {
  if (box.x < 0) {
    throw new Error(`Box x=${box.x} is negative`);
  }
  if (box.y < 0) {
    throw new Error(`Box y=${box.y} is negative`);
  }
  if (box.x + box.w > SLIDE.width) {
    throw new Error(
      `Box right edge ${box.x + box.w} exceeds slide width ${SLIDE.width}`
    );
  }
  if (box.y + box.h > SLIDE.height) {
    throw new Error(
      `Box bottom edge ${box.y + box.h} exceeds slide height ${SLIDE.height}`
    );
  }
}

export function assertNoBoxOverlap(
  a: Box,
  b: Box,
  tolerance: number = 0
): void {
  const ax2 = a.x + a.w + tolerance;
  const ay2 = a.y + a.h + tolerance;
  const bx2 = b.x + b.w + tolerance;
  const by2 = b.y + b.h + tolerance;

  const overlaps =
    a.x < bx2 && ax2 > b.x && a.y < by2 && ay2 > b.y;

  if (overlaps) {
    throw new Error(
      `Boxes overlap: (${a.x},${a.y})-(${ax2},${ay2}) ` +
        `and (${b.x},${b.y})-(${bx2},${by2})`
    );
  }
}

export function titleBox(): Box {
  return {
    x: SLIDE.marginX,
    y: SLIDE.marginY,
    w: SLIDE.width - 2 * SLIDE.marginX,
    h: 1.2,
  };
}

export function bodyBox(): Box {
  return {
    x: SLIDE.marginX,
    y: SLIDE.marginY + 1.4,
    w: SLIDE.width - 2 * SLIDE.marginX,
    h: SLIDE.height - SLIDE.marginY - 1.4 - 1.2,
  };
}

export function footerBox(): Box {
  return {
    x: SLIDE.marginX,
    y: SLIDE.footerY,
    w: SLIDE.width - 2 * SLIDE.marginX,
    h: SLIDE.footerH,
  };
}
