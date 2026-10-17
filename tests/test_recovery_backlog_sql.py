import os
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.recovery_backlog_dal import RecoveryBacklogDAL
from services.recovery_backlog_service import EvidenceBatchAdapter
from services.recovery_dal import RecoveryDAL
from tests.test_export_evidence_recovery import damage, recovery as recovery
from tests.test_recovery_sql import store as store

pytestmark = pytest.mark.skipif(
    os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Explicit local disposable SQL opt-in"
)


def evidence(store, token="a" * 64):
    return store.observe(
        "private_evidence",
        str(uuid4()),
        dict(
            title="Private recovery evidence",
            outcome="recoverable",
            explanation="Exact copy",
            copies=dict(primary="verified", replica="missing"),
            actions=dict(
                protect_evidence=dict(
                    label="Protect verified evidence",
                    check="Verify original",
                    effect="Restore exact bytes",
                )
            ),
        ),
        token,
    )


def test_group_approval_persists_every_member_and_survives_restart(store):
    first, second = evidence(store), evidence(store)
    dal = RecoveryBacklogDAL(store)
    preview = dal.preview()
    assert preview["count"] == 2
    group = dal.approve(preview, "discord:1")
    assert dal.preview()["count"] == 0
    restarted = RecoveryBacklogDAL(
        RecoveryDAL(store.connect, account="test-account", storage_owner="test-disk", guild_id=2)
    )
    assert set(restarted.pending_repairs()) == {first["IncidentID"], second["IncidentID"]}
    adapter = EvidenceBatchAdapter(store)
    assert adapter.inspect(group)[0]["pending_count"] == 2
    for row, outcome in ((first, "verified"), (second, "not_applied")):
        action = store.pending_actions(row["IncidentID"])[0]
        assert action["Actor"] == "discord:1"
        assert action["EvidenceHash"] == row["EvidenceHash"]
        store.finish(row["IncidentID"], action["ActionID"], outcome, {"verification": outcome})
    final, _, completed = adapter.inspect(group)
    assert completed and final["outcome"] == "completed_with_exceptions"
    assert final["verified_count"] == 1 and final["changed_count"] == 1


@pytest.mark.parametrize("outcome", [None, "verified", "not_applied"])
def test_group_discovery_persists_completion_without_general_backlog_cursor(
    store, monkeypatch, outcome
):
    from contextlib import contextmanager

    from services import recovery_runtime as runtime
    from services.recovery_service import RecoveryService

    row = evidence(store)
    dal = RecoveryBacklogDAL(store)
    group = dal.approve(dal.preview(), "discord:1")
    if outcome:
        action = store.pending_actions(row["IncidentID"])[0]
        store.finish(row["IncidentID"], action["ActionID"], outcome, {"verification": outcome})
    service = RecoveryService(
        store, {"evidence_batch": EvidenceBatchAdapter(store)}, admin_id=1, guild_id=2, channel_id=3
    )

    @contextmanager
    def scoped_service():
        yield service

    monkeypatch.setattr(runtime, "recovery_service", scoped_service)
    monkeypatch.setattr(runtime, "_retry_admission", lambda: True)
    monkeypatch.setattr(runtime, "_cursors", {})
    monkeypatch.setattr(runtime, "_incident_cursor", None)
    # Simulate the group being unreachable by the general backlog scan this cycle.
    monkeypatch.setattr(store, "list_open", lambda **kwargs: [])
    assert runtime.observe_recovery() == []
    current = store.get(group)
    assert current["State"] == ("resolved" if outcome else "open")
    assert (
        current["evidence"]["outcome"]
        == {None: "running", "verified": "verified", "not_applied": "completed_with_exceptions"}[
            outcome
        ]
    )
    assert dal.pending_groups() == ([] if outcome else [group])


def test_stale_group_and_duplicate_confirmation_dispatch_nothing(store):
    row = evidence(store)
    dal = RecoveryBacklogDAL(store)
    preview = dal.preview()
    store.check_failed(row["IncidentID"], "TimeoutError")
    with pytest.raises(SourceConflict, match="group changed"):
        dal.approve(preview, "discord:1")
    assert not store.pending_actions(row["IncidentID"])
    assert not dal.pending_groups()
    row = store.observe("private_evidence", row["SourceID"], row["evidence"], "b" * 64)
    preview = dal.preview()
    dal.approve(preview, "discord:1")
    with pytest.raises(SourceConflict, match="group changed"):
        dal.approve(preview, "discord:1")
    assert len(store.pending_actions(row["IncidentID"])) == 1


def test_other_scope_and_unknown_writes_are_never_grouped(store):
    evidence(store)
    store.observe("stats_import", str(uuid4()), dict(outcome="unproven", actions={}), "a" * 64)
    foreign = RecoveryDAL(store.connect, account="foreign", storage_owner="test-disk", guild_id=2)
    evidence(foreign)
    assert RecoveryBacklogDAL(store).preview()["count"] == 1
    group = RecoveryBacklogDAL(store).approve(RecoveryBacklogDAL(store).preview(), "discord:1")
    with pytest.raises(SourceConflict):
        RecoveryBacklogDAL(foreign).group_progress(group)


def test_quiet_overview_replaces_per_incident_notifications(store):
    for _ in range(30):
        evidence(store)
    assert store.alerts_due() == []
    overview = store.observe(
        "recovery_overview", str(uuid4()), dict(actions={}, outcome="attention"), "a" * 64
    )
    assert store.alerts_due() == [overview["IncidentID"]]
    store.alert_sent(overview["IncidentID"], 1, 2, 3)
    assert store.alerts_due() == []
    assert overview["IncidentID"] not in {r["IncidentID"] for r in store.list_open()}
    store.observe(
        "recovery_overview", overview["SourceID"], dict(actions={}, outcome="changed"), "b" * 64
    )
    assert store.alerts_due() == []  # Changed summaries are coalesced for five minutes.


def test_centre_header_count_is_scoped_and_preserves_priority_and_individual_pages(store):
    from services.recovery_service import RecoveryService
    from tests.test_guided_recovery import ACTOR

    evidence_row = evidence(store)
    operational = store.observe("stats_import", str(uuid4()), dict(actions={}), "a" * 64)
    store.observe("stats_import", str(uuid4()), dict(actions={}), "a" * 64, resolved=True)
    store.observe("recovery_overview", str(uuid4()), dict(actions={}), "a" * 64)
    foreign = RecoveryDAL(store.connect, account="foreign", storage_owner="test-disk", guild_id=2)
    evidence(foreign)
    service = RecoveryService(store, {}, admin_id=1, guild_id=2, channel_id=3)
    priority = service.centre_page(ACTOR)
    assert priority["open_count"] == 2
    assert [row["IncidentID"] for row in priority["rows"]] == [operational["IncidentID"]]
    individual = service.centre_page(ACTOR, individual=True)
    assert individual["open_count"] == 2
    assert {row["IncidentID"] for row in individual["rows"]} == {
        evidence_row["IncidentID"],
        operational["IncidentID"],
    }


@pytest.mark.asyncio
async def test_unchanged_open_overview_checks_delivery_and_recreates_deleted_card(
    store, monkeypatch
):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    import discord

    import bot_config
    from stats_alerts import recovery_notifications as module

    overview = store.observe(
        "recovery_overview",
        str(uuid4()),
        dict(
            title="Recovery overview",
            explanation="Review recovery",
            actions={},
            outcome="attention",
        ),
        "a" * 64,
    )
    incident_id = overview["IncidentID"]
    store.alert_sent(incident_id, overview["Revision"], 3, 40)
    message = SimpleNamespace(id=40, edit=AsyncMock())

    async def history(**kwargs):
        for item in ():
            yield item

    channel = SimpleNamespace(
        id=3,
        guild=SimpleNamespace(id=2),
        fetch_message=AsyncMock(return_value=message),
        send=AsyncMock(return_value=SimpleNamespace(id=41)),
        history=history,
    )
    bot = SimpleNamespace(user=SimpleNamespace(id=99), get_channel=lambda _: channel)
    monkeypatch.setattr(bot_config, "NOTIFY_CHANNEL_ID", 3)
    monkeypatch.setattr(bot_config, "GUILD_ID", 2)
    monkeypatch.setattr(module, "alert_rows", lambda: [store.get(i) for i in store.alerts_due()])
    monkeypatch.setattr(module, "claim_alert", store.claim_alert)
    monkeypatch.setattr(module, "record_alert", store.alert_sent)

    async def inline(fn, *args):
        return fn(*args)

    monkeypatch.setattr(module, "drain_thread", inline)

    def elapse_interval():
        connection = store.connect()
        try:
            connection.cursor().execute(
                "UPDATE dbo.RecoveryIncident SET AlertCheckedUTC=DATEADD(minute,-6,SYSUTCDATETIME()) "
                "WHERE IncidentID=?",
                incident_id,
            )
            connection.commit()
        finally:
            connection.close()

    # No unrelated incident change is needed to check the delivered revision.
    assert store.alerts_due() == []
    elapse_interval()
    assert store.alerts_due() == [incident_id]
    assert await module.publish_recovery_alerts(bot)
    channel.fetch_message.assert_awaited_once_with(40)
    message.edit.assert_not_awaited()
    channel.send.assert_not_awaited()
    assert store.alerts_due() == []

    elapse_interval()
    channel.fetch_message.side_effect = discord.NotFound(
        SimpleNamespace(status=404, reason="deleted"), "deleted"
    )
    assert await module.publish_recovery_alerts(bot)
    channel.send.assert_awaited_once()
    assert store.get(incident_id)["AlertMessageID"] == 41
    assert store.alerts_due() == []

    # Resolved overviews receive their final update, then stop periodic delivery checks.
    resolved = store.observe(
        "recovery_overview",
        overview["SourceID"],
        dict(actions={}, outcome="clear"),
        "b" * 64,
        resolved=True,
    )
    elapse_interval()
    assert store.alerts_due() == [incident_id]
    store.alert_sent(incident_id, resolved["Revision"], 3, 41)
    elapse_interval()
    assert store.alerts_due() == []


def test_group_reconciles_exact_private_copy_after_restart(store, recovery):
    from services.recovery_service import RecoveryService
    from tests.test_guided_recovery import ACTOR

    r = recovery
    damage(r)
    service = RecoveryService(
        store, {"private_evidence": r.adapter}, admin_id=1, guild_id=2, channel_id=3
    )
    row = service.review_source(ACTOR, "private_evidence", r.reference)
    dal = RecoveryBacklogDAL(store)
    group = dal.approve(dal.preview(), "discord:1")
    # No filesystem write occurs until the restarted service reconciles the
    # individually persisted approval through the real protected-copy adapter.
    assert not (r.tmp_path / r.receipt.key).exists()
    restarted = RecoveryService(
        store, {"private_evidence": r.adapter}, admin_id=1, guild_id=2, channel_id=3
    )
    result = restarted.refresh(row["IncidentID"])
    assert result["State"] == "resolved" and not result["pending_action"]
    assert r.private.read(r.receipt) == r.raw
    final, _, complete = EvidenceBatchAdapter(store).inspect(group)
    assert complete and final["verified_count"] == 1
