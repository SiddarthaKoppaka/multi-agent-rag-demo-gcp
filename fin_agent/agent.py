"""Root router agent — delegates to Knowledgebase and Policy Lookup sub-agents."""

from google.adk.agents import Agent

from fin_agent.config import MODEL_REGISTRY
from fin_agent.guardrails import pii_before_model, pii_before_tool
from fin_agent.subagents.Knowledgebase_agent import knowledgebase_agent
from fin_agent.subagents.policy_lookup_agent import policy_lookup_agent

root_agent = Agent(
    name="finops_router",
    model=MODEL_REGISTRY["router"],
    description="FinOps Intelligence Assistant — routes queries to specialist agents.",
    instruction=(
        "You are the FinOps Intelligence Assistant for Acme Corp. "
        "You route user questions to the right specialist sub-agent.\n\n"
        "Routing rules:\n"
        "• Policy / contract / incident document lookups → transfer to knowledgebase_agent\n"
        "  Examples: 'What is the idle resource policy?', 'What are the CUD payment terms?', "
        "'What happened in incident INC-2025-052?'\n\n"
        "• Numerical analysis / budget checks / idle resources / SQL queries → transfer to policy_lookup_agent\n"
        "  Examples: 'Which teams exceeded budget?', 'How much are idle resources costing?', "
        "'What is the CUD utilization rate?'\n\n"
        "• For questions that need BOTH document context AND computation, start with "
        "knowledgebase_agent for context then use policy_lookup_agent for the numbers.\n\n"
        "Always be helpful, accurate, and cite sources. If unsure which agent to use, "
        "ask the user for clarification."
    ),
    sub_agents=[knowledgebase_agent, policy_lookup_agent],
    before_model_callback=pii_before_model,
    before_tool_callback=pii_before_tool,
) 




