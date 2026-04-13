"""Idle resource tool — query and flag under-utilized GCP resources."""

import sqlite3

from fin_agent.config import DB_PATH


def get_idle_resources(team: str = "", min_days_idle: int = 0) -> str:
    """Get idle or under-utilized GCP resources with cost impact.

    Args:
        team: Filter by team (platform, data-analytics, ml-ai, backend,
              frontend, security). Leave empty for all teams.
        min_days_idle: Minimum idle days to include (0 = all).

    Returns:
        List of idle resources with cost, status, and remediation notes.
    """
    conn = sqlite3.connect(str(DB_PATH))

    query = (
        "SELECT resource_name, resource_type, team, environment, "
        "CAST(monthly_cost_usd AS REAL) AS cost, "
        "CAST(days_idle AS INTEGER) AS days_idle, "
        "idle_status, notes "
        "FROM idle_resources WHERE 1=1"
    )
    params: list = []

    if team:
        query += " AND team = ?"
        params.append(team)
    if min_days_idle > 0:
        query += " AND CAST(days_idle AS INTEGER) >= ?"
        params.append(min_days_idle)

    query += " ORDER BY cost DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    if not rows:
        return "No idle resources found matching the criteria."

    total_cost = sum(r[4] for r in rows)
    lines = [f"Found {len(rows)} idle resource(s) | Total monthly waste: ${total_cost:,.2f}\n"]

    for name, rtype, rteam, env, cost, days, status, notes in rows:
        lines.append(
            f"• {name} ({rtype})\n"
            f"  Team: {rteam} | Env: {env} | Cost: ${cost:,.2f}/mo | Idle: {days} days\n"
            f"  Status: {status}\n"
            f"  Notes: {notes}"
        )

    return "\n\n".join(lines)
