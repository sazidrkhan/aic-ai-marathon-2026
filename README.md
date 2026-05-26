# ReconMate: Global Treasury Reconciliation Agent

ReconMate is an AI Marathon 2026 prototype for Problem Statement 3: The Global Treasury Agent.

ReconMate uses a custom FastAPI orchestrator and direct Chutes.AI inference for finance-safe document generation. It does not use any prebuilt agent framework. It uses PaddleOCR for payment-proof OCR and a React frontend planned through Lovable AI.

## Quick Start

```powershell
# From the repository root
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version  # should show Python 3.11.x
python -m pip install -r requirements.txt
python main.py
```

Stop the server with `Ctrl+C`.

`python scripts/test_api.py` is only a test command. It starts a temporary server, verifies the API, and stops it on purpose.

For optional real OCR support, install:

```powershell
python -m pip install -r requirements-ocr.txt
```

Use Python 3.11 on Windows for this project, especially for OCR. If
`python --version` shows others, there is a slight chance PaddlePaddle cannot install.


## Current Base

This repository contains:

- **FastAPI backend** (`main.py`) with `/api/reconcile`, `/health`, `/api/models`, `/api/ocr-extract`
- **Chutes.AI LLM client** with retry logic for rate limits
- **ReconMate system prompt** for finance-safe document generation
- **Agent document generation** (Reconciliation Report + Discrepancy Summary)
- **Template fallback** when Chutes is unavailable or rate-limited
- **Optional OCR integration** (`reconmate.agent.ocr_engine`) - install `requirements-ocr.txt` to enable PaddleOCR image/scanned-PDF extraction and text-PDF parsing
- **Sample reconciliation payload** for controlled demo data
- **Lovable React frontend** (`frontend/`) with TanStack Start — connect to backend via `VITE_API_BASE_URL`
- **Minimal fallback frontend** (`frontend/index.html`) served at `/` for quick demo
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

## Sample Data

- `data/sample/reconciliation_payload.json` - compact default demo payload
- `data/sample/ocr_demo/payment_proof_*.png` - generated proof images for OCR upload testing
- `data/sample/ocr_demo/bank_statement_may_2026.csv` - matching bank statement CSV for the Bank Statement tab

## Verify API Key

```bash
python scripts/verify_key.py
```

## Lovable React Frontend

**Note:** The hosted Lovable preview URL cannot reach your local FastAPI backend. Always test local backend integration using the local frontend dev server (`npm run dev`).

**Exact steps to run locally:**

```powershell
# Terminal 1 - Backend (must run first)
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version  # should show Python 3.11.x
python -m pip install -r requirements.txt
python -m pip install -r requirements-ocr.txt
$env:PYTHONPATH="src"
python main.py
# Backend runs at http://127.0.0.1:8000

# Terminal 2 - Frontend
cd frontend
npm install    # first time only
npm run dev
# Frontend runs at http://localhost:5173
```

**Open in browser:**
- Dashboard: `http://localhost:5173/dashboard`
- Health check indicator shows: "Backend connected" (green) or "Backend unreachable" (red)
- Click "Load Sample Payload" then "Run Reconciliation"

**Environment:**
The frontend reads `VITE_API_BASE_URL` from `frontend/.env` (defaults to `http://127.0.0.1:8000`).

**Backend CORS:**
- Allowed origins: `localhost:5173`, `127.0.0.1:5173`, `localhost:3000`, `127.0.0.1:3000`
- Credentials: disabled (`allow_credentials=False`)

**Debugging "Failed to fetch" / "Could not reach agent":**
1. Verify backend is running at `http://127.0.0.1:8000` (open directly in browser)
2. Check the dashboard's "Backend status" badge — if red, backend is unreachable
3. Check browser console (F12) — look for `[ReconMate]` log lines showing the exact URL, method, and error
4. Verify you are using the **local frontend dev server** (`localhost:5173`), not the Lovable preview URL
5. Confirm your frontend port matches the CORS allowed origins list (see above)

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
- `docs/chutes-runbook.md` (legacy provider notes)
- `docs/pitch_deck.md`
- `docs/video_script.md`
