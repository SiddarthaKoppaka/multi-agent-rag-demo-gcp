"""Read-only SQL queries against the FinOps SQLite database."""

import sqlite3

from fin_agent.config import DB_PATH


def query_billing_data(sql_query: str) -> str:
    """Execute a read-only SQL query against the FinOps billing database.

    Available tables and key columns:

    billing_data — GCP billing export (Jan 2026)
      billing_account_id, invoice_month, service_description, sku_description,
      project_id, project_name, cost (TEXT→REAL), credits_amount, net_cost,
      currency, usage_amount, usage_unit, resource_name, location_region,
      label_team, label_environment, label_cost_center, label_project_id,
      label_owner_email, label_created_date, tags_environment

    idle_resources — Flagged idle resources
      resource_name, resource_type, project_id, team, environment, region,
      monthly_cost_usd (TEXT→REAL), last_active_date, days_idle,
      cpu_avg_pct_14d, idle_status, notes

    budget_allocation — Team budgets (Q1 2026)
      team, cost_center, monthly_budget_usd (TEXT→REAL),
      q1_2026_budget_usd, alert_threshold_pct, hard_cap_usd,
      primary_services, budget_owner_email, chargeback_model

    IMPORTANT: All numeric columns are stored as TEXT. Cast them with
    CAST(column AS REAL) for arithmetic. Only SELECT statements are allowed.

    Args:
        sql_query: A SELECT SQL query.

    Returns:
        Query results formatted as a text table.
    """
    normalized = sql_query.strip().upper()
    if not normalized.startswith("SELECT"):
        return "Error: Only SELECT queries are allowed for safety."

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(sql_query)
        rows = cursor.fetchall()
        if not rows:
            return "Query returned no results."

        columns = list(rows[0].keys())
        header = " | ".join(columns)
        sep = "-+-".join("-" * max(len(c), 8) for c in columns)
        lines = [header, sep]
        for row in rows:
            lines.append(" | ".join(str(row[c]) for c in columns))

        return "\n".join(lines)
    except Exception as e:
        return f"SQL Error: {e}"
    finally:
        conn.close()
