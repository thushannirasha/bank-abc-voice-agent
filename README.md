# bank-abc-voice-agent

Full-stack POC for the "Bank ABC" voice agent using FastAPI, LangGraph, LangSmith tracing, and React (Vite).

## Features
- Routing across 6 required flows.
- Deep logic + tool calls for Card & ATM Issues and Account Servicing.
- Identity verification guardrail enforced before account data access.
- LangSmith tracing via `LANGCHAIN_TRACING_V2`.

## Tech Stack
- Backend: FastAPI + LangGraph
- Observability: LangSmith
- Frontend: React + Vite

## Project Structure
- Backend: [backend](backend)
- Frontend: [frontend](frontend)

## Backend Setup
1. Create a virtual environment and install dependencies:
	- `pip install -r backend/requirements.txt`
2. Copy [backend/.env.example](backend/.env.example) to `backend/.env` and add your LangSmith API key.
3. Run the API:
	- `uvicorn app.main:app --reload --app-dir backend`

API endpoints:
- `GET /health`
- `POST /chat`

Sample request body:
```json
{
  "message": "What is my balance?",
  "customer_id": "cust_1001",
  "pin": "1234"
}
```

## Frontend Setup
1. Install dependencies:
	- `npm install`
2. Copy [frontend/.env.example](frontend/.env.example) to `frontend/.env` if needed.
3. Run the UI:
	- `npm run dev`

## Test Credentials
- `cust_1001` / `1234`
- `cust_2002` / `4321`

## Demo Scenarios
- Lost card: "I lost my card" (Card & ATM Issues)
- Balance check: "What's my balance?" (Account Servicing)
- App login issue: "I can't login" (Digital App Support)

## LangSmith Trace Evidence
Enable tracing by setting `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY` in your backend `.env`.
Run a scenario (lost card or balance check) and capture the trace URL or screenshot in LangSmith.

## Notes / Trade-offs
- This POC uses deterministic routing (keyword-based) to keep the graph lightweight.
- Voice input is simulated via text in the UI for faster iteration.