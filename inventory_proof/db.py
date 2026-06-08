from __future__ import annotations

import sqlite3
from pathlib import Path


DEFAULT_DB_PATH = Path("inventory.sqlite")


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        super().__exit__(exc_type, exc_value, traceback)
        self.close()
        return False


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS items (
    sku TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    unit TEXT NOT NULL DEFAULT 'each',
    reorder_point REAL NOT NULL DEFAULT 0,
    safety_stock REAL NOT NULL DEFAULT 0,
    lead_time_days INTEGER NOT NULL DEFAULT 7,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL REFERENCES items(sku),
    movement_type TEXT NOT NULL CHECK (movement_type IN ('inflow', 'outflow', 'adjustment')),
    quantity REAL NOT NULL CHECK (quantity > 0),
    reason TEXT NOT NULL,
    ref TEXT,
    occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS demand_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL REFERENCES items(sku),
    event_name TEXT NOT NULL,
    expected_quantity REAL NOT NULL CHECK (expected_quantity > 0),
    event_date TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventory_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL REFERENCES items(sku),
    counted_quantity REAL NOT NULL CHECK (counted_quantity >= 0),
    counted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    note TEXT
);

CREATE TABLE IF NOT EXISTS source_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    source_path TEXT,
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sha256 TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS box_specs (
    code TEXT PRIMARY KEY,
    dimensions TEXT NOT NULL,
    box_type TEXT,
    source_document_id INTEGER REFERENCES source_documents(id),
    source_line INTEGER
);

CREATE TABLE IF NOT EXISTS supply_statuses (
    item TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    source TEXT,
    notes TEXT,
    category TEXT NOT NULL,
    source_document_id INTEGER REFERENCES source_documents(id),
    source_line INTEGER,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS open_order_flags (
    order_number TEXT PRIMARY KEY,
    pallet_size TEXT,
    item_quantity REAL,
    ship_date TEXT,
    notes TEXT,
    flag_reason TEXT NOT NULL,
    source_document_id INTEGER REFERENCES source_documents(id),
    source_line INTEGER
);

CREATE TABLE IF NOT EXISTS hs_codes (
    product_type TEXT PRIMARY KEY,
    hs_code TEXT NOT NULL,
    source_document_id INTEGER REFERENCES source_documents(id),
    source_line INTEGER
);

CREATE TABLE IF NOT EXISTS packing_specs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product TEXT NOT NULL,
    variant TEXT NOT NULL,
    inner_box TEXT,
    foam_config TEXT,
    weight TEXT,
    notes TEXT,
    carrier_restriction TEXT,
    source_document_id INTEGER REFERENCES source_documents(id),
    source_line INTEGER,
    UNIQUE(product, variant)
);
"""


def connect(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), factory=ClosingConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)
