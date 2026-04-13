"""Budget checker — compare actual Jan 2026 spend vs. approved team budgets."""

import sqlite3

from fin_agent.config import DB_PATH


def check_team_budget_status(team: str = "") -> str:
    """Check budget utilization for one team or for all teams.

    Compares actual January 2026 billing data against the approved monthly
    budgets and flags teams approaching or exceeding their limits.

    Args:
        team: Team name to check (platform, data-analytics, ml-ai, backend,
              frontend, security). Leave empty to check all teams.

    Returns:
        Budget status report with actual vs. budget, utilization %, and alerts.
    """
    conn = sqlite3.connect(str(DB_PATH))

    if team:
        budgets = conn.execute(
            "SELECT team, CAST(monthly_budget_usd AS REAL) AS budget, "
            "CAST(hard_cap_usd AS REAL) AS hard_cap, "
            "CAST(alert_threshold_pct AS REAL) AS alert_pct "
            "FROM budget_allocation WHERE team = ?",
            (team,),
        ).fetchall()
    else:
        budgets = conn.execute(
            "SELECT team, CAST(monthly_budget_usd AS REAL) AS budget, "
            "CAST(hard_cap_usd AS REAL) AS hard_cap, "
            "CAST(alert_threshold_pct AS REAL) AS alert_pct "
            "FROM budget_allocation ORDER BY budget DESC"
        ).fetchall()

    if not budgets:
        conn.close()
        return f"No budget data found for team '{team}'." if team else "No budget data found."

    results = []
    for team_name, budget, hard_cap, alert_pct in budgets:
        (actual,) = conn.execute(
            "SELECT COALESCE(SUM(CAST(net_cost AS REAL)), 0) "
            "FROM billing_data WHERE label_team = ?",
            (team_name,),
        ).fetchone()

        utilization = (actual / budget * 100) if budget > 0 else 0
        alert_threshold = budget * alert_pct / 100

        if actual >= hard_cap:
            status = "HARD CAP EXCEEDED"
        elif actual >= budget:
            status = "OVER BUDGET"
        elif actual >= alert_threshold:
            status = "ALERT — APPROACHING LIMIT"
        else:
            status = "OK"

        results.append(
            f"Team: {team_name}\n"
            f"  Monthly Budget: ${budget:,.2f} | Actual Spend: ${actual:,.2f}\n"
            f"  Utilization: {utilization:.1f}%\n"
            f"  Alert @ ${alert_threshold:,.2f} | Hard Cap: ${hard_cap:,.2f}\n"
            f"  Status: {status}"
        )

    conn.close()
    return "\n\n".join(results)
