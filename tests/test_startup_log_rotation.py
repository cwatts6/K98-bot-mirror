"""Offline log-generation fixtures; no bot, provider or SQL operations."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts import read_k98_startup_evidence as reader
from scripts.verify_k98_update_pair import PairPublicationPending, startup_admission_result

ROOT = Path(__file__).resolve().parents[1]
PS = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def history(tmp_path, rotations=1):
    root = tmp_path / "logs"
    root.mkdir()
    prefix = b"S11 export admission remains closed in the OLD runtime\n"
    record = dict(
        version=1,
        pid=912,
        created_filetime=134395021909371571,
        manifest_sha256="a" * 64,
        observed_utc="2020-11-18T19:03:57+00:00",
        outcome="installed",
    )
    startup = (
        b"K98_STARTUP_ADMISSION_RESULT " + json.dumps(record).encode() + b"\n"
        b"Logged in as fixture\n[BOOT] full_startup_sequence completed successfully\n"
    )
    anchor_raw = prefix + startup
    anchor = dict(sha256=sha(anchor_raw), bytes=len(anchor_raw), offset=len(prefix))
    (root / reader.NAMES[rotations]).write_bytes(anchor_raw)
    for i in range(rotations):
        (root / reader.NAMES[i]).write_bytes(f"later generation {i}\n".encode())
    profile = dict(release_id="r", startup_log_anchor=anchor)
    start = dict(release_id="r", log_offset=len(prefix), requested_utc="2020-11-18T19:02:56+00:00")
    journal = dict(
        bindings=dict(bot=dict(pid=912, created_filetime=134395021909371571)),
        publication=dict(manifests=dict(bot="a" * 64)),
    )
    return root, profile, start, journal, record, startup


@pytest.mark.parametrize("rotations", [0, 1, 2, 5])
def test_exact_anchor_orders_every_newer_generation_and_excludes_old_failure(tmp_path, rotations):
    root, profile, start, journal, record, startup = history(tmp_path, rotations)
    result = reader.observe(dict(root=str(tmp_path)), start, profile)
    expected = startup + b"".join(
        f"later generation {i}\n".encode() for i in reversed(range(rotations))
    )
    assert result["raw"] == expected
    assert result["evidence"]["interval_sha256"] == sha(expected)
    assert [row["name"] for row in result["evidence"]["generations"]] == list(
        reversed(reader.NAMES[: rotations + 1])
    )
    assert (
        startup_admission_result(dict(release_id="r"), journal, start, raw=result["raw"]) == record
    )
    assert (
        result["evidence"]["bytes_read"]
        == sum(p.stat().st_size for p in root.iterdir()) + (root / "log.txt").stat().st_size
    )


@pytest.mark.parametrize(
    "fault",
    [
        "anchor_missing",
        "gap",
        "wrong_anchor",
        "wrong_offset",
        "partial_current",
        "partial_archive",
        "invalid_utf8",
    ],
)
def test_missing_ambiguous_or_incomplete_history_refuses(tmp_path, fault):
    root, profile, start, *_ = history(tmp_path, 2)
    if fault == "anchor_missing":
        (root / "log.txt.2").unlink()
    elif fault == "gap":
        (root / "log.txt.1").unlink()
    elif fault == "wrong_anchor":
        original = (root / "log.txt.2").read_bytes()
        (root / "log.txt.2").write_bytes(b"X" + original[1:])
    elif fault == "wrong_offset":
        profile["startup_log_anchor"]["offset"] += 1
    elif fault == "partial_current":
        (root / "log.txt").write_bytes(b"incomplete")
    elif fault == "partial_archive":
        (root / "log.txt.1").write_bytes(b"incomplete")
    else:
        (root / "log.txt").write_bytes(b"\xff\n")
    with pytest.raises((ValueError, OSError, UnicodeError)):
        reader.observe(dict(root=str(tmp_path)), start, profile)


@pytest.mark.parametrize(
    "failure",
    [
        b"S11 export admission remains closed\n",
        b"Export admission disabled: drift\n",
        b"Export coordinator unavailable error_type=SourceConflict\n",
        b"Export coordinator unavailable\n",
        b"Export coordinator unavailable error_type=ObservationBusyExtra\n",
    ],
)
def test_later_negative_evidence_is_not_hidden_by_historical_success(tmp_path, failure):
    root, profile, start, *_ = history(tmp_path)
    (root / "log.txt").write_bytes(failure)
    with pytest.raises(
        reader.StartupHistoryRefused, match="does not establish readiness"
    ) as caught:
        reader.observe(dict(root=str(tmp_path)), start, profile)
    failure_record = reader.failure_record(caught.value)
    assert failure_record["evidence"]["interval_bytes"] > 0
    assert failure_record["failure_category"] in {
        "admission_closed",
        "admission_disabled",
        "coordinator_unavailable",
    }
    assert failure.decode().strip() not in json.dumps(failure_record)


def test_exact_observation_busy_is_degraded_but_not_terminal(tmp_path):
    root, profile, start, *_ = history(tmp_path)
    (root / "log.txt").write_bytes(b"Export coordinator unavailable error_type=ObservationBusy\n")
    assert reader.observe(dict(root=str(tmp_path)), start, profile)["raw"].endswith(
        b"ObservationBusy\n"
    )


@pytest.mark.parametrize("damage", ["failed", "duplicate", "wrong_pid", "wrong_manifest"])
def test_shared_admission_parser_still_rejects_wrong_or_repeated_success(tmp_path, damage):
    root, profile, start, journal, record, _ = history(tmp_path)
    if damage in ("failed", "duplicate"):
        extra = dict(record, outcome="failed" if damage == "failed" else "installed")
        (root / "log.txt").write_bytes(
            b"K98_STARTUP_ADMISSION_RESULT " + json.dumps(extra).encode() + b"\n"
        )
    elif damage == "wrong_pid":
        journal["bindings"]["bot"]["pid"] = 999
    else:
        journal["publication"]["manifests"]["bot"] = "b" * 64
    result = reader.observe(dict(root=str(tmp_path)), start, profile)
    with pytest.raises((ValueError, PairPublicationPending), match=r"failed|successful|Awaiting"):
        startup_admission_result(dict(release_id="r"), journal, start, raw=result["raw"])


def on_read(monkeypatch, action, *, target="log.txt", call=1):
    original = reader.open_log
    seen = 0

    class Wrapped:
        def __init__(self, stream, path):
            self.stream, self.path = stream, path

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.stream.close()

        def fileno(self):
            return self.stream.fileno()

        def seek(self, *args):
            return self.stream.seek(*args)

        def read(self, size):
            nonlocal seen
            value = self.stream.read(size)
            if self.path.name == target:
                seen += 1
                if seen == call:
                    action()
            return value

    monkeypatch.setattr(reader, "open_log", lambda path: Wrapped(original(path), path))


def test_active_append_preserves_captured_prefix_and_next_capture_sees_failure(
    tmp_path, monkeypatch
):
    root, profile, start, *_ = history(tmp_path)

    def append():
        with (root / "log.txt").open("ab") as stream:
            stream.write(b"S11 export admission remains closed\n")

    on_read(monkeypatch, append)
    result = reader.observe(dict(root=str(tmp_path)), start, profile)
    assert not result["raw"].endswith(b"admission remains closed\n")
    with pytest.raises(ValueError, match="does not establish readiness"):
        reader.observe(dict(root=str(tmp_path)), start, profile)


def test_same_sized_active_rewrite_refuses(tmp_path, monkeypatch):
    root, profile, start, *_ = history(tmp_path)
    on_read(
        monkeypatch,
        lambda: (root / "log.txt").write_bytes(
            b"X" * ((root / "log.txt").stat().st_size - 1) + b"\n"
        ),
    )
    with pytest.raises(ValueError, match="prefix changed"):
        reader.observe(dict(root=str(tmp_path)), start, profile)


@pytest.mark.parametrize("change", ["current_append", "archive_append", "current_shrink"])
def test_changes_between_path_stat_and_open_preserve_current_append_only(
    tmp_path, monkeypatch, change
):
    root, profile, start, *_ = history(tmp_path)
    original = reader.open_log
    target = "log.txt.1" if change == "archive_append" else "log.txt"

    def open_after_change(path):
        if path.name == target:
            if change == "current_shrink":
                path.write_bytes(b"\n")
            else:
                with path.open("ab") as stream:
                    stream.write(b"complete ordinary append\n")
        return original(path)

    monkeypatch.setattr(reader, "open_log", open_after_change)
    if change == "current_append":
        result = reader.observe(dict(root=str(tmp_path)), start, profile)
        assert result["raw"].endswith(b"complete ordinary append\n")
        assert result["evidence"]["generations"][-1]["sha256"] == sha(
            (root / "log.txt").read_bytes()
        )
    else:
        with pytest.raises(ValueError, match="identity changed before capture"):
            reader.observe(dict(root=str(tmp_path)), start, profile)


def test_archived_mutation_after_read_refuses(tmp_path, monkeypatch):
    root, profile, start, *_ = history(tmp_path)

    def damage():
        path = root / "log.txt.1"
        info = path.stat()
        path.write_bytes(b"X" + path.read_bytes()[1:])
        os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns + 1000000000))

    on_read(monkeypatch, damage, call=2)
    with pytest.raises(ValueError, match="generation changed"):
        reader.observe(dict(root=str(tmp_path)), start, profile)


def test_rotation_during_capture_is_not_blocked_and_cannot_be_accepted(tmp_path, monkeypatch):
    root, profile, start, *_ = history(tmp_path)
    moved = []

    def rotate():
        source, destination = root / "log.txt", root / "log.txt.2"
        assert source.parent.resolve() == destination.parent.resolve() == root.resolve()
        source.rename(destination)
        source.write_bytes(b"new generation\n")
        moved.append(True)

    on_read(monkeypatch, rotate)
    with pytest.raises(ValueError, match="rotated during"):
        reader.observe(dict(root=str(tmp_path)), start, profile)
    assert moved == [True]


def test_hardlinked_history_is_refused(tmp_path):
    root, profile, start, *_ = history(tmp_path)
    os.link(root / "log.txt.1", root / "linked")
    with pytest.raises(ValueError, match="link or identity"):
        reader.observe(dict(root=str(tmp_path)), start, profile)


@pytest.mark.parametrize("extra", [0, 1])
def test_read_budget_counts_prefix_recheck_and_fails_before_excess_read(
    tmp_path, monkeypatch, extra
):
    root, profile, start, *_ = history(tmp_path)
    required = sum(p.stat().st_size for p in root.iterdir()) + (root / "log.txt").stat().st_size
    monkeypatch.setattr(reader, "READ_LIMIT", required - extra)
    if extra:
        with pytest.raises(ValueError, match="read budget"):
            reader.observe(dict(root=str(tmp_path)), start, profile)
    else:
        assert (
            reader.observe(dict(root=str(tmp_path)), start, profile)["evidence"]["bytes_read"]
            == required
        )


@pytest.mark.parametrize(
    "damage",
    [dict(extra=True), dict(offset=True), dict(bytes=True), dict(offset=-1), dict(sha256="x" * 64)],
)
def test_anchor_is_closed_and_strict(tmp_path, damage):
    _, profile, *_ = history(tmp_path)
    profile["startup_log_anchor"].update(damage)
    with pytest.raises(ValueError, match="anchor required"):
        reader.validate_anchor(profile["startup_log_anchor"])


def test_python_verification_failure_retains_redacted_captured_evidence(tmp_path):
    from scripts.verify_k98_running_release import failure_result

    root, profile, start, journal, *_ = history(tmp_path)
    result = reader.observe(dict(root=str(tmp_path)), start, profile)
    error = reader.StartupHistoryRefused("admission_refused", result["evidence"])
    code, record = failure_result(error, startup_reader=vars(reader))
    assert code == 1 and record["verified"] is False and record["retry"] is False
    assert record["startup_observation"]["evidence"] == result["evidence"]
    assert record["startup_observation"]["failure_category"] == "admission_refused"
    assert "raw_base64" not in json.dumps(record) and "Logged in as" not in json.dumps(record)


@pytest.mark.skipif(os.name != "nt", reason="Isolated Windows sealed-reader entry point")
@pytest.mark.parametrize("damage", [None, "pair", "journal", "offset", "late_failure", "admission"])
def test_isolated_reader_uses_pinned_inputs_and_real_admission_parser(tmp_path, damage):
    root, profile, start, journal, record, startup = history(tmp_path)
    if damage == "admission":
        journal["bindings"]["bot"]["pid"] = 913
    config = dict(
        root=r"C:\discord_file_downloader", release_id="r", new_state_directory=str(tmp_path)
    )
    profile.update(version=2, host="MINI_AMD", stage=str(tmp_path), journal_name="journal.json")
    if damage == "offset":
        start["log_offset"] += 1
    for name, value, key in [
        ("ReleaseBindings.json", config, "bindings_sha256"),
        ("start-requested.json", start, "start_sha256"),
        ("journal.json", journal, "journal_sha256"),
    ]:
        raw = json.dumps(value).encode()
        (tmp_path / name).write_bytes(raw)
        profile[key] = sha(raw)
    pair = (ROOT / "scripts/verify_k98_update_pair.py").read_bytes()
    (tmp_path / "Verify-NewPair.py").write_bytes(pair)
    profile["pair_sha256"] = sha(pair)
    if damage in {"pair", "journal"}:
        profile[damage + "_sha256"] = "0" * 64
    if damage == "late_failure":
        (root / "log.txt").write_bytes(b"S11 export admission remains closed\n")
    raw = json.dumps(profile).encode()
    (tmp_path / "profile.json").write_bytes(raw)
    # Redirect only the log filesystem effect into a fixture. All profile,
    # binding, journal and same-packet parser validation uses the actual code.
    harness = """
import json,runpy,sys
from pathlib import Path
scope=runpy.run_path(sys.argv[1])
capture=scope['capture']
fixture=Path(sys.argv[2])/'logs'
scope['observe'].__globals__['capture']=lambda root,anchor:capture(fixture,anchor)
sys.argv=['reader','--profile',str(Path(sys.argv[2])/'profile.json'),'--sha256',sys.argv[3]]
try:
    scope['main']()
except Exception as error:
    print(json.dumps(dict(stage='STARTUP_HISTORY_REFUSED',**scope['failure_record'](error))))
    sys.exit(1)
assert not any(name in sys.modules for name in ('pyodbc','bot_instance','services'))
"""
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-c",
            harness,
            str(ROOT / "scripts/read_k98_startup_evidence.py"),
            str(tmp_path),
            sha(raw),
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert (result.returncode == 0) == (damage is None), result.stdout + result.stderr
    if damage is None:
        observation = json.loads(result.stdout)
        assert observation["stage"] == "STARTUP_HISTORY_CAPTURED"
        assert observation["evidence"]["admission"] == record
        assert observation["evidence"]["interval_bytes"] == len(startup + b"later generation 0\n")
    elif damage in {"late_failure", "admission"}:
        failure_record = json.loads(result.stdout)
        assert failure_record["evidence"]["anchor"] == profile["startup_log_anchor"]
        assert failure_record["failure_category"] == (
            "admission_closed" if damage == "late_failure" else "admission_pending"
        )
        assert "raw_base64" not in result.stdout and "Logged in as" not in result.stdout


@pytest.mark.skipif(os.name != "nt", reason="Actual PowerShell reader boundary and failed evidence")
@pytest.mark.parametrize("damage", [None, "refused", "hash", "base64", "utf8", "json"])
def test_native_reader_boundary_retains_success_or_failure_without_log_contents(tmp_path, damage):
    import base64

    raw = b"private fixture log\n" if damage != "utf8" else b"\xff\n"
    response = dict(
        stage="STARTUP_HISTORY_CAPTURED",
        raw_base64=base64.b64encode(raw).decode(),
        evidence=dict(interval_bytes=len(raw), interval_sha256=sha(raw)),
    )
    if damage == "refused":
        response = dict(
            stage="STARTUP_HISTORY_REFUSED",
            failure_type="StartupHistoryRefused",
            failure_category="admission_closed",
            evidence=response["evidence"],
            retry=False,
        )
    elif damage == "hash":
        response["evidence"]["interval_sha256"] = "0" * 64
    elif damage == "base64":
        response["raw_base64"] = "!"
    output = "not-json" if damage == "json" else json.dumps(response)
    (tmp_path / "Read-StartupEvidence.py").write_text(
        f"import sys\nprint({output!r})\nsys.exit({1 if damage == 'refused' else 0})\n"
    )
    (tmp_path / "profile.json").write_bytes(b"{}")
    harness = tmp_path / "reader.ps1"
    harness.write_text(r"""
param($Root,$Fixture,$Python)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. (Join-Path $Root 'scripts/K98-SourceUpdate.ps1') -Action Library
. (Join-Path $Root 'scripts/K98-FailedReadiness.ps1')
. (Join-Path $Root 'scripts/K98-VerifyRunningRelease.ps1')
$c=[pscustomobject]@{venv=[pscustomobject]@{path=$Python;sha256='fixture'}}
$profile=[pscustomobject]@{version=2;release_id='r';startup_log_anchor=[pscustomobject]@{offset=1};members=[pscustomobject]@{'Read-StartupEvidence.py'='fixture'}}
function Read-RetirementBytes($Path,$Expected='', $Limit=0){return ,([IO.File]::ReadAllBytes($Path))}
function Write-RetirementBytes($Path,$Bytes){[IO.File]::WriteAllBytes($Path,$Bytes)}
function ApplyStart {throw 'FORBIDDEN'}
function Start-ScheduledTask {throw 'FORBIDDEN'}
$text=Read-RunningStartupText $profile 'fixture' $Fixture ([pscustomobject]@{release_id='r';log_offset=1})
if($text -cne "private fixture log`n" -or $script:runningStartupObservationHash.Length -ne 64){throw 'Result differs'}
""")
    result = subprocess.run(
        [
            PS,
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(harness),
            str(ROOT),
            str(tmp_path),
            sys.executable,
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert (result.returncode == 0) == (damage is None), result.stdout + result.stderr
    receipts = list(tmp_path.glob("startup-observation-*.json"))
    assert len(receipts) == 1
    receipt = json.loads(receipts[0].read_text(encoding="utf-8-sig"))
    assert (receipt["failure_type"] is None) == (damage is None)
    if damage == "refused":
        assert receipt["failure_category"] == "admission_closed"
        assert receipt["evidence"] == response["evidence"]
    assert "private fixture" not in receipts[0].read_text()
    assert "raw_base64" not in receipts[0].read_text()
    assert not (tmp_path / "verified.json").exists()
