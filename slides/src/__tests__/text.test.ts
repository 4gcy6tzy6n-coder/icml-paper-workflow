import { describe, it, expect } from "vitest";
import { truncateText, splitLines, makeTextRun } from "../helpers/text.js";

describe("truncateText", () => {
  it("should leave short text unchanged", () => {
    expect(truncateText("hello", 10)).toBe("hello");
  });

  it("should truncate long text with ellipsis", () => {
    expect(truncateText("hello world this is long", 10)).toBe("hello w...");
  });
});

describe("splitLines", () => {
  it("should split text at word boundaries", () => {
    const result = splitLines("hello world foo bar", 12);
    expect(result.length).toBeGreaterThanOrEqual(2);
    for (const line of result) {
      expect(line.length).toBeLessThanOrEqual(12);
    }
  });
});

describe("makeTextRun", () => {
  it("should create a text run with defaults", () => {
    const run = makeTextRun({ text: "Hello" });
    expect(run.text).toBe("Hello");
    expect(run.options.fontSize).toBe(18);
    expect(run.options.color).toBe("172033");
  });

  it("should respect custom options", () => {
    const run = makeTextRun({ text: "Bold", bold: true, fontSize: 24 });
    expect(run.options.bold).toBe(true);
    expect(run.options.fontSize).toBe(24);
  });
});
