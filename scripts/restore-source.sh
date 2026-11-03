#!/usr/bin/env bash
# Recover from the local, verified delivery bundle without network access or force resets.
set -euo pipefail
checkout="${1:-/workspace/PLAN}"
delivery="${2:-/workspace/p4-entrega}"
if test -f "$checkout/backend/app/main.py" && test -f "$checkout/frontend/src/main.tsx"; then
    printf 'Código da aplicação presente; nenhuma restauração foi aplicada.\n'
    exit 0
fi
git -C "$checkout" diff --quiet
git -C "$checkout" diff --cached --quiet
initial_head="$(git -C "$checkout" rev-parse HEAD)"
if test "$initial_head" != 'c3de39e5d63bba81326e0168fffd898f70c89c1b'; then
    printf 'Checkout incompleto em uma versão diferente da inicial. Preserve o trabalho e revise manualmente; nenhum arquivo foi substituído.\n' >&2
    exit 1
fi
expected_commit="$(python3 - "$delivery" <<'PY'
from pathlib import Path
import sys,json,hashlib
root=Path(sys.argv[1]);m=json.loads((root/'manifesto.json').read_text())
for name,expected in m['files'].items():
    if name not in ('p4-consultores-codigo.zip','p4-consultores-historico.bundle'):raise SystemExit('Arquivo inesperado no manifesto.')
    if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:raise SystemExit('Cópia local não passou na verificação de integridade.')
print(m['commit'])
PY
)"
git -C "$checkout" bundle verify "$delivery/p4-consultores-historico.bundle"
git -C "$checkout" fetch "$delivery/p4-consultores-historico.bundle" HEAD
actual_commit="$(git -C "$checkout" rev-parse FETCH_HEAD)"
test "$expected_commit" = "$actual_commit"
# Git refuses to overwrite conflicting untracked work; never add --force here.
git -C "$checkout" switch --detach "$actual_commit"
printf 'Código restaurado do bundle local verificado. Nenhum envio remoto foi realizado.\n'
