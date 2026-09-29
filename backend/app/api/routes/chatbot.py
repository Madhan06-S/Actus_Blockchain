"""API routes for AI Chatbot / Financial Assistant."""

from fastapi import APIRouter, status

from app.intelligence.chatbot.schemas import ChatRequest, ChatResponse
from app.intelligence.orchestration.service import financial_intelligence_service

router = APIRouter(prefix="/api/v1", tags=["financial-assistant"])


@router.post(
    "/contracts/{contract_id}/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask AI Financial Assistant questions about contract",
)
def chat_with_contract(
    contract_id: str, payload: ChatRequest
) -> ChatResponse:
    """Answer natural language question about current contract using structured backend context."""
    return financial_intelligence_service.answer_chat(contract_id, payload)
