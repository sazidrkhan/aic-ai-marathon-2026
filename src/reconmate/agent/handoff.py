from __future__ import annotations

from typing import Any, Iterable


def choose_demo_model_ids(model_payload: dict[str, Any], *, limit: int = 8) -> list[str]:
    models = model_payload.get("data", [])
    aliases = ["default", "default:latency", "default:throughput"]
    available_ids = {model.get("id") for model in models}
    chosen = [model_id for model_id in aliases if model_id in available_ids]

    for model in models:
        model_id = model.get("id")
        if not model_id or model_id in chosen:
            continue
        features = model.get("supported_features") or []
        if "tools" in features:
            chosen.append(model_id)
        if len(chosen) >= limit:
            return chosen

    for model in models:
        model_id = model.get("id")
        if model_id and model_id not in chosen:
            chosen.append(model_id)
        if len(chosen) >= limit:
            break

    return chosen


def build_chutes_provider_config(*, models: Iterable[str]) -> str:
    model_lines = "\n".join(f"      {model}: {{}}" for model in models)
    return f"""providers:
  chutes:
    name: Chutes
    base_url: https://llm.chutes.ai/v1
    key_env: CHUTES_API_KEY
    api_mode: chat_completions
    model: default:latency
    discover_models: true
    models:
{model_lines}
"""


def build_backend_reconcile_response(run_id: str, agent_result: dict[str, Any]) -> dict[str, Any]:
    report_source = agent_result["report_source"]
    documents = agent_result["documents"]

    return {
        "run_id": run_id,
        "report_source": report_source,
        "documents": {
            "reconciliation_report": {
                "generated": documents["reconciliation_report"]["generated"],
                "source": report_source,
                "content": documents["reconciliation_report"]["content"],
            },
            "discrepancy_summary": {
                "generated": documents["discrepancy_summary"]["generated"],
                "source": report_source,
                "content": documents["discrepancy_summary"]["content"],
            },
        },
        "agent_trace": agent_result["agent_trace"],
        "model": agent_result["model"],
        "fallback_used": agent_result["fallback_used"],
        "llm_error": agent_result["llm_error"],
    }
