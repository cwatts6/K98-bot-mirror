"""Durable asynchronous lifecycle without SQL, Discord or Google network calls."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from services.processing_notification_store import NotificationHeld, NotificationStore
from stats_alerts.processing_delivery import DurableStatsTracker


@pytest.fixture
def journal(tmp_path, monkeypatch):
    from stats_alerts import processing_notifications as service

    store = NotificationStore(tmp_path / "notifications.json")
    monkeypatch.setattr(service, "notification_store", lambda: store)
    from services import processing_notification_service as core

    monkeypatch.setattr(core, "notification_store", lambda: store)
    monkeypatch.setattr(service, "validate_runtime_scope", lambda row: None)
    return store


def new_run(store, **changes):
    run = store.create(
        str(uuid4()),
        account="a",
        storage_owner="disk",
        source_message_id=1,
        source_channel_id=5,
        summary_channel_id=10,
        sheets_channel_id=20,
    )
    return store.patch(run["run_id"], **changes) if changes else run


def channel(channel_id):
    result = SimpleNamespace(id=channel_id, guild=SimpleNamespace(id=1))
    result.message = SimpleNamespace(
        id=channel_id * 100, channel=result, author=SimpleNamespace(id=99), edit=AsyncMock()
    )
    result.send = AsyncMock(return_value=result.message)
    result.fetch_message = AsyncMock(return_value=result.message)
    return result


def client():
    channels = {10: channel(10), 20: channel(20)}
    return SimpleNamespace(user=SimpleNamespace(id=99), get_channel=channels.get), channels


@pytest.mark.asyncio
@pytest.mark.parametrize("registration", [None, OSError("journal unavailable")])
async def test_registration_failure_stops_before_prompt_or_import(monkeypatch, registration):
    import bot_config
    import processing_pipeline as pipeline
    from services import processing_notification_service as core

    monkeypatch.setattr(bot_config, "EXPORT_COORDINATION_ENABLED", True)
    register = (
        Mock(side_effect=registration)
        if isinstance(registration, Exception)
        else Mock(return_value=None)
    )
    monkeypatch.setattr(core, "register_run", register)
    monkeypatch.setattr(pipeline, "get_channel_safe", lambda *a: object())
    sender, prompt, process = AsyncMock(), AsyncMock(), AsyncMock()
    monkeypatch.setattr(pipeline, "send_embed_safe", sender)
    monkeypatch.setattr(pipeline, "prompt_admin_inputs", prompt)
    monkeypatch.setattr(pipeline, "execute_processing_pipeline", process)
    message = SimpleNamespace(id=123, channel=SimpleNamespace(id=987), author="uploader")
    with pytest.raises(RuntimeError, match="no import started"):
        await pipeline.handle_file_processing(object(), message, "fixture.xlsx", None)
    prompt.assert_not_awaited()
    process.assert_not_awaited()
    sender.assert_awaited_once()
    assert sender.call_args.args[1] == "File processing not started"
    assert "Admin action" in sender.call_args.args[2]


@pytest.mark.asyncio
@pytest.mark.parametrize("handoff_error", [False, True])
@pytest.mark.parametrize("observer_finished", [False, True])
async def test_submission_failure_handoff_and_multiple_attachment_queue_binding(
    journal, monkeypatch, handoff_error, observer_finished
):
    import bot_config
    import processing_pipeline as pipeline
    from services import (
        processing_notification_service as core,
        processing_notification_store as storage,
    )

    rows = [new_run(journal, preparation_id=str(uuid4()), stats="ready") for _ in range(2)]
    run_ids = [row["run_id"] for row in rows]
    monkeypatch.setattr(bot_config, "EXPORT_COORDINATION_ENABLED", True)
    monkeypatch.setattr(core, "register_run", Mock(side_effect=run_ids))
    if handoff_error:
        monkeypatch.setattr(
            core, "patch_run", AsyncMock(side_effect=core.NotificationTransitionFailed("disk"))
        )
    monkeypatch.setattr(storage, "notification_store", lambda: journal)
    monkeypatch.setattr(pipeline, "get_channel_safe", lambda *a: object())
    monkeypatch.setattr(pipeline, "send_embed_safe", AsyncMock())
    monkeypatch.setattr(pipeline, "prompt_admin_inputs", AsyncMock(return_value=(1, 1)))
    monkeypatch.setattr(pipeline, "load_cached_input", lambda: None)
    monkeypatch.setattr(pipeline, "log_processing_result", AsyncMock())
    monkeypatch.setattr(pipeline, "update_live_queue_embed", AsyncMock())
    monkeypatch.setattr(pipeline, "live_queue_lock", asyncio.Lock())
    queue = {
        "jobs": [
            dict(source_message_id=123, filename=name, user="uploader", status="queued")
            for name in ("first.xlsx", "second.xlsx")
        ]
    }
    monkeypatch.setattr(pipeline, "live_queue", queue)
    if observer_finished:

        async def finish_observer(*args, **kwargs):
            import time

            for run_id in run_ids:
                if journal.get(run_id).get("handoff"):
                    journal.patch(run_id, sheets="confirmed", closed=True, completed_at=time.time())

        monkeypatch.setattr(
            pipeline, "log_processing_result", AsyncMock(side_effect=finish_observer)
        )
    monkeypatch.setattr(
        pipeline,
        "execute_processing_pipeline",
        AsyncMock(
            return_value=(
                True,
                True,
                True,
                "pending" if observer_finished else False,
                True,
                "submission outcome",
            )
        ),
    )
    message = SimpleNamespace(id=123, channel=SimpleNamespace(id=987), author="uploader")
    for name in ("first.xlsx", "second.xlsx"):
        if handoff_error:
            with pytest.raises(core.NotificationTransitionFailed):
                await pipeline.handle_file_processing(object(), message, name, None)
        else:
            await pipeline.handle_file_processing(object(), message, name, None)
    assert [job["processing_run_id"] for job in queue["jobs"]] == run_ids
    if handoff_error:
        pipeline.log_processing_result.assert_not_awaited()
        assert (
            sum(
                call.args[1] == "Processing notification needs attention"
                for call in pipeline.send_embed_safe.call_args_list
            )
            == 2
        )
        assert all(not journal.get(run_id).get("handoff") for run_id in run_ids)
        return
    for run_id in run_ids:
        row = journal.get(run_id)
        assert row["sheets"] == ("confirmed" if observer_finished else "uncertain")
        assert row["handoff"] and row["stats"] == "ready"
        assert row["completed_at"] >= row["created"]
    if observer_finished:
        assert all("Sheets: confirmed" in job["status"] for job in queue["jobs"])


@pytest.mark.parametrize("terminal", ["confirmed", "failed", "cancelled"])
def test_late_uncertain_handoff_preserves_authoritative_terminal_outcome(journal, terminal):
    row = new_run(journal, sheets=terminal, completed_at=100, duration_seconds=10)
    updated = journal.patch(
        row["run_id"], handoff=True, sheets="uncertain", completed_at=200, duration_seconds=20
    )
    assert updated["sheets"] == terminal
    assert updated["completed_at"] == 100 and updated["duration_seconds"] == 10


@pytest.mark.asyncio
async def test_restart_after_pending_updates_same_summary_and_posts_sheets_once(
    journal, monkeypatch
):
    from stats_alerts import processing_notifications as service

    row = new_run(journal, handoff=True, stats="ready", stats_delivery="complete")
    bot, channels = client()
    monkeypatch.setattr(service, "update_queue", AsyncMock())
    await service.observe_notifications(bot)
    channels[10].send.assert_awaited_once()
    channels[20].send.assert_not_awaited()
    # A fresh store instance simulates process restart; only disk evidence survives.
    restored = NotificationStore(journal.path)
    monkeypatch.setattr(service, "notification_store", lambda: restored)
    restored.patch(row["run_id"], sheets="confirmed", job_id=str(uuid4()), links=[])
    await service.observe_notifications(bot)
    await service.observe_notifications(bot)
    channels[10].send.assert_awaited_once()
    channels[10].message.edit.assert_awaited_once()
    channels[20].send.assert_awaited_once()
    assert restored.get(row["run_id"])["closed"] is True
    assert channels[20].send.call_args.kwargs["allowed_mentions"].everyone is False
    assert channels[10].message.edit.call_args.kwargs["allowed_mentions"].everyone is False


@pytest.mark.asyncio
async def test_unknown_send_acknowledgment_never_repeated_after_restart(journal):
    from stats_alerts import processing_notifications as service

    row = new_run(journal, sheets="confirmed", stats="ready")
    bot, channels = client()
    channels[20].send.side_effect = TimeoutError()
    await service.publish_status(bot, row, "sheets_confirmed")
    restored = NotificationStore(journal.path).get(row["run_id"])
    assert restored["components"]["sheets_confirmed"]["state"] == "held"
    channels[20].send.side_effect = None
    await service.publish_status(bot, restored, "sheets_confirmed")
    channels[20].send.assert_awaited_once()


@pytest.mark.asyncio
async def test_missing_destination_retries_bounded_without_marking_export_failed(journal):
    from stats_alerts import processing_notifications as service

    row = new_run(journal, sheets="confirmed")
    missing = SimpleNamespace(get_channel=Mock(return_value=None))
    for _ in range(5):
        await service.publish_status(missing, journal.get(row["run_id"]), "sheets_confirmed")
    final = journal.get(row["run_id"])
    assert final["sheets"] == "confirmed"
    assert final["components"]["sheets_confirmed"]["tries"] == 3
    assert final["components"]["sheets_confirmed"]["state"] == "failed"
    assert missing.get_channel.call_count == 3


@pytest.mark.asyncio
async def test_deleted_summary_replaced_once_without_pings(journal):
    import discord

    from stats_alerts import processing_notifications as service

    row = new_run(journal)
    bot, channels = client()
    await service.publish_status(bot, row, "summary_pending")
    channels[10].fetch_message.side_effect = discord.NotFound(
        SimpleNamespace(status=404, reason="missing"), "missing"
    )
    row = journal.patch(row["run_id"], sheets="failed")
    await service.publish_status(bot, row, "summary_final_failed")
    await service.publish_status(bot, journal.get(row["run_id"]), "summary_final_failed")
    assert channels[10].send.await_count == 2
    channels[10].message.edit.assert_not_awaited()


@pytest.mark.asyncio
async def test_stats_receipts_survive_duplicate_observer_and_do_not_erase_unknown(journal):
    row = new_run(journal)
    first = DurableStatsTracker(journal, row["run_id"])
    first.begin("fighting", channel_id=10)
    await first.before_dispatch(10)
    # Cancellation occurs after Discord dispatch; no durable message acknowledgment.
    second = DurableStatsTracker(NotificationStore(journal.path), row["run_id"])
    second.begin("fighting", channel_id=10)
    with pytest.raises(NotificationHeld):
        await second.before_dispatch(10)
    await second.finish()
    assert journal.get(row["run_id"])["components"]["fighting"]["state"] == "sending"
    await first.finish()
    await second.finish()
    assert journal.get(row["run_id"])["components"]["fighting"]["state"] == "held"


@pytest.mark.asyncio
async def test_concurrent_component_claim_allows_only_one_dispatch(journal):
    row = new_run(journal)
    trackers = [DurableStatsTracker(journal, row["run_id"]) for _ in range(2)]
    for item in trackers:
        item.begin("fighting")
    results = await asyncio.gather(
        *(item.before_dispatch(10) for item in trackers), return_exceptions=True
    )
    assert sum(isinstance(result, NotificationHeld) for result in results) == 1
    assert sum(result is None for result in results) == 1


@pytest.mark.parametrize(
    "patch",
    [
        None,
        {"cache_write_status": "preserved_existing"},
        {"source_refresh_status": "last_known_good"},
        {"source_refresh_succeeded": False},
    ],
)
def test_cache_readiness_never_uses_old_snapshot(patch):
    from services.processing_notification_service import cache_generation

    output = {
        "_meta": dict(
            source="SQL:dbo.STATS_FOR_UPLOAD",
            generated_at="now",
            source_refresh_succeeded=True,
            source_refresh_status="refreshed",
            cache_write_status="written",
        )
    }
    assert cache_generation(output) == "now"
    if patch is None:
        output = None
    else:
        output["_meta"].update(patch)
    assert cache_generation(output) is None


@pytest.mark.asyncio
async def test_queue_completion_binds_exact_run_not_filename(journal, monkeypatch):
    from stats_alerts.processing_notifications import update_queue
    import utils

    row = new_run(journal, sheets="confirmed", stats="ready")
    queue = {
        "jobs": [
            dict(filename="same.xlsx", processing_run_id=str(uuid4()), status="pending"),
            dict(filename="same.xlsx", processing_run_id=row["run_id"], status="pending"),
        ]
    }
    monkeypatch.setattr(utils, "live_queue", queue)
    monkeypatch.setattr(utils, "live_queue_lock", asyncio.Lock())
    monkeypatch.setattr(utils, "update_live_queue_embed", AsyncMock())
    await update_queue(object(), row)
    assert queue["jobs"][0]["status"] == "pending"
    assert queue["jobs"][1]["status"] == "Stats: ready; Sheets: confirmed"


def test_corrupt_journal_is_retained_not_replaced(journal):
    journal.path.write_text("{broken", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        new_run(journal)
    assert journal.path.read_text() == "{broken"


def test_admin_confirmation_binds_version_and_never_resends(journal):
    row = new_run(journal)
    journal.enter(row["run_id"], "sheets", channel_id=20)
    preview = journal.get(row["run_id"])
    journal.patch(row["run_id"], handoff=True)
    with pytest.raises(NotificationHeld):
        journal.resolve(
            row["run_id"],
            action="dismiss",
            component="sheets",
            actor="local:operator",
            token=journal.token(preview),
            reason="checked channel",
        )
    current = journal.get(row["run_id"])
    journal.resolve(
        row["run_id"],
        action="dismiss",
        component="sheets",
        actor="local:operator",
        token=journal.token(current),
        reason="Manually confirmed delivered",
    )
    with pytest.raises(NotificationHeld):
        journal.enter(row["run_id"], "sheets", channel_id=20)


@pytest.mark.asyncio
async def test_later_confirmation_after_uncertainty_has_its_own_receipt(journal, monkeypatch):
    from contextlib import contextmanager

    from services import processing_notification_dal as dal
    from stats_alerts import processing_notifications as service

    row = new_run(
        journal,
        preparation_id=str(uuid4()),
        handoff=True,
        sheets="uncertain",
        stats="ready",
        stats_delivery="complete",
    )

    @contextmanager
    def runtime():
        yield object()

    from services import processing_notification_service as core

    monkeypatch.setattr(core, "caller_runtime", runtime)
    state = {"state": "uncertain", "job_id": str(uuid4()), "links": []}
    monkeypatch.setattr(dal, "read_export_outcome", lambda *_: dict(state))
    monkeypatch.setattr(service, "update_queue", AsyncMock())
    bot, channels = client()
    await service.observe_notifications(bot)
    assert not journal.get(row["run_id"]).get("closed")
    state["state"] = "confirmed"
    await service.observe_notifications(bot)
    await service.observe_notifications(bot)
    assert channels[20].send.await_count == 2
    assert channels[10].send.await_count == 1
    assert channels[10].message.edit.await_count == 1
    assert journal.get(row["run_id"])["closed"] is True


def test_late_handoff_cannot_overwrite_terminal_confirmation(journal):
    row = new_run(journal, sheets="confirmed")
    assert journal.patch(row["run_id"], handoff=True, sheets="pending")["sheets"] == "confirmed"


@pytest.mark.asyncio
async def test_wrong_runtime_does_not_publish_any_notification(journal, monkeypatch):
    from stats_alerts import processing_notifications as service

    new_run(journal, handoff=True, sheets="confirmed", stats="ready", stats_delivery="complete")
    monkeypatch.setattr(
        service, "validate_runtime_scope", Mock(side_effect=NotificationHeld("scope mismatch"))
    )
    bot, channels = client()
    await service.observe_notifications(bot)
    for item in channels.values():
        item.send.assert_not_awaited()


def test_admin_cannot_retry_unknown_send_but_can_close_notification_watch(journal):
    row = new_run(journal)
    journal.enter(row["run_id"], "sheets_confirmed", channel_id=20)
    for action in ("retry",):
        current = journal.get(row["run_id"])
        with pytest.raises(NotificationHeld):
            journal.resolve(
                row["run_id"],
                action=action,
                component="sheets_confirmed",
                token=journal.token(current),
                actor="local:operator",
                reason="inspection",
            )

    current = journal.get(row["run_id"])
    closed = journal.resolve(
        row["run_id"],
        action="close",
        token=journal.token(current),
        actor="local:operator",
        reason="Inspected interrupted run; stop notifications only",
    )
    assert closed["closed"] is True
    assert closed["sheets"] == "pending"
    assert closed["components"]["sheets_confirmed"]["state"] == "sending"


def test_analysis_links_are_not_truncated(journal):
    from stats_alerts.processing_notifications import outcome_embed

    links = ["https://docs.google.com/spreadsheets/d/" + str(i) + "a" * 80 for i in range(11)]
    row = new_run(journal, sheets="confirmed", links=links)
    embed = outcome_embed(row, sheets=True)
    fields = [f.value for f in embed.fields if f.name == "Analysis"]
    assert all(len(v) <= 1024 for v in fields)
    assert all(any(url in v for v in fields) for url in links)


def test_closed_run_cannot_claim_a_late_notification(journal):
    row = new_run(journal)
    journal.resolve(
        row["run_id"],
        action="close",
        token=journal.token(row),
        reason="Inspected interrupted run",
        actor="local:operator",
    )
    with pytest.raises(NotificationHeld, match="closed"):
        journal.enter(row["run_id"], "sheets_confirmed", channel_id=20)


def test_local_cli_preview_and_safe_resolution(journal, monkeypatch, capsys):
    from scripts import processing_notifications as command

    monkeypatch.setattr(command, "notification_store", lambda: journal)
    row = new_run(journal)
    assert command.main(["--run-id", row["run_id"], "--action", "preview"]) == 0
    token = capsys.readouterr().out.split("Confirmation token: ")[1].strip()
    assert (
        command.main(
            [
                "--run-id",
                row["run_id"],
                "--action",
                "close",
                "--confirmation",
                token,
                "--reason",
                "Inspected interrupted run",
            ]
        )
        == 0
    )
    final = journal.get(row["run_id"])
    assert final["closed"] is True
    assert final["last_admin_resolution"]["actor"].startswith("local:")


def test_unchanged_export_observation_preserves_admin_preview(journal, monkeypatch):
    from contextlib import contextmanager

    from services import processing_notification_dal as dal, processing_notification_service as core

    row = new_run(
        journal, preparation_id=str(uuid4()), job_id=str(uuid4()), links=[], additional_links=0
    )

    @contextmanager
    def runtime():
        yield object()

    monkeypatch.setattr(core, "caller_runtime", runtime)
    monkeypatch.setattr(
        dal, "read_export_outcome", lambda *_: dict(state="pending", job_id=row["job_id"], links=[])
    )
    token = journal.token(row)
    assert journal.token(core.observe_export(row)) == token
    assert journal.token(journal.get(row["run_id"])) == token


@pytest.mark.asyncio
async def test_stats_retry_reaches_failed_primary_after_acknowledged_summary(journal, monkeypatch):
    import time

    from stats_alerts import interface, processing_notifications as service

    row = new_run(
        journal,
        stats="ready",
        stats_delivery="retry_pending",
        ready_at=time.time(),
        cache_generation="same",
        is_kvk=True,
        stats_timestamp="now",
    )
    monkeypatch.setattr(service, "_current_cache_generation", lambda: "same")
    monkeypatch.setattr(interface, "is_kvk_fighting_open", lambda: True)
    monkeypatch.setattr(interface, "clear_prekvk_message", AsyncMock())
    monkeypatch.setattr(interface, "sent_today_any", lambda *a: False)
    monkeypatch.setattr(interface, "read_counts_for", lambda *a: 0)
    monkeypatch.setattr(interface, "claim_send", lambda *a, **kw: True)
    from kvk.services import new_source_recovery_service

    monkeypatch.setattr(new_source_recovery_service, "wake_recovery", lambda: None)
    destination = channel(10)
    bot = SimpleNamespace(get_channel=lambda _: destination)
    summary_sends = []
    primary_attempts = []

    async def summary(*args, _delivery, **kwargs):
        await _delivery.before_dispatch(10)
        summary_sends.append(True)
        await _delivery.after_dispatch(destination.message, destination)

    async def primary(*args, _delivery, **kwargs):
        primary_attempts.append(True)
        if len(primary_attempts) == 1:
            raise ValueError("preview failed before dispatch")
        await _delivery.before_dispatch(10)
        await _delivery.after_dispatch(destination.message, destination)

    monkeypatch.setattr(interface, "ks_mod", summary)
    monkeypatch.setattr(interface.kvk_mod, "send_kvk_embed", primary)
    await service.publish_stats(bot, row)
    assert journal.get(row["run_id"])["stats_delivery"] == "retry_pending"
    await service.publish_stats(bot, journal.get(row["run_id"]))
    final = journal.get(row["run_id"])
    assert len(summary_sends) == 1 and len(primary_attempts) == 2
    assert final["stats_delivery"] == "complete"
    assert final["components"]["kingdom_summary_daily"]["state"] == "acknowledged"
    assert final["components"]["fighting"]["state"] == "acknowledged"


@pytest.mark.asyncio
async def test_required_fact_patch_retries_transient_failure_with_same_changes(
    journal, monkeypatch
):
    from services import processing_notification_service as core

    row = new_run(journal)
    original = journal.patch
    calls = []

    def flaky(run_id, **changes):
        calls.append(dict(changes))
        if len(calls) == 1:
            raise OSError("temporarily unavailable")
        return original(run_id, **changes)

    monkeypatch.setattr(journal, "patch", flaky)
    result = await core.patch_run(row["run_id"], stats="ready", handoff=True)
    assert result["stats"] == "ready" and result["handoff"]
    assert calls == [dict(stats="ready", handoff=True)] * 2


@pytest.mark.asyncio
@pytest.mark.parametrize("error,attempts", [(OSError("disk"), 3), (NotificationHeld("invalid"), 1)])
async def test_required_fact_patch_exhaustion_propagates(journal, monkeypatch, error, attempts):
    from services import processing_notification_service as core

    row = new_run(journal)
    patch = Mock(side_effect=error)
    monkeypatch.setattr(journal, "patch", patch)
    with pytest.raises(core.NotificationTransitionFailed):
        await core.patch_run(row["run_id"], handoff=True)
    assert patch.call_count == attempts
    assert not journal.get(row["run_id"]).get("handoff")


@pytest.mark.asyncio
async def test_readiness_write_failure_does_not_replace_verified_fact(journal, monkeypatch):
    from services import processing_notification_service as core
    from stats_alerts import kvk_meta, processing_notifications as service

    row = new_run(journal)
    output = {
        "_meta": dict(
            source="SQL:dbo.STATS_FOR_UPLOAD",
            generated_at="same",
            source_refresh_status="refreshed",
            source_refresh_succeeded=True,
            cache_write_status="written",
        )
    }
    monkeypatch.setattr(kvk_meta, "is_currently_kvk", lambda: True)
    patch = Mock(side_effect=OSError("disk"))
    monkeypatch.setattr(journal, "patch", patch)
    publish = AsyncMock()
    monkeypatch.setattr(service, "publish_stats", publish)
    with pytest.raises(core.NotificationTransitionFailed):
        await service.bot_data_ready(object(), row["run_id"], output)
    assert patch.call_count == 3
    assert all(call.kwargs["stats"] == "ready" for call in patch.call_args_list)
    publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_intervention_uses_real_sender_contract(monkeypatch):
    from unittest.mock import create_autospec

    from embed_utils import send_embed_safe
    import processing_pipeline as pipeline

    sender = create_autospec(send_embed_safe)
    monkeypatch.setattr(pipeline, "send_embed_safe", sender)
    run_id = str(uuid4())
    await pipeline._notification_intervention("user", "admin channel", run_id)
    assert sender.call_args.args[2]["Processing run"] == run_id
    assert "Do not repeat" in sender.call_args.args[2]["Admin action"]
