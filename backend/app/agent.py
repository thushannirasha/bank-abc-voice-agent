from __future__ import annotations

import logging
import os
from enum import Enum
from typing import Optional, TypedDict
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langsmith import traceable
from pydantic import BaseModel, Field

from .tools import block_card, get_account_balance, get_recent_transactions, verify_identity

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

load_dotenv()


class AgentState(TypedDict):
    message: str
    customer_id: Optional[str]
    pin: Optional[str]
    verified: bool
    route: str
    response: str


class AgentResult(TypedDict):
    response: str
    route: str


def _normalize(text: str) -> str:
    return text.lower().strip()


class RouteLabel(str, Enum):
    CARD_ATM = "card_atm"
    ACCOUNT_SERVICING = "account_servicing"
    ACCOUNT_OPENING = "account_opening"
    DIGITAL_SUPPORT = "digital_support"
    TRANSFERS = "transfers"
    ACCOUNT_CLOSURE = "account_closure"
    CLARIFY = "clarify"
    FALLBACK = "fallback"


class RouteDecision(BaseModel):
    route: RouteLabel = Field(..., description="Best matching route for the user request")
    reason: str = Field(..., description="Short reason for the route")


_LLM = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))


@traceable(name="route_intent")
def route_intent(state: AgentState) -> AgentState:
    text = _normalize(state["message"])
    route = RouteLabel.FALLBACK
    system_prompt = (
        "You are an intent router for a bank voice agent. "
        "Choose exactly one route label for the user message. "
        "If the user says 'account details' without specifying which details, choose 'clarify'. "
        "If the user says their card is fine but the app login is broken, choose 'digital_support'. "
        "Valid routes: card_atm, account_servicing, account_opening, digital_support, "
        "transfers, account_closure, clarify, fallback."
    )

    try:
        decision = _LLM.with_structured_output(RouteDecision).invoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ]
        )
        route = decision.route
        logger.info("Routing via LLM: %s (%s)", route, decision.reason)
    except Exception as exc:
        logger.exception("LLM routing failed, falling back to keyword routing: %s", exc)
        if "card" in text or "atm" in text:
            route = RouteLabel.CARD_ATM
        elif "account" in text or "balance" in text or "statement" in text:
            route = RouteLabel.ACCOUNT_SERVICING
        elif "open" in text or "onboarding" in text:
            route = RouteLabel.ACCOUNT_OPENING
        elif "login" in text or "otp" in text or "app" in text:
            route = RouteLabel.DIGITAL_SUPPORT
        elif "transfer" in text or "bill" in text or "payment" in text:
            route = RouteLabel.TRANSFERS
        elif "close" in text or "deactivate" in text or "retention" in text:
            route = RouteLabel.ACCOUNT_CLOSURE

    logger.info("Routing message '%s' to route '%s'", state["message"], route)
    state["route"] = route.value if isinstance(route, RouteLabel) else route
    return state


def _ensure_verification(state: AgentState) -> Optional[str]:
    if state.get("verified"):
        return None

    customer_id = state.get("customer_id")
    pin = state.get("pin")
    if not customer_id or not pin:
        return "Before I access account data, please provide your customer ID and PIN."

    if verify_identity(customer_id, pin):
        state["verified"] = True
        return None

    return "I couldn't verify your identity with that PIN. Please try again."


@traceable(name="handle_card_atm")
def handle_card_atm(state: AgentState) -> AgentState:
    text = _normalize(state["message"])
    if any(k in text for k in ["lost", "stolen", "block"]):
        card_id = "card_unknown"
        if state.get("customer_id"):
            card_id = f"card_for_{state['customer_id']}"
        verification_message = _ensure_verification(state)
        if verification_message:
            state["response"] = verification_message
            return state
        response = block_card(card_id, reason="reported lost/stolen")
        state["response"] = (
            f"{response} I can also order a replacement. Would you like a new card sent to your address on file?"
        )
        return state

    if "declined" in text:
        state["response"] = (
            "I can help with declined payments. Are you traveling, or was this a specific merchant? "
            "You can also try a chip insert instead of tap. If it keeps happening, I can block and replace the card."
        )
        return state

    if "cash" in text or "atm" in text:
        state["response"] = (
            "Sorry about the ATM issue. Can you share the ATM location and approximate time? "
            "I'll open a dispute and keep you updated."
        )
        return state

    state["response"] = (
        "I can help with card or ATM issues like lost cards, cash not dispensed, or declined payments."
    )
    return state


@traceable(name="handle_account_servicing")
def handle_account_servicing(state: AgentState) -> AgentState:
    verification_message = _ensure_verification(state)
    if verification_message:
        state["response"] = verification_message
        return state

    text = _normalize(state["message"])

    if "balance" in text:
        balance = get_account_balance(state["customer_id"])
        state["response"] = (
            f"Your current balance is {balance['balance']} {balance['currency']}. "
            "Do you need recent transactions as well?"
        )
        return state

    if "statement" in text or "transaction" in text:
        transactions = get_recent_transactions(state["customer_id"], 3)
        summary = "; ".join(
            f"{t['date']} {t['merchant']} {t['amount']} {t['currency']}" for t in transactions
        )
        state["response"] = f"Here are your last 3 transactions: {summary}."
        return state

    if "address" in text or "profile" in text:
        state["response"] = (
            "I can update your profile details. Please share the new address or the fields you'd like to change."
        )
        return state

    state["response"] = (
        "Account servicing can include balance checks, statements, or profile updates. How can I help?"
    )
    return state


@traceable(name="handle_clarify")
def handle_clarify(state: AgentState) -> AgentState:
    state["response"] = (
        "When you say account details, do you want your balance, recent transactions, or a profile update?"
    )
    return state


@traceable(name="handle_stub")
def handle_stub(state: AgentState) -> AgentState:
    route = state["route"]
    text = _normalize(state["message"])
    if route == "account_opening" and any(k in text for k in ["next week", "schedule", "appointment", "callback"]):
        state["response"] = (
            "Great, I can set up an appointment or a callback. Which day and time next week works best, "
            "and what is the best phone number to reach you?"
        )
        return state
    if route == "transfers" and any(k in text for k in ["sent money", "didn't go through", "did not go through"]):
        state["response"] = (
            "Was this a bank transfer or a bill payment? If it's a transfer, was it to a person or a beneficiary?"
        )
        return state
    responses = {
        "account_opening": "I can help with onboarding and eligibility. Would you like to schedule an appointment?",
        "digital_support": "I can help with login, OTP, or app issues. What error are you seeing?",
        "transfers": "I can help with transfers or bill payments. Is the transfer pending or failed?",
        "account_closure": "I'm sorry to hear that. Can you share the reason for closure so I can try to help?",
        "fallback": "I can help with card issues, account servicing, app support, transfers, or account closure.",
    }
    state["response"] = responses.get(route, responses["fallback"])
    return state


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("route_intent", route_intent)
    graph.add_node("card_atm", handle_card_atm)
    graph.add_node("account_servicing", handle_account_servicing)
    graph.add_node("clarify", handle_clarify)
    graph.add_node("stub", handle_stub)

    graph.set_entry_point("route_intent")

    def _select_route(state: AgentState) -> str:
        if state["route"] in {"card_atm"}:
            return "card_atm"
        if state["route"] in {"account_servicing"}:
            return "account_servicing"
        if state["route"] in {"clarify"}:
            return "clarify"
        return "stub"

    graph.add_conditional_edges("route_intent", _select_route)
    graph.add_edge("card_atm", END)
    graph.add_edge("account_servicing", END)
    graph.add_edge("clarify", END)
    graph.add_edge("stub", END)

    return graph.compile()


_graph = build_graph()


@traceable(name="run_agent")
def run_agent(message: str, customer_id: Optional[str], pin: Optional[str]) -> AgentResult:
    state: AgentState = {
        "message": message,
        "customer_id": customer_id,
        "pin": pin,
        "verified": False,
        "route": "fallback",
        "response": "",
    }
    final_state = _graph.invoke(state)
    return {"response": final_state["response"], "route": final_state["route"]}
