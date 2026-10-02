# Inventory Proof System Guardrails

> **This repository is PUBLIC on GitHub** (`drjliddy-max/inventory-proof-system`;
> code is All Rights Reserved, see `LICENSE`). Everything committed here is
> world-readable: no secrets, no credentials, no real customer, vendor, or
> employee data, no client names. Sample data only. Treat every commit message
> and doc as public copy (see "Public Exposure Rule" below).

Inherits `~/.claude/CLAUDE.md` (verification protocol, status taxonomy, success
vocabulary, AI-methodology triggers, secret rules) and the workspace rules in:

- `/Users/johnliddy/Desktop/Projects/CLAUDE.md` (includes the pre-share secret checks)
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
python3 -m unittest discover -s tests
python3 -m inventory_proof.cli --db /tmp/inventory-proof-check.sqlite seed
python3 -m inventory_proof.cli --db /tmp/inventory-proof-check.sqlite plan
git status --short
```

Then run the pre-share secret checks in `/Users/johnliddy/Desktop/Projects/CLAUDE.md`
("Security & demo/deploy gate"). They matter more here because the repo is public.

## Claim Language

Use the global status taxonomy (`~/.claude/CLAUDE.md`). Locally, `Production
verified` means live business source data confirms behavior, and `Proven` means a
reproducible proof artifact shows the business outcome.

Local rule: never say the system is foolproof, production-ready, or cost-saving until the corresponding proof level exists.

## Public Exposure Rule

This repo may be public only as a defensible proof harness. Public-facing language must make the current evidence level clear:

- Local code and tests are implemented.
- Sample studio ops brief import is locally verified.
- Live inventory access, source-system parity, and business savings are unknown until a pilot proves them.

Never use public copy that suggests bulletproof automation, guaranteed employment outcomes, guaranteed raises, guaranteed savings, or complete production readiness.
