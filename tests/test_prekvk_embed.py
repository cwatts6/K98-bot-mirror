from datetime import UTC, datetime

import pytest

from core.discord_embed_limits import require_valid_embed_payload
from prekvk.models import (
    PreKvkScheduledSummary,
    PreKvkScheduledTopBlocks,
    PreKvkScheduledTopEntry,
)
from stats_alerts import dispatch_reservations, guard, state
from stats_alerts.embeds import prekvk as prekvk_embed


@pytest.fixture(autouse=True)
def isolated_dispatch(monkeypatch, tmp_path):
    monkeypatch.setattr(guard, "LOG_PATH", str(tmp_path / "alerts.csv"))
    monkeypatch.setattr(state, "STATE_PATH", str(tmp_path / "state.json"))
    monkeypatch.setattr(state, "_STATE_LOCK_PATH", str(tmp_path / "state.lck"))


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


def _kvk16_launch_events():
    rows = [
        ("2026-08-26 00:00", "Preparation phase"),
        ("2026-08-28 00:00", "Pre-KVK Starts!"),
        ("2026-08-28 00:00", "KVK Map opens!"),
        ("2026-08-28 00:00", "Marauders"),
        ("2026-08-28 00:00", "Four Kings Enter..."),
        ("2026-08-28 03:00", "Karuak"),
        ("2026-08-28 03:00", "Finding a Foothold"),
        ("2026-08-28 15:00", "Crusader Camp"),
        ("2026-08-30 00:00", "Marauders' Forts"),
        ("2026-08-30 03:00", "Megingjörð (Artifact)"),
        ("2026-08-30 03:00", "Shoring Up"),
        ("2026-08-30 15:00", "Crusader Fortress"),
    ]
    return [
        {
            "name": name,
            "type": "chronicle" if index % 2 == 0 else "major",
            "start_time": datetime.strptime(start, "%Y-%m-%d %H:%M").replace(tzinfo=UTC),
        }
        for index, (start, name) in enumerate(rows)
    ]


def _legacy_event_value(events):
    def event_line(event):
        timestamp = int(event["start_time"].timestamp())
        return (
            f"• **{event['name']}** — starts <t:{timestamp}:R>\n"
            f"  {prekvk_embed.format_event_time(event['start_time'])}"
        )

    return "\n".join(event_line(event) for event in events[:12])


def _patch_builder_dependencies(monkeypatch, *, events=None):
    async def fake_summary(**_kwargs):
        return _summary()

    async def fake_honor_top(_n):
        return []

    monkeypatch.setattr(prekvk_embed, "get_latest_kvk_metadata_sql", _metadata)
    monkeypatch.setattr(
        prekvk_embed.report_service,
        "build_prekvk_scheduled_summary",
        fake_summary,
    )
    monkeypatch.setattr(prekvk_embed, "get_latest_honor_top", fake_honor_top)
    monkeypatch.setattr(prekvk_embed, "get_all_upcoming_events", lambda: list(events or []))


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
    monkeypatch.setattr(
        prekvk_embed,
        "update_prekvk_message",
        lambda mid: saved_states.append({"prekvk_msg_id": mid}),
    )

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
    fixed_now = datetime(2026, 8, 25, 12, 0, tzinfo=UTC)

    class ExistingMessage:
        id = 456
        created_at = fixed_now

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
    monkeypatch.setattr(prekvk_embed, "get_all_upcoming_events", _kvk16_launch_events)
    monkeypatch.setattr(prekvk_embed, "utcnow", lambda: fixed_now)
    monkeypatch.setattr(prekvk_embed, "load_state", lambda: {"prekvk_msg_id": 456})
    monkeypatch.setattr(prekvk_embed, "update_prekvk_message", lambda _mid: None)
    monkeypatch.setattr(
        prekvk_embed,
        "DispatchAttempt",
        lambda *_args, **_kwargs: pytest.fail("edit path must not reserve a fresh send"),
    )

    result = await prekvk_embed.send_prekvk_embed(
        object(),
        channel,
        "2026-05-18 12:00 UTC",
        is_test=False,
    )

    assert result == "edited"
    assert channel.fetched == [456]
    assert channel.sent == []
    assert message.edits
    edited_embed = message.edits[0]["embed"]
    require_valid_embed_payload(edited_embed)
    upcoming = [field for field in edited_embed.fields if field.name.startswith("🗓️ Next 7 days")]
    assert [len(field.value) for field in upcoming] == [941, 87]


@pytest.mark.asyncio
async def test_exact_kvk16_event_payload_chunks_complete_blocks(monkeypatch):
    events = _kvk16_launch_events()
    assert len(_legacy_event_value(events)) == 1029
    source_events = [
        *events,
        {
            "name": "Thirteenth event stays view-only",
            "type": "major",
            "start_time": datetime(2026, 9, 1, 0, 0, tzinfo=UTC),
        },
    ]

    fixed_now = datetime(2026, 8, 25, 12, 0, tzinfo=UTC)
    channel = _Channel()
    _patch_builder_dependencies(monkeypatch, events=source_events)
    monkeypatch.setattr(prekvk_embed, "utcnow", lambda: fixed_now)
    monkeypatch.setattr(prekvk_embed, "load_state", lambda: {})
    monkeypatch.setattr(prekvk_embed, "update_prekvk_message", lambda _mid: None)

    result = await prekvk_embed.send_prekvk_embed(
        object(), channel, "2026-08-25 12:00 UTC", is_test=True
    )

    assert result == "sent"
    payload = channel.sent[0]
    embed = payload["embed"]
    usage = require_valid_embed_payload(embed)
    upcoming = [field for field in embed.fields if field.name.startswith("🗓️ Next 7 days")]
    assert [field.name for field in upcoming] == [
        "🗓️ Next 7 days:",
        "🗓️ Next 7 days (continued):",
    ]
    assert [len(field.value) for field in upcoming] == [941, 87]
    assert usage.field_counts[0] <= 25
    assert usage.total_characters <= 6000
    assert all(len(field.name) <= 256 and len(field.value) <= 1024 for field in embed.fields)

    rendered = "\n".join(field.value for field in upcoming)
    positions = [rendered.index(event["name"]) for event in events]
    assert positions == sorted(positions)
    for event in events:
        assert f"<t:{int(event['start_time'].timestamp())}:R>" in rendered
    assert source_events[-1]["name"] not in rendered
    assert len(payload["view"].events) == 13


def test_pathological_single_event_compacts_only_name_and_keeps_tokens():
    event = {
        "name": "A" * 2000,
        "type": "major",
        "start_time": datetime(2026, 8, 30, 15, 0, tzinfo=UTC),
    }

    fields, omitted, compacted = prekvk_embed._build_upcoming_event_fields(
        [event], available_fields=1, available_characters=2000
    )

    assert omitted == 0
    assert compacted == 1
    assert len(fields) == 1
    value = fields[0][1]
    assert len(value) == 1024
    assert value.count("**") == 2
    assert f"…** — starts <t:{int(event['start_time'].timestamp())}:R>" in value
    assert prekvk_embed.format_event_time(event["start_time"]) in value


def test_event_block_exact_boundary_and_one_over_preserve_complete_suffix():
    start = datetime(2026, 8, 30, 15, 0, tzinfo=UTC)
    suffix = (
        f"** — starts <t:{int(start.timestamp())}:R>\n  {prekvk_embed.format_event_time(start)}"
    )
    exact_name = "A" * (1024 - len("• **") - len(suffix))

    exact, exact_compacted = prekvk_embed._format_event_block(
        {"name": exact_name, "start_time": start}
    )
    over, over_compacted = prekvk_embed._format_event_block(
        {"name": f"{exact_name}A", "start_time": start}
    )

    assert len(exact) == 1024
    assert exact_name in exact
    assert exact_compacted is False
    assert len(over) == 1024
    assert over_compacted is True
    assert over.count("**") == 2
    assert over.endswith(suffix)


def test_event_budget_exhaustion_uses_truthful_marker():
    events = _kvk16_launch_events()[:2]
    first_block, _ = prekvk_embed._format_event_block(events[0])
    marker = "… 1 more event — see Timeline"
    budget = len("🗓️ Next 7 days:") + len(first_block) + 1 + len(marker)

    fields, omitted, _compacted = prekvk_embed._build_upcoming_event_fields(
        events,
        available_fields=1,
        available_characters=budget,
    )

    assert omitted == 1
    assert len(fields) == 1
    assert fields[0][1].endswith(marker)
    assert events[0]["name"] in fields[0][1]
    assert events[1]["name"] not in fields[0][1]


@pytest.mark.asyncio
async def test_fresh_production_send_commits_once(monkeypatch):
    _patch_builder_dependencies(monkeypatch)
    channel = _Channel()
    result = await prekvk_embed.send_prekvk_embed(object(), channel, "audit", is_test=False)
    assert result == "sent"
    assert guard.sent_today("prekvk_daily")
    assert len(list(guard.iter_log_rows())) == 1
    assert state.load_state() == {"prekvk_msg_id": 123}
    assert channel.sent[0]["content"] == "@everyone"
    assert channel.sent[0]["allowed_mentions"].everyone is True


@pytest.mark.asyncio
async def test_send_failure_does_not_persist_or_claim(monkeypatch):
    class FailingChannel(_Channel):
        async def send(self, **_kwargs):
            raise RuntimeError("transport failed")

    _patch_builder_dependencies(monkeypatch)
    with pytest.raises(RuntimeError, match="transport failed"):
        await prekvk_embed.send_prekvk_embed(object(), FailingChannel(), "audit", is_test=False)
    assert state.load_state() == {}
    assert list(guard.iter_log_rows()) == []
    row = next(iter(dispatch_reservations.ReservationStore()._read()["attempts"].values()))
    assert row["phase"] == "uncertain"


@pytest.mark.asyncio
async def test_daily_guard_skip_does_not_send_or_claim(monkeypatch):
    _patch_builder_dependencies(monkeypatch)
    assert guard.claim_send("prekvk_daily")
    channel = _Channel()
    with pytest.raises(prekvk_embed.PreKvkSkip):
        await prekvk_embed.send_prekvk_embed(object(), channel, "audit", is_test=False)
    assert channel.sent == []
    assert len(list(guard.iter_log_rows())) == 1


@pytest.mark.asyncio
async def test_two_real_builders_have_one_fresh_send(monkeypatch):
    import asyncio

    _patch_builder_dependencies(monkeypatch)
    entered = asyncio.Event()
    finish = asyncio.Event()

    class WaitingChannel(_Channel):
        async def send(self, **kwargs):
            self.sent.append(kwargs)
            entered.set()
            await finish.wait()
            return _SentMessage()

    channel = WaitingChannel()
    first = asyncio.create_task(prekvk_embed.send_prekvk_embed(object(), channel, "first"))
    await asyncio.wait_for(entered.wait(), 3)
    try:
        with pytest.raises(prekvk_embed.PreKvkSkip):
            await prekvk_embed.send_prekvk_embed(object(), channel, "second")
    finally:
        finish.set()
        assert await first == "sent"
    assert len(channel.sent) == 1
    assert len(list(guard.iter_log_rows())) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["missing", "yesterday", "edit"])
@pytest.mark.parametrize("claimed", [False, True])
async def test_existing_reference_fallback_keeps_daily_guard(monkeypatch, failure, claimed):
    from datetime import timedelta

    _patch_builder_dependencies(monkeypatch)
    state.update_prekvk_message(456)
    if claimed:
        guard.claim_send("prekvk_daily")

    class Message:
        id = 456
        created_at = prekvk_embed.utcnow() - (
            timedelta(days=1) if failure == "yesterday" else timedelta()
        )

        async def edit(self, **kwargs):
            raise RuntimeError("edit failure")

    class Channel(_Channel):
        async def fetch_message(self, mid):
            if failure == "missing":
                raise LookupError("missing")
            return Message()

    channel = Channel()
    if claimed:
        with pytest.raises(prekvk_embed.PreKvkSkip):
            await prekvk_embed.send_prekvk_embed(object(), channel, "audit")
        assert channel.sent == []
    else:
        assert await prekvk_embed.send_prekvk_embed(object(), channel, "audit") == "sent"
        assert channel.sent[0]["content"] == "@everyone"
        assert state.load_state()["prekvk_msg_id"] == 123
