import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import type PptxGenJS from "pptxgenjs";
import { describe, it, expect } from "vitest";
import {
  StoryboardSchema,
  SlideSpecSchema,
  PaperIRSchema,
} from "../models.js";
import { renderDeck } from "../render.js";
import { renderTakeawaySlide } from "../layouts/takeaway.js";

const validSlideSpec = {
  slide_id: "slide-01",
  purpose: "Title",
  assertion_title: "Test Assertion Title",
  takeaway: "This is the takeaway message.",
  supporting_evidence_ids: ["ev-p01-b001"],
  layout: "title",
  body_lines: ["Line 1", "Line 2"],
  source_footer: "Test Paper, ICML 2024",
  speaker_notes: "These are speaker notes with enough characters to be valid.",
};

const validStoryboard = {
  schema_version: "1.0" as const,
  title: "Test Storyboard",
  language: "zh-CN",
  talk_minutes: 15,
  slides: Array(6)
    .fill(null)
    .map((_, i) => ({
      ...validSlideSpec,
      slide_id: `slide-${String(i + 1).padStart(2, "0")}`,
    })),
};

const validPaperIR = {
  schema_version: "1.0" as const,
  metadata: {
    title: "Test Paper",
    authors: ["Author One"],
    venue: "ICML",
    abstract: "An abstract.",
  },
  contributions: [
    {
      id: "c-1",
      statement: "A novel method.",
      evidence_ids: ["ev-p01-b001"],
    },
  ],
  numeric_results: [
    {
      id: "nr-1",
      metric: "Accuracy",
      value_text: "87.4%",
      direction: "higher_better" as const,
      evidence_ids: ["ev-p01-b002"],
    },
  ],
  limitations: [
    {
      id: "l-1",
      statement: "A limitation.",
      evidence_ids: ["ev-p01-b003"],
    },
  ],
  evidence: [
    {
      id: "ev-p01-b001",
      page: 1,
      block_id: "p01-b001",
      source_text: "Abstract text.",
    },
    {
      id: "ev-p01-b002",
      page: 1,
      block_id: "p01-b002",
      source_text: "Result text.",
    },
    {
      id: "ev-p01-b003",
      page: 1,
      block_id: "p01-b003",
      source_text: "Limitation text.",
    },
  ],
  selected_asset_ids: [],
};

describe("SlideSpecSchema", () => {
  it("should parse a valid slide spec", () => {
    const result = SlideSpecSchema.parse(validSlideSpec);
    expect(result.slide_id).toBe("slide-01");
  });

  it("should reject missing speaker notes", () => {
    const invalid = { ...validSlideSpec, speaker_notes: "" };
    expect(() => SlideSpecSchema.parse(invalid)).toThrow();
  });

  it("should reject too many body lines", () => {
    const invalid = {
      ...validSlideSpec,
      body_lines: ["1", "2", "3", "4", "5", "6", "7"],
    };
    expect(() => SlideSpecSchema.parse(invalid)).toThrow();
  });
});

describe("StoryboardSchema", () => {
  it("should parse a valid storyboard", () => {
    const result = StoryboardSchema.parse(validStoryboard);
    expect(result.slides).toHaveLength(6);
  });

  it("should reject too few slides", () => {
    const invalid = { ...validStoryboard, slides: validStoryboard.slides.slice(0, 2) };
    expect(() => StoryboardSchema.parse(invalid)).toThrow();
  });
});

describe("PaperIRSchema", () => {
  it("should parse a valid paper IR", () => {
    const result = PaperIRSchema.parse(validPaperIR);
    expect(result.metadata.title).toBe("Test Paper");
  });
});

describe("renderDeck", () => {
  it("atomically writes to a temporary pptx path before renaming", async () => {
    const directory = fs.mkdtempSync(path.join(os.tmpdir(), "paperflow-slides-"));
    const outputPath = path.join(directory, "presentation.pptx");
    const storyboard = StoryboardSchema.parse(validStoryboard);
    const paperIR = PaperIRSchema.parse(validPaperIR);

    await expect(
      renderDeck(storyboard, paperIR, { workspace: directory, outputPath })
    ).resolves.toBeUndefined();
    expect(fs.existsSync(outputPath)).toBe(true);

    fs.rmSync(directory, { recursive: true, force: true });
  });
});

describe("renderTakeawaySlide", () => {
  it("uses the storyboard assertion title instead of a hard-coded heading", () => {
    const texts: string[] = [];
    const slide = {
      background: {},
      addText(text: string) {
        texts.push(text);
      },
    } as unknown as PptxGenJS.Slide;
    const spec = SlideSpecSchema.parse({
      ...validSlideSpec,
      assertion_title: "三句话理解论文",
      layout: "takeaway",
    });

    renderTakeawaySlide({} as PptxGenJS, slide, spec, { workspace: "/tmp" });

    expect(texts[0]).toBe("三句话理解论文");
  });
});
