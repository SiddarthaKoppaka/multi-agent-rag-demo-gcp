# FinOps Intelligence Assistant — Full Planning Document

---

## What is FinOps?

FinOps stands for **Financial Operations** — it's the practice of bringing financial accountability to cloud spending. As companies move to AWS, GCP, Azure, they lose the predictability of fixed infrastructure costs. Cloud bills become variable, complex, and hard to attribute.

FinOps is the discipline that answers:
- *Who is spending what, on which service, and why?*
- *Is this spend justified against business value?*
- *Where are we wasting money?*

The FinOps Foundation defines three lifecycle stages every organization cycles through:

**Inform → Optimize → Operate**

| Stage | What's happening |
|---|---|
| Inform | Visibility — understand where money is going |
| Optimize | Action — rightsize, reserve, eliminate waste |
| Operate | Culture — engineers own their costs, decisions are data-driven |

In most mid-to-large companies today, this cycle is **manually driven** — a FinOps analyst spends hours every week pulling cost exports from AWS Cost Explorer or GCP Billing, writing Excel formulas, reading policy PDFs, cross-referencing with engineering teams, and writing Slack messages like *"Hey, your Cloud Run service has been idle for 3 weeks."*

That manual loop is what we're replacing.

---

## Key Terms to Know Cold

**Cost Allocation** — tagging cloud resources (VMs, storage, functions) to a team, project, or business unit so you know who owns what spend.

**Showback vs. Chargeback** — Showback means you *show* teams their costs for awareness. Chargeback means you actually *bill* internal teams. Most orgs start with showback.

**Rightsizing** — identifying resources that are over-provisioned (a VM with 64GB RAM running at 4% utilization) and recommending a smaller, cheaper tier.

**Idle Resources** — cloud resources that exist but aren't doing useful work. A stopped VM still costs money for the disk. A Load Balancer with zero traffic still has a fixed fee.

**Anomaly Detection** — catching spend spikes that deviate from historical baseline. A service that normally costs $200/month suddenly costs $4,000 — something changed.

**Budget Policy** — a written rule like *"No single team can exceed $5,000/month on compute without VP approval"* or *"All VMs must have cost-center tags."*

**Invoice Reconciliation** — matching line items on a cloud bill against expected spend, approved POs, and internal budgets.

**Unit Economics** — cost per meaningful business metric. *"We spend $0.003 per API call"* or *"Our cost per active user is $1.20/month."*

---

## What We're Mimicking / Replacing with AI

Here is the exact manual workflow we're automating:

```
Today (Manual):
Finance Analyst
  → Downloads GCP Billing export CSV
  → Opens Excel, pivots by service/team
  → Opens Policy PDF, checks approval thresholds manually
  → Calculates: days since resource created, % budget used
  → Writes summary email to engineering leads
  → Waits for response, follows up

Tomorrow (Our System):
Engineer/Finance Analyst types a question in natural language
  → System retrieves relevant policy docs + billing context
  → System computes derived metrics (% over budget, idle days)
  → System returns a grounded, cited answer in seconds
```

**Concrete questions our system must answer:**

- *"Which teams exceeded their compute budget this month?"*
- *"Does our current GKE cluster spend comply with the Q2 approved budget?"*
- *"Flag all resources that have been idle for more than 14 days."*
- *"What does our FinOps policy say about untagged resources?"*
- *"Summarize the payment terms in our GCP committed use contract."*
- *"What's our cost per active user this month?"*

The first two are **retrieval questions** — answered from policy docs and billing data. The last three are **computation questions** — require math, date logic, threshold evaluation.

That's exactly why the two-agent architecture is *motivated*, not arbitrary.

---

## Our Architecture

### The Corpus (What we ingest)

| Document | Type | Used for |
|---|---|---|
| FinOps Policy PDF | Policy doc | Budget thresholds, approval rules, tagging requirements |
| GCP Committed Use Contract | Contract PDF | Payment terms, committed spend, penalty clauses |
| Q1/Q2 Budget Allocation Sheet | Structured CSV | Per-team budget limits |
| GCP Billing Export | Structured CSV | Actual spend per service/resource/team |
| Anomaly Report (mock) | Text doc | Historical flagged incidents |

---

### Agent Architecture

```
User Query
    │
    ▼
┌─────────────────────────────┐
│      Router Agent            │  ← Gemini Flash (cheap, fast classifier)
│  reads: query intent         │
│  decides: lookup vs compute  │
└──────────┬──────────────────┘
           │
     ┌─────┴─────┐
     │           │
     ▼           ▼
┌─────────┐  ┌──────────────┐
│  RAG    │  │  Tool Agent  │  ← Claude Sonnet via LiteLLM
│  Agent  │  │              │     (multi-model layer)
└────┬────┘  └──────┬───────┘
     │               │
     ▼               ▼
Vertex AI        Python Tools:
Vector Search  • budget_checker()
+ AlloyDB      • idle_resource_flagger()
  pgvector     • date_calculator()
               • unit_economics_calculator()
               • anomaly_threshold_checker()
```

**Router Agent** — Gemini Flash. Reads the query, classifies intent, delegates via ADK agent transfer. One shot, fast, cheap.

**RAG Agent** — Gemini 1.5 Flash. Has one tool: `vector_search_tool`. Embeds the query, hits AlloyDB pgvector, retrieves top-3 policy/contract chunks, synthesizes a cited answer.

**Tool Agent** — Claude Sonnet (via LiteLLM). Has 5 pure Python function tools. No retrieval — pure computation over structured billing data. This is where your multi-model abstraction story lives.

**AlloyDB + pgvector** — stores embedded chunks from all policy and contract documents. Also stores the raw billing CSV rows as structured tables that the tool agent functions query directly via SQL.

**FastAPI** — three endpoints: `/query`, `/ingest`, `/health`. The `/query` handler runs the router agent and streams back the final response.

---

### Communication Pattern Between Agents

The router uses **LLM-driven delegation (agent transfer)** — not `AgentTool`. Control fully transfers to the specialist. The specialist's final response goes directly to the user.

For compound queries (*"Which teams violated policy AND what's their spend delta?"*) — the router can chain: call RAG agent first via `AgentTool` (returns result to router), then call Tool Agent with that result as context. This is the **Coordinator/Dispatcher** pattern from the ADK docs.

Session state (`session.state`) carries intermediate results between steps using `output_key`.

---

### Multi-Model Layer

```python
MODEL_REGISTRY = {
    "router": "gemini-flash-latest",
    "rag":    "gemini-1.5-flash",
    "tool":   LiteLlm("claude-sonnet-4-6"),
}
```

One file. One change to swap any model. That's the story.

---

### Deployment Stack

```
GitHub
  └── push → Cloud Build trigger
                └── docker build
                └── push to Artifact Registry
                └── gcloud run deploy
                        └── Cloud Run (containerized FastAPI)
                                └── connects to AlloyDB
                                └── connects to Vertex AI Embeddings
                                └── writes logs to Cloud Logging
