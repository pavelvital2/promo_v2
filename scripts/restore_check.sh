#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <postgres_dump> <media_tar_gz>" >&2
  echo "Optional: set RESTORE_DB to execute pg_restore into a non-production database." >&2
  exit 2
fi

postgres_dump="$1"
media_backup="$2"
POSTGRES_HOST="${POSTGRES_HOST:-127.0.0.1}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-promo_v2}"

if [[ -z "${POSTGRES_PASSWORD:-}" ]]; then
  echo "POSTGRES_PASSWORD is required" >&2
  exit 2
fi

test -s "$postgres_dump"
test -s "$media_backup"

PGPASSWORD="$POSTGRES_PASSWORD" pg_restore --list "$postgres_dump" >/dev/null
tar -tzf "$media_backup" >/dev/null

if [[ -n "${RESTORE_DB:-}" ]]; then
  if [[ "$RESTORE_DB" == "${POSTGRES_DB:-promo_v2}" ]]; then
    echo "RESTORE_DB must not be the production POSTGRES_DB" >&2
    exit 2
  fi
  PGPASSWORD="$POSTGRES_PASSWORD" createdb \
    --host="$POSTGRES_HOST" \
    --port="$POSTGRES_PORT" \
    --username="$POSTGRES_USER" \
    "$RESTORE_DB"
  PGPASSWORD="$POSTGRES_PASSWORD" pg_restore \
    --host="$POSTGRES_HOST" \
    --port="$POSTGRES_PORT" \
    --username="$POSTGRES_USER" \
    --dbname="$RESTORE_DB" \
    --no-owner \
    "$postgres_dump"
  echo "restore_db=$RESTORE_DB"
fi

echo "restore_check=backup_archives_readable"
