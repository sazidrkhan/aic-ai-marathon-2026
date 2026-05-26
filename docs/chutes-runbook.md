# Chutes.AI Runbook

Use this to complete Member A setup on the main demo laptop.

## 1. Configure Environment

Do not commit real keys.

```bash
export CHUTES_API_KEY=cpk_your_key_here
export CHUTES_MODEL=default:latency
export CHUTES_BASE_URL=https://llm.chutes.ai/v1
export CHUTES_TIMEOUT_SECONDS=30
```

## 2. Verify Live Chutes Models

```bash
PYTHONPATH=src python3 scripts/list_chutes_models.py
```

Prefer `default:latency` for the live demo unless a better live model is found.

## 3. Verify Local Fallback

```bash
PYTHONPATH=src python3 -m reconmate.agent.run_sample data/sample/reconciliation_payload.json
```

Expected:

- `report_source` is `template_fallback`.
- Both document types are returned.
- Agent trace includes `chutes_generate_documents` with `fallback` status.

## 4. Verify Live Chutes Generation

```bash
PYTHONPATH=src python3 -m reconmate.agent.run_sample data/sample/reconciliation_payload.json --use-chutes
```

Expected:

- `report_source` is `chutes_agent`.
- `model` is the selected Chutes model.
- Both document types are returned.
- Agent trace includes `chutes_generate_documents` with `success` status.

## 5. Demo Talking Point

Use this wording:

```text
ReconMate uses deterministic finance tools for reconciliation and a Chutes-powered ReconMate Agent for audit-friendly document generation. The LLM explains structured facts; it does not invent or calculate financial truth.
```
