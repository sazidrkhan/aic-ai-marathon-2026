# ReconMate Agentic AI Base

ReconMate is the Global Treasury Agent for AI Marathon 2026 Problem Statement 3. The agentic base separates deterministic financial reconciliation from LLM-generated finance communication.

## Competition Fit

- OCR: PaddleOCR extracts text from controlled payment proofs.
- Reasoning logic: backend tools calculate FX conversion, fee tolerance, match confidence, and discrepancy reason codes.
- Tool usage: the backend exposes each workflow step as a traceable tool action.
- Reconciliation Report: generated for successful matches.
- Discrepancy Summary: generated for unresolved, failed, or possible matches.
- Agentic AI: Chutes.AI generates audit-friendly documents from structured tool facts.

## Architecture

```text
React frontend from Lovable AI
  -> Python backend /api/reconcile
  -> PaddleOCR extraction
  -> Payment proof parser
  -> Bank statement parser
  -> FX and fee calculator
  -> Matching engine
  -> ReconMate agent document generator
  -> Chutes.AI LLM or template fallback
```

## Member A Scope

Sazid owns the Chutes.AI setup and the ReconMate agent contract:

- `CHUTES_API_KEY` stays in environment variables only.
- Chutes endpoint is `https://llm.chutes.ai/v1`.
- Default model is `default:latency` unless live model discovery suggests a better model.
- LLM generates explanations and documents only.
- Backend remains source of truth for financial math and match status.

## Document Rules

The agent generates two document types:

- `reconciliation_report`: for `matched_transactions`.
- `discrepancy_summary`: for `possible_matches`, `unmatched_payment_proofs`, and `unmatched_bank_rows`.

If both matched and unresolved items exist, both documents are generated in the same run.

## Backend Contract

Input to `generate_agent_documents()` is a structured reconciliation payload:

```json
{
  "run_id": "recon_demo_001",
  "company_name": "Demo SME Trading Sdn Bhd",
  "base_currency": "MYR",
  "matched_transactions": [],
  "possible_matches": [],
  "unmatched_payment_proofs": [],
  "unmatched_bank_rows": [],
  "fx_rates_used": [],
  "agent_trace": []
}
```

Output:

```json
{
  "report_source": "chutes_agent",
  "model": "default:latency",
  "documents": {
    "reconciliation_report": {"generated": true, "content": "..."},
    "discrepancy_summary": {"generated": true, "content": "..."}
  },
  "agent_trace": [],
  "fallback_used": false,
  "llm_error": null
}
```

If Chutes fails, `report_source` becomes `template_fallback`, `fallback_used` becomes `true`, and deterministic template documents are returned.

## Local Commands

Run tests:

```bash
PYTHONPATH=src python3 -m unittest tests/test_agent_documents.py
```

Run fallback demo without Chutes:

```bash
PYTHONPATH=src python3 -m reconmate.agent.run_sample data/sample/reconciliation_payload.json
```

Run with Chutes:

```bash
export CHUTES_API_KEY=cpk_your_key_here
export CHUTES_MODEL=default:latency
PYTHONPATH=src python3 -m reconmate.agent.run_sample data/sample/reconciliation_payload.json --use-chutes
```

Do not commit real API keys.
