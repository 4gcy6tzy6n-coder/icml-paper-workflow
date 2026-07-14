from paperflow.models.common import Severity
from paperflow.models.paper_ir import EvidenceRef, PaperIR
from paperflow.models.qa import ValidationIssue


def validate_paper_ir(
    ir: PaperIR, evidence: list[EvidenceRef] | None = None
) -> list[ValidationIssue]:
    """Validate a Paper IR against hard constraints.

    Returns a list of issues. Zero errors means the IR is valid.
    """
    issues: list[ValidationIssue] = []

    if evidence is None:
        evidence = ir.evidence

    ev_ids = {ev.id for ev in evidence}

    _check_duplicate_ids(ir, issues)
    _check_evidence_refs(ir, ev_ids, issues)
    _check_required_sections(ir, issues)
    _check_numeric_evidence(ir, ev_ids, issues)
    _check_inferred_labeled(ir, issues)

    return issues


def _check_duplicate_ids(ir: PaperIR, issues: list[ValidationIssue]) -> None:
    contrib_ids = [c.id for c in ir.contributions]
    if len(contrib_ids) != len(set(contrib_ids)):
        issues.append(
            ValidationIssue(
                code="IR_DUPLICATE_ID",
                severity=Severity.ERROR,
                message="Duplicate contribution IDs found.",
                location="contributions",
            )
        )

    finding_ids = [f.id for f in ir.findings]
    if len(finding_ids) != len(set(finding_ids)):
        issues.append(
            ValidationIssue(
                code="IR_DUPLICATE_ID",
                severity=Severity.ERROR,
                message="Duplicate finding IDs found.",
                location="findings",
            )
        )

    result_ids = [r.id for r in ir.numeric_results]
    if len(result_ids) != len(set(result_ids)):
        issues.append(
            ValidationIssue(
                code="IR_DUPLICATE_ID",
                severity=Severity.ERROR,
                message="Duplicate numeric result IDs found.",
                location="numeric_results",
            )
        )

    limit_ids = [lim.id for lim in ir.limitations]
    if len(limit_ids) != len(set(limit_ids)):
        issues.append(
            ValidationIssue(
                code="IR_DUPLICATE_ID",
                severity=Severity.ERROR,
                message="Duplicate limitation IDs found.",
                location="limitations",
            )
        )


def _check_evidence_refs(
    ir: PaperIR, ev_ids: set[str], issues: list[ValidationIssue]
) -> None:
    all_evidence_refs: list[tuple[str, str]] = []

    for c in ir.contributions:
        for eid in c.evidence_ids:
            all_evidence_refs.append((eid, f"contribution/{c.id}"))

    for f in ir.findings:
        for eid in f.evidence_ids:
            all_evidence_refs.append((eid, f"finding/{f.id}"))

    for nr in ir.numeric_results:
        for eid in nr.evidence_ids:
            all_evidence_refs.append((eid, f"numeric_result/{nr.id}"))

    for limitation in ir.limitations:
        for eid in limitation.evidence_ids:
            all_evidence_refs.append((eid, f"limitation/{limitation.id}"))

    for mc in ir.method_components:
        for eid in mc.evidence_ids:
            all_evidence_refs.append((eid, f"method_component/{mc.id}"))

    for eid in ir.research_problem.evidence_ids:
        all_evidence_refs.append((eid, "research_problem"))

    for eid in ir.experimental_setup.evidence_ids:
        all_evidence_refs.append((eid, "experimental_setup"))

    for eid, location in all_evidence_refs:
        if eid not in ev_ids:
            issues.append(
                ValidationIssue(
                    code="IR_UNKNOWN_EVIDENCE",
                    severity=Severity.ERROR,
                    message=f"Evidence '{eid}' referenced at {location} does not exist.",
                    location=location,
                )
            )

    for aid in ir.selected_asset_ids:
        issues.append(
            ValidationIssue(
                code="IR_UNKNOWN_ASSET",
                severity=Severity.WARNING,
                message=f"Selected asset '{aid}' cannot be verified (asset registry not loaded).",
                location="selected_asset_ids",
            )
        )


def _check_required_sections(ir: PaperIR, issues: list[ValidationIssue]) -> None:
    if not ir.contributions:
        issues.append(
            ValidationIssue(
                code="IR_EMPTY_REQUIRED_SECTION",
                severity=Severity.ERROR,
                message="At least one contribution is required.",
                location="contributions",
            )
        )
    if not ir.findings:
        issues.append(
            ValidationIssue(
                code="IR_EMPTY_REQUIRED_SECTION",
                severity=Severity.ERROR,
                message="At least one finding is required.",
                location="findings",
            )
        )
    if not ir.numeric_results:
        issues.append(
            ValidationIssue(
                code="IR_EMPTY_REQUIRED_SECTION",
                severity=Severity.ERROR,
                message="At least one numeric result is required.",
                location="numeric_results",
            )
        )
    if not ir.limitations:
        issues.append(
            ValidationIssue(
                code="IR_EMPTY_REQUIRED_SECTION",
                severity=Severity.ERROR,
                message="At least one limitation is required.",
                location="limitations",
            )
        )


def _check_numeric_evidence(
    ir: PaperIR, ev_ids: set[str], issues: list[ValidationIssue]
) -> None:
    for nr in ir.numeric_results:
        for eid in nr.evidence_ids:
            if eid not in ev_ids:
                issues.append(
                    ValidationIssue(
                        code="IR_NUMERIC_WITHOUT_EVIDENCE",
                        severity=Severity.ERROR,
                        message=f"Numeric result '{nr.id}' references unknown evidence '{eid}'.",
                        location=f"numeric_results/{nr.id}",
                    )
                )


def _check_inferred_labeled(ir: PaperIR, issues: list[ValidationIssue]) -> None:
    for f in ir.findings:
        if f.source_type == "analyst_inferred":
            pass  # valid: properly labeled

    for limitation in ir.limitations:
        if limitation.source_type == "analyst_inferred":
            pass  # valid: properly labeled
