"""CUD utilization analysis — committed use discount waste & recommendations."""

import json


def analyze_cud_utilization() -> str:
    """Analyze Committed Use Discount (CUD) portfolio utilization and waste.

    Based on contract GCP-CUD-ACME-2025-0047 (auto-renewed Mar 2026 – Feb 2027).
    Total monthly commitment: $10,140.

    Returns:
        CUD utilization summary, waste breakdown, and optimisation recommendations.
    """
    cuds = [
        {
            "id": "CUD-001",
            "type": "N2 Standard",
            "region": "us-central1",
            "vcpus": 64,
            "memory_gb": 256,
            "monthly_usd": 4100,
            "utilization_pct": 94,
            "discount_rate": 37,
        },
        {
            "id": "CUD-002",
            "type": "N2 Standard",
            "region": "us-east1",
            "vcpus": 32,
            "memory_gb": 128,
            "monthly_usd": 2050,
            "utilization_pct": 71,
            "discount_rate": 37,
        },
        {
            "id": "CUD-003",
            "type": "C2 Compute-Optimized",
            "region": "us-central1",
            "vcpus": 16,
            "memory_gb": 64,
            "monthly_usd": 1890,
            "utilization_pct": 88,
            "discount_rate": 57,
        },
        {
            "id": "CUD-004",
            "type": "Memory-Optimized M1",
            "region": "us-central1",
            "vcpus": 8,
            "memory_gb": 208,
            "monthly_usd": 1420,
            "utilization_pct": 52,
            "discount_rate": 28,
        },
        {
            "id": "CUD-005",
            "type": "GPU (NVIDIA T4)",
            "region": "us-central1",
            "vcpus": 4,
            "memory_gb": 15,
            "monthly_usd": 680,
            "utilization_pct": 103,
            "discount_rate": 15,
        },
    ]

    total_monthly = sum(c["monthly_usd"] for c in cuds)
    total_waste = sum(
        c["monthly_usd"] * (100 - c["utilization_pct"]) / 100
        for c in cuds
        if c["utilization_pct"] < 100
    )
    avg_util = sum(c["utilization_pct"] for c in cuds) / len(cuds)

    lines = [
        "CUD Portfolio Summary — GCP-CUD-ACME-2025-0047",
        f"Total Monthly Commitment: ${total_monthly:,.2f}",
        f"Average Utilization: {avg_util:.1f}%",
        f"Total Monthly Waste (under-utilized CUDs): ${total_waste:,.2f}",
        f"Contract Status: Auto-renewed (Mar 2026 – Feb 2027)\n",
    ]

    for c in cuds:
        waste = (
            c["monthly_usd"] * (100 - c["utilization_pct"]) / 100
            if c["utilization_pct"] < 100
            else 0
        )
        lines.append(
            f"• {c['id']} — {c['type']} ({c['region']})\n"
            f"  {c['vcpus']} vCPUs / {c['memory_gb']}GB | ${c['monthly_usd']:,.2f}/mo\n"
            f"  Utilization: {c['utilization_pct']}% | Waste: ${waste:,.2f}/mo | Discount: {c['discount_rate']}%"
        )

    lines.append("\nRecommendations:")
    lines.append("• CUD-002 (71%): Migrate workloads from other regions to us-east1 to boost utilization")
    lines.append("• CUD-004 (52%): Memory-optimized capacity significantly under-used — evaluate M1-eligible workloads for migration")
    lines.append("• CUD-005 (103%): GPU over-committed — evaluate purchasing additional T4 CUD to capture overage at discount")
    lines.append("• Overall CUD coverage is 67% of eligible compute (target: 80% per policy §6.2)")

    return "\n".join(lines)
