import type { EvidenceRef } from "../models.js";

export function formatEvidenceFootnote(evRefs: EvidenceRef[]): string {
  if (evRefs.length === 0) return "";
  const ids = evRefs.map((r) => r.id).join(", ");
  return `Source: ${ids}`;
}

export function findEvidenceForSlide(
  evidenceIds: string[],
  allEvidence: EvidenceRef[]
): EvidenceRef[] {
  const evSet = new Set(evidenceIds);
  return allEvidence.filter((ev) => evSet.has(ev.id));
}
