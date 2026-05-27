import os
import unittest

from tests import _path  # noqa: F401
from reconmate.agent.documents import (
    generate_agent_documents,
    generate_agent_documents_with_chain,
)


class SuccessfulChutesClient:
    model = "default:latency"
    api_key = "test-chutes-key"

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        assert "ReconMate" in system_prompt
        return """
## Reconciliation Report
Matched proof_001 to bank_001 with audit-ready evidence.

## Discrepancy Summary
proof_002 remains unresolved because no bank transaction matched the payment proof.
""".strip()


class SuccessfulGeminiClient:
    model = "gemini-3.5-flash"
    api_key = "test-gemini-key"

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        assert "ReconMate" in system_prompt
        return """
## Reconciliation Report
Gemini-generated: Matched proof_001 to bank_001 with audit-ready evidence.

## Discrepancy Summary
Gemini-generated: proof_002 remains unresolved because no bank transaction matched.
""".strip()


class FailingChutesClient:
    model = "default:latency"
    api_key = "test-chutes-key"

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        raise TimeoutError("Chutes request timed out")


class FailingGeminiClient:
    model = "gemini-3.5-flash"
    api_key = "test-gemini-key"

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        raise RuntimeError("Gemini API returned 429 Too Many Requests")


class UnconfiguredChutesClient:
    model = "default:latency"
    api_key = None

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        raise RuntimeError("CHUTES_API_KEY is not configured")


class UnconfiguredGeminiClient:
    model = "gemini-3.5-flash"
    api_key = None

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        raise RuntimeError("GEMINI_API_KEY is not configured")


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
        result = generate_agent_documents(sample_payload(), llm_client=SuccessfulChutesClient())

        self.assertEqual(result["report_source"], "chutes_agent")
        self.assertEqual(result["model"], "default:latency")
        self.assertIs(result["fallback_used"], False)
        self.assertIs(result["documents"]["reconciliation_report"]["generated"], True)
        self.assertIs(result["documents"]["discrepancy_summary"]["generated"], True)
        self.assertIn("Matched proof_001", result["documents"]["reconciliation_report"]["content"])
        self.assertIn("proof_002 remains unresolved", result["documents"]["discrepancy_summary"]["content"])

    def test_falls_back_to_template_documents_when_chutes_generation_fails(self):
        result = generate_agent_documents(sample_payload(), llm_client=FailingChutesClient())

        self.assertEqual(result["report_source"], "template_fallback")
        self.assertIsNone(result["model"])
        self.assertIs(result["fallback_used"], True)
        self.assertIn("Chutes request timed out", result["llm_error"])
        self.assertIn("Reconciliation Report", result["documents"]["reconciliation_report"]["content"])
        self.assertIn("Discrepancy Summary", result["documents"]["discrepancy_summary"]["content"])
        self.assertEqual(result["agent_trace"][-1]["status"], "fallback")


class GeminiClientTests(unittest.TestCase):
    def test_gemini_success_returns_gemini_agent_source(self):
        result = generate_agent_documents_with_chain(
            sample_payload(),
            chutes_client=None,
            gemini_client=SuccessfulGeminiClient(),
            provider_mode="gemini",
        )

        self.assertEqual(result["report_source"], "gemini_agent")
        self.assertEqual(result["model"], "gemini-3.5-flash")
        self.assertIs(result["fallback_used"], False)
        self.assertIsNone(result["llm_error"])
        self.assertIn("Gemini-generated", result["documents"]["reconciliation_report"]["content"])

    def test_gemini_failure_falls_back_to_template(self):
        result = generate_agent_documents_with_chain(
            sample_payload(),
            chutes_client=None,
            gemini_client=FailingGeminiClient(),
            provider_mode="gemini",
        )

        self.assertEqual(result["report_source"], "template_fallback")
        self.assertIsNone(result["model"])
        self.assertIs(result["fallback_used"], True)
        self.assertIn("Gemini API returned 429", result["llm_error"])


class ProviderChainTests(unittest.TestCase):
    def setUp(self):
        if "LLM_PROVIDER" in os.environ:
            self._old_llm_provider = os.environ["LLM_PROVIDER"]
        else:
            self._old_llm_provider = None

    def tearDown(self):
        if self._old_llm_provider is not None:
            os.environ["LLM_PROVIDER"] = self._old_llm_provider
        elif "LLM_PROVIDER" in os.environ:
            del os.environ["LLM_PROVIDER"]

    def test_auto_mode_chutes_available_uses_chutes_first(self):
        result = generate_agent_documents_with_chain(
            sample_payload(),
            chutes_client=SuccessfulChutesClient(),
            gemini_client=SuccessfulGeminiClient(),
            provider_mode="auto",
        )

        self.assertEqual(result["report_source"], "chutes_agent")
        self.assertEqual(result["model"], "default:latency")
        self.assertIs(result["fallback_used"], False)

    def test_auto_mode_chutes_fails_tries_gemini(self):
        result = generate_agent_documents_with_chain(
            sample_payload(),
            chutes_client=FailingChutesClient(),
            gemini_client=SuccessfulGeminiClient(),
            provider_mode="auto",
        )

        self.assertEqual(result["report_source"], "gemini_agent")
        self.assertEqual(result["model"], "gemini-3.5-flash")
        self.assertIs(result["fallback_used"], False)
        self.assertIn("Gemini-generated", result["documents"]["reconciliation_report"]["content"])
        self.assertEqual(len(result["agent_trace"]), 2)
        self.assertEqual(result["agent_trace"][0]["status"], "failed")
        self.assertEqual(result["agent_trace"][1]["status"], "success")

    def test_auto_mode_both_fail_falls_back_to_template(self):
        result = generate_agent_documents_with_chain(
            sample_payload(),
            chutes_client=FailingChutesClient(),
            gemini_client=FailingGeminiClient(),
            provider_mode="auto",
        )

        self.assertEqual(result["report_source"], "template_fallback")
        self.assertIsNone(result["model"])
        self.assertIs(result["fallback_used"], True)
        self.assertIn("Chutes request timed out", result["llm_error"])
        self.assertIn("Gemini API returned 429", result["llm_error"])
        self.assertEqual(len(result["agent_trace"]), 3)
        self.assertEqual(result["agent_trace"][0]["status"], "failed")
        self.assertEqual(result["agent_trace"][1]["status"], "failed")
        self.assertEqual(result["agent_trace"][2]["status"], "fallback")

    def test_template_mode_skips_all_llms(self):
        result = generate_agent_documents_with_chain(
            sample_payload(),
            chutes_client=SuccessfulChutesClient(),
            gemini_client=SuccessfulGeminiClient(),
            provider_mode="template",
        )

        self.assertEqual(result["report_source"], "template_fallback")
        self.assertIsNone(result["model"])
        self.assertIs(result["fallback_used"], True)
        self.assertEqual(len(result["agent_trace"]), 1)
        self.assertEqual(result["agent_trace"][0]["tool"], "template_fallback")

    def test_chutes_mode_only_tries_chutes(self):
        result = generate_agent_documents_with_chain(
            sample_payload(),
            chutes_client=FailingChutesClient(),
            gemini_client=SuccessfulGeminiClient(),
            provider_mode="chutes",
        )

        self.assertEqual(result["report_source"], "template_fallback")
        self.assertEqual(len(result["agent_trace"]), 2)
        self.assertEqual(result["agent_trace"][0]["tool"], "chutes_generate_documents")
        self.assertEqual(result["agent_trace"][1]["tool"], "template_fallback")


if __name__ == "__main__":
    unittest.main()
