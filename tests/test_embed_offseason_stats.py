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
