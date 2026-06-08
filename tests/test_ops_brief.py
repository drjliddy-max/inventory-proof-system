from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from inventory_proof.db import connect
from inventory_proof.ops_brief import import_ops_brief, operational_alerts


SAMPLE = """Studio Operations — Cowork Setup Brief
Box Codes and Dimensions
Code\tDimensions\tType
A1\t10x10x10\tinner
B1\t14x14x10\tinner
Instapak Foam Reference
SKU Packing Specs
Francis
Variant\tInner Box\tFoam Config\tWeight
1\tA1\tx2 #20\t2 lbs
Yves
Variant\tInner Box\tFoam Config\tNotes
36\t48x48x28 CRATE\tx4 #100\tCRATE
Shipping Supplies Inventory
Printing / Computer
Item\tStatus\tSource
Label Tape\tLOW\tAmazon
Instapak Foam (main + annex)
Size\tMain\tAnnex
#10\tIN STOCK\t2
Pallet Shipping Supplies
Item\tStatus\tSource
Pallets 30x30\tOUT\tUline
Items Currently Flagged for Reorder
Open Pallet Orders (as of last update)
Order #\tPallet Size\tItem Qty\tShip Date\tNotes
9001001\tSmall 30x30\t4\tTBD\tConfirm payment with approver
Flag orders 9001001 and 9001002 as held until payment is confirmed.
Harmonization (HS) Codes
Product Type\tHS Code
Glass Lamps\t9405.11.5090
Shipping terms:
"""


class OpsBriefImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "test.sqlite"
        self.brief = self.root / "brain.md"
        self.brief.write_text(SAMPLE, encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_imports_structured_brief_data_with_alerts(self) -> None:
        summary = import_ops_brief(self.db, self.brief)

        self.assertEqual(summary.box_specs, 2)
        self.assertEqual(summary.supply_statuses, 3)
        self.assertEqual(summary.open_order_flags, 1)
        self.assertEqual(summary.hs_codes, 1)
        self.assertEqual(summary.packing_specs, 2)

        alerts = operational_alerts(self.db)
        messages = [alert["message"] for alert in alerts]
        self.assertIn("Label Tape is LOW in Printing / Computer.", messages)
        self.assertIn("Pallets 30x30 is OUT in Pallet Shipping Supplies.", messages)
        self.assertIn("Order 9001001: Hold until payment is confirmed.", messages)

    def test_packing_specs_mark_crate_restrictions(self) -> None:
        import_ops_brief(self.db, self.brief)

        with connect(self.db) as conn:
            row = conn.execute(
                "SELECT carrier_restriction FROM packing_specs WHERE product = ? AND variant = ?",
                ("Yves", "36"),
            ).fetchone()

        self.assertEqual(row["carrier_restriction"], "CRATE")


if __name__ == "__main__":
    unittest.main()
