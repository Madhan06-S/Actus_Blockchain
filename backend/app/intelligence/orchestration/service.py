"""Financial Intelligence Orchestration Service unifying all AI engines."""

from typing import Optional

from app.intelligence.chatbot.schemas import ChatRequest, ChatResponse
from app.intelligence.chatbot.service import chatbot_service
from app.intelligence.liquidity.schemas import LiquidityForecastRequest, LiquidityForecastResponse
from app.intelligence.liquidity.service import liquidity_service
from app.intelligence.negotiation.schemas import NegotiationRequest, NegotiationResponse
from app.intelligence.negotiation.service import negotiation_service
from app.intelligence.risk.schemas import RiskPredictionResponse
from app.intelligence.risk.service import risk_prediction_service
from app.intelligence.stress.schemas import StressTestRequest, StressTestResponse
from app.intelligence.stress.service import stress_test_service


class FinancialIntelligenceService:
    """Unified facade for risk, liquidity, stress testing, negotiation, and chatbot engines."""

    def run_risk_analysis(self, contract_id: str) -> RiskPredictionResponse:
        return risk_prediction_service.evaluate_contract_risk(contract_id)

    def forecast_liquidity(
        self, request: Optional[LiquidityForecastRequest] = None
    ) -> LiquidityForecastResponse:
        return liquidity_service.forecast_portfolio_liquidity(request)

    def run_stress_test(
        self, contract_id: str, request: StressTestRequest
    ) -> StressTestResponse:
        return stress_test_service.run_stress_test(contract_id, request)

    def negotiate_contract(
        self, contract_id: str, request: Optional[NegotiationRequest] = None
    ) -> NegotiationResponse:
        return negotiation_service.negotiate_contract(contract_id, request)

    def answer_chat(self, contract_id: str, request: ChatRequest) -> ChatResponse:
        return chatbot_service.answer_question(contract_id, request)


financial_intelligence_service = FinancialIntelligenceService()
