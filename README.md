# ReconMate: Global Treasury Reconciliation Agent

ReconMate is an AI Marathon 2026 prototype for Problem Statement 3: The Global Treasury Agent.

It uses a Python backend agent base, Chutes.AI LLM document generation, PaddleOCR for payment-proof OCR, and a React frontend planned through Lovable AI.

## Current Base

This repository currently contains the Member A foundation:

- Chutes-compatible LLM client.
- ReconMate system prompt.
- Agent document generation contract.
- Reconciliation Report output.
- Discrepancy Summary output.
- Template fallback when Chutes is unavailable.
- Sample reconciliation payload for controlled demo data.

## Core Principle

The LLM does not perform financial truth calculations. Backend tools calculate FX, fees, match status, and confidence. Chutes generates finance-friendly reports from those structured facts.

## Environment

```bash
export CHUTES_API_KEY=cpk_your_key_here
export CHUTES_BASE_URL=https://llm.chutes.ai/v1
export CHUTES_MODEL=default:latency
export CHUTES_TIMEOUT_SECONDS=30
```

Never commit real API keys.

## Test

```bash
PYTHONPATH=src python3 -m unittest tests/test_agent_documents.py
```

## Demo Without LLM

```bash
PYTHONPATH=src python3 -m reconmate.agent.run_sample data/sample/reconciliation_payload.json
```

## Demo With Chutes

```bash
PYTHONPATH=src python3 -m reconmate.agent.run_sample data/sample/reconciliation_payload.json --use-chutes
```

## Hermes Config Snippet

```bash
PYTHONPATH=src python3 scripts/generate_hermes_config.py
```

## Live Model Discovery

```bash
PYTHONPATH=src python3 scripts/list_chutes_models.py
```

## Documentation

See:

- `docs/agentic-ai-base.md`
- `docs/backend-frontend-contract.md`
- `docs/hermes-chutes-runbook.md`
