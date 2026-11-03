"""Create local development configuration and optionally preserve it outside the checkout."""

from pathlib import Path
import os, secrets


def configure(root: Path, shared: Path | None = None):
    local = root / ".env"
    if shared is not None:
        shared = shared.resolve()
        if shared == local.resolve():
            shared = None
    if (
        shared
        and shared.exists()
        and local.exists()
        and shared.read_bytes() != local.read_bytes()
    ):
        raise ValueError(
            "A configuração local difere da cópia preservada. Confira qual é a correta antes de continuar; nenhum arquivo foi sobrescrito."
        )
    if not local.exists():
        local.write_bytes(
            shared.read_bytes()
            if shared and shared.exists()
            else (
                "POSTGRES_PASSWORD=" + secrets.token_hex(32) + "\nAPP_ENV=development\n"
            ).encode()
        )
        local.chmod(0o600)
    if shared and not shared.exists():
        shared.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        shared.write_bytes(local.read_bytes())
        shared.chmod(0o600)
    return local


def main():
    root = Path(__file__).resolve().parents[1]
    try:
        configure(
            root,
            Path(os.environ["P4_CONFIG_FILE"]) if os.getenv("P4_CONFIG_FILE") else None,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
    print("Configuração local disponível e preservada, sem exibir credenciais.")


if __name__ == "__main__":
    main()
