from __future__ import annotations

from decimal import Decimal
from typing import Optional

from .models import FxRate, PaymentProof


def parse_fx_pair(pair: str) -> tuple[str, str]:
    parts = pair.split("_")
    if len(parts) != 2:
        raise ValueError(f"Invalid FX pair format: '{pair}'. Expected 'SOURCE_TARGET' like 'USD_MYR'")
    return parts[0].upper(), parts[1].upper()


def build_fx_lookup(
    rates: list[FxRate],
    base_currency: str,
) -> dict[str, Decimal]:
    lookup: dict[str, Decimal] = {}
    base = base_currency.upper()

    for rate_entry in rates:
        source, target = parse_fx_pair(rate_entry.pair)
        if target == base:
            lookup[source] = rate_entry.rate

    return lookup


def apply_fx_rate(
    proof: PaymentProof,
    fx_lookup: dict[str, Decimal],
    base_currency: str,
) -> tuple[Optional[Decimal], Optional[Decimal], Optional[str], list[str], list[str]]:
    """
    Apply FX rate to a single payment proof.

    Returns:
        (expected_amount_local, fx_rate_used, fx_rate_source, reason_codes, reasoning_facts)
    """
    reason_codes: list[str] = []
    reasoning_facts: list[str] = []

    currency = proof.currency.upper()
    base = base_currency.upper()

    if currency == base:
        reasoning_facts.append(
            f"Payment currency '{currency}' equals base currency '{base_currency}'. FX rate is 1.0."
        )
        return proof.amount, Decimal("1.0"), "default_1.0", reason_codes, reasoning_facts

    if currency in fx_lookup:
        rate = fx_lookup[currency]
        expected = proof.amount * rate
        reasoning_facts.append(
            f"FX rate {proof.currency}_{base_currency}={str(rate)} applied to {proof.currency} {str(proof.amount):s}."
        )
        reasoning_facts.append(
            f"Expected local amount: {base_currency} {expected:.2f}"
        )
        return expected, rate, "provided", reason_codes, reasoning_facts

    reasoning_facts.append(
        f"Missing FX rate for pair '{proof.currency}_{base_currency}'. "
        f"Cannot convert {proof.currency} {str(proof.amount):s} to {base_currency}."
    )
    reason_codes.append("missing_fx_rate")
    return None, None, "missing", reason_codes, reasoning_facts
