from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .alerts import build_alerts
from .db import DEFAULT_DB_PATH, connect, init_db
from .forecast import build_reorder_plan
from .ops_brief import import_ops_brief, operational_alerts
from .inventory import add_demand_event, add_item, load_items_csv, record_movement
from .server import run_dashboard


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inventory proof tracking system")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Create database schema")
    sub.add_parser("seed", help="Load sample items and movements")

    item = sub.add_parser("item", help="Manage items")
    item_sub = item.add_subparsers(dest="item_command", required=True)
    add = item_sub.add_parser("add")
    add.add_argument("--sku", required=True)
    add.add_argument("--name", required=True)
    add.add_argument("--unit", default="each")
    add.add_argument("--reorder-point", type=float, default=0)
    add.add_argument("--safety-stock", type=float, default=0)
    add.add_argument("--lead-time-days", type=int, default=7)

    move = sub.add_parser("move", help="Record inventory movement")
    move.add_argument("--sku", required=True)
    move.add_argument("--type", choices=["inflow", "outflow", "adjustment"], required=True)
    move.add_argument("--quantity", type=float, required=True)
    move.add_argument("--reason", required=True)
    move.add_argument("--ref")
    move.add_argument("--occurred-at")

    demand = sub.add_parser("demand", help="Add known calendar demand")
    demand.add_argument("--sku", required=True)
    demand.add_argument("--event-name", required=True)
    demand.add_argument("--expected-quantity", type=float, required=True)
    demand.add_argument("--event-date", required=True)

    import_items = sub.add_parser("import-items")
    import_items.add_argument("--csv", required=True)

    sub.add_parser("plan", help="Print reorder plan")
    sub.add_parser("alerts", help="Print action alerts")

    import_brief = sub.add_parser("import-ops-brief", help="Import studio ops brief markdown/text")
    import_brief.add_argument("--file", required=True)

    sub.add_parser("ops-alerts", help="Print operational alerts from imported brief")

    dashboard = sub.add_parser("dashboard", help="Run local dashboard")
    dashboard.add_argument("--host", default="127.0.0.1")
    dashboard.add_argument("--port", type=int, default=8787)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    db_path = Path(args.db)
    if args.command == "init":
        init_db(db_path)
        print(f"initialized {db_path}")
    elif args.command == "seed":
        seed(db_path)
        print(f"seeded {db_path}")
    elif args.command == "item" and args.item_command == "add":
        add_item(db_path, args.sku, args.name, args.unit, args.reorder_point, args.safety_stock, args.lead_time_days)
        print(f"saved item {args.sku}")
    elif args.command == "move":
        record_movement(db_path, args.sku, args.type, args.quantity, args.reason, args.ref, args.occurred_at)
        print(f"recorded {args.type} for {args.sku}")
    elif args.command == "demand":
        add_demand_event(db_path, args.sku, args.event_name, args.expected_quantity, args.event_date)
        print(f"recorded demand for {args.sku}")
    elif args.command == "import-items":
        count = load_items_csv(db_path, args.csv)
        print(f"imported {count} items")
    elif args.command == "plan":
        for plan in build_reorder_plan(db_path):
            print(
                f"{plan.status:10} {plan.sku:14} stock={plan.stock_on_hand:g} {plan.unit} "
                f"use/day={plan.daily_usage:g} reorder_by={plan.reorder_by_date or '-'} "
                f"order_qty={plan.reorder_quantity:g}"
            )
    elif args.command == "alerts":
        for alert in build_alerts(db_path):
            print(f"[{alert['severity']}] {alert['sku']}: {alert['message']}")
    elif args.command == "import-ops-brief":
        summary = import_ops_brief(db_path, args.file)
        print(
            "imported ops brief "
            f"source_id={summary.source_document_id} "
            f"boxes={summary.box_specs} supplies={summary.supply_statuses} "
            f"orders={summary.open_order_flags} hs_codes={summary.hs_codes} "
            f"packing_specs={summary.packing_specs}"
        )
    elif args.command == "ops-alerts":
        for alert in operational_alerts(db_path):
            print(f"[{alert['severity']}] {alert['type']} {alert['item']}: {alert['message']} source_line={alert['source_line']}")
    elif args.command == "dashboard":
        init_db(db_path)
        run_dashboard(db_path, args.host, args.port)
    return 0


def seed(db_path: Path) -> None:
    init_db(db_path)
    with connect(db_path) as conn:
        existing_seed = conn.execute(
            "SELECT COUNT(*) AS count FROM movements WHERE ref = 'seed' OR ref LIKE 'seed-day-%'"
        ).fetchone()
        if int(existing_seed["count"]) > 0:
            return
    add_item(db_path, "GLOVES-M", "Nitrile Gloves Medium", "box", 20, 10, 7)
    add_item(db_path, "SANITIZER-1L", "Hand Sanitizer 1L", "bottle", 12, 6, 5)
    add_item(db_path, "LABEL-ROLL", "Shipping Label Roll", "roll", 8, 4, 10)
    for sku, quantity in [("GLOVES-M", 80), ("SANITIZER-1L", 30), ("LABEL-ROLL", 16)]:
        record_movement(db_path, sku, "inflow", quantity, "seed opening stock", "seed")
    for day, qty in enumerate([6, 8, 7, 9, 5, 8, 7], start=1):
        record_movement(db_path, "GLOVES-M", "outflow", qty, "seed usage", f"seed-day-{day}", f"2026-06-0{day}T09:00:00")
    add_demand_event(db_path, "GLOVES-M", "Scheduled high-volume week", 18, "2026-06-15")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
