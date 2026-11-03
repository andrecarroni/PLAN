#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
backup_file="${1:?Informe o caminho do backup .dump}"
test -s "$backup_file"
check_db="p4_restore_$(date -u +%Y%m%d%H%M%S)_${RANDOM}"
docker compose exec -T db createdb -U p4 "$check_db"
trap 'docker compose exec -T db dropdb -U p4 "$check_db"' EXIT
docker compose exec -T db pg_restore -U p4 -d "$check_db" --no-owner --exit-on-error < "$backup_file"
docker compose exec -T db psql -U p4 -d "$check_db" -c 'SELECT count(*) AS usuarios_restaurados FROM users; SELECT version_num FROM alembic_version;'
printf 'Restauração validada em banco temporário, sem substituir o banco da aplicação.\n'
