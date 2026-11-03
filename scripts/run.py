"""Run backend modules using the local development database without printing secrets."""

import os, sys, subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
settings = dict(
    l.split("=", 1)
    for l in (root / ".env").read_text().splitlines()
    if "=" in l and not l.startswith("#")
)
env = {
    **os.environ,
    "DATABASE_URL": f"postgresql+psycopg://p4:{settings['POSTGRES_PASSWORD']}@127.0.0.1:55432/p4",
    "FRONTEND_DIST": str(root / "frontend/dist"),
}
if len(sys.argv) > 1:
    args = sys.argv[1:]
else:
    args = [
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--no-proxy-headers",
    ]
raise SystemExit(
    subprocess.call(
        [str(root / ".venv/bin/python"), "-m", *args], cwd=root / "backend", env=env
    )
)
