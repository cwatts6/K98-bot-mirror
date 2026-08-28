from datetime import UTC, datetime

import pytest

from prekvk.models import (
    PreKvkScheduledSummary,
    PreKvkScheduledTopBlocks,
    PreKvkScheduledTopEntry,
)
from stats_alerts.embeds import prekvk as prekvk_embed


def _metadata():
    return {
        "kvk_no": 15,
        "kvk_name": "Test KVK",
        "registration": datetime(2026, 5, 1, tzinfo=UTC),
        "start_date": datetime(2026, 5, 10, tzinfo=UTC),
        "end_date": datetime(2026, 6, 1, tzinfo=UTC),
        "fighting_start_date": datetime(2026, 5, 20, tzinfo=UTC),
        "pass4_start_scan": 100,
    }


def _summary(previous=True):
    return PreKvkScheduledSummary(
        kvk_no=15,
        previous_kvk_no=14 if previous else None,
        current=PreKvkScheduledTopBlocks(
            overall=[
                PreKvkScheduledTopEntry("Alice", 150),
                PreKvkScheduledTopEntry("Bob", 120),
            ],
            p1=[PreKvkScheduledTopEntry("Charlie", 40)],
            p2=[PreKvkScheduledTopEntry("Delta", 30)],
            p3=[PreKvkScheduledTopEntry("Echo", 20)],
        ),
        previous=(
            PreKvkScheduledTopBlocks(
                overall=[PreKvkScheduledTopEntry("Previous Overall", 100)],
                p1=[PreKvkScheduledTopEntry("Previous P1", 10)],
                p2=[PreKvkScheduledTopEntry("Previous P2", 20)],
                p3=[PreKvkScheduledTopEntry("Previous P3", 30)],
            )
            if previous
            else PreKvkScheduledTopBlocks()
        ),
    )


class _SentMessage:
    id = 123


class _Channel:
    id = 99

    def __init__(self):
        self.sent = []
        self.fetched = []

    async def send(self, **kwargs):
        self.sent.append(kwargs)
        return _SentMessage()

    async def fetch_message(self, message_id):
        self.fetched.append(message_id)
        raise LookupError("missing")


@pytest.mark.asyncio
async def test_send_prekvk_embed_uses_scheduled_summary_service(monkeypatch):
    calls = []
    channel = _Channel()
    saved_states = []

    async def fake_summary(**kwargs):
        calls.append(kwargs)
        return _summary()

    async def fake_honor_top(_n):
        return []

    monkeypatch.setattr(prekvk_embed, "get_latest_kvk_metadata_sql", _metadata)
    monkeypatch.setattr(prekvk_embed.report_service, "build_prekvk_scheduled_summary", fake_summary)
    monkeypatch.setattr(prekvk_embed, "get_latest_honor_top", fake_honor_top)
    monkeypatch.setattr(prekvk_embed, "get_all_upcoming_events", lambda: [])
    monkeypatch.setattr(prekvk_embed, "load_state", lambda: {})
    monkeypatch.setattr(prekvk_embed, "save_state", lambda state: saved_states.append(dict(state)))

    result = await prekvk_embed.send_prekvk_embed(
        object(),
        channel,
        "2026-05-18 12:00 UTC",
        is_test=True,
    )

    assert result == "sent"
    assert calls == [
        {
            "kvk_no": 15,
            "previous_kvk_no": 14,
            "current_limit": 3,
            "previous_limit": 1,
        }
    ]
    embed = channel.sent[0]["embed"]
    values = "\n".join(field.value for field in embed.fields)
    assert "Alice" in values
    assert "Charlie" in values
    assert "Previous Overall" in values
    assert "Previous P3" in values
    assert saved_states == [{"prekvk_msg_id": 123}]


@pytest.mark.asyncio
async def test_send_prekvk_embed_edits_existing_today_message(monkeypatch):
    class ExistingMessage:
        id = 456
        created_at = prekvk_embed.utcnow()

        def __init__(self):
            self.edits = []

        async def edit(self, **kwargs):
            self.edits.append(kwargs)

    class EditChannel(_Channel):
        def __init__(self, message):
            super().__init__()
            self.message = message

        async def fetch_message(self, message_id):
            self.fetched.append(message_id)
            return self.message

    message = ExistingMessage()
    channel = EditChannel(message)

    async def fake_summary(**_kwargs):
        return _summary(previous=False)

    async def fake_honor_top(_n):
        return []

    monkeypatch.setattr(prekvk_embed, "get_latest_kvk_metadata_sql", _metadata)
    monkeypatch.setattr(
        prekvk_embed.report_service,
        "build_prekvk_scheduled_summary",
        fake_summary,
    )
    monkeypatch.setattr(prekvk_embed, "get_latest_honor_top", fake_honor_top)
    monkeypatch.setattr(prekvk_embed, "get_all_upcoming_events", lambda: [])
    monkeypatch.setattr(prekvk_embed, "load_state", lambda: {"prekvk_msg_id": 456})
    monkeypatch.setattr(prekvk_embed, "save_state", lambda _state: None)

    result = await prekvk_embed.send_prekvk_embed(
        object(),
        channel,
        "2026-05-18 12:00 UTC",
        is_test=True,
    )

    assert result == "edited"
    assert channel.fetched == [456]
    assert channel.sent == []
    assert message.edits
