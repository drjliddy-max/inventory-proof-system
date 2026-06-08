from __future__ import annotations

from pathlib import Path

from .forecast import build_reorder_plan


def build_alerts(db_path: str | Path) -> list[dict[str, object]]:
    alerts: list[dict[str, object]] = []
    for plan in build_reorder_plan(db_path):
        if plan.status == "ORDER_NOW":
            alerts.append(
                {
                    "severity": "critical",
                    "sku": plan.sku,
                    "message": f"Order {plan.name} now. Suggested quantity: {plan.reorder_quantity} {plan.unit}.",
                }
            )
        elif plan.status == "ORDER_SOON":
            alerts.append(
                {
                    "severity": "warning",
                    "sku": plan.sku,
                    "message": f"Prepare purchase for {plan.name} by {plan.reorder_by_date}.",
                }
            )
        elif plan.status == "WATCH":
            alerts.append(
                {
                    "severity": "info",
                    "sku": plan.sku,
                    "message": f"No recent consumption for {plan.name}; verify usage tracking is connected.",
                }
            )
    return alerts

