from __future__ import annotations

import os
import unittest
from datetime import date
from decimal import Decimal

from tests import _path  # noqa: F401

from reconmate.reconciliation.models import (
    AgentReconcileRequest,
    BankRow,
    FxRate,
    PaymentProof,
)
from reconmate.agent.orchestrator import run_agent_orchestrator


class OrchestratorIntegrationTest(unittest.TestCase):
    """Integration tests for the full Orchestrator-Workers pipeline.

    These tests force template_fallback to avoid requiring live LLM keys.
    """

    def setUp(self):
        if "LLM_PROVIDER" in os.environ:
            self._old_provider = os.environ["LLM_PROVIDER"]
        else:
            self._old_provider = None
        os.environ["LLM_PROVIDER"] = "template"

    def tearDown(self):
        if self._old_provider is not None:
            os.environ["LLM_PROVIDER"] = self._old_provider
        elif "LLM_PROVIDER" in os.environ:
            del os.environ["LLM_PROVIDER"]

    def _make_matched_request(self) -> AgentReconcileRequest:
        return AgentReconcileRequest(
            run_id="test-matched-001",
            company_name="TestCo",
            base_currency="MYR",
            payment_proofs=[
                PaymentProof(
                    proof_id="p1",
                    sender_name="Alice Buyer",
                    amount=Decimal("1000"),
                    currency="MYR",
                    reference="INV-2026-001",
                    payment_date=date(2026, 5, 20),
                )
            ],
            bank_rows=[
                BankRow(
                    bank_row_id="b1",
                    amount_local=Decimal("1000"),
                    currency="MYR",
                    settlement_date=date(2026, 5, 20),
                    description="INV-2026-001 Alice Buyer",
                )
            ],
        )

    def _make_possible_request(self) -> AgentReconcileRequest:
        return AgentReconcileRequest(
            run_id="test-possible-001",
            company_name="TestCo",
            base_currency="MYR",
            payment_proofs=[
                PaymentProof(
                    proof_id="p1",
                    sender_name="Alice Buyer",
                    amount=Decimal("1000"),
                    currency="MYR",
                    reference="INV-2026-001",
                    payment_date=date(2026, 5, 20),
                )
            ],
            bank_rows=[
                BankRow(
                    bank_row_id="b1",
                    amount_local=Decimal("1000"),
                    currency="MYR",
                    settlement_date=date(2026, 5, 20),
                    description="INV-2026-001 Alice Buyer",
                ),
                BankRow(
                    bank_row_id="b2",
                    amount_local=Decimal("1005"),
                    currency="MYR",
                    settlement_date=date(2026, 5, 20),
                    description="INV-2026-001 Alice Buyer alt",
                ),
            ],
        )

    def _make_unmatched_request(self) -> AgentReconcileRequest:
        return AgentReconcileRequest(
            run_id="test-unmatched-001",
            company_name="TestCo",
            base_currency="MYR",
            payment_proofs=[
                PaymentProof(
                    proof_id="p1",
                    sender_name="Alice Buyer",
                    amount=Decimal("1000"),
                    currency="USD",
                    reference="INV-2026-001",
                    payment_date=date(2026, 5, 20),
                )
            ],
            bank_rows=[
                BankRow(
                    bank_row_id="b1",
                    amount_local=Decimal("999"),
                    currency="MYR",
                    settlement_date=date(2026, 6, 1),
                    description="Completely unrelated payment",
                )
            ],
            fx_rates=[],
        )

    def _make_empty_request(self) -> AgentReconcileRequest:
        return AgentReconcileRequest(
            run_id="test-empty-001",
            company_name="TestCo",
            base_currency="MYR",
        )

    def test_orchestrator_returns_computed_by_backend_true(self):
        result = run_agent_orchestrator(self._make_matched_request())
        self.assertTrue(result["computed_by_backend"])
        self.assertEqual(result["run_id"], "test-matched-001")
        self.assertEqual(result["company_name"], "TestCo")

    def test_orchestrator_returns_agent_trace(self):
        result = run_agent_orchestrator(self._make_matched_request())
        self.assertIn("agent_trace", result)
        trace = result["agent_trace"]
        self.assertGreaterEqual(len(trace), 3)

        tool_names = [t["tool"] for t in trace]
        self.assertIn("validate_reconciliation_inputs", tool_names)
        self.assertIn("match_transactions", tool_names)
        self.assertIn("classify_reconciliation_results", tool_names)
        self.assertIn("template_fallback", tool_names)

    def test_orchestrator_matched_classification(self):
        result = run_agent_orchestrator(self._make_matched_request())
        self.assertEqual(result["summary"]["matched_count"], 1)
        self.assertEqual(result["summary"]["possible_match_count"], 0)
        self.assertEqual(result["summary"]["unmatched_payment_proof_count"], 0)
        transactions = result["transactions"]
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0]["classification"], "matched")

    def test_orchestrator_possible_with_close_candidates(self):
        result = run_agent_orchestrator(self._make_possible_request())
        txn = result["transactions"]
        self.assertGreaterEqual(len(txn), 1)
        self.assertIn(
            "multiple_candidate_matches",
            txn[0]["reason_codes"],
        )

    def test_orchestrator_unmatched_with_missing_fx_and_ref(self):
        result = run_agent_orchestrator(self._make_unmatched_request())
        self.assertEqual(result["summary"]["unmatched_payment_proof_count"], 1)
        txn = result["transactions"]
        if txn:
            self.assertEqual(txn[0]["classification"], "unmatched")

    def test_orchestrator_validation_error_on_empty_request(self):
        result = run_agent_orchestrator(self._make_empty_request())
        self.assertIn("llm_error", result)
        self.assertEqual(result["summary"]["matched_count"], 0)

    def test_orchestrator_always_has_documents(self):
        result = run_agent_orchestrator(self._make_matched_request())
        self.assertIn("documents", result)
        docs = result["documents"]
        self.assertIn("reconciliation_report", docs)
        self.assertIn("discrepancy_summary", docs)

    def test_orchestrator_returns_summary_with_counts(self):
        result = run_agent_orchestrator(self._make_matched_request())
        summary = result["summary"]
        self.assertIn("matched_count", summary)
        self.assertIn("possible_match_count", summary)
        self.assertIn("unmatched_payment_proof_count", summary)
        self.assertIn("unmatched_bank_row_count", summary)

    def test_orchestrator_fx_same_currency_no_rate_needed(self):
        request = AgentReconcileRequest(
            run_id="test-fx-001",
            company_name="TestCo",
            base_currency="MYR",
            payment_proofs=[
                PaymentProof(
                    proof_id="p1",
                    amount=Decimal("500"),
                    currency="MYR",
                    reference="REF-001",
                    payment_date=date(2026, 5, 20),
                )
            ],
            bank_rows=[
                BankRow(
                    bank_row_id="b1",
                    amount_local=Decimal("500"),
                    currency="MYR",
                    settlement_date=date(2026, 5, 21),
                    description="REF-001",
                )
            ],
        )
        result = run_agent_orchestrator(request)
        self.assertEqual(result["summary"]["matched_count"], 1)

    def test_orchestrator_fx_conversion_missing_rate(self):
        request = AgentReconcileRequest(
            run_id="test-fx-missing",
            company_name="TestCo",
            base_currency="MYR",
            payment_proofs=[
                PaymentProof(
                    proof_id="p1",
                    amount=Decimal("100"),
                    currency="SGD",
                    reference="REF-001",
                )
            ],
            bank_rows=[
                BankRow(
                    bank_row_id="b1",
                    amount_local=Decimal("100"),
                    currency="MYR",
                    description="REF-001",
                )
            ],
        )
        result = run_agent_orchestrator(request)
        self.assertEqual(result["summary"]["unmatched_payment_proof_count"], 1)
        self.assertEqual(
            result["transactions"][0]["classification"], "unmatched"
        )

    def test_orchestrator_report_source_is_template_fallback(self):
        result = run_agent_orchestrator(self._make_matched_request())
        self.assertEqual(result["report_source"], "template_fallback")
        self.assertTrue(result["fallback_used"])


if __name__ == "__main__":
    unittest.main()
