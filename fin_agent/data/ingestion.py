"""Ingestion pipeline — chunk markdown docs, embed via Vertex AI, load CSVs to SQLite."""

import csv
import json
import sqlite3
from pathlib import Path

import vertexai
from vertexai.language_models import TextEmbeddingModel

from fin_agent.config import (
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_CLOUD_LOCATION,
    DATA_DIR,
    DB_PATH,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    MODEL_REGISTRY,
)

VECTOR_STORE_PATH = DATA_DIR / "vector_store.json"


# ── Text Chunking ───────────────────────────────────────────────
def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping character-level chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


# ── Vertex AI Embeddings ────────────────────────────────────────
def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using Vertex AI text-embedding-005."""
    vertexai.init(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION)
    model = TextEmbeddingModel.from_pretrained(MODEL_REGISTRY["embedding"])

    embeddings = []
    batch_size = 250  # Vertex AI limit
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        results = model.get_embeddings(batch)
        embeddings.extend([r.values for r in results])
    return embeddings


# ── Markdown → Vector Store ─────────────────────────────────────
def ingest_markdown_docs() -> list[dict]:
    """Chunk and embed all markdown docs in data/, save to vector_store.json."""
    md_files = sorted(DATA_DIR.glob("*.md"))
    all_chunks: list[dict] = []

    for md_path in md_files:
        text = md_path.read_text(encoding="utf-8")
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            all_chunks.append(
                {"source": md_path.name, "chunk_index": i, "text": chunk}
            )

    if not all_chunks:
        print("No markdown files found to ingest.")
        return []

    texts = [c["text"] for c in all_chunks]
    embeddings = embed_texts(texts)

    for chunk, emb in zip(all_chunks, embeddings):
        chunk["embedding"] = emb

    VECTOR_STORE_PATH.write_text(json.dumps(all_chunks, indent=2))
    print(f"Ingested {len(all_chunks)} chunks from {len(md_files)} markdown files → {VECTOR_STORE_PATH}")
    return all_chunks


# ── CSV → SQLite ────────────────────────────────────────────────
def ingest_csv_to_sqlite() -> None:
    """Load all CSV data files into SQLite tables."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))

    csv_tables = {
        "billing_data": DATA_DIR / "gcp_billing_export_jan2026.csv",
        "idle_resources": DATA_DIR / "idle_resources_jan2026.csv",
        "budget_allocation": DATA_DIR / "q1_2026_team_budgets.csv",
    }

    for table_name, csv_path in csv_tables.items():
        if not csv_path.exists():
            print(f"  Skipping {table_name}: {csv_path} not found")
            continue

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            columns = next(reader)
            raw_rows = list(reader)

        if not raw_rows:
            continue

        # Handle rows with more values than headers by merging extras
        # into the last column (covers notes fields that contain commas)
        cleaned_rows: list[list[str]] = []
        n_cols = len(columns)
        for row in raw_rows:
            if len(row) > n_cols:
                merged = row[: n_cols - 1] + [",".join(row[n_cols - 1 :])]
                cleaned_rows.append(merged)
            else:
                # Pad short rows with empty strings
                cleaned_rows.append(row + [""] * (n_cols - len(row)))

        col_defs = ", ".join(f'"{c}" TEXT' for c in columns)
        conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')
        conn.execute(f'CREATE TABLE "{table_name}" ({col_defs})')

        placeholders = ", ".join("?" for _ in columns)
        col_names = ", ".join(f'"{c}"' for c in columns)
        for row in cleaned_rows:
            conn.execute(
                f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})',
                row,
            )

        print(f"  Loaded {len(cleaned_rows)} rows into {table_name}")

    conn.commit()
    conn.close()
    print(f"SQLite database ready at {DB_PATH}")


# ── Run All ─────────────────────────────────────────────────────
def run_ingestion() -> None:
    """Run the full ingestion pipeline."""
    print("=" * 60)
    print("Starting ingestion pipeline")
    print("=" * 60)
    print("\n[1/2] Loading CSVs into SQLite...")
    ingest_csv_to_sqlite()
    print("\n[2/2] Chunking & embedding markdown docs...")
    ingest_markdown_docs()
    print("\nIngestion complete.")


if __name__ == "__main__":
    run_ingestion()
