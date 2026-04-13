"""Anomaly / incident checker — search Q4 2025 + Jan 2026 incident reports."""

from fin_agent.config import DATA_DIR


def search_anomaly_incidents(query: str = "", severity: str = "") -> str:
    """Search cloud spend anomaly and incident reports.

    Covers Q4 2025 and January 2026 incidents documented by the FinOps CoE.

    Args:
        query: Free-text search term (e.g. 'BigQuery', 'GPU', 'idle', 'egress').
        severity: Filter by severity level: P1, P2, or P3. Leave empty for all.

    Returns:
        Matching incident summaries with root cause, impact, and resolution.
    """
    report_path = DATA_DIR / "anomaly_incident_report_q4_2025.md"
    if not report_path.exists():
        return "Anomaly incident report not found."

    text = report_path.read_text(encoding="utf-8")

    # Split on incident headers
    sections = text.split("### INC-")
    incidents: list[str] = []

    for section in sections[1:]:  # skip preamble
        first_line = section.split("\n")[0]
        inc_id = "INC-" + first_line.strip()

        # Severity filter
        if severity:
            sev = severity.upper()
            if f"| {sev} " not in first_line and f"| {sev}|" not in first_line:
                continue

        # Text filter
        if query and query.lower() not in section.lower():
            continue

        body = "\n".join(section.split("\n")[1:]).strip()
        incidents.append(f"### {inc_id}\n{body}")

    if not incidents:
        filters = []
        if query:
            filters.append(f"query='{query}'")
        if severity:
            filters.append(f"severity='{severity}'")
        return f"No incidents found matching {', '.join(filters) or 'any criteria'}."

    return f"Found {len(incidents)} incident(s):\n\n" + "\n\n---\n\n".join(incidents)
