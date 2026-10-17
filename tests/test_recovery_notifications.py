import asyncio
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import discord
import pytest

from tests.test_guided_recovery import setup


@pytest.mark.asyncio
@pytest.mark.parametrize("existing", ["known", "lost_ack", "deleted", "new"])
async def test_alert_reuses_identity_or_recreates_deleted_message(monkeypatch, existing):
    import bot_config
    from stats_alerts import recovery_notifications as module
    from ui.views.recovery_view import incident_embed

    _, _, _, row = setup()
    row.update(
        AlertMessageID=40 if existing in {"known", "deleted"} else None,
        AlertChannelID=3,
        AlertedRevision=0,
    )
    monkeypatch.setattr(bot_config, "NOTIFY_CHANNEL_ID", 3)
    monkeypatch.setattr(bot_config, "GUILD_ID", 2)
    message = SimpleNamespace(
        id=40, author=SimpleNamespace(id=99), embeds=[incident_embed(row)], edit=AsyncMock()
    )

    async def history(**kwargs):
        # Pycord 2.7 returns None for a missing footer, not an empty proxy.
        yield SimpleNamespace(
            author=SimpleNamespace(id=99), embeds=[discord.Embed(title="Ordinary status")]
        )
        if existing == "lost_ack":
            yield message

    channel = SimpleNamespace(
        id=3,
        guild=SimpleNamespace(id=2),
        fetch_message=AsyncMock(return_value=message),
        send=AsyncMock(return_value=message),
        history=history,
    )
    if existing == "deleted":
        channel.fetch_message.side_effect = discord.NotFound(
            SimpleNamespace(status=404, reason="deleted"), "deleted"
        )
    bot = SimpleNamespace(user=SimpleNamespace(id=99), get_channel=lambda _: channel)
    recorded = Mock()
    monkeypatch.setattr(module, "alert_rows", lambda: [row])
    monkeypatch.setattr(module, "claim_alert", lambda _: True)
    monkeypatch.setattr(module, "record_alert", recorded)

    async def inline(fn, *args):
        return fn(*args)

    monkeypatch.setattr(module, "drain_thread", inline)
    assert await module.publish_recovery_alerts(bot) is True
    assert channel.send.call_count == (1 if existing in {"new", "deleted"} else 0)
    recorded.assert_called_once_with(row["IncidentID"], row["Revision"], 3, 40)


@pytest.mark.asyncio
async def test_notification_lease_prevents_second_sender(monkeypatch):
    import bot_config
    from stats_alerts import recovery_notifications as module

    _, _, _, row = setup()
    monkeypatch.setattr(bot_config, "NOTIFY_CHANNEL_ID", 3)
    monkeypatch.setattr(bot_config, "GUILD_ID", 2)
    channel = SimpleNamespace(id=3, guild=SimpleNamespace(id=2), send=AsyncMock())
    bot = SimpleNamespace(get_channel=lambda _: channel)
    monkeypatch.setattr(module, "alert_rows", lambda: [row])
    monkeypatch.setattr(module, "claim_alert", lambda _: False)

    async def inline(fn, *args):
        return fn(*args)

    monkeypatch.setattr(module, "drain_thread", inline)
    assert await module.publish_recovery_alerts(bot) is False
    channel.send.assert_not_called()


def test_monitor_health_is_not_healthy_before_first_check_or_after_stall(monkeypatch):
    from services import recovery_health as health

    monkeypatch.setattr(health, "_last_success", None)
    monkeypatch.setattr(health, "_failure", None)
    monkeypatch.setattr(health, "_notification_failure", None)
    assert not health.status()[0]
    health.record_success()
    assert health.status()[0]
    health.record_failure(TimeoutError())
    assert not health.status()[0]
    health.record_success()
    health._last_success = datetime.now(UTC) - timedelta(seconds=91)
    assert not health.status()[0]


@pytest.mark.asyncio
async def test_recovery_registered_independently_and_entry_rehydrated(monkeypatch):
    import bot_config
    from core.recovery_lifecycle import register_recovery_monitor

    monkeypatch.setattr(bot_config, "EXPORT_COORDINATION_ENABLED", True)
    bot = Mock()
    monitor = Mock()
    monitor.is_running.return_value = False
    register_recovery_monitor(bot, monitor)
    assert bot.add_view.call_args.args[0].is_persistent()
    assert monitor.create.call_args.args[0] == "guided_recovery"
    monitor.is_running.return_value = True
    monitor.create.reset_mock()
    register_recovery_monitor(bot, monitor)
    monitor.create.assert_not_called()


def test_failed_check_remains_degraded_across_pages_and_empty_reset(monkeypatch):
    from services import recovery_runtime as module

    failed = set()
    pages = iter(
        [
            [{"IncidentID": "failed", "SourceKind": "stats_import"}],
            [{"IncidentID": "healthy", "SourceKind": "stats_import"}],
            [],
            [{"IncidentID": "failed", "SourceKind": "stats_import"}],
        ]
    )
    restored = False

    def refresh(key):
        if key == "failed" and not restored:
            raise TimeoutError()
        failed.discard(key)

    store = SimpleNamespace(
        scope="test",
        list_open=lambda **kwargs: next(pages),
        check_failed=lambda key, error: failed.add(key),
        has_failed_checks=lambda: bool(failed),
    )
    adapter = SimpleNamespace(pending_recovery=lambda **kwargs: [])

    @contextmanager
    def service():
        yield SimpleNamespace(
            store=store, adapters={"stats_import": adapter}, recover_automatic=refresh
        )

    monkeypatch.setattr(module, "recovery_service", service)
    monkeypatch.setattr(module, "_cursors", {})
    monkeypatch.setattr(module, "_incident_cursor", None)
    assert module.observe_recovery()
    assert module.observe_recovery()
    assert module.observe_recovery()
    restored = True
    assert module.observe_recovery() == []


@pytest.mark.asyncio
async def test_deleted_outage_alert_does_not_block_monitor_recovery(monkeypatch):
    import bot_config
    from core import recovery_lifecycle as module

    monkeypatch.setattr(bot_config, "NOTIFY_CHANNEL_ID", 3)
    monkeypatch.setattr(bot_config, "GUILD_ID", 2)
    message = SimpleNamespace(
        edit=AsyncMock(
            side_effect=discord.NotFound(SimpleNamespace(status=404, reason="deleted"), "deleted")
        )
    )
    channel = SimpleNamespace(guild=SimpleNamespace(id=2), send=AsyncMock(return_value=message))
    bot = SimpleNamespace(get_channel=lambda _: channel)
    monkeypatch.setattr(module, "drain_thread", AsyncMock(side_effect=[TimeoutError(), [], []]))
    monkeypatch.setattr(module, "publish_recovery_alerts", AsyncMock())
    healthy = Mock()
    unhealthy = Mock()
    monkeypatch.setattr(module.recovery_health, "record_success", healthy)
    monkeypatch.setattr(module.recovery_health, "record_failure", unhealthy)
    monkeypatch.setattr(
        module.asyncio, "sleep", AsyncMock(side_effect=[None, None, asyncio.CancelledError()])
    )
    with pytest.raises(asyncio.CancelledError):
        await module.observe_recovery_outcomes(bot)
    assert healthy.call_count == 2
    unhealthy.assert_called_once()
    message.edit.assert_awaited_once()


@pytest.mark.asyncio
async def test_notification_error_does_not_invalidate_incident_checks(monkeypatch):
    from core import recovery_lifecycle as module

    monkeypatch.setattr(module, "drain_thread", AsyncMock(return_value=[]))
    monkeypatch.setattr(
        module, "publish_recovery_alerts", AsyncMock(side_effect=AttributeError("private payload"))
    )
    healthy, unhealthy, notifications = Mock(), Mock(), Mock()
    monkeypatch.setattr(module.recovery_health, "record_success", healthy)
    monkeypatch.setattr(module.recovery_health, "record_failure", unhealthy)
    monkeypatch.setattr(module.recovery_health, "record_notifications", notifications)
    monkeypatch.setattr(module.asyncio, "sleep", AsyncMock(side_effect=asyncio.CancelledError()))
    with pytest.raises(asyncio.CancelledError):
        await module.observe_recovery_outcomes(Mock())
    healthy.assert_called_once()
    unhealthy.assert_not_called()
    assert isinstance(notifications.call_args.args[0], AttributeError)


def test_monitor_diagnostics_retain_callsite_without_private_exception_text(monkeypatch):
    from services import recovery_health as health

    monkeypatch.setattr(health, "_notification_failure", None)
    try:
        raise ValueError("password=secret-private-data")
    except ValueError as exc:
        health.record_notifications(exc)
    result = health.report()
    assert (
        result["notification_failure"]["frames"][-1]["function"]
        == "test_monitor_diagnostics_retain_callsite_without_private_exception_text"
    )
    assert "secret-private-data" not in str(result)
    health.record_notifications()
    assert health.report()["notification_failure"] is None


@pytest.mark.asyncio
async def test_review_entry_handles_real_embed_without_footer(monkeypatch):
    from ui.views import recovery_view as module

    monkeypatch.setattr(module, "actor_for", Mock())
    centre = AsyncMock()
    monkeypatch.setattr(module, "show_centre", centre)
    interaction = SimpleNamespace(message=SimpleNamespace(embeds=[discord.Embed(title="Status")]))
    view = module.RecoveryEntryView()
    await next(child for child in view.children if child.label == "Review & fix").callback(
        interaction
    )
    centre.assert_awaited_once_with(interaction)


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["edit", "send"])
async def test_outage_message_failure_never_blocks_due_incident_alerts(monkeypatch, failure):
    import bot_config
    from core import recovery_lifecycle as module

    monkeypatch.setattr(bot_config, "NOTIFY_CHANNEL_ID", 3)
    monkeypatch.setattr(bot_config, "GUILD_ID", 2)
    error = discord.Forbidden(SimpleNamespace(status=403, reason="Forbidden"), "denied")
    message = SimpleNamespace(edit=AsyncMock(side_effect=error))
    channel = SimpleNamespace(
        guild=SimpleNamespace(id=2),
        send=AsyncMock(side_effect=error) if failure == "send" else AsyncMock(return_value=message),
    )
    checks = [TimeoutError(), [], [], []] if failure == "edit" else [TimeoutError()] * 4
    monkeypatch.setattr(module, "drain_thread", AsyncMock(side_effect=checks))
    publish = AsyncMock()
    notifications = Mock()
    monkeypatch.setattr(module, "publish_recovery_alerts", publish)
    monkeypatch.setattr(module.recovery_health, "record_notifications", notifications)
    monkeypatch.setattr(
        module.asyncio, "sleep", AsyncMock(side_effect=[None, None, None, asyncio.CancelledError()])
    )
    with pytest.raises(asyncio.CancelledError):
        await module.observe_recovery_outcomes(SimpleNamespace(get_channel=lambda _: channel))
    assert publish.await_count == 4
    assert notifications.call_args.args[0] is error
    assert message.edit.await_count == (3 if failure == "edit" else 0)


def test_notification_degradation_preserves_successful_check_health(monkeypatch):
    from services import recovery_health as health

    monkeypatch.setattr(health, "_last_success", datetime.now(UTC))
    monkeypatch.setattr(health, "_failure", None)
    monkeypatch.setattr(health, "_failure_detail", None)
    monkeypatch.setattr(health, "_notification_failure", None)
    health.record_notifications(TimeoutError())
    healthy, text = health.status()
    assert healthy and text.startswith("Monitoring active")
    assert "notifications need attention" in text
    assert health.report()["healthy"] is True
    assert health.report()["notification_failure"]["error_type"] == "TimeoutError"


def test_health_report_uses_one_consistent_status_snapshot(monkeypatch):
    from services import recovery_health as health

    snapshot = Mock(side_effect=[(True, "Monitoring active"), (False, "Monitoring stale")])
    monkeypatch.setattr(health, "status", snapshot)
    report = health.report()
    assert (report["healthy"], report["status"]) == (True, "Monitoring active")
    snapshot.assert_called_once_with()


@pytest.mark.asyncio
async def test_delivery_failure_survives_lease_skip_until_verified_retry(monkeypatch):
    import bot_config
    from core import recovery_lifecycle as lifecycle
    from services import recovery_health as health
    from stats_alerts import recovery_notifications as notifications

    _, _, _, row = setup()
    row.update(AlertMessageID=None, AlertChannelID=3, AlertedRevision=0)
    monkeypatch.setattr(bot_config, "NOTIFY_CHANNEL_ID", 3)
    monkeypatch.setattr(bot_config, "GUILD_ID", 2)
    for name in ("_last_success", "_failure", "_failure_detail", "_notification_failure"):
        monkeypatch.setattr(health, name, None)
    message = SimpleNamespace(id=40)

    async def history(**kwargs):
        for item in []:
            yield item

    channel = SimpleNamespace(
        id=3,
        guild=SimpleNamespace(id=2),
        history=history,
        send=AsyncMock(side_effect=[TimeoutError(), message]),
    )
    bot = SimpleNamespace(user=SimpleNamespace(id=99), get_channel=lambda _: channel)
    monkeypatch.setattr(notifications, "alert_rows", lambda: [row])
    monkeypatch.setattr(notifications, "claim_alert", Mock(side_effect=[True, False, True]))
    recorded = Mock()
    monkeypatch.setattr(notifications, "record_alert", recorded)

    async def inline(fn, *args):
        return fn(*args)

    monkeypatch.setattr(notifications, "drain_thread", inline)
    monkeypatch.setattr(lifecycle, "drain_thread", AsyncMock(return_value=[]))
    snapshots = []

    async def next_cycle(_):
        snapshots.append(health.report())
        if len(snapshots) == 3:
            raise asyncio.CancelledError()

    monkeypatch.setattr(lifecycle.asyncio, "sleep", next_cycle)
    with pytest.raises(asyncio.CancelledError):
        await lifecycle.observe_recovery_outcomes(bot)
    assert all(snapshot["healthy"] for snapshot in snapshots)
    assert snapshots[0]["notification_failure"]["error_type"] == "TimeoutError"
    assert snapshots[1]["notification_failure"] == snapshots[0]["notification_failure"]
    assert snapshots[2]["notification_failure"] is None
    assert channel.send.await_count == 2
    recorded.assert_called_once_with(row["IncidentID"], row["Revision"], 3, 40)
