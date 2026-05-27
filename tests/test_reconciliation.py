from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from tests import _path  # noqa: F401

from reconmate.reconciliation import fx as fx_module
from reconmate.reconciliation import fees as fees_module
from reconmate.reconciliation import matcher as matcher_module
from reconmate.reconciliation.models import (
    AgentReconcileRequest,
    BankRow,
    FeeTolerance,
    FxRate,
    MatchCandidate,
    PaymentProof,
)


class FxTests(unittest.TestCase):
    def test_parse_fx_pair_splits_correctly(self):
        source, target = fx_module.parse_fx_pair("USD_MYR")
        self.assertEqual(source, "USD")
        self.assertEqual(target, "MYR")

    def test_parse_fx_pair_raises_on_missing_underscore(self):
        with self.assertRaises(ValueError):
            fx_module.parse_fx_pair("USDMYR")

    def test_build_fx_lookup_returns_rate_when_target_matches_base(self):
        rates = [FxRate(pair="USD_MYR", rate=Decimal("4.45"))]
        lookup = fx_module.build_fx_lookup(rates, "MYR")
        self.assertEqual(lookup["USD"], Decimal("4.45"))

    def test_build_fx_lookup_ignores_unrelated_pairs(self):
        rates = [FxRate(pair="EUR_SGD", rate=Decimal("1.5"))]
        lookup = fx_module.build_fx_lookup(rates, "MYR")
        self.assertNotIn("EUR", lookup)
        self.assertNotIn("SGD", lookup)

    def test_apply_fx_rate_same_currency_returns_1_0(self):
        proof = PaymentProof(
            proof_id="p1", amount=Decimal("1000"), currency="MYR"
        )
        expected, rate, source, codes, facts = fx_module.apply_fx_rate(
            proof, {}, "MYR"
        )
        self.assertEqual(expected, Decimal("1000"))
        self.assertEqual(rate, Decimal("1.0"))
        self.assertEqual(source, "default_1.0")

    def test_apply_fx_rate_known_pair_converts(self):
        proof = PaymentProof(
            proof_id="p1", amount=Decimal("500"), currency="USD"
        )
        fx_lookup = {"USD": Decimal("4.45")}
        expected, rate, source, codes, facts = fx_module.apply_fx_rate(
            proof, fx_lookup, "MYR"
        )
        self.assertEqual(expected, Decimal("2225"))
        self.assertEqual(rate, Decimal("4.45"))
        self.assertEqual(source, "provided")

    def test_apply_fx_rate_missing_rate_returns_none(self):
        proof = PaymentProof(
            proof_id="p1", amount=Decimal("500"), currency="SGD"
        )
        expected, rate, source, codes, facts = fx_module.apply_fx_rate(
            proof, {}, "MYR"
        )
        self.assertIsNone(expected)
        self.assertIsNone(rate)
        self.assertEqual(source, "missing")
        self.assertIn("missing_fx_rate", codes)


class FeesTests(unittest.TestCase):
    def test_calculate_tolerance_percent_based(self):
        result = fees_module.calculate_tolerance_allowed(
            Decimal("10000"), Decimal("0.02"), Decimal("20")
        )
        self.assertEqual(result, Decimal("200"))

    def test_calculate_tolerance_fixed_capped(self):
        result = fees_module.calculate_tolerance_allowed(
            Decimal("100"), Decimal("0.02"), Decimal("20")
        )
        self.assertEqual(result, Decimal("20"))

    def test_evaluate_fee_tolerance_within_threshold(self):
        fee_diff, tol_allowed, within, codes, facts = (
            fees_module.evaluate_fee_tolerance(
                Decimal("1000"),
                Decimal("1010"),
                FeeTolerance(percent=Decimal("0.02"), fixed=Decimal("20")),
                "MYR",
                "p1",
                "b1",
            )
        )
        self.assertEqual(fee_diff, Decimal("10"))
        self.assertTrue(within)
        self.assertIn("amount_within_fee_tolerance", codes)

    def test_evaluate_fee_tolerance_outside_threshold(self):
        fee_diff, tol_allowed, within, codes, facts = (
            fees_module.evaluate_fee_tolerance(
                Decimal("1000"),
                Decimal("1100"),
                FeeTolerance(percent=Decimal("0.02"), fixed=Decimal("20")),
                "MYR",
                "p1",
                "b1",
            )
        )
        self.assertEqual(fee_diff, Decimal("100"))
        self.assertFalse(within)
        self.assertIn("amount_outside_fee_tolerance", codes)

    def test_evaluate_fee_tolerance_none_inputs(self):
        fee_diff, tol_allowed, within, codes, facts = (
            fees_module.evaluate_fee_tolerance(
                None,
                Decimal("1000"),
                FeeTolerance(),
                "MYR",
                "p1",
                "b1",
            )
        )
        self.assertIsNone(fee_diff)
        self.assertIsNone(tol_allowed)
        self.assertFalse(within)


class MatcherTests(unittest.TestCase):
    def test_normalize_text_removes_punctuation_and_case(self):
        result = matcher_module.normalize_text("INV-2026/001! A")
        self.assertEqual(result, "INV2026001A")

    def test_fuzzy_match_exact(self):
        self.assertTrue(matcher_module.fuzzy_match("hello", "hello"))

    def test_fuzzy_match_different(self):
        self.assertFalse(matcher_module.fuzzy_match("abc123", "xyz789"))

    def test_fuzzy_match_similar_above_cutoff(self):
        self.assertTrue(matcher_module.fuzzy_match("INV-001", "INV-001"))

    def test_check_reference_match_exact(self):
        exact, norm, fuzzy, in_desc, codes, facts = (
            matcher_module.check_reference_match("INV-2026-001", "INV-2026-001")
        )
        self.assertTrue(exact)
        self.assertIn("reference_exact_match", codes)

    def test_check_reference_match_normalized_in_bank_desc(self):
        exact, norm, fuzzy, in_desc, codes, facts = (
            matcher_module.check_reference_match(
                "INV-001", "Payment for INV-001 please"
            )
        )
        self.assertTrue(norm)
        self.assertIn("reference_normalized_match", codes)

    def test_check_reference_match_none_reference(self):
        exact, norm, fuzzy, in_desc, codes, facts = (
            matcher_module.check_reference_match(None, "bank description")
        )
        self.assertFalse(exact)
        self.assertFalse(norm)
        self.assertIn("reference_missing", codes)

    def test_check_reference_match_empty_description(self):
        exact, norm, fuzzy, in_desc, codes, facts = (
            matcher_module.check_reference_match("INV-001", "")
        )
        self.assertFalse(exact)
        self.assertFalse(norm)
        self.assertIn("reference_missing", codes)

    def test_check_sender_name_match_found(self):
        match, codes, facts = matcher_module.check_sender_name_match(
            "Alice Buyer", "Payment from Alice Buyer"
        )
        self.assertTrue(match)
        self.assertIn("sender_name_match", codes)

    def test_check_sender_name_match_not_found(self):
        match, codes, facts = matcher_module.check_sender_name_match(
            "Alice Buyer", "Bob Corp payment"
        )
        self.assertFalse(match)

    def test_check_sender_name_match_none_sender(self):
        match, codes, facts = matcher_module.check_sender_name_match(
            None, "some description"
        )
        self.assertFalse(match)

    def test_check_date_window_within_tolerance(self):
        diff, within, codes, facts = matcher_module.check_date_window(
            date(2026, 5, 20), date(2026, 5, 22), 3
        )
        self.assertEqual(diff, 2)
        self.assertTrue(within)
        self.assertIn("date_within_window", codes)

    def test_check_date_window_outside_tolerance(self):
        diff, within, codes, facts = matcher_module.check_date_window(
            date(2026, 5, 10), date(2026, 5, 22), 3
        )
        self.assertEqual(diff, 12)
        self.assertFalse(within)
        self.assertIn("date_outside_window", codes)

    def test_check_date_window_none_dates(self):
        diff, within, codes, facts = matcher_module.check_date_window(
            None, date(2026, 5, 22), 3
        )
        self.assertIsNone(diff)
        self.assertFalse(within)


class ConfidenceTests(unittest.TestCase):
    def test_calculate_confidence_all_factors(self):
        score = matcher_module.calculate_confidence(
            reference_match=True,
            amount_within_tolerance=True,
            date_within_tolerance=True,
            sender_name_match=True,
        )
        self.assertEqual(score, Decimal("1.0"))

    def test_calculate_confidence_three_factors(self):
        score = matcher_module.calculate_confidence(
            reference_match=True,
            amount_within_tolerance=True,
            date_within_tolerance=True,
            sender_name_match=False,
        )
        self.assertEqual(score, Decimal("0.90"))

    def test_calculate_confidence_reference_only(self):
        score = matcher_module.calculate_confidence(
            reference_match=True,
            amount_within_tolerance=False,
            date_within_tolerance=False,
            sender_name_match=False,
        )
        self.assertEqual(score, Decimal("0.40"))

    def test_calculate_confidence_caps_at_1_0(self):
        score = matcher_module.calculate_confidence(
            reference_match=True,
            amount_within_tolerance=True,
            date_within_tolerance=True,
            sender_name_match=True,
        )
        self.assertLessEqual(score, Decimal("1.0"))


class ClassificationTests(unittest.TestCase):
    def test_classify_matched(self):
        self.assertEqual(
            matcher_module.classify_score(Decimal("0.75")), "matched"
        )
        self.assertEqual(
            matcher_module.classify_score(Decimal("0.95")), "matched"
        )

    def test_classify_possible(self):
        self.assertEqual(
            matcher_module.classify_score(Decimal("0.45")), "possible"
        )
        self.assertEqual(
            matcher_module.classify_score(Decimal("0.60")), "possible"
        )

    def test_classify_unmatched(self):
        self.assertEqual(
            matcher_module.classify_score(Decimal("0.44")), "unmatched"
        )
        self.assertEqual(
            matcher_module.classify_score(Decimal("0.00")), "unmatched"
        )


class TieBreakTests(unittest.TestCase):
    def test_pick_best_candidate_highest_confidence(self):
        c1 = MatchCandidate(
            proof_id="p1", bank_row_id="b1", confidence=Decimal("0.8")
        )
        c2 = MatchCandidate(
            proof_id="p1", bank_row_id="b2", confidence=Decimal("0.9")
        )
        best = matcher_module.pick_best_candidate([c1, c2])
        self.assertEqual(best.bank_row_id, "b2")

    def test_pick_best_candidate_tie_confidence_smaller_fee(self):
        c1 = MatchCandidate(
            proof_id="p1",
            bank_row_id="b1",
            confidence=Decimal("0.8"),
            fee_difference=Decimal("50"),
        )
        c2 = MatchCandidate(
            proof_id="p1",
            bank_row_id="b2",
            confidence=Decimal("0.8"),
            fee_difference=Decimal("10"),
        )
        best = matcher_module.pick_best_candidate([c1, c2])
        self.assertEqual(best.bank_row_id, "b2")

    def test_pick_best_empty_list(self):
        self.assertIsNone(matcher_module.pick_best_candidate([]))

    def test_needs_possible_review_true(self):
        c1 = MatchCandidate(
            proof_id="p1", bank_row_id="b1", confidence=Decimal("0.80")
        )
        c2 = MatchCandidate(
            proof_id="p1", bank_row_id="b2", confidence=Decimal("0.78")
        )
        needs, codes, facts = matcher_module.needs_possible_review([c1, c2], c1)
        self.assertTrue(needs)
        self.assertIn("multiple_candidate_matches", codes)

    def test_needs_possible_review_false_when_far_apart(self):
        c1 = MatchCandidate(
            proof_id="p1", bank_row_id="b1", confidence=Decimal("0.95")
        )
        c2 = MatchCandidate(
            proof_id="p1", bank_row_id="b2", confidence=Decimal("0.30")
        )
        needs, codes, facts = matcher_module.needs_possible_review([c1, c2], c1)
        self.assertFalse(needs)


class ServiceToolTests(unittest.TestCase):
    def test_validate_inputs_passes_valid_request(self):
        request = AgentReconcileRequest(
            company_name="TestCo",
            payment_proofs=[
                PaymentProof(proof_id="p1", amount=Decimal("100"), currency="MYR")
            ],
            bank_rows=[
                BankRow(
                    bank_row_id="b1", amount_local=Decimal("100"), currency="MYR"
                )
            ],
        )
        from reconmate.reconciliation.service import tool_validate_inputs

        result = tool_validate_inputs(request)
        self.assertEqual(result.status, "success")

    def test_validate_inputs_fails_empty(self):
        request = AgentReconcileRequest(company_name="TestCo")
        from reconmate.reconciliation.service import tool_validate_inputs

        result = tool_validate_inputs(request)
        self.assertEqual(result.status, "error")
        self.assertIn("validation_error", result.reason_codes)

    def test_apply_fx_rates_handles_mixed(self):
        request = AgentReconcileRequest(
            company_name="TestCo",
            base_currency="MYR",
            payment_proofs=[
                PaymentProof(proof_id="p1", amount=Decimal("100"), currency="MYR"),
                PaymentProof(proof_id="p2", amount=Decimal("50"), currency="USD"),
            ],
            bank_rows=[
                BankRow(
                    bank_row_id="b1", amount_local=Decimal("100"), currency="MYR"
                )
            ],
            fx_rates=[FxRate(pair="USD_MYR", rate=Decimal("4.45"))],
        )
        from reconmate.reconciliation.service import tool_apply_fx_rates

        result = tool_apply_fx_rates(request)
        self.assertEqual(result.status, "success")
        conversions = result.output["conversion_results"]
        p1 = [c for c in conversions if c["proof_id"] == "p1"][0]
        p2 = [c for c in conversions if c["proof_id"] == "p2"][0]
        self.assertEqual(p1["fx_rate_source"], "default_1.0")
        self.assertEqual(p2["fx_rate_source"], "provided")
        self.assertEqual(p2["expected_amount_local"], "222.50")


if __name__ == "__main__":
    unittest.main()
