"""Analyst agent — visualization & reporting specialist (runs as A2A service)."""

from google.adk.agents import Agent

from analyst_agent.tools import (
    bar_chart,
    data_explainer,
    line_chart,
    pie_chart,
    summary_stats,
)

root_agent = Agent(
    name="analyst_agent",
    model="gemini-2.0-flash",
    description=(
        "FinOps Analyst that creates chart specifications, computes summary "
        "statistics, and produces plain-English data narratives."
    ),
    instruction=(
        "You are the FinOps Analyst for Acme Corp. You specialise in:\n"
        "• Creating chart specifications (bar, line, pie) from provided data\n"
        "• Computing summary statistics\n"
        "• Translating numbers into clear executive-level narratives\n\n"
        "Rules:\n"
        "1. Always use the chart tools to produce structured JSON specs.\n"
        "2. Accompany every chart with a data_explainer narrative.\n"
        "3. Use summary_stats for any dataset with 3+ values.\n"
        "4. Be specific — include dollar amounts, percentages, and team names.\n"
        "5. Highlight actionable insights (savings opportunities, policy violations)."
    ),
    tools=[bar_chart, line_chart, pie_chart, summary_stats, data_explainer],
)
