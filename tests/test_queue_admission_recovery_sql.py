import json
import os
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.queue_admission_recovery import QueueAdmissionRecovery
from services.queue_admission_recovery_dal import QueueAdmissionDAL
from services.recovery_service import RecoveryService
from tests.test_export_target_containment_sql import contained_job as contained_job
from tests.test_guided_recovery import ACTOR, Store, execute
from tests.test_producer_admission_recovery_sql import unstarted
from tests.test_producer_refusal_sql import refused as refused, unblock
from tests.test_recovery_sql import store as store


def legacy_unstarted(r):
    unblock(r)
    request = json.loads(r.runtime.dal.read(r.source)["RequestJson"])["request"]
    request.pop("producer")
    request["operation"] = str(uuid4())
    r.source = r.runtime.dal.request(
        account=r.runtime.account,
        consumer="scan_data",
        kvk_no=None,
        request=request,
        storage_owner="disk",
        actor="test",
        reason="Legacy queued request",
    )


pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Explicit local disposable SQL opt-in"
)


def service_for(r):
    adapter = QueueAdmissionRecovery(QueueAdmissionDAL(r.runtime))
    store = Store()
    service = RecoveryService(store, {adapter.kind: adapter}, admin_id=1, guild_id=2, channel_id=3)
    row = service.review_source(ACTOR, adapter.kind, r.source)
    return adapter, store, service, row


def withdrawn_configuration_read(r, *, associated=False):
    request = dict(read_configuration=str(uuid4()))
    if associated:
        request["configuration_import"] = dict(invocation_mode="publish")
    r.source = r.runtime.dal.request(
        account=r.runtime.account,
        consumer="config",
        kvk_no=None,
        request=request,
        storage_owner=r.runtime.store.storage_owner,
        actor="system:configuration",
        reason="Read immutable configuration inputs",
    )
    r.runtime.dal.withdraw_unstarted(r.source)


@pytest.mark.asyncio
async def test_close_withdrawn_read_guided_confirmation_report_and_lost_reply(refused, monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from services.recovery_release_policy import p0a_presentation
    from services.recovery_report import incident_report
    from ui.views import recovery_view as view

    r = refused
    withdrawn_configuration_read(r)
    adapter, store, service, row = service_for(r)
    service.presentation_policy = p0a_presentation
    original = r.runtime.dal.read(r.source)
    assert set(row["evidence"]["actions"]) == {"close_withdrawn_read"}
    assert not row["evidence"]["recovery_links"]
    close = adapter.dal.close_withdrawn_read

    def lost(*args):
        close(*args)
        raise TimeoutError("lost acknowledgement")

    monkeypatch.setattr(adapter.dal, "close_withdrawn_read", lost)

    async def call(method, *args):
        return getattr(service, method)(*args)

    monkeypatch.setattr(view, "call", call)
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    await next(
        b for b in view.RecoveryIncidentView(row).children if b.label == "Close withdrawn read"
    ).callback(interaction)
    assert not store.actions
    confirmation = interaction.followup.send.call_args.kwargs["view"]
    await next(b for b in confirmation.children if b.label.startswith("Confirm")).callback(
        interaction
    )
    final = service.refresh(row["IncidentID"])
    assert final["State"] == "resolved" and store.actions[0]["State"] == "verified"
    assert not final["pending_action"]
    after = r.runtime.dal.read(r.source)
    for key in ("RequestJson", "RequestHash", "OwnerID", "Fence", "State"):
        assert after[key] == original[key]
    assert (
        incident_report(service, final)["diagnosis"]["failure_context"]["input_identity"]
        == "not_recorded"
    )
    assert service.refresh(row["IncidentID"])["State"] == "resolved"


def test_withdrawn_read_alias_routes_to_one_decision_then_verifies_closure(refused, store):
    from unittest.mock import Mock

    from services.config_read_recovery_adapter import ConfigReadRecoveryAdapter

    r = refused
    withdrawn_configuration_read(r)
    queue = QueueAdmissionRecovery(QueueAdmissionDAL(r.runtime))
    service = RecoveryService(store, {queue.kind: queue}, admin_id=1, guild_id=2, channel_id=3)
    row = service.review_source(ACTOR, queue.kind, r.source)
    client = Mock()
    alias = ConfigReadRecoveryAdapter(
        Mock(),
        client,
        account=r.runtime.account,
        storage_owner=r.runtime.store.storage_owner,
        queue_dal=queue.dal,
    )
    service.adapters[alias.kind] = alias
    read_row = service.review_source(ACTOR, alias.kind, r.source)
    assert not read_row["evidence"]["actions"]
    assert read_row["evidence"]["recovery_links"] == [
        dict(label="Review withdrawn queue entry", kind="queue_admission", source_id=r.source)
    ]
    execute(service, row, action="close_withdrawn_read")
    assert service.refresh(read_row["IncidentID"])["State"] == "resolved"
    client.inspect_configuration_recovery.assert_not_called()


def test_admitted_read_still_uses_authority_membership_verification(refused):
    from unittest.mock import Mock

    from services.config_read_recovery_adapter import ConfigReadRecoveryAdapter

    r = refused
    withdrawn_configuration_read(r)
    r.f.sql.execute(
        "UPDATE #ExportPreparation SET Version=4,Fence=2,State='uncertain' WHERE PreparationID=?",
        r.source,
    )
    client = Mock()
    client.inspect_configuration_recovery.return_value = dict(
        eligible=False,
        outcome="held",
        token="a" * 64,
        explanation="Reservation membership differs from the installed configuration.",
    )
    adapter = ConfigReadRecoveryAdapter(
        Mock(),
        client,
        account=r.runtime.account,
        storage_owner=r.runtime.store.storage_owner,
        queue_dal=QueueAdmissionDAL(r.runtime),
    )
    evidence, _, resolved = adapter.inspect(r.source)
    assert not resolved and not evidence["actions"]
    client.inspect_configuration_recovery.assert_called_once_with(r.source)


@pytest.mark.parametrize(
    "change", ["version", "hash", "generation", "consumer", "association", "membership"]
)
def test_withdrawn_read_refuses_changed_or_typed_evidence(refused, change):
    from kvk.dal.new_source_import_dal import digest

    r = refused
    withdrawn_configuration_read(r, associated=change == "association")
    dal = QueueAdmissionDAL(r.runtime)
    state = dal.snapshot(r.source)
    if change == "version":
        state["preparation"]["Version"] += 1
    elif change == "hash":
        state["preparation"]["RequestHash"] = "0" * 64
    elif change == "generation":
        state["preparation"]["GenerationJson"] = "{}"
    elif change == "consumer":
        state["preparation"]["ConsumerKind"] = "scan_data"
    elif change == "membership":
        state["counts"]["ExportPreparationResource"] = 1
    assert not dal.withdrawn_read(state)
    with pytest.raises(SourceConflict):
        dal.close_withdrawn_read(
            r.source, digest(state).hex() if change == "association" else "0" * 64, str(uuid4())
        )


def test_cancel_initial_queue_entry_fences_late_worker_and_verifies(refused):
    r = refused
    legacy_unstarted(r)
    adapter, store, service, row = service_for(r)
    assert r.source in adapter.pending_recovery()
    assert "withdraw_queued" in row["evidence"]["actions"]
    result = execute(service, row, action="withdraw_queued")
    assert result["State"] == "resolved" and store.actions[0]["State"] == "verified"
    assert r.runtime.dal.read(r.source)["State"] == "unavailable"
    with pytest.raises(SourceConflict):
        r.runtime.dal.claim(
            r.source,
            account=r.runtime.account,
            storage_owner="disk",
            stage="preflight",
            resource_keys=("account:" + r.runtime.account,),
        )


@pytest.mark.parametrize("stage", ["preflight", "sql_pending", "writing", "uncertain"])
@pytest.mark.asyncio
async def test_admitted_or_uncertain_work_requires_domain_recovery(refused, stage):
    from ui.views.recovery_view import RecoveryIncidentView

    r = refused
    unstarted(r, stage)
    _, _, _, row = service_for(r)
    assert not row["evidence"]["actions"]
    assert row["State"] == "open"
    assert row["evidence"]["recovery_links"][0]["kind"] == "producer_refusal"
    view = RecoveryIncidentView(row)
    assert "Review execution and ownership" in [item.label for item in view.children]
    assert r.runtime.dal.read(r.source)["State"] == stage


def test_admission_race_does_not_release_new_owner(refused):
    r = refused
    legacy_unstarted(r)
    adapter, store, service, row = service_for(r)
    r.runtime.dal.claim(
        r.source,
        account=r.runtime.account,
        storage_owner="disk",
        stage="preflight",
        resource_keys=("account:" + r.runtime.account,),
    )
    with pytest.raises(SourceConflict, match="evidence changed"):
        execute(service, row, action="withdraw_queued")
    result = service.review(ACTOR, row["IncidentID"])
    assert result["evidence"]["outcome"] == "execution_review_required"
    assert result["State"] == "open"
    assert not store.actions
    assert r.runtime.dal.read(r.source)["State"] == "preflight"


def test_lost_withdrawal_reply_reconciles_without_repeating(refused, monkeypatch):
    r = refused
    legacy_unstarted(r)
    adapter, store, service, row = service_for(r)
    withdraw = adapter.dal.withdraw

    def lost(*args):
        withdraw(*args)
        raise TimeoutError("lost response")

    monkeypatch.setattr(adapter.dal, "withdraw", lost)
    result = execute(service, row, action="withdraw_queued")
    assert result["State"] == "resolved"
    assert store.actions[0]["State"] == "verified"


def test_typed_queue_routes_to_domain_close_and_saved_continuation(refused):
    from tests.test_producer_refusal_sql import setup

    r = refused
    unstarted(r, "pending")
    adapter, _, _, row = service_for(r)
    assert not row["evidence"]["actions"]
    assert row["evidence"]["recovery_links"][0]["kind"] == "producer_refusal"
    with pytest.raises(SourceConflict):
        adapter.dal.withdraw(r.source, row["EvidenceHash"], str(uuid4()))
    producer, store, service, row = setup(r)
    closed = execute(service, row, action="close_unstarted_admission")
    assert store.actions[0]["State"] == "verified"
    assert closed["evidence"]["actions"].keys() == {"resume_sql_stage", "cancel_saved_stage"}
    execute(service, closed, action="resume_sql_stage")
    producer.runner.assert_called_once_with(r.inputs)


@pytest.mark.parametrize(
    "producer_kind,linked_kind",
    [
        ("configuration_import", "configuration_producer"),
        ("player_stats_report", "player_report"),
    ],
)
def test_other_typed_producers_preserve_domain_cancellation(refused, producer_kind, linked_kind):
    r = refused
    unblock(r)
    request = json.loads(r.runtime.dal.read(r.source)["RequestJson"])["request"]
    request["operation"] = str(uuid4())
    request["producer"]["kind"] = producer_kind
    r.source = r.runtime.dal.request(
        account=r.runtime.account,
        consumer="scan_data",
        kvk_no=None,
        request=request,
        storage_owner="disk",
        actor="test",
        reason="Typed queued request",
    )
    adapter, _, _, row = service_for(r)
    assert not row["evidence"]["actions"]
    assert row["evidence"]["recovery_links"][0]["kind"] == linked_kind
    with pytest.raises(SourceConflict):
        adapter.dal.withdraw(r.source, row["EvidenceHash"], str(uuid4()))
    assert r.runtime.dal.read(r.source)["State"] == "pending"


def test_queue_discovery_covers_more_than_one_page_and_wraps(refused):
    r = refused
    expected = set()
    for _ in range(45):
        unstarted(r, "pending")
        expected.add(r.source)
    dal = QueueAdmissionDAL(r.runtime)
    first = dal.pending()
    second = dal.pending(first[-1])
    third = dal.pending(second[-1])
    assert len(first) == len(second) == len(third) == 20
    assert not set(first) & set(second)
    assert set(first + second + third) == expected
    assert set(first) & set(third)  # cyclic continuation, with rows still pending
    # The cursor is an ordering boundary, not a row lookup: deletion/state change
    # of that preparation must not restart discovery at the first page.
    r.f.sql.execute(
        "UPDATE #ExportPreparation SET State='unavailable',OwnerID=?,Fence=1,Version=2 WHERE PreparationID=?",
        str(uuid4()),
        first[-1],
    )
    assert dal.pending(first[-1]) == second


@pytest.mark.parametrize("verified", [False, True])
def test_terminal_queue_state_requires_owning_domain_verification(refused, verified):
    from unittest.mock import Mock

    r = refused
    unstarted(r, "pending")
    r.f.sql.execute(
        "UPDATE #ExportPreparation SET State='unavailable',OwnerID=?,Fence=1,Version=2 WHERE PreparationID=?",
        str(uuid4()),
        r.source,
    )
    dal = QueueAdmissionDAL(r.runtime)
    assert QueueAdmissionRecovery(dal).inspect(r.source)[2] is False
    domain = Mock()
    domain.inspect.return_value = ({}, "d" * 64, verified)
    adapter = QueueAdmissionRecovery(dal, {"producer_refusal": domain})
    evidence, _, resolved = adapter.inspect(r.source)
    assert resolved is verified
    assert not evidence["actions"]
    assert evidence["outcome"] == (
        "domain_recovery_verified" if verified else "execution_review_required"
    )
    domain.inspect.assert_called_once_with(r.source)
    domain.inspect.side_effect = TimeoutError("verification unavailable")
    with pytest.raises(TimeoutError):
        adapter.inspect(r.source)


def test_priority_refresh_pages_and_wraps_independently_with_no_duplicate_checks(
    store, monkeypatch
):
    from contextlib import contextmanager
    from types import SimpleNamespace
    from unittest.mock import Mock

    from services import recovery_runtime as runtime

    operational = {
        store.observe("queue_admission", str(uuid4()), dict(actions={}), "a" * 64)["IncidentID"]
        for _ in range(45)
    }
    copies = [
        store.observe("private_evidence", str(uuid4()), dict(actions={}), "b" * 64)
        for _ in range(25)
    ]
    original_list = store.list_open
    first = original_list(non_evidence=True)[0]
    monkeypatch.setattr(
        store,
        "list_open",
        lambda **kwargs: (
            original_list(**kwargs) if kwargs.get("non_evidence") else copies[:19] + [first]
        ),
    )
    refreshed = Mock()

    @contextmanager
    def scoped_service():
        yield SimpleNamespace(
            store=store,
            adapters={"queue_admission": SimpleNamespace(pending_recovery=lambda **kwargs: [])},
            recover_automatic=refreshed,
        )

    monkeypatch.setattr(runtime, "recovery_service", scoped_service)
    monkeypatch.setattr(runtime, "_retry_admission", lambda: True)
    monkeypatch.setattr(runtime, "_cursors", {})
    monkeypatch.setattr(runtime, "_incident_cursor", None)
    monkeypatch.setattr(runtime, "_priority_incident_cursor", None)
    seen = set()
    for expected_count in (20, 21, 6, 1, 20):
        refreshed.reset_mock()
        assert runtime.observe_recovery() == []
        checked = [call.args[0] for call in refreshed.call_args_list]
        assert len(checked) == len(set(checked)) == expected_count
        seen.update(checked)
    assert seen == operational


@pytest.mark.parametrize("verified", [False, True])
def test_terminal_queue_is_refreshed_ahead_of_evidence_backlog(
    refused, store, monkeypatch, verified
):
    from contextlib import contextmanager
    from unittest.mock import Mock

    from services import recovery_runtime as runtime

    recovery_store = store
    r = refused
    unstarted(r, "pending")
    domain = Mock()
    domain.inspect.return_value = ({}, "d" * 64, verified)
    adapter = QueueAdmissionRecovery(QueueAdmissionDAL(r.runtime), {"producer_refusal": domain})
    service = RecoveryService(
        recovery_store, {adapter.kind: adapter}, admin_id=1, guild_id=2, channel_id=3
    )
    queue = service.review_source(ACTOR, adapter.kind, r.source)
    backlog = [
        recovery_store.observe("private_evidence", str(uuid4()), dict(actions={}), "a" * 64)
        for _ in range(25)
    ]
    r.f.sql.execute(
        "UPDATE #ExportPreparation SET State='unavailable',OwnerID=?,Fence=1,Version=2 WHERE PreparationID=?",
        str(uuid4()),
        r.source,
    )
    r.f.sql.commit()
    assert r.source not in adapter.pending_recovery()

    @contextmanager
    def scoped_service():
        yield service

    original_list = recovery_store.list_open
    monkeypatch.setattr(
        recovery_store,
        "list_open",
        lambda **kwargs: original_list(**kwargs) if kwargs.get("non_evidence") else backlog[:20],
    )
    monkeypatch.setattr(runtime, "recovery_service", scoped_service)
    monkeypatch.setattr(runtime, "_retry_admission", lambda: True)
    monkeypatch.setattr(runtime, "_cursors", {})
    monkeypatch.setattr(runtime, "_incident_cursor", None)
    monkeypatch.setattr(runtime, "_priority_incident_cursor", None)
    assert runtime.observe_recovery() == []
    result = recovery_store.get(queue["IncidentID"])
    assert result["State"] == ("resolved" if verified else "open")
    domain.inspect.assert_called_once_with(r.source)


def health_request(r, actor="system:health_probe:v1"):
    return r.runtime.dal.request(
        account=r.runtime.account,
        consumer="config",
        kvk_no=None,
        request=dict(read_configuration=str(uuid4())),
        storage_owner=r.runtime.store.storage_owner,
        actor=actor,
        reason="Read immutable configuration inputs",
    )


def test_health_cleanup_keeps_other_export_owner_and_fences_late_claim(refused):
    r = refused
    r.source = health_request(r)
    before = r.f.sql.execute(
        "SELECT Version,Fence,ActiveJobID FROM #ExportResource WHERE ResourceKey='account:test-account'"
    ).fetchone()
    dal = QueueAdmissionDAL(r.runtime)
    dal.withdraw_health_probe(r.source)
    assert r.runtime.dal.read(r.source)["State"] == "unavailable"
    assert tuple(
        r.f.sql.execute(
            "SELECT Version,Fence,ActiveJobID FROM #ExportResource WHERE ResourceKey='account:test-account'"
        ).fetchone()
    ) == tuple(before)
    unblock(r)
    with pytest.raises(SourceConflict):
        r.runtime.dal.claim(
            r.source,
            account=r.runtime.account,
            storage_owner="disk",
            stage="preflight",
            resource_keys=("account:test-account",),
        )


def test_health_restart_discovers_and_automatically_withdraws(refused):
    r = refused
    r.source = health_request(r)
    adapter, store, service, row = service_for(r)
    assert r.source in adapter.pending_recovery()
    assert set(row["evidence"]["actions"]) == {"withdraw_health_probe"}
    result = service.recover_automatic(row["IncidentID"])
    assert result["State"] == "resolved"
    assert store.actions[-1]["State"] == "verified"
    # Fresh objects have no in-memory identity or request handle to rely on.
    fresh = QueueAdmissionRecovery(QueueAdmissionDAL(r.runtime))
    assert fresh.inspect(r.source)[2]
    assert r.source not in fresh.pending_recovery()


def test_health_lost_cleanup_reply_is_reconciled_without_second_write(refused, monkeypatch):
    r = refused
    r.source = health_request(r)
    adapter, store, service, row = service_for(r)
    original = adapter.dal.withdraw_health_probe
    calls = []

    def lost(*args):
        calls.append(args)
        original(*args)
        raise TimeoutError("lost reply")

    monkeypatch.setattr(adapter.dal, "withdraw_health_probe", lost)
    result = service.recover_automatic(row["IncidentID"])
    assert result["State"] == "resolved"
    assert len(calls) == 1
    assert store.actions[-1]["State"] == "verified"


def test_health_pending_cleanup_retries_after_restart(refused, monkeypatch):
    from services.export_contention import CoordinationLockRefused

    r = refused
    r.source = health_request(r)
    adapter, store, service, row = service_for(r)
    error = CoordinationLockRefused(
        result=-1, session=1, transaction_state=1, transaction_count=1, resource_hash="a" * 64
    )
    error.transaction_released = True
    monkeypatch.setattr(
        adapter.dal, "withdraw_health_probe", lambda *a: (_ for _ in ()).throw(error)
    )
    from core.sql_observation import ObservationBusy

    with pytest.raises(ObservationBusy):
        service.recover_automatic(row["IncidentID"])
    assert r.runtime.dal.read(r.source)["State"] == "pending"
    service.adapters[adapter.kind] = QueueAdmissionRecovery(QueueAdmissionDAL(r.runtime))
    assert service.recover_automatic(row["IncidentID"])["State"] == "resolved"


def test_ordinary_config_stays_guided_and_cannot_use_health_action(refused):
    r = refused
    r.source = health_request(r, "system:configuration")
    adapter, store, service, row = service_for(r)
    assert set(row["evidence"]["actions"]) == {"withdraw_queued"}
    service.recover_automatic(row["IncidentID"])
    assert not store.actions
    with pytest.raises(SourceConflict):
        adapter.dal.withdraw_health_probe(r.source)


def test_health_claim_wins_race_and_cleanup_retains_ownership(refused):
    r = refused
    r.source = health_request(r)
    dal = QueueAdmissionDAL(r.runtime)
    from kvk.dal.new_source_import_dal import digest

    token = digest(dal.snapshot(r.source)).hex()
    unblock(r)
    claim = r.runtime.dal.claim(
        r.source,
        account=r.runtime.account,
        storage_owner="disk",
        stage="preflight",
        resource_keys=("account:test-account",),
    )
    assert claim
    with pytest.raises(SourceConflict):
        dal.withdraw_health_probe(r.source, token)
    assert r.runtime.dal.read(r.source)["State"] == "preflight"
