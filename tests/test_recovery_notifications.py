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
    await module.publish_recovery_alerts(bot)
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
    await module.publish_recovery_alerts(bot)
    channel.send.assert_not_called()


def test_monitor_health_is_not_healthy_before_first_check_or_after_stall(monkeypatch):
    from services import recovery_health as health

    monkeypatch.setattr(health, "_last_success", None)
    monkeypatch.setattr(health, "_failure", None)
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
        [[{"IncidentID": "failed"}], [{"IncidentID": "healthy"}], [], [{"IncidentID": "failed"}]]
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
    adapter = SimpleNamespace(dal=SimpleNamespace(pending_recovery=lambda **kwargs: []))

    @contextmanager
    def service():
        yield SimpleNamespace(store=store, adapters={"stats_import": adapter}, refresh=refresh)

    monkeypatch.setattr(module, "recovery_service", service)
    monkeypatch.setattr(module, "_cursor", None)
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
