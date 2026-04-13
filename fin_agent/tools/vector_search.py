"""RAG retrieval — embed query via Vertex AI, cosine-search local vector store."""

import json

import numpy as np
import vertexai
from vertexai.language_models import TextEmbeddingModel

from fin_agent.config import (
    DATA_DIR,
    GOOGLE_CLOUD_LOCATION,
    GOOGLE_CLOUD_PROJECT,
    MODEL_REGISTRY,
    TOP_K,
)

VECTOR_STORE_PATH = DATA_DIR / "vector_store.json"

_model_cache: TextEmbeddingModel | None = None


def _get_embedding_model() -> TextEmbeddingModel:
    global _model_cache
    if _model_cache is None:
        vertexai.init(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION)
        _model_cache = TextEmbeddingModel.from_pretrained(MODEL_REGISTRY["embedding"])
    return _model_cache


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    a_arr, b_arr = np.asarray(a), np.asarray(b)
    return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))


def search_knowledge_base(query: str) -> str:
    """Search the FinOps knowledge base (policies, contracts, incident reports).

    Use this tool to find information about Acme Corp's cloud cost management
    policy, CUD contracts, anomaly/incident reports, budget thresholds, tagging
    requirements, idle resource definitions, and escalation procedures.

    Args:
        query: Natural-language description of the information you need.

    Returns:
        Top-k relevant text passages with source attribution and relevance scores.
    """
    model = _get_embedding_model()
    query_emb = model.get_embeddings([query])[0].values

    store = json.loads(VECTOR_STORE_PATH.read_text(encoding="utf-8"))

    scored = []
    for chunk in store:
        sim = _cosine_similarity(query_emb, chunk["embedding"])
        scored.append((sim, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:TOP_K]

    results = []
    for score, chunk in top:
        results.append(
            f"[Source: {chunk['source']} | Chunk {chunk['chunk_index']} | Relevance: {score:.3f}]\n"
            f"{chunk['text']}"
        )

    return "\n\n---\n\n".join(results)
