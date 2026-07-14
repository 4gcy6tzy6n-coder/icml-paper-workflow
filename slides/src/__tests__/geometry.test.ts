import { describe, it, expect } from "vitest";
import {
  containImage,
  estimateFontSize,
  assertInsideSlide,
  assertNoBoxOverlap,
  titleBox,
  bodyBox,
} from "../helpers/geometry.js";

describe("containImage", () => {
  it("should fit a wide image into a taller box", () => {
    const box = { x: 0, y: 0, w: 10, h: 10 };
    const result = containImage(2000, 1000, box);
    expect(result.w).toBe(10);
    expect(result.h).toBe(5);
    expect(result.y).toBe(2.5);
  });

  it("should fit a tall image into a wider box", () => {
    const box = { x: 0, y: 0, w: 10, h: 10 };
    const result = containImage(1000, 2000, box);
    expect(result.w).toBe(5);
    expect(result.h).toBe(10);
    expect(result.x).toBe(2.5);
  });
});

describe("estimateFontSize", () => {
  it("should return preferred size if text fits", () => {
    const box = { w: 10, h: 10 };
    const result = estimateFontSize("Short", box, 30, 16);
    expect(result).toBe(30);
  });

  it("should not go below minimum", () => {
    const box = { w: 1, h: 0.5 };
    const result = estimateFontSize(
      "A very long text that cannot possibly fit",
      box,
      30,
      16
    );
    expect(result).toBeGreaterThanOrEqual(16);
  });
});

describe("assertInsideSlide", () => {
  it("should pass for valid box", () => {
    expect(() =>
      assertInsideSlide({ x: 0.6, y: 0.45, w: 10, h: 5 })
    ).not.toThrow();
  });

  it("should throw for box with negative x", () => {
    expect(() =>
      assertInsideSlide({ x: -0.1, y: 0.45, w: 10, h: 5 })
    ).toThrow();
  });
});

describe("assertNoBoxOverlap", () => {
  it("should pass for non-overlapping boxes", () => {
    expect(() =>
      assertNoBoxOverlap(
        { x: 0, y: 0, w: 5, h: 5 },
        { x: 6, y: 6, w: 5, h: 5 }
      )
    ).not.toThrow();
  });

  it("should throw for overlapping boxes", () => {
    expect(() =>
      assertNoBoxOverlap(
        { x: 0, y: 0, w: 5, h: 5 },
        { x: 3, y: 3, w: 5, h: 5 }
      )
    ).toThrow();
  });
});

describe("titleBox", () => {
  it("should return expected dimensions", () => {
    const box = titleBox();
    expect(box.w).toBeGreaterThan(10);
    expect(box.h).toBe(1.2);
  });
});
