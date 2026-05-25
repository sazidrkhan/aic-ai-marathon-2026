"""Test script for the ReconMate FastAPI backend.

Starts the server, hits the /health and /api/reconcile endpoints,
prints the JSON responses, and exits cleanly.

Usage
-----
    python scripts/test_api.py

"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

TEST_PORT = 8010
API_BASE = f"http://127.0.0.1:{TEST_PORT}"

# ---------------------------------------------------------------------------
# Sample payload (same structure as data/sample/reconciliation_payload.json)
# ---------------------------------------------------------------------------
SAMPLE_PAYLOAD = {
    "run_id": "recon_demo_001",
    "company_name": "Demo SME Trading Sdn Bhd",
    "base_currency": "MYR",
    "matched_transactions": [
        {
            "proof_id": "proof_001",
            "bank_row_id": "bank_001",
            "sender_name": "ABC Trading Ltd",
            "amount": 1000.0,
            "currency": "USD",
            "payment_date": "2026-05-20",
            "bank_settlement_date": "2026-05-21",
            "reference": "INV-8821",
            "expected_amount_local": 4700.0,
            "actual_amount_local": 4685.0,
            "local_currency": "MYR",
            "fx_rate": 4.7,
            "fee_difference": 15.0,
            "confidence": 0.94,
            "reason_codes": [
                "reference_exact_match",
                "date_within_tolerance",
                "amount_within_fee_tolerance",
            ],
            "reasoning_facts": [
                "Payment reference INV-8821 matched bank row bank_001.",
                "The bank settlement date is one day after the payment date.",
                "The MYR 15.00 difference is consistent with an expected bank fee.",
            ],
        },
        {
            "proof_id": "proof_002",
            "bank_row_id": "bank_004",
            "sender_name": "Northwind Imports",
            "amount": 250.0,
            "currency": "SGD",
            "payment_date": "2026-05-22",
            "bank_settlement_date": "2026-05-22",
            "reference": "NW-2044",
            "expected_amount_local": 875.0,
            "actual_amount_local": 875.0,
            "local_currency": "MYR",
            "fx_rate": 3.5,
            "fee_difference": 0.0,
            "confidence": 0.98,
            "reason_codes": [
                "reference_exact_match",
                "date_exact_match",
                "amount_exact_match",
            ],
            "reasoning_facts": [
                "Payment reference NW-2044 matched bank row bank_004.",
                "The expected MYR amount equals the bank credit amount.",
                "The transaction date matched exactly.",
            ],
        },
    ],
    "possible_matches": [
        {
            "proof_id": "proof_003",
            "candidate_bank_row_id": "bank_006",
            "sender_name": "Kuala Export Partner",
            "amount": 700.0,
            "currency": "USD",
            "reference": "KEP-7100",
            "confidence": 0.68,
            "reason_codes": [
                "reference_missing",
                "amount_within_fee_tolerance",
                "date_within_tolerance",
            ],
            "reasoning_facts": [
                "The candidate bank row amount is close after FX conversion.",
                "The payment proof reference is missing from the bank statement.",
                "Human review is required before marking the item as reconciled.",
            ],
        }
    ],
    "unmatched_payment_proofs": [
        {
            "proof_id": "proof_004",
            "sender_name": "Pacific Buyer Co",
            "amount": 500.0,
            "currency": "EUR",
            "reference": "PB-9910",
            "confidence": 0.31,
            "reason_codes": ["missing_bank_transaction", "low_ocr_confidence"],
            "reasoning_facts": [
                "No bank row matched the expected local amount or reference.",
                "OCR confidence was low, so the extracted amount should be checked manually.",
            ],
        }
    ],
    "unmatched_bank_rows": [
        {
            "bank_row_id": "bank_009",
            "amount_local": 1200.0,
            "currency": "MYR",
            "settlement_date": "2026-05-23",
            "description": "Unknown incoming transfer",
            "reason_codes": ["missing_payment_proof"],
            "reasoning_facts": [
                "The bank statement contains an incoming transfer without a corresponding payment proof."
            ],
        }
    ],
    "fx_rates_used": [
        {"pair": "USD/MYR", "rate": 4.7, "date": "2026-05-20"},
        {"pair": "SGD/MYR", "rate": 3.5, "date": "2026-05-22"},
        {"pair": "EUR/MYR", "rate": 5.1, "date": "2026-05-23"},
    ],
    "agent_trace": [
        {
            "step": 1,
            "tool": "paddle_ocr_extract",
            "status": "success",
            "summary": "Extracted text from four controlled payment proofs using PaddleOCR.",
        },
        {
            "step": 2,
            "tool": "parse_payment_proof",
            "status": "success",
            "summary": "Extracted sender, amount, currency, dates, and references.",
        },
        {
            "step": 3,
            "tool": "match_transactions",
            "status": "success",
            "summary": "Applied reference, amount, date, FX, and fee matching rules.",
        },
    ],
}


def start_server() -> subprocess.Popen:
    """Start the FastAPI server in a subprocess."""
    env = {**dict(os.environ), "PYTHONPATH": str(REPO / "src")}
    # Forward API key and model from the parent environment, if set
    for key in ("CHUTES_API_KEY", "CHUTES_MODEL", "CHUTES_BASE_URL", "CHUTES_TIMEOUT_SECONDS"):
        value = os.environ.get(key)
        if value is not None:
            env[key] = value
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(TEST_PORT)],
        cwd=REPO,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Give the server time to start
    time.sleep(3)
    if proc.poll() is not None:
        stdout = proc.stdout.read().decode("utf-8", errors="replace") if proc.stdout else ""
        stderr = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
        raise RuntimeError(f"Server failed to start.\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}")
    return proc


def stop_server(proc: subprocess.Popen) -> None:
    """Gracefully terminate the server process."""
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def test_health() -> dict:
    """Test the /health endpoint."""
    print("\n[1/3] Testing /health ...")
    r = requests.get(f"{API_BASE}/health", timeout=5)
    r.raise_for_status()
    data = r.json()
    print(json.dumps(data, indent=2))
    return data


def test_models() -> dict:
    """Test the /api/models endpoint."""
    print("\n[2/3] Testing /api/models ...")
    r = requests.get(f"{API_BASE}/api/models", timeout=5)
    r.raise_for_status()
    data = r.json()
    print(json.dumps(data, indent=2))
    return data


def test_reconcile() -> dict:
    """Test the /api/reconcile endpoint."""
    print("\n[3/3] Testing /api/reconcile ...")
    r = requests.post(
        f"{API_BASE}/api/reconcile",
        json=SAMPLE_PAYLOAD,
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    print("Status:", r.status_code)
    print("Summary:", data.get("summary"))
    print("Documents:", list(data.get("documents", {}).keys()))
    print("Agent trace tools:", [t["tool"] for t in data.get("agent_trace", [])])
    print("Fallback used:", data.get("fallback_used"))
    return data


def main() -> int:
    print("=" * 60)
    print("ReconMate API Test Suite")
    print("=" * 60)

    print(f"\nStarting temporary test server on {API_BASE} ...")
    proc = start_server()

    try:
        print("Running tests ...")
        test_health()
        # test_models()
        test_reconcile()
        print("\nAll tests passed.")
        print("This script intentionally stops its temporary server.")
        print("To run the browser app, use: python main.py")
        print("Then open: http://127.0.0.1:8000/")
        return 0
    except requests.ConnectionError as exc:
        print(f"\n[ERROR] Could not connect to server: {exc}")
        return 1
    except requests.HTTPError as exc:
        print(f"\n[ERROR] HTTP error: {exc}")
        return 1
    finally:
        print("\nStopping temporary test server ...")
        stop_server(proc)


if __name__ == "__main__":
    sys.exit(main())
