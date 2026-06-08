# Inventory Proof System

A cloneable inventory tracking system designed for proof outcomes:

- Track every inventory item from auditable inflow and outflow movements.
- Show current stock, consumption velocity, projected stockout dates, reorder-by dates, and user alerts.
- Run locally with Python and SQLite before real business inventory access is granted.
- Protect behavior with CI, tests, and guardrails so the system does not drift quietly.

This is a local proof harness and operations automation starter, not a claim that live inventory operations are fully automated or failure-proof.

## Quick Start

```bash
git clone <repo-url>
cd inventory-proof-system
./scripts/cowork_start.sh
```

Open `http://127.0.0.1:8787`.

## Core Commands

```bash
python -m inventory_proof.cli seed
python -m inventory_proof.cli item add --sku GLOVES-M --name "Nitrile Gloves M" --unit box --reorder-point 20 --safety-stock 10 --lead-time-days 7
python -m inventory_proof.cli move --sku GLOVES-M --type inflow --quantity 100 --reason purchase --ref PO-1001
python -m inventory_proof.cli move --sku GLOVES-M --type outflow --quantity 8 --reason usage --ref CASE-884
python -m inventory_proof.cli plan
python -m inventory_proof.cli alerts
python -m inventory_proof.cli dashboard
```

## Studio Ops Brief Import

The studio operations brief is a mixed source document, not a clean inventory table. Import it as evidence-backed operational data:

```bash
python -m inventory_proof.cli import-ops-brief --file /path/to/brain.md
python -m inventory_proof.cli ops-alerts
```

The importer extracts:

- box dimensions
- supply statuses
- open pallet-order flags
- HS codes
- packing specs with source-line evidence

Quantity-less values such as `LOW`, `OUT`, or `IN STOCK` are stored as operational status, not converted into fake stock counts.

Operational alerts appear in the dashboard and can also be printed with:

```bash
python -m inventory_proof.cli ops-alerts
```

For a real local deployment:

```bash
./scripts/cowork_start.sh --brief /path/to/ops/brain.md
```

## Proof Outcome Rules

This repo treats inventory as a ledger, not a spreadsheet guess.

1. Every stock count is calculated from immutable movement rows.
2. Outflows cannot make stock negative unless a manager explicitly reconciles with a count adjustment.
3. Reorder alerts are based on stock on hand, lead time, safety stock, recent consumption, and known calendar demand.
4. The dashboard reads the same tested planning engine as the CLI.
5. CI runs tests on every push and pull request.

## Data Model

- `items`: sku, name, unit, reorder point, safety stock, lead time.
- `movements`: inflow, outflow, or adjustment rows with quantity, reason, reference, timestamp.
- `demand_events`: calendar events that increase expected consumption.
- `inventory_snapshots`: optional physical count records used to reconcile ledger accuracy.

## Connecting Real Inventory Later

When access is granted, add an importer that writes to `movements` rather than overwriting stock counts. Keep external IDs in `ref` so each business event can be traced back to its source system.

## CI

The GitHub Actions workflow runs:

```bash
python -m unittest discover -s tests
python -m inventory_proof.cli --db /tmp/inventory-proof-ci.sqlite seed
python -m inventory_proof.cli --db /tmp/inventory-proof-ci.sqlite plan
```

## Claim Boundary

Until real system access is connected, this repo can truthfully claim:

- `Implemented`: local ledger, planning engine, CLI, dashboard, tests, CI workflow.
- `Locally verified`: only after `python -m unittest discover -s tests` and a CLI proof path pass.
- `Unknown`: live inventory accuracy, source-system parity, vendor integration, employee time saved, and business outcome impact.

Do not claim production reliability, cost savings, complete automation, or "bulletproof" behavior until live source data is connected and proof artifacts exist.

## Public Positioning

If this repo is public, describe it as:

> A defensible local inventory proof harness for ledger-backed stock tracking, ops alerts, and reorder planning.

Do not describe it as:

- a finished ERP
- guaranteed cost savings
- fully automated procurement
- production-verified inventory control
- foolproof or bulletproof automation

Those claims require live pilot evidence, source-system parity checks, and documented outcomes.
