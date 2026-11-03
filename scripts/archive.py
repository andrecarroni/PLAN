"""Export only committed source. Secrets, databases and dependencies are not included."""

from pathlib import Path
import hashlib, json, subprocess, sys

root = Path(__file__).resolve().parents[1]
output = (
    Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else root.parent / "p4-entrega"
)
output.mkdir(parents=True, exist_ok=True)
sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
zip_path = output / "p4-consultores-codigo.zip"
bundle_path = output / "p4-consultores-historico.bundle"
subprocess.run(
    ["git", "archive", "--format=zip", "--output", str(zip_path), "HEAD"],
    cwd=root,
    check=True,
)
subprocess.run(
    ["git", "bundle", "create", str(bundle_path), "HEAD"], cwd=root, check=True
)
manifest = {
    "commit": sha,
    "files": {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [zip_path, bundle_path]
    },
}
(output / "manifesto.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(
    "Código e histórico exportados sem .env, banco de dados ou dependências: "
    + str(output)
)
