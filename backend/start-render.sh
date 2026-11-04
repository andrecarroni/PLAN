#!/bin/sh
# Render Docker Command: /bin/sh /app/backend/start-render.sh
set -eu
cd /app/backend
python -m alembic upgrade head
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-10000}" --no-proxy-headers
