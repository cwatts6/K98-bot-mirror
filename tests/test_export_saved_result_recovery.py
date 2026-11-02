"""Full private verifier regressions for retained results; no provider substitute."""

from copy import deepcopy
import os
from types import SimpleNamespace
from uuid import uuid4

import pytest
from test_legacy_export_closeout import recovery  # noqa: F401

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_execution_protocol import encode
from services.export_saved_result_recovery import SavedResultRecovery
from services.export_saved_result_recovery_dal import journal_digest


@pytest.fixture
def saved(recovery):  # noqa: F811
    closeout, state, stream, request, events, docs = recovery
    response = events.pop()
    original_stream = deepcopy(stream)
    stream.update(
        State="frozen",
        ActiveAccountKey="account-a",
        Version=3,
        ClosureHash=None,
        ClosureReference=None,
        EventDigest=None,
        ClosedUTC=None,
    )
    state["foreign_streams"] = []
    for resource in state["resources"]:
        resource["BlockedReason"] = "retained result"

    def sync():
        state["streams"] = [{k: v.hex() if isinstance(v, bytes) else v for k, v in stream.items()}]

    sync()

    def records(_):
        yield request["RequestID"], deepcopy(request), deepcopy(events)

    execution = closeout.execution
    execution.request_records = records
    execution.stream_digest = lambda sid: journal_digest(records(sid))
    session = dict(
        SessionID=stream["SessionID"],
        State="open",
        AuthorityPrincipal="authority",
        ManifestHash=b"m" * 32,
    )
    execution.read_session = lambda _: session
    old = dict(
        stream_id=stream["StreamID"],
        version=3,
        last_sequence=1,
        event_digest=execution.stream_digest(stream["StreamID"])[1].hex(),
        closure=dict(child_id=stream["ChildIdentity"], process_signaled=True, job_empty=True),
    )
    old_saved = closeout.store.put(encode(old))
    target = dict(
        job_id=state["job"]["JobID"],
        owner_id=state["job"]["OwnerID"],
        fence=2,
        job_version=7,
        stream_id=stream["StreamID"],
        session_id=stream["SessionID"],
        child_id=stream["ChildIdentity"],
        stream_version=3,
        last_sequence=1,
        request_id=request["RequestID"],
        registration_sha256=stream["RegistrationHash"].hex(),
        manifest_sha256=(b"m" * 32).hex(),
        response_reference=response["EvidenceReference"],
        response_sha256=response["EvidenceHash"].hex(),
        closure_reference=old_saved.key,
        closure_sha256=old_saved.sha256,
    )
    journal_data = {}

    def write(name, value):
        if name in journal_data:
            assert journal_data[name] == value
        journal_data[name] = deepcopy(value)

    journal = SimpleNamespace(read=lambda name: deepcopy(journal_data.get(name)), write=write)
    calls = []

    def transition(expected, kind, **values):
        assert expected == state
        assert values["ExpectedVersion"] == stream["Version"]
        calls.append(kind)
        stream["Version"] += 1
        if kind == "event":
            events.append(
                {k: values[k] for k in response if k != "EventSequence"} | {"EventSequence": 3}
            )
        else:
            stream.update(
                State="closed",
                ActiveAccountKey=None,
                ClosedUTC="2026-11-02T00:00:00",
                **{k: values[k] for k in ("ClosureHash", "ClosureReference", "EventDigest")},
            )
        sync()

    execution.checked_transition = transition

    def service():
        return SavedResultRecovery(
            closeout=closeout,
            execution=execution,
            store=closeout.store,
            journal=journal,
            check_boundary=lambda: None,
            target=target,
        )

    return SimpleNamespace(
        service=service,
        state=state,
        stream=stream,
        events=events,
        request=request,
        docs=docs,
        target=target,
        calls=calls,
        journal=journal_data,
        session=session,
        closeout=closeout,
        sync=sync,
        original_stream=original_stream,
    )


def finish(f, review, token):
    for _ in range(4):
        result = f.service().step(review, token)
        if result["stage"] == "PARTIAL_EXPORT_CLOSED":
            return result
    pytest.fail("Recovery did not finish")


def test_saved_result_restart_each_stage_preserves_old_seal_and_failed_history(saved):
    f = saved
    before = deepcopy(f.docs)
    provenance = f.state["job"]["ProvenanceJson"]
    review = f.service().inspect()
    result = finish(f, review, f.service().token(review))
    assert result["provider_requests"] == 0
    assert f.calls == ["event", "stream"]
    assert f.state["job"]["State"] == "failed" and f.state["job"]["ProvenanceJson"] == provenance
    assert all(f.docs[k] == v for k, v in before.items())
    assert f.service().step(review, f.service().token(review)) == result
    assert f.closeout.dal.settle.call_count == 1


@pytest.mark.parametrize("stage", ["event", "stream", "closeout"])
def test_lost_reply_resume_reads_receipt_without_repeating_write(saved, stage):
    f = saved
    review = f.service().inspect()
    token = f.service().token(review)
    if stage == "closeout":
        original = f.closeout.dal.settle.side_effect

        def lose(*a, **k):
            original(*a, **k)
            raise OSError("reply lost")

        f.closeout.dal.settle.side_effect = lose
    else:
        execution = f.closeout.execution
        original = execution.checked_transition

        def lose(expected, kind, **values):
            result = original(expected, kind, **values)
            if kind == stage:
                raise OSError("reply lost")
            return result

        execution.checked_transition = lose
    with pytest.raises(OSError):
        finish(f, review, token)
    result = finish(f, review, token)
    assert result["stage"] == "PARTIAL_EXPORT_CLOSED" and f.calls == ["event", "stream"]
    assert f.closeout.dal.settle.call_count == 1


@pytest.mark.parametrize(
    "change",
    [
        "response",
        "seal",
        "request",
        "owner",
        "fence",
        "membership",
        "session",
        "manifest",
        "unknown",
        "safe_retry",
    ],
)
def test_invalid_proof_or_ownership_never_writes(saved, change):
    f = saved
    if change == "response":
        f.docs[f.target["response_reference"]] = b"{}"
    elif change == "seal":
        f.docs[f.target["closure_reference"]] = b"{}"
    elif change == "request":
        f.request["TargetID"] = "foreign-file"
    elif change == "owner":
        f.state["resources"][0]["OwnerID"] = str(uuid4())
    elif change == "fence":
        f.state["resources"][0]["Fence"] += 1
    elif change == "membership":
        f.state["membership"].append("destination:foreign")
    elif change == "session":
        f.session["State"] = "closed"
    elif change == "manifest":
        f.session["ManifestHash"] = b"x" * 32
    elif change == "unknown":
        f.events.append(dict(f.events[-1], State="unknown", EventSequence=3))
    elif change == "safe_retry":
        f.state["job"]["ProvenanceJson"] = '{"safe_retry":{"requested":true}}'
    with pytest.raises((SourceConflict, ValueError)):
        f.service().inspect()
    assert not f.calls and f.closeout.dal.settle.call_count == 0


def test_changed_resource_between_review_and_action_is_not_adopted(saved):
    f = saved
    review = f.service().inspect()
    f.state["resources"][0]["Version"] += 1
    with pytest.raises(SourceConflict):
        f.service().step(review, f.service().token(review))
    assert not f.calls


def test_wrong_terminal_reference_after_append_refuses_reseal(saved):
    f = saved
    review = f.service().inspect()
    token = f.service().token(review)
    f.service().step(review, token)
    f.events[-1]["EvidenceReference"] = str(uuid4())
    with pytest.raises(SourceConflict):
        f.service().step(review, token)
    assert f.calls == ["event"]


def test_protocol_invalid_response_with_valid_hash_is_rejected(saved):
    f = saved
    marker = f.closeout.store.put(encode(dict(request_id=f.target["request_id"], response={})))
    f.target.update(response_reference=marker.key, response_sha256=marker.sha256)
    with pytest.raises(ValueError):
        f.service().inspect()
    assert not f.calls


def test_recovery_waits_automatically_and_notification_failure_is_secondary():
    from services.export_saved_result_recovery import run_saved_recovery
    from services.export_saved_result_recovery_dal import RecoveryWaiting

    elapsed = [0.0]
    notices = []

    def step(*args):
        if elapsed[0] < 330:
            raise RecoveryWaiting()
        return dict(stage="PARTIAL_EXPORT_CLOSED")

    def sleep(seconds):
        assert seconds <= 30
        elapsed[0] += seconds

    def notify(value):
        notices.append(value)
        raise OSError("optional sink unavailable")

    result = run_saved_recovery(
        SimpleNamespace(step=step, check_boundary=lambda: None),
        {},
        "token",
        SimpleNamespace(checkpoint=lambda work: work()),
        clock=lambda: elapsed[0],
        sleep=sleep,
        notify=notify,
    )
    assert result["stage"] == "PARTIAL_EXPORT_CLOSED" and len(notices) == 1


@pytest.mark.parametrize("cleanup", ["failed", "forgotten"])
def test_cleanup_failure_never_becomes_retry_eligibility(cleanup):
    from services.export_saved_result_recovery_dal import RecoveryConnections, RecoveryWaiting

    def close():
        raise OSError("close failed")

    connections = RecoveryConnections(lambda: SimpleNamespace(close=close))

    def work():
        connection = connections.connect()
        if cleanup == "failed":
            connection.close()
        raise RecoveryWaiting()

    with pytest.raises(SourceConflict, match="cleanup"):
        connections.checkpoint(work)


def test_packet_inventory_hashes_and_refusal_to_overwrite(tmp_path):
    import hashlib
    import json

    from scripts.build_saved_result_recovery_packet import MEMBERS, build

    target = tmp_path / "target.json"
    target.write_text('{"synthetic":true}')
    destination = tmp_path / "packet"
    receipt = build(target, destination)
    packet = json.loads((destination / "recovery-packet.json").read_bytes())
    assert {m["name"] for m in packet["members"]} == {*MEMBERS, "recovery-target.json"}
    for member in packet["members"]:
        assert (
            hashlib.sha256((destination / member["name"]).read_bytes()).hexdigest()
            == member["sha256"]
        )
    assert (
        hashlib.sha256((destination / "recovery-packet.json").read_bytes()).hexdigest()
        == receipt["packet_sha256"]
    )
    with pytest.raises(FileExistsError):
        build(target, destination)


def test_saved_store_hex_keys_become_canonical_sql_references(saved):
    from uuid import UUID

    service = saved.service()
    raw_put = service.store.put

    def hex_put(raw):
        marker = raw_put(raw)
        return SimpleNamespace(key=UUID(marker.key).hex, sha256=marker.sha256)

    service.store.put = hex_put
    marker = service._save(dict(synthetic="retained"))
    assert str(UUID(marker["reference"])) == marker["reference"]


@pytest.mark.parametrize("state,number", [("42000", 8114), ("42000", 51700), ("28000", 18456)])
def test_permanent_sql_error_is_not_retryable(state, number):
    from services.export_saved_result_recovery_dal import RecoveryConnections

    def work():
        raise RuntimeError(state, f"synthetic permanent SQL error ({number})")

    with pytest.raises(RuntimeError) as caught:
        RecoveryConnections(lambda: None).checkpoint(work)
    assert caught.value.args[0] == state


@pytest.mark.parametrize("failure", ["write", "flush"])
def test_verified_success_survives_final_console_failure(saved, monkeypatch, failure):
    import sys

    from scripts.recover_stranded_export import emit_result

    review = saved.service().inspect()
    result = finish(saved, review, saved.service().token(review))
    before = deepcopy(saved.journal)

    class Console:
        def write(self, value):
            if failure == "write":
                raise BrokenPipeError("synthetic closed console")

        def flush(self):
            raise OSError("synthetic flush failure")

    monkeypatch.setattr(sys, "stdout", Console())
    emit_result(result, recovery="saved_result")
    assert sys.stdout is None  # No failing interpreter-exit flush.
    assert saved.journal == before and before["verified"] == result
    assert saved.closeout.dal.settle.call_count == 1


@pytest.mark.parametrize(
    "profile,stage",
    [("saved_result", "RECOVERY_REVIEW_READY"), ("stranded", "PARTIAL_EXPORT_CLOSED")],
)
def test_unverified_or_legacy_output_errors_keep_existing_failure_behavior(
    monkeypatch, profile, stage
):
    from scripts.recover_stranded_export import emit_result

    def broken(*args, **kwargs):
        raise OSError("synthetic output failure")

    monkeypatch.setattr("builtins.print", broken)
    with pytest.raises(OSError):
        emit_result(dict(stage=stage), recovery=profile)


@pytest.mark.skipif(os.name != "nt", reason="Windows PowerShell launcher")
def test_launcher_final_notice_failure_is_secondary():
    from pathlib import Path
    import subprocess

    script = """
$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile(
 (Join-Path $PWD 'scripts/Invoke-SavedExportResultRecovery.ps1'),[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Launcher syntax failed'}
$definition=$ast.Find({param($node)
 $node -is [Management.Automation.Language.FunctionDefinitionAst] -and
 $node.Name -eq 'Recovery-ShowEvidence'},$false)
if($null -eq $definition){throw 'Evidence notice helper missing'}
Invoke-Expression $definition.Extent.Text
function Write-Host {throw 'synthetic closed console'}
Recovery-ShowEvidence 'C:/synthetic/journal'
exit 0
"""
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
