"""Long publication checks retain their pending action during concurrent review."""

import json
from threading import Event, Thread
from uuid import uuid4

import pytest

from services.export_proof_progress import AuthorityProofBusy
from services.recovery_execution_guard import recovery_execution
from services.recovery_service import RecoveryService
from tests.test_export_recovery import job_fixture
from tests.test_guided_recovery import ACTOR, Store


@pytest.mark.parametrize("stream_visible", [False, True])
def test_recheck_and_repeat_confirmation_do_not_race_live_publication(stream_visible, monkeypatch):
    adapter, snapshot = job_fixture(state="confirmed", attempted=True)
    store = Store()
    source = snapshot["job"]["JobID"]
    evidence, token, resolved = adapter.inspect(source)
    row = store.observe(adapter.kind, source, evidence, token, resolved=resolved)

    def service():
        # Production creates a new service for each command and observer call.
        return RecoveryService(store, {adapter.kind: adapter}, admin_id=1, guild_id=2, channel_id=3)

    entered, finish = Event(), Event()
    errors, results = [], []

    def probe(_):
        if stream_visible:
            snapshot["streams"].append(dict(StreamID=str(uuid4())))
        entered.set()
        assert finish.wait(5), "Test did not release its disposable proof worker"
        return dict(state="confirmed", proof_id=str(uuid4()))

    def settled(_snapshot, proof, *, actor):
        snapshot["job"]["ProvenanceJson"] = json.dumps(
            dict(reconciliations=[dict(actor=actor, proof=proof)])
        )
        snapshot["job"]["Version"] += 1

    adapter.reconciler.probe.side_effect = probe
    adapter.coordinator.reconcile_operator.side_effect = settled

    def execute():
        try:
            results.append(
                service().execute(
                    ACTOR,
                    row["IncidentID"],
                    row["Revision"],
                    token,
                    "verify_publication",
                    "Check this retained output",
                )
            )
        except BaseException as exc:
            errors.append(exc)

    worker = Thread(target=execute)
    worker.start()
    try:
        assert entered.wait(5)
        original_inspect = adapter.inspect

        def inspect(source_id):
            if not finish.is_set():
                raise AuthorityProofBusy("Authority-backed inspection is busy")
            return original_inspect(source_id)

        monkeypatch.setattr(adapter, "inspect", inspect)
        reviewed = service().review(ACTOR, row["IncidentID"])
        assert reviewed["pending_action"] == dict(state="dispatched", kind="verify_publication")
        assert reviewed["execution_progress"]["state"] == "in_progress"
        assert store.actions[0]["State"] == "dispatched"
        repeated = service().execute(
            ACTOR,
            row["IncidentID"],
            row["Revision"],
            token,
            "verify_publication",
            "Duplicate click",
        )
        assert repeated["pending_action"]["state"] == "dispatched"
        assert adapter.reconciler.probe.call_count == 1
        adapter.coordinator.reconcile_operator.assert_not_called()
    finally:
        finish.set()
        worker.join(5)
    assert not worker.is_alive() and not errors
    assert results[0]["pending_action"] is None
    assert store.actions[0]["State"] == "verified"
    assert len(store.actions) == adapter.coordinator.reconcile_operator.call_count == 1


def test_monitor_reconciliation_does_not_run_twice_or_block_other_incidents():
    from tests.test_guided_recovery import setup

    service, dal, store, row = setup()
    store.claim(
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "supersede_partial",
        "discord:1",
        "Accepted partial outcome",
    )
    original = service.adapters["stats_import"].reconcile
    entered, finish = Event(), Event()
    calls, errors = [], []

    def reconcile(*args):
        calls.append(args)
        entered.set()
        assert finish.wait(5)
        return original(*args)

    service.adapters["stats_import"].reconcile = reconcile

    def refresh():
        try:
            service.refresh(row["IncidentID"])
        except BaseException as exc:
            errors.append(exc)

    worker = Thread(target=refresh)
    worker.start()
    try:
        assert entered.wait(5)
        assert service.refresh(row["IncidentID"])["pending_action"]["state"] == "dispatched"
        other, _, _, other_row = setup()
        assert other.refresh(other_row["IncidentID"])["State"] == "open"
        assert len(calls) == 1
    finally:
        finish.set()
        worker.join(5)
    assert not worker.is_alive() and not errors
    assert len(dal.calls) == 1 and store.actions[0]["State"] == "verified"


def test_failed_local_execution_does_not_retain_guard_or_authorize_completion():
    key = str(uuid4())
    with pytest.raises(RuntimeError):
        with recovery_execution(key) as acquired:
            assert acquired
            raise RuntimeError("synthetic interruption")
    with recovery_execution(key) as acquired:
        assert acquired
