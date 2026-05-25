# ReconMate API

Backend for the Global Treasury Reconciliation Agent (AI Marathon 2026).

## Quick Start

```bash
# 1. Install required dependencies
pip install -r requirements.txt

# 2. Start the server
python main.py

# 3. Test the API
python scripts/test_api.py
```

`python scripts/test_api.py` starts a temporary test server and stops it on purpose.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CHUTES_API_KEY` | Your Chutes API key | (optional) |
| `CHUTES_MODEL` | Model to use | `default:latency` |
| `CHUTES_BASE_URL` | Chutes API base URL | `https://llm.chutes.ai/v1` |
| `CHUTES_TIMEOUT_SECONDS` | Request timeout | `30` |

## API Endpoints

- `GET /health` — Health check
- `GET /api/models` — List available models
- `POST /api/reconcile` — Run reconciliation workflow
- `POST /api/ocr-extract` — Extract text from payment proof image

## Testing with Live API Key

```powershell
$env:CHUTES_API_KEY="your-key-here"
python scripts/test_live_api.py
```

## OCR

To enable real OCR, install the optional OCR dependencies:

```bash
pip install -r requirements-ocr.txt
```

Without it, the OCR endpoints return a stub response for demo purposes.

## Demo Frontend

Open `http://127.0.0.1:8000/` in a browser while the server is running.

## Team

- **Backend / Agent**: Your Name
- **Frontend**: Syafieqah (Lovable AI)
- **Problem**: Track 3 — The Global Treasury Agent

## License

Hackathon submission for AI Marathon 2026.
