"""Publication proofs keep IPC responsive without bypassing authority evidence."""

from copy import deepcopy
from threading import Event, Thread
from unittest.mock import Mock
from uuid import uuid4

import pytest

from scripts.run_export_authority import AuthorityBroker
from services.export_execution_authority import ExecutionUncertain
from services.export_proof_progress import AuthorityProofBusy, ProofProgress
from services.export_runtime_composition import AuthorityClient, RuntimeRegistration
from tests.test_export_runtime_composition import registration_fixture


def endpoint():
    boundary = Mock(fingerprint="d" * 64, _manifest={})
    boundary.recheck.return_value = boundary.fingerprint
    broker = AuthorityBroker(Mock(), RuntimeRegistration(registration_fixture()), boundary=boundary)
    broker.issuer = Mock()
    client = object.__new__(AuthorityClient)
    client._invoke = lambda m: broker.dispatch(dict(m, deployment_hash=boundary.fingerprint))
    return broker, client, boundary


def selector():
    return dict(
        version=1,
        action="proof_start",
        request_id=str(uuid4()),
        kind="publication",
        object_id=str(uuid4()),
        snapshot_hash="a" * 64,
        current_attempt_id=None,
        old_attempt_id=None,
    )


def test_proof_check_leaves_control_plane_responsive_and_preserves_exclusion():
    broker, client, boundary = endpoint()
    entered, finish = Event(), Event()
    request = selector()
    receipt = dict(state="confirmed", snapshot_hash="a" * 64, proof_id=str(uuid4()))

    def issue(**kwargs):
        entered.set()
        assert finish.wait(5)
        return receipt

    broker.issuer.issue.side_effect = issue
    try:
        first = client._invoke(request)
        assert first["state"] == "running" and entered.wait(5)
        assert client._invoke(request)["state"] == "running"
        assert client._invoke(dict(request, action="proof_status"))["state"] == "running"
        ready = client._invoke(dict(version=1, action="ready"))
        assert ready["deployment_hash"] == boundary.fingerprint
        with pytest.raises(AuthorityProofBusy):
            client._invoke(dict(version=1, action="open"))
        with pytest.raises(AuthorityProofBusy):
            client._invoke(dict(request, request_id=str(uuid4())))
        broker.authority.open_stream.assert_not_called()
        assert broker.issuer.issue.call_count == 1
    finally:
        finish.set()
        broker.proof_progress.drain()
    result = client._invoke(dict(request, action="proof_status"))
    assert result["state"] == "complete" and result["result"] == receipt
    assert broker.issuer.issue.call_count == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("object_id", str(uuid4())),
        ("snapshot_hash", "b" * 64),
        ("kind", "retirement_recovery"),
    ],
)
def test_existing_progress_cannot_be_rebound(field, value):
    broker, client, _ = endpoint()
    request = selector()
    client._invoke(request)
    broker.proof_progress.drain()
    with pytest.raises(ValueError, match="another exact selector"):
        client._invoke(dict(request, action="proof_status", **{field: value}))
    assert broker.issuer.issue.call_count == 1


@pytest.mark.parametrize(
    "change",
    [
        dict(kind="retirement"),
        dict(kind="rollover_complete"),
        dict(snapshot_hash="bad"),
        dict(current_attempt_id=str(uuid4())),
        dict(old_attempt_id=str(uuid4())),
        dict(version=True),
        dict(object_id="bad"),
        dict(request_id="bad"),
        dict(proof=dict(state="confirmed")),
        dict(deployment_hash="b" * 64),
    ],
)
def test_progress_rejects_untrusted_selector_before_work(change):
    broker, _, boundary = endpoint()
    message = dict(selector(), deployment_hash=boundary.fingerprint)
    message.update(change)
    with pytest.raises(ValueError):
        broker.dispatch(message)
    broker.issuer.issue.assert_not_called()


def test_restart_poll_never_starts_or_adopts_work():
    broker, client, _ = endpoint()
    request = dict(selector(), action="proof_status")
    assert client._invoke(request)["state"] == "unavailable"
    broker.issuer.issue.assert_not_called()


def test_client_polls_same_request_and_validates_final_proof(monkeypatch):
    client = object.__new__(AuthorityClient)
    messages = []
    proof = dict(state="confirmed", snapshot_hash="a" * 64, proof_id=str(uuid4()))

    def invoke(message):
        messages.append(deepcopy(message))
        return dict(
            request_id=message["request_id"],
            state="running" if len(messages) == 1 else "complete",
            elapsed_seconds=2,
            result=None if len(messages) == 1 else proof,
        )

    client._invoke = invoke
    monkeypatch.setattr("time.sleep", lambda _: None)
    assert client.prove("publication", str(uuid4()), "a" * 64) == proof
    assert [m["action"] for m in messages] == ["proof_start", "proof_status"]
    assert len({m["request_id"] for m in messages}) == 1


def test_missing_result_does_not_resubmit_original_check(monkeypatch):
    client = object.__new__(AuthorityClient)
    messages = []

    def invoke(message):
        messages.append(deepcopy(message))
        return dict(
            request_id=message["request_id"],
            state="running" if len(messages) == 1 else "unavailable",
            elapsed_seconds=0,
            result=None,
        )

    client._invoke = invoke
    monkeypatch.setattr("time.sleep", lambda _: None)
    with pytest.raises(ExecutionUncertain, match="no replay"):
        client.prove("publication", str(uuid4()), "a" * 64)
    assert [m["action"] for m in messages] == ["proof_start", "proof_status"]


def test_drain_waits_for_owned_proof_and_refuses_new_admission():
    entered, finish, drained = Event(), Event(), Event()

    def issue(_):
        entered.set()
        assert finish.wait(5)
        raise RuntimeError("private provider detail must not appear in response")

    runner = ProofProgress(issue)
    key = str(uuid4())
    runner.start(key, {})
    assert entered.wait(5)

    def drain():
        runner.drain()
        drained.set()

    thread = Thread(target=drain)
    thread.start()
    try:
        assert not drained.wait(0.05)
        with pytest.raises(AuthorityProofBusy):
            runner.start(str(uuid4()), {})
    finally:
        finish.set()
        thread.join(5)
    assert drained.is_set()
    assert runner.poll(key, {})["state"] == "unavailable"
    assert runner.poll(key, {})["result"] is None
