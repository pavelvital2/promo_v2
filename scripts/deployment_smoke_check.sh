#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8080}"
PYTHON_BIN="${PYTHON_BIN:-python}"

"$PYTHON_BIN" manage.py check

health_json="$(curl -fsS "$BASE_URL/health/")"
case "$health_json" in
  *'"status": "ok"'*|*'"status":"ok"'*)
    echo "health_ok=$BASE_URL/health/"
    ;;
  *)
    echo "Unexpected health response: $health_json" >&2
    exit 1
    ;;
esac

echo "deployment_smoke=pass"
