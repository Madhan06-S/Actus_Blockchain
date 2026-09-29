"""Pydantic schemas for AI Chatbot / Financial Assistant."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for asking the AI Financial Assistant a question."""
    message: str = Field(..., description="User's natural language question about the contract")


class ChatResponse(BaseModel):
    """Response schema from the AI Financial Assistant."""
    contract_id: str
    answer: str = Field(..., description="Answer to the user's question based on contract context")
    sources: List[str] = Field(default_factory=list, description="Data sources utilized (e.g. reconciliation, actus_schedule, risk)")
    available: bool = Field(True, description="Whether LLM engine or fallback responder handled request")
    message: Optional[str] = Field(None, description="Diagnostic status message")
