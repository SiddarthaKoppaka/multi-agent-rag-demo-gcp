"""Pre-built chart & analysis tools for the Analyst agent."""

import json
import statistics


def bar_chart(title: str, labels: list[str], values: list[float], x_label: str = "", y_label: str = "") -> str:
    """Generate a bar chart data specification.

    Args:
        title: Chart title.
        labels: Category labels for the x-axis.
        values: Numeric values for each bar.
        x_label: X-axis label.
        y_label: Y-axis label.

    Returns:
        JSON chart specification ready for rendering.
    """
    return json.dumps(
        {
            "chart_type": "bar",
            "title": title,
            "data": {"labels": labels, "values": values},
            "axes": {"x": x_label, "y": y_label},
        },
        indent=2,
    )


def line_chart(title: str, x_values: list[str], y_values: list[float], x_label: str = "", y_label: str = "") -> str:
    """Generate a line chart data specification.

    Args:
        title: Chart title.
        x_values: X-axis data points (e.g. dates, months).
        y_values: Y-axis numeric values.
        x_label: X-axis label.
        y_label: Y-axis label.

    Returns:
        JSON chart specification ready for rendering.
    """
    return json.dumps(
        {
            "chart_type": "line",
            "title": title,
            "data": {"x": x_values, "y": y_values},
            "axes": {"x": x_label, "y": y_label},
        },
        indent=2,
    )


def pie_chart(title: str, labels: list[str], values: list[float]) -> str:
    """Generate a pie chart data specification.

    Args:
        title: Chart title.
        labels: Slice labels.
        values: Slice values.

    Returns:
        JSON chart specification with calculated percentages.
    """
    total = sum(values) or 1
    slices = [
        {"label": l, "value": v, "percentage": round(v / total * 100, 1)}
        for l, v in zip(labels, values)
    ]
    return json.dumps(
        {"chart_type": "pie", "title": title, "data": {"slices": slices, "total": total}},
        indent=2,
    )


def summary_stats(data_description: str, values: list[float]) -> str:
    """Compute summary statistics for a dataset.

    Args:
        data_description: What the values represent.
        values: Numeric data points.

    Returns:
        JSON statistical summary (count, total, mean, median, min, max, stdev).
    """
    if not values:
        return json.dumps({"error": "No values provided."})

    result = {
        "description": data_description,
        "count": len(values),
        "total": round(sum(values), 2),
        "mean": round(statistics.mean(values), 2),
        "median": round(statistics.median(values), 2),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "stdev": round(statistics.stdev(values), 2) if len(values) > 1 else 0,
    }
    return json.dumps(result, indent=2)


def data_explainer(topic: str, findings: list[str]) -> str:
    """Structure key findings into a plain-English analysis narrative.

    Args:
        topic: The analysis topic.
        findings: List of key findings to present.

    Returns:
        Numbered findings formatted as an executive summary.
    """
    lines = [f"Analysis: {topic}", "=" * (len(topic) + 10), ""]
    for i, finding in enumerate(findings, 1):
        lines.append(f"{i}. {finding}")
    return "\n".join(lines)
