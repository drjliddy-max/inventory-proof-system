from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re

from .db import connect, init_db


STATUS_ORDER = {"OUT": 0, "LOW": 1, "IN STOCK": 2}


@dataclass(frozen=True)
class ImportSummary:
    source_document_id: int
    box_specs: int
    supply_statuses: int
    open_order_flags: int
    hs_codes: int
    packing_specs: int


def import_ops_brief(db_path: str | Path, brief_path: str | Path) -> ImportSummary:
    init_db(db_path)
    path = Path(brief_path)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    digest = sha256(text.encode("utf-8")).hexdigest()

    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT id FROM source_documents WHERE sha256 = ?",
            (digest,),
        ).fetchone()
        if row:
            source_id = int(row["id"])
        else:
            cur = conn.execute(
                "INSERT INTO source_documents (source_name, source_path, sha256) VALUES (?, ?, ?)",
                ("Studio Operations Brief", str(path), digest),
            )
            source_id = int(cur.lastrowid)

        box_count = _import_box_specs(conn, lines, source_id)
        supply_count = _import_supply_statuses(conn, lines, source_id)
        order_count = _import_open_order_flags(conn, lines, source_id)
        hs_count = _import_hs_codes(conn, lines, source_id)
        pack_count = _import_packing_specs(conn, lines, source_id)

    return ImportSummary(source_id, box_count, supply_count, order_count, hs_count, pack_count)


def operational_alerts(db_path: str | Path) -> list[dict[str, object]]:
    init_db(db_path)
    alerts: list[dict[str, object]] = []
    with connect(db_path) as conn:
        for row in conn.execute(
            """
            SELECT item, status, category, source, notes, source_line
            FROM supply_statuses
            WHERE status IN ('LOW', 'OUT')
            ORDER BY CASE status WHEN 'OUT' THEN 0 ELSE 1 END, item
            """
        ):
            severity = "critical" if row["status"] == "OUT" else "warning"
            alerts.append(
                {
                    "severity": severity,
                    "type": "supply",
                    "item": row["item"],
                    "message": f"{row['item']} is {row['status']} in {row['category']}.",
                    "source_line": row["source_line"],
                }
            )
        for row in conn.execute(
            """
            SELECT order_number, pallet_size, item_quantity, notes, flag_reason, source_line
            FROM open_order_flags
            ORDER BY order_number
            """
        ):
            alerts.append(
                {
                    "severity": "critical" if "payment" in row["flag_reason"].lower() else "warning",
                    "type": "order",
                    "item": row["order_number"],
                    "message": f"Order {row['order_number']}: {row['flag_reason']}.",
                    "source_line": row["source_line"],
                }
            )
    return alerts


def _section(lines: list[str], start: str, stop_prefixes: tuple[str, ...]) -> list[tuple[int, str]]:
    in_section = False
    collected: list[tuple[int, str]] = []
    for index, line in enumerate(lines, start=1):
        if line.strip() == start:
            in_section = True
            continue
        if in_section and line.strip() in stop_prefixes:
            break
        if in_section:
            collected.append((index, line))
    return collected


def _import_box_specs(conn, lines: list[str], source_id: int) -> int:
    rows = _section(lines, "Box Codes and Dimensions", ("Instapak Foam Reference",))
    count = 0
    for line_no, line in rows:
        if not line.strip() or line.startswith("Code\t"):
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            code = parts[0].strip()
            dimensions = parts[1].strip()
            box_type = parts[2].strip() if len(parts) > 2 else ""
            conn.execute(
                """
                INSERT INTO box_specs (code, dimensions, box_type, source_document_id, source_line)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(code) DO UPDATE SET
                    dimensions = excluded.dimensions,
                    box_type = excluded.box_type,
                    source_document_id = excluded.source_document_id,
                    source_line = excluded.source_line
                """,
                (code, dimensions, box_type, source_id, line_no),
            )
            count += 1
    return count


def _import_supply_statuses(conn, lines: list[str], source_id: int) -> int:
    categories = {
        "Printing / Computer",
        "Instapak Foam (main + annex)",
        "Box Shipping Supplies",
        "Pallet Shipping Supplies",
    }
    stop = "Items Currently Flagged for Reorder"
    current_category = ""
    count = 0
    in_supplies = False
    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped == "Shipping Supplies Inventory":
            in_supplies = True
            continue
        if in_supplies and stripped == stop:
            break
        if not in_supplies:
            continue
        if stripped in categories:
            current_category = stripped
            continue
        if not current_category or not stripped or stripped.startswith(("Item\t", "Size\t", "Last checked:")):
            continue
        parts = line.split("\t")
        if current_category == "Instapak Foam (main + annex)" and len(parts) >= 3:
            item = f"Instapak Foam {parts[0].strip()}"
            status = "IN STOCK" if parts[1].strip() == "IN STOCK" or parts[2].strip() not in {"", "—"} else "UNKNOWN"
            source = "main + annex"
            notes = f"main={parts[1].strip()} annex={parts[2].strip()}"
        elif len(parts) >= 2:
            item = parts[0].strip()
            status = parts[1].strip().upper()
            source = parts[2].strip() if len(parts) > 2 else ""
            notes = parts[3].strip() if len(parts) > 3 else ""
        else:
            continue
        conn.execute(
            """
            INSERT INTO supply_statuses (item, status, source, notes, category, source_document_id, source_line)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(item) DO UPDATE SET
                status = excluded.status,
                source = excluded.source,
                notes = excluded.notes,
                category = excluded.category,
                source_document_id = excluded.source_document_id,
                source_line = excluded.source_line,
                updated_at = CURRENT_TIMESTAMP
            """,
            (item, status, source, notes, current_category, source_id, line_no),
        )
        count += 1
    return count


def _import_open_order_flags(conn, lines: list[str], source_id: int) -> int:
    rows = []
    in_section = False
    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped == "Open Pallet Orders (as of last update)":
            in_section = True
            continue
        if in_section and (stripped.startswith("Flag orders ") or stripped == "Harmonization (HS) Codes"):
            break
        if in_section:
            rows.append((line_no, line))
    count = 0
    for line_no, line in rows:
        if not line.strip() or line.startswith("Order #\t"):
            continue
        parts = line.split("\t")
        if len(parts) < 5:
            continue
        order_number, pallet_size, quantity, ship_date, notes = [part.strip() for part in parts[:5]]
        flag_reason = _order_flag_reason(notes, pallet_size)
        if flag_reason:
            conn.execute(
                """
                INSERT INTO open_order_flags (order_number, pallet_size, item_quantity, ship_date, notes, flag_reason, source_document_id, source_line)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(order_number) DO UPDATE SET
                    pallet_size = excluded.pallet_size,
                    item_quantity = excluded.item_quantity,
                    ship_date = excluded.ship_date,
                    notes = excluded.notes,
                    flag_reason = excluded.flag_reason,
                    source_document_id = excluded.source_document_id,
                    source_line = excluded.source_line
                """,
                (order_number, pallet_size, float(quantity), ship_date, notes, flag_reason, source_id, line_no),
            )
            count += 1
    return count


def _order_flag_reason(notes: str, pallet_size: str) -> str:
    if "confirm payment" in notes.lower():
        return "Hold until payment is confirmed"
    if "30x30" in pallet_size:
        return "Small pallet order depends on 30x30 pallet availability"
    return ""


def _import_hs_codes(conn, lines: list[str], source_id: int) -> int:
    rows = _section(lines, "Product Type\tHS Code", ("Shipping terms:",))
    count = 0
    for line_no, line in rows:
        parts = line.split("\t")
        if len(parts) == 2:
            product_type, hs_code = parts[0].strip(), parts[1].strip()
            conn.execute(
                """
                INSERT INTO hs_codes (product_type, hs_code, source_document_id, source_line)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(product_type) DO UPDATE SET
                    hs_code = excluded.hs_code,
                    source_document_id = excluded.source_document_id,
                    source_line = excluded.source_line
                """,
                (product_type, hs_code, source_id, line_no),
            )
            count += 1
    return count


def _import_packing_specs(conn, lines: list[str], source_id: int) -> int:
    product = ""
    headers: list[str] = []
    count = 0
    known_products = {"Simone", "Anaïs", "Francis", "Inés", "Julien", "L'eau", "Lucienne", "Eden", "Yves", "Lazare"}
    stop_heads = {"Shipping Supplies Inventory", "Harmonization (HS) Codes", "Batch ID System"}
    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped in stop_heads:
            product = ""
            headers = []
        if stripped in known_products:
            product = stripped
            headers = []
            continue
        if not product or not stripped:
            continue
        if stripped.startswith("Variant\t"):
            headers = [part.strip() for part in line.split("\t")]
            continue
        if not headers or "\t" not in line:
            continue
        values = [part.strip() for part in line.split("\t")]
        row = {headers[i]: values[i] for i in range(min(len(headers), len(values)))}
        variant = row.get("Variant", "")
        if not variant:
            continue
        notes = row.get("Notes", "")
        carrier = _carrier_restriction(" ".join(values))
        conn.execute(
            """
            INSERT INTO packing_specs (product, variant, inner_box, foam_config, weight, notes, carrier_restriction, source_document_id, source_line)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(product, variant) DO UPDATE SET
                inner_box = excluded.inner_box,
                foam_config = excluded.foam_config,
                weight = excluded.weight,
                notes = excluded.notes,
                carrier_restriction = excluded.carrier_restriction,
                source_document_id = excluded.source_document_id,
                source_line = excluded.source_line
            """,
            (
                product,
                variant,
                row.get("Inner Box", ""),
                row.get("Foam Config", "") or _join_foam_columns(row),
                row.get("Weight", ""),
                notes,
                carrier,
                source_id,
                line_no,
            ),
        )
        count += 1
    return count


def _join_foam_columns(row: dict[str, str]) -> str:
    foam_parts = [row.get(key, "") for key in ("Bottom", "Top", "Sides") if row.get(key, "") not in {"", "—"}]
    return " / ".join(foam_parts)


def _carrier_restriction(text: str) -> str:
    upper = text.upper()
    if "CRATE" in upper:
        return "CRATE"
    if "PALLET" in upper:
        return "PALLET"
    return ""
