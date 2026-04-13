#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
# FinOps Multi-Agent RAG — GCP Infrastructure Setup
# ══════════════════════════════════════════════════════════════════
# Run sections individually, NOT as a single script.
# Each section is idempotent (safe to re-run).
#
# Prerequisites:
#   - gcloud CLI authenticated (gcloud auth login)
#   - Project: finagent-demo
#   - Region:  us-central1
# ══════════════════════════════════════════════════════════════════

set -euo pipefail

export PROJECT_ID="finagent-demo"
export REGION="us-central1"
export ZONE="us-central1-a"

gcloud config set project "$PROJECT_ID"
gcloud config set compute/region "$REGION"
gcloud config set compute/zone "$ZONE"

# ╔═══════════════════════════════════════════════════════════════╗
# ║  STEP 1 — Enable Required APIs                               ║
# ╚═══════════════════════════════════════════════════════════════╝

gcloud services enable \
  aiplatform.googleapis.com \
  alloydb.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  compute.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  run.googleapis.com \
  secretmanager.googleapis.com \
  servicenetworking.googleapis.com \
  storage.googleapis.com \
  vpcaccess.googleapis.com

echo "✓ APIs enabled"

# ╔═══════════════════════════════════════════════════════════════╗
# ║  STEP 2 — GCS Buckets                                        ║
# ╚═══════════════════════════════════════════════════════════════╝

# 2a. Corpus bucket (already exists: finops-demo-42128)
# Upload source documents + CSVs to GCS
gsutil -m cp data/*.md data/*.csv gs://finops-demo-42128/raw/

# 2b. Artifacts bucket (vector store JSON, model artifacts)
gcloud storage buckets create gs://finops-demo-42128-artifacts \
  --default-storage-class=STANDARD \
  --location="$REGION" \
  --uniform-bucket-level-access \
  --public-access-prevention 2>/dev/null || true

echo "✓ Buckets configured"

# ╔═══════════════════════════════════════════════════════════════╗
# ║  STEP 3 — Networking (VPC Peering + Serverless Connector)    ║
# ╚═══════════════════════════════════════════════════════════════╝
# AlloyDB (Private Services Access mode) requires VPC peering with
# servicenetworking.googleapis.com BEFORE any instance is created.
# This step must fully complete before Step 4.

# 3a. Reserve an IP range for Google-managed services
# (using 172.24.0.0/16 — avoids conflict with the default 10.x VPC)
gcloud compute addresses create peering-range-for-alloydb \
  --global \
  --purpose=VPC_PEERING \
  --addresses=172.24.0.0 \
  --prefix-length=16 \
  --network=default 2>/dev/null || echo "  (IP range peering-range-for-alloydb already exists)"

# 3b. Establish the VPC peering — WAIT for it to complete (not async)
# This is the step that was missing before; it must finish before AlloyDB instance creation.
echo "  Establishing VPC peering with servicenetworking (this is synchronous)..."
gcloud services vpc-peerings connect \
  --service=servicenetworking.googleapis.com \
  --ranges=peering-range-for-alloydb \
  --network=default \
  --project="$PROJECT_ID" 2>&1 || echo "  (VPC peering already active)"

# 3c. Confirm peering is ACTIVE before proceeding
PEERING_STATE=$(gcloud compute networks peerings list \
  --network=default \
  --filter="name:servicenetworking-googleapis-com" \
  --format="value(stateDetails)" 2>/dev/null || echo "")
if [[ "$PEERING_STATE" != *"Connected"* ]]; then
  echo "ERROR: VPC peering is not in Connected state. Do not proceed to Step 4."
  echo "Current state: $PEERING_STATE"
  echo "Run: gcloud compute networks peerings list --network=default"
  exit 1
fi
echo "  VPC peering state: $PEERING_STATE"

# 3d. Serverless VPC Connector (for Cloud Run → AlloyDB private IP)
# If a previous connector exists in ERROR state, delete and recreate it.
if gcloud compute networks vpc-access connectors describe finops-connector \
     --region="$REGION" --format="value(state)" 2>/dev/null | grep -q "ERROR"; then
  echo "  Deleting broken VPC connector (ERROR state)..."
  gcloud compute networks vpc-access connectors delete finops-connector \
    --region="$REGION" --quiet 2>/dev/null || true
fi

gcloud compute networks vpc-access connectors create finops-connector \
  --region="$REGION" \
  --network=default \
  --range="10.9.0.0/28" \
  --min-instances=2 \
  --max-instances=3 \
  --machine-type=e2-micro 2>/dev/null || echo "  (VPC connector already exists)"

echo "✓ Networking configured"

# ╔═══════════════════════════════════════════════════════════════╗
# ║  STEP 4 — AlloyDB Cluster + Instance                         ║
# ╚═══════════════════════════════════════════════════════════════╝
# PREREQUISITE: Step 3 VPC peering must be ACTIVE before running this.
# AlloyDB = PostgreSQL 17, pgvector support, used for session storage,
# structured data, and agent memory.

ALLOYDB_CLUSTER="finops-cluster"
ALLOYDB_INSTANCE="finops-primary"

# 4a. Generate password and store in Secret Manager first
# (so it survives if you re-run the script)
if gcloud secrets describe alloydb-password --quiet 2>/dev/null; then
  ALLOYDB_PASSWORD=$(gcloud secrets versions access latest --secret=alloydb-password)
  echo "  Using existing password from Secret Manager"
else
  ALLOYDB_PASSWORD="$(openssl rand -base64 24)"
  echo -n "$ALLOYDB_PASSWORD" | gcloud secrets create alloydb-password \
    --data-file=- \
    --replication-policy=automatic
  echo "  Created new password in Secret Manager"
fi

# 4b. Create cluster (with --network=default for Private Services Access)
# NOTE: cluster creation is fast (~30s). Instance creation is slow (~10 min).
gcloud alloydb clusters create "$ALLOYDB_CLUSTER" \
  --region="$REGION" \
  --password="$ALLOYDB_PASSWORD" \
  --network=default \
  --quiet 2>/dev/null || echo "  (Cluster $ALLOYDB_CLUSTER already exists)"

# 4c. Create the primary instance
# --database-version not needed at instance level (inherited from cluster)
gcloud alloydb instances create "$ALLOYDB_INSTANCE" \
  --cluster="$ALLOYDB_CLUSTER" \
  --region="$REGION" \
  --instance-type=PRIMARY \
  --cpu-count=2 \
  --quiet 2>/dev/null || echo "  (Instance $ALLOYDB_INSTANCE already exists)"

# 4d. Wait for the instance to reach READY state
echo "  Waiting for AlloyDB instance to be READY..."
for i in $(seq 1 30); do
  STATE=$(gcloud alloydb instances describe "$ALLOYDB_INSTANCE" \
    --cluster="$ALLOYDB_CLUSTER" \
    --region="$REGION" \
    --format="value(state)" 2>/dev/null || echo "UNKNOWN")
  echo "  Attempt $i/30: state=$STATE"
  [[ "$STATE" == "READY" ]] && break
  sleep 30
done

# 4e. Get the private IP
ALLOYDB_IP=$(gcloud alloydb instances describe "$ALLOYDB_INSTANCE" \
  --cluster="$ALLOYDB_CLUSTER" \
  --region="$REGION" \
  --format="value(ipAddress)")

# Update Secret Manager with the IP
echo -n "$ALLOYDB_IP" | gcloud secrets create alloydb-ip \
  --data-file=- \
  --replication-policy=automatic 2>/dev/null || \
echo -n "$ALLOYDB_IP" | gcloud secrets versions add alloydb-ip \
  --data-file=-

echo "✓ AlloyDB ready at $ALLOYDB_IP"
echo "  Password and IP stored in Secret Manager (alloydb-password / alloydb-ip)"

# ╔═══════════════════════════════════════════════════════════════╗
# ║  STEP 5 — AlloyDB Schema Setup                               ║
# ╚═══════════════════════════════════════════════════════════════╝
# Connect via AlloyDB Auth Proxy or a Compute Engine jump box.
#
# Option A — Auth Proxy (local machine):
#   gcloud alloydb instances describe finops-primary \
#     --cluster=finops-cluster --region=us-central1 --format="value(ipAddress)"
#   # Then use psql:
#   PGPASSWORD="$ALLOYDB_PASSWORD" psql -h "$ALLOYDB_IP" -U postgres -d postgres
#
# Option B — Cloud Shell / Compute Engine in same VPC:
#   psql -h "$ALLOYDB_IP" -U postgres

cat <<'EOSQL'
-- Run this SQL against the AlloyDB instance:

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ── Structured Data Tables ──────────────────────────────────────

CREATE TABLE IF NOT EXISTS billing_data (
    id SERIAL PRIMARY KEY,
    billing_account_id TEXT,
    invoice_month TEXT,
    usage_start_time TEXT,
    usage_end_time TEXT,
    service_id TEXT,
    service_description TEXT,
    sku_id TEXT,
    sku_description TEXT,
    project_id TEXT,
    project_name TEXT,
    cost_type TEXT,
    cost NUMERIC(12,2),
    credits_amount NUMERIC(12,2),
    net_cost NUMERIC(12,2),
    currency TEXT DEFAULT 'USD',
    usage_amount NUMERIC(12,4),
    usage_unit TEXT,
    resource_name TEXT,
    location_region TEXT,
    label_team TEXT,
    label_environment TEXT,
    label_cost_center TEXT,
    label_project_id TEXT,
    label_owner_email TEXT,
    label_created_date TEXT,
    tags_environment TEXT
);

CREATE TABLE IF NOT EXISTS idle_resources (
    id SERIAL PRIMARY KEY,
    resource_name TEXT,
    resource_type TEXT,
    project_id TEXT,
    team TEXT,
    environment TEXT,
    region TEXT,
    monthly_cost_usd NUMERIC(10,2),
    last_active_date DATE,
    days_idle INTEGER,
    cpu_avg_pct_14d NUMERIC(5,2),
    connection_count_14d INTEGER,
    invocation_count_21d INTEGER,
    label_owner_email TEXT,
    label_created_date DATE,
    label_team TEXT,
    label_environment TEXT,
    idle_status TEXT,
    flagged_date DATE,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS budget_allocation (
    id SERIAL PRIMARY KEY,
    team TEXT UNIQUE NOT NULL,
    cost_center TEXT,
    monthly_budget_usd NUMERIC(10,2),
    q1_2026_budget_usd NUMERIC(10,2),
    alert_threshold_pct NUMERIC(5,2),
    hard_cap_usd NUMERIC(10,2),
    environment_split_prod_pct NUMERIC(5,2),
    environment_split_staging_pct NUMERIC(5,2),
    environment_split_dev_pct NUMERIC(5,2),
    primary_services TEXT,
    budget_owner_email TEXT,
    approved_date DATE,
    chargeback_model TEXT
);

-- ── Vector Store Table (pgvector) ───────────────────────────────

CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    source_file TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(768),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_file, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_chunks_embedding
    ON document_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 10);

-- ── ADK Session Storage ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS adk_sessions (
    id TEXT PRIMARY KEY,
    app_name TEXT NOT NULL,
    user_id TEXT NOT NULL,
    state JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_app_user
    ON adk_sessions(app_name, user_id);

-- ── Agent Memory ────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agent_memory (
    id SERIAL PRIMARY KEY,
    session_id TEXT REFERENCES adk_sessions(id),
    agent_name TEXT NOT NULL,
    memory_key TEXT NOT NULL,
    memory_value JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

EOSQL

echo "✓ Schema SQL printed above — run it against AlloyDB"

# ╔═══════════════════════════════════════════════════════════════╗
# ║  STEP 6 — Vertex AI Vector Search Index                      ║
# ╚═══════════════════════════════════════════════════════════════╝
# Creates a managed vector search index for production RAG.
# The local JSON file is for dev; this replaces it in prod.

# 6a. Prepare embeddings in JSONL format for Vertex AI
python3 -c "
import json
store = json.load(open('data/vector_store.json'))
with open('/tmp/embeddings.jsonl', 'w') as f:
    for chunk in store:
        record = {
            'id': f\"{chunk['source']}_{chunk['chunk_index']}\",
            'embedding': chunk['embedding'],
        }
        f.write(json.dumps(record) + '\n')
print(f'Wrote {len(store)} records to /tmp/embeddings.jsonl')
"

# 6b. Upload to GCS
gsutil cp /tmp/embeddings.jsonl gs://finops-demo-42128-artifacts/embeddings/embeddings.jsonl

# 6c. Create the Vector Search Index
gcloud ai indexes create \
  --display-name="finops-rag-index" \
  --description="FinOps policy/contract/incident doc embeddings" \
  --metadata-schema-uri="gs://google-cloud-aiplatform/schema/matchingengine/metadata/nearest_neighbor_search_1.0.0.yaml" \
  --metadata='{
    "contentsDeltaUri": "gs://finops-demo-42128-artifacts/embeddings/",
    "config": {
      "dimensions": 768,
      "approximateNeighborsCount": 10,
      "distanceMeasureType": "COSINE_DISTANCE",
      "algorithmConfig": {
        "treeAhConfig": {
          "leafNodeEmbeddingCount": 500,
          "leafNodesToSearchPercent": 10
        }
      }
    }
  }' \
  --region="$REGION"

# ⚠️  Index creation takes 20-40 minutes. Note the INDEX_ID from output.
# Check status:
#   gcloud ai indexes list --region=us-central1

echo "✓ Vector Search index creation started (check status with: gcloud ai indexes list --region=$REGION)"

# 6d. Create an Index Endpoint (after index is ready)
# gcloud ai index-endpoints create \
#   --display-name="finops-rag-endpoint" \
#   --region="$REGION" \
#   --public-endpoint-enabled
#
# 6e. Deploy the index to the endpoint
# gcloud ai index-endpoints deploy-index ENDPOINT_ID \
#   --deployed-index-id="finops_deployed" \
#   --index=INDEX_ID \
#   --display-name="finops-rag-deployed" \
#   --region="$REGION"

# ╔═══════════════════════════════════════════════════════════════╗
# ║  STEP 7 — Artifact Registry + Container Build                ║
# ╚═══════════════════════════════════════════════════════════════╝

AR_REPO="finops-agents"

# 7a. Create Docker repository
gcloud artifacts repositories create "$AR_REPO" \
  --repository-format=docker \
  --location="$REGION" \
  --description="FinOps multi-agent containers" 2>/dev/null || echo "  (Repo already exists)"

# 7b. Configure Docker auth
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# 7c. Build and push — Main Agent
docker build -t "${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/fin-agent:latest" \
  -f Dockerfile .
docker push "${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/fin-agent:latest"

# 7d. Build and push — Analyst Agent
docker build -t "${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/analyst-agent:latest" \
  -f Dockerfile.analyst .
docker push "${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/analyst-agent:latest"

echo "✓ Container images pushed to Artifact Registry"

# ╔═══════════════════════════════════════════════════════════════╗
# ║  STEP 8 — Cloud Run Deployment                               ║
# ╚═══════════════════════════════════════════════════════════════╝

# 8a. Create a service account for the agents
gcloud iam service-accounts create finops-agent-sa \
  --display-name="FinOps Agent Service Account" 2>/dev/null || true

SA_EMAIL="finops-agent-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant required roles
for ROLE in \
  roles/aiplatform.user \
  roles/alloydb.client \
  roles/logging.logWriter \
  roles/monitoring.metricWriter \
  roles/secretmanager.secretAccessor \
  roles/storage.objectViewer; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="$ROLE" --quiet
done

# 8b. Deploy Analyst Agent (must be up first, fin-agent depends on its URL)
gcloud run deploy analyst-agent \
  --image="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/analyst-agent:latest" \
  --region="$REGION" \
  --service-account="$SA_EMAIL" \
  --port=8080 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=3 \
  --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION}" \
  --no-allow-unauthenticated

ANALYST_URL=$(gcloud run services describe analyst-agent \
  --region="$REGION" --format="value(status.url)")

echo "✓ Analyst Agent deployed at $ANALYST_URL"

# 8c. Deploy Main FinOps Agent — runs 'adk web' (built-in ADK chat UI)
#
# The container's start.sh entrypoint assembles:
#   adk web --host 0.0.0.0 --port $PORT \
#           --session_service_uri postgresql+asyncpg://... \
#           --artifact_service_uri gs://... \
#           --otel_to_cloud /app
#
# AlloyDB is reached via its public IP (34.68.208.239).
# VPC connector is not required — Cloud Run uses internet egress.
# The password is injected from Secret Manager at runtime.
gcloud run deploy fin-agent \
  --image="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/fin-agent:latest" \
  --region="$REGION" \
  --service-account="$SA_EMAIL" \
  --clear-vpc-connector \
  --port=8080 \
  --memory=2Gi \
  --cpu=2 \
  --min-instances=1 \
  --max-instances=5 \
  --set-env-vars="\
GOOGLE_GENAI_USE_VERTEXAI=TRUE,\
GOOGLE_CLOUD_PROJECT=${PROJECT_ID},\
GOOGLE_CLOUD_LOCATION=${REGION},\
GCS_CORPUS_BUCKET=finops-demo-42128,\
ALLOYDB_IP=34.68.208.239,\
ANALYST_AGENT_URL=${ANALYST_URL}" \
  --set-secrets="ALLOYDB_PASSWORD=alloydb-password:latest" \
  --allow-unauthenticated

FIN_AGENT_URL=$(gcloud run services describe fin-agent \
  --region="$REGION" --format="value(status.url)")

echo "✓ FinOps Agent (ADK Web UI) deployed at $FIN_AGENT_URL"

# ╔═══════════════════════════════════════════════════════════════╗
# ║  STEP 9 — Cloud Logging (Log Router + Sink)                  ║
# ╚═══════════════════════════════════════════════════════════════╝
# Cloud Run automatically sends stdout/stderr to Cloud Logging.
# Create a custom log sink for agent-specific structured logs.

# 9a. Create a dedicated log bucket (90-day retention)
gcloud logging buckets create finops-agent-logs \
  --location="$REGION" \
  --retention-days=90 \
  --description="FinOps agent structured logs" 2>/dev/null || true

# 9b. Create a log sink that routes agent logs to the bucket
gcloud logging sinks create finops-agent-sink \
  "logging.googleapis.com/projects/${PROJECT_ID}/locations/${REGION}/buckets/finops-agent-logs" \
  --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name=("fin-agent" OR "analyst-agent")' \
  --description="Route FinOps agent logs to dedicated bucket" 2>/dev/null || true

# 9c. Create a log-based metric for agent errors
gcloud logging metrics create finops-agent-errors \
  --description="Count of ERROR-level logs from FinOps agents" \
  --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name=("fin-agent" OR "analyst-agent") AND severity>=ERROR' 2>/dev/null || true

# 9d. Create alert policy (email on >5 errors in 5 min)
cat > /tmp/alert-policy.json << 'ALERTEOF'
{
  "displayName": "FinOps Agent Error Rate",
  "conditions": [{
    "displayName": "Error rate > 5/5min",
    "conditionThreshold": {
      "filter": "metric.type=\"logging.googleapis.com/user/finops-agent-errors\"",
      "comparison": "COMPARISON_GT",
      "thresholdValue": 5,
      "duration": "300s",
      "aggregations": [{
        "alignmentPeriod": "300s",
        "perSeriesAligner": "ALIGN_RATE"
      }]
    }
  }],
  "combiner": "OR",
  "notificationChannels": []
}
ALERTEOF

gcloud alpha monitoring policies create --policy-from-file=/tmp/alert-policy.json 2>/dev/null || true

echo "✓ Cloud Logging configured"

# ╔═══════════════════════════════════════════════════════════════╗
# ║  STEP 10 — Data Ingestion into AlloyDB                       ║
# ╚═══════════════════════════════════════════════════════════════╝
# Run from a machine with VPC access (Compute Engine or Cloud Shell).

cat <<'EOPYTHON'
# ingest_to_alloydb.py — Run this from within the VPC
# pip install psycopg2-binary google-cloud-aiplatform

import csv
import json
import psycopg2
import vertexai
from vertexai.language_models import TextEmbeddingModel

ALLOYDB_IP = "REPLACE_WITH_ALLOYDB_IP"
ALLOYDB_PASSWORD = "REPLACE_WITH_PASSWORD"

conn = psycopg2.connect(
    host=ALLOYDB_IP, port=5432, dbname="postgres",
    user="postgres", password=ALLOYDB_PASSWORD
)

# 1. Load CSV data
csv_files = {
    "billing_data": "data/gcp_billing_export_jan2026.csv",
    "idle_resources": "data/idle_resources_jan2026.csv",
    "budget_allocation": "data/q1_2026_team_budgets.csv",
}

for table, path in csv_files.items():
    with open(path) as f:
        reader = csv.reader(f)
        cols = next(reader)
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {table}")
        for row in reader:
            # Pad/merge as needed
            n = len(cols)
            if len(row) > n:
                row = row[:n-1] + [",".join(row[n-1:])]
            elif len(row) < n:
                row += [""] * (n - len(row))
            placeholders = ",".join(["%s"] * n)
            cur.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})", row)
        conn.commit()
        print(f"  Loaded {table}")

# 2. Load vector embeddings
store = json.load(open("data/vector_store.json"))
cur = conn.cursor()
cur.execute("DELETE FROM document_chunks")
for chunk in store:
    cur.execute(
        "INSERT INTO document_chunks (source_file, chunk_index, chunk_text, embedding) "
        "VALUES (%s, %s, %s, %s) ON CONFLICT (source_file, chunk_index) DO UPDATE "
        "SET chunk_text=EXCLUDED.chunk_text, embedding=EXCLUDED.embedding",
        (chunk["source"], chunk["chunk_index"], chunk["text"], str(chunk["embedding"]))
    )
conn.commit()
print(f"  Loaded {len(store)} chunks into document_chunks")
conn.close()
EOPYTHON

echo "✓ Ingestion script printed above — run from within VPC"

# ╔═══════════════════════════════════════════════════════════════╗
# ║  STEP 11 — Verification                                      ║
# ╚═══════════════════════════════════════════════════════════════╝

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  DEPLOYMENT SUMMARY"
echo "═══════════════════════════════════════════════════════════"
echo "  Project:          $PROJECT_ID"
echo "  Region:           $REGION"
echo "  GCS Bucket:       gs://finops-demo-42128"
echo "  AlloyDB IP:       $ALLOYDB_IP"
echo "  Analyst Agent:    $ANALYST_URL"
echo "  FinOps Agent:     $FIN_AGENT_URL"
echo ""
echo "  Test endpoints:"
echo "    curl ${FIN_AGENT_URL}/health"
echo "    curl -X POST ${FIN_AGENT_URL}/query \\"
echo "      -H 'Content-Type: application/json' \\"
echo "      -d '{\"query\": \"Which teams exceeded budget?\"}'"
echo "═══════════════════════════════════════════════════════════"
