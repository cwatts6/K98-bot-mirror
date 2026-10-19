from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from stats_alerts.embeds import kingdom_summary as ks


@pytest.mark.asyncio
@pytest.mark.parametrize("claim", [True, False])
@pytest.mark.parametrize("send_error", [False, True])
async def test_summary_claim_precedes_send_and_receipt_is_independent(
    monkeypatch, claim, send_error
):
    order = []
    monkeypatch.setattr(ks, "sent_today", lambda _: False)
    monkeypatch.setattr(ks, "load_latest_and_prev_rows", lambda _: ({"KP": 1}, None))
    monkeypatch.setattr(ks, "claim_send", lambda *a, **k: order.append("claim") or claim)
    channel = SimpleNamespace(id=90)

    async def send(**kwargs):
        order.append("send")
        assert kwargs["content"] == ("@everyone" if claim else None)
        if send_error:
            raise TimeoutError()
        return SimpleNamespace(id=100, channel=channel)

    channel.send = send
    result = await ks.send_kingdom_summary(None, channel, "stamp", return_outcome=True)
    item = result.attempts[0]
    assert order == ["claim", "send"]
    assert item.claim == ("confirmed" if claim else "not_confirmed")
    assert item.outcome == ("unknown" if send_error else "sent")
    assert item.message_id == (None if send_error else 100)


@pytest.mark.asyncio
@pytest.mark.parametrize("posted", [False, True])
async def test_summary_skips_without_claim_or_send(monkeypatch, posted):
    monkeypatch.setattr(ks, "sent_today", lambda _: posted)
    monkeypatch.setattr(ks, "load_latest_and_prev_rows", lambda _: (None, None))
    monkeypatch.setattr(ks, "claim_send", lambda *a, **k: pytest.fail("must not claim"))
    channel = SimpleNamespace(id=90, send=AsyncMock())
    result = await ks.send_kingdom_summary(None, channel, "stamp", return_outcome=True)
    assert result.attempts[0].outcome == "skipped"
    assert result.attempts[0].reason == ("already_sent" if posted else "no_data")
    channel.send.assert_not_called()


@pytest.mark.asyncio
async def test_summary_missing_channel_not_entered_but_legacy_preclaim_preserved(monkeypatch):
    claims = []
    monkeypatch.setattr(ks, "sent_today", lambda _: False)
    monkeypatch.setattr(ks, "load_latest_and_prev_rows", lambda _: ({"KP": 1}, None))
    monkeypatch.setattr(ks, "claim_send", lambda *a, **k: claims.append(1) or True)
    result = await ks.send_kingdom_summary(None, None, "stamp", return_outcome=True)
    assert result.attempts[0].outcome == "failed" and not result.attempts[0].entered
    assert claims == [1]
