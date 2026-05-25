# ReconMate: Global Treasury Reconciliation Agent

ReconMate is an AI Marathon 2026 prototype for Problem Statement 3: The Global Treasury Agent.

It uses a Python backend agent base, Chutes.AI LLM document generation, PaddleOCR for payment-proof OCR, and a React frontend planned through Lovable AI.

## Quick Start

```bash
# Install required Python dependencies
pip install -r requirements.txt

# Start the FastAPI server
python main.py

# Test the API
python scripts/test_api.py
```

Stop the server with `Ctrl+C`.

`python scripts/test_api.py` is only a test command. It starts a temporary server, verifies the API, and stops it on purpose.

For optional real OCR support, install:

```bash
pip install -r requirements-ocr.txt
```

## Current Base

This repository contains:

- **FastAPI backend** (`main.py`) with `/api/reconcile`, `/health`, `/api/models`, `/api/ocr-extract`
- **Chutes-compatible LLM client** with retry logic for rate limits
- **ReconMate system prompt** for finance-safe document generation
- **Agent document generation** (Reconciliation Report + Discrepancy Summary)
- **Template fallback** when Chutes is unavailable or rate-limited
- **Optional PaddleOCR integration** (`reconmate.agent.ocr_engine`) — install `requirements-ocr.txt` to enable
- **Sample reconciliation payload** for controlled demo data
- **Minimal frontend** (`frontend/index.html`) served at `/` for demo
- **Pitch deck** (`docs/pitch_deck.md`) and **demo script** (`docs/video_script.md`)

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

## API Test

```bash
python scripts/test_api.py
```

## Verify API Key

```bash
python scripts/verify_key.py
```

## Hermes Config Snippet

```bash
PYTHONPATH=src python3 scripts/generate_hermes_config.py
```

## Live Model Discovery

```bash
PYTHONPATH=src python3 scripts/list_chutes_models.py
```

## Frontend Demo

Open `http://127.0.0.1:8000/` in a browser while the server is running.

## Submission Package

- `docs/pitch_deck.md` — Pitch deck outline and content
- `docs/video_script.md` — 3-4 minute demo video script
- `frontend/index.html` — Minimal frontend for live demo
- `README.md` — This file
- `API_README.md` — API documentation

## Team

- **Backend / AI Agent**: Your Name
- **Frontend**: Syafieqah (Lovable AI)
- **Problem**: Track 3 — The Global Treasury Agent

## Documentation

See:

- `docs/agentic-ai-base.md`
- `docs/backend-frontend-contract.md`
- `docs/hermes-chutes-runbook.md`
- `docs/pitch_deck.md`
- `docs/video_script.md`
