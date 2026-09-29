"""API routes for AI Risk Prediction, Liquidity Engine, Stress Testing, and Negotiation Agent."""

from typing import Optional
from fastapi import APIRouter, HTTPException, status

from app.intelligence.liquidity.schemas import LiquidityForecastRequest, LiquidityForecastResponse
from app.intelligence.negotiation.schemas import NegotiationRequest, NegotiationResponse
from app.intelligence.orchestration.service import financial_intelligence_service
from app.intelligence.risk.schemas import RiskPredictionResponse
from app.intelligence.stress.schemas import StressTestRequest, StressTestResponse

router = APIRouter(prefix="/api/v1", tags=["financial-intelligence"])


@router.get(
    "/contracts/{contract_id}/risk",
    response_model=RiskPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate contract AI risk prediction",
)
def get_contract_risk(contract_id: str) -> RiskPredictionResponse:
    """Evaluate contract default probability, risk category, expected loss, and model features."""
    return financial_intelligence_service.run_risk_analysis(contract_id)


@router.post(
    "/liquidity/forecast",
    response_model=LiquidityForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Forecast portfolio liquidity inflows vs bank outflows",
)
def forecast_liquidity(
    payload: Optional[LiquidityForecastRequest] = None,
) -> LiquidityForecastResponse:
    """Calculate portfolio yearly expected cash inflows against configured bank obligation outflows."""
    return financial_intelligence_service.forecast_liquidity(payload)


@router.post(
    "/contracts/{contract_id}/stress-test",
    response_model=StressTestResponse,
    status_code=status.HTTP_200_OK,
    summary="Run what-if scenario interest rate stress test",
)
def run_stress_test(
    contract_id: str, payload: StressTestRequest
) -> StressTestResponse:
    """Simulate interest rate shock on contract cash flows and calculate risk impact."""
    return financial_intelligence_service.run_stress_test(contract_id, payload)


@router.post(
    "/contracts/{contract_id}/negotiation",
    response_model=NegotiationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate proposed risk-mitigating contract adjustments",
)
def negotiate_contract(
    contract_id: str, payload: Optional[NegotiationRequest] = None
) -> NegotiationResponse:
    """Propose structured contract term adjustments for human review."""
    return financial_intelligence_service.negotiate_contract(contract_id, payload)
