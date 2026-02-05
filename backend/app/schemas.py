from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: Optional[str] = Field(default=None)
    customer_id: Optional[str] = None
    pin: Optional[str] = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatResponse(BaseModel):
    session_id: str
    messages: List[ChatMessage]
    route: str
