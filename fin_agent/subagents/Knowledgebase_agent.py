"""Knowledgebase (RAG) sub-agent — retrieves from embedded FinOps documents."""

from google.adk.agents import Agent

from fin_agent.config import MODEL_REGISTRY
from fin_agent.tools.vector_search import search_knowledge_base

knowledgebase_agent = Agent(
    name="knowledgebase_agent",
    description=(
        "Retrieves information from FinOps policy documents, CUD contracts, "
        "and anomaly incident reports using semantic search."
    ),
    model=MODEL_REGISTRY["rag"],
    instruction=(
        "You are the FinOps Knowledge Base specialist for Acme Corp.\n\n"
        "Your knowledge covers:\n"
        "• Cloud Cost Management & FinOps Policy (FINOPS-POL-001 v2.4)\n"
        "• GCP Committed Use Discount Contract (GCP-CUD-ACME-2025-0047)\n"
        "• Cloud Spend Anomaly & Incident Report (Q4 2025 + Jan 2026)\n\n"
        "Rules:\n"
        "1. ALWAYS call search_knowledge_base to retrieve context before answering.\n"
        "2. Quote specific section numbers, dollar amounts, dates, and thresholds.\n"
        "3. Cite the source document name for every factual claim.\n"
        "4. If the retrieved passages don't contain the answer, say so explicitly.\n"
        "5. Never fabricate policy details — rely only on retrieved content."
    ),
    tools=[search_knowledge_base],
)
