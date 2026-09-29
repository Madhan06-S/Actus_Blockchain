"""API endpoints for MST Blockchain state inspection, contract linking, hash verification, and payment reconciliation."""

from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from app.blockchain.exceptions import BlockchainError, ContractNotLinkedError
from app.blockchain.models import (
    ActualPayment,
    BlockchainContractState,
    ContractLinkRecord,
    ExpectedVsActualComparison,
    HashVerificationResult,
)
from app.core.config import settings
from app.services.blockchain_service import blockchain_service

router = APIRouter(tags=["Blockchain Integration"])


class ContractLinkRequest(BaseModel):
    """Request schema for linking a FinancialContract ID to a deployed EVM contract address."""

    contract_address: str = Field(..., description="Deployed EVM contract address (0x...)")
    network_name: Optional[str] = Field(default="MST Testnet", description="Optional network name")


class BlockchainHealthResponse(BaseModel):
    """Response schema for blockchain health check endpoint."""

    status: str = Field(..., description="Connection status indicator")
    chain_id: Optional[int] = Field(default=None, description="Connected network chain ID")
    rpc_url: str = Field(..., description="RPC endpoint URL (without credentials)")
    message: Optional[str] = Field(default=None, description="Additional status message or error detail")


@router.get(
    "/api/v1/blockchain/health",
    response_model=BlockchainHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Check MST RPC endpoint connectivity and chain ID",
)
def check_blockchain_health() -> BlockchainHealthResponse:
    """Query MST RPC health, verify connection, and check configured chain ID."""
    try:
        connected, chain_id = blockchain_service.client.check_connection()
        return BlockchainHealthResponse(
            status="connected",
            chain_id=chain_id,
            rpc_url=settings.MST_RPC_URL,
            message="MST RPC connection active.",
        )
    except BlockchainError as err:
        return BlockchainHealthResponse(
            status="error",
            chain_id=None,
            rpc_url=settings.MST_RPC_URL,
            message=err.message,
        )
    except Exception as exc:
        return BlockchainHealthResponse(
            status="error",
            chain_id=None,
            rpc_url=settings.MST_RPC_URL,
            message=f"RPC connection error: {str(exc)}",
        )


@router.post(
    "/api/v1/contracts/{contract_id}/blockchain/link",
    response_model=ContractLinkRecord,
    status_code=status.HTTP_200_OK,
    summary="Link a backend FinancialContract ID to a deployed EVM contract address",
)
def link_contract_to_blockchain(
    contract_id: str, request: ContractLinkRequest
) -> ContractLinkRecord:
    """Link an internal FinancialContract ID to a deployed FinancialContractV2 address."""
    return blockchain_service.link_contract(
        contract_id=contract_id,
        address=request.contract_address,
        network_name=request.network_name or "MST Testnet",
    )


@router.get(
    "/api/v1/contracts/{contract_id}/blockchain",
    response_model=ContractLinkRecord,
    status_code=status.HTTP_200_OK,
    summary="Retrieve stored blockchain link record for a FinancialContract ID",
)
def get_contract_blockchain_link(contract_id: str) -> ContractLinkRecord:
    """Retrieve the registered blockchain address link record for a contract ID."""
    try:
        return blockchain_service.get_link(contract_id)
    except ContractNotLinkedError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=err.message,
        ) from err


@router.get(
    "/api/v1/blockchain/contracts/{address}",
    response_model=BlockchainContractState,
    status_code=status.HTTP_200_OK,
    summary="Read live FinancialContractV2 state by contract address",
)
def get_onchain_contract_state(address: str) -> BlockchainContractState:
    """Read live state attributes (lender, borrower, principal, status, actusHash) from blockchain."""
    try:
        return blockchain_service.get_onchain_state(address)
    except BlockchainError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if "INVALID" in err.code else status.HTTP_404_NOT_FOUND,
            detail=err.message,
        ) from err


@router.get(
    "/api/v1/blockchain/contracts/{address}/payments",
    response_model=List[ActualPayment],
    status_code=status.HTTP_200_OK,
    summary="Read PaymentRecorded event logs for a contract address",
)
def get_onchain_payment_events(address: str) -> List[ActualPayment]:
    """Retrieve all PaymentRecorded event logs emitted by the contract address on MST Blockchain."""
    try:
        return blockchain_service.get_payment_events(address)
    except BlockchainError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "NOT_FOUND" in err.code else status.HTTP_400_BAD_REQUEST,
            detail=err.message,
        ) from err


@router.get(
    "/api/v1/contracts/{contract_id}/blockchain/hash-verification",
    response_model=HashVerificationResult,
    status_code=status.HTTP_200_OK,
    summary="Compare Phase 6 off-chain SHA-256 hash with on-chain actusHash",
)
def verify_onchain_actus_hash(contract_id: str) -> HashVerificationResult:
    """Compare off-chain Phase 6 SHA-256 hash against live on-chain bytes32 actusHash."""
    try:
        return blockchain_service.verify_onchain_hash(contract_id)
    except ContractNotLinkedError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=err.message,
        ) from err
    except BlockchainError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err.message,
        ) from err


@router.get(
    "/api/v1/contracts/{contract_id}/blockchain/compare",
    response_model=ExpectedVsActualComparison,
    status_code=status.HTTP_200_OK,
    summary="Reconcile expected ACTUS cash flows against actual on-chain payment events",
)
def compare_expected_vs_actual_payments(contract_id: str) -> ExpectedVsActualComparison:
    """Perform expected vs actual payment reconciliation for a linked FinancialContract."""
    try:
        return blockchain_service.compare_expected_vs_actual(contract_id)
    except ContractNotLinkedError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=err.message,
        ) from err
    except BlockchainError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err.message,
        ) from err


class RecordPaymentRequest(BaseModel):
    amount: float = Field(default=4614.49, description="Payment amount in INR")
    contract_address: Optional[str] = Field(default=None, description="Optional target contract address")


@router.post(
    "/api/v1/blockchain/pay",
    status_code=status.HTTP_200_OK,
    summary="Record payment on MST Blockchain testnet",
)
def record_blockchain_payment(payload: Optional[RecordPaymentRequest] = None):
    """Execute live payment transaction on MST Blockchain."""
    amt = Decimal(str(payload.amount if payload else 4614.49))
    addr = payload.contract_address if payload else None
    try:
        return blockchain_service.client.record_payment(contract_address=addr, amount_inr=amt)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment execution failed: {str(exc)}",
        )

