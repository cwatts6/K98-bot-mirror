"""Real sealed SQL/source policy transport; never connects to SQL or an updater host."""

from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

from scripts import p0a_release as policy, prepare_k98_update as updater


@pytest.fixture
def release():
    source = os.environ.get("K98_OBSERVER_SQL_SOURCE")
    if not source:
        pytest.skip("Explicit observer SQL source worktree required; no database connection")
    root = Path(source)
    migration = policy.OBSERVER_MIGRATION
    profile_raw = (root / "migrations" / (migration + ".release.json")).read_bytes()
    assert policy.sha(profile_raw) == policy.OBSERVER_PROFILE_SHA256
    names = [
        "deploy/" + name
        for name in (
            "Deploy-SqlMigration.ps1",
            "SqlDeploy.ModuleRelease.ps1",
            "SqlDeploy.P02D4Release.ps1",
            "SqlDeploy.Phase1Release.ps1",
            "SqlDeploy.P02ObserverRelease.ps1",
        )
    ]
    names += [
        "migrations/" + migration + suffix
        for suffix in (".sql", ".release.json", ".before.sql", ".after.sql")
    ]
    files = {name: (root / name).read_bytes() for name in names}
    profile = json.loads(profile_raw)
    target = dict(server="MINI_AMD", database="ROK_TRACKER", principal="app")
    fixed = dict(target, version=4, profile="application", collation=profile["database_collation"])
    contracts = {"sql_contract": dict(before=deepcopy(fixed), after=deepcopy(fixed))}
    for name in ("legacy_sql_contract", "application_sql_contract"):
        contracts[name] = dict(
            before=deepcopy(target), after=dict(target, observer_installation=migration)
        )
    blobs = {
        ("a" * 40, "services/export_runtime_composition.py"): b"old\n",
        ("b" * 40, "services/export_runtime_composition.py"): b"new\n",
        ("b" * 40, "services/observer_release_issuance.py"): b"issuer\n",
    }
    spec = dict(
        version=1,
        before="a" * 40,
        contracts=contracts,
        sources=[
            dict(
                path=path,
                before=policy.sha(blobs["a" * 40, path]) if ("a" * 40, path) in blobs else None,
                after=policy.sha(blobs["b" * 40, path]),
            )
            for path in (
                "services/export_runtime_composition.py",
                "services/observer_release_issuance.py",
            )
        ],
        sql=dict(
            commit="c" * 40,
            profile=profile,
            members=[dict(path=n, sha256=policy.sha(raw)) for n, raw in sorted(files.items())],
        ),
    )
    environment = dict(
        server=target["server"],
        database=target["database"],
        **{
            key: profile[key]
            for key in ("database_collation", "tempdb_collation", "compatibility_level")
        },
    )
    return spec, files, environment, blobs


def installed(monkeypatch, tmp_path, value):
    (tmp_path / "p0a_release_spec.json").write_text(json.dumps(value), encoding="utf-8")
    monkeypatch.setattr(policy, "__file__", str(tmp_path / "p0a_release.py"))
    monkeypatch.setattr(updater, "coordinated_policy", lambda: policy)


def test_exact_sql_profile_and_transitive_runner_members_survive_payload(release):
    spec, files, environment, _ = release
    original = deepcopy(spec)
    policy.validate_specification(spec)
    binding, payload = policy.sql_payload(spec, environment, files.get)
    assert spec == original
    assert len(payload) == 9
    profile = binding["profiles"][0]
    assert profile["sha256"] == policy.OBSERVER_PROFILE_SHA256
    assert payload[profile["file"]] == files["migrations/" + profile["file"]]
    assert all(policy.sha(payload[row["name"]]) == row["sha256"] for row in binding["members"])
    assert json.loads(payload[profile["file"]]) == spec["sql"]["profile"]


def test_installed_two_release_selection_preserves_legacy_and_exact_source_pins(
    release, tmp_path, monkeypatch
):
    legacy = policy.specification()
    spec, _, _, blobs = release
    installed(monkeypatch, tmp_path, dict(version=2, releases=[legacy, spec]))
    assert policy.selected_specification(legacy["before"]) == legacy
    assert policy.selected_specification("d" * 40) is None
    changes = [row["path"] for row in spec["sources"]]
    plan, payload = updater.source_plan(
        {"AutomaticStartupPolicy.json": {"source_hashes": {changes[0]: policy.sha(b"old\r\n")}}},
        spec["before"],
        "b" * 40,
        changes,
        lambda *key: blobs.get(key),
    )
    assert payload[changes[0]] == b"new\r\n"
    assert plan["new_pins"] == {path: policy.sha(raw) for path, raw in payload.items()}
    blobs["b" * 40, changes[1]] += b"drift"
    with pytest.raises(ValueError, match="Protected recovery source differs"):
        policy.selected(spec["before"], "b" * 40, changes, lambda *key: blobs.get(key))


def test_policy_disappearing_during_selection_stops_before_source_reads(release, monkeypatch):
    spec, _, _, _ = release
    selections = iter([spec, None])
    monkeypatch.setattr(policy, "selected_specification", lambda before: next(selections))
    reads = []
    with pytest.raises(ValueError, match="policy changed during selection"):
        policy.selected(
            spec["before"],
            "b" * 40,
            [row["path"] for row in spec["sources"]],
            lambda *key: reads.append(key),
        )
    assert reads == []


@pytest.mark.parametrize(
    "damage",
    [
        "missing_d4",
        "missing_phase1",
        "duplicate",
        "profile_hash",
        "script_hash",
        "migration",
        "history",
        "issued_identity",
        "contract_target",
        "partial_sources",
        "duplicate_predecessor",
    ],
)
def test_invalid_installed_observer_policies_are_refused(release, tmp_path, monkeypatch, damage):
    spec, _, _, _ = release
    if damage in ("missing_d4", "missing_phase1"):
        missing = "P02D4Release.ps1" if damage == "missing_d4" else "Phase1Release.ps1"
        spec["sql"]["members"] = [
            r for r in spec["sql"]["members"] if not r["path"].endswith(missing)
        ]
    elif damage == "duplicate":
        spec["sql"]["members"][-1] = spec["sql"]["members"][0]
    elif damage == "profile_hash":
        next(r for r in spec["sql"]["members"] if r["path"].endswith(".release.json"))["sha256"] = (
            "e" * 64
        )
    elif damage == "script_hash":
        spec["sql"]["profile"]["script"]["sha256"] = "e" * 64
    elif damage == "migration":
        spec["sql"]["profile"]["migration_id"] = "20261120_002_other"
    elif damage == "history":
        spec["sql"]["profile"]["requires"][0]["status"] = "Started"
    elif damage == "issued_identity":
        spec["contracts"]["application_sql_contract"]["after"]["observation_installation"] = {}
    elif damage == "contract_target":
        spec["contracts"]["application_sql_contract"]["after"]["principal"] = "other"
    elif damage == "partial_sources":
        spec["sources"] = []
    if damage == "duplicate_predecessor":
        spec = dict(version=2, releases=[spec, deepcopy(spec)])
    installed(monkeypatch, tmp_path, spec)
    with pytest.raises(ValueError):
        policy.specification()


@pytest.mark.parametrize(
    "damage",
    [
        "profile_newline",
        "changed_runner",
        "changed_check",
        "profile_reencode",
        "profile_object",
        "tempdb",
        "compatibility",
    ],
)
def test_payload_cannot_adopt_reencoded_profiles_or_live_environment(release, damage):
    spec, files, environment, _ = release
    name = "migrations/" + policy.OBSERVER_MIGRATION + ".release.json"
    if damage == "profile_newline":
        files[name] = files[name].replace(b"\n", b"\r\n")
    elif damage == "profile_reencode":
        files[name] = policy.encode(json.loads(files[name]))
    elif damage == "changed_runner":
        files["deploy/SqlDeploy.P02D4Release.ps1"] += b"# drift"
    elif damage == "changed_check":
        files["migrations/" + policy.OBSERVER_MIGRATION + ".after.sql"] += b"-- drift"
    elif damage == "profile_object":
        spec["sql"]["profile"]["protocol_sha256"] = "f" * 64
    elif damage == "tempdb":
        environment["tempdb_collation"] = "Latin1_General_CI_AS"
    else:
        environment["compatibility_level"] = 150
    with pytest.raises(ValueError):
        policy.sql_payload(spec, environment, files.get)


@pytest.mark.parametrize("damage", ["none", "missing_phase1", "resource_refusal"])
def test_assembled_payload_runs_actual_transitive_resource_check(release, tmp_path, damage):
    powershell = shutil.which("powershell")
    if not powershell:
        pytest.skip("Windows PowerShell required for actual release helper loading")
    spec, files, environment, _ = release
    _, payload = policy.sql_payload(spec, environment, files.get)
    package = tmp_path / "package"
    package.mkdir()
    for name, raw in payload.items():
        if damage != "missing_phase1" or name != "SqlDeploy.Phase1Release.ps1":
            (package / name).write_bytes(raw)
    runner = tmp_path / "check.ps1"
    runner.write_text(
        r"""
param([string]$Package,[string]$Damage)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. "$Package\SqlDeploy.ModuleRelease.ps1"
. "$Package\SqlDeploy.P02D4Release.ps1"
$id='20261120_001_p02_catalogue_observer'
$loaded=Read-K98ModuleProfile (Join-Path $Package ($id+'.release.json')) 'cd3bcb8c1f7303b8b45d5dc2b3d118aad70002f684ae847ffaf400c056bc1692' $id
if($loaded.Commands.Count -ne 1){throw 'Package profile did not load'}
$script:resourceCalls=0
$script:expectedConnection=[object]::new()
$script:expectedTransaction=[object]::new()
function Invoke-K98ModuleQuery($Connection,$Transaction,[string]$Sql) {
    $script:resourceCalls++
    if(-not [object]::ReferenceEquals($Connection,$script:expectedConnection) -or
       -not [object]::ReferenceEquals($Transaction,$script:expectedTransaction)){
        throw 'Resource ownership changed'
    }
    if($Sql -notlike '*used_log_space_in_percent<70*' -or
       $Sql -notlike '*version_store_reserved_page_count*524288*' -or
       $Sql -notlike '*v.available_bytes<8589934592*' -or
       $Sql -notlike '*THROW 52980*'){throw 'Resource gates changed'}
    if($Damage -ceq 'resource_refusal'){throw 'Injected resource refusal'}
    return ,@()
}
$failure=$null
try {Assert-K98D4Resources $script:expectedConnection $script:expectedTransaction}
catch {$failure=$_}
switch($Damage) {
    'none' {
        if($failure){throw $failure}
        if($script:resourceCalls -ne 1){throw 'Incomplete resource check'}
    }
    'missing_phase1' {
        if(-not $failure -or $failure.Exception.Message -notlike '*SqlDeploy.Phase1Release.ps1*' -or $script:resourceCalls -ne 0){
            throw 'Missing packaged helper did not refuse before SQL'
        }
    }
    'resource_refusal' {
        if(-not $failure -or $failure.Exception.Message -cne 'Injected resource refusal' -or $script:resourceCalls -ne 1){
            throw 'Resource refusal was not preserved'
        }
    }
}
@{case=$Damage;calls=$script:resourceCalls;profile_loaded=$true}|ConvertTo-Json -Compress
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(runner),
            "-Package",
            str(package),
            "-Damage",
            damage,
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == {
        "case": damage,
        "calls": 0 if damage == "missing_phase1" else 1,
        "profile_loaded": True,
    }


@pytest.mark.parametrize(
    "resource", ["p02_observer_protocol.json", "p02_observer_options_protocol.json"]
)
def test_windows_git_checkout_preserves_pinned_observer_bytes(release, tmp_path, resource):
    """Exercise Git's real filters without touching either worktree's index."""
    spec, files, _, _ = release
    source = Path(os.environ["K98_OBSERVER_SQL_SOURCE"])
    bot = Path(__file__).resolve().parents[1]
    protocol = json.loads((bot / "deploy" / resource).read_bytes())
    pins = {
        name: row["raw_source_sha256"]
        for row in [*protocol["modules"], protocol["sequence"]]
        for name in [row["path"]]
    }
    pins.update(
        {
            row["path"]: row["sha256"]
            for row in spec["sql"]["members"]
            if row["path"].startswith("migrations/")
        }
    )
    fixture = tmp_path / "git-filter-fixture"
    fixture.mkdir()
    output = tmp_path / "export"
    output.mkdir()

    def git(*args):
        return subprocess.run(
            ["git", *args], cwd=fixture, capture_output=True, timeout=15, check=True
        ).stdout

    git("init", "--quiet")
    git("config", "core.autocrlf", "true")
    (fixture / ".gitattributes").write_bytes((source / ".gitattributes").read_bytes())
    for name, digest in pins.items():
        raw = files[name] if name in files else (source / name).read_bytes()
        if (
            resource == "p02_observer_protocol.json"
            and name == "sql_schema/tr_P02CatalogueObservation.DatabaseTrigger.sql"
        ):
            # Retain the immutable predecessor fixture after its source snapshot advances.
            body = next(row["definition"] for row in protocol["modules"] if row["path"] == name)
            raw = ("SET ANSI_NULLS ON;\nSET QUOTED_IDENTIFIER ON;\nGO\n" + body + "GO\n").encode()
        assert policy.sha(raw) == digest
        target = fixture / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    git("add", "--", ".gitattributes", *pins)
    git("checkout-index", "--all", "--prefix=" + output.as_posix() + "/")
    for name, digest in pins.items():
        assert policy.sha((output / name).read_bytes()) == digest, name


@pytest.mark.parametrize("damage", [None, "source_drift", "unlisted_peer", "unrelated_root"])
def test_stats_admission_correction_requires_exact_installed_source_pair(
    release, tmp_path, monkeypatch, damage
):
    spec, _, _, blobs = release
    name = "unrelated_root.py" if damage == "unrelated_root" else "stats_module.py"
    blobs[spec["before"], name] = b"old stats caller\n"
    blobs["b" * 40, name] = b"corrected stats caller\n"
    spec["sources"].append(
        dict(
            path=name,
            before=policy.sha(blobs[spec["before"], name]),
            after=policy.sha(blobs["b" * 40, name]),
        )
    )
    installed(monkeypatch, tmp_path, spec)
    paths = [row["path"] for row in spec["sources"]]
    if damage == "source_drift":
        blobs["b" * 40, name] += b"changed"
    elif damage == "unlisted_peer":
        paths.remove(name)
    if damage:
        with pytest.raises(ValueError):
            policy.selected(spec["before"], "b" * 40, paths, lambda *key: blobs.get(key))
    else:
        assert policy.selected(spec["before"], "b" * 40, paths, lambda *key: blobs.get(key)) == spec
