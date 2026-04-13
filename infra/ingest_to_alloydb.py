"""Load CSV data and vector embeddings into AlloyDB.

Run this from a machine with VPC access to the AlloyDB private IP
(Cloud Shell, Compute Engine in same VPC, or via AlloyDB Auth Proxy).

Usage:
    ALLOYDB_IP=<ip> ALLOYDB_PASSWORD=<pw> python infra/ingest_to_alloydb.py
"""

import csv
import json
import os
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_batch

# ── Config from environment ──────────────────────────────────────
ALLOYDB_IP = os.environ.get("ALLOYDB_IP") or sys.exit("ERROR: ALLOYDB_IP not set")
ALLOYDB_PASSWORD = os.environ.get("ALLOYDB_PASSWORD") or sys.exit("ERROR: ALLOYDB_PASSWORD not set")
ALLOYDB_USER = os.environ.get("ALLOYDB_USER", "postgres")
ALLOYDB_DB = os.environ.get("ALLOYDB_DB", "postgres")
ALLOYDB_PORT = int(os.environ.get("ALLOYDB_PORT", "5432"))

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DSN = {
    "host": ALLOYDB_IP,
    "port": ALLOYDB_PORT,
    "dbname": ALLOYDB_DB,
    "user": ALLOYDB_USER,
    "password": ALLOYDB_PASSWORD,
    "sslmode": "require",
    "connect_timeout": 30,
}


def connect():
    return psycopg2.connect(**DSN)


def load_billing_data(conn) -> int:
    path = DATA_DIR / "gcp_billing_export_jan2026.csv"
    with open(path) as f:
        reader = csv.reader(f)
        cols = next(reader)
        rows = list(reader)

    n = len(cols)
    cleaned = []
    for row in rows:
        if len(row) > n:
            row = row[: n - 1] + [",".join(row[n - 1 :])]
        cleaned.append(row + [""] * (n - len(row)))

    col_list = ", ".join(cols)
    placeholders = ", ".join(["%s"] * n)
    with conn.cursor() as cur:
        cur.execute("DELETE FROM billing_data")
        execute_batch(
            cur,
            f"INSERT INTO billing_data ({col_list}) VALUES ({placeholders})",
            cleaned,
            page_size=100,
        )
    conn.commit()
    return len(cleaned)


def load_idle_resources(conn) -> int:
    path = DATA_DIR / "idle_resources_jan2026.csv"
    with open(path) as f:
        reader = csv.reader(f)
        cols = next(reader)
        rows = list(reader)

    n = len(cols)
    cleaned = []
    for row in rows:
        if len(row) > n:
            row = row[: n - 1] + [",".join(row[n - 1 :])]
        cleaned.append(row + [""] * (n - len(row)))

    # Replace empty strings / non-date values with None for typed columns
    import re
    _DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    _NUM_RE  = re.compile(r"^-?\d+(\.\d+)?$")

    date_cols    = {"last_active_date", "label_created_date", "flagged_date"}
    numeric_cols = {
        "monthly_cost_usd", "days_idle", "cpu_avg_pct_14d",
        "connection_count_14d", "invocation_count_21d",
    }
    col_indices = {c: i for i, c in enumerate(cols)}
    result = []
    for row in cleaned:
        row = list(row)
        for col in date_cols:
            if col in col_indices:
                v = row[col_indices[col]]
                if not (v and _DATE_RE.match(v)):
                    row[col_indices[col]] = None
        for col in numeric_cols:
            if col in col_indices:
                v = row[col_indices[col]]
                if not (v and _NUM_RE.match(v)):
                    row[col_indices[col]] = None
        result.append(row)

    col_list = ", ".join(cols)
    placeholders = ", ".join(["%s"] * n)
    with conn.cursor() as cur:
        cur.execute("DELETE FROM idle_resources")
        execute_batch(
            cur,
            f"INSERT INTO idle_resources ({col_list}) VALUES ({placeholders})",
            result,
            page_size=100,
        )
    conn.commit()
    return len(result)


def load_budget_allocation(conn) -> int:
    path = DATA_DIR / "q1_2026_team_budgets.csv"
    with open(path) as f:
        reader = csv.reader(f)
        cols = next(reader)
        rows = list(reader)

    n = len(cols)
    cleaned = [row + [""] * (n - len(row)) for row in rows]

    col_list = ", ".join(cols)
    placeholders = ", ".join(["%s"] * n)
    with conn.cursor() as cur:
        cur.execute("DELETE FROM budget_allocation")
        execute_batch(
            cur,
            f"INSERT INTO budget_allocation ({col_list}) VALUES ({placeholders})",
            cleaned,
            page_size=100,
        )
    conn.commit()
    return len(cleaned)


def load_document_chunks(conn) -> int:
    store_path = DATA_DIR / "vector_store.json"
    if not store_path.exists():
        print("  ⚠ vector_store.json not found — run the ingestion pipeline first")
        return 0

    store = json.loads(store_path.read_text())

    with conn.cursor() as cur:
        cur.execute("DELETE FROM document_chunks")
        for chunk in store:
            cur.execute(
                "INSERT INTO document_chunks (source_file, chunk_index, chunk_text, embedding) "
                "VALUES (%s, %s, %s, %s::vector) "
                "ON CONFLICT (source_file, chunk_index) DO UPDATE "
                "SET chunk_text = EXCLUDED.chunk_text, embedding = EXCLUDED.embedding",
                (
                    chunk["source"],
                    chunk["chunk_index"],
                    chunk["text"],
                    "[" + ",".join(str(v) for v in chunk["embedding"]) + "]",
                ),
            )
    conn.commit()
    return len(store)


def main():
    print("=" * 60)
    print(f"FinOps AlloyDB Ingestion — {ALLOYDB_IP}:{ALLOYDB_PORT}/{ALLOYDB_DB}")
    print("=" * 60)

    print("\nConnecting...")
    conn = connect()
    print("  Connected")

    print("\n[1/4] Loading billing_data...")
    n = load_billing_data(conn)
    print(f"  Loaded {n} rows")

    print("\n[2/4] Loading idle_resources...")
    n = load_idle_resources(conn)
    print(f"  Loaded {n} rows")

    print("\n[3/4] Loading budget_allocation...")
    n = load_budget_allocation(conn)
    print(f"  Loaded {n} rows")

    print("\n[4/4] Loading document_chunks (vector embeddings)...")
    n = load_document_chunks(conn)
    print(f"  Loaded {n} chunks")

    conn.close()
    print("\n✓ AlloyDB ingestion complete")


if __name__ == "__main__":
    main()
