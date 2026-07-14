import { z } from "zod";

export const SlideLayoutEnum = z.enum([
  "title",
  "assertion_figure",
  "two_column",
  "method_flow",
  "result_highlight",
  "comparison",
  "limitations",
  "takeaway",
]);
export type SlideLayout = z.infer<typeof SlideLayoutEnum>;

export const SlideSpecSchema = z.object({
  slide_id: z.string(),
  purpose: z.string(),
  assertion_title: z.string(),
  takeaway: z.string(),
  supporting_evidence_ids: z.array(z.string()).min(1),
  visual_asset_ids: z.array(z.string()).default([]),
  layout: SlideLayoutEnum,
  body_lines: z.array(z.string()).max(6).default([]),
  source_footer: z.string(),
  speaker_notes: z.string().min(20),
});
export type SlideSpec = z.infer<typeof SlideSpecSchema>;

export const StoryboardSchema = z.object({
  schema_version: z.literal("1.0"),
  title: z.string(),
  language: z.string().default("zh-CN"),
  talk_minutes: z.number().min(5).max(60).default(15),
  slides: z.array(SlideSpecSchema).min(6).max(40),
});
export type Storyboard = z.infer<typeof StoryboardSchema>;

export const EvidenceRefSchema = z.object({
  id: z.string(),
  page: z.number().min(1),
  block_id: z.string(),
  source_text: z.string(),
});
export type EvidenceRef = z.infer<typeof EvidenceRefSchema>;

export const NumericResultSchema = z.object({
  id: z.string(),
  metric: z.string(),
  value_text: z.string(),
  comparison_text: z.string().nullable().optional(),
  direction: z.enum(["higher_better", "lower_better", "neutral"]),
  evidence_ids: z.array(z.string()).min(1),
});

export const PaperIRSchema = z.object({
  schema_version: z.literal("1.0"),
  metadata: z.object({
    title: z.string(),
    authors: z.array(z.string()),
    venue: z.string().default("ICML"),
    abstract: z.string(),
  }),
  contributions: z.array(
    z.object({
      id: z.string(),
      statement: z.string(),
      evidence_ids: z.array(z.string()),
    })
  ),
  numeric_results: z.array(NumericResultSchema),
  limitations: z.array(
    z.object({
      id: z.string(),
      statement: z.string(),
      evidence_ids: z.array(z.string()),
    })
  ),
  evidence: z.array(EvidenceRefSchema),
  selected_asset_ids: z.array(z.string()).default([]),
});
export type PaperIR = z.infer<typeof PaperIRSchema>;
