from __future__ import annotations

import os
import uuid
from typing import Dict, List

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .agent import run_agent
from .schemas import ChatMessage, ChatRequest, ChatResponse

load_dotenv()

app = FastAPI(title="Bank ABC Voice Agent", version="0.1.0")

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"] ,
)

_sessions: Dict[str, List[ChatMessage]] = {}


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    session_id = payload.session_id or str(uuid.uuid4())
    history = _sessions.setdefault(session_id, [])

    history.append(ChatMessage(role="user", content=payload.message))

    result = run_agent(payload.message, payload.customer_id, payload.pin)
    history.append(ChatMessage(role="assistant", content=result["response"]))

    return ChatResponse(session_id=session_id, messages=history, route=result["route"])
