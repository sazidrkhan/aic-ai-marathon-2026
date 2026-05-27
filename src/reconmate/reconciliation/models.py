from datetime import date
from decimal import Decimal
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


ToolStatus = Literal["success", "warning", "error"]


class PaymentProof(BaseModel):
    proof_id: str
    sender_name: Optional[str] = None
    amount: Decimal
    currency: str
    reference: Optional[str] = None
    payment_date: Optional[date] = None
    raw_description: Optional[str] = None


class BankRow(BaseModel):
    bank_row_id: str
    amount_local: Decimal
    currency: str
    settlement_date: Optional[date] = None
    transaction_date: Optional[date] = None
    description: Optional[str] = None

    def resolved_settlement_date(self) -> Optional[date]:
        if self.settlement_date is not None:
            return self.settlement_date
        return self.transaction_date


class FxRate(BaseModel):
    pair: str
    rate: Decimal
    rate_date: Optional[date] = Field(default=None, alias="date")


class FeeTolerance(BaseModel):
    percent: Decimal = Decimal("0.02")
    fixed: Decimal = Decimal("20")


class AgentReconcileRequest(BaseModel):
    run_id: Optional[str] = None
    company_name: str
    base_currency: str = "MYR"
    payment_proofs: list[PaymentProof] = Field(default_factory=list)
    bank_rows: list[BankRow] = Field(default_factory=list)
    fx_rates: list[FxRate] = Field(default_factory=list)
    fee_tolerance: FeeTolerance = Field(default_factory=FeeTolerance)
    date_tolerance_days: int = 3


class ToolResult(BaseModel):
    status: ToolStatus
    tool_name: str
    action: str
    observation: str
    key_output_summary: str
    output: Any = None
    reason_codes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AgentTraceItem(BaseModel):
    step: int
    tool: str
    action: str
    observation: str
    status: str
    key_output_summary: Optional[str] = None


class MatchCandidate(BaseModel):
    proof_id: str
    bank_row_id: str
    reference_exact_match: bool = False
    reference_normalized_match: bool = False
    reference_fuzzy_match: bool = False
    reference_found_in_description: bool = False
    sender_name_in_description: bool = False
    date_days_diff: Optional[int] = None
    date_within_tolerance: bool = False
    expected_amount_local: Optional[Decimal] = None
    actual_amount_local: Optional[Decimal] = None
    fee_difference: Optional[Decimal] = None
    tolerance_allowed: Optional[Decimal] = None
    amount_within_tolerance: bool = False
    confidence: Decimal = Field(default=Decimal("0.0"))
    reason_codes: list[str] = Field(default_factory=list)
    reasoning_facts: list[str] = Field(default_factory=list)
