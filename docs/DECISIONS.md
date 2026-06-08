# Decisions

## 2026-06-08: Start With Stdlib Python And SQLite

Decision: build the first cloneable system with Python stdlib, SQLite, CLI, local dashboard, and GitHub Actions.

Why: the cowork terminal path should be low-friction and avoid dependency or account setup before inventory access exists.

Claim boundary: this proves the local ledger and planning workflow, not live business integration or admin cost savings.

## 2026-06-08: Ledger Is Source Of Truth

Decision: stock totals are computed from movements instead of stored as editable item fields.

Why: the proof rules require auditability and reproducibility. A hand-edited stock field would create dashboard drift and make inflow/outflow tracking impossible to verify.

