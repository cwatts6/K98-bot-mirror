"""Explicit first-SQL-step amendments preserve original release evidence."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import pytest
from test_prepare_k98_release import specification

from scripts.prepare_k98_release import validate_manifest


def amendment():
    value = specification()
    value.update(
        version=2,
        amendment=dict(
            id="7840a12e-c27b-4674-a6d1-63e7f324e32f",
            base_manifest_sha256="a" * 64,
            failed_step_id="sql",
        ),
    )
    value["steps"][0]["id"] = "sql-correction"
    value["members"][0]["sha256"] = "d" * 64
    return value


def test_version_two_requires_explicit_base_and_keeps_version_one_supported():
    validate_manifest(specification())
    validate_manifest(amendment())
    for change in ("missing", "version", "hash", "extra", "id", "step", "no_sql", "same_step"):
        value = amendment()
        if change == "missing":
            value.pop("amendment")
        elif change == "version":
            value["version"] = 1
        elif change == "hash":
            value["amendment"]["base_manifest_sha256"] = "x"
        elif change == "extra":
            value["amendment"]["accept_unknown"] = True
        elif change == "id":
            value["amendment"]["id"] = None
        elif change == "no_sql":
            value["steps"].pop(0)
        elif change == "same_step":
            value["steps"][0]["id"] = value["amendment"]["failed_step_id"]
        else:
            value["amendment"]["failed_step_id"] = "../sql"
        with pytest.raises(ValueError):
            validate_manifest(value)


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "base_hash",
        "release_id",
        "policy",
        "issuer",
        "host",
        "repository",
        "base_version",
        "first_step",
        "no_intent",
        "later_intent",
        "complete",
        "start",
        "intent_identity",
        "no_corrective_sql",
        "reused_step_id",
        "reused_apply_script",
        "renamed_apply_script",
        "unlisted_apply_script",
    ],
)
def test_native_amendment_gate_preserves_evidence_and_rejects_progress(tmp_path, damage):
    powershell = shutil.which("powershell.exe")
    if not powershell:
        pytest.skip("Windows PowerShell required for native release adapter check")
    base = specification()
    current = amendment()
    if damage in ("release_id", "host", "repository"):
        current[damage] = "different"
    elif damage in ("policy", "issuer"):
        current["policy" if damage == "policy" else "issuer_launcher"]["sha256"] = (
            "b" * 64 if damage == "policy" else "a" * 64
        )
    elif damage == "base_version":
        base["version"] = 2
    elif damage == "first_step":
        base["steps"][0]["kind"] = "source"
    elif damage == "no_corrective_sql":
        current["steps"].pop(0)
    elif damage == "reused_step_id":
        current["steps"][0]["id"] = "sql"
    elif damage in ("reused_apply_script", "renamed_apply_script"):
        current["members"][0]["sha256"] = base["members"][0]["sha256"]
        if damage == "renamed_apply_script":
            current["members"][0]["name"] = "renamed.ps1"
            current["steps"][0]["apply"]["file"] = "renamed.ps1"
    elif damage == "unlisted_apply_script":
        current["steps"][0]["apply"]["file"] = "missing.ps1"
    raw = json.dumps(base).encode()
    (tmp_path / ".release.json").write_bytes(raw)
    current["amendment"]["base_manifest_sha256"] = hashlib.sha256(raw).hexdigest()
    if damage == "base_hash":
        current["amendment"]["base_manifest_sha256"] = "0" * 64
    receipts = tmp_path / ".receipts"
    receipts.mkdir()
    intent = dict(stage="starting", release_id=base["release_id"], step="sql")
    if damage == "intent_identity":
        intent["release_id"] = "different"
    if damage != "no_intent":
        (receipts / "sql.intent.json").write_text(json.dumps(intent))
    if damage in ("later_intent", "complete"):
        (
            receipts / ("source.intent.json" if damage == "later_intent" else "sql.complete.json")
        ).write_text("{}")
    if damage == "start":
        (tmp_path / "start-requested.json").write_text("{}")
    (tmp_path / "current.json").write_text(json.dumps(current))
    before = {p.name: p.read_bytes() for p in receipts.iterdir()}
    runner = Path(__file__).resolve().parents[1] / "scripts/Deploy-K98Release.ps1"
    script = tmp_path / "gate.ps1"
    script.write_text(
        r"""
param([string]$Runner,[string]$Fixture)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$env:PSModulePath='C:\Windows\System32\WindowsPowerShell\v1.0\Modules'
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile($Runner,[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Parser errors'}
$fn=$ast.Find({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Assert-ReleaseAmendment'},$true)
. ([scriptblock]::Create($fn.Extent.Text))
function Assert-AdminPath([string]$Path){if(-not(Test-Path -LiteralPath $Path)){throw 'Missing fixture'}}
function Read-Pinned([string]$Path,[string]$Hash,[long]$Limit){
 if((Get-FileHash -LiteralPath $Path).Hash.ToLowerInvariant() -cne $Hash){throw 'Checksum differs'}
 return ,[IO.File]::ReadAllBytes($Path)
}
function Read-Control([string]$Path){Get-Content -LiteralPath $Path -Raw|ConvertFrom-Json}
$current=Get-Content -LiteralPath (Join-Path $Fixture 'current.json') -Raw|ConvertFrom-Json
Assert-ReleaseAmendment $current $Fixture
Write-Output 'AMENDMENT_GATE_PASSED'
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
            str(script),
            "-Runner",
            str(runner),
            "-Fixture",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    if damage is None:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "AMENDMENT_GATE_PASSED" in result.stdout
    else:
        assert result.returncode != 0
    assert (tmp_path / ".release.json").read_bytes() == raw
    assert {p.name: p.read_bytes() for p in receipts.iterdir()} == before


@pytest.mark.parametrize(
    "scenario,expected_apply,success",
    [
        ("fresh", 1, True),
        ("committed", 0, True),
        ("uncertain", 0, False),
        ("intent_absent_result", 0, False),
        ("apply_failed", 1, False),
        ("postcondition_failed", 1, False),
    ],
)
def test_actual_step_engine_never_replays_uncertain_amendment(
    tmp_path, scenario, expected_apply, success
):
    powershell = shutil.which("powershell.exe")
    if not powershell:
        pytest.skip("Windows PowerShell required")
    runner = Path(__file__).resolve().parents[1] / "scripts/Deploy-K98Release.ps1"
    script = tmp_path / "steps.ps1"
    script.write_text(
        r"""
param([string]$Runner,[string]$Fixture,[string]$Scenario)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$ast=[Management.Automation.Language.Parser]::ParseFile($Runner,[ref]$null,[ref]$null)
$fn=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Invoke-ReleaseSteps'},$true)
. ([scriptblock]::Create($fn.Extent.Text))
$script:applies=0;$script:later=0;$script:verifies=0
function Invoke-ReleaseScript($Invocation) {
 if($Invocation -ceq 'later'){$script:later++;return 0}
 if($Invocation -ceq 'apply'){$script:applies++;if($Scenario -ceq 'apply_failed'){return 1};return 0}
 $script:verifies++
 if($Scenario -ceq 'committed'){return 0}
 if($Scenario -ceq 'uncertain'){return 1}
 if($script:verifies -eq 1){return 10}
 if($Scenario -ceq 'postcondition_failed'){return 1}
 return 0
}
function Write-NewRecord([string]$Path,$Value){[IO.File]::WriteAllText($Path,($Value|ConvertTo-Json -Compress))}
if($Scenario -cin @('committed','intent_absent_result','uncertain')){Write-NewRecord (Join-Path $Fixture 'sql-collation.intent.json') @{stage='starting';release_id='release';step='sql-collation'}}
$steps=@(@{id='sql-collation';apply='apply';verify='verify'},@{id='next';apply='later';verify='later'})
try {Invoke-ReleaseSteps $steps $Fixture 'release';$success=$true}catch{$success=$false}
@{success=$success;applies=$script:applies;later=$script:later;intent=(Test-Path -LiteralPath (Join-Path $Fixture 'sql-collation.intent.json'));complete=(Test-Path -LiteralPath (Join-Path $Fixture 'sql-collation.complete.json'))}|ConvertTo-Json -Compress
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(script),
            "-Runner",
            str(runner),
            "-Fixture",
            str(tmp_path),
            "-Scenario",
            scenario,
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    observed = json.loads(result.stdout)
    assert observed["success"] is success
    assert observed["applies"] == expected_apply
    assert observed["later"] == (1 if success else 0)
    assert observed["intent"] is True
    assert observed["complete"] is success


@pytest.mark.parametrize(
    "selection", ["absent", "same", "other_id", "other_hash", "other_release", "create_race"]
)
def test_selection_observed_after_preflight_is_revalidated(tmp_path, selection):
    powershell = shutil.which("powershell.exe")
    if not powershell:
        pytest.skip("Windows PowerShell required")
    runner = Path(__file__).resolve().parents[1] / "scripts/Deploy-K98Release.ps1"
    script = tmp_path / "selection.ps1"
    script.write_text(
        r"""
param([string]$Runner,[string]$Fixture,[string]$Scenario)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$ast=[Management.Automation.Language.Parser]::ParseFile($Runner,[ref]$null,[ref]$null)
$fn=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Assert-AmendmentSelection'},$true)
. ([scriptblock]::Create($fn.Extent.Text))
# Execute the actual post-preflight selection block, with a competing record
# already present (or arriving between its existence check and CreateNew).
$block=$ast.Find({param($n) $n -is [Management.Automation.Language.IfStatementAst] -and $n.Extent.Text.StartsWith('if($null -ne $amendmentSelection)')},$true)
if($null -eq $block){throw 'Selection block missing'}
$amendmentSelection=Join-Path $Fixture 'selection.json';$releaseId='release';$ExpectedSHA256='a'*64
$manifest=[pscustomobject]@{release_id=$releaseId;amendment=@{id='current'}}
function Read-Control([string]$Path){Get-Content -LiteralPath $Path -Raw|ConvertFrom-Json}
function Write-NewRecord([string]$Path,$Value){
 if($Scenario -ceq 'create_race'){[IO.File]::WriteAllText($Path,'{"amendment_id":"other","manifest_sha256":"other","release_id":"release"}')}
 $stream=[IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
 try{$raw=[Text.Encoding]::UTF8.GetBytes(($Value|ConvertTo-Json -Compress));$stream.Write($raw,0,$raw.Length)}finally{$stream.Dispose()}
}
if($Scenario -notin @('absent','create_race')) {
 $record=@{amendment_id='current';manifest_sha256=$ExpectedSHA256;release_id=$releaseId}
 if($Scenario -ceq 'other_id'){$record.amendment_id='other'}
 if($Scenario -ceq 'other_hash'){$record.manifest_sha256='b'*64}
 if($Scenario -ceq 'other_release'){$record.release_id='other'}
 [IO.File]::WriteAllText($amendmentSelection,($record|ConvertTo-Json -Compress))
}
try{. ([scriptblock]::Create($block.Extent.Text));$success=$true}catch{$success=$false}
@{success=$success;selected=(Read-Control $amendmentSelection)}|ConvertTo-Json -Compress
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(script),
            "-Runner",
            str(runner),
            "-Fixture",
            str(tmp_path),
            "-Scenario",
            selection,
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    observed = json.loads(result.stdout)
    assert observed["success"] is (selection in ("absent", "same"))
    if selection in ("other_id", "create_race"):
        assert observed["selected"]["amendment_id"] == "other"
