from __future__ import annotations

from typing import Any, Optional

from reconmate.agent.documents import generate_agent_documents_with_chain
from reconmate.reconciliation.models import (
    AgentReconcileRequest,
    AgentTraceItem,
    ToolResult,
)
from reconmate.reconciliation.service import (
    tool_apply_fx_rates,
    tool_classify_results,
    tool_match_transactions,
    tool_parse_bank_rows,
    tool_parse_payment_proofs,
    tool_validate_inputs,
)


def _execute_tool(
    step: int,
    tool_name: str,
    action: str,
    result: ToolResult,
) -> AgentTraceItem:
    return AgentTraceItem(
        step=step,
        tool=tool_name,
        action=action,
        observation=result.observation,
        status=result.status,
        key_output_summary=result.key_output_summary,
    )


def _build_legacy_payload(
    request: AgentReconcileRequest,
    classify_result: ToolResult,
    fx_result: ToolResult,
    agent_trace: list[dict[str, Any]],
) -> dict[str, Any]:
    classifications = (classify_result.output or {}).get("classifications", [])
    counts = (classify_result.output or {}).get("counts", {})
    unassigned_proofs = (classify_result.output or {}).get("unassigned_proofs", [])
    fx_conversions = (fx_result.output or {}).get("conversion_results", [])

    matched_transactions: list[dict[str, Any]] = []
    possible_matches: list[dict[str, Any]] = []

    for cls in classifications:
        entry = {
            "proof_id": cls["proof_id"],
            "bank_row_id": cls["bank_row_id"],
            "confidence": cls["confidence"],
            "classification": cls["classification"],
            "expected_amount_local": cls["expected_amount_local"],
            "actual_amount_local": cls["actual_amount_local"],
            "fee_difference": cls["fee_difference"],
            "amount_within_tolerance": cls["amount_within_tolerance"],
            "reference_found": cls["reference_found"],
            "date_within_tolerance": cls["date_within_tolerance"],
            "sender_match": cls["sender_match"],
            "reason_codes": cls["reason_codes"],
            "reasoning_facts": cls["reasoning_facts"],
        }
        if cls["classification"] == "matched":
            matched_transactions.append(entry)
        elif cls["classification"] == "possible":
            possible_matches.append(entry)

    unmatched_proofs: list[dict[str, Any]] = []
    for proof in request.payment_proofs:
        if proof.proof_id in unassigned_proofs:
            unmatched_proofs.append({
                "proof_id": proof.proof_id,
                "reference": proof.reference,
                "amount": str(proof.amount),
                "currency": proof.currency,
                "reason_codes": ["no_match_candidate"],
            })

    matched_bank_row_ids = {c["bank_row_id"] for c in classifications}
    unmatched_bank_rows: list[dict[str, Any]] = []
    for bank_row in request.bank_rows:
        if bank_row.bank_row_id not in matched_bank_row_ids:
            unmatched_bank_rows.append({
                "bank_row_id": bank_row.bank_row_id,
                "amount_local": str(bank_row.amount_local),
                "currency": bank_row.currency,
                "reason_codes": ["unmatched_bank_row"],
            })

    for cls in classifications:
        if cls["classification"] == "unmatched":
            unmatched_proofs.append({
                "proof_id": cls["proof_id"],
                "reason_codes": cls["reason_codes"],
            })
            unmatched_bank_rows = [
                r for r in unmatched_bank_rows
                if r["bank_row_id"] != cls["bank_row_id"]
            ]

    return {
        "run_id": request.run_id or "agent-orchestrated",
        "company_name": request.company_name,
        "base_currency": request.base_currency,
        "matched_transactions": matched_transactions,
        "possible_matches": possible_matches,
        "unmatched_payment_proofs": unmatched_proofs,
        "unmatched_bank_rows": unmatched_bank_rows,
        "fx_rates_used": fx_conversions,
        "agent_trace": agent_trace,
    }


def run_agent_orchestrator(
    request: AgentReconcileRequest,
    *,
    chutes_client: Any = None,
    gemini_client: Any = None,
    provider_mode: Any = None,
) -> dict[str, Any]:
    agent_trace: list[dict[str, Any]] = []
    step = 0

    step += 1
    result = tool_validate_inputs(request)
    agent_trace.append(
        _execute_tool(step, "validate_reconciliation_inputs", "validate_inputs", result).model_dump()
    )

    if result.status == "error":
        return _build_error_response("Input validation failed", agent_trace, result)

    step += 1
    result = tool_parse_payment_proofs(request)
    agent_trace.append(
        _execute_tool(step, "parse_payment_proofs", "parse_payment_proofs", result).model_dump()
    )

    step += 1
    result = tool_parse_bank_rows(request)
    agent_trace.append(
        _execute_tool(step, "parse_bank_rows", "parse_bank_rows", result).model_dump()
    )

    step += 1
    result = tool_apply_fx_rates(request)
    fx_result = result
    agent_trace.append(
        _execute_tool(step, "apply_fx_rates", "apply_fx_rates", result).model_dump()
    )

    step += 1
    result = tool_match_transactions(request)
    match_result = result
    agent_trace.append(
        _execute_tool(step, "match_transactions", "match_transactions", result).model_dump()
    )

    if result.status == "error":
        return _build_error_response("Transaction matching failed", agent_trace, result)

    step += 1
    result = tool_classify_results(match_result, request)
    classify_result = result
    agent_trace.append(
        _execute_tool(
            step, "classify_reconciliation_results", "classify_results", result
        ).model_dump()
    )

    legacy_payload = _build_legacy_payload(
        request, classify_result, fx_result, agent_trace
    )

    llm_result = generate_agent_documents_with_chain(
        legacy_payload,
        chutes_client=chutes_client,
        gemini_client=gemini_client,
        provider_mode=provider_mode,
    )

    classifications = (classify_result.output or {}).get("classifications", [])
    counts = (classify_result.output or {}).get("counts", {"matched": 0, "possible": 0, "unmatched": 0})

    return {
        "computed_by_backend": True,
        "run_id": request.run_id or "agent-orchestrated",
        "company_name": request.company_name,
        "base_currency": request.base_currency,
        "summary": {
            "matched_count": counts.get("matched", 0),
            "possible_match_count": counts.get("possible", 0),
            "unmatched_payment_proof_count": counts.get("unmatched", 0),
            "unmatched_bank_row_count": len(
                [r for r in legacy_payload["unmatched_bank_rows"]]
            ),
        },
        "transactions": classifications,
        "report_source": llm_result.get("report_source"),
        "documents": llm_result.get("documents", {}),
        "model": llm_result.get("model"),
        "fallback_used": llm_result.get("fallback_used", False),
        "llm_error": llm_result.get("llm_error"),
        "agent_trace": llm_result.get("agent_trace", agent_trace),
    }


def _build_error_response(
    message: str,
    agent_trace: list[dict[str, Any]],
    tool_result: ToolResult,
) -> dict[str, Any]:
    return {
        "computed_by_backend": True,
        "run_id": None,
        "company_name": "",
        "base_currency": "",
        "summary": {
            "matched_count": 0,
            "possible_match_count": 0,
            "unmatched_payment_proof_count": 0,
            "unmatched_bank_row_count": 0,
        },
        "transactions": [],
        "report_source": None,
        "documents": {},
        "model": None,
        "fallback_used": False,
        "llm_error": message,
        "agent_trace": agent_trace,
    }
