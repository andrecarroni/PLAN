import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location(
    "p4_configure", Path(__file__).resolve().parents[2] / "scripts/configure.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_preserve_config_outside_checkout_and_restore(tmp_path):
    root = tmp_path / "checkout"
    root.mkdir()
    shared = tmp_path / "retained" / "config.env"
    module.configure(root, shared)
    original = (root / ".env").read_bytes()
    assert original == shared.read_bytes()
    (
        root / ".env"
    ).unlink()  # Simulates the cleanup observed after repository restoration.
    module.configure(root, shared)
    assert (root / ".env").read_bytes() == original


def test_configuration_conflict_does_not_overwrite(tmp_path):
    root = tmp_path / "checkout"
    root.mkdir()
    shared = tmp_path / "config.env"
    (root / ".env").write_text("POSTGRES_PASSWORD=fictitious-one\n")
    shared.write_text("POSTGRES_PASSWORD=fictitious-two\n")
    with pytest.raises(ValueError):
        module.configure(root, shared)
    assert "one" in (root / ".env").read_text() and "two" in shared.read_text()


def test_existing_local_configuration_is_not_regenerated(tmp_path):
    (tmp_path / ".env").write_text("POSTGRES_PASSWORD=fictitious-existing\n")
    module.configure(tmp_path)
    module.configure(tmp_path)
    assert (tmp_path / ".env").read_text() == "POSTGRES_PASSWORD=fictitious-existing\n"
