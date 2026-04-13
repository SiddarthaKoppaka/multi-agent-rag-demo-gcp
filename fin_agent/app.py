"""FastAPI server — HTTP endpoints for the FinOps multi-agent system.

Session backend (ADK `DatabaseSessionService`):
  - Prod : AlloyDB PostgreSQL  (postgresql+asyncpg://…)
  - Local: SQLite              (sqlite+aiosqlite://…)

Chat history (BigQuery streaming insert):
  - Every turn is appended to `finops_sessions.chat_history` asynchronously
    so it never blocks the response path.

Tracing:
  - Vertex AI / Cloud Trace via ADK's built-in GCP telemetry setup.
  - Enabled when GOOGLE_CLOUD_PROJECT is set (all envs).
"""

import logging
import time
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types

from fin_agent.agent import root_agent
from fin_agent.config import APP_NAME, GOOGLE_CLOUD_PROJECT, SESSION_DB_URL
from fin_agent.services.bq_chat_history import TurnRecord, bq_logger

logger = logging.getLogger(__name__)

# ── Vertex AI Tracing (Cloud Trace + Cloud Logging via OTEL) ──
def _setup_tracing() -> None:
    """Wire ADK's built-in GCP telemetry: Cloud Trace + Cloud Logging."""
    try:
        import google.auth
        from google.adk.telemetry.google_cloud import get_gcp_exporters, get_gcp_resource
        from google.adk.telemetry.setup import maybe_set_otel_providers

        credentials, project_id = google.auth.default()
        gcp_hooks = get_gcp_exporters(
            enable_cloud_tracing=True,
            enable_cloud_metrics=False,   # skip metrics (unstable at shutdown)
            enable_cloud_logging=True,
            google_auth=(credentials, project_id),
        )
        otel_resource = get_gcp_resource(project_id)
        maybe_set_otel_providers(
            otel_hooks_to_setup=[gcp_hooks],
            otel_resource=otel_resource,
        )
        logger.info("Cloud Trace + Cloud Logging telemetry enabled (project=%s)", project_id)
    except Exception as exc:
        logger.warning("Tracing setup skipped: %s", exc)


if GOOGLE_CLOUD_PROJECT:
    _setup_tracing()

app = FastAPI(title="FinOps Intelligence Assistant", version="1.0.0")

# ── Session backend ────────────────────────────────────────────
# AlloyDB (PostgreSQL) in prod; SQLite for local dev — both are natively
# supported by ADK's DatabaseSessionService (SQLAlchemy async under the hood).
session_service = DatabaseSessionService(db_url=SESSION_DB_URL)

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


# ── Request / Response models ──────────────────────────────────
class QueryRequest(BaseModel):
    query: str
    session_id: str | None = None
    user_id: str = "default_user"


class QueryResponse(BaseModel):
    response: str
    session_id: str


# ── Endpoints ──────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "healthy", "agent": root_agent.name}


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    session_id = request.session_id or str(uuid.uuid4())
    t0 = time.monotonic()

    # Ensure a session exists
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=request.user_id, session_id=session_id
    )
    if session is None:
        session = await session_service.create_session(
            app_name=APP_NAME, user_id=request.user_id, session_id=session_id
        )

    # turn_number = number of existing events before this new turn
    turn_number = len(session.events) if session.events else 0

    user_content = types.Content(
        role="user", parts=[types.Part.from_text(text=request.query)]
    )

    final_response = ""
    async for event in runner.run_async(
        user_id=request.user_id,
        session_id=session_id,
        new_message=user_content,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_response = event.content.parts[0].text

    latency_ms = int((time.monotonic() - t0) * 1000)

    # ── BigQuery chat history (fire-and-forget, non-blocking) ──
    record = TurnRecord(
        session_id=session_id,
        user_id=request.user_id,
        turn_number=turn_number,
        user_query=request.query,
        agent_response=final_response,
        agent_name=root_agent.name,
        latency_ms=latency_ms,
    )
    await bq_logger.log_turn(record)

    return QueryResponse(response=final_response, session_id=session_id)


@app.post("/ingest")
async def ingest():
    from fin_agent.data.ingestion import run_ingestion

    try:
        run_ingestion()
        return {"status": "success", "message": "Ingestion complete"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
