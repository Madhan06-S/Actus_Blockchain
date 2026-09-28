"""API routes for Financial Contract management."""

from fastapi import APIRouter, HTTPException, status

from app.schemas.contract import (
    FinancialContractCreate,
    FinancialContractListResponse,
    FinancialContractResponse,
)
from app.services.contract_service import contract_service

router = APIRouter(prefix="/api/v1/contracts", tags=["Contracts"])


@router.post(
    "",
    response_model=FinancialContractResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and validate a new financial contract",
)
def create_contract(payload: FinancialContractCreate) -> FinancialContractResponse:
    """Create, validate, normalize, and store a financial contract."""
    return contract_service.create_contract(payload)


@router.get(
    "/{contract_id}",
    response_model=FinancialContractResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a stored financial contract by ID",
)
def get_contract(contract_id: str) -> FinancialContractResponse:
    """Retrieve a stored financial contract by its unique contract ID."""
    contract = contract_service.get_contract_by_id(contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Financial contract with ID '{contract_id}' not found",
        )
    return contract


@router.get(
    "",
    response_model=FinancialContractListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all stored financial contracts",
)
def list_contracts() -> FinancialContractListResponse:
    """List all financial contracts currently stored in memory."""
    return contract_service.list_contracts()
