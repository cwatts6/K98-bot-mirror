"""Installed recovery policy accepts only its reviewed source/SQL transition."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess

import pytest

from scripts import p0a_release as recovery, prepare_k98_update as updater
from tests.test_recovery_release_seed import seed_fixture


def synthetic_policy(monkeypatch):
    blobs = {
        ("a" * 40, "core/export_execution_host.py"): b"old\n",
        ("b" * 40, "core/export_execution_host.py"): b"new\n",
        ("b" * 40, "services/export_recovery_service.py"): b"recovery\n",
    }
    spec = dict(
        before="a" * 40,
        sources=[
            dict(
                path=path,
                before=recovery.sha(blobs["a" * 40, path]) if ("a" * 40, path) in blobs else None,
                after=recovery.sha(blobs["b" * 40, path]),
            )
            for path in ("core/export_execution_host.py", "services/export_recovery_service.py")
        ],
    )
    monkeypatch.setattr(recovery, "specification", lambda: deepcopy(spec))
    monkeypatch.setattr(updater, "coordinated_policy", lambda: recovery)
    return spec, blobs


def test_exact_transition_preserves_source_policy_and_line_conventions(monkeypatch):
    spec, blobs = synthetic_policy(monkeypatch)
    previous = {
        "AutomaticStartupPolicy.json": {
            "source_hashes": {"core/export_execution_host.py": recovery.sha(b"old\r\n")}
        }
    }
    plan, payload = updater.source_plan(
        previous,
        spec["before"],
        "b" * 40,
        [r["path"] for r in spec["sources"]],
        lambda *key: blobs.get(key),
    )
    assert payload["core/export_execution_host.py"] == b"new\r\n"
    assert payload["services/export_recovery_service.py"] == b"recovery\n"
    assert plan["new_pins"] == {p: recovery.sha(b) for p, b in payload.items()}
    assert previous["AutomaticStartupPolicy.json"]["source_hashes"][
        "core/export_execution_host.py"
    ] == recovery.sha(b"old\r\n")


@pytest.mark.parametrize(
    "damage", ["partial", "wrong_predecessor", "old_drift", "new_drift", "extra_protected"]
)
def test_source_exceptions_do_not_admit_another_transition(monkeypatch, damage):
    spec, blobs = synthetic_policy(monkeypatch)
    changes = [r["path"] for r in spec["sources"]]
    before = spec["before"]
    if damage == "partial":
        changes.pop()
    elif damage == "wrong_predecessor":
        before = "c" * 40
    elif damage == "old_drift":
        blobs[before, changes[0]] = b"different old\n"
    elif damage == "new_drift":
        blobs["b" * 40, changes[0]] = b"different new\n"
    else:
        changes.append("core/export_process_identity.py")
    with pytest.raises(ValueError):
        updater.source_plan(
            {"AutomaticStartupPolicy.json": {"source_hashes": {}}},
            before,
            "b" * 40,
            changes,
            lambda *key: blobs.get(key),
        )


def payload_fixture():
    spec = recovery.specification()
    files = {r["path"]: (r["path"] + "\n").encode() for r in spec["sql"]["members"]}
    for row in spec["sql"]["members"]:
        row["sha256"] = recovery.sha(files[row["path"]])
    for row in spec["sql"]["profile"]["scripts"]:
        row["sha256"] = recovery.sha(files["migrations/" + row["id"] + ".sql"])
    old = spec["contracts"]["sql_contract"]["before"]
    environment = dict(
        server=old["server"],
        database=old["database"],
        database_collation=old["collation"],
        tempdb_collation="Latin1_General_CI_AS",
        compatibility_level=160,
    )
    return spec, environment, files


def test_sql_package_binds_ambient_environment_without_learning_images():
    spec, environment, files = payload_fixture()
    original = deepcopy(spec)
    bindings, payload = recovery.sql_payload(spec, environment, files.get)
    assert spec == original
    assert len(payload) == 5
    profile = json.loads(payload[bindings["profiles"][0]["file"]])
    assert profile["images"] == spec["sql"]["profile"]["images"]
    assert profile["requires"] == spec["sql"]["profile"]["requires"]
    assert all(recovery.sha(payload[row["name"]]) == row["sha256"] for row in bindings["members"])
    assert profile["compatibility_level"] == environment["compatibility_level"]


@pytest.mark.parametrize("row_count", [0, 1, 2])
def test_native_updater_environment_serialization(tmp_path, row_count):
    powershell = Path("C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")
    if not powershell.exists():
        pytest.skip("Windows PowerShell 5.1 observation boundary qualification")
    spec, environment, files = payload_fixture()
    fixture = tmp_path / "environment.json"
    fixture.write_text(json.dumps({"rows": [environment] * row_count}), encoding="utf-8")
    result = subprocess.run(
        [
            str(powershell),
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(Path(__file__).resolve().parents[1] / "scripts/Test-K98SqlEnvironment.ps1"),
            "-FixturePath",
            str(fixture),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if row_count != 1:
        assert result.returncode != 0
        assert "Complete SQL environment observation required" in result.stderr
        return
    assert result.returncode == 0, result.stderr
    observed = json.loads(result.stdout)["bindings"]["sql_environment"]
    assert observed == environment
    bindings, payload = recovery.sql_payload(spec, observed, files.get)
    profile = json.loads(payload[bindings["profiles"][0]["file"]])
    assert profile["compatibility_level"] == environment["compatibility_level"]


@pytest.mark.parametrize("shape", [None, [], [{}], "environment", 1])
def test_sql_package_rejects_non_object_environment_before_reading_payload(shape):
    spec, _, _ = payload_fixture()

    def unexpected_read(path):
        pytest.fail("Malformed environment must be refused before reading SQL payload")

    with pytest.raises(ValueError, match="Complete fresh SQL environment observation"):
        recovery.sql_payload(spec, shape, unexpected_read)


@pytest.mark.parametrize("key", ["server", "database", "database_collation", "tempdb_collation"])
@pytest.mark.parametrize("value", [None, 1, [], {}])
def test_sql_package_rejects_non_string_environment_values(key, value):
    spec, environment, files = payload_fixture()
    environment[key] = value
    with pytest.raises(ValueError, match="must be strings"):
        recovery.sql_payload(spec, environment, files.get)


@pytest.mark.parametrize(
    "damage",
    [
        "server",
        "database",
        "database_collation",
        "missing",
        "compatibility",
        "bad_type",
        "tempdb",
        "sql_bytes",
        "missing_sql",
    ],
)
def test_sql_package_refuses_foreign_environment_or_unreviewed_bytes(damage):
    spec, environment, files = payload_fixture()
    if damage in ("server", "database", "database_collation"):
        environment[damage] = "other"
    elif damage == "missing":
        environment.pop("tempdb_collation")
    elif damage == "compatibility":
        environment["compatibility_level"] = 100
    elif damage == "bad_type":
        environment["compatibility_level"] = "160"
    elif damage == "tempdb":
        environment["tempdb_collation"] = "SQL;"
    elif damage == "sql_bytes":
        files[next(iter(files))] += b"drift"
    else:
        files.pop(next(iter(files)))
    with pytest.raises(ValueError):
        recovery.sql_payload(spec, environment, files.get)


@pytest.mark.parametrize(
    "damage", ["commit", "partial", "duplicate", "script_hash", "script_member", "receipt", "image"]
)
def test_installed_sql_policy_requires_complete_consistent_inventory(damage):
    sql = recovery.specification()["sql"]
    if damage == "commit":
        sql["commit"] = "main"
    elif damage == "partial":
        sql["members"].pop()
    elif damage == "duplicate":
        sql["members"][-1] = sql["members"][0]
    elif damage == "script_hash":
        sql["profile"]["scripts"][0]["sha256"] = "f" * 64
    elif damage == "script_member":
        sql["members"][0]["path"] = "deploy/unreviewed.ps1"
    elif damage == "receipt":
        sql["profile"]["requires"][0]["status"] = "Failed"
    else:
        sql["profile"]["images"][0]["before"] = ""
    with pytest.raises(ValueError):
        recovery.validate_sql_policy(sql)


def test_candidate_preserves_old_evidence_until_actual_observation(monkeypatch):
    seed, _, bot, _ = seed_fixture(monkeypatch)
    spec = dict(
        contracts={
            key: dict(before=deepcopy(bot[key]), after={**bot[key], "reviewed_successor": True})
            for key in ("sql_contract", "legacy_sql_contract", "application_sql_contract")
        }
    )
    seed["authority-template.json"] = recovery.encode(
        {**json.loads(seed["authority-template.json"]), "sql_contract": bot["sql_contract"]}
    )
    original = deepcopy(seed)
    adapted = recovery.adapt_candidate(seed, spec)
    assert seed == original
    assert adapted["sql_installation.json"] == seed["sql_installation.json"]
    policy = json.loads(adapted["AutomaticStartupPolicy.json"])
    old_policy = json.loads(seed["AutomaticStartupPolicy.json"])
    assert {k: v for k, v in policy.items() if k != "seed_plan"} == {
        k: v for k, v in old_policy.items() if k != "seed_plan"
    }
    assert all(
        json.loads(adapted["bot-template.json"])[k] == p["after"]
        for k, p in spec["contracts"].items()
    )
    # A prior observation is intentionally not successor installation evidence.
    assert adapted["sql_installation.json"] == original["sql_installation.json"]
    spec["contracts"]["sql_contract"]["before"]["database"] = "foreign"
    with pytest.raises(ValueError, match="predecessor SQL contract"):
        recovery.adapt_candidate(seed, spec)


def test_reviewed_source_inventory_matches_current_runtime():
    root = Path(__file__).resolve().parents[1]
    expected = {row["path"]: row["after"] for row in recovery.specification()["sources"]}
    # P0a's original pins remain immutable. Later source releases may install a
    # complete reviewed successor chain; intermediate images no longer need to
    # be installed. Every bundle must match its known predecessor pins; members
    # introduced after P0a join the complete bundle's final-image check below.
    # Never learn expected hashes from the live checkout.
    for transition in updater.reviewed_transitions():
        members = transition["members"]
        if any(m["path"] in expected for m in members) and all(
            m["path"] not in expected or expected[m["path"]] == m["before_sha256"] for m in members
        ):
            expected.update({m["path"]: m["after_sha256"] for m in members})
    for relative, checksum in expected.items():
        path = root / relative
        assert recovery.sha(path.read_bytes().replace(b"\r\n", b"\n")) == checksum, relative


def test_compatibility_requires_complete_installed_coordinated_tool(monkeypatch):
    from scripts import validate_k98_update_compatibility as compatibility

    spec, blobs = synthetic_policy(monkeypatch)
    monkeypatch.setattr(compatibility, "coordinated_policy", lambda: recovery)
    paths = [row["path"] for row in spec["sources"]]
    root = Path(__file__).resolve().parents[1]
    installed = dict(
        version=1,
        files={
            Path(p).name: recovery.sha((root / p).read_bytes().replace(b"\r\n", b"\n"))
            for p in updater.TOOL_SOURCE_PATHS
        },
    )
    installed["files"]["EmptyGitConfig.txt"] = recovery.sha(b"")

    def classify():
        return compatibility.classify(
            spec["before"], "b" * 40, paths, lambda *key: blobs.get(key), installed
        )

    assert classify()["classification"] == "COORDINATED_COMPATIBLE"
    installed["files"]["p0a_release_spec.json"] = "f" * 64
    assert classify()["classification"] == "UPDATER_UPGRADE_REQUIRED"
    for name in ("p0a_release.py", "p0a_release_spec.json", "recovery_release_seed.py"):
        installed["files"].pop(name)
    assert classify()["classification"] == "UPDATER_UPGRADE_REQUIRED"


def test_closeout_release_requires_credential_corrected_predecessor():
    spec = recovery.specification()
    assert spec["before"] == "c349802b51686d649d3beeac43e7ef61b3b7f825"
    paths = {row["path"] for row in spec["sources"]}
    assert recovery.possible_paths(spec["before"], paths) == paths
    assert not recovery.possible_paths("a7519e453e0582cd54eee3847af25e1fad0d31a6", paths)
    assert "services/export_startup_reconciliation.py" not in paths
