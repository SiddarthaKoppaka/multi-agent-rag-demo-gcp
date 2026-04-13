#!/bin/sh
# ──────────────────────────────────────────────────────────────────────────────
# Container entrypoint — starts the ADK Web UI server.
#
# Expected Cloud Run env vars (injected at deploy time):
#   PORT              — set automatically by Cloud Run (default 8080)
#   ALLOYDB_IP        — AlloyDB private IP (via VPC connector) or public IP
#   ALLOYDB_PASSWORD  — mounted from Secret Manager (alloydb-password:latest)
#   GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, GOOGLE_GENAI_USE_VERTEXAI
# ──────────────────────────────────────────────────────────────────────────────
set -e

SESSION_URI="postgresql+asyncpg://postgres:${ALLOYDB_PASSWORD}@${ALLOYDB_IP:-34.68.208.239}:5432/postgres"

exec adk web \
  --host 0.0.0.0 \
  --port "${PORT:-8080}" \
  --session_service_uri "${SESSION_URI}" \
  --artifact_service_uri "gs://${GCS_CORPUS_BUCKET:-finops-demo-42128-artifacts}" \
  --otel_to_cloud \
  /app
