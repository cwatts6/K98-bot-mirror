from __future__ import annotations

from datetime import date

import pytest

import embed_offseason_stats as embed


class _Connection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return object()


class _Channel:
    def __init__(self):
        self.sent = []

    async def send(self, **kwargs):
        self.sent.append(kwargs)
        return type("Receipt", (), {"id": 123})()


@pytest.mark.asyncio
async def test_offseason_embed_renders_plain_dal_payload_without_sql(monkeypatch) -> None:
    channel = _Channel()
    payload = {
        "building": [("Builder", 100)],
        "tech": [("Researcher", 90)],
        "helps": [("Helper", 80)],
        "rss_gathered": [("Gatherer", 70)],
        "rss_assisted": [("Assistant", 60)],
        "forts": [("Rallier", 50)],
    }
    monkeypatch.setattr(embed, "get_conn_with_retries", lambda: _Connection())
    monkeypatch.setattr(embed, "load_all_daily", lambda _cursor: payload)
    monkeypatch.setattr(
        embed,
        "_pick_daily_snapshot_date",
        lambda _cursor: date(2026, 7, 28),
    )

    await embed.send_offseason_stats_embed_v2(
        bot=object(),
        channel=channel,
        include_kingdom_summary=False,
    )

    assert len(channel.sent) == 1
    sent = channel.sent[0]
    assert sent["content"] is None
    assert [item.title for item in sent["embeds"]] == [
        "🛡️ Forts (Most Recent Day)",
        "🏗️ Building • 🧪 Tech • 🤝 Helps (Most Recent Day)",
        "🌾 RSS (Most Recent Day)",
    ]


def test_embed_module_contains_no_sql_execution_helpers() -> None:
    assert not hasattr(embed, "_fetchone")
    assert not hasattr(embed, "_fetchall")


@pytest.mark.asyncio
async def test_receipt_adapter_starts_only_at_publication(monkeypatch):
    calls = []
    channel = _Channel()
    monkeypatch.setattr(embed, "get_conn_with_retries", lambda: _Connection())
    monkeypatch.setattr(embed, "load_all_daily", lambda cur: {})
    monkeypatch.setattr(embed, "_pick_daily_snapshot_date", lambda cur: date(2026, 9, 8))

    async def before_send():
        assert channel.sent == []
        calls.append("start")

    receipt = await embed.send_offseason_stats_embed_v2(
        object(),
        channel=channel,
        include_kingdom_summary=False,
        before_send=before_send,
        return_receipt=True,
    )
    assert calls == ["start"]
    assert receipt.id == 123
    assert len(channel.sent) == 1


@pytest.mark.asyncio
async def test_outcome_uses_actual_destination_and_keeps_receipt_api(monkeypatch):
    from types import SimpleNamespace

    channel = SimpleNamespace(id=90)
    actual = SimpleNamespace(id=91, guild=SimpleNamespace(id=80))

    async def send(**kwargs):
        return SimpleNamespace(id=100, channel=actual)

    channel.send = send
    monkeypatch.setattr(embed, "get_conn_with_retries", lambda: _Connection())
    monkeypatch.setattr(embed, "load_all_daily", lambda _: {})
    monkeypatch.setattr(embed, "_pick_daily_snapshot_date", lambda _: date(2026, 9, 8))
    result = await embed.send_offseason_stats_embed_v2(
        None, channel=channel, include_kingdom_summary=False, return_outcome=True
    )
    item = result.attempts[0]
    assert (item.outcome, item.channel_id, item.message_id) == ("sent", 91, 100)
    assert item.requested_channel_id == 90 and item.includes_summary is False
    with pytest.raises(ValueError):
        await embed.send_offseason_stats_embed_v2(None, return_receipt=True, return_outcome=True)
