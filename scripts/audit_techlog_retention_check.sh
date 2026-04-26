#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"

"$PYTHON_BIN" manage.py cleanup_audit_techlog --dry-run

if [[ "${APPLY_CLEANUP:-0}" == "1" ]]; then
  "$PYTHON_BIN" manage.py cleanup_audit_techlog
fi
