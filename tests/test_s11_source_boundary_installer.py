"""Native Windows guard tests; none perform administrative installation."""

import ast
import asyncio
from datetime import UTC, datetime
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/install_s11_source_boundary.ps1"
pytestmark = pytest.mark.skipif(os.name != "nt", reason="Native Windows filesystem guards")


def run_helpers(tmp_path, body):
    script = str(SCRIPT).replace("'", "''")
    fixture = str(tmp_path).replace("'", "''")
    source = f"""
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$tokens=$null; $errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile('{script}',[ref]$tokens,[ref]$errors)
if($errors.Count){{throw 'Installer parse failure'}}
foreach($name in @('CanonicalPath','Inside','CheckedItem','FileDigest','ReadBoundedGit','BeginOperation','InvokeBoundedWorker','VerifySourceDirectory')){{
 $node=$ast.Find({{param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name}},$false)
 if($null -eq $node){{throw 'Helper missing'}}
 Invoke-Expression $node.Extent.Text
}}
$fixture='{fixture}'
$progressPath=$null
{body}
"""
    probe = tmp_path / "native-guard-test.ps1"
    probe.write_text(source, encoding="utf-8-sig")
    result = subprocess.run(
        [
            r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(probe),
        ],
        capture_output=True,
        text=True,
        timeout=20,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    assert result.returncode == 0, result.stderr + result.stdout


def test_reject_noncanonical_escape_network_root_and_stream(tmp_path):
    run_helpers(
        tmp_path,
        r"""
foreach($bad in @('relative\file','C:\','C:\root\..\outside','\\server\share\file','C:\root\file:stream')){
 $refused=$false
 try{$null=CanonicalPath $bad}catch{$refused=$true}
 if(-not $refused){throw "Unsafe path accepted: $bad"}
}
if(Inside 'C:\root-extra\file' 'C:\root'){throw 'Prefix escape accepted'}
if(-not (Inside 'C:\root\file' 'C:\root')){throw 'Valid child rejected'}
""",
    )


def test_bounded_file_digest_and_no_overwrite_preservation(tmp_path):
    run_helpers(
        tmp_path,
        r"""
$file=Join-Path $fixture 'small.txt'; [IO.File]::WriteAllText($file,'reviewed')
if((FileDigest $file) -cnotmatch '^[0-9a-f]{64}$'){throw 'Digest failed'}
$large=Join-Path $fixture 'large.bin';$stream=[IO.File]::Open($large,[IO.FileMode]::CreateNew)
$stream.SetLength(16MB+1);$stream.Dispose()
$refused=$false;try{$null=FileDigest $large}catch{$refused=$true}
if(-not $refused){throw 'Oversize hash accepted'}
$from=Join-Path $fixture 'from';$to=Join-Path $fixture 'to'
$null=[IO.Directory]::CreateDirectory($from);$null=[IO.Directory]::CreateDirectory($to)
$refused=$false;try{[IO.Directory]::Move($from,$to)}catch{$refused=$true}
if(-not $refused -or -not (Test-Path -LiteralPath $from)){throw 'Move overwrote destination'}
$fresh=Join-Path $fixture 'fresh';[IO.Directory]::Move($from,$fresh)
if((Test-Path -LiteralPath $from) -or -not (Test-Path -LiteralPath $fresh)){throw 'Preservation move failed'}
""",
    )


def test_bounded_git_reads_report_actual_failure(tmp_path):
    run_helpers(
        tmp_path,
        r"""
$git='C:\Program Files\Git\cmd\git.exe';$root=$fixture
$refused=$false;try{$null=ReadBoundedGit 'rev-parse HEAD'}catch{$refused=$true}
if(-not $refused){throw 'Git failure accepted as a binding'}
""",
    )


def test_source_directory_rejects_unreviewed_imports_and_native_modules(tmp_path):
    run_helpers(
        tmp_path,
        r"""
$known=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$null=$known.Add($PSCommandPath) # The test harness itself lives in this fixture.
$moves=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$reviewed=Join-Path $fixture 'reviewed.py';[IO.File]::WriteAllText($reviewed,'reviewed');$null=$known.Add($reviewed)
VerifySourceDirectory $fixture $known $moves $fixture
foreach($name in @('discord.py','dotenv.py','sitecustomize.py','module.pyw','native.pyd','cache.pyc','taskkill.exe','tool.com','tool.cmd','tool.bat','tool.ps1','tool.dll','tool.vbs','tool.js','tool.hta','tool.lnk')){
 $unexpected=Join-Path $fixture $name;[IO.File]::WriteAllText($unexpected,'unreviewed')
 $refused=$false;try{VerifySourceDirectory $fixture $known $moves $fixture}catch{$refused=$true}
 if(-not $refused){throw 'Unreviewed executable accepted'}
 [IO.File]::Delete($unexpected)
}
$reviewedScript=Join-Path $fixture 'reviewed.ps1';[IO.File]::WriteAllText($reviewedScript,'reviewed');$null=$known.Add($reviewedScript)
VerifySourceDirectory $fixture $known $moves $fixture
$unexpected=Join-Path $fixture 'telemetry';$null=[IO.Directory]::CreateDirectory($unexpected)
$refused=$false;try{VerifySourceDirectory $fixture $known $moves $fixture}catch{$refused=$true}
if(-not $refused){throw 'Unreviewed package accepted'}
$null=$known.Add($unexpected);VerifySourceDirectory $fixture $known $moves $fixture
""",
    )


def test_runtime_inventory_includes_imported_telemetry_and_rejects_native_shadow(tmp_path):
    repo = SCRIPT.parents[1]
    tree = ast.parse((repo / "scripts/run_export_authority.py").read_text(encoding="utf-8"))
    inventory = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "code_files"
    )
    namespace = {"os": os, "Path": Path, "AuthorityStartupError": RuntimeError}
    exec(
        compile(ast.Module(body=[inventory], type_ignores=[]), "run_export_authority.py", "exec"),
        namespace,
    )
    package = tmp_path / "telemetry"
    dal = package / "dal"
    dal.mkdir(parents=True)
    members = [
        "telemetry/__init__.py",
        "telemetry/service.py",
        "telemetry/dal/__init__.py",
        "telemetry/dal/command_usage_dal.py",
    ]
    for member in members:
        (tmp_path / member).write_text("# reviewed fixture\n", encoding="utf-8")
    assert namespace["code_files"](tmp_path) == set(members)
    (package / "service.pyd").write_bytes(b"unreviewed fixture")
    with pytest.raises(RuntimeError, match="Unreviewed executable"):
        namespace["code_files"](tmp_path, inspect_directory=lambda _: None)


def test_supervisor_stops_owned_stalled_worker_and_retains_receipt(tmp_path):
    run_helpers(
        tmp_path,
        r"""
$progress=Join-Path $fixture 'progress';[IO.File]::WriteAllText($progress,'initial')
$receipt=Join-Path $fixture 'receipt.jsonl'
$sentinel=Join-Path $fixture 'must-not-finish'
$command="[Console]::WriteLine('partial');Start-Sleep -Seconds 4;[IO.File]::WriteAllText('"+$sentinel.Replace("'","''")+"','unexpected')"
$refused=$false
try{$null=InvokeBoundedWorker $command $progress $receipt 300}catch{$refused=$true;if(-not (Test-Path -LiteralPath $receipt)){throw $_}}
if(-not $refused -or (Test-Path -LiteralPath $sentinel)){throw 'Stalled worker continued'}
if(-not (([IO.File]::ReadAllText($receipt)).Contains('STOP_INCOMPLETE_SUPERVISOR'))){throw 'Missing reconciliation receipt'}
""",
    )


def test_supervisor_allows_progress_without_a_total_duration_cap(tmp_path):
    run_helpers(
        tmp_path,
        r"""
$progress=Join-Path $fixture 'progress';[IO.File]::WriteAllText($progress,'initial')
$receipt=Join-Path $fixture 'receipt.jsonl'
$command="1..15 | ForEach-Object {[IO.File]::WriteAllText('"+$progress.Replace("'","''")+"',[guid]::NewGuid().ToString());Start-Sleep -Milliseconds 100};[Console]::WriteLine('completed')"
$null=InvokeBoundedWorker $command $progress $receipt 1000
if([IO.File]::ReadAllText($receipt).Trim() -cne 'completed'){throw 'Progressing worker failed'}
""",
    )


def test_public_entry_rejects_bad_plan_without_installation(tmp_path):
    copy = tmp_path / SCRIPT.name
    copy.write_bytes(SCRIPT.read_bytes())
    plan = tmp_path / "plan.json"
    plan.write_text("{}", encoding="utf-8")
    result = subprocess.run(
        [
            r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(copy),
            "-PlanPath",
            str(plan),
            "-ExpectedPlanSHA256",
            "0" * 64,
        ],
        capture_output=True,
        text=True,
        timeout=20,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    assert result.returncode != 0
    receipts = list(tmp_path.glob("source-boundary-receipt-*.jsonl"))
    assert len(receipts) == 1
    text = receipts[0].read_text(encoding="utf-8-sig")
    assert "STOP_INCOMPLETE" in text
    assert "installation_started" not in text


def test_real_pid_writers_use_writable_logs_with_readonly_source(tmp_path):
    """Execute the actual PID writer bodies without importing either startup module."""
    import aiofiles
    import win32api
    import win32security

    root = tmp_path / "source"
    logs = root / "logs"
    logs.mkdir(parents=True)
    repo = SCRIPT.parents[1]
    namespace = {"os": os, "Path": Path, "LOG_DIR": str(logs), "logger": Mock(), "log": Mock()}
    constants = ast.parse((repo / "constants.py").read_text(encoding="utf-8"))
    pid_constant = next(
        node
        for node in constants.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "BOT_PID_PATH" for t in node.targets)
    )
    exec(
        compile(ast.Module(body=[pid_constant], type_ignores=[]), "constants.py", "exec"), namespace
    )
    child = ast.parse((repo / "DL_bot.py").read_text(encoding="utf-8"))
    selected = [
        node
        for node in child.body
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "BOT_PID_FILE" for t in node.targets)
        )
        or (isinstance(node, ast.FunctionDef) and node.name == "_write_child_pid_file")
    ]
    exec(compile(ast.Module(body=selected, type_ignores=[]), "DL_bot.py", "exec"), namespace)
    watchdog = ast.parse((repo / "run_bot.py").read_text(encoding="utf-8"))
    pid_assignment = next(
        node
        for node in watchdog.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "pid_path" for t in node.targets)
    )
    pid_write = next(
        node
        for node in ast.walk(watchdog)
        if isinstance(node, ast.Try)
        and any(
            isinstance(t, ast.Assign)
            and any(isinstance(n, ast.Name) and n.id == "tmp_path" for n in t.targets)
            for t in node.body
        )
    )
    namespace["child"] = SimpleNamespace(pid=12345)
    token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), 8)
    try:
        sid, _ = win32security.GetTokenInformation(token, win32security.TokenUser)
    finally:
        token.Close()
    original = win32security.GetNamedSecurityInfo(str(root), 1, 4)
    logs_original = win32security.GetNamedSecurityInfo(str(logs), 1, 4)
    protected = 4 | win32security.PROTECTED_DACL_SECURITY_INFORMATION
    state_acl = win32security.ACL()
    state_acl.AddAccessAllowedAce(2, 0x1F01FF, sid)
    source_acl = win32security.ACL()
    source_acl.AddAccessAllowedAce(2, 0x1200A9, sid)
    try:
        win32security.SetNamedSecurityInfo(str(logs), 1, protected, None, None, state_acl, None)
        win32security.SetNamedSecurityInfo(str(root), 1, protected, None, None, source_acl, None)
        with pytest.raises(PermissionError):
            (root / "bot_pid.tmp").write_text("blocked")
        namespace["_write_child_pid_file"]()
        assert (logs / "bot_pid.txt").read_text() == str(os.getpid())
        exec(
            compile(
                ast.Module(body=[pid_assignment, pid_write], type_ignores=[]), "run_bot.py", "exec"
            ),
            namespace,
        )
        assert (logs / "bot_pid.txt").read_text() == "12345"
        assert not (root / "bot_pid.txt").exists()
        # Execute the actual audit writer with the same read-only source boundary.
        audit_constant = next(
            node
            for node in constants.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(t, ast.Name) and t.id == "EMBED_AUDIT_LOG_PATH" for t in node.targets
            )
        )
        exec(
            compile(ast.Module(body=[audit_constant], type_ignores=[]), "constants.py", "exec"),
            namespace,
        )
        namespace.update(
            aiofiles=aiofiles,
            discord=SimpleNamespace(
                Embed=object, utils=SimpleNamespace(utcnow=lambda: datetime.now(UTC))
            ),
        )
        audit_tree = ast.parse((repo / "embed_utils.py").read_text(encoding="utf-8"))
        audit_writer = next(
            node
            for node in audit_tree.body
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "log_embed_to_file"
        )
        exec(
            compile(ast.Module(body=[audit_writer], type_ignores=[]), "embed_utils.py", "exec"),
            namespace,
        )
        embed = SimpleNamespace(title="audit-title", description="audit-description")
        asyncio.run(namespace["log_embed_to_file"](embed))
        asyncio.run(namespace["log_embed_to_file"](embed))
        audit_lines = (logs / "embed_audit.log").read_text(encoding="utf-8").splitlines()
        assert len(audit_lines) == 2
        assert all("audit-title - audit-description" in line for line in audit_lines)
        assert not (root / "embed_audit.log").exists()
    finally:
        for path, saved in [(root, original), (logs, logs_original)]:
            flags = 4 | (
                win32security.PROTECTED_DACL_SECURITY_INFORMATION
                if saved.GetSecurityDescriptorControl()[0] & 0x1000
                else win32security.UNPROTECTED_DACL_SECURITY_INFORMATION
            )
            win32security.SetNamedSecurityInfo(
                str(path), 1, flags, None, None, saved.GetSecurityDescriptorDacl(), None
            )
