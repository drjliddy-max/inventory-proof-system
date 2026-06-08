#!/usr/bin/env bash
set -euo pipefail

python3 --version
python3 -m unittest discover -s tests
python3 -m inventory_proof.cli init

cat <<'MSG'

Inventory Proof System is ready.

Next:
  python3 -m inventory_proof.cli seed
  python3 -m inventory_proof.cli dashboard

MSG

