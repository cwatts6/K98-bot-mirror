"""Native catalogue contention must yield without replaying work or bypassing cleanup."""

from unittest.mock import Mock

import pytest

from core import sql_connection_custody as custody
from services import (
    application_observation_schedule as schedule,
    catalogue_observation_dal as dal,
    legacy_export_snapshot_service as service,
)
from tests.test_catalogue_observation import Cursor, expected, token
from tests.test_observer_admission_continuation import Clock, setup_runtime


@pytest.mark.parametrize(
    "phase",
    [
        "boundary_execute",
        "boundary_fetch",
        "boundary_next",
        "metadata_execute",
        "metadata_fetch",
        "metadata_next",
    ],
)
@pytest.mark.parametrize(
    "state,code,deferred",
    [
        ("42000", 1222, True),
        ("42000", 229, False),
        ("40001", 1205, False),
        ("HYT00", 0, False),
        ("08001", 1222, False),
    ],
)
def test_exact_read_failure_keeps_native_cause_and_discards_candidate(phase, state, code, deferred):
    error = Exception(state, f"native ({code})")
    cursor = Cursor(token(), token())
    if phase.startswith("boundary"):
        method = {
            "boundary_execute": "execute",
            "boundary_fetch": "fetchone",
            "boundary_next": "nextset",
        }[phase]
        setattr(cursor, method, Mock(side_effect=error))

    def metadata(checkpoint):
        if phase.startswith("metadata"):
            raise error
        pytest.fail("A failed initial boundary must not reach metadata")

    with pytest.raises(dal.ObservationDeferred if deferred else Exception) as caught:
        dal.observe_catalogue(cursor, expected(), metadata)
    if deferred:
        assert caught.value.reason == "catalogue_busy" and caught.value.__cause__ is error
    else:
        assert caught.value is error


@pytest.mark.parametrize("close_fault", [False, True])
def test_real_owner_closes_before_bounded_wait_and_never_retries_unknown_cleanup(
    monkeypatch, close_fault
):
    clock = Clock()
    connections = []
    native = Exception("42000", "catalogue lock (1222)")
    retained = []
    monkeypatch.setattr(custody, "retain_connection", lambda *a, **k: retained.append(k))

    def connect():
        raw = Mock(autocommit=False)
        cursor = Cursor(token(), token())
        cursor.close = Mock()
        raw.cursor.return_value = cursor
        raw.closed = False

        def close():
            if close_fault:
                raise OSError("unconfirmed original close")
            raw.closed = True

        raw.close.side_effect = close
        connections.append(raw)
        return raw

    def wait(seconds):
        assert all(c.closed for c in connections)
        clock.sleep(seconds)

    request = schedule.ObservationRequest(clock=clock.monotonic, wait=wait)
    attempts = []

    def collect():
        def read(cursor):
            with request.collection():
                attempts.append(1)

                def metadata(checkpoint):
                    if len(attempts) == 1:
                        raise native
                    return {"whole": "candidate"}

                return dal.observe_catalogue(cursor, expected(), metadata)

        return schedule.read_owned_observation(connect, read, request=request)

    def probe():
        return schedule.read_owned_observation(
            connect, lambda c: dal.read_boundary(c, expected()), request=request
        )

    if close_fault:
        with pytest.raises(custody.SqlCleanupUnknown):
            request.run(collect, probe)
        assert len(attempts) == 1 and not clock.waits and retained
        assert retained[0]["first_failure"].__cause__ is native
    else:
        assert request.run(collect, probe).value == {"whole": "candidate"}
        assert len(attempts) == 2 and request.collections == 2 and request.boundary_checks == 1
        assert all(c.closed for c in connections) and clock.waits == [1.0]


@pytest.mark.parametrize("reason", ["catalogue_busy", "active_writer", "generation_changed"])
def test_borrowed_producer_keeps_original_claim_and_runs_business_only_once(
    tmp_path, monkeypatch, reason
):
    runtime, store, events, connections, attempts, evidence = setup_runtime(tmp_path, monkeypatch)
    from contextlib import contextmanager

    old = store.session.side_effect

    @contextmanager
    def guard(*args, **kwargs):
        try:
            with old(*args, **kwargs) as result:
                yield result
        except dal.ObservationDeferred as error:
            raise dal.ObservationDeferred(reason) from error

    store.session.side_effect = guard
    body = Mock()
    with service.use_runtime(runtime), service.producer_capture_scope():
        with service.writer_scope("all_kvk") as owner:
            admitted_claim = owner.claim
            body()
            service.record_writer_completion(procedure="single-native-owner")
    body.assert_called_once()
    runtime.capture.assert_called_once()
    store.request.assert_called_once()
    assert attempts[0][0] == attempts[1][0] == admitted_claim
    assert all(c.closed for c in connections)


def test_catalogue_busy_probe_limit_keeps_first_failure_and_no_third_collection():
    clock = Clock()
    request = schedule.ObservationRequest(clock=clock.monotonic, wait=clock.sleep)
    original = dal.ObservationDeferred("catalogue_busy")
    collect = Mock(side_effect=original)
    probe = Mock(side_effect=dal.ObservationDeferred("catalogue_busy"))
    with pytest.raises(dal.ObservationDeferred) as caught:
        request.run(collect, probe)
    assert caught.value is original and collect.call_count == 1 and probe.call_count == 3
    assert request.boundary_checks == 3 and clock.value == 30
