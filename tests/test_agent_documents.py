import unittest

from tests import _path  # noqa: F401
from reconmate.agent.documents import generate_agent_documents


class SuccessfulClient:
    model = "default:latency"

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        assert "ReconMate" in system_prompt
        assert "Reconciliation Report" in user_prompt
        assert "Discrepancy Summary" in user_prompt
        return """
## Reconciliation Report
Matched proof_001 to bank_001 with audit-ready evidence.

## Discrepancy Summary
proof_002 remains unresolved because no bank transaction matched the payment proof.
""".strip()


class FailingClient:
    model = "default:latency"

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        raise TimeoutError("Chutes request timed out")


def sample_payload() -> dict:
    return {
        "run_id": "recon_demo_001",
        "company_name": "Demo SME Trading Sdn Bhd",
        "base_currency": "MYR",
        "matched_transactions": [
            {
                "proof_id": "proof_001",
                "bank_row_id": "bank_001",
                "amount": 1000.0,
                "currency": "USD",
                "expected_amount_local": 4700.0,
                "actual_amount_local": 4685.0,
                "fee_difference": 15.0,
                "confidence": 0.94,
                "reason_codes": ["reference_exact_match", "amount_within_fee_tolerance"],
            }
        ],
        "possible_matches": [],
        "unmatched_payment_proofs": [
            {
                "proof_id": "proof_002",
                "amount": 500.0,
                "currency": "SGD",
                "reason_codes": ["missing_bank_transaction"],
            }
        ],
        "unmatched_bank_rows": [],
        "fx_rates_used": [{"pair": "USD/MYR", "rate": 4.7, "date": "2026-05-20"}],
        "agent_trace": [],
    }


class AgentDocumentTests(unittest.TestCase):
    def test_generates_both_agent_documents_when_payload_has_matches_and_discrepancies(self):
        result = generate_agent_documents(sample_payload(), llm_client=SuccessfulClient())

        self.assertEqual(result["report_source"], "chutes_hermes")
        self.assertEqual(result["model"], "default:latency")
        self.assertIs(result["fallback_used"], False)
        self.assertIs(result["documents"]["reconciliation_report"]["generated"], True)
        self.assertIs(result["documents"]["discrepancy_summary"]["generated"], True)
        self.assertIn("Matched proof_001", result["documents"]["reconciliation_report"]["content"])
        self.assertIn("proof_002 remains unresolved", result["documents"]["discrepancy_summary"]["content"])
        self.assertEqual(result["agent_trace"][-1]["tool"], "chutes_generate_documents")

    def test_falls_back_to_template_documents_when_chutes_generation_fails(self):
        result = generate_agent_documents(sample_payload(), llm_client=FailingClient())

        self.assertEqual(result["report_source"], "template_fallback")
        self.assertIsNone(result["model"])
        self.assertIs(result["fallback_used"], True)
        self.assertIn("Chutes request timed out", result["llm_error"])
        self.assertIn("Reconciliation Report", result["documents"]["reconciliation_report"]["content"])
        self.assertIn("Discrepancy Summary", result["documents"]["discrepancy_summary"]["content"])
        self.assertEqual(result["agent_trace"][-1]["status"], "fallback")


if __name__ == "__main__":
    unittest.main()
