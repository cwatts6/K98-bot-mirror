"""The same reviewed metadata must work in a checkout and sealed source bundle."""

import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from services import export_contract_resources as resources
from services.export_execution_dal import application_activation_scope
from services.export_sql_direct_permissions import application_grant_rows

ROOT = Path(__file__).resolve().parents[1]
NAMES = ("s11_activation_scope.json", "s11_application_grants.json")


@pytest.mark.parametrize("name", NAMES)
def test_checkout_reads_exact_committed_bytes(name):
    assert resources.read_contract_resource(name) == (ROOT / "deploy" / name).read_bytes()


@pytest.mark.parametrize("name", ["../s11_activation_scope.json", "config.json", "", None, []])
def test_unknown_resource_is_refused_before_io(monkeypatch, name):
    class Loader:
        def get_data(self, path):
            pytest.fail("Invalid resource reached the loader")

    monkeypatch.setattr(resources, "__loader__", Loader())
    with pytest.raises(ValueError, match="Exact deployment contract"):
        resources.read_contract_resource(name)


@pytest.mark.parametrize(
    "data", [b"", b"x" * (1024 * 1024 + 1), "not bytes"], ids=["empty", "oversized", "wrong-type"]
)
def test_invalid_resource_bytes_are_refused(monkeypatch, data):
    class Loader:
        def get_data(self, path):
            return data

    monkeypatch.setattr(resources, "__loader__", Loader())
    with pytest.raises(ValueError, match="Bounded deployment contract bytes"):
        resources.read_contract_resource(NAMES[0])


def test_unsupported_loader_has_no_filesystem_fallback(monkeypatch):
    monkeypatch.setattr(resources, "__loader__", object())
    with pytest.raises(ValueError, match="import source cannot read"):
        resources.read_contract_resource(NAMES[0])


@pytest.mark.parametrize("broken", [None, "missing_scope", "changed_grants"])
def test_actual_contract_readers_from_isolated_zip(tmp_path, broken):
    archive = tmp_path / "reviewed-verifier.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as bundle:
        # Exercise actual imports in a fresh isolated interpreter, not a mocked
        # loader or a process that already imported the working-tree modules.
        for package in ("services", "kvk"):
            for path in sorted((ROOT / package).rglob("*.py")):
                bundle.writestr(path.relative_to(ROOT).as_posix(), path.read_bytes())
        for name in NAMES:
            raw = (ROOT / "deploy" / name).read_bytes()
            # A valid adjacent loose copy must never rescue a missing/bad bundle.
            loose = tmp_path / "deploy" / name
            loose.parent.mkdir(exist_ok=True)
            loose.write_bytes(raw)
            if broken == "missing_scope" and name == NAMES[0]:
                continue
            if broken == "changed_grants" and name == NAMES[1]:
                raw = b"{}"
            bundle.writestr("deploy/" + name, raw)
    program = """
import json, sys
sys.path.insert(0, sys.argv[1])
from services import export_contract_resources as resources
from services import export_execution_dal as dal
from services import export_sql_direct_permissions as permissions
assert all(module.__file__.startswith(sys.argv[1]) for module in (resources, dal, permissions))
print(json.dumps(dict(scope=dal.application_activation_scope(), grants=permissions.application_grant_rows())))
"""
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", program, str(archive)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if broken is None:
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout) == dict(
            scope=application_activation_scope(), grants=application_grant_rows()
        )
    else:
        assert result.returncode != 0
        assert not result.stdout
        if broken == "changed_grants":
            assert "Reviewed application grant source differs" in result.stderr


def test_historical_test_bridge_refuses_unreviewed_source(tmp_path):
    from tests.updater_source_assertions import before_contract_resource_hash

    member = "services/export_contract_resources.py"
    assert before_contract_resource_hash(ROOT, member) is None
    fixture = "tests/fixtures/updater_contract_resource_pairs.json"
    (tmp_path / fixture).parent.mkdir(parents=True)
    (tmp_path / fixture).write_bytes((ROOT / fixture).read_bytes())
    (tmp_path / member).parent.mkdir(parents=True)
    (tmp_path / member).write_bytes(b"unreviewed resource reader")
    with pytest.raises(AssertionError):
        before_contract_resource_hash(tmp_path, member)
