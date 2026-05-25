"""Test your Chutes API key end-to-end.

Usage:
    $env:CHUTES_API_KEY="your-key-here"
    python scripts/test_live_api.py

The script will:
1. Check if CHUTES_API_KEY is set in the environment.
2. Generate a small document via the live Chutes LLM.
3. Print whether it received a real LLM response or a fallback.
4. Report any errors (429, 401, network issues, etc.).
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Ensure src/ is on the path
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from reconmate.agent.chutes_client import ChutesClient
from reconmate.agent.documents import generate_agent_documents


def main() -> int:
    print("=" * 60)
    print("ReconMate Chutes API Key Test")
    print("=" * 60)

    api_key = os.environ.get("CHUTES_API_KEY")
    if not api_key:
        print("\n[ERROR] CHUTES_API_KEY is not set in your environment.")
        print("Please run first:")
        print('    $env:CHUTES_API_KEY="your-key-here"')
        return 1

    print(f"\nAPI Key: {api_key[:8]}...{api_key[-4:]}")
    print(f"Model:   {os.environ.get('CHUTES_MODEL', 'default:latency')}")

    # Minimal test payload
    test_payload = {
        "run_id": "api_test_001",
        "company_name": "Test Corp",
        "base_currency": "MYR",
        "matched_transactions": [
            {
                "proof_id": "p_001",
                "bank_row_id": "b_001",
                "amount": 100.0,
                "currency": "USD",
                "expected_amount_local": 470.0,
                "actual_amount_local": 468.0,
                "fee_difference": 2.0,
                "confidence": 0.95,
                "reason_codes": ["reference_exact_match"],
            }
        ],
        "possible_matches": [],
        "unmatched_payment_proofs": [],
        "unmatched_bank_rows": [],
        "fx_rates_used": [{"pair": "USD/MYR", "rate": 4.7, "date": "2026-05-20"}],
        "agent_trace": [],
    }

    print("\nSending test request to Chutes LLM ...")
    start = time.time()
    try:
        client = ChutesClient.from_env()
        result = generate_agent_documents(test_payload, llm_client=client)
        elapsed = time.time() - start

        print(f"\nResponse time: {elapsed:.1f}s")
        print(f"Report source: {result['report_source']}")
        print(f"Model used:    {result.get('model') or 'N/A (fallback)'}")
        print(f"Fallback used: {result['fallback_used']}")

        if result["fallback_used"]:
            print("\n[WARNING] Template fallback was used. The LLM was not reached.")
            print("Error:", result["llm_error"])
            return 1
        else:
            print("\n[SUCCESS] Live LLM generation worked!")
            print("Sample of Reconciliation Report:")
            content = result["documents"]["reconciliation_report"]["content"]
            print(content[:300] + "..." if len(content) > 300 else content)
            return 0

    except Exception as exc:
        elapsed = time.time() - start
        print(f"\n[FAILED] Request failed after {elapsed:.1f}s")
        print("Error:", str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
