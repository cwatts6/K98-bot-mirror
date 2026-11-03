"""A failed pre-incarnation attempt is preserved, never reset or replayed."""

import base64
from copy import deepcopy
import json
import os
from pathlib import Path, PureWindowsPath
import shutil
import subprocess
from uuid import uuid4

import pytest

from scripts import (
    package_k98_startup_correction as packaging,
    prepare_k98_startup_correction as correction,
)

ROOT = Path(__file__).resolve().parents[1]
RECOVERY = "11111111-2222-4333-8444-555555555555"


def profile():
    release = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
    stage = rf"C:\ProgramData\K98\S11\automatic-startup\{RECOVERY}\release-{release}"
    return dict(
        release_id=release,
        recovery_id=RECOVERY,
        stage=stage,
        work=rf"C:\ProgramData\K98\S11\updates\{release}",
        bindings=str(PureWindowsPath(stage) / "ReleaseBindings.json"),
        bindings_sha256="a" * 64,
        manifest_sha256="b" * 64,
        library_sha256="c" * 64,
        failed_target=correction.FAILED_TARGET,
        target="1" * 40,
        receipts={name: "d" * 64 for name in packaging.RECEIPTS},
        start_request=dict(
            release_id=release, requested_utc="2026-11-03T08:40:53.2318670Z", log_offset=123
        ),
    )


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "extra",
        "id",
        "stage",
        "work",
        "bindings",
        "hash",
        "receipt",
        "target",
        "start",
        "offset",
    ],
)
def test_packaging_requires_exact_reviewed_incident_profile(damage):
    value = profile()
    if damage == "extra":
        value["override"] = True
    elif damage == "id":
        value["recovery_id"] = value["release_id"]
    elif damage in {"stage", "work", "bindings"}:
        value[damage] += "\\..\\other"
    elif damage == "hash":
        value["bindings_sha256"] = "A" * 64
    elif damage == "receipt":
        value["receipts"]["start.complete.json"] = "e" * 64
    elif damage == "target":
        value["target"] = value["failed_target"]
    elif damage == "start":
        value["start_request"]["release_id"] = RECOVERY
    elif damage == "offset":
        value["start_request"]["log_offset"] = True
    if damage:
        with pytest.raises(ValueError):
            packaging.validate_profile(value)
    else:
        packaging.validate_profile(value)


def test_packaged_recovery_authenticates_tools_and_parses_in_powershell(tmp_path):
    from tests.updater_source_assertions import installed_tool_fixture

    tools, _ = installed_tool_fixture(tmp_path)
    payload = {p.name: p.read_bytes() for p in tools.iterdir()}
    value = profile()
    value["library_sha256"] = correction.digest(payload["K98-SourceUpdate.ps1"])
    helper = (ROOT / "scripts/prepare_k98_startup_correction.py").read_bytes()
    template = (ROOT / "scripts/Recover-K98StartupEvidence.ps1").read_text()
    script = packaging.build(value, payload, helper, template)
    assert b"param([ValidateSet('Inspect','Apply')]" in script
    assert b"'__PROFILE__'" not in script and b"'__PAYLOAD__'" not in script
    with pytest.raises(ValueError, match="exact installed"):
        packaging.build(
            value, dict(payload, **{"K98-SourceUpdate.ps1": b"changed"}), helper, template
        )
    powershell = shutil.which("powershell.exe")
    if not powershell:
        return  # Package-byte checks above also run on Linux.
    path = tmp_path / "built.ps1"
    path.write_bytes(script)
    parser = tmp_path / "parse.ps1"
    parser.write_text(
        "param([string]$Path)\n$t=$null;$e=$null;$null=[Management.Automation.Language.Parser]::ParseFile($Path,[ref]$t,[ref]$e);if($e.Count){$e|Out-String|Write-Error;exit 1}",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(parser),
            "-Path",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_full_normal_packet_transforms_with_authenticated_issuer_and_complete_seed(
    tmp_path, monkeypatch
):
    from core.export_release_seed import successor_seed
    from scripts.prepare_k98_update import prepare_update
    from tests.test_export_release_seed import predecessor
    from tests.updater_source_assertions import installed_tool_fixture

    tools, archive_hash = installed_tool_fixture(tmp_path)
    issuer = (ROOT / correction.ISSUER).read_bytes().replace(b"\r\n", b"\n")
    fixed = b"""\n        def inspect_evidence():
            # Runtime evidence is writable by the verified application identity.
            # Source, policy and history still use administrative_inspector.
            return launcher["protected_path"](
                authority["evidence_root"], private=True, identity=sid
            )

        evidence_root = inspect_evidence()"""
    assert issuer.count(fixed) == 1
    old_issuer = issuer.replace(
        fixed, b'        evidence_root = inspect(authority["evidence_root"], private=True)'
    )
    old_issuer = old_issuer.replace(
        b"check_boundary=inspect_evidence,",
        b'check_boundary=lambda: inspect(authority["evidence_root"], private=True),',
    )
    assert (
        correction.digest(old_issuer)
        == "e701d805aa8103cdf62827b23fd50852bc0bfb9488e97352ae9ef689164495ea"
    )
    initial = predecessor(tmp_path, monkeypatch)
    # Production seed publication paths include the deployment identity. The
    # generic pair fixture otherwise keeps a stable temporary publication path.
    initial["ManualProcessPairPlan-CANDIDATE.json"][
        "commit_file"
    ] = r"C:\K98\reviewed-deployment\commit.json"
    initial["AutomaticStartupPolicy.json"]["seed_plan"]["sha256"] = correction.digest(
        correction.encode(initial["ManualProcessPairPlan-CANDIDATE.json"])
    )
    seed = {
        name: json.loads(raw)
        for name, raw in successor_seed(
            initial,
            {correction.ISSUER: correction.digest(old_issuer)},
            deployment_id=str(uuid4()),
            review_id=str(uuid4()),
            pipe_id=str(uuid4()),
        ).items()
    }
    original, _ = packet()
    policy = seed["AutomaticStartupPolicy.json"]
    old_policy = initial["AutomaticStartupPolicy.json"]
    original.update(
        contract_verifier_sha256=archive_hash,
        new_policy=policy,
        new_policy_sha256=correction.digest(correction.encode(policy)),
        new_seed_directory=str(PureWindowsPath(policy["seed_plan"]["path"]).parent),
        new_state_directory=policy["state_directory"],
        new_pins=policy["source_hashes"],
        flags=policy["flags"],
        old_policy=dict(
            Path=str(
                PureWindowsPath(old_policy["seed_plan"]["path"]).with_name(
                    "AutomaticStartupPolicy.json"
                )
            ),
            SHA256=policy["predecessor"]["policy_sha256"],
            StateDirectory=old_policy["state_directory"],
        ),
        old_plan=dict(Python=r"C:\fixture\python.exe", PythonSHA256="b" * 64),
        sid="S-1-5-21-1-2-3-1001",
    )
    observed = deepcopy(original)
    observed.update(
        before=correction.FAILED_TARGET,
        target="1" * 40,
        old_policy=dict(
            Path=str(
                PureWindowsPath(original["new_seed_directory"]) / "AutomaticStartupPolicy.json"
            ),
            SHA256=original["new_policy_sha256"],
            StateDirectory=original["new_state_directory"],
        ),
    )
    blobs = {
        (correction.FAILED_TARGET, correction.ISSUER): old_issuer,
        ("1" * 40, correction.ISSUER): issuer,
    }
    changes = [correction.ISSUER]
    for name in (
        "Recover-K98StartupEvidence.ps1",
        "prepare_k98_startup_correction.py",
        "package_k98_startup_correction.py",
    ):
        path = "scripts/" + name
        changes.append(path)
        blobs["1" * 40, path] = (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
    gate = f"$policy='{observed['old_policy']['Path']}'\n$policyHash='{original['new_policy_sha256']}'\n"
    prepared = prepare_update(
        dict(seed=seed, gate=gate, bindings=observed),
        changes,
        lambda *key: blobs.get(key),
        tmp_path / "candidate",
        tools,
    )
    folder = Path(prepared["manifest"]).parent
    manifest = json.loads(Path(prepared["manifest"]).read_bytes())
    files = {m["name"]: (folder / m["name"]).read_bytes() for m in manifest["members"]}
    corrected = correction.correction_files(original, files, recovery_id=RECOVERY, target="1" * 40)
    binding = json.loads(corrected["ReleaseBindings.json"])
    assert binding["new_policy"]["predecessor"] == policy["predecessor"]
    for name in (
        "authority-template.json",
        "bot-template.json",
        "ManualProcessPairPlan-CANDIDATE.json",
    ):
        assert corrected[name] == files[name]
    for member in binding["seed_members"] + binding["extra_members"]:
        assert correction.digest(corrected[member["name"]]) == member["sha256"]
    assert binding["old_journal"] == original["old_journal"]
    assert binding["old_session"] == original["old_session"]
    assert binding["new_policy"]["flags"] == original["flags"]
    assert set(binding["new_pins"]) == {
        correction.ISSUER,
        "scripts/prepare_k98_startup_correction.py",
        "scripts/package_k98_startup_correction.py",
    }


def packet():
    issuer = (ROOT / correction.ISSUER).read_bytes().replace(b"\r\n", b"\n")
    original = dict(
        release_id="aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
        target=correction.FAILED_TARGET,
        old_policy=dict(
            Path=r"C:\old\AutomaticStartupPolicy.json",
            SHA256="a" * 64,
            StateDirectory=r"C:\old-history",
        ),
        old_plan=dict(Python="python", PythonSHA256="b" * 64),
        new_seed_directory=r"C:\failed-seed",
        new_state_directory=r"C:\failed-history",
        new_policy_sha256="c" * 64,
        new_pins={correction.ISSUER: "d" * 64},
        flags=dict(EXPORT_COORDINATION_ENABLED=True),
        old_journal=dict(sequence=12),
        old_native=[dict(PID=7)],
        old_session=dict(State="open"),
        expected_preparation=[dict(Version=7)],
        expected_resources=[dict(Fence=12)],
        root="C:\\bot",
        host="MINI_AMD",
        sid="sid",
        account="account",
        git_path="git",
        git_sha256="e" * 64,
        venv=dict(path="python", sha256="b" * 64),
        contract_verifier_sha256="f" * 64,
    )
    original["new_policy"] = dict(
        predecessor=dict(policy_sha256="a" * 64, state_directory=r"C:\old-history")
    )
    binding = deepcopy(original)
    policy = dict(
        predecessor=dict(policy_sha256="c" * 64, state_directory=r"C:\failed-history"),
        state_directory=r"C:\fresh-history",
        seed_plan=dict(path=r"C:\fresh-seed\ManualProcessPairPlan-CANDIDATE.json"),
    )
    raw_policy = correction.encode(policy)
    gate = ("$policyHash='" + correction.digest(raw_policy) + "'\n").encode()
    binding.update(
        before=correction.FAILED_TARGET,
        target="1" * 40,
        old_pins=original["new_pins"],
        new_pins={correction.ISSUER: correction.digest(issuer)},
        old_policy=dict(
            Path=r"C:\failed-seed\AutomaticStartupPolicy.json",
            SHA256="c" * 64,
            StateDirectory=r"C:\failed-history",
        ),
        old_gate=dict(Path=r"C:\failed-seed\Start-ReviewedAutomaticStartup.ps1", SHA256="9" * 64),
        new_seed_directory=r"C:\fresh-seed",
        new_state_directory=r"C:\fresh-history",
        new_policy=policy,
        new_policy_sha256=correction.digest(raw_policy),
        source_members=[
            dict(
                path=correction.ISSUER,
                payload="source-0000.bin",
                target_sha256=correction.digest(issuer),
            )
        ],
        seed_members=[
            dict(name=name, sha256=correction.digest(raw))
            for name, raw in (
                ("AutomaticStartupPolicy.json", raw_policy),
                ("Start-ReviewedAutomaticStartup.ps1", gate),
            )
        ],
    )
    files = {
        "ReleaseBindings.json": correction.encode(binding),
        "AutomaticStartupPolicy.json": raw_policy,
        "Start-ReviewedAutomaticStartup.ps1": gate,
        "source-0000.bin": issuer,
        "Release-Step.ps1": (ROOT / "scripts/K98-SourceUpdate.ps1")
        .read_bytes()
        .replace(b"\r\n", b"\n"),
    }
    return original, files


def test_correction_preserves_original_and_rebinds_only_unused_candidate():
    original, files = packet()
    before = deepcopy((original, files))
    result = correction.correction_files(original, files, recovery_id=RECOVERY, target="1" * 40)
    assert (original, files) == before
    binding = json.loads(result["ReleaseBindings.json"])
    policy = json.loads(result["AutomaticStartupPolicy.json"])
    assert policy["predecessor"] == original["new_policy"]["predecessor"]
    assert binding["old_policy"] == original["old_policy"]
    assert binding["old_pins"] == original["new_pins"]
    assert binding["release_id"] == original["release_id"]
    assert binding["new_policy_sha256"] == correction.digest(result["AutomaticStartupPolicy.json"])
    assert binding["new_policy_sha256"].encode() in result["Start-ReviewedAutomaticStartup.ps1"]
    assert result["source-0000.bin"] == files["source-0000.bin"]
    assert ("before-recovery-" + RECOVERY).encode() in result["Release-Step.ps1"]
    for member in binding["seed_members"]:
        assert member["sha256"] == correction.digest(result[member["name"]])


@pytest.mark.parametrize(
    "damage",
    [
        "target",
        "sql",
        "lineage",
        "old_pin",
        "flags",
        "ownership",
        "host",
        "history",
        "issuer",
        "gate",
        "adapter",
    ],
)
def test_correction_refuses_changed_preconditions(damage):
    original, files = packet()
    binding = json.loads(files["ReleaseBindings.json"])
    if damage == "target":
        original["target"] = "2" * 40
    elif damage == "sql":
        original["sql"] = {}
    elif damage == "lineage":
        original["new_policy"]["predecessor"]["policy_sha256"] = "0" * 64
    elif damage == "old_pin":
        binding["old_pins"] = {}
    elif damage == "flags":
        binding["flags"] = {}
    elif damage == "ownership":
        binding["expected_resources"][0]["Fence"] += 1
    elif damage == "host":
        binding["host"] = "other"
    elif damage == "history":
        binding["new_state_directory"] = original["new_state_directory"]
    elif damage == "issuer":
        files["source-0000.bin"] += b"# unreviewed\n"
    elif damage == "gate":
        files["Start-ReviewedAutomaticStartup.ps1"] *= 2
    else:
        files["Release-Step.ps1"] = b"# unreviewed adapter\n"
    files["ReleaseBindings.json"] = correction.encode(binding)
    with pytest.raises(ValueError):
        correction.correction_files(original, files, recovery_id=RECOVERY, target="1" * 40)


def inspect_fixture(tmp_path, damage=None):
    powershell = shutil.which("powershell.exe")
    if not powershell:
        pytest.skip("Windows PowerShell required")
    stage, work, history, seed = [tmp_path / name for name in ("stage", "work", "history", "seed")]
    updates = tmp_path / "updates"
    for directory in (stage, work, history, seed, updates, stage / ".receipts"):
        directory.mkdir()
    release = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
    original = dict(
        root=r"C:\discord_file_downloader",
        host="MINI_AMD",
        sid="sid",
        release_id=release,
        target=correction.FAILED_TARGET,
        old_policy=dict(StateDirectory=str(tmp_path)),
        new_state_directory=str(history),
        new_seed_directory=str(seed),
        seed_members=[],
        new_pins={},
    )
    binding_raw = correction.encode(original)
    (stage / "ReleaseBindings.json").write_bytes(binding_raw)
    (stage / ".release.json").write_bytes(b"{}")
    start = dict(release_id=release, requested_utc="2026-11-03T08:40:53.2318670Z", log_offset=123)
    (stage / "start-requested.json").write_bytes(correction.encode(start))
    receipts = {}
    for name in (
        "source.intent.json",
        "source.complete.json",
        "seed.intent.json",
        "seed.complete.json",
        "start.intent.json",
    ):
        raw = correction.encode(dict(name=name))
        (stage / ".receipts" / name).write_bytes(raw)
        receipts[name] = correction.digest(raw)
    (updates / "active.json").write_bytes(
        correction.encode(dict(release_id=release, directory=str(work)))
    )
    (updates / "operator.lock").write_bytes(b"0")
    (tmp_path / ("deployment-" + release + ".lock")).write_bytes(b"0")
    library = tmp_path / "library.ps1"
    adapter = (ROOT / "scripts/K98-SourceUpdate.ps1").read_text()
    same = adapter[
        adapter.index("function Same(") : adapter.index("function Get-GitCredentialManager")
    ]
    library.write_text(
        r"""
param([string]$Action)
function Assert-Protected($Path) {}
function Read-Bytes($Path,$Expected='', $Limit=1MB) {
 $raw=[IO.File]::ReadAllBytes($Path)
 if($Expected -and (Hash $raw) -cne $Expected){throw 'hash differs'}
 return ,$raw
}
function Read-Json($Path,$Expected='') {[Text.Encoding]::UTF8.GetString((Read-Bytes $Path $Expected))|ConvertFrom-Json}
function Assert-Drained {}
function Sessions {if($env:K98_CORRECTION_FIXTURE -ceq 'session'){return ,@(@{State='open'})};return ,@()}
function Get-CimInstance {return @()}
function Assert-Source {}
function Assert-Task {return [pscustomobject]@{Enabled=$true}}
function New-Directory {throw 'WRITE IS FORBIDDEN DURING INSPECT'}
function Write-New {throw 'WRITE IS FORBIDDEN DURING INSPECT'}
""" + same,
        encoding="utf-8",
    )
    profile = dict(
        recovery_id=RECOVERY,
        release_id=release,
        bindings=str(stage / "ReleaseBindings.json"),
        bindings_sha256=correction.digest(binding_raw),
        manifest_sha256=correction.digest(b"{}"),
        library_sha256=correction.digest(library.read_bytes()),
        stage=str(stage),
        work=str(work),
        receipts=receipts,
        start_request=start,
        failed_target=correction.FAILED_TARGET,
        target="1" * 40,
    )
    template = (ROOT / "scripts/Recover-K98StartupEvidence.ps1").read_text()
    template = template.replace(
        "'__PROFILE__'", "'" + base64.b64encode(correction.encode(profile)).decode() + "'"
    )
    template = template.replace("'__PAYLOAD__'", "'e30='")
    template = template.replace(
        r"C:\ProgramData\K98\S11\updater\K98-SourceUpdate.ps1", str(library)
    )
    template = template.replace(r"C:\ProgramData\K98\S11\updates", str(updates))
    preamble = r"""
param([string]$Action='Inspect')
Set-StrictMode -Version Latest;$ErrorActionPreference='Stop'
$sid='sid';$identity=[pscustomobject]@{Owner=[pscustomobject]@{Value='S-1-5-32-544'}}
function Assert-Custody {}
function Hash([byte[]]$Bytes){$h=[Security.Cryptography.SHA256]::Create();try{return ([BitConverter]::ToString($h.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant()}finally{$h.Dispose()}}
"""
    harness = tmp_path / "inspect.ps1"
    harness.write_text(preamble + template, encoding="utf-8")
    if damage == "receipt":
        (stage / ".receipts" / "start.intent.json").write_bytes(b"changed")
    elif damage == "history":
        (history / "incarnation.json").write_bytes(b"{}")
    return harness, profile, original


@pytest.mark.parametrize("damage", [None, "receipt", "history", "session"])
def test_complete_inspect_path_is_read_only_despite_library_parameter_binding(tmp_path, damage):
    harness, _, _ = inspect_fixture(tmp_path, damage)
    powershell = shutil.which("powershell.exe")
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}

    environment = dict(os.environ, K98_CORRECTION_FIXTURE=damage or "none")
    result = subprocess.run(
        [powershell, "-NoProfile", "-NonInteractive", "-File", str(harness), "-Action", "Inspect"],
        capture_output=True,
        text=True,
        timeout=30,
        env=environment,
    )
    assert (result.returncode == 0) is (damage is None), result.stdout + result.stderr
    if damage is None:
        assert json.loads(result.stdout)["stage"] == "STARTUP_CORRECTION_REVIEW_READY"
    assert {
        p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()
    } == before


@pytest.mark.parametrize(
    "outcome", ["verified", "start_unknown", "source_unknown", "readiness_wait"]
)
def test_complete_apply_and_resume_preserve_failed_release(tmp_path, outcome):
    harness, value, original = inspect_fixture(tmp_path)
    destination = tmp_path / "updates" / ("startup-correction-" + RECOVERY)
    directory = destination / ("plan-" + str(uuid4()))
    directory.mkdir(parents=True)
    binding = dict(original, before=correction.FAILED_TARGET, target=value["target"], old_pins={})
    raw = correction.encode(binding)
    (directory / "ReleaseBindings.json").write_bytes(raw)
    plan = dict(
        version=1,
        kind="startup_evidence_correction_v1",
        recovery_id=RECOVERY,
        original_release_id=value["release_id"],
        original_bindings_sha256=value["bindings_sha256"],
        profile_sha256=correction.digest(correction.encode(value)),
        target=value["target"],
        bindings_sha256=correction.digest(raw),
        members=[dict(name="ReleaseBindings.json", sha256=correction.digest(raw))],
    )
    plan_raw = correction.encode(plan)
    (directory / "correction-plan.json").write_bytes(plan_raw)
    (destination / "selected-plan.json").write_bytes(
        correction.encode(
            dict(
                profile_sha256=plan["profile_sha256"],
                directory=str(directory),
                sha256=correction.digest(plan_raw),
            )
        )
    )
    # Exercise the entire orchestrator with disposable files. Only the native
    # custody/task/SQL/adapter boundaries are substituted; stage state and all
    # original/selected hashes and receipt checks execute unchanged.
    substitutes = r"""
function New-Directory($Path){$null=[IO.Directory]::CreateDirectory($Path)}
function Write-New($Path,[byte[]]$Bytes){$s=[IO.File]::Open($Path,'CreateNew','Write','None');try{$s.Write($Bytes,0,$Bytes.Length)}finally{$s.Dispose()}}
function Write-Record($Path,$Value){Write-New $Path ([Text.Encoding]::UTF8.GetBytes(($Value|ConvertTo-Json -Depth 30 -Compress)))}
function Write-AtomicRecord($Path,$Value){Write-Record $Path $Value}
function Initialize-UpdateCustody {Write-New (Join-Path $correctionDirectory 'custody.checked') ([byte[]]@(1))}
function Assert-UpdatePaths {}
function Task {
 $action=[pscustomobject]@{Arguments='failed gate'}
 $actions=[pscustomobject]@{Action=$action};$actions|Add-Member ScriptMethod Item {param($index) $this.Action}
 $t=[pscustomobject]@{Enabled=$true;Definition=[pscustomobject]@{Actions=$actions}}
 $t|Add-Member ScriptMethod GetInstances {return ,@()}
 return $t
}
function Assert-Task {return (Task)}
function Enter-StartupExclusion {
 $script:mutex=New-Object psobject
 $mutex|Add-Member ScriptMethod ReleaseMutex {}
 $mutex|Add-Member ScriptMethod Dispose {}
 $script:mutexOwned=$true
 Assert-QuietPredecessor
}
function Invoke-CorrectionAdapter($Operation){
 Read-CorrectionPlan
 $events=Join-Path $correctionDirectory 'adapter-events.txt'
 [IO.File]::AppendAllText($events,$Operation+"`n")
 $name=switch -Regex ($Operation){'Source$'{'source'};'Seed$'{'seed'};'Start$'{'start'};'Readiness$'{'readiness'}}
 $applied=Join-Path $correctionDirectory ($name+'.applied')
 if($Operation.StartsWith('Verify')){
  if(Test-Path -LiteralPath $applied){
   if($name -ceq 'start' -and $env:K98_CORRECTION_FIXTURE -ceq 'start_unknown'){return 1}
   if($name -ceq 'source' -and $env:K98_CORRECTION_FIXTURE -ceq 'source_unknown'){return 1}
   if($name -ceq 'readiness' -and $env:K98_CORRECTION_FIXTURE -ceq 'readiness_wait'){return 11}
   return 0
  }
  if($name -ceq 'readiness'){return 11};return 10
 }
 if(-not(Test-Path -LiteralPath $applied)){Write-New $applied ([byte[]]@(1))}
 return 0
}
"""
    text = harness.read_text()
    assert text.count("try {\n Assert-Protected $updates") == 1
    harness.write_text(
        text.replace(
            "try {\n Assert-Protected $updates", substitutes + "\ntry {\n Assert-Protected $updates"
        ),
        encoding="utf-8",
    )
    preserved = {p: p.read_bytes() for p in Path(value["stage"]).rglob("*") if p.is_file()}
    powershell = shutil.which("powershell.exe")
    command = [
        powershell,
        "-NoProfile",
        "-NonInteractive",
        "-File",
        str(harness),
        "-Action",
        "Apply",
    ]
    environment = dict(os.environ, K98_CORRECTION_FIXTURE=outcome)
    first = subprocess.run(command, capture_output=True, text=True, timeout=30, env=environment)
    assert (first.returncode == 0) is (outcome == "verified"), first.stdout + first.stderr
    before_resume = (directory / "adapter-events.txt").read_text().splitlines()
    if outcome == "readiness_wait":
        environment["K98_CORRECTION_FIXTURE"] = "verified"
    second = subprocess.run(command, capture_output=True, text=True, timeout=30, env=environment)
    assert (second.returncode == 0) is (outcome in {"verified", "readiness_wait"}), (
        second.stdout + second.stderr
    )
    after_resume = (directory / "adapter-events.txt").read_text().splitlines()
    assert after_resume.count("ApplyStart") == (0 if outcome == "source_unknown" else 1)
    assert not any(x.startswith("Apply") for x in after_resume[len(before_resume) :])
    assert (directory / "custody.checked").read_bytes() == b"\x01"
    assert all(p.read_bytes() == raw for p, raw in preserved.items())
    assert (tmp_path / "updates" / "active.json").exists() is (
        outcome in {"source_unknown", "start_unknown"}
    )
    assert (destination / "complete.json").exists() is (outcome in {"verified", "readiness_wait"})


@pytest.mark.parametrize(
    "scenario,applies,success",
    [
        ("fresh", 1, True),
        ("verified", 0, True),
        ("uncertain", 0, False),
        ("start_intent", 0, False),
        ("start_code11", 0, False),
        ("bad_receipt", 0, False),
        ("apply_failed", 1, False),
        ("post_failed", 1, False),
    ],
)
def test_actual_powershell_stage_never_replays_uncertain_start(
    tmp_path, scenario, applies, success
):
    powershell = shutil.which("powershell.exe")
    if not powershell:
        pytest.skip("Windows PowerShell required")
    receipts = tmp_path / ".receipts"
    receipts.mkdir()
    script = tmp_path / "exercise.ps1"
    script.write_text(
        r"""
param([string]$Template,[string]$Fixture,[string]$Scenario)
Set-StrictMode -Version Latest;$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($Template,[ref]$tokens,[ref]$errors)
if($errors.Count){throw ($errors|Out-String)}
$fn=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Invoke-CorrectionStage'},$true)
. ([scriptblock]::Create($fn.Extent.Text))
$profile=@{release_id='release'};$correctionDirectory=$Fixture
$script:applies=0;$script:verifies=0;$script:quiet=0;$script:released=0
$mutexOwned=$true
$mutex=New-Object psobject
$mutex|Add-Member ScriptMethod ReleaseMutex {$script:released++}
$mutex|Add-Member ScriptMethod Dispose {}
function Assert-QuietPredecessor {$script:quiet++}
function Read-Json($Path){Get-Content -LiteralPath $Path -Raw|ConvertFrom-Json}
function Write-Record($Path,$Value){[IO.File]::WriteAllText($Path,($Value|ConvertTo-Json -Compress))}
function Invoke-CorrectionAdapter($Operation){
 if($Operation -ceq 'apply'){$script:applies++;if($Scenario -ceq 'apply_failed'){return 1};return 0}
 $script:verifies++
 if($Scenario -ceq 'verified'){return 0}
 if($Scenario -ceq 'uncertain'){return 1}
 if($Scenario -ceq 'start_code11'){return 11}
 if($script:verifies -eq 1){return 10}
 if($Scenario -ceq 'post_failed'){return 1}
 return 0
}
if($Scenario -in @('start_intent','bad_receipt')){
 $id=if($Scenario -ceq 'bad_receipt'){'foreign'}else{'release'}
 Write-Record (Join-Path $Fixture '.receipts\start.intent.json') @{release_id=$id;step='start';stage='starting'}
}
try {Invoke-CorrectionStage 'start' 'verify' 'apply';$success=$true}catch{$success=$false}
@{success=$success;applies=$script:applies;released=$script:released;quiet=$script:quiet}|ConvertTo-Json -Compress
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
            "-Template",
            str(ROOT / "scripts/Recover-K98StartupEvidence.ps1"),
            "-Fixture",
            str(tmp_path),
            "-Scenario",
            scenario,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    observed = json.loads(result.stdout)
    assert observed["success"] is success
    assert observed["applies"] == applies
    assert observed["quiet"] == observed["released"] == applies


def test_native_mutex_excludes_other_process_and_detects_abandonment(tmp_path):
    powershell = shutil.which("powershell.exe")
    if not powershell:
        pytest.skip("Windows named mutex qualification")
    harness = tmp_path / "mutex.ps1"
    harness.write_text(
        r"""
param([string]$Template,[string]$Machine,[string]$Role='parent')
Set-StrictMode -Version Latest;$ErrorActionPreference='Stop'
$t=$null;$e=$null;$ast=[Management.Automation.Language.Parser]::ParseFile($Template,[ref]$t,[ref]$e)
if($e.Count){throw ($e|Out-String)}
$fn=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Enter-StartupExclusion'},$true)
# The dev process is not elevated. Substitute only the expected owner and the
# unique LOCAL namespace; retain the actual .NET security/ownership/wait code.
$surrogate=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$body=$fn.Extent.Text.Replace('S-1-5-32-544',$surrogate).Replace('Global\K98.S11.Startup.','Local\K98.Test.Startup.')
. ([scriptblock]::Create($body))
$original=@{new_seed_directory=$env:TEMP};$script:quiet=0;$script:mutex=$null;$script:mutexOwned=$false
function Read-Json {return @{deployment_boundary=@{host=@{machine_guid=$Machine}}}}
function Assert-QuietPredecessor {$script:quiet++}
if($Role -cne 'parent'){
 try {Enter-StartupExclusion;$owned=$true}catch{$owned=$false}
 @{owned=$owned;quiet=$script:quiet}|ConvertTo-Json -Compress
 # Deliberately exit without releasing the successful child acquisition.
 exit 0
}
try {
 Enter-StartupExclusion
 $child=@(& (Join-Path $PSHOME 'powershell.exe') -NoProfile -NonInteractive -File $PSCommandPath -Template $Template -Machine $Machine -Role 'blocked') -join ''
 if($LASTEXITCODE){throw 'Contender failed'}
 $blocked=$child|ConvertFrom-Json
 if($blocked.owned -or $blocked.quiet -ne 0){throw 'A competing process entered the exclusion'}
 $mutex.ReleaseMutex();$script:mutexOwned=$false
 $child=@(& (Join-Path $PSHOME 'powershell.exe') -NoProfile -NonInteractive -File $PSCommandPath -Template $Template -Machine $Machine -Role 'abandon') -join ''
 if($LASTEXITCODE){throw 'Abandonment child failed'}
 $abandon=$child|ConvertFrom-Json
 if(-not $abandon.owned -or $abandon.quiet -ne 1){throw 'Released exclusion was not acquired'}
 $wasAbandoned=$false
 try {$script:mutexOwned=$mutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$script:mutexOwned=$true;$wasAbandoned=$true}
 if(-not $mutexOwned -or -not $wasAbandoned){throw 'Native abandonment was not observed'}
 @{blocked=$true;abandoned=$true;owner_model='surrogate_account';quiet=$script:quiet}|ConvertTo-Json -Compress
}finally{if($mutexOwned){$mutex.ReleaseMutex()};if($null -ne $mutex){$mutex.Dispose()}}
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(harness),
            "-Template",
            str(ROOT / "scripts/Recover-K98StartupEvidence.ps1"),
            "-Machine",
            str(uuid4()),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == dict(
        blocked=True, abandoned=True, owner_model="surrogate_account", quiet=1
    )
