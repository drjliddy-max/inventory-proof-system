# Inventory Proof System Guardrails

This project inherits the workspace rules in:

- `/Users/johnliddy/Desktop/Projects/CLAUDE.md`
- `/Users/johnliddy/Desktop/Projects/PORTFOLIO_DOCTRINE.md`
- `/Users/johnliddy/Desktop/Projects/PORTFOLIO_AI_DEVELOPMENT.md`
- `/Users/johnliddy/Desktop/Projects/MASTER_VISIBILITY_MATRIX.md`

## Project Role

This is a proof-oriented operations tool, not a marketing site. Its job is to reduce admin oversight by making inventory state, purchase timing, and required user actions auditable.

Operating loop:

`measure inventory -> diagnose risk -> recommend purchase/reconcile action -> record action -> verify stock truth -> prove admin reduction`

## Evidence Rules

- Stock on hand must be derived from movement records, not hand-edited dashboard values.
- Dashboard numbers must come from the same planning engine used by CLI/tests.
- Unknown source-system access must be represented as unknown, not as zero or complete.
- Cost-saving and employee-time-saving claims require before/after evidence.
- Reorder recommendations must expose the factors used: stock, daily usage, known demand, lead time, and safety stock.

## Development Rules

- Add or update tests for every inventory math, alerting, import, or planning change.
- Keep external integrations additive. Importers write ledger movements; they do not overwrite stock totals.
- Prefer reversible local changes until live inventory credentials and source data are granted.
- Do not commit `.env*`, `.vercel/`, API keys, vendor tokens, exported credentials, or raw customer files.

## Before Commit Or Share

Run:

```bash
python -m unittest discover -s tests
python -m inventory_proof.cli --db /tmp/inventory-proof-check.sqlite seed
python -m inventory_proof.cli --db /tmp/inventory-proof-check.sqlite plan
find . -maxdepth 3 \( -name '.env.local' -o -name '.env' -o -name '.vercel' \)
rg -n "VERCEL_|SENDGRID|SMTP_|API_KEY|TOKEN|SECRET" .
git status --short
```

## Claim Language

Use the portfolio trust stack:

- `Implemented`: code/config exists.
- `Locally verified`: tests or local proof path passed.
- `Production verified`: live business source data confirms behavior.
- `Proven`: reproducible proof artifact shows the business outcome.

Never say the system is foolproof, production-ready, or cost-saving until the corresponding proof level exists.

## Public Exposure Rule

This repo may be public only as a defensible proof harness. Public-facing language must make the current evidence level clear:

- Local code and tests are implemented.
- Sample studio ops brief import is locally verified.
- Live inventory access, source-system parity, and business savings are unknown until a pilot proves them.

Never use public copy that suggests bulletproof automation, guaranteed employment outcomes, guaranteed raises, guaranteed savings, or complete production readiness.
