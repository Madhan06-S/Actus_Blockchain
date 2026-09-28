"""Domain model definitions for financial risk status evaluation."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.blockchain.models import BlockchainStatus


class FinancialStatusEnum(str, Enum):
    """Overall off-chain financial status classification enum."""

    ON_TRACK = "ON_TRACK"
    DEVIATION_DETECTED = "DEVIATION_DETECTED"
    OVERDUE = "OVERDUE"
    COMPLETED = "COMPLETED"


class ContractRiskStatus(BaseModel):
    """Domain model representing calculated financial risk status and payment reconciliation metrics."""

    contract_id: str = Field(..., description="Unique source FinancialContract ID")
    blockchain_contract_address: Optional[str] = Field(
        default=None, description="Linked EVM smart contract address"
    )
    overall_status: FinancialStatusEnum = Field(
        ..., description="Overall calculated financial reconciliation status"
    )
    blockchain_status: Optional[BlockchainStatus] = Field(
        default=None, description="Live status of on-chain Solidity smart contract"
    )
    hash_integrity_matched: bool = Field(
        ..., description="True if Phase 6 off-chain SHA-256 matches on-chain actusHash"
    )
    total_expected_amount: Decimal = Field(
        ..., description="Total monetary amount expected according to ACTUS schedule"
    )
    total_actual_paid: Decimal = Field(
        ..., description="Total cumulative monetary amount paid on-chain"
    )
    net_amount_variance: Decimal = Field(
        ..., description="Total actual paid minus total expected amount"
    )
    total_expected_payments: int = Field(
        ..., description="Total number of expected payment schedule events"
    )
    matched_payment_count: int = Field(
        ..., description="Count of matched or variation payments"
    )
    unpaid_payment_count: int = Field(
        ..., description="Count of future unpaid scheduled payments"
    )
    overdue_payment_count: int = Field(
        ..., description="Count of past due unpaid scheduled payments"
    )
    unexpected_payment_count: int = Field(
        ..., description="Count of surplus actual payments beyond expected schedule"
    )
    evaluation_date: datetime = Field(
        ..., description="UTC evaluation timestamp used for status classification"
    )
    status_reasons: List[str] = Field(
        ..., description="List of factual human-readable explanations supporting status"
    )

    model_config = ConfigDict(
        use_enum_values=True,
        arbitrary_types_allowed=True,
    )
