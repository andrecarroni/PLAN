"""Use only the isolated p4_test PostgreSQL database."""
from pathlib import Path
import os,subprocess
root=Path(__file__).resolve().parents[1]
settings=dict(l.split('=',1) for l in (root/'.env').read_text().splitlines() if '=' in l and not l.startswith('#'))
env={**os.environ,'TEST_DATABASE_URL':f"postgresql+psycopg://p4:{settings['POSTGRES_PASSWORD']}@127.0.0.1:55432/p4_test"}
raise SystemExit(subprocess.call([str(root/'.venv/bin/python'),'-m','pytest','tests','-q'],cwd=root/'backend',env=env))
