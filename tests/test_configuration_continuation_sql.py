"""Actual SQL evidence and admin callbacks for fresh configuration continuation."""

import json
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.configuration_continuation import ConfigurationContinuation
from services.configuration_continuation_dal import ConfigurationContinuationDAL
from services.configuration_producer_recovery import ConfigurationProducerRecovery
from services.producer_recovery_intent import current_intent
from services.recovery_service import RecoveryService
from tests.test_guided_recovery import ACTOR, Store
from tests.test_import_capture_recovery_sql import recovery as recovery
from tests.test_player_report_recovery_sql import uncommitted

pytestmark = [
    pytest.mark.skipif(
        os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Disposable SQL opt-in required"
    ),
    pytest.mark.parametrize("recovery", ["configuration_continuation"], indirect=True),
]


def setup(r, runner=None):
    preview, _ = uncommitted(r)
    r.outcomes.cancel(r.source, preview["token"], "admin", "Verified rollback")
    r.runtime.account = "a"
    config = json.loads(r.runtime.configuration)
    config["config"] = dict(consumer="config", destinations=["source_sheet"])
    r.runtime.configuration = json.dumps(config)
    producer = ConfigurationProducerRecovery(r.outcomes, r.service)
    adapter = ConfigurationContinuation(
        ConfigurationContinuationDAL(r.runtime, r.outcomes),
        producer,
        runner=runner or (lambda: None),
    )
    service = RecoveryService(
        Store(),
        {adapter.kind: adapter, producer.kind: producer},
        admin_id=1,
        guild_id=2,
        channel_id=3,
    )
    return adapter, service


def run(service, row, action):
    return service.execute(
        ACTOR,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        action,
        "Admin checked current configuration",
    )


def test_no_dispatch_reply_creates_terminal_tombstone_and_allows_new_decision(recovery):
    r = recovery
    adapter, service = setup(r)
    assert r.source in adapter.pending_recovery()
    row = service.review_source(ACTOR, adapter.kind, r.source)
    action_id, _ = service.store.claim(
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "retry_configuration",
        "discord:1",
        "Confirmed",
    )
    final = service.refresh(row["IncidentID"])
    assert final["State"] == "open"
    assert "retry_configuration" in final["evidence"]["actions"]
    assert service.store.actions[0]["State"] == "not_applied"
    state = adapter.dal.snapshot(r.source)
    assert state["child"]["State"] == "unavailable"
    assert not r.outcomes.inspect(state["child"]["PreparationID"])["resources"]
    with pytest.raises(SourceConflict):
        adapter.execute(
            r.source,
            "retry_configuration",
            row["EvidenceHash"],
            "recovery:" + action_id,
            "Late callback",
        )


@pytest.mark.parametrize("read_continuation", [False, True])
def test_claimed_retry_reconstructs_no_export_intent_without_dispatch(recovery, read_continuation):
    calls = []
    if read_continuation:
        from tests.test_configuration_read_continuation_sql import setup as read_setup

        source, adapter, service = read_setup(recovery, lambda: calls.append(1))
    else:
        adapter, service = setup(recovery, lambda: calls.append(1))
        source = recovery.source
    row = service.review_source(ACTOR, adapter.kind, source)
    action_id, _ = service.store.claim(
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "retry_configuration",
        "discord:1",
        "Confirmed SQL-only refresh",
    )
    assert adapter.dal.snapshot(source)["marker"] is None
    restarted = type(adapter)(adapter.dal, adapter.producer, lambda: calls.append(1))
    service.adapters[adapter.kind] = restarted
    for _ in range(2):
        final = service.refresh(row["IncidentID"])
        state = restarted.dal.snapshot(source)
        child = state["child"]
        request = json.loads(child["RequestJson"])["request"]["producer"]
        assert state["marker"]["export_disposition"] == "configuration_only_v1"
        assert request["export_disposition"] == "configuration_only_v1"
        assert request["operation"] == action_id
        assert request["parent"] == source
        assert child["State"] == "unavailable"
        assert not recovery.outcomes.inspect(child["PreparationID"])["resources"]
        assert service.store.actions[0]["State"] == "not_applied"
        assert "retry_configuration" in final["evidence"]["actions"]
        assert calls == []
    with pytest.raises(SourceConflict):
        restarted.execute(
            source,
            "retry_configuration",
            row["EvidenceHash"],
            "recovery:" + action_id,
            "Late callback",
        )


def test_claimed_keep_prior_survives_restart_without_creating_continuation(recovery):
    calls = []
    adapter, service = setup(recovery, lambda: calls.append(1))
    row = service.review_source(ACTOR, adapter.kind, recovery.source)
    action_id, _ = service.store.claim(
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "keep_prior",
        "discord:1",
        "Confirmed prior configuration",
    )
    # The process stopped after the durable claim, before the callback recorded a marker.
    assert adapter.dal.snapshot(recovery.source)["marker"] is None
    restarted = ConfigurationContinuation(
        ConfigurationContinuationDAL(recovery.runtime, recovery.outcomes),
        adapter.producer,
        lambda: calls.append(1),
    )
    service.adapters[adapter.kind] = restarted
    for _ in range(2):
        final = service.refresh(row["IncidentID"])
        assert final["State"] == "resolved"
        assert service.store.actions[0]["State"] == "verified"
        state = restarted.dal.snapshot(recovery.source)
        assert state["marker"]["choice"] == "keep_prior"
        assert state["marker"]["action"] == action_id
        assert state["child"] is None
        assert calls == []
    assert recovery.source not in restarted.pending_recovery()
    with pytest.raises(SourceConflict):
        restarted.execute(
            recovery.source,
            "keep_prior",
            row["EvidenceHash"],
            "recovery:" + action_id,
            "Late callback",
        )


@pytest.mark.asyncio
async def test_actual_admin_buttons_review_sources_and_keep_prior(recovery, monkeypatch):
    from ui.views import recovery_view as view

    adapter, service = setup(recovery)
    row = service.review_source(ACTOR, adapter.kind, recovery.source)
    details = adapter.review_details(recovery.source, "retry_configuration", row["EvidenceHash"])
    assert any(field.get("file_id") == "source_sheet" for field in details)

    async def call(method, *args):
        return getattr(service, method)(*args)

    monkeypatch.setattr(view, "call", call)
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    button = next(
        b for b in view.RecoveryIncidentView(row).children if b.label == "Keep prior configuration"
    )
    await button.callback(interaction)
    confirmation = interaction.followup.send.call_args.kwargs["view"]
    assert not service.store.actions
    await next(b for b in confirmation.children if b.label.startswith("Confirm")).callback(
        interaction
    )
    final = service.refresh(row["IncidentID"])
    assert final["State"] == "resolved"
    assert service.store.actions[0]["State"] == "verified"
    assert recovery.source not in adapter.pending_recovery()


def test_runner_failure_is_reconciled_without_replay_and_new_retry_is_separate(recovery):
    calls = []

    def runner():
        calls.append(dict(current_intent()))
        raise TimeoutError("Fresh read failed before writer admission")

    adapter, service = setup(recovery, runner)
    row = service.review_source(ACTOR, adapter.kind, recovery.source)
    final = run(service, row, "retry_configuration")
    assert len(calls) == 1 and calls[0]["parent"] == recovery.source
    assert final["State"] == "open" and not final["pending_action"]
    restarted = ConfigurationContinuation(adapter.dal, adapter.producer, runner)
    service.adapters[adapter.kind] = restarted
    service.refresh(row["IncidentID"])
    assert len(calls) == 1
    run(service, final, "retry_configuration")
    assert len(calls) == 2 and calls[0]["operation"] != calls[1]["operation"]


def test_changed_registration_and_non_admin_cannot_dispatch(recovery):
    calls = []
    adapter, service = setup(recovery, lambda: calls.append(1))
    row = service.review_source(ACTOR, adapter.kind, recovery.source)
    from services.recovery_service import RecoveryActor

    with pytest.raises(SourceConflict):
        service.execute(
            RecoveryActor(9, 2, 3),
            row["IncidentID"],
            row["Revision"],
            row["EvidenceHash"],
            "retry_configuration",
            "No",
        )
    value = json.loads(recovery.runtime.configuration)
    value["config"]["destinations"] = ["changed_sheet"]
    recovery.runtime.configuration = json.dumps(value)
    with pytest.raises(SourceConflict):
        run(service, row, "retry_configuration")
    assert calls == []


def test_foreign_or_nested_root_is_rejected(recovery):
    adapter, _ = setup(recovery)
    adapter.dal.outcomes.account = "other-account"
    with pytest.raises(SourceConflict):
        adapter.inspect(recovery.source)


def test_lost_dispatch_marker_reply_reconciles_same_saved_registration(recovery):
    adapter, service = setup(recovery)
    row = service.review_source(ACTOR, adapter.kind, recovery.source)
    action = dict(
        ActionID=str(uuid4()),
        ActionKind="retry_configuration",
        EvidenceHash=row["EvidenceHash"],
        Reason="Confirmed",
    )
    with adapter.dal.serialized(recovery.source):
        state = adapter.dal.snapshot(recovery.source)
        adapter.dal.record(
            recovery.source,
            row["EvidenceHash"],
            dict(
                action=action["ActionID"],
                token=row["EvidenceHash"],
                choice="retry",
                configuration=state["current"],
            ),
        )
    value = json.loads(recovery.runtime.configuration)
    value["scan_data"]["destinations"] = ["new_destination"]
    recovery.runtime.configuration = json.dumps(value)
    assert adapter.reconcile(recovery.source, action) == "not_applied"
    state = adapter.dal.snapshot(recovery.source)
    assert json.loads(state["child"]["RequestJson"])["request"]["config"] != value["scan_data"]


def commit_child(r, generation, *, lost_reply=False):
    """Real writer admission and atomic receipt; no Google or persistent SQL writes."""
    producer = current_intent()
    assert producer is not None
    scope = json.loads(r.runtime.configuration)["scan_data"]
    identifier = r.runtime.dal.request(
        account="a",
        consumer="scan_data",
        kvk_no=None,
        request=dict(
            operation=producer["operation"], kind="scan_data", config=scope, producer=producer
        ),
        storage_owner="disk-a",
        actor="test",
        reason="fresh config",
    )
    claim = r.runtime.dal.claim(
        identifier,
        account="a",
        storage_owner="disk-a",
        stage="preflight",
        resource_keys=("account:a",),
    )
    claim = r.runtime.dal.transition(claim, expected="preflight", state="sql_pending", release=True)
    claim = r.runtime.dal.claim(
        identifier,
        account="a",
        storage_owner="disk-a",
        stage="writing",
        resource_keys=("sql_snapshot:legacy_outputs",),
    )
    connection = r.outcomes.connect()
    try:
        cursor = connection.cursor()
        r.runtime.dal.begin_producer_transaction(claim, cursor)
        generation = dict(generation, commit_identity=identifier)
        r.runtime.dal.transition(
            claim,
            expected="writing",
            state="committed",
            generation=generation,
            external_cursor=cursor,
        )
        connection.commit()
    finally:
        connection.close()
    if lost_reply:
        raise TimeoutError("Committed reply lost")
    return identifier


@pytest.mark.parametrize("lost_reply", [False, True])
def test_committed_retry_hands_off_exact_result_and_cannot_replay(recovery, lost_reply):
    r = recovery
    generation = json.loads(r.outcomes.inspect(r.source)["preparation"]["GenerationJson"])
    calls = []

    def runner():
        calls.append(1)
        return commit_child(r, generation, lost_reply=lost_reply)

    adapter, service = setup(r, runner)
    row = service.review_source(ACTOR, adapter.kind, r.source)
    final = run(service, row, "retry_configuration")
    assert calls == [1]
    assert service.store.actions[0]["State"] == "verified"
    assert final["State"] == "open"
    assert not final["evidence"]["actions"]
    link = final["evidence"]["recovery_links"][0]
    assert link["kind"] == "configuration_producer"
    child = adapter.dal.snapshot(r.source)["child"]
    assert child["PreparationID"] == link["source_id"]
    assert r.outcomes.inspect(child["PreparationID"])["action"] == "resume_capture"
    # The next guided action completes capture; only its verified outcome closes
    # the continuation incident. This is not a claim about downstream caches.
    result = adapter.producer.inspect(link["source_id"])
    adapter.producer.execute(
        link["source_id"],
        "resume_capture",
        result[1],
        "recovery:" + str(uuid4()),
        "Capture committed output",
    )
    result = adapter.producer.inspect(link["source_id"])
    assert set(result[0]["actions"]) == {"complete_configuration_only"}
    adapter.producer.execute(
        link["source_id"],
        "complete_configuration_only",
        result[1],
        "recovery:" + str(uuid4()),
        "Verify approved configuration-only completion",
    )
    assert (
        adapter.producer.inspect(link["source_id"])[0]["outcome"] == "configuration_only_completed"
    )
    assert service.refresh(row["IncidentID"])["State"] == "resolved"
    run(service, row, "retry_configuration")
    assert calls == [1]


@pytest.mark.asyncio
async def test_retry_button_requires_all_review_pages_and_separate_confirmation(
    recovery, monkeypatch
):
    from ui.views import recovery_review_view as review, recovery_view as view

    calls = []
    adapter, service = setup(recovery, lambda: calls.append(1))
    row = service.review_source(ACTOR, adapter.kind, recovery.source)

    async def call(method, *args):
        return getattr(service, method)(*args)

    for module in (view, review):
        monkeypatch.setattr(module, "call", call)
        monkeypatch.setattr(module, "actor_for", lambda _: ACTOR)
        monkeypatch.setattr(module, "safe_defer", AsyncMock(return_value=True))
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    await next(
        b
        for b in view.RecoveryIncidentView(row).children
        if b.label == "Read & publish current config"
    ).callback(interaction)
    assert (
        interaction.followup.send.call_args.kwargs["embed"].title
        == "Review configuration sources and outputs"
    )
    pages = 0
    while True:
        current = interaction.followup.send.call_args.kwargs["view"]
        pages += 1
        assert calls == []
        next_button = next(b for b in current.children if b.label == "Next checks")
        confirm = next(b for b in current.children if b.label == "Continue to confirmation")
        if next_button.disabled:
            assert not confirm.disabled
            await confirm.callback(interaction)
            break
        assert confirm.disabled
        await next_button.callback(interaction)
    assert pages > 1 and calls == []
    confirm_view = interaction.followup.send.call_args.kwargs["view"]
    await next(b for b in confirm_view.children if b.label.startswith("Confirm")).callback(
        interaction
    )
    assert calls == [1]
    assert service.store.actions[0]["State"] == "not_applied"


def test_held_configuration_read_routes_to_guided_recovery_before_retry(recovery):
    r = recovery
    adapter, service = setup(r)
    reader = r.runtime.dal.request(
        account="a",
        consumer="config",
        kvk_no=None,
        request={"read_configuration": str(uuid4())},
        storage_owner="disk-a",
        actor="test",
        reason="Read still owns admission",
    )
    claim = r.runtime.dal.claim(
        reader, account="a", storage_owner="disk-a", stage="preflight", resource_keys=("account:a",)
    )
    row = service.review_source(ACTOR, adapter.kind, r.source)
    assert "retry_configuration" not in row["evidence"]["actions"]
    assert row["evidence"]["recovery_links"] == [
        dict(label="Review blocking operation", kind="configuration_read", source_id=reader)
    ]
    assert r.runtime.dal.read(reader)["State"] == "preflight"
    # Simulate the reader's own verified successful completion, not timeout release.
    r.runtime.dal.transition(claim, expected="preflight", state="completed", release=True)
    refreshed = service.refresh(row["IncidentID"])
    assert "retry_configuration" in refreshed["evidence"]["actions"]


def test_live_dispatch_cannot_be_reconciled_or_duplicated(recovery):
    from services.stats_import_outcome_dal import ImportExecutionActive

    adapter, service = setup(recovery)
    row = service.review_source(ACTOR, adapter.kind, recovery.source)
    action = dict(
        ActionID=str(uuid4()),
        ActionKind="retry_configuration",
        EvidenceHash=row["EvidenceHash"],
        Reason="Confirmed",
    )
    with adapter.dal.serialized(recovery.source):
        with pytest.raises(ImportExecutionActive):
            adapter.reconcile(recovery.source, action)
    assert adapter.dal.snapshot(recovery.source)["marker"] is None
