from __future__ import annotations

from decimal import Decimal
from typing import Optional

from .models import FeeTolerance


def calculate_tolerance_allowed(
    expected_amount: Decimal,
    tolerance_percent: Decimal,
    tolerance_fixed: Decimal,
) -> Decimal:
    percent_based = expected_amount * tolerance_percent
    return max(percent_based, tolerance_fixed)


def evaluate_fee_tolerance(
    expected_amount_local: Optional[Decimal],
    actual_amount_local: Optional[Decimal],
    tolerance: FeeTolerance,
    base_currency: str,
    proof_id: str,
    bank_row_id: str,
) -> tuple[Optional[Decimal], Optional[Decimal], bool, list[str], list[str]]:
    if expected_amount_local is None or actual_amount_local is None:
        return None, None, False, [], []

    fee_difference = abs(expected_amount_local - actual_amount_local)
    tolerance_allowed = calculate_tolerance_allowed(
        expected_amount_local,
        tolerance.percent,
        tolerance.fixed,
    )

    within_tolerance = fee_difference <= tolerance_allowed
    reason_codes: list[str] = []
    reasoning_facts: list[str] = []

    reasoning_facts.append(
        f"Fee difference: {base_currency} {fee_difference:.2f}; "
        f"tolerance allowed: {base_currency} {tolerance_allowed:.2f} "
        f"(max of {str(tolerance.percent)}% = {expected_amount_local * tolerance.percent:.2f}, "
        f"fixed {base_currency} {str(tolerance.fixed):s})."
    )

    if within_tolerance:
        reason_codes.append("amount_within_fee_tolerance")
        reasoning_facts.append(
            f"Fee difference {fee_difference:.2f} is within allowed tolerance {tolerance_allowed:.2f}."
        )
    else:
        reason_codes.append("amount_outside_fee_tolerance")
        reasoning_facts.append(
            f"Fee difference {fee_difference:.2f} exceeds allowed tolerance {tolerance_allowed:.2f}."
        )

    return fee_difference, tolerance_allowed, within_tolerance, reason_codes, reasoning_facts
