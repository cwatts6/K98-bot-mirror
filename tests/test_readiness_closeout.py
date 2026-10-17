"""The reviewed restart chain is not inferred from age, task exit or missing PIDs."""

from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import subprocess

import pytest

from scripts.package_k98_readiness_closeout import BODY, build, profile_from_diagnostic
from scripts.verify_k98_readiness_closeout import checked_read, verify_chain


def chain():
    predecessor = dict(sequence=21, publication=dict(manifests=dict(authority="a" * 64)))
    journals = [
        dict(sequence=22 + n, policy_sha256="p", publication=dict(manifests=dict(authority=c * 64)))
        for n, c in enumerate("bc")
    ]
    now = datetime(2026, 10, 17)
    sessions = [
        dict(
            SessionID=str(n),
            AuthorityPrincipal="S11_ExportApplication",
            HostIdentity="mini_AMD",
            ManifestHash=c.upper() * 64,
            State="open" if n == 2 else "closed",
            Version=1 if n == 2 else 2,
            CreatedUTC=now + timedelta(minutes=n * 2),
            ClosedUTC=None if n == 2 else now + timedelta(minutes=n * 2 + 1),
        )
        for n, c in enumerate("abc")
    ]
    config = dict(
        release_id="r", target="t", new_policy_sha256="p", old_journal=dict(Record=predecessor)
    )
    profile = dict(
        release_id="r",
        target="t",
        policy_sha256="p",
        journals=[{}, {}],
        sessions=["0", "1", "2"],
        current_session="2",
    )
    return config, profile, predecessor, journals, sessions


def test_exact_closed_closed_open_chain_verifies_without_historical_readiness():
    verify_chain(*chain())


@pytest.mark.parametrize(
    "fault",
    [
        "release",
        "target",
        "policy",
        "predecessor",
        "extra_journal",
        "sequence",
        "current_session",
        "extra_session",
        "overlap",
        "unclosed",
        "version",
        "principal",
        "manifest",
        "close_time",
    ],
)
def test_bad_chain_never_verifies(fault):
    config, profile, predecessor, journals, sessions = deepcopy(chain())
    if fault in {"release", "target", "policy"}:
        config[
            {"release": "release_id", "target": "target", "policy": "new_policy_sha256"}[fault]
        ] = "other"
    elif fault == "predecessor":
        config["old_journal"] = dict(Record={})
    elif fault == "extra_journal":
        journals.append(deepcopy(journals[-1]))
    elif fault == "sequence":
        journals[-1]["sequence"] += 1
    elif fault == "current_session":
        profile["current_session"] = "0"
    elif fault == "extra_session":
        sessions.append(dict(sessions[-1], SessionID="3"))
    elif fault == "overlap":
        sessions[0]["ClosedUTC"] = sessions[1]["CreatedUTC"] + timedelta(seconds=1)
    elif fault == "unclosed":
        sessions[1]["State"] = "open"
    elif fault == "version":
        sessions[2]["Version"] = 2
    elif fault == "principal":
        sessions[2]["AuthorityPrincipal"] = "other"
    elif fault == "manifest":
        sessions[2]["ManifestHash"] = "f" * 64
    else:
        sessions[1]["ClosedUTC"] = None
    with pytest.raises(ValueError):
        verify_chain(config, profile, predecessor, journals, sessions)


def test_checked_read_rejects_altered_and_oversized_bytes(tmp_path):
    import hashlib

    path = tmp_path / "profile.json"
    path.write_bytes(b"abc")
    sha = hashlib.sha256(b"abc").hexdigest()
    assert checked_read(path, sha) == b"abc"
    with pytest.raises(ValueError):
        checked_read(path, sha, limit=2)
    path.write_bytes(b"abd")
    with pytest.raises(ValueError):
        checked_read(path, sha)


def test_package_uses_reviewed_custody_bootstrap_and_no_apply_or_restart():
    # The launcher has no step-runner, SQL mutation or task-start call.
    assert "Assert-HistoricalRecords" in BODY
    assert BODY.count("$proof=Verify-Current") == 2
    assert "CONFIRM ONLINE" in BODY
    assert "Write-AtomicRecord $completePath $acceptance" in BODY
    assert "current_successor_admin_verified_v1" in BODY
    assert "-Resume" not in BODY and "Start-ScheduledTask" not in BODY


def diagnostic():
    from scripts.package_k98_readiness_closeout import RELEASE

    return dict(
        format="k98-readiness-diagnostic-v1",
        errors=[],
        sections=dict(
            binding=dict(
                release_id=RELEASE,
                original_sha256="a" * 64,
                selected_sha256="a" * 64,
                new_policy_sha256="b" * 64,
                target="471742d76a21f1ab888a6c20741bcba341df80fd",
            ),
            readiness_status_exists=False,
            start=dict(sha256="c" * 64),
            successor_journals=[
                dict(
                    name=f"incarnation-{n:020d}-00000000-0000-0000-0000-000000000000.json",
                    sha256="d" * 64,
                    record=dict(sequence=n),
                )
                for n in (22, 23)
            ],
            receipts=[
                dict(name=f"{step}.{suffix}.json", step=step, stage=stage, sha256="e" * 64)
                for step in ("source", "seed", "start", "readiness")
                for suffix, stage in (("intent", "starting"), ("complete", "verified"))
                if not (step == "readiness" and suffix == "complete")
            ],
            recent_sessions=[
                dict(SessionID=f"00000000-0000-0000-0000-{n:012d}", State=state)
                for n, state in enumerate(("open", "closed", "closed"))
            ],
        ),
    )


@pytest.mark.parametrize(
    "fault",
    [None, "receipt_path", "receipt_state", "hash", "target", "session", "extra_incarnation"],
)
def test_package_rejects_unreviewed_diagnostic_shapes(fault):
    d = diagnostic()
    s = d["sections"]
    if fault == "receipt_path":
        s["receipts"][0]["name"] = "../escape"
    elif fault == "receipt_state":
        s["receipts"][0]["stage"] = "verified"
    elif fault == "hash":
        s["binding"]["new_policy_sha256"] = "not a hash"
    elif fault == "target":
        s["binding"]["target"] = "other"
    elif fault == "session":
        s["recent_sessions"][0]["SessionID"] = "invalid"
    elif fault == "extra_incarnation":
        s["successor_journals"].append(s["successor_journals"][-1])
    if fault:
        with pytest.raises(ValueError):
            profile_from_diagnostic(d)
    else:
        result = build(d, b"reviewed helper")
        assert b"__PROFILE__" not in result and b"__HELPER__" not in result
        assert b"function Assert-Custody" in result


def test_powershell_acceptance_write_is_atomic_restart_safe_and_preserves_receipts(tmp_path):
    """Exercise actual closeout writer statements with disposable ACL substitution."""
    if not shutil.which("powershell.exe"):
        pytest.skip("Windows PowerShell required")
    root = Path(__file__).resolve().parents[1]
    script = tmp_path / "closeout.ps1"
    script.write_text(
        r"""
param([string]$Library,[string]$Fixture)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. $Library -Action Library
function Assert-Protected([string]$Path){}
function Write-New([string]$Path,[byte[]]$Bytes){
 $stream=[IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
 try{$stream.Write($Bytes,0,$Bytes.Length)}finally{$stream.Dispose()}
}
$completePath=Join-Path $Fixture 'verified.json'
$priorPath=Join-Path $Fixture 'readiness.intent.json'
[IO.File]::WriteAllText($priorPath,'original intent stays unconfirmed')
$before=Hash ([IO.File]::ReadAllBytes($priorPath))
$acceptance=@{release_id='r';target='t';closeout_kind='current_successor_admin_verified_v1';current_successor=@{sequence=23};readiness=@{original_readiness='unconfirmed_preserved'}}|ConvertTo-Json -Depth 10|ConvertFrom-Json
Write-AtomicRecord $completePath $acceptance
$saved=Read-Json $completePath
if(-not(Same $saved $acceptance)){throw 'Readback differs'}
$refused=$false;try{Write-AtomicRecord $completePath $acceptance}catch{$refused=$true}
if(-not $refused){throw 'Existing immutable closeout overwritten'}
if((Hash ([IO.File]::ReadAllBytes($priorPath))) -cne $before){throw 'Original intent changed'}
if(@(Get-ChildItem -LiteralPath $Fixture -Filter 'pending-*').Count -ne 1){throw 'Interrupted evidence was lost'}
'PASS'
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(script),
            "-Library",
            str(root / "scripts/K98-SourceUpdate.ps1"),
            "-Fixture",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout


@pytest.mark.parametrize(
    "answer,changed,existing",
    [
        ("", False, False),
        ("CONFIRM ONLINE", False, False),
        ("CONFIRM ONLINE", True, False),
        ("", False, True),
        ("", True, True),
    ],
)
def test_actual_guided_closeout_statements_recheck_after_confirmation(
    tmp_path, answer, changed, existing
):
    import hashlib
    import json

    if not shutil.which("powershell.exe"):
        pytest.skip("Windows PowerShell required")
    root = Path(__file__).resolve().parents[1]
    statements = BODY[
        BODY.index(" $proof=Verify-Current") : BODY.index("} finally {$lock.Dispose()}")
    ]
    script = tmp_path / "guided.ps1"
    prelude = r"""
param([string]$Library,[string]$Fixture,[string]$Answer,[int]$Changed,[int]$Existing)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. $Library -Action Library
function Assert-Protected([string]$Path){}
function Write-New([string]$Path,[byte[]]$Bytes){
 $stream=[IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
 try{$stream.Write($Bytes,0,$Bytes.Length)}finally{$stream.Dispose()}
}
$profile=[pscustomobject]@{release_id='r';target='t'}
$profileBytes=[byte[]]@(1);$helperBytes=[byte[]]@(2);$sid='fixture'
$completePath=Join-Path $Fixture 'verified.json'
$script:checks=0
function Verify-Current {
 $script:checks++
 [IO.File]::AppendAllText((Join-Path $Fixture 'checks.txt'),'checked;')
 if($Changed -and ($Existing -or $script:checks -eq 2)){throw 'Current identity changed'}
 return [pscustomobject]@{stage='CURRENT_SUCCESSOR_VERIFIED';sequence=23}
}
function Assert-HistoricalRecords {}
function Read-Host([string]$Prompt){return $Answer}
"""
    acceptance = tmp_path / "verified.json"
    if existing:
        acceptance.write_text(
            json.dumps(
                dict(
                    release_id="r",
                    target="t",
                    closeout_kind="current_successor_admin_verified_v1",
                    profile_sha256=hashlib.sha256(bytes([1])).hexdigest(),
                    helper_sha256=hashlib.sha256(bytes([2])).hexdigest(),
                )
            ),
            encoding="utf-8",
        )
        before = acceptance.read_bytes()
    script.write_text(prelude + statements, encoding="utf-8")
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(script),
            "-Library",
            str(root / "scripts/K98-SourceUpdate.ps1"),
            "-Fixture",
            str(tmp_path),
            "-Answer",
            answer or "DECLINE",
            "-Changed",
            str(int(changed)),
            "-Existing",
            str(int(existing)),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert (result.returncode != 0) == changed, result.stdout + result.stderr
    assert acceptance.exists() == bool(existing or (answer and not changed))
    assert (tmp_path / "checks.txt").read_text().count("checked;") == (
        1 if existing or not answer else 2
    )
    if existing:
        assert acceptance.read_bytes() == before
        assert (
            "already recorded and its current successor has been reverified" in result.stdout
        ) == (not changed)
