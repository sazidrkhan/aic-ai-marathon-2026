from __future__ import annotations

import json
from typing import Any, Protocol

from reconmate.agent.prompts import SYSTEM_PROMPT, build_document_prompt


class LlmClient(Protocol):
    model: str

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        """Generate text from an LLM provider."""


def generate_agent_documents(payload: dict[str, Any], *, llm_client: LlmClient) -> dict[str, Any]:
    payload_json = json.dumps(payload, indent=2, sort_keys=True)
    user_prompt = build_document_prompt(payload_json)
    trace = list(payload.get("agent_trace", []))

    try:
        content = llm_client.generate(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
        documents = _split_markdown_documents(content)
        trace.append(
            {
                "step": len(trace) + 1,
                "tool": "chutes_generate_documents",
                "status": "success",
                "summary": "Generated reconciliation report and discrepancy summary using Chutes-powered agent prompts.",
            }
        )
        return {
            "report_source": "chutes_agent",
            "model": llm_client.model,
            "documents": documents,
            "agent_trace": trace,
            "fallback_used": False,
            "llm_error": None,
        }
    except Exception as exc:  # Demo reliability: report generation must not crash reconciliation.
        documents = _template_documents(payload)
        trace.append(
            {
                "step": len(trace) + 1,
                "tool": "chutes_generate_documents",
                "status": "fallback",
                "summary": f"Used deterministic template fallback because LLM generation failed: {exc}",
            }
        )
        return {
            "report_source": "template_fallback",
            "model": None,
            "documents": documents,
            "agent_trace": trace,
            "fallback_used": True,
            "llm_error": str(exc),
        }


def _split_markdown_documents(content: str) -> dict[str, dict[str, Any]]:
    reconciliation = _extract_section(content, "## Reconciliation Report", "## Discrepancy Summary")
    discrepancy = _extract_section(content, "## Discrepancy Summary", None)

    return {
        "reconciliation_report": {
            "generated": bool(reconciliation.strip()),
            "content": reconciliation.strip(),
        },
        "discrepancy_summary": {
            "generated": bool(discrepancy.strip()),
            "content": discrepancy.strip(),
        },
    }


def _extract_section(content: str, start_marker: str, end_marker: str | None) -> str:
    start = content.find(start_marker)
    if start == -1:
        return content if end_marker is None else ""

    end = len(content)
    if end_marker is not None:
        marker_index = content.find(end_marker, start + len(start_marker))
        if marker_index != -1:
            end = marker_index

    return content[start:end].strip()


def _template_documents(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    matched = payload.get("matched_transactions", [])
    possible = payload.get("possible_matches", [])
    unmatched_proofs = payload.get("unmatched_payment_proofs", [])
    unmatched_bank_rows = payload.get("unmatched_bank_rows", [])

    reconciliation_lines = [
        "## Reconciliation Report",
        f"Run ID: {payload.get('run_id', 'unknown')}",
        f"Company: {payload.get('company_name', 'unknown')}",
        f"Base currency: {payload.get('base_currency', 'unknown')}",
        "",
        f"Matched transactions: {len(matched)}",
    ]
    for item in matched:
        reconciliation_lines.append(
            "- "
            f"{item.get('proof_id', 'unknown proof')} matched to {item.get('bank_row_id', 'unknown bank row')} "
            f"with confidence {item.get('confidence', 'unknown')}. Reason codes: "
            f"{', '.join(item.get('reason_codes', [])) or 'none provided'}."
        )

    discrepancy_lines = [
        "## Discrepancy Summary",
        f"Possible matches requiring review: {len(possible)}",
        f"Unmatched payment proofs: {len(unmatched_proofs)}",
        f"Unmatched bank rows: {len(unmatched_bank_rows)}",
        "",
    ]
    for item in possible:
        discrepancy_lines.append(
            f"- Possible match {item.get('proof_id', 'unknown proof')} requires human review. "
            f"Reason codes: {', '.join(item.get('reason_codes', [])) or 'none provided'}."
        )
    for item in unmatched_proofs:
        discrepancy_lines.append(
            f"- Payment proof {item.get('proof_id', 'unknown proof')} is unresolved. "
            f"Reason codes: {', '.join(item.get('reason_codes', [])) or 'none provided'}."
        )
    for item in unmatched_bank_rows:
        discrepancy_lines.append(
            f"- Bank row {item.get('bank_row_id', 'unknown bank row')} has no matched proof. "
            f"Reason codes: {', '.join(item.get('reason_codes', [])) or 'none provided'}."
        )

    return {
        "reconciliation_report": {
            "generated": bool(matched),
            "content": "\n".join(reconciliation_lines),
        },
        "discrepancy_summary": {
            "generated": bool(possible or unmatched_proofs or unmatched_bank_rows),
            "content": "\n".join(discrepancy_lines),
        },
    }
