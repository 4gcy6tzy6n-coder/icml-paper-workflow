"""Semantic packet builder for Claude Code consumption."""

from pathlib import Path

from paperflow.models.document import ParsedDocument
from paperflow.models.paper_ir import EvidenceRef


def find_evidence_by_page(evidence: list[EvidenceRef], page: int) -> list[EvidenceRef]:
    """Return all evidence references for a given page number."""
    return [ref for ref in evidence if ref.page == page]


def find_evidence_by_id(
    evidence: list[EvidenceRef], ev_id: str
) -> EvidenceRef | None:
    """Find an evidence reference by its ID."""
    for ref in evidence:
        if ref.id == ev_id:
            return ref
    return None


def build_semantic_packet(
    document: ParsedDocument,
    evidence: list[EvidenceRef],
    paper_ir_path: Path,
) -> str:
    """Generate a compact semantic authoring packet for Claude Code."""
    lines: list[str] = []
    lines.append("# Semantic Authoring Packet\n")
    lines.append("## Paper Metadata Guess\n")
    if document.title_guess:
        lines.append(f"**Title:** {document.title_guess}\n")
    lines.append(f"**Pages:** {document.page_count}\n")
    lines.append(f"**Parser:** {document.parser_name}\n")

    lines.append("## Evidence Index (by page)\n")
    for page in range(1, document.page_count + 1):
        page_ev = find_evidence_by_page(evidence, page)
        lines.append(f"\n### Page {page}\n")
        for ref in page_ev:
            snippet = ref.source_text[:120].replace("\n", " ")
            lines.append(f"- `{ref.id}`: {snippet}...\n")

    lines.append("\n## Figure/Table Registry\n")
    for asset in document.assets:
        label = asset.label or asset.id
        lines.append(f"- `{asset.id}` ({asset.asset_type.value}): {label} — page {asset.page}\n")

    lines.append(f"\n## Paper IR Path\n\n`{paper_ir_path}`\n")
    lines.append("\n## Instructions\n")
    lines.append(
        "- Write `paper-ir.json` **only** from the source evidence above.\n"
        "- Do not invent unsupported facts, numbers, or claims.\n"
        "- Every claim must reference at least one valid `evidence_id`.\n"
        "- Distinguish author-stated claims from analyst-inferred claims.\n"
    )

    return "".join(lines)
