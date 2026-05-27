from __future__ import annotations

import difflib
import re
from datetime import date
from decimal import Decimal
from typing import Optional

from .models import BankRow, FeeTolerance, MatchCandidate, PaymentProof


_NON_ALNUM_PATTERN = re.compile(r"[^a-zA-Z0-9\s]")


def normalize_text(text: str) -> str:
    text = text.upper()
    text = _NON_ALNUM_PATTERN.sub(" ", text)
    text = re.sub(r"\s+", "", text)
    return text.strip()


def fuzzy_match(a: str, b: str, cutoff: float = 0.85) -> bool:
    if not a or not b:
        return False
    a_norm = normalize_text(a)
    b_norm = normalize_text(b)
    if a_norm == b_norm:
        return True
    return difflib.SequenceMatcher(None, a_norm, b_norm).ratio() >= cutoff


# ---------------------------------------------------------------------------
# Reference matching
# ---------------------------------------------------------------------------

ReferenceMatchResult = tuple[
    bool,   # exact_match
    bool,   # normalized_match
    bool,   # fuzzy_match
    bool,   # found_in_description
    list[str],  # reason_codes
    list[str],  # reasoning_facts
]


def check_reference_match(
    proof_reference: Optional[str],
    bank_description: Optional[str],
    proof_sender: Optional[str] = None,
) -> ReferenceMatchResult:
    reason_codes: list[str] = []
    reasoning_facts: list[str] = []

    if not proof_reference:
        reason_codes.append("reference_missing")
        reasoning_facts.append("Payment proof has no reference number.")
        return False, False, False, False, reason_codes, reasoning_facts

    if not bank_description:
        reason_codes.append("reference_missing")
        reasoning_facts.append(
            f"Reference '{proof_reference}' could not be matched (bank description is empty)."
        )
        return False, False, False, False, reason_codes, reasoning_facts

    proof_norm = normalize_text(proof_reference)
    bank_norm = normalize_text(bank_description)

    exact_match = proof_norm == bank_norm
    normalized_match = proof_norm in bank_norm
    found_in_description = proof_reference.upper() in bank_description.upper()

    fuzzy = fuzzy_match(proof_reference, bank_description)

    if exact_match:
        reason_codes.append("reference_exact_match")
        reasoning_facts.append(
            f"Reference '{proof_reference}' matches bank row exactly."
        )
    elif normalized_match:
        reason_codes.append("reference_normalized_match")
        reasoning_facts.append(
            f"Reference '{proof_reference}' found in normalized bank description."
        )
    elif fuzzy:
        reason_codes.append("reference_fuzzy_match")
        reasoning_facts.append(
            f"Reference '{proof_reference}' fuzzy-matched bank description (similarity >= 85%)."
        )
    elif found_in_description:
        reason_codes.append("reference_normalized_match")
        reasoning_facts.append(
            f"Reference '{proof_reference}' appears in bank description."
        )
    else:
        reason_codes.append("reference_missing")
        reasoning_facts.append(
            f"Reference '{proof_reference}' could not be matched to bank description."
        )

    return exact_match, normalized_match, fuzzy, found_in_description, reason_codes, reasoning_facts


# ---------------------------------------------------------------------------
# Sender name matching
# ---------------------------------------------------------------------------

SenderMatchResult = tuple[bool, list[str], list[str]]


def check_sender_name_match(
    sender_name: Optional[str],
    bank_description: Optional[str],
) -> SenderMatchResult:
    reason_codes: list[str] = []
    reasoning_facts: list[str] = []

    if not sender_name or not bank_description:
        return False, reason_codes, reasoning_facts

    parts = sender_name.upper().split()
    bank_upper = bank_description.upper()
    matched_parts = [p for p in parts if len(p) > 2 and p in bank_upper]

    if matched_parts:
        reason_codes.append("sender_name_match")
        reasoning_facts.append(
            f"Sender name '{sender_name}' appears in bank description."
        )
        return True, reason_codes, reasoning_facts

    sender_norm = normalize_text(sender_name)
    bank_norm = normalize_text(bank_description)
    if sender_norm and sender_norm in bank_norm:
        reason_codes.append("sender_name_match")
        reasoning_facts.append(
            f"Normalized sender name '{sender_name}' found in bank description."
        )
        return True, reason_codes, reasoning_facts

    return False, reason_codes, reasoning_facts


# ---------------------------------------------------------------------------
# Date matching
# ---------------------------------------------------------------------------

DateMatchResult = tuple[Optional[int], bool, list[str], list[str]]


def check_date_window(
    payment_date: Optional[date],
    settlement_date: Optional[date],
    tolerance_days: int,
) -> DateMatchResult:
    reason_codes: list[str] = []
    reasoning_facts: list[str] = []

    if payment_date is None or settlement_date is None:
        return None, False, reason_codes, reasoning_facts

    days_diff = abs((settlement_date - payment_date).days)
    within_tolerance = days_diff <= tolerance_days

    if within_tolerance:
        reason_codes.append("date_within_window")
        reasoning_facts.append(
            f"Payment date {payment_date} and settlement date {settlement_date} "
            f"are {days_diff} day(s) apart (within {tolerance_days} day tolerance)."
        )
    else:
        reason_codes.append("date_outside_window")
        reasoning_facts.append(
            f"Payment date {payment_date} and settlement date {settlement_date} "
            f"are {days_diff} day(s) apart (exceeds {tolerance_days} day tolerance)."
        )

    return days_diff, within_tolerance, reason_codes, reasoning_facts


# ---------------------------------------------------------------------------
# Confidence scoring
# ---------------------------------------------------------------------------

def calculate_confidence(
    reference_match: bool,
    amount_within_tolerance: bool,
    date_within_tolerance: bool,
    sender_name_match: bool,
) -> Decimal:
    confidence = Decimal("0.0")
    if reference_match:
        confidence += Decimal("0.40")
    if amount_within_tolerance:
        confidence += Decimal("0.30")
    if date_within_tolerance:
        confidence += Decimal("0.20")
    if sender_name_match:
        confidence += Decimal("0.10")
    if confidence > Decimal("1.0"):
        confidence = Decimal("1.0")
    return confidence


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

ClassificationLabel = str  # "matched" | "possible" | "unmatched"


def classify_score(confidence: Decimal) -> ClassificationLabel:
    if confidence >= Decimal("0.75"):
        return "matched"
    elif confidence >= Decimal("0.45"):
        return "possible"
    else:
        return "unmatched"


# ---------------------------------------------------------------------------
# Tie-breaking
# ---------------------------------------------------------------------------

def pick_best_candidate(
    candidates: list[MatchCandidate],
) -> Optional[MatchCandidate]:
    if not candidates:
        return None

    def sort_key(c: MatchCandidate) -> tuple:
        fd = c.fee_difference if c.fee_difference is not None else Decimal("Infinity")
        dd = c.date_days_diff if c.date_days_diff is not None else 999999
        return (-c.confidence, fd, dd, c.bank_row_id)

    candidates_sorted = sorted(candidates, key=sort_key)
    return candidates_sorted[0]


def needs_possible_review(
    candidates: list[MatchCandidate],
    best: MatchCandidate,
    threshold: Decimal = Decimal("0.15"),
) -> tuple[bool, list[str], list[str]]:
    if len(candidates) < 2:
        return False, [], []

    reason_codes: list[str] = []
    reasoning_facts: list[str] = []

    for c in candidates:
        if c.bank_row_id != best.bank_row_id:
            diff = abs(c.confidence - best.confidence)
            if diff <= threshold:
                reason_codes.append("multiple_candidate_matches")
                reasoning_facts.append(
                    f"Multiple close candidates for proof '{c.proof_id}': "
                    f"best '{best.bank_row_id}' (confidence {best.confidence}), "
                    f"also '{c.bank_row_id}' (confidence {c.confidence}). "
                    f"Human review recommended."
                )
                return True, reason_codes, reasoning_facts

    return False, reason_codes, reasoning_facts
