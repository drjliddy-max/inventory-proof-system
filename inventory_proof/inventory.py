from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
import csv
import sqlite3

from .db import connect, init_db


@dataclass(frozen=True)
class Item:
    sku: str
    name: str
    unit: str
    reorder_point: float
    safety_stock: float
    lead_time_days: int


class InventoryError(ValueError):
    pass


def add_item(
    db_path: str | Path,
    sku: str,
    name: str,
    unit: str = "each",
    reorder_point: float = 0,
    safety_stock: float = 0,
    lead_time_days: int = 7,
) -> None:
    init_db(db_path)
    if not sku.strip():
        raise InventoryError("SKU is required")
    if reorder_point < 0 or safety_stock < 0 or lead_time_days < 0:
        raise InventoryError("Planning fields cannot be negative")
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO items (sku, name, unit, reorder_point, safety_stock, lead_time_days)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(sku) DO UPDATE SET
                name = excluded.name,
                unit = excluded.unit,
                reorder_point = excluded.reorder_point,
                safety_stock = excluded.safety_stock,
                lead_time_days = excluded.lead_time_days,
                active = 1
            """,
            (sku.strip(), name.strip(), unit.strip(), reorder_point, safety_stock, lead_time_days),
        )


def stock_on_hand(conn: sqlite3.Connection, sku: str) -> float:
    row = conn.execute(
        """
        SELECT COALESCE(SUM(
            CASE movement_type
                WHEN 'inflow' THEN quantity
                WHEN 'outflow' THEN -quantity
                WHEN 'adjustment' THEN quantity
            END
        ), 0) AS stock
        FROM movements
        WHERE sku = ?
        """,
        (sku,),
    ).fetchone()
    return float(row["stock"])


def record_movement(
    db_path: str | Path,
    sku: str,
    movement_type: str,
    quantity: float,
    reason: str,
    ref: str | None = None,
    occurred_at: str | None = None,
) -> None:
    init_db(db_path)
    if movement_type not in {"inflow", "outflow", "adjustment"}:
        raise InventoryError("movement_type must be inflow, outflow, or adjustment")
    if quantity <= 0:
        raise InventoryError("quantity must be positive")
    timestamp = occurred_at or datetime.now(UTC).replace(microsecond=0).isoformat()

    with connect(db_path) as conn:
        item = conn.execute("SELECT sku FROM items WHERE sku = ? AND active = 1", (sku,)).fetchone()
        if item is None:
            raise InventoryError(f"Unknown active SKU: {sku}")
        if movement_type == "outflow" and stock_on_hand(conn, sku) - quantity < 0:
            raise InventoryError(f"Outflow would make stock negative for {sku}")
        conn.execute(
            """
            INSERT INTO movements (sku, movement_type, quantity, reason, ref, occurred_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (sku, movement_type, quantity, reason.strip(), ref, timestamp),
        )


def add_demand_event(
    db_path: str | Path,
    sku: str,
    event_name: str,
    expected_quantity: float,
    event_date: str,
) -> None:
    init_db(db_path)
    if expected_quantity <= 0:
        raise InventoryError("expected_quantity must be positive")
    date.fromisoformat(event_date)
    with connect(db_path) as conn:
        if conn.execute("SELECT sku FROM items WHERE sku = ?", (sku,)).fetchone() is None:
            raise InventoryError(f"Unknown SKU: {sku}")
        conn.execute(
            """
            INSERT INTO demand_events (sku, event_name, expected_quantity, event_date)
            VALUES (?, ?, ?, ?)
            """,
            (sku, event_name.strip(), expected_quantity, event_date),
        )


def reconcile_count(db_path: str | Path, sku: str, counted_quantity: float, note: str = "") -> None:
    init_db(db_path)
    if counted_quantity < 0:
        raise InventoryError("counted_quantity cannot be negative")
    with connect(db_path) as conn:
        current = stock_on_hand(conn, sku)
        delta = counted_quantity - current
        conn.execute(
            "INSERT INTO inventory_snapshots (sku, counted_quantity, note) VALUES (?, ?, ?)",
            (sku, counted_quantity, note),
        )
        if delta != 0:
            movement_type = "inflow" if delta > 0 else "outflow"
            conn.execute(
                """
                INSERT INTO movements (sku, movement_type, quantity, reason, ref)
                VALUES (?, ?, ?, ?, ?)
                """,
                (sku, movement_type, abs(delta), f"reconcile: {note}".strip(), "physical-count"),
            )


def load_items_csv(db_path: str | Path, csv_path: str | Path) -> int:
    count = 0
    with open(csv_path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            add_item(
                db_path,
                row["sku"],
                row["name"],
                row.get("unit", "each"),
                float(row.get("reorder_point") or 0),
                float(row.get("safety_stock") or 0),
                int(row.get("lead_time_days") or 7),
            )
            count += 1
    return count
