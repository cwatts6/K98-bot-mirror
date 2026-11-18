"""Bounded original-request custody; previews never authorize mutation or replay."""

from threading import Event, RLock
from unittest.mock import Mock

import pytest

from services import authority_observation as module


def selector(key="one"):
    return dict(version=1, action="inspect_target_recovery", job_id=key)


@pytest.mark.parametrize("started", [False, True])
def test_interrupted_thread_start_keeps_worker_custody(monkeypatch, started):
    real_thread = module.Thread
    threads = []

    class InterruptedThread(real_thread):
        def start(self):
            threads.append(self)
            if started:
                super().start()
            raise KeyboardInterrupt("launch acknowledgement interrupted")

    monkeypatch.setattr(module, "Thread", InterruptedThread)
    dispatch, reply, close = Mock(), Mock(), Mock()
    worker = module.ObservationProgress(dispatch)
    try:
        with pytest.raises(KeyboardInterrupt):
            worker.submit(selector(), reply, close)
        assert worker._thread is threads[0]
        assert worker.snapshot()["admission"] == "closed"
        assert worker.drain(timeout=2) is started
        assert not worker.submit(selector(), reply, close)
        dispatch.assert_not_called()
        reply.assert_not_called()
        close.assert_not_called()  # Transport was never transferred.
    finally:
        worker.stop_admission()
        if started:
            threads[0].join(2)
            assert not threads[0].is_alive()


def test_slow_observation_allows_one_waiter_and_independent_mutation():
    entered, release = Event(), Event()
    lock = RLock()
    calls, replies, closed = [], [], []

    def dispatch(message):
        with module.observation_guard(lock, read_only=True):
            calls.append(message["job_id"])
            entered.set()
            assert release.wait(3)
            return message["job_id"]

    worker = module.ObservationProgress(dispatch)
    try:
        assert worker.submit(selector(), replies.append, lambda: closed.append("one"))
        assert entered.wait(2)
        # A real mutation still takes the original lock and can progress.
        assert lock.acquire(blocking=False)
        lock.release()
        assert worker.submit(selector("two"), replies.append, lambda: closed.append("two"))
        assert not worker.submit(selector("three"), replies.append, lambda: closed.append("three"))
        assert calls == ["one"]
        assert worker.snapshot() == dict(active=1, waiting=1, unconfirmed=0, admission="open")
        worker.stop_admission()
        release.set()
        assert worker.drain(timeout=3)
        # Shutdown cancels the waiting observation; it never dispatches or replays it.
        assert calls == ["one"]
        assert replies == [dict(version=1, result="one"), dict(version=1, error="authority_busy")]
        assert closed == ["one", "two"]
    finally:
        release.set()
        worker.drain(timeout=3)


@pytest.mark.parametrize("damage", ["mutation", "configuration", "extra", "version", "unknown"])
def test_worker_independently_refuses_non_read_only_selectors(damage):
    message = selector()
    if damage == "mutation":
        message["action"] = "isolate_export_targets"
    elif damage == "configuration":
        message = dict(version=1, action="inspect_configuration_recovery", preparation_id="one")
    elif damage == "extra":
        message["execute"] = True
    elif damage == "version":
        message["version"] = True
    else:
        message["action"] = "new_inspection"
    dispatch, reply, close = Mock(), Mock(), Mock()
    worker = module.ObservationProgress(dispatch)
    assert not worker.submit(message, reply, close)
    assert worker.drain(timeout=0)
    dispatch.assert_not_called()
    reply.assert_not_called()
    close.assert_not_called()  # Refused admission leaves custody with the caller.


def test_lost_reply_never_replays_and_next_request_keeps_its_own_reply():
    sent, first_closed = Event(), Event()
    dispatch = Mock(side_effect=lambda message: message["job_id"])
    report = Mock()
    worker = module.ObservationProgress(dispatch, report_connection_failure=report)
    first = Mock(side_effect=OSError("private transport prose"))
    second = Mock(side_effect=lambda _: sent.set())
    try:
        assert worker.submit(selector(), first, first_closed.set)
        assert first_closed.wait(2)
        assert worker.submit(selector("two"), second, lambda: None)
        assert sent.wait(2)
        assert worker.drain(timeout=2)
        assert dispatch.call_count == 2
        first.assert_called_once_with(dict(version=1, result="one"))
        second.assert_called_once_with(dict(version=1, result="two"))
        report.assert_called_once()
    finally:
        worker.drain(timeout=2)


@pytest.mark.parametrize("failure", [OSError("private SQL"), KeyboardInterrupt()])
def test_dispatch_failure_is_redacted_and_all_custody_closes(failure):
    completed = Event()
    reply, report = Mock(), Mock()
    worker = module.ObservationProgress(Mock(side_effect=failure), report_failure=report)
    try:
        assert worker.submit(selector(), reply, completed.set)
        assert completed.wait(2)
        assert worker.drain(timeout=2)
        reply.assert_called_once_with(dict(version=1, error="unresolved_action"))
        assert report.call_args.args[1] is failure
    finally:
        worker.drain(timeout=2)


def test_unconfirmed_transport_cleanup_retains_entry_and_closes_admission():
    finished = Event()
    worker = module.ObservationProgress(lambda _: "read")

    def close():
        finished.set()
        raise OSError("unconfirmed handle close")

    try:
        assert worker.submit(selector(), Mock(), close)
        assert finished.wait(2)
        assert not worker.drain(timeout=2)
        assert worker.snapshot()["unconfirmed"] == 1
        assert not worker.submit(selector("two"), Mock(), Mock())
    finally:
        worker.drain(timeout=2)


def test_unconfirmed_sql_cleanup_cannot_be_hidden_by_a_returned_preview():
    from core.sql_connection_custody import retain_connection

    finished = Event()

    def dispatch(_):
        retain_connection(
            object(), effect="not_applicable", first_failure=OSError(), cleanup_error=OSError()
        )
        return "unavailable"

    reply = Mock()
    worker = module.ObservationProgress(dispatch)
    try:
        assert worker.submit(selector(), reply, finished.set)
        assert finished.wait(2)
        assert not worker.drain(timeout=2)
        assert worker.snapshot()["unconfirmed"] == 1
        reply.assert_called_once_with(dict(version=1, error="unresolved_action"))
    finally:
        worker.drain(timeout=2)


def test_deadline_cannot_release_a_running_owner():
    entered, release = Event(), Event()
    close = Mock()

    def dispatch(_):
        entered.set()
        assert release.wait(3)
        return "done"

    worker = module.ObservationProgress(dispatch)
    try:
        assert worker.submit(selector(), Mock(), close)
        assert entered.wait(2)
        assert not worker.drain(timeout=0)
        close.assert_not_called()
        assert worker.snapshot()["active"] == 1
        assert not worker.submit(selector("new"), Mock(), Mock())
        release.set()
        assert worker.drain(timeout=2)
        close.assert_called_once()
    finally:
        release.set()
        worker.drain(timeout=2)


def test_ordinary_read_and_every_mutation_still_take_the_authority_lock():
    lock = Mock()
    lock.__enter__ = Mock()
    lock.__exit__ = Mock()
    with module.observation_guard(lock, read_only=True):
        pass
    lock.__enter__.assert_called_once()
    with module.parallel_observation(), module.observation_guard(lock, read_only=False):
        pass
    assert lock.__enter__.call_count == 2


def test_waiting_observation_executes_once_after_original_cleanup():
    entered, release, done = Event(), Event(), Event()
    order = []

    def dispatch(message):
        order.append("dispatch-" + message["job_id"])
        if message["job_id"] == "one":
            entered.set()
            assert release.wait(3)
        return message["job_id"]

    worker = module.ObservationProgress(dispatch)
    try:
        assert worker.submit(selector(), Mock(), lambda: order.append("close-one"))
        assert entered.wait(2)
        message = selector("two")
        assert worker.submit(message, Mock(), done.set)
        message["action"] = "mutated-after-admission"
        release.set()
        assert done.wait(2)
        assert worker.drain(timeout=2)
        assert order == ["dispatch-one", "close-one", "dispatch-two"]
    finally:
        release.set()
        worker.drain(timeout=2)


@pytest.mark.parametrize("failed", ["peer", "handle", "bot"])
def test_request_cleanup_attempts_every_owned_handle(failed):
    from scripts.run_export_authority import _PipeRequest

    request = _PipeRequest(Mock())
    request.peer, request.bot = Mock(), Mock()
    first = OSError("close")
    getattr(request, failed).Close.side_effect = first
    with pytest.raises(OSError) as caught:
        request.close()
    assert caught.value is first
    for handle in (request.peer, request.handle, request.bot):
        handle.Close.assert_called_once()


def test_request_cannot_drop_an_unconfirmed_io_operation():
    from types import SimpleNamespace

    from core.export_execution_host import HostBoundaryError
    from scripts.run_export_authority import _PipeRequest

    request = _PipeRequest(Mock())
    request.pipe = SimpleNamespace(_unconfirmed_io=[object()])
    with pytest.raises(HostBoundaryError):
        request.close()
    request.handle.Close.assert_not_called()


def test_shared_observation_keeps_original_peer_and_its_own_process_handle(monkeypatch):
    from types import SimpleNamespace

    from core import export_execution_host as host, export_process_identity as identity
    from scripts import run_export_authority as launcher
    from tests.test_export_single_account import SID, TRUST_MODEL, process_bindings

    bindings = process_bindings()
    lifetime, own, lease = [SimpleNamespace(Close=Mock()) for _ in range(3)]
    peers = [SimpleNamespace(Close=Mock()) for _ in range(2)]
    handles = [SimpleNamespace(Close=Mock()) for _ in range(3)]
    entered, release = Event(), Event()
    pipes = [
        SimpleNamespace(connect=Mock(), send=Mock(), receive=Mock(return_value=m))
        for m in (selector(), dict(version=1, action="fixture_mutation"))
    ]
    opener = Mock(side_effect=[lifetime, own, lease, own])
    monkeypatch.setattr(identity, "open_pinned_process", opener)
    monkeypatch.setattr(identity, "pinned_process_alive", Mock(side_effect=[True, True, False]))
    monkeypatch.setattr(identity, "authenticate_process_peer", Mock(side_effect=peers))
    monkeypatch.setattr(identity, "process_snapshot", lambda _: bindings["bot"])
    monkeypatch.setattr(host, "MessagePipe", Mock(side_effect=pipes))
    make = Mock(side_effect=handles)

    def dispatch(message):
        if message["action"] == "inspect_target_recovery":
            entered.set()
            assert release.wait(3)
            assert pipes[0].process is lease
            lease.Close.assert_not_called()
            peers[0].Close.assert_not_called()
            return "observation"
        assert entered.wait(2)
        release.set()
        return "mutation"

    broker = SimpleNamespace(dispatch=dispatch)
    try:
        launcher.serve(
            manifest=dict(
                pipe_id="fixture",
                authority_sid=SID,
                bot_sid=SID,
                trust_model=TRUST_MODEL,
                process_bindings=bindings,
            ),
            authority=None,
            make_pipe=make,
            authenticate=Mock(side_effect=AssertionError),
            broker=broker,
        )
        pipes[0].send.assert_called_once_with(dict(version=1, result="observation"))
        pipes[1].send.assert_called_once_with(dict(version=1, result="mutation"))
        assert [c.kwargs["first_instance"] for c in make.call_args_list] == [True, False, False]
        for handle in [lifetime, lease, *peers, *handles]:
            handle.Close.assert_called_once()
    finally:
        release.set()
        broker.observation_progress.drain(timeout=3)
