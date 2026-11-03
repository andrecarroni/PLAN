#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
umask 077
mkdir -p backups
chmod 700 backups
destination="backups/p4-$(date -u +%Y%m%dT%H%M%SZ).dump"
docker compose exec -T db pg_dump -U p4 -d p4 -Fc > "$destination"
test -s "$destination"
docker compose exec -T db pg_restore --list < "$destination" >/dev/null
printf 'Backup criado e catálogo verificado: %s\n' "$destination"
