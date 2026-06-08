# Operator Runbook

## Local Verification

```bash
python -m unittest discover -s tests
python -m inventory_proof.cli --db /tmp/inventory-proof-check.sqlite seed
python -m inventory_proof.cli --db /tmp/inventory-proof-check.sqlite plan
python -m inventory_proof.cli --db /tmp/inventory-proof-check.sqlite alerts
```

## Start Dashboard

```bash
python -m inventory_proof.cli seed
python -m inventory_proof.cli dashboard
```

Open `http://127.0.0.1:8787`.

## Daily Operator Flow

1. Record new purchases as `inflow`.
2. Record usage, sales, waste, or transfers as `outflow`.
3. Enter known future demand as `demand`.
4. Review `alerts`.
5. Create purchase orders for `ORDER_NOW` items.
6. Physically count high-risk SKUs and reconcile differences.

## Integration Rule

When real inventory access is granted, create importers that append movements with stable source references. Do not replace the ledger total with a vendor total unless it is recorded as a reconciliation with evidence.

## Escalation Conditions

- Dashboard shows `WATCH` for a fast-moving item.
- Stock count differs from physical count.
- An outflow is blocked because it would create negative stock.
- Reorder alert conflicts with operator knowledge.
- Source importer cannot prove which records were already imported.

