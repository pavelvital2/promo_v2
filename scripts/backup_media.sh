#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/promo_v2/media}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
MEDIA_ROOT="${DJANGO_MEDIA_ROOT:-/var/lib/promo_v2/media}"

if [[ ! -d "$MEDIA_ROOT" ]]; then
  echo "MEDIA_ROOT does not exist: $MEDIA_ROOT" >&2
  exit 2
fi

mkdir -p "$BACKUP_DIR"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="$BACKUP_DIR/media_${timestamp}.tar.gz"
parent_dir="$(dirname "$MEDIA_ROOT")"
media_name="$(basename "$MEDIA_ROOT")"

tar -C "$parent_dir" -czf "$target" "$media_name"
test -s "$target"
find "$BACKUP_DIR" -type f -name "media_*.tar.gz" -mtime +"$RETENTION_DAYS" -delete

echo "media_backup=$target"
