from __future__ import annotations

from decimal import Decimal
from typing import Any

from . import fx as fx_module
from . import fees as fees_module
from . import matcher as matcher_module
from .models import (
    AgentReconcileRequest,
    MatchCandidate,
    ToolResult,
)


def tool_validate_inputs(request: AgentReconcileRequest) -> ToolResult:
    missing = []
    if not request.payment_proofs:
        missing.append("payment_proofs")
    if not request.bank_rows:
        missing.append("bank_rows")

    if missing:
        return ToolResult(
            status="error",
            tool_name="validate_reconciliation_inputs",
            action="validate_inputs",
            observation=f"Missing required fields: {', '.join(missing)}",
            key_output_summary="Input validation failed",
            reason_codes=["validation_error"],
            output={"missing_fields": missing},
        )

    return ToolResult(
        status="success",
        tool_name="validate_reconciliation_inputs",
        action="validate_inputs",
        observation=f"Request validated: {len(request.payment_proofs)} proof(s), {len(request.bank_rows)} bank row(s)",
        key_output_summary="Input validation passed",
        output={
            "proof_count": len(request.payment_proofs),
            "bank_row_count": len(request.bank_rows),
            "fx_rate_count": len(request.fx_rates),
        },
    )


def tool_parse_payment_proofs(request: AgentReconcileRequest) -> ToolResult:
    return ToolResult(
        status="success",
        tool_name="parse_payment_proofs",
        action="parse_payment_proofs",
        observation=f"Parsed {len(request.payment_proofs)} payment proof(s)",
        key_output_summary=f"{len(request.payment_proofs)} proof(s) parsed",
        output={"proofs": [p.model_dump(mode="json") for p in request.payment_proofs]},
    )


def tool_parse_bank_rows(request: AgentReconcileRequest) -> ToolResult:
    return ToolResult(
        status="success",
        tool_name="parse_bank_rows",
        action="parse_bank_rows",
        observation=f"Parsed {len(request.bank_rows)} bank row(s)",
        key_output_summary=f"{len(request.bank_rows)} bank row(s) parsed",
        output={"bank_rows": [b.model_dump(mode="json") for b in request.bank_rows]},
    )


def tool_apply_fx_rates(request: AgentReconcileRequest) -> ToolResult:
    fx_lookup = fx_module.build_fx_lookup(request.fx_rates, request.base_currency)
    conversion_results: list[dict[str, Any]] = []
    warnings: list[str] = []

    for proof in request.payment_proofs:
        (
            expected_amount_local,
            fx_rate_used,
            fx_rate_source,
            reason_codes,
            reasoning_facts,
        ) = fx_module.apply_fx_rate(proof, fx_lookup, request.base_currency)

        entry = {
            "proof_id": proof.proof_id,
            "currency": proof.currency,
            "original_amount": str(proof.amount),
            "expected_amount_local": str(expected_amount_local) if expected_amount_local is not None else None,
            "fx_rate_used": str(fx_rate_used) if fx_rate_used is not None else None,
            "fx_rate_source": fx_rate_source,
            "reason_codes": reason_codes,
            "reasoning_facts": reasoning_facts,
        }
        conversion_results.append(entry)

        if expected_amount_local is None and "missing_fx_rate" in reason_codes:
            warnings.append(
                f"Proof '{proof.proof_id}': missing FX rate for {proof.currency}_{request.base_currency}"
            )

    all_failed = all(r["expected_amount_local"] is None for r in conversion_results)
    status = "warning" if warnings and not all_failed else ("error" if all_failed else "success")

    return ToolResult(
        status=status,
        tool_name="apply_fx_rates",
        action="apply_fx_rates",
        observation=f"Applied FX rates to {len(conversion_results)} proof(s)",
        key_output_summary=f"{sum(1 for r in conversion_results if r['fx_rate_source'] != 'missing')} converted, {sum(1 for r in conversion_results if r['fx_rate_source'] == 'missing')} missing",
        output={"conversion_results": conversion_results},
        reason_codes=[],
        warnings=warnings,
    )


def tool_evaluate_fee_tolerance(
    expected_amount_local: Decimal | None,
    actual_amount_local: Decimal | None,
    request: AgentReconcileRequest,
    proof_id: str,
    bank_row_id: str,
) -> ToolResult:
    fee_difference, tolerance_allowed, within_tolerance, reason_codes, reasoning_facts = (
        fees_module.evaluate_fee_tolerance(
            expected_amount_local,
            actual_amount_local,
            request.fee_tolerance,
            request.base_currency,
            proof_id,
            bank_row_id,
        )
    )

    return ToolResult(
        status="success",
        tool_name="evaluate_fee_tolerance",
        action="evaluate_fee_tolerance",
        observation=(
            f"Fee diff={fee_difference}, tolerance={tolerance_allowed}, within={within_tolerance}"
            if fee_difference is not None
            else "Cannot evaluate (missing amounts)"
        ),
        key_output_summary=(
            "Within tolerance" if within_tolerance
            else "Outside tolerance" if fee_difference is not None
            else "Cannot evaluate"
        ),
        output={
            "fee_difference": str(fee_difference) if fee_difference is not None else None,
            "tolerance_allowed": str(tolerance_allowed) if tolerance_allowed is not None else None,
            "amount_within_tolerance": within_tolerance,
            "proof_id": proof_id,
            "bank_row_id": bank_row_id,
        },
        reason_codes=reason_codes,
    )


def tool_match_transactions(request: AgentReconcileRequest) -> ToolResult:
    fx_lookup = fx_module.build_fx_lookup(request.fx_rates, request.base_currency)
    all_candidates: list[MatchCandidate] = []
    warnings: list[str] = []

    for proof in request.payment_proofs:
        for bank_row in request.bank_rows:
            expected_amount_local: Decimal | None = None
            actual_amount_local = bank_row.amount_local

            ref_exact, ref_norm, ref_fuzzy, ref_in_desc, ref_codes, ref_facts = (
                matcher_module.check_reference_match(
                    proof.reference,
                    bank_row.description,
                    proof.sender_name,
                )
            )

            sender_match, sender_codes, sender_facts = (
                matcher_module.check_sender_name_match(
                    proof.sender_name,
                    bank_row.description,
                )
            )

            settlement = bank_row.resolved_settlement_date()
            date_diff, date_ok, date_codes, date_facts = (
                matcher_module.check_date_window(
                    proof.payment_date,
                    settlement,
                    request.date_tolerance_days,
                )
            )

            currency = proof.currency.upper()
            base = request.base_currency.upper()

            if currency == base:
                expected_amount_local = proof.amount
            elif currency in fx_lookup:
                expected_amount_local = proof.amount * fx_lookup[currency]
            else:
                pass

            fee_diff, tol_allowed, amt_ok, fee_codes, fee_facts = (
                fees_module.evaluate_fee_tolerance(
                    expected_amount_local,
                    actual_amount_local,
                    request.fee_tolerance,
                    request.base_currency,
                    proof.proof_id,
                    bank_row.bank_row_id,
                )
            )

            reference_match_any = ref_exact or ref_norm or ref_fuzzy or ref_in_desc
            confidence = matcher_module.calculate_confidence(
                reference_match=reference_match_any,
                amount_within_tolerance=amt_ok,
                date_within_tolerance=date_ok,
                sender_name_match=sender_match,
            )

            all_reason_codes = list(
                set(ref_codes + sender_codes + date_codes + fee_codes)
            )
            all_reasoning_facts = ref_facts + sender_facts + date_facts + fee_facts

            candidate = MatchCandidate(
                proof_id=proof.proof_id,
                bank_row_id=bank_row.bank_row_id,
                reference_exact_match=ref_exact,
                reference_normalized_match=ref_norm or ref_in_desc,
                reference_fuzzy_match=ref_fuzzy,
                reference_found_in_description=ref_in_desc,
                sender_name_in_description=sender_match,
                date_days_diff=date_diff,
                date_within_tolerance=date_ok,
                expected_amount_local=expected_amount_local,
                actual_amount_local=actual_amount_local,
                fee_difference=fee_diff,
                tolerance_allowed=tol_allowed,
                amount_within_tolerance=amt_ok,
                confidence=confidence,
                reason_codes=all_reason_codes,
                reasoning_facts=all_reasoning_facts,
            )

            all_candidates.append(candidate)

    if not all_candidates:
        return ToolResult(
            status="warning",
            tool_name="match_transactions",
            action="match_transactions",
            observation="No match candidates generated",
            key_output_summary="No candidates",
            output={"candidates": []},
            warnings=["No match candidates found - check input data"],
        )

    return ToolResult(
        status="success",
        tool_name="match_transactions",
        action="match_transactions",
        observation=f"Generated {len(all_candidates)} candidate pair(s) "
        f"({len(request.payment_proofs)} proofs x {len(request.bank_rows)} bank rows)",
        key_output_summary=f"{len(all_candidates)} candidate(s) generated",
        output={"candidates": [c.model_dump(mode="json") for c in all_candidates]},
    )


def tool_classify_results(
    candidates_result: ToolResult,
    request: AgentReconcileRequest,
) -> ToolResult:
    candidates_raw = (candidates_result.output or {}).get("candidates", [])
    if not candidates_raw:
        return ToolResult(
            status="error",
            tool_name="classify_reconciliation_results",
            action="classify_results",
            observation="No candidates to classify",
            key_output_summary="No results",
            output={"classifications": [], "unassigned_proofs": []},
            reason_codes=["no_candidates"],
        )

    candidates = [MatchCandidate(**c) for c in candidates_raw]

    best_per_proof: dict[str, MatchCandidate] = {}
    warnings: list[str] = []
    unassigned_proofs: list[str] = []

    for proof in request.payment_proofs:
        proof_candidates = [c for c in candidates if c.proof_id == proof.proof_id]
        if not proof_candidates:
            unassigned_proofs.append(proof.proof_id)
            continue

        best = matcher_module.pick_best_candidate(proof_candidates)
        if best is None:
            unassigned_proofs.append(proof.proof_id)
            continue

        needs_review, review_codes, review_facts = (
            matcher_module.needs_possible_review(proof_candidates, best)
        )
        if needs_review:
            best.reason_codes = list(set(best.reason_codes + review_codes))
            best.reasoning_facts.extend(review_facts)
            if best.confidence >= Decimal("0.75"):
                best.confidence = Decimal("0.74")
            best.confidence = min(best.confidence, Decimal("0.74"))
            best.reason_codes.append("downgraded_to_possible")

        best_per_proof[proof.proof_id] = best

    classifications = []
    for proof_id, best in best_per_proof.items():
        label = matcher_module.classify_score(best.confidence)
        classifications.append({
            "proof_id": proof_id,
            "bank_row_id": best.bank_row_id,
            "confidence": str(best.confidence),
            "classification": label,
            "expected_amount_local": str(best.expected_amount_local) if best.expected_amount_local is not None else None,
            "actual_amount_local": str(best.actual_amount_local) if best.actual_amount_local is not None else None,
            "fee_difference": str(best.fee_difference) if best.fee_difference is not None else None,
            "amount_within_tolerance": best.amount_within_tolerance,
            "reference_found": best.reference_exact_match or best.reference_normalized_match or best.reference_fuzzy_match,
            "date_within_tolerance": best.date_within_tolerance,
            "sender_match": best.sender_name_in_description,
            "reason_codes": best.reason_codes,
            "reasoning_facts": best.reasoning_facts,
        })

    counts = {"matched": 0, "possible": 0, "unmatched": 0}
    for c in classifications:
        counts[c["classification"]] = counts.get(c["classification"], 0) + 1
    for pid in unassigned_proofs:
        counts["unmatched"] = counts.get("unmatched", 0) + 1

    if unassigned_proofs:
        warnings.append(f"{len(unassigned_proofs)} proof(s) have no match candidates")

    return ToolResult(
        status="success",
        tool_name="classify_reconciliation_results",
        action="classify_results",
        observation=f"Classified: {counts['matched']} matched, {counts['possible']} possible, {counts['unmatched']} unmatched",
        key_output_summary=f"{counts['matched']} matched, {counts['possible']} possible, {counts['unmatched']} unmatched",
        output={
            "classifications": classifications,
            "unassigned_proofs": unassigned_proofs,
            "counts": counts,
        },
        warnings=warnings,
    )
