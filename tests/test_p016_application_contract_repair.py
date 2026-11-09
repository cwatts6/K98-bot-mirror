"""Exact offline authority and native release gates for already-applied P016 SQL."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import subprocess
import sys
from uuid import uuid4

import pytest

from scripts import prepare_k98_update as updater, verify_k98_update_pair as verifier
from services.export_execution_protocol import encode

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def bot(monkeypatch):
    contract = {
        "version": 3,
        "fingerprint_format": "application_schema_v2",
        "metadata_hash": "before",
        "permissions_hash": "unchanged",
        "scope_hash": "unchanged",
        "server": "fixture",
        "database": "fixture",
        "principal": "restricted",
        "sources": [{"name": "dbo.Fixture", "type": "U"}],
        "review_id": "before",
    }
    # Synthetic expected contract only. Production authority remains the complete
    # real predecessor digest; full private catalogues are qualified separately.
    monkeypatch.setattr(
        verifier, "P016_APPLICATION_BEFORE", hashlib.sha256(encode(contract)).hexdigest()
    )
    return {
        "application_sql_contract": contract,
        "sql_contract": {"principal": "restricted"},
        "legacy_sql_contract": {"source": {"modules": []}, "principal": "restricted"},
    }


def bindings():
    return {
        "before": verifier.P016_APPLICATION_REPAIR["predecessor"],
        "application_contract_repair": deepcopy(verifier.P016_APPLICATION_REPAIR),
    }


def candidate(bot):
    transition = verifier.p016_application_transition(bindings()["before"], bot)
    return {key: pair["after"] for key, pair in transition["contracts"].items()}


def test_exact_amendment_preserves_scope_permissions_other_contracts_and_original(bot):
    original = deepcopy(bot)
    after = candidate(bot)
    assert verifier.repair_verification_bot(bindings(), bot, after) == after
    assert {
        k
        for k in bot["application_sql_contract"]
        if bot["application_sql_contract"][k] != after["application_sql_contract"][k]
    } == {"metadata_hash", "review_id"}
    for key in ("sql_contract", "legacy_sql_contract"):
        assert after[key] == bot[key]
    after["application_sql_contract"]["sources"][0]["name"] = "mutation"
    after["sql_contract"]["principal"] = "mutation"
    assert bot == original


@pytest.mark.parametrize(
    "field",
    [
        "version",
        "fingerprint_format",
        "metadata_hash",
        "permissions_hash",
        "scope_hash",
        "server",
        "database",
        "principal",
        "sources",
        "review_id",
        "extra",
    ],
)
def test_every_predecessor_contract_field_is_pinned(bot, field):
    bot["application_sql_contract"][field] = "drift"
    with pytest.raises(ValueError, match="predecessor application contract"):
        candidate(bot)


@pytest.mark.parametrize(
    "damage",
    [
        "predecessor",
        "sql",
        "recovery_seed",
        "marker",
        "marker_bool",
        "extra_marker",
        "application",
        "permissions",
        "legacy",
        "installation",
    ],
)
def test_wrong_release_candidate_or_added_work_refuses(bot, damage):
    config, after = bindings(), candidate(bot)
    if damage == "predecessor":
        config["before"] = "a" * 40
    elif damage in ("sql", "recovery_seed"):
        config[damage] = None
    elif damage == "marker":
        config["application_contract_repair"]["migration_sha256"] = "0" * 64
    elif damage == "marker_bool":
        config["application_contract_repair"]["version"] = True
    elif damage == "extra_marker":
        config["application_contract_repair"]["extra"] = "bad"
    elif damage == "application":
        after["application_sql_contract"]["metadata_hash"] = "observed-hash"
    elif damage == "permissions":
        after["application_sql_contract"]["permissions_hash"] = "new-permissions"
    elif damage == "legacy":
        after["legacy_sql_contract"]["source"]["modules"] = [{"name": "unexpected"}]
    else:
        after["sql_contract"]["principal"] = "owner"
    with pytest.raises(ValueError):
        verifier.repair_verification_bot(config, bot, after)


@pytest.mark.parametrize("preflight", [True, False])
@pytest.mark.parametrize(
    "damage", [None, "candidate_bytes", "old_policy_bytes", "old_contract", "permission_change"]
)
def test_both_native_sql_gates_authenticate_templates_before_comparison(
    tmp_path, monkeypatch, bot, preflight, damage
):
    import core.export_startup_windows as windows

    config = bindings()
    after = candidate(bot)

    def save(name, value):
        path = tmp_path / name
        raw = encode(value)
        path.write_bytes(raw)
        return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()}

    if damage == "old_contract":
        bot["application_sql_contract"]["permissions_hash"] = "drift"
    if damage == "permission_change":
        after["application_sql_contract"]["permissions_hash"] = "drift"
    old_plan = save("old-plan.json", {"templates": {"bot": save("old-bot.json", bot)}})
    old_policy = {"seed_plan": old_plan}
    old = save("old-policy.json", old_policy)
    config["old_policy"] = {"Path": old["path"], "SHA256": old["sha256"]}
    new_ref = save("bot-template.json", after)
    new_policy = {"seed_plan": save("new-plan.json", {"templates": {"bot": new_ref}})}
    config["seed_members"] = [{"name": "bot-template.json", "sha256": new_ref["sha256"]}]
    if damage == "candidate_bytes":
        (tmp_path / "bot-template.json").write_text("{}")
    if damage == "old_policy_bytes":
        (tmp_path / "old-plan.json").write_text("{}")
    monkeypatch.setattr(windows, "administrative_path", lambda path, **kw: Path(path))
    monkeypatch.setattr(verifier, "__file__", str(tmp_path / "Verify-NewPair.py"))
    observed = []
    monkeypatch.setattr(verifier, "verify_bot_sql_contracts", lambda value: observed.append(value))
    if damage:
        with pytest.raises(ValueError):
            verifier.verify_sql_contracts(
                config, old_policy if preflight else new_policy, preflight=preflight
            )
        assert not observed
    else:
        verifier.verify_sql_contracts(
            config, old_policy if preflight else new_policy, preflight=preflight
        )
        assert observed == [after]


def test_complete_packet_rebinds_seed_and_does_not_replay_sql(tmp_path, monkeypatch, bot):
    from core.export_release_seed import successor_seed
    from tests.test_export_release_seed import predecessor
    from tests.updater_source_assertions import installed_tool_fixture

    initial = predecessor(tmp_path, monkeypatch)
    # Retain the fixture's validated installation contract and authority binding.
    initial["bot-template.json"].update({k: v for k, v in bot.items() if k != "sql_contract"})
    plan = initial["ManualProcessPairPlan-CANDIDATE.json"]
    plan["templates"]["bot"]["sha256"] = updater.sha256(encode(initial["bot-template.json"]))
    initial["AutomaticStartupPolicy.json"]["seed_plan"]["sha256"] = updater.sha256(encode(plan))
    previous = {
        name: json.loads(raw)
        for name, raw in successor_seed(
            initial,
            {"application_feature.py": updater.sha256(b"old\n")},
            deployment_id=str(uuid4()),
            review_id=str(uuid4()),
            pipe_id=str(uuid4()),
        ).items()
    }
    policy = previous["AutomaticStartupPolicy.json"]
    path = str(
        PureWindowsPath(policy["seed_plan"]["path"]).with_name("AutomaticStartupPolicy.json")
    )
    config = bindings() | dict(
        target="c" * 40,
        root="C:\\fixture",
        host="FIXTURE",
        sid="S-1-5-21-1-2-3-1001",
        old_policy=dict(Path=path, SHA256=updater.sha256(encode(policy))),
        old_plan=dict(Python="C:\\fixture\\python.exe", PythonSHA256="a" * 64),
    )
    config.pop("application_contract_repair")  # It must be selected by installed authority.
    observation = dict(
        seed=previous,
        gate=f"$policy='{path}'\n$policyHash='{updater.sha256(encode(policy))}'\n",
        bindings=config,
    )
    tools, archive_hash = installed_tool_fixture(tmp_path)
    config["contract_verifier_sha256"] = archive_hash
    real_run_path = updater.runpy.run_path

    def reviewed_fixture_authority(path, *args, **kwargs):
        result = real_run_path(path, *args, **kwargs)
        if Path(path).name == "verify_k98_update_pair.py":
            result["p016_application_transition"] = verifier.p016_application_transition
        return result

    monkeypatch.setattr(updater.runpy, "run_path", reviewed_fixture_authority)
    blobs = {
        (config["before"], "application_feature.py"): b"old\n",
        (config["target"], "application_feature.py"): b"new\n",
    }
    result = updater.prepare_update(
        observation,
        ["application_feature.py"],
        lambda *key: blobs.get(key),
        tmp_path / "packet",
        tools,
    )
    package = Path(result["manifest"]).parent
    manifest = json.loads(Path(result["manifest"]).read_bytes())
    saved = json.loads((package / "ReleaseBindings.json").read_bytes())
    assert saved["application_contract_repair"] == verifier.P016_APPLICATION_REPAIR
    assert "sql" not in saved and "recovery_seed" not in saved
    assert [s["kind"] for s in manifest["steps"]] == ["source", "seed", "start", "readiness"]
    candidate_bot = json.loads((package / "bot-template.json").read_bytes())
    verifier.repair_verification_bot(saved, previous["bot-template.json"], candidate_bot)
    candidate_plan = json.loads((package / "ManualProcessPairPlan-CANDIDATE.json").read_bytes())
    assert candidate_plan["templates"]["bot"]["sha256"] == updater.sha256(encode(candidate_bot))
    assert saved["new_policy"]["seed_plan"]["sha256"] == updater.sha256(encode(candidate_plan))
    assert saved["flags"] == policy["flags"]
    for member in manifest["members"]:
        assert updater.sha256((package / member["name"]).read_bytes()) == member["sha256"]


@pytest.mark.skipif(os.name != "nt", reason="Native Windows PowerShell release gates")
def test_native_source_only_sql_check_and_admission_failure_are_blocking(tmp_path):
    helper = tmp_path / "Verify-NewPair.py"
    helper.write_text(
        "import json,sys\nfrom pathlib import Path\nPath(__file__).with_suffix('.args.json').write_text(json.dumps(sys.argv[1:]))\n"
    )
    (tmp_path / "logs").mkdir()
    script = tmp_path / "gates.ps1"
    script.write_text(r"""
param([string]$Root,[string]$Python)
$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $Root 'scripts/K98-SourceUpdate.ps1'),[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Parser failed'}
foreach($func in $ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$true)) {
 if($func.Name -in @('Verify-Native','Check-Readiness','Import-ExportStatus')) {
  $file=Join-Path $PSScriptRoot ($func.Name+'.ps1');[IO.File]::WriteAllText($file,$func.Extent.Text);. $file
 }
}
function Assert-ContractVerifier {}
function Read-Bytes {return [byte[]]@(1)}
$c=[pscustomobject]@{extra_members=@([pscustomobject]@{name='Verify-NewPair.py';sha256='fixture'});venv=[pscustomobject]@{path=$Python;sha256='fixture'};new_pins=@{};target='fixture';release_id='fixture';root=$PSScriptRoot}
$ExpectedBindingsSHA256='fixture'
Verify-Native -Preflight
$arguments=Get-Content (Join-Path $PSScriptRoot 'Verify-NewPair.args.json') -Raw|ConvertFrom-Json
if('--sql-contracts' -notin $arguments -or '--preflight' -notin $arguments){throw 'Source-only preflight skipped SQL'}
Verify-Native
$arguments=Get-Content (Join-Path $PSScriptRoot 'Verify-NewPair.args.json') -Raw|ConvertFrom-Json
if('--sql-contracts' -notin $arguments -or '--preflight' -in $arguments){throw 'Successor skipped SQL'}
function Assert-Drained {}
function Assert-Source {}
function Seed-Complete {return $true}
function New-Journal {return @{}}
function Verify-Native {}
function Assert-NewSession {}
function Read-Json {return @{log_offset=0}}
function Write-Record {$script:written=$true}
$script:written=$false
$log=Join-Path $PSScriptRoot 'logs/log.txt'
[IO.File]::WriteAllText($log,"Logged in as fixture`n[BOOT] full_startup_sequence completed successfully`nS11 export admission remains closed")
$refused=$false
try {$null=Check-Readiness} catch {if($_.Exception.Message -notmatch 'protected runtime admission failed'){throw};$refused=$true}
if(-not $refused -or $script:written){throw 'Closed admission was accepted'}
[IO.File]::WriteAllText($log,"Logged in as fixture`n[BOOT] full_startup_sequence completed successfully")
if(-not(Check-Readiness) -or -not $script:written){throw 'Unobserved provider health blocked source readiness'}
Write-Output 'NATIVE_REPAIR_GATES_PASSED'
""")
    result = subprocess.run(
        [
            r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(script),
            str(ROOT),
            sys.executable,
        ],
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "NATIVE_REPAIR_GATES_PASSED" in result.stdout
