"""Policy Lookup (structured data) sub-agent — SQL queries, budget checks, analytics."""

from google.adk.agents import Agent

from fin_agent.config import MODEL_REGISTRY
from fin_agent.tools.anomaly_checker import search_anomaly_incidents
from fin_agent.tools.budget_checker import check_team_budget_status
from fin_agent.tools.idle_resources import get_idle_resources
from fin_agent.tools.sql_query import query_billing_data
from fin_agent.tools.unit_economics import analyze_cud_utilization

policy_lookup_agent = Agent(
    name="policy_lookup_agent",
    description=(
        "Runs computations on structured FinOps data: billing exports, budget "
        "allocations, idle resources, CUD utilization, and anomaly incidents."
    ),
    model=MODEL_REGISTRY["tool_agent"],
    instruction=(
        "You are a FinOps Data Analyst with direct access to Acme Corp's structured data.\n\n"
        "Available data (January 2026):\n"
        "• billing_data — 38 line items across 6 teams and 26 columns\n"
        "• budget_allocation — Q1 2026 budgets for 6 teams\n"
        "• idle_resources — 9 flagged idle/under-utilized resources\n"
        "• CUD portfolio — 5 active committed use discounts ($10,140/mo total)\n"
        "• Anomaly incidents — Q4 2025 + Jan 2026 (5 incidents, $41,820 unplanned)\n\n"
        "SQL tips (all columns stored as TEXT — use CAST for math):\n"
        "  SELECT label_team, SUM(CAST(net_cost AS REAL)) FROM billing_data GROUP BY label_team\n"
        "  SELECT * FROM idle_resources WHERE CAST(days_idle AS INTEGER) > 30\n\n"
        "Rules:\n"
        "1. Use the right tool for each question — prefer specific tools (check_team_budget_status, "
        "get_idle_resources, analyze_cud_utilization) over raw SQL where possible.\n"
        "2. Use query_billing_data for custom or cross-table analysis.\n"
        "3. Always show specific numbers, dollar amounts, and percentages.\n"
        "4. Compare actuals against budgets and policy thresholds when relevant.\n"
        "5. Highlight violations, anomalies, and concerning trends."
    ),
    tools=[
        query_billing_data,
        check_team_budget_status,
        get_idle_resources,
        search_anomaly_incidents,
        analyze_cud_utilization,
    ],
)
