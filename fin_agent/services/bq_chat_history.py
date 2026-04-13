"""BigQuery chat-history logger.

Appends one row per conversation turn to `finops_sessions.chat_history`.
The insert runs in a thread-pool executor so it never blocks the async
FastAPI handler.
"""

import asyncio
import logging
import time
from dataclasses import dataclass

from google.cloud import bigquery

from fin_agent.config import BQ_PROJECT, BQ_DATASET, BQ_CHAT_TABLE

logger = logging.getLogger(__name__)

_TABLE_REF = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_CHAT_TABLE}"


@dataclass
class TurnRecord:
    session_id: str
    user_id: str
    turn_number: int
    user_query: str
    agent_response: str
    agent_name: str
    latency_ms: int


class BigQueryChatLogger:
    """Async wrapper around the BigQuery streaming-insert API."""

    def __init__(self) -> None:
        self._client: bigquery.Client | None = None

    def _get_client(self) -> bigquery.Client:
        if self._client is None:
            self._client = bigquery.Client(project=BQ_PROJECT)
        return self._client

    def _insert_sync(self, record: TurnRecord) -> None:
        row = {
            "session_id": record.session_id,
            "user_id": record.user_id,
            "turn_number": record.turn_number,
            "user_query": record.user_query,
            "agent_response": record.agent_response,
            "agent_name": record.agent_name,
            "latency_ms": record.latency_ms,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        errors = self._get_client().insert_rows_json(_TABLE_REF, [row])
        if errors:
            logger.error("BigQuery insert errors: %s", errors)

    async def log_turn(self, record: TurnRecord) -> None:
        """Non-blocking: runs the BQ insert in the default thread-pool."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._insert_sync, record)


# Module-level singleton — imported by app.py
bq_logger = BigQueryChatLogger()
