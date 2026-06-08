from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from inventory_proof.alerts import build_alerts
from inventory_proof.cli import seed
from inventory_proof.forecast import build_reorder_plan
from inventory_proof.inventory import InventoryError, add_demand_event, add_item, reconcile_count, record_movement


class InventoryProofTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "test.sqlite"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_stock_is_derived_from_movements(self) -> None:
        add_item(self.db, "A", "Widget", "each", reorder_point=5, safety_stock=2, lead_time_days=3)
        record_movement(self.db, "A", "inflow", 10, "purchase", "PO-1")
        record_movement(self.db, "A", "outflow", 4, "usage", "JOB-1")

        [plan] = build_reorder_plan(self.db)

        self.assertEqual(plan.stock_on_hand, 6)

    def test_outflow_cannot_make_stock_negative(self) -> None:
        add_item(self.db, "A", "Widget")
        record_movement(self.db, "A", "inflow", 2, "purchase")

        with self.assertRaises(InventoryError):
            record_movement(self.db, "A", "outflow", 3, "usage")

    def test_calendar_demand_changes_reorder_quantity(self) -> None:
        add_item(self.db, "A", "Widget", reorder_point=5, safety_stock=2, lead_time_days=3)
        record_movement(self.db, "A", "inflow", 10, "purchase")
        add_demand_event(self.db, "A", "Planned campaign", 12, "2026-06-15")

        [plan] = build_reorder_plan(self.db)

        self.assertEqual(plan.upcoming_demand, 12)
        self.assertEqual(plan.reorder_quantity, 9)

    def test_alerts_raise_order_now_below_reorder_point(self) -> None:
        add_item(self.db, "A", "Widget", reorder_point=5, safety_stock=2, lead_time_days=3)
        record_movement(self.db, "A", "inflow", 4, "purchase")

        alerts = build_alerts(self.db)

        self.assertEqual(alerts[0]["severity"], "critical")

    def test_reconcile_count_can_reduce_stock(self) -> None:
        add_item(self.db, "A", "Widget")
        record_movement(self.db, "A", "inflow", 10, "purchase")

        reconcile_count(self.db, "A", 7, "cycle count")

        [plan] = build_reorder_plan(self.db)
        self.assertEqual(plan.stock_on_hand, 7)

    def test_seed_is_idempotent(self) -> None:
        seed(self.db)
        first = {plan.sku: plan.stock_on_hand for plan in build_reorder_plan(self.db)}

        seed(self.db)
        second = {plan.sku: plan.stock_on_hand for plan in build_reorder_plan(self.db)}

        self.assertEqual(second, first)
        self.assertEqual(second["GLOVES-M"], 30)


if __name__ == "__main__":
    unittest.main()
