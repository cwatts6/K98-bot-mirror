import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from stats_alerts import interface
from stats_alerts.delivery_outcomes import DeliveryAttempt, DeliveryResult, normalize_result
from stats_alerts.embeds import kvk
from stats_alerts.kvk_diagnostics import PreviewPayload


@pytest.fixture
def publication(monkeypatch):
    claims = []
    channel = SimpleNamespace(id=90, guild=SimpleNamespace(id=80))
    message = SimpleNamespace(id=100, channel=channel)
    channel.send = AsyncMock(return_value=message)
    bot = SimpleNamespace(get_channel=lambda _: channel)
    monkeypatch.setattr(interface, "is_kvk_fighting_open", lambda: True)
    monkeypatch.setattr(interface, "clear_prekvk_message", AsyncMock())
    monkeypatch.setattr(interface, "sent_today_any", lambda _: False)
    monkeypatch.setattr(interface, "read_counts_for", lambda *args: 0)
    monkeypatch.setattr(interface, "claim_send", lambda *a, **kw: claims.append((a, kw)) or True)
    monkeypatch.setattr(
        kvk, "build_kvk_preview", AsyncMock(return_value=PreviewPayload([], False, "", ""))
    )

    async def summary(*args, _delivery=None, **kwargs):
        _delivery.enter(91)
        _delivery.receipt(SimpleNamespace(id=101, channel=SimpleNamespace(id=91)))

    monkeypatch.setattr(interface, "ks_mod", summary)
    return bot, channel, claims


@pytest.mark.asyncio
@pytest.mark.parametrize("is_test", [False, True])
async def test_empty_production_payload_receipt_and_claim(publication, is_test):
    bot, channel, claims = publication
    result = await interface.send_stats_update_embed(bot, "stamp", True, is_test)
    assert [a.outcome for a in result.attempts] == ["sent", "sent"]
    item = result.attempts[-1]
    assert (item.channel_id, item.guild_id, item.message_id) == (90, 80, 100)
    assert item.data == "empty_or_unavailable"
    assert len(claims) == (0 if is_test else 1)
    assert channel.send.await_count == 1
    assert channel.send.call_args.kwargs["content"] == (None if is_test else "@everyone")


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [RuntimeError("send"), TimeoutError("send")])
async def test_unknown_never_claims_or_retries_but_next_invocation_can_publish(publication, error):
    bot, channel, claims = publication
    channel.send.side_effect = error
    result = await interface.send_stats_update_embed(bot, "stamp", True)
    assert result.attempts[0].outcome == "sent"
    assert result.attempts[-1].outcome == "unknown"
    assert not claims and channel.send.await_count == 1
    channel.send.side_effect = None
    again = await interface.send_stats_update_embed(bot, "next", True)
    assert again.attempts[-1].outcome == "sent"
    assert len(claims) == 1 and channel.send.await_count == 2


@pytest.mark.asyncio
async def test_false_claim_does_not_erase_receipt_or_repeat(publication, monkeypatch):
    bot, channel, _ = publication
    calls = []
    monkeypatch.setattr(interface, "claim_send", lambda *a, **k: calls.append(1) or False)
    result = await interface.send_stats_update_embed(bot, "stamp", True)
    assert result.attempts[-1].outcome == "sent"
    assert result.attempts[-1].claim == "not_confirmed"
    assert result.attempts[-1].message_id == 100
    assert len(calls) == channel.send.await_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("guard", ["cap", "exclusion"])
async def test_primary_skip_preserves_summary(publication, monkeypatch, guard):
    bot, channel, claims = publication
    if guard == "cap":
        monkeypatch.setattr(interface, "read_counts_for", lambda *args: 3)
    else:
        monkeypatch.setattr(interface, "sent_today_any", lambda _: True)
    result = await interface.send_stats_update_embed(bot, "stamp", True)
    assert [a.outcome for a in result.attempts] == ["sent", "skipped"]
    assert not claims and not channel.send.called


@pytest.mark.asyncio
async def test_build_error_and_missing_receipt_are_distinct(publication, monkeypatch):
    bot, channel, claims = publication
    build = kvk.build_kvk_preview
    build.side_effect = ValueError("build")
    result = await interface.send_stats_update_embed(bot, "stamp", True)
    assert result.attempts[-1].outcome == "failed"
    assert not channel.send.called and not claims
    build.side_effect = None
    channel.send.return_value = None
    result = await interface.send_stats_update_embed(bot, "stamp", True)
    assert result.attempts[-1].outcome == "unknown"
    assert result.attempts[-1].reason == "missing_receipt"
    assert not claims


@pytest.mark.asyncio
async def test_missing_destination_prevents_summary(publication):
    _, channel, claims = publication
    result = await interface.send_stats_update_embed(
        SimpleNamespace(get_channel=lambda _: None), "stamp", True
    )
    assert [a.outcome for a in result.attempts] == ["skipped", "failed"]
    assert result.attempts[-1].reason == "missing_destination"
    assert not channel.send.called and not claims


@pytest.mark.asyncio
async def test_cancellation_logs_partial_and_propagates(publication, caplog):
    bot, channel, claims = publication
    channel.send.side_effect = asyncio.CancelledError()
    with caplog.at_level("INFO"), pytest.raises(asyncio.CancelledError):
        await interface.send_stats_update_embed(bot, "stamp", True)
    assert "message=101" in caplog.text and "outcome=unknown" in caplog.text
    assert not claims and channel.send.await_count == 1


@pytest.mark.asyncio
async def test_summary_failure_does_not_suppress_primary(publication, monkeypatch):
    bot, channel, claims = publication
    monkeypatch.setattr(interface, "ks_mod", AsyncMock(side_effect=ValueError("preparation")))
    result = await interface.send_stats_update_embed(bot, "stamp", True)
    assert [a.outcome for a in result.attempts] == ["failed", "sent"]
    assert len(claims) == channel.send.await_count == 1


def test_legacy_values_cannot_fabricate_receipts():
    for value in (None, True, "sent", "edited", 123):
        item = normalize_result(value, "legacy").attempts[0]
        assert item.outcome == "unknown" and item.message_id is None
    result = DeliveryResult((DeliveryAttempt("test"),), "correlation", "test")
    assert normalize_result(result, "legacy") is result


@pytest.mark.asyncio
async def test_broken_outcome_logger_cannot_erase_receipt(publication, monkeypatch):
    import stats_alerts.delivery_outcomes as outcomes

    bot, channel, claims = publication

    def broken(*args, **kwargs):
        raise OSError("log unavailable")

    monkeypatch.setattr(outcomes.logger, "info", broken)
    result = await interface.send_stats_update_embed(bot, "stamp", True)
    assert result.attempts[-1].outcome == "sent"
    assert len(claims) == channel.send.await_count == 1
