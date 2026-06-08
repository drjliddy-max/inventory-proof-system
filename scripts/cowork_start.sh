#!/usr/bin/env bash
set -euo pipefail

DB_PATH="inventory.sqlite"
BRIEF_PATH=""
PORT="8787"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --db)
      DB_PATH="${2:?Missing value for --db}"
      shift 2
      ;;
    --brief)
      BRIEF_PATH="${2:?Missing value for --brief}"
      shift 2
      ;;
    --port)
      PORT="${2:?Missing value for --port}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

python3 -m unittest discover -s tests
python3 -m inventory_proof.cli --db "$DB_PATH" init

if [[ -n "$BRIEF_PATH" ]]; then
  if [[ ! -f "$BRIEF_PATH" ]]; then
    echo "Brief file does not exist: $BRIEF_PATH" >&2
    echo "Expected a markdown/text ops brief such as /path/to/ops/brain.md" >&2
    exit 1
  fi
  python3 -m inventory_proof.cli --db "$DB_PATH" import-ops-brief --file "$BRIEF_PATH"
  python3 -m inventory_proof.cli --db "$DB_PATH" ops-alerts
else
  python3 -m inventory_proof.cli --db "$DB_PATH" seed
  python3 -m inventory_proof.cli --db "$DB_PATH" alerts
fi

echo
echo "Inventory dashboard starting at http://127.0.0.1:$PORT"
echo "Press Ctrl+C to stop."
python3 -m inventory_proof.cli --db "$DB_PATH" dashboard --port "$PORT"
