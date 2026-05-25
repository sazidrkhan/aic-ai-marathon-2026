# Backend and Frontend Contract

This contract is for Tanvir's Python backend and Syafieqah's React frontend generated through Lovable AI.

## Endpoint

```text
POST /api/reconcile
```

The endpoint should run the full reconciliation workflow:

```text
PaddleOCR -> proof parser -> bank parser -> FX/fee tools -> matcher -> ReconMate agent documents
```

## Backend Response

```json
{
  "run_id": "recon_demo_001",
  "summary": {
    "matched_count": 2,
    "possible_match_count": 1,
    "unmatched_payment_proof_count": 1,
    "unmatched_bank_row_count": 1
  },
  "transactions": [],
  "documents": {
    "reconciliation_report": {
      "generated": true,
      "source": "chutes_hermes",
      "content": "## Reconciliation Report\n..."
    },
    "discrepancy_summary": {
      "generated": true,
      "source": "chutes_hermes",
      "content": "## Discrepancy Summary\n..."
    }
  },
  "agent_trace": [
    {
      "step": 1,
      "tool": "paddle_ocr_extract",
      "status": "success",
      "summary": "Extracted text from controlled payment proofs using PaddleOCR."
    }
  ],
  "model": "default:latency",
  "fallback_used": false,
  "llm_error": null
}
```

## Frontend Display Rules

The React UI should have these sections:

1. Payment Proof Input
2. Bank Statement Input
3. Reconciliation Result
4. Agent Tool Trace
5. Hermes/Chutes Generated Report
6. Discrepancy Summary

Show this label only when `source` is `chutes_hermes` and `fallback_used` is `false`:

```text
Generated using Chutes-powered Hermes Agent
```

Show this label when `fallback_used` is `true`:

```text
Template fallback used because LLM generation was unavailable
```

Do not show the Chutes/Hermes label for template fallback output.

## Document Rendering

The first MVP can render document `content` as Markdown. PDF export can be added later.

Recommended UI behavior:

- Show `reconciliation_report` only if `generated` is `true`.
- Show `discrepancy_summary` only if `generated` is `true`.
- Keep the agent trace visible during the demo to satisfy the agentic architecture judging criteria.

## Backend Integration Snippet

```python
from reconmate.agent.chutes_client import ChutesClient
from reconmate.agent.documents import generate_agent_documents
from reconmate.agent.handoff import build_backend_reconcile_response


def reconcile_endpoint_handler(reconciliation_payload: dict) -> dict:
    agent_result = generate_agent_documents(
        reconciliation_payload,
        llm_client=ChutesClient.from_env(),
    )
    response = build_backend_reconcile_response(
        reconciliation_payload["run_id"],
        agent_result,
    )
    response["summary"] = {
        "matched_count": len(reconciliation_payload.get("matched_transactions", [])),
        "possible_match_count": len(reconciliation_payload.get("possible_matches", [])),
        "unmatched_payment_proof_count": len(reconciliation_payload.get("unmatched_payment_proofs", [])),
        "unmatched_bank_row_count": len(reconciliation_payload.get("unmatched_bank_rows", [])),
    }
    return response
```

## Finance-Safe Boundary

The backend must decide match status before the agent document generator is called.

The Chutes/Hermes agent may explain:

- Why a match was accepted.
- Why a discrepancy remains unresolved.
- What a finance user should check next.

The Chutes/Hermes agent must not decide:

- Final match status.
- FX rate truth.
- Fee calculation.
- Whether money was actually settled.
