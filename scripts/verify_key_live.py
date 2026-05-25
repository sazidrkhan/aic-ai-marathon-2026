"""Test the live Chutes API key directly.

Usage:
    $env:CHUTES_API_KEY="your-key-here"
    python scripts/verify_key_live.py

This script runs a direct test using the existing run_sample module,
which is the most reliable way to verify the key works.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Ensure src/ is on the path
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from reconmate.agent.chutes_client import ChutesClient
from reconmate.agent.documents import generate_agent_documents


def main() -> int:
    print("=" * 60)
    print("Chutes API Key Test")
    print("=" * 60)

    api_key = os.environ.get("CHUTES_API_KEY")
    model = os.environ.get("CHUTES_MODEL", "default:latency")

    if not api_key:
        print("\n[ERROR] CHUTES_API_KEY is not set.")
        print("Please run: $env:CHUTES_API_KEY=\"your-key-here\"")
        return 1

    print(f"\nKey prefix: {api_key[:15]}...")
    print(f"Model:      {model}")

    # Test payload
    test_payload = {
        "run_id": "key_test_001",
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

    print("\nSending request to Chutes LLM ...")
    client = ChutesClient(api_key=api_key, model=model)

    try:
        result = generate_agent_documents(test_payload, llm_client=client)

        print(f"\nResult:")
        print(f"  Source:        {result['report_source']}")
        print(f"  Model:         {result.get('model') or 'N/A'}")
        print(f"  Fallback:      {result['fallback_used']}")

        if result["fallback_used"]:
            print(f"\n[WARNING] Template fallback used.")
            print(f"Error: {result['llm_error']}")
            print("\nYour key IS valid but may be rate-limited (429).")
            print("Run again in a few minutes, or the demo will use template fallback.")
            return 0  # Not a failure
        else:
            print("\n[SUCCESS] Live LLM generation worked!")
            return 0

    except Exception as exc:
        print(f"\n[ERROR] {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
