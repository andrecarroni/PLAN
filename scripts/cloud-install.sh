#!/usr/bin/env bash
set -euo pipefail
cd /workspace/PLAN
# The checkout is already isolated. Do not create a worktree or reset source files.
test -f backend/requirements.lock || { echo 'Código incompleto: restaure o ZIP/bundle da reconstrução antes de instalar.' >&2; exit 1; }
python3 -m venv .venv
.venv/bin/python -m pip install --index-url https://pypi.org/simple -r backend/requirements.lock
npm ci --prefix frontend --cache /tmp/p4-npm --no-audit --no-fund
npm run build --prefix frontend
export P4_CONFIG_FILE="${P4_CONFIG_FILE:-/workspace/shared/p4-consultores/config.env}"
python3 scripts/configure.py
docker compose up -d --wait db
python3 scripts/run.py alembic upgrade head
python3 scripts/run.py app.cli seed-course
