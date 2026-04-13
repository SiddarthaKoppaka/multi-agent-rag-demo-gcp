"""Central configuration — model registry, GCP settings, paths."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── GCP Settings ────────────────────────────────────────────────
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "finagent-demo")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
GCS_CORPUS_BUCKET = os.getenv("GCS_CORPUS_BUCKET", "finops-demo-42128")

# ── AlloyDB Settings ─────────────────────────────────────────────
# Private IP set via ALLOYDB_IP env var in Cloud Run (from Secret Manager)
# For local dev, set to empty string to fall back to SQLite
ALLOYDB_IP = os.getenv("ALLOYDB_IP", "")
ALLOYDB_PASSWORD = os.getenv("ALLOYDB_PASSWORD", "")
ALLOYDB_DB = os.getenv("ALLOYDB_DB", "postgres")
ALLOYDB_USER = os.getenv("ALLOYDB_USER", "postgres")
ALLOYDB_PORT = int(os.getenv("ALLOYDB_PORT", "5432"))

# Use AlloyDB when ALLOYDB_IP is set, otherwise fall back to SQLite
USE_ALLOYDB = bool(ALLOYDB_IP)

# ADK session DB URL:
#   Prod  → AlloyDB (PostgreSQL-compatible, supported by DatabaseSessionService)
#   Local → SQLite  (zero-config for development)
if USE_ALLOYDB:
    from urllib.parse import quote_plus
    _pw = quote_plus(ALLOYDB_PASSWORD)
    SESSION_DB_URL = (
        f"postgresql+asyncpg://{ALLOYDB_USER}:{_pw}"
        f"@{ALLOYDB_IP}:{ALLOYDB_PORT}/{ALLOYDB_DB}"
    )
else:
    SESSION_DB_URL = "sqlite+aiosqlite:///./finops_sessions.db"

# ── BigQuery Chat-History Settings ──────────────────────────────
# All conversation turns are appended to this BQ table for analytics / audit.
BQ_PROJECT = os.getenv("BQ_PROJECT", GOOGLE_CLOUD_PROJECT)
BQ_DATASET = os.getenv("BQ_DATASET", "finops_sessions")
BQ_CHAT_TABLE = os.getenv("BQ_CHAT_TABLE", "chat_history")

# ── Model Registry ──────────────────────────────────────────────
MODEL_REGISTRY = {
    "router": "gemini-2.5-flash",
    "rag": "gemini-2.5-flash",
    "tool_agent": "gemini-2.5-flash",
    "analyst": "gemini-2.5-flash",
    "embedding": "text-embedding-005",
}

# ── Paths ───────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent          # Multi Agent RAG/
DATA_DIR = BASE_DIR / "data"
CORPUS_DIR = DATA_DIR / "corpus"
DB_PATH = BASE_DIR / "fin_agent" / "finops.db"             # SQLite for local dev
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ── App Constants ───────────────────────────────────────────────
APP_NAME = "finops_assistant"
EMBEDDING_DIMENSION = 768
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
TOP_K = 5
