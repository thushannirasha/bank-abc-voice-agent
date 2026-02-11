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

## Setup Instructions
1. Prereqs:
	- Python 3.10+ (3.11 recommended)
	- Node.js 18+
	- A LangSmith API key and GenAI API key
2. Clone and open the repo.
3. Backend setup (see [backend](backend)):
	- `cd backend`
	- `pip install -r requirements.txt`
	- `cp .env.example .env` and add keys
	- `uvicorn app.main:app --reload`
4. Frontend setup (see [frontend](frontend)):
	- `cd frontend`
	- `npm install`
	- `cp .env.example .env` if needed
	- `npm run dev`
5. Verify:
	- Backend health: `GET /health`
	- UI opens at the Vite dev URL

## Backend Setup
1. Go to the backend directory from the project root.
2. Create a virtual environment and install dependencies:
	- `pip install -r requirements.txt`
3. Copy [.env.example](.env.example) to `.env` and add your LangSmith + GenAI API keys.
4. Run the API:
	- `uvicorn app.main:app --reload`

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
1. Go to the frontend directory from the project root.
2. Install dependencies:
	- `npm install`
3. Copy [.env.example](.env.example) to `.env` if needed.
4. Run the UI:
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

## Vercel Deployment (Backend on Vercel)
This repo includes a Vercel Python serverless entrypoint at [api/index.py](api/index.py) and a root [vercel.json](vercel.json).

Steps:
1. Push the repo to GitHub.
2. In Vercel, import the repo.
3. Set these Environment Variables in the Vercel project:
	- `LANGCHAIN_TRACING_V2=true`
	- `LANGCHAIN_API_KEY=...`
	- `LANGCHAIN_PROJECT=bank-abc-voice-agent`
	- `ALLOWED_ORIGINS=https://bank-abc-voice-agent-1x9q.vercel.app`
	- `GENAI_API_KEY=...`
4. Deploy. Your API base URL will be the Vercel project URL.

Then set `VITE_API_BASE_URL` in the frontend Vercel project to that API base URL.

## Notes / Trade-offs
- Routing uses Gemini structured output with a keyword fallback; no supervised intent model.
- Account data and tools are mocked (`_FAKE_CUSTOMERS`, balances, transactions, block card).
- Session history is stored in-memory in the API process; no persistence or multi-instance sync.
- Identity verification is PIN-only and not tied to real auth or step-up verification.
- Voice is browser-based speech-to-text and speech synthesis; no telephony or streaming audio.
- Observability is limited to LangSmith traces; no metrics, alerts, or log aggregation.