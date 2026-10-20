"""Publication proofs keep IPC responsive without bypassing authority evidence."""

from copy import deepcopy
from threading import Event, RLock, Thread
from unittest.mock import Mock
from uuid import uuid4

import pytest

from scripts.run_export_authority import AuthorityBroker
from services.export_execution_authority import ExecutionUncertain
from services.export_proof_progress import AuthorityProofBusy, ProofProgress
from services.export_runtime_composition import AuthorityClient, RuntimeRegistration
from tests.test_export_runtime_composition import registration_fixture


def test_failed_proof_reports_bounded_diagnostic_without_exposing_exception(capsys):
    broker, client, _ = endpoint()
    request = selector()
    broker.issuer.issue.side_effect = ValueError("private spreadsheet contents")
    client._invoke(request)
    broker.proof_progress.drain()
    result = client._invoke(dict(request, action="proof_status"))
    assert result["state"] == "unavailable" and result["result"] is None
    import json

    record = json.loads(capsys.readouterr().err)
    assert record["stage"] == "AUTHORITY_DISPATCH_FAILED"
    assert record["action"] == "prove"
    assert record["object_id"] == request["object_id"]
    assert record["exception_types"] == ["ValueError"]
    assert "private spreadsheet contents" not in str(record)


def test_failure_reporter_failure_cannot_strand_proof_admission():
    def fail(*_):
        raise RuntimeError("private details")

    progress = ProofProgress(fail, report_failure=fail)
    request = selector()
    progress.start(request["request_id"], request)
    progress.drain()
    assert not progress.busy()
    assert progress.poll(request["request_id"], request)["state"] == "unavailable"


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


def test_registration_request_cannot_block_progress_behind_proof_lock():
    broker, client, _ = endpoint()
    entered, finish, answered = Event(), Event(), Event()
    authority_lock = RLock()
    request = selector()
    broker.replacements = Mock()
    broker.replacements.registrations.return_value = (
        (broker.registration,),
        broker.registration,
    )

    def current():
        with authority_lock:
            return {}

    def issue(**kwargs):
        with authority_lock:
            entered.set()
            assert finish.wait(5)
            return dict(state="confirmed", snapshot_hash="a" * 64, proof_id=str(uuid4()))

    broker.replacements.current.side_effect = current
    broker.issuer.issue.side_effect = issue
    errors = []

    def registration():
        try:
            client._invoke(dict(version=1, action="effective_registration"))
        except AuthorityProofBusy:
            answered.set()
        except BaseException as exc:
            errors.append(exc)

    thread = Thread(target=registration)
    try:
        client._invoke(request)
        assert entered.wait(5)
        thread.start()
        assert answered.wait(1), "Registration blocked the serial control plane"
        assert client._invoke(dict(request, action="proof_status"))["state"] == "running"
        broker.replacements.current.assert_not_called()
    finally:
        finish.set()
        broker.proof_progress.drain()
        if thread.ident is not None:
            thread.join(5)
    assert not errors
    client._invoke(dict(version=1, action="effective_registration"))
    broker.replacements.current.assert_called_once()


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


def test_claimed_export_waits_for_proof_without_failing_or_repeating_attempt(monkeypatch):
    from services.export_coordination_service import ExportCoordinator
    from services.export_runtime_composition import AuthorityStream

    waiting, available = Event(), Event()
    client, dal = Mock(), Mock()
    claim = Mock(job_id=str(uuid4()))
    dal.pending_intents.return_value = []
    dal.accounts.return_value = ["account"]
    dal.claim_next.return_value = claim
    dal.authorize.return_value = dict(ConsumerKind="new_source", SpoolKey=None)
    attempts, opened = [], []

    def open_stream(stream_id, scope):
        if not available.is_set():
            waiting.set()
            raise AuthorityProofBusy("Existing publication proof")
        opened.append(stream_id)

    client.open_stream.side_effect = open_stream
    monkeypatch.setattr("time.sleep", lambda _: available.wait(0.01))

    def deliver(*args):
        attempts.append(claim.job_id)
        with AuthorityStream(client, {"Purpose": "mutation"}) as stream:
            stream.execute({"stream_id": stream.stream_id})

    coordinator = ExportCoordinator(dal, adapters={"new_source": deliver})
    worker = Thread(target=coordinator.run_batch, args=(Event(),))
    worker.start()
    try:
        assert waiting.wait(5)
        dal.fail.assert_not_called()
        client.execute.assert_not_called()
        assert attempts == [claim.job_id]
    finally:
        available.set()
        worker.join(5)
    assert not worker.is_alive()
    dal.fail.assert_not_called()
    dal.claim_next.assert_called_once()
    assert len(opened) == len(attempts) == 1
    client.execute.assert_called_once()
    client.close_stream.assert_called_once()
    assert len({call.args[0] for call in client.open_stream.call_args_list}) == 1


@pytest.mark.parametrize("method", ["open_stream", "execute", "close_stream"])
@pytest.mark.parametrize("purpose", ["mutation", "probe"])
def test_owned_stream_retries_only_authenticated_pre_dispatch_busy(method, purpose, monkeypatch):
    from services.export_runtime_composition import AuthorityStream

    client = Mock()
    stream = AuthorityStream(client, {"Purpose": purpose})
    operation = getattr(client, method)
    operation.side_effect = [AuthorityProofBusy("busy"), "acknowledged"]
    monkeypatch.setattr("time.sleep", lambda _: None)
    assert stream._wait_before_dispatch(operation, "same-message") == "acknowledged"
    assert [call.args for call in operation.call_args_list] == [
        ("same-message",),
        ("same-message",),
    ]
    operation.reset_mock(side_effect=True)
    operation.side_effect = ExecutionUncertain("Lost reply")
    with pytest.raises(ExecutionUncertain):
        stream._wait_before_dispatch(operation, "same-message")
    operation.assert_called_once()


def test_unrecognised_scope_busy_returns_without_dispatch(monkeypatch):
    from services.export_runtime_composition import AuthorityStream

    client = Mock()
    client.open_stream.side_effect = AuthorityProofBusy("busy")
    sleep = Mock()
    monkeypatch.setattr("time.sleep", sleep)
    with pytest.raises(AuthorityProofBusy):
        with AuthorityStream(client, {"Purpose": "unknown"}):
            pytest.fail("Refused probe entered")
    client.open_stream.assert_called_once()
    client.execute.assert_not_called()
    sleep.assert_not_called()
