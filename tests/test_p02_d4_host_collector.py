"""Native read-only fixture coverage; never query the installed scheduler or SQL."""

import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "scripts/collect_p02_d4_host.ps1"


@pytest.fixture
def powershell():
    executable = shutil.which("powershell.exe")
    if executable is None:
        pytest.skip("Windows PowerShell 5.1 required")
    return executable


def invoke(powershell, script, *args):
    return subprocess.run(
        [powershell, "-NoProfile", "-NonInteractive", "-File", str(script), *map(str, args)],
        capture_output=True,
        text=True,
        timeout=25,
    )


def fixture_functions(powershell, tmp_path, body):
    # Evaluate only function definitions from the parsed source, never the host
    # collection body. Every file read below uses this test's disposable folder.
    script = tmp_path / "fixture.ps1"
    script.write_text(
        "param([string]$Source,[string]$Fixture)\n"
        "$ErrorActionPreference='Stop';Set-StrictMode -Version Latest\n"
        "$tokens=$null;$errors=$null\n"
        "$ast=[Management.Automation.Language.Parser]::ParseFile("
        "$Source,[ref]$tokens,[ref]$errors)\n"
        "if($errors.Count){throw ($errors|Out-String)}\n"
        "foreach($s in $ast.EndBlock.Statements){"
        "if($s -is [Management.Automation.Language.FunctionDefinitionAst]){"
        ". ([scriptblock]::Create($s.Extent.Text))}}\n"
        "$timer=[Diagnostics.Stopwatch]::StartNew();$script:readBytes=0L\n"
        "$script:visited=0;$script:seen=@{}\n"
        "$script:files=New-Object 'Collections.Generic.List[object]'\n" + body,
        encoding="utf-8",
    )
    result = invoke(powershell, script, SOURCE, tmp_path)
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_wrong_host_has_no_output(powershell, tmp_path):
    if os.environ.get("COMPUTERNAME", "").casefold() == "mini_amd":
        pytest.skip("Never run the full collector on the installed host in tests")
    output = tmp_path / "receipt.json"
    result = invoke(powershell, SOURCE, "-OutputFile", output)
    assert result.returncode != 0
    assert "requires MINI_AMD" in result.stderr
    assert not output.exists()


def test_private_create_new_receipt(powershell, tmp_path):
    source = SOURCE.read_text(encoding="utf-8").split("$timer=", 1)[0]
    prefix = "\n".join(
        line for line in source.splitlines() if not line.startswith("if($env:COMPUTERNAME")
    )
    script = tmp_path / "output.ps1"
    script.write_text(
        prefix + "\n$output.Dispose()\n$a=[IO.File]::GetAccessControl($outputPath)\n"
        "if(-not $a.AreAccessRulesProtected -or @($a.Access).Count -ne 2){throw 'ACL'}\n",
        encoding="utf-8",
    )
    output = tmp_path / "receipt.json"
    result = invoke(powershell, script, "-OutputFile", output)
    assert result.returncode == 0, result.stderr
    output.write_text("retained original", encoding="utf-8")
    assert invoke(powershell, script, "-OutputFile", output).returncode != 0
    assert output.read_text() == "retained original"


def test_identity_allowlist_never_exports_credentials(powershell, tmp_path):
    (tmp_path / "settings.env").write_text(
        'SQL_USERNAME="ReadUser"\nSQL_PASSWORD=never-export-this\n'
        "S11_SQL_USERNAME='S11_ExportApplication'\nSQL_MONITOR_USERNAME=${SECRET}\n"
        "DISCORD_TOKEN=never-export-token\nSQL_SERVER=MINI_AMD\n",
        encoding="utf-8",
    )
    output = fixture_functions(
        powershell,
        tmp_path,
        "Read-IdentitySettings (Join-Path $Fixture 'settings.env')|ConvertTo-Json -Depth 5\n",
    )
    rows = {row["key"]: row for row in json.loads(output)["settings"]}
    assert rows["SQL_USERNAME"]["value"] == "ReadUser"
    assert rows["S11_SQL_USERNAME"]["value"] == "S11_ExportApplication"
    assert rows["SQL_MONITOR_USERNAME"]["status"] == "unresolved"
    assert rows["SQL_MONITOR_USERNAME"]["value"] is None
    assert len(rows) == 4
    assert "never-export" not in output


def test_source_tree_exclusions_hashes_and_exact_root_names(powershell, tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    (root / "entry.py").write_bytes(b"exec UPDATE_ALL2\r\n")
    (root / "old.ps1").write_text("exec dbo.UPDATE_ALL; Test-Path file", encoding="utf-16")
    (root / "secrets.json").write_text('{"password":"not-source"}')
    (root / "venv").mkdir()
    (root / "venv" / "ignore.py").write_text("UPDATE_RALLY_DATA")
    output = fixture_functions(
        powershell,
        tmp_path,
        "Read-SourceTree (Join-Path $Fixture 'source')\n"
        "$script:files.ToArray()|ConvertTo-Json -Depth 5\n",
    )
    rows = {Path(row["path"]).name: row for row in json.loads(output)}
    assert set(rows) == {"entry.py", "old.ps1"}
    assert rows["entry.py"]["root_candidates"] == ["UPDATE_ALL2"]
    assert rows["entry.py"]["sha256"] != rows["entry.py"]["textLF_SHA256"]
    # TEST is intentionally a lexical candidate (Test-Path is not a SQL caller).
    assert rows["old.ps1"]["root_candidates"] == ["UPDATE_ALL", "TEST"]
    assert "not-source" not in output


def test_file_bounds_and_partial_section_are_not_success(powershell, tmp_path):
    (tmp_path / "large.txt").write_bytes(b"a" * 20)
    output = fixture_functions(
        powershell,
        tmp_path,
        "$record=[ordered]@{sections=@()}\n"
        "Add-Section 'bounded' {Read-Bounded (Join-Path $Fixture 'large.txt') 10}\n"
        "$script:readBytes=128MB\n"
        "Add-Section 'aggregate' {Read-Bounded (Join-Path $Fixture 'large.txt')}\n"
        "Add-Section 'private_error' {throw 'never_export_this_secret'}\n"
        "$record|ConvertTo-Json -Depth 5\n",
    )
    sections = json.loads(output)["sections"]
    assert all(s["status"] == "unavailable" for s in sections)
    assert [s["error_code"] for s in sections] == ["byte_bound", "byte_bound", "read_failed"]
    assert "never_export_this_secret" not in output


def test_reparse_and_nonlocal_reads_refuse(powershell, tmp_path):
    output = fixture_functions(
        powershell,
        tmp_path,
        "$target=Join-Path $Fixture 'target';$link=Join-Path $Fixture 'link'\n"
        "$null=New-Item -ItemType Directory -Path $target\n"
        "$null=New-Item -ItemType Junction -Path $link -Target $target\n"
        "$record=[ordered]@{sections=@()}\n"
        "try {\n"
        "Add-Section 'junction' {Assert-LocalPath $link}\n"
        "Add-Section 'unc' {Assert-LocalPath '\\localhost\\c$\\file'}\n"
        "Add-Section 'stream' {Assert-LocalPath ($target+':stream')}\n"
        "} finally {[IO.Directory]::Delete($link)}\n"
        "$record|ConvertTo-Json -Depth 5\n",
    )
    assert all(s["status"] == "unavailable" for s in json.loads(output)["sections"])


def test_task_inventory_keeps_opaque_actions_and_hashes_arguments(powershell, tmp_path):
    output = fixture_functions(
        powershell,
        tmp_path,
        r"""
$action=[pscustomobject]@{Type=0;Path='powershell.exe';WorkingDirectory='C:\app';Arguments='-File "C:\app\entry.ps1" -Password never-export-this UPDATE_ALL2'}
$task=[pscustomobject]@{Path='\Fixture';Enabled=$true;State=3;LastRunTime=[datetime]'2026-11-10';LastTaskResult=0;Definition=[pscustomobject]@{Principal=[pscustomobject]@{UserId='FixtureUser';LogonType=3};Actions=@($action,[pscustomobject]@{Type=5})}}
$script:taskFixture=$task
$script:folderFixture=New-Object psobject
$script:folderFixture|Add-Member ScriptMethod GetTasks {param($flags);if($flags -ne 1){throw 'hidden tasks omitted'};return @($script:taskFixture)}
$script:folderFixture|Add-Member ScriptMethod GetFolders {param($flags);if($flags -ne 0){throw 'reserved folder flag'};return @()}
$script:schedulerFixture=New-Object psobject
$script:schedulerFixture|Add-Member ScriptMethod Connect {}
$script:schedulerFixture|Add-Member ScriptMethod GetFolder {param($path);return $script:folderFixture}
function New-Object {
    param([string]$TypeName,[string]$ComObject)
    if($ComObject){if($ComObject -ne 'Schedule.Service'){throw 'unexpected COM'};return $script:schedulerFixture}
    Microsoft.PowerShell.Utility\New-Object -TypeName $TypeName
}
Read-Tasks|ConvertTo-Json -Depth 10
""",
    )
    tasks = json.loads(output)["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["actions"][0]["script_candidates"] == [r"C:\app\entry.ps1"]
    assert tasks[0]["actions"][0]["root_candidates"] == ["UPDATE_ALL2"]
    assert len(tasks[0]["actions"][0]["arguments_sha256"]) == 64
    assert tasks[0]["actions"][1]["status"] == "opaque"
    assert "never-export-this" not in output


@pytest.mark.parametrize("has_predecessor", [False, True])
def test_protected_release_supports_both_policy_shapes(powershell, tmp_path, has_predecessor):
    seed = r"C:\ProgramData\K98\S11\runtime\12345678-1234-1234-1234-123456789012"
    policy = {
        "version": 1,
        "seed_plan": {"path": seed + r"\ManualProcessPairPlan-CANDIDATE.json", "sha256": "a" * 64},
        "source_hashes": {"DL_bot.py": "b" * 64},
        "flags": {},
        "state_directory": r"C:\ProgramData\K98\S11\state",
    }
    if has_predecessor:
        policy["predecessor"] = {"policy_sha256": "c" * 64}
    (tmp_path / "AutomaticStartupPolicy.json").write_text(json.dumps(policy))
    bot = {
        key: {"version": 1}
        for key in ("sql_contract", "legacy_sql_contract", "application_sql_contract")
    }
    bot["source_hashes"] = {"DL_bot.py": "b" * 64}
    # Only selected fields are retained even when a fixture includes another field.
    bot["unselected"] = "never-export-this"
    (tmp_path / "bot-template.json").write_text(json.dumps(bot))
    for name in (
        "ManualProcessPairPlan-CANDIDATE.json",
        "authority-template.json",
        "host_acl.json",
        "bot_identity.json",
        "identity_issuance.json",
        "file_access.json",
        "key_inventory.json",
        "writer_drain.json",
        "sql_installation.json",
    ):
        (tmp_path / name).write_text("{}")
    updater = tmp_path / "updater"
    updater.mkdir()
    (updater / "update-tool.json").write_text('{"version":1}')
    output = fixture_functions(
        powershell,
        tmp_path,
        r"""
$script:fixtureRoot=$Fixture
$script:nativeRead=${function:Read-Bounded}
$script:nativeUpdater=${function:Read-UpdaterMembers}
function Read-Bounded {
    param([string]$Path,[int]$Limit=2MB)
    if($Path.StartsWith($script:fixtureRoot)){& $script:nativeRead $Path $Limit;return}
    if($Path -cnotmatch '^C:\\ProgramData\\K98\\S11\\runtime\\12345678-1234-1234-1234-123456789012\\[^\\]+$'){throw 'unexpected fixture path'}
    & $script:nativeRead (Join-Path $script:fixtureRoot ([IO.Path]::GetFileName($Path))) $Limit
}
function Read-SourceFile {param([string]$Path);$script:observedGate=$Path}
function Read-UpdaterMembers {
    param([string]$Directory)
    if($Directory -cne 'C:\ProgramData\K98\S11\updater'){throw 'updater path'}
    & $script:nativeUpdater (Join-Path $script:fixtureRoot 'updater')
}
$script:actionFixture=[pscustomobject]@{Type=0;Arguments='-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "C:\ProgramData\K98\S11\runtime\12345678-1234-1234-1234-123456789012\Start-ReviewedAutomaticStartup.ps1"'}
$actions=[pscustomobject]@{Count=1}
$actions|Add-Member ScriptMethod Item {param($index);if($index -ne 1){throw 'index'};return $script:actionFixture}
$script:taskFixture=[pscustomobject]@{Definition=[pscustomobject]@{Actions=$actions}}
$script:folderFixture=New-Object psobject
$script:folderFixture|Add-Member ScriptMethod GetTask {param($name);if($name -ne 'StartDLBotAfterSQL'){throw 'task name'};return $script:taskFixture}
$script:schedulerFixture=New-Object psobject
$script:schedulerFixture|Add-Member ScriptMethod Connect {}
$script:schedulerFixture|Add-Member ScriptMethod GetFolder {param($path);return $script:folderFixture}
function New-Object {
    param([string]$TypeName,[object[]]$ArgumentList,[string]$ComObject)
    if($ComObject){if($ComObject -ne 'Schedule.Service'){throw 'unexpected COM'};return $script:schedulerFixture}
    Microsoft.PowerShell.Utility\New-Object -TypeName $TypeName -ArgumentList $ArgumentList
}
Read-ProtectedRelease|ConvertTo-Json -Depth 12
""",
    )
    result = json.loads(output)
    assert result["policy"]["predecessor"] == policy.get("predecessor")
    assert len(result["seed_members"]) == 10
    assert result["updater"][0]["name"] == "update-tool.json"
    assert len(result["updater"][0]["sha256"]) == 64
    assert result["bot_contracts"]["sql_contract"] == {"version": 1}
    assert "never-export-this" not in output
