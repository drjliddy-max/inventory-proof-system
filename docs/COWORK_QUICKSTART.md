# Cowork Quickstart

Copy this into the local terminal after cloning the repo.

## Demo Mode

Use this when real inventory files are not available yet.

```bash
cd inventory-proof-system
./scripts/cowork_start.sh
```

Open `http://127.0.0.1:8787`.

## Real Ops Brief Mode

Use this when the local ops folder exists.

```bash
cd inventory-proof-system
./scripts/cowork_start.sh --brief /path/to/ops/brain.md
```

The script will:

- run tests
- initialize SQLite
- import the ops brief
- print immediate supply/order alerts
- start the dashboard

## First Checks

Confirm the dashboard shows:

- LOW/OUT supplies
- held orders
- pallet/crate restrictions
- no fake stock counts for quantity-less statuses

## Promise Boundary

This system is locally verified when tests pass and the dashboard reflects imported source data. It is production-proven only after real inventory files, order exports, and reconciliation evidence are connected.
