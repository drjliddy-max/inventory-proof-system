from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from pathlib import Path

from .db import connect, init_db
from .inventory import stock_on_hand


@dataclass(frozen=True)
class ReorderPlan:
    sku: str
    name: str
    stock_on_hand: float
    unit: str
    daily_usage: float
    upcoming_demand: float
    days_until_stockout: float | None
    projected_stockout_date: str | None
    reorder_by_date: str | None
    reorder_quantity: float
    status: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _parse_day(value: str) -> date:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def recent_daily_usage(conn, sku: str, lookback_days: int = 30) -> float:
    since = (date.today() - timedelta(days=lookback_days)).isoformat()
    row = conn.execute(
        """
        SELECT COALESCE(SUM(quantity), 0) AS used
        FROM movements
        WHERE sku = ? AND movement_type = 'outflow' AND date(occurred_at) >= date(?)
        """,
        (sku, since),
    ).fetchone()
    return round(float(row["used"]) / lookback_days, 3)


def upcoming_demand(conn, sku: str, horizon_days: int = 30) -> float:
    start = date.today().isoformat()
    end = (date.today() + timedelta(days=horizon_days)).isoformat()
    row = conn.execute(
        """
        SELECT COALESCE(SUM(expected_quantity), 0) AS expected
        FROM demand_events
        WHERE sku = ? AND date(event_date) BETWEEN date(?) AND date(?)
        """,
        (sku, start, end),
    ).fetchone()
    return float(row["expected"])


def build_reorder_plan(db_path: str | Path) -> list[ReorderPlan]:
    init_db(db_path)
    plans: list[ReorderPlan] = []
    with connect(db_path) as conn:
        items = conn.execute(
            """
            SELECT sku, name, unit, reorder_point, safety_stock, lead_time_days
            FROM items
            WHERE active = 1
            ORDER BY sku
            """
        ).fetchall()
        for item in items:
            sku = item["sku"]
            stock = stock_on_hand(conn, sku)
            daily_usage = recent_daily_usage(conn, sku)
            future_demand = upcoming_demand(conn, sku)
            effective_available = max(stock - future_demand - float(item["safety_stock"]), 0)
            days_until_stockout = None
            stockout_date = None
            reorder_by_date = None

            if daily_usage > 0:
                days_until_stockout = round(effective_available / daily_usage, 1)
                stockout = date.today() + timedelta(days=days_until_stockout)
                stockout_date = stockout.isoformat()
                reorder_by_date = (stockout - timedelta(days=int(item["lead_time_days"]))).isoformat()

            target_stock = max(float(item["reorder_point"]) + float(item["safety_stock"]) + future_demand, 0)
            reorder_quantity = max(round(target_stock - stock, 2), 0)
            status = _status(stock, float(item["reorder_point"]), daily_usage, reorder_by_date)
            plans.append(
                ReorderPlan(
                    sku=sku,
                    name=item["name"],
                    stock_on_hand=round(stock, 2),
                    unit=item["unit"],
                    daily_usage=daily_usage,
                    upcoming_demand=round(future_demand, 2),
                    days_until_stockout=days_until_stockout,
                    projected_stockout_date=stockout_date,
                    reorder_by_date=reorder_by_date,
                    reorder_quantity=reorder_quantity,
                    status=status,
                )
            )
    return plans


def _status(stock: float, reorder_point: float, daily_usage: float, reorder_by_date: str | None) -> str:
    today = date.today()
    if stock <= reorder_point:
        return "ORDER_NOW"
    if reorder_by_date and _parse_day(reorder_by_date) <= today:
        return "ORDER_NOW"
    if reorder_by_date and _parse_day(reorder_by_date) <= today + timedelta(days=7):
        return "ORDER_SOON"
    if daily_usage == 0:
        return "WATCH"
    return "OK"

