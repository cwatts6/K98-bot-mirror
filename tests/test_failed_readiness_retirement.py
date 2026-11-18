"""Retirement never converts a failed release into readiness or replays effects."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.package_k98_update_tool import package, retirement_profile

ROOT = Path(__file__).resolve().parents[1]


def profile():
    return {
        "version": 1,
        "kind": "failed_readiness_retirement",
        "host": "MINI_AMD",
        "sid": "S-1-5-21-1-2-3-1001",
        "release_id": "10000000-0000-0000-0000-000000000001",
        "work": r"C:\ProgramData\K98\S11\updates\20000000-0000-0000-0000-000000000002",
        "approved_target": "b" * 40,
        "journal_name": "incarnation-00000000000000000002-30000000-0000-0000-0000-000000000003.json",
        "receipts": {
            f"{step}.{state}.json": "a" * 64
            for step in ("source", "seed", "start")
            for state in ("intent", "complete")
        },
        **{
            name + "_sha256": "a" * 64
            for name in (
                "active",
                "bindings",
                "drain",
                "failure_evidence",
                "journal",
                "manifest",
                "prepared",
                "request",
                "start",
            )
        },
    }


def test_profile_is_exact_and_contains_no_executable_commands():
    document = profile()
    assert retirement_profile(json.dumps(document).encode()) == document


@pytest.mark.parametrize(
    "mutation",
    [
        "extra",
        "sql_receipt",
        "missing_complete",
        "readiness",
        "work_escape",
        "work_relative",
        "other_host",
        "other_kind",
        "short_hash",
        "bad_target",
        "journal_escape",
        "bool_version",
        "bad_sid",
    ],
)
def test_profile_rejects_unreviewed_or_advanced_scope(mutation):
    document = profile()
    if mutation == "extra":
        document["command"] = "anything"
    elif mutation == "sql_receipt":
        document["receipts"]["sql.complete.json"] = "a" * 64
    elif mutation == "missing_complete":
        del document["receipts"]["start.complete.json"]
    elif mutation == "readiness":
        document["receipts"]["readiness.intent.json"] = "a" * 64
    else:
        key, value = {
            "work_escape": ("work", document["work"] + r"\..\outside"),
            "work_relative": ("work", "relative"),
            "other_host": ("host", "LAB"),
            "other_kind": ("kind", "force"),
            "short_hash": ("bindings_sha256", "a" * 63),
            "bad_target": ("approved_target", "main"),
            "journal_escape": ("journal_name", "../journal.json"),
            "bool_version": ("version", True),
            "bad_sid": ("sid", "administrator"),
        }[mutation]
        document[key] = value
    with pytest.raises(ValueError):
        retirement_profile(json.dumps(document).encode())


def test_retirement_cannot_be_packaged_as_a_first_install(tmp_path):
    source = tmp_path / "profile.json"
    source.write_text(json.dumps(profile()), encoding="utf-8")
    with pytest.raises(ValueError, match="used-updater"):
        package(tmp_path / "output", retirement=source)
    assert not (tmp_path / "output").exists()


@pytest.fixture(scope="module")
def packaged(tmp_path_factory):
    import base64

    root = tmp_path_factory.mktemp("retirement-tool")
    initial = root / "initial"
    package(initial)
    text = (initial / "Install-K98UpdateTool.ps1").read_text(encoding="utf-8")
    encoded = text.split("$encoded='")[1].split("'")[0]
    files = json.loads(base64.b64decode(encoded))
    manifest = base64.b64decode(files["update-tool.json"])
    # The deployed predecessor inventory predates the new shared retirement helper.
    old = json.loads(manifest)
    del old["files"]["K98-FailedReadiness.ps1"]
    old_path = root / "previous.json"
    old_path.write_text(json.dumps(old), encoding="utf-8")
    profile_path = root / "profile.json"
    profile_path.write_text(json.dumps(profile()), encoding="utf-8")
    result = package(root / "upgrade", previous_manifest=old_path, retirement=profile_path)
    return root, result, files


def test_package_binds_profile_and_installs_shared_support(packaged):
    import base64

    root, result, files = packaged
    helper = Path(result["upgrade"]).read_text(encoding="utf-8")
    raw = (root / "profile.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() in helper
    assert (root / "upgrade" / "Retire-FailedReadiness.json").read_bytes() == raw
    assert "__RETIREMENT_PROFILE_SHA256__" not in helper
    manifest = json.loads(base64.b64decode(files["update-tool.json"]))
    shared = base64.b64decode(files["K98-FailedReadiness.ps1"])
    assert hashlib.sha256(shared).hexdigest() == manifest["files"]["K98-FailedReadiness.ps1"]
    assert shared == (ROOT / "scripts" / "K98-FailedReadiness.ps1").read_bytes().replace(
        b"\r\n", b"\n"
    )


def test_windows_retirement_state_and_native_file_harness(tmp_path):
    if os.name != "nt":
        pytest.skip("Actual Windows PowerShell 5.1 and NTFS fixture operations")
    source = tmp_path / "profile.json"
    source.write_text(json.dumps(profile()), encoding="utf-8")
    result = subprocess.run(
        [
            r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts" / "Test-K98FailedReadiness.ps1"),
            "-FixtureRoot",
            str(tmp_path / "native"),
            "-ProfilePath",
            str(source),
            "-NativePython",
            sys._base_executable,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout.splitlines()[-1])
    assert report["Status"] == "PASS"
    assert report["ProductionTouched"] is False
    assert report["Cases"] >= 35


def test_generated_package_passes_actual_normal_updater_inventory(packaged, tmp_path):
    """Run the real consumer block without executing host/updater entrypoints."""
    import base64

    if os.name != "nt":
        pytest.skip("Actual Windows PowerShell consumer")
    _, _, files = packaged
    payload = tmp_path / "tool"
    payload.mkdir()
    for name, encoded in files.items():
        (payload / name).write_bytes(base64.b64decode(encoded))
    harness = tmp_path / "consumer.ps1"
    harness.write_text(
        r"""
param([string]$ToolDirectory)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $ToolDirectory 'K98-SourceUpdate.ps1'),[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Library parse failed'}
foreach($name in @('Hash','Read-Bytes','Read-Json')) {
 $definition=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $name},$true)
 if($null -eq $definition){throw ('Required library function missing: '+$name)}
 . ([scriptblock]::Create($definition.Extent.Text))
}
function Assert-Protected([string]$Path) {
 if(-not [IO.Path]::GetFullPath($Path).StartsWith(($ToolDirectory+'\'),[StringComparison]::OrdinalIgnoreCase)){throw 'Fixture escaped'}
}
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $ToolDirectory 'Update-K98.ps1'),[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Updater parse failed'}
$nodes=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.IfStatementAst] -and $n.Clauses[0].Item1.Extent.Text -ceq 'Test-Path -LiteralPath $toolManifestPath'},$true))
if($nodes.Count -ne 1){throw 'Exact actual inventory block required'}
$body='$PSScriptRoot=$ToolDirectory'+"`n"+(($nodes[0].Clauses[0].Item2.Statements|ForEach-Object {$_.Extent.Text}) -join "`n")
$toolManifestPath=Join-Path $ToolDirectory 'update-tool.json'
$original=[IO.File]::ReadAllBytes($toolManifestPath)
& ([scriptblock]::Create($body))
function Reject([string]$Pattern) {
 try {& ([scriptblock]::Create($body));throw 'DID_NOT_REJECT'}
 catch {if($_.Exception.Message -notlike $Pattern){throw}}
}
$manifest=[Text.Encoding]::UTF8.GetString($original)|ConvertFrom-Json
$manifest.files.PSObject.Properties.Remove('K98-FailedReadiness.ps1')
[IO.File]::WriteAllText($toolManifestPath,($manifest|ConvertTo-Json -Depth 5))
Reject '*Exact update tool inventory*'
$manifest.files|Add-Member NoteProperty 'unexpected.ps1' ('a'*64)
[IO.File]::WriteAllText($toolManifestPath,($manifest|ConvertTo-Json -Depth 5))
Reject '*K98-FailedReadiness.ps1*'
[IO.File]::WriteAllBytes($toolManifestPath,$original)
[IO.File]::WriteAllText((Join-Path $ToolDirectory 'K98-FailedReadiness.ps1'),'changed')
Reject '*checksum differs*'
Write-Output 'ACTUAL_CONSUMER_PASS: package accepted; missing, substituted and changed helper refused'
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(harness),
            "-ToolDirectory",
            str(payload),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ACTUAL_CONSUMER_PASS" in result.stdout
