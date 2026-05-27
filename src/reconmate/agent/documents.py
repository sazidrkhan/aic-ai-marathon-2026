from __future__ import annotations

import json
import os
from typing import Any, Literal, NamedTuple, Optional, Protocol

from reconmate.agent.prompts import SYSTEM_PROMPT, build_document_prompt

ProviderName = Literal["chutes", "gemini", "template"]
ProviderMode = Literal["auto", "chutes", "gemini", "template"]


class LlmClient(Protocol):
    model: str

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        """Generate text from an LLM provider."""


class ProviderResult(NamedTuple):
    success: bool
    report_source: str
    model: Optional[str]
    documents: dict[str, dict[str, Any]]
    agent_trace_entry: dict[str, Any]
    error: Optional[str]


def _try_generate_with_client(
    payload: dict[str, Any],
    llm_client: LlmClient,
    provider_name: ProviderName,
    existing_trace: list[dict[str, Any]],
) -> ProviderResult:
    payload_json = json.dumps(payload, indent=2, sort_keys=True)
    user_prompt = build_document_prompt(payload_json)
    step = len(existing_trace) + 1

    try:
        content = llm_client.generate(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
        documents = _split_markdown_documents(content)
        report_source = f"{provider_name}_agent"
        trace_entry = {
            "step": step,
            "tool": f"{provider_name}_generate_documents",
            "status": "success",
            "summary": f"Generated reconciliation report and discrepancy summary using {provider_name.title()}-powered agent prompts.",
        }
        return ProviderResult(
            success=True,
            report_source=report_source,
            model=llm_client.model,
            documents=documents,
            agent_trace_entry=trace_entry,
            error=None,
        )
    except Exception as exc:
        trace_entry = {
            "step": step,
            "tool": f"{provider_name}_generate_documents",
            "status": "failed",
            "summary": f"{provider_name.title()} LLM generation failed: {exc}",
        }
        return ProviderResult(
            success=False,
            report_source="",
            model=None,
            documents={},
            agent_trace_entry=trace_entry,
            error=str(exc),
        )


def generate_agent_documents(payload: dict[str, Any], *, llm_client: LlmClient) -> dict[str, Any]:
    return generate_agent_documents_with_chain(
        payload,
        chutes_client=llm_client,
        gemini_client=None,
        provider_mode="chutes",
    )


def generate_agent_documents_with_chain(
    payload: dict[str, Any],
    *,
    chutes_client: Optional[LlmClient] = None,
    gemini_client: Optional[LlmClient] = None,
    provider_mode: Optional[ProviderMode] = None,
) -> dict[str, Any]:
    if provider_mode is None:
        provider_mode = _get_provider_mode_from_env()

    trace = list(payload.get("agent_trace", []))
    errors: list[str] = []

    chutes_available = chutes_client is not None and chutes_client.api_key is not None if hasattr(chutes_client, "api_key") else False
    gemini_available = gemini_client is not None and gemini_client.api_key is not None if hasattr(gemini_client, "api_key") else False

    if chutes_client is not None:
        try:
            chutes_available = bool(getattr(chutes_client, "api_key", None))
        except Exception:
            chutes_available = False

    if gemini_client is not None:
        try:
            gemini_available = bool(getattr(gemini_client, "api_key", None))
        except Exception:
            gemini_available = False

    providers_to_try: list[tuple[ProviderName, Optional[LlmClient]]] = []

    if provider_mode == "auto":
        if chutes_available and chutes_client is not None:
            providers_to_try.append(("chutes", chutes_client))
        if gemini_available and gemini_client is not None:
            providers_to_try.append(("gemini", gemini_client))
    elif provider_mode == "chutes":
        if chutes_client is not None:
            providers_to_try.append(("chutes", chutes_client))
    elif provider_mode == "gemini":
        if gemini_client is not None:
            providers_to_try.append(("gemini", gemini_client))
    elif provider_mode == "template":
        pass

    for provider_name, client in providers_to_try:
        if client is None:
            continue
        result = _try_generate_with_client(payload, client, provider_name, trace)
        trace.append(result.agent_trace_entry)
        if result.success:
            return {
                "report_source": result.report_source,
                "model": result.model,
                "documents": result.documents,
                "agent_trace": trace,
                "fallback_used": False,
                "llm_error": None,
            }
        if result.error:
            errors.append(f"{provider_name}: {result.error}")

    documents = _template_documents(payload)
    fallback_step = len(trace) + 1
    combined_error = "; ".join(errors) if errors else None
    trace.append(
        {
            "step": fallback_step,
            "tool": "template_fallback",
            "status": "fallback",
            "summary": "Used deterministic template fallback because LLM generation was unavailable"
            + (f": {combined_error}" if combined_error else ""),
        }
    )

    return {
        "report_source": "template_fallback",
        "model": None,
        "documents": documents,
        "agent_trace": trace,
        "fallback_used": True,
        "llm_error": combined_error,
    }


def _get_provider_mode_from_env() -> ProviderMode:
    mode = os.environ.get("LLM_PROVIDER", "auto").lower().strip()
    if mode in ("auto", "chutes", "gemini", "template"):
        return mode  # type: ignore
    return "auto"


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
