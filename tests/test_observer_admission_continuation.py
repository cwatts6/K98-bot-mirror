"""Bounded continuation through the actual producer, capture and cleanup owner."""

from contextlib import contextmanager
from unittest.mock import Mock

import pytest

from core import sql_connection_custody as custody
from kvk.dal.new_source_import_dal import SourceConflict
from services import (
    application_observation_schedule as scheduling,
    legacy_export_snapshot_service as service,
)
from services.catalogue_observation_dal import ObservationContractError, ObservationDeferred
from tests.test_legacy_export_snapshot import producer_runtime
from tests.test_observer_contract_selection import approved as application_contract


class Clock:
    def __init__(self):
        self.value = 0.0
        self.waits = []

    def monotonic(self):
        return self.value

    def sleep(self, seconds):
        self.waits.append(seconds)
        self.value += seconds


def request(clock):
    return scheduling.ObservationRequest(clock=clock.monotonic, wait=clock.sleep)


@pytest.mark.parametrize("busy_checks", [0, 2, 3])
def test_finite_continuation_and_no_wait_with_live_connection(busy_checks):
    clock = Clock()
    owner = request(clock)
    active = []
    seen = []

    def collect():
        with owner.collection():
            seen.append("collect")
            active.append("connection")
            try:
                if seen.count("collect") == 1:
                    raise ObservationDeferred("generation_changed")
                return "current"
            finally:
                active.clear()

    def probe():
        assert not active
        seen.append("probe")
        if seen.count("probe") <= busy_checks:
            raise ObservationDeferred("active_writer")

    def wait(seconds):
        assert not active
        clock.sleep(seconds)

    owner.wait = wait
    if busy_checks == 3:
        with pytest.raises(ObservationDeferred, match="generation_changed"):
            owner.run(collect, probe)
    else:
        assert owner.run(collect, probe) == "current"
    assert seen.count("collect") == (1 if busy_checks == 3 else 2)
    assert owner.boundary_checks == min(busy_checks + 1, 3)
    assert clock.waits == [1.0, 14.5, 14.5][: owner.boundary_checks]
    with pytest.raises(ValueError, match="restarted"):
        owner.run(collect, probe)


@pytest.mark.parametrize(
    "failure",
    [
        ObservationContractError("changed source"),
        custody.SqlCleanupUnknown("unknown"),
        ObservationDeferred("observation_deadline"),
        ObservationDeferred("statement_limit"),
    ],
)
def test_only_coherence_deferral_can_schedule(failure):
    clock = Clock()
    collect = Mock(side_effect=failure)
    probe = Mock()
    with pytest.raises(type(failure)) as caught:
        request(clock).run(collect, probe)
    assert caught.value is failure
    collect.assert_called_once()
    probe.assert_not_called()
    assert not clock.waits


def test_statement_and_time_budgets_span_attempts_and_result_consumption():
    clock = Clock()
    owner = request(clock)
    raw = Mock(connection=object())
    cursor = owner.cursor(raw)
    with owner.collection():
        for _ in range(130):
            cursor.execute("SELECT 1")
    with owner.collection():
        for _ in range(126):
            cursor.execute("SELECT 1")
        with pytest.raises(ObservationDeferred, match="statement_limit"):
            cursor.execute("SELECT 1")
    assert raw.execute.call_count == 256
    clock.value = 45.0
    with pytest.raises(ObservationDeferred, match="observation_deadline"):
        cursor.fetchone()
    raw.fetchone.assert_not_called()


def test_partial_scan_deadline_does_not_create_replacement():
    clock = Clock()
    owner = request(clock)
    probe = Mock()

    def collect():
        with owner.collection():
            clock.value = 15.0

    with pytest.raises(ObservationDeferred, match="observation_deadline"):
        owner.run(collect, probe)
    probe.assert_not_called()
    assert not clock.waits


def setup_runtime(tmp_path, monkeypatch, *, close_failure=False, repeat_deferral=False):
    runtime, dal = producer_runtime(tmp_path)
    dal.application_sql_contract = application_contract.__wrapped__()
    clock = Clock()
    monkeypatch.setattr(scheduling, "time", clock)
    events = []
    connections = []
    evidence = object()
    attempts = []

    def connect():
        connection = Mock(autocommit=False)
        connection.closed = False

        def close():
            events.append("close")
            if close_failure:
                raise OSError("close acknowledgement lost")
            connection.closed = True

        connection.close.side_effect = close
        connections.append(connection)
        return connection

    @contextmanager
    def guard(claim, connection, **kwargs):
        attempts.append((claim, kwargs))
        events.append("guard_enter")
        try:
            if len(attempts) == 1 or repeat_deferral:
                raise ObservationDeferred("generation_changed")
            yield evidence
        finally:
            events.append("guard_exit")

    def boundary(connection, observation_request):
        assert all(c.closed for c in connections[:-1])
        assert observation_request is attempts[0][1]["observation_request"]
        events.append("probe")

    old_wait = clock.sleep

    def wait(seconds):
        assert all(c.closed for c in connections)
        assert not any(
            call.kwargs.get("state") == "unavailable" for call in dal.transition.call_args_list
        )
        events.append("wait")
        old_wait(seconds)

    clock.sleep = wait
    dal.connect.side_effect = connect
    dal.session.side_effect = guard
    dal.observation_boundary.side_effect = boundary
    return runtime, dal, events, connections, attempts, evidence


def test_actual_writer_continues_same_claim_and_captures_once(tmp_path, monkeypatch):
    runtime, dal, events, connections, attempts, evidence = setup_runtime(tmp_path, monkeypatch)
    body = Mock()
    with service.use_runtime(runtime), service.producer_capture_scope():
        with service.writer_scope("all_kvk") as owner:
            assert owner.observation is evidence
            assert attempts[0][0] == attempts[1][0] == owner.claim
            assert attempts[0][1]["observation_request"] is attempts[1][1]["observation_request"]
            assert events == [
                "guard_enter",
                "guard_exit",
                "close",
                "wait",
                "probe",
                "close",
                "guard_enter",
            ]
            with service.writer_scope("all_kvk", owner_token=owner) as nested:
                assert nested is owner
                service.verify_producer_cursor(object())
                body()
                service.record_writer_completion(procedure="qualified-test-publication")
            runtime.capture.assert_not_called()
        assert service._captures.get() == [
            ("all_kvk", 7, None),
            ("all_kvk", 7, owner.claim.preparation_id),
        ]
    body.assert_called_once()
    dal.request.assert_called_once()
    assert dal.claim.call_count == 2  # Original preflight and writing claims only.
    assert dal.session.call_count == 2
    dal.captured.assert_called_once()
    runtime.capture.assert_called_once()
    assert all(c.closed for c in connections)
    assert owner.closed
    assert not any(c.kwargs.get("state") == "unavailable" for c in dal.transition.call_args_list)


@pytest.mark.parametrize("failure", ["unknown_close", "second_deferral", "config_drift"])
def test_actual_admission_failure_preserves_claim_and_no_business_replay(
    tmp_path, monkeypatch, failure
):
    runtime, dal, events, connections, attempts, _ = setup_runtime(
        tmp_path,
        monkeypatch,
        close_failure=failure == "unknown_close",
        repeat_deferral=failure == "second_deferral",
    )
    if failure == "config_drift":
        old = scheduling.time.sleep

        def change(seconds):
            old(seconds)
            runtime.configuration += " "

        scheduling.time.sleep = change
    expected = (
        custody.SqlCleanupUnknown
        if failure == "unknown_close"
        else (ObservationDeferred if failure == "second_deferral" else service.SnapshotUnavailable)
    )
    with service.use_runtime(runtime), pytest.raises(expected):
        with service.writer_scope("all_kvk"):
            pytest.fail("Business body must not enter")
    dal.request.assert_called_once()
    runtime.capture.assert_not_called()
    dal.captured.assert_not_called()
    unavailable = [
        c for c in dal.transition.call_args_list if c.kwargs.get("state") == "unavailable"
    ]
    if failure == "unknown_close":
        assert not unavailable
        assert custody.connection_retained(connections[0])
        assert events == ["guard_enter", "guard_exit", "close"]
        dal.observation_boundary.assert_not_called()
    else:
        assert len(unavailable) == 1
        assert all(c.closed for c in connections)
        assert len(attempts) == (2 if failure == "second_deferral" else 1)


@pytest.mark.parametrize(
    "fault", [None, "cursor_close", "connection_close", "mismatch", "unbracketed"]
)
def test_owned_startup_observation_closes_before_continuation_and_acceptance(monkeypatch, fault):
    from services import (
        catalogue_observation_dal as catalogue,
        export_runtime_composition as composition,
    )
    from tests.test_observer_contract_selection import sample_proof

    clock = Clock()
    owner = request(clock)
    proof = sample_proof()
    connections = []
    calls = []

    def connect():
        raw = Mock()
        raw.cursor.return_value.connection = raw
        raw.closed = False
        raw.close.side_effect = lambda: setattr(raw, "closed", True)
        if fault == "connection_close":
            raw.close.side_effect = OSError("lost connection close")
        if fault == "cursor_close":
            raw.cursor.return_value.close.side_effect = OSError("lost cursor close")
        connections.append(raw)
        return raw

    def collect(cursor, approved):
        calls.append("collect")
        if len(calls) == 1:
            raise ObservationDeferred("generation_changed")
        return proof.value if fault == "unbracketed" else proof

    def wait(seconds):
        assert all(c.closed for c in connections)
        clock.sleep(seconds)

    compare = Mock(
        side_effect=ObservationContractError("mismatch") if fault == "mismatch" else None
    )
    after = Mock()
    owner.wait = wait
    monkeypatch.setattr(composition, "application_snapshot_for_contract", collect)
    monkeypatch.setattr(composition, "verify_application_installation_contract", compare)
    monkeypatch.setattr(catalogue, "read_boundary", Mock(return_value=proof.boundary))
    approved = application_contract.__wrapped__()
    if fault:
        expected = custody.SqlCleanupUnknown if "close" in fault else ObservationContractError
        with pytest.raises(expected):
            scheduling.observe_application(connect, approved, request=owner, after_read=after)
        after.assert_not_called()
    else:
        assert (
            scheduling.observe_application(connect, approved, request=owner, after_read=after)
            is proof
        )
        assert all(c.closed for c in connections)
        after.assert_called_once()
        compare.assert_called_once_with(proof.value, approved, observation=proof)
    assert len(connections) == (1 if fault and "close" in fault else 3)
    if fault and "close" in fault:
        assert custody.connection_retained(connections[0])
        assert calls == ["collect"]
    for raw in connections:
        raw.commit.assert_not_called()
        raw.rollback.assert_not_called()


def test_invalid_successor_source_refuses_before_opening_connection():
    approved = application_contract.__wrapped__()
    approved["scope_hash"] = "0" * 64
    connect = Mock()
    with pytest.raises(SourceConflict):
        scheduling.observe_application(connect, approved)
    connect.assert_not_called()


def test_one_active_one_waiting_and_third_pending_without_sql(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    lane = scheduling.ObservationLane()
    monkeypatch.setattr(scheduling, "observation_lane", lane)
    entered, release, waiting = Event(), Event(), Event()
    second_read = Mock(return_value="second")

    def first():
        entered.set()
        assert release.wait(5)
        return "first"

    class WaitingRequest(scheduling.ObservationRequest):
        def check(self):
            super().check()
            if lane._waiting is not None:
                waiting.set()

    with ThreadPoolExecutor(max_workers=2) as pool:
        active = pool.submit(scheduling.ObservationRequest().run, first, Mock())
        assert entered.wait(5)
        pending = pool.submit(WaitingRequest().run, second_read, Mock())
        try:
            assert waiting.wait(5)
            rejected = Mock()
            with pytest.raises(ObservationDeferred, match="observation_pending"):
                scheduling.ObservationRequest().run(rejected, Mock())
            rejected.assert_not_called()
            second_read.assert_not_called()
        finally:
            release.set()
        assert active.result(5) == "first"
        assert pending.result(5) == "second"
    second_read.assert_called_once()
    assert lane._active is lane._waiting is None


def test_borrowed_capture_cursor_never_waits_or_changes_transaction(monkeypatch):
    from services import export_runtime_composition as composition

    lane = scheduling.ObservationLane()
    monkeypatch.setattr(scheduling, "observation_lane", lane)
    cursor = Mock()
    with lane.enter(scheduling.ObservationRequest()):
        with pytest.raises(ObservationDeferred, match="observation_pending"):
            composition.verify_application_cursor(cursor, application_contract.__wrapped__())
    cursor.execute.assert_not_called()
    cursor.connection.commit.assert_not_called()
    cursor.connection.rollback.assert_not_called()


def test_existing_verifier_deadline_bounds_collection_and_quiet_wait(monkeypatch):
    from scripts.verify_k98_running_release import ObservationConnections

    clock = Clock()
    owner = ObservationConnections(Mock(), clock=clock.monotonic)
    clock.value = 40.0  # Fixed/legacy checks have already used the original budget.
    request = owner.observation_request()
    request.wait = clock.sleep
    assert request.deadline == owner.deadline == 45.0
    with request.collection():
        assert request._collection_deadline == 45.0
    clock.value = 44.5
    collect = Mock(side_effect=ObservationDeferred("active_writer"))
    probe = Mock()
    with pytest.raises(ObservationDeferred, match="observation_deadline"):
        request.run(collect, probe)
    assert clock.value == 44.5
    assert not clock.waits
    probe.assert_not_called()
    owner.connect.assert_not_called()


def test_actual_writer_waits_for_longer_peer_without_new_claim_or_business_replay(
    tmp_path, monkeypatch
):
    runtime, dal, events, connections, attempts, evidence = setup_runtime(tmp_path, monkeypatch)
    clock = scheduling.time
    original_probe = dal.observation_boundary.side_effect

    def peer_finishing(connection, request):
        original_probe(connection, request)
        if clock.value < 15.0:
            raise ObservationDeferred("active_writer")

    dal.observation_boundary.side_effect = peer_finishing
    body = Mock()
    with service.use_runtime(runtime), service.producer_capture_scope():
        with service.writer_scope("all_kvk") as owner:
            assert owner.observation is evidence
            assert clock.value == 15.5
            assert attempts[0][0] == attempts[1][0] == owner.claim
            body()
            service.record_writer_completion(procedure="qualified-test-publication")
    assert clock.waits == [1.0, 14.5]
    assert events.count("probe") == 2
    assert all(connection.closed for connection in connections)
    body.assert_called_once()
    dal.request.assert_called_once()
    dal.captured.assert_called_once()
    runtime.capture.assert_called_once()
    assert not any(
        call.kwargs.get("state") == "unavailable" for call in dal.transition.call_args_list
    )


def test_actual_three_contract_verifier_passes_original_owner_deadline(monkeypatch):
    from types import SimpleNamespace

    from scripts.verify_k98_running_release import ObservationConnections
    from scripts.verify_k98_update_pair import verify_bot_sql_contracts
    from services import export_execution_dal as dal, export_runtime_composition as composition
    from services.export_observer_contract import LEGACY_FINGERPRINT_FORMAT

    clock = Clock()
    raw = Mock()
    owner = ObservationConnections(Mock(return_value=raw), clock=clock.monotonic)
    application = application_contract.__wrapped__()
    fixed = dict(application, version=4, profile="application")
    legacy = dict(application, version=2, fingerprint_format=LEGACY_FINGERPRINT_FORMAT, source={})
    bot = dict(sql_contract=fixed, legacy_sql_contract=legacy, application_sql_contract=application)

    def fixed_read(**_):
        clock.value = 20.0
        return "fixed"

    def legacy_read(*_):
        clock.value = 40.0
        return "legacy"

    monkeypatch.setattr(
        dal, "ExportExecutionDAL", lambda _: SimpleNamespace(installation_snapshot=fixed_read)
    )
    monkeypatch.setattr(dal, "installation_migrations", lambda _: ())
    monkeypatch.setattr(dal, "legacy_installation_snapshot", legacy_read)
    monkeypatch.setattr(composition, "verify_installation_contract", Mock())
    monkeypatch.setattr(composition, "verify_legacy_installation_contract", Mock())

    def application_read(factory, approved, *, request):
        assert factory is owner and approved is application
        assert request.deadline == owner.deadline == 45.0
        assert all(connection.closed for connection in owner.connections)
        assert request.clock() == 40.0
        raise ObservationDeferred("active_writer")

    application_read = Mock(side_effect=application_read)
    monkeypatch.setattr(scheduling, "observe_application", application_read)
    with pytest.raises(ObservationDeferred, match="active_writer"):
        verify_bot_sql_contracts(bot, connection_factory=owner)
    application_read.assert_called_once()
    assert owner.phase == "application"
    raw.close.assert_called_once()
