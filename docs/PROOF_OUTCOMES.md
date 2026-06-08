# Proof Outcomes Contract

## Business Purpose

Reduce employee time spent manually tracking inventory while improving purchase timing and inventory reliability.

## Required Outcomes

| Outcome | Evidence Required | Current Status |
| --- | --- | --- |
| Accurate inventory totals | Stock calculated from auditable movement ledger | Implemented locally |
| Inflows and outflows tracked | Movement rows include type, quantity, reason, ref, timestamp | Implemented locally |
| Advance purchase knowledge | Reorder plan uses usage rate, calendar demand, lead time, safety stock | Implemented locally |
| User action alerts | Alerts identify order-now, order-soon, and watch conditions | Implemented locally |
| Studio ops exceptions | Brief importer flags LOW/OUT supplies and held pallet orders with source lines | Implemented locally |
| Reduced admin oversight | Before/after employee time study and exception rate | Unknown until live pilot |
| Live business reliability | Source-system importer, parity checks, operator reconciliation | Unknown until access granted |

## Proof Rules

1. Every dashboard value must be reproducible from the SQLite ledger.
2. Every recommendation must expose its inputs.
3. Every live integration must preserve source IDs in movement references.
4. Every production claim must include a timestamped proof artifact.
5. Any missing connector, failed import, or ambiguous value is `UNKNOWN`, not zero.

## Public Claim Boundary

Public exposure is allowed only if the system is represented as a proof harness, not a proven business outcome.

Allowed now:

- Local ledger-backed inventory tracking.
- Local dashboard and CLI.
- Studio-style ops brief importer.
- Source-line-backed alerts for LOW/OUT supplies and held orders.
- CI and regression tests.

Not allowed yet:

- "Bulletproof" automation.
- Guaranteed reduction in employee oversight.
- Guaranteed admin cost savings.
- Live inventory accuracy.
- Production-ready procurement automation.
- Any claim that the system has already protected a job, earned a raise, or delivered company-wide operational savings.

Promotion from local proof to production proof requires a pilot with real source files, before/after admin-time tracking, reconciliation exceptions, and dated proof artifacts.

## Pilot Proof Plan

1. Capture baseline manual process: time spent, error rate, stockout incidents, emergency purchases.
2. Import or enter real opening inventory through ledger movements.
3. Run the system for one purchasing cycle.
4. Compare recommendations against actual usage and purchase lead times.
5. Record exceptions: missing data, source drift, manual overrides, late purchases.
6. Promote claims only after the evidence supports them.
