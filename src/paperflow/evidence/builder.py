from paperflow.models.document import ParsedDocument
from paperflow.models.paper_ir import EvidenceRef

_MAX_SOURCE_LEN = 2000


def build_evidence_map(document: ParsedDocument) -> list[EvidenceRef]:
    """Build a stable evidence map from a parsed document's text blocks."""
    evidence: list[EvidenceRef] = []

    for block in document.blocks:
        text = block.text
        idx = 0
        while text:
            chunk = text[:_MAX_SOURCE_LEN]
            text = text[_MAX_SOURCE_LEN:]
            suffix = ""
            if idx > 0:
                suffix = f"-{chr(ord('a') + idx - 1)}"
            ev_id = f"ev-{block.id}{suffix}"
            evidence.append(
                EvidenceRef(
                    id=ev_id,
                    page=block.page,
                    block_id=block.id,
                    source_text=chunk,
                )
            )
            idx += 1

    return evidence
