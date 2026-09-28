"""Domain models and Pydantic schemas for blockchain integration and payment comparison."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BlockchainStatus(str, Enum):
    """On-chain contract status enum mapping Solidity enum FinancialContractV2.Status."""

    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    DELINQUENT = "DELINQUENT"

    @classmethod
    def from_solidity_uint(cls, value: int) -> "BlockchainStatus":
        """Map Solidity uint8 enum index (0..3) to backend enum."""
        mapping = {
            0: cls.CREATED,
            1: cls.ACTIVE,
            2: cls.COMPLETED,
            3: cls.DELINQUENT,
        }
        if value not in mapping:
            raise ValueError(f"Unknown Solidity status uint8 index '{value}'.")
        return mapping[value]


class PaymentComparisonStatus(str, Enum):
    """Reconciliation status enum for expected-vs-actual payment comparison."""

    MATCHED = "MATCHED"
    AMOUNT_VARIANCE = "AMOUNT_VARIANCE"
    DATE_VARIANCE = "DATE_VARIANCE"
    UNPAID = "UNPAID"
    UNEXPECTED = "UNEXPECTED"


class BlockchainContractState(BaseModel):
    """Structured domain model representing live on-chain FinancialContractV2 state."""

    contract_address: str = Field(..., description="EVM contract deployment address")
    lender: str = Field(..., description="Lender wallet address")
    borrower: str = Field(..., description="Borrower wallet address")
    principal: Decimal = Field(..., description="Principal amount in backend monetary units")
    interest_rate_bps: int = Field(..., description="Interest rate in basis points (e.g. 1000 = 10%)")
    maturity_date: datetime = Field(..., description="Contract maturity date (UTC datetime)")
    actus_hash: str = Field(..., description="64-character lowercase SHA-256 hash digest of actusHash")
    status: BlockchainStatus = Field(..., description="Mapped on-chain contract status")
    total_paid: Decimal = Field(..., description="Cumulative total paid amount in monetary units")
    chain_id: int = Field(..., description="MST blockchain network chain ID")

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class ActualPayment(BaseModel):
    """Model representing an actual PaymentRecorded event log read from the blockchain."""

    transaction_hash: str = Field(..., description="Blockchain transaction hash")
    block_number: int = Field(..., description="Block number containing the log")
    log_index: int = Field(default=0, description="Log index within the block")
    amount: Decimal = Field(..., description="Payment amount in monetary units")
    payment_date: datetime = Field(..., description="Payment timestamp from block/event (UTC datetime)")
    cumulative_total_paid: Decimal = Field(..., description="Total cumulative paid on-chain after this payment")

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class ContractLinkRecord(BaseModel):
    """Model representing the link between an off-chain FinancialContract and an on-chain deployment."""

    contract_id: str = Field(..., description="Internal backend FinancialContract ID")
    blockchain_contract_address: str = Field(..., description="Deployed EVM contract address")
    chain_id: int = Field(..., description="Blockchain network chain ID")
    network_name: str = Field(default="MST Testnet", description="Blockchain network name")
    linked_at: datetime = Field(..., description="UTC link creation timestamp")

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class HashVerificationResult(BaseModel):
    """Response model for comparing Phase 6 SHA-256 hash with on-chain actusHash."""

    contract_id: str = Field(..., description="Internal backend FinancialContract ID")
    blockchain_contract_address: str = Field(..., description="Deployed EVM contract address")
    backend_sha256_hash: str = Field(..., description="Off-chain Phase 6 SHA-256 hex string")
    onchain_bytes32_hash: str = Field(..., description="On-chain actusHash converted to SHA-256 hex string")
    hash_matches: bool = Field(..., description="True if off-chain SHA-256 matches on-chain bytes32")
    chain_id: int = Field(..., description="MST network chain ID")

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class PaymentComparisonItem(BaseModel):
    """Model representing comparison result for a single expected contractual payment line."""

    sequence: int = Field(..., description="Payment sequence index (1-based)")
    event_type: str = Field(..., description="ACTUS event type or combined type (e.g. PR_IP, PR, IP)")
    expected_date: str = Field(..., description="Expected payment ISO timestamp")
    expected_total_amount: Decimal = Field(..., description="Expected total payment monetary amount")
    expected_principal: Decimal = Field(..., description="Expected principal portion")
    expected_interest: Decimal = Field(..., description="Expected interest portion")
    actual_payment: Optional[ActualPayment] = Field(default=None, description="Matched actual payment log")
    amount_variance: Optional[Decimal] = Field(
        default=None, description="Actual amount minus expected total amount"
    )
    date_variance_days: Optional[int] = Field(
        default=None, description="Actual date minus expected date in days"
    )
    comparison_status: PaymentComparisonStatus = Field(..., description="Reconciliation status")

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class ExpectedVsActualComparison(BaseModel):
    """Overall report comparing expected ACTUS cash flows against actual on-chain payment events."""

    contract_id: str = Field(..., description="Internal backend FinancialContract ID")
    blockchain_contract_address: str = Field(..., description="Deployed EVM contract address")
    actus_contract_type: Optional[str] = Field(default=None, description="ACTUS contract type")
    total_expected_payments: int = Field(..., description="Count of expected payment events")
    total_actual_payments: int = Field(..., description="Count of actual on-chain payment events")
    total_expected_amount: Decimal = Field(..., description="Sum of expected payment amounts")
    total_actual_paid: Decimal = Field(..., description="Sum of actual payment amounts")
    matched_count: int = Field(..., description="Count of matched or variation payments")
    unpaid_count: int = Field(..., description="Count of unpaid expected payments")
    unexpected_count: int = Field(..., description="Count of unexpected actual payments")
    comparison_items: List[PaymentComparisonItem] = Field(..., description="Reconciled payment line items")
    unexpected_payments: List[ActualPayment] = Field(
        default_factory=list, description="Surplus actual payments beyond expected schedule"
    )
    generated_at: datetime = Field(..., description="UTC timestamp of report generation")

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
