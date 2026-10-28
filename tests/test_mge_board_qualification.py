"""Q1: real qualification boundaries, with SQL/Discord replaced at the IO edge."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import discord
import pytest

from mge import mge_board_preparation as preparation, mge_embed_manager as boards
from mge.dal import qualified_read as reader
from mge.dataset_errors import MgeDatasetError


def event():
    now = datetime.now(UTC)
    return dict(
        EventId=77,
        EventName="Fixture",
        VariantName="Infantry",
        EventMode="controlled",
        Status="signup_open",
        RuleMode="fixed",
        RulesText=None,
        PublishVersion=0,
        StartUtc=now,
        EndUtc=now + timedelta(days=7),
        SignupCloseUtc=now + timedelta(days=1),
        SignupEmbedChannelId=1,
        SignupEmbedMessageId=10,
        LeadershipEmbedChannelId=1,
        LeadershipEmbedMessageId=11,
        AwardEmbedChannelId=1,
        AwardEmbedMessageId=12,
    )


@pytest.mark.parametrize(
    "metadata,rows,valid",
    [
        (None, [], False),
        ([("Wrong",)], [], False),
        ([("EventId",)], [], True),
        ([("EventId",), ("EventId",)], [], False),
        ([("EventId",)], [(77,)], True),
        ([("EventId",)], [(77, 88)], False),
    ],
)
def test_result_set_shape_even_when_empty(monkeypatch, metadata, rows, valid):
    cur = SimpleNamespace(description=metadata, execute=Mock(), fetchall=lambda: rows, close=Mock())
    conn = SimpleNamespace(cursor=lambda: cur, close=Mock())
    monkeypatch.setattr(reader, "get_conn_with_retries", lambda: conn)
    if valid:
        assert reader.qualified_read("SELECT", (77,), columns=("EventId",), stage="fixture") == [
            dict(EventId=row[0]) for row in rows
        ]
    else:
        with pytest.raises(MgeDatasetError) as exc:
            reader.qualified_read("SELECT", (77,), columns=("EventId",), stage="fixture")
        assert exc.value.state == "incomplete"
    cur.close.assert_called_once()
    conn.close.assert_called_once()


def test_sql_failure_is_unavailable_and_redacted(monkeypatch):
    monkeypatch.setattr(reader, "get_conn_with_retries", Mock(side_effect=OSError("private token")))
    with pytest.raises(MgeDatasetError) as exc:
        reader.qualified_read("SELECT", (), columns=("EventId",), stage="event_read")
    assert exc.value.state == "unavailable" and "private" not in str(exc.value)


@pytest.mark.parametrize(
    "change",
    [
        {"EventId": 88},
        {"Status": "unknown"},
        {"SignupCloseUtc": "tomorrow"},
        {"SignupEmbedMessageId": None},
        {"PublishVersion": -1},
        {"RuleMode": None},
    ],
)
@pytest.mark.asyncio
async def test_bad_event_cannot_touch_discord_or_ids(monkeypatch, change):
    row = event() | change
    monkeypatch.setattr(boards, "fetch_event_for_embed", lambda *a, **k: row)
    bot = SimpleNamespace(get_channel=Mock(side_effect=AssertionError("Discord entered")))
    save = Mock(side_effect=AssertionError("ID write entered"))
    monkeypatch.setattr(boards, "update_event_embed_ids", save)
    assert not await boards.sync_event_signup_embed(bot=bot, event_id=77, signup_channel_id=1)
    save.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("stage", ["public_names", "view", "destination"])
async def test_dependency_failure_prevents_discord(monkeypatch, stage):
    row = event()
    monkeypatch.setattr(boards, "fetch_event_for_embed", lambda *a, **k: row)
    monkeypatch.setattr(boards, "public_names", lambda *a, **k: [])
    monkeypatch.setattr(boards, "_build_signup_view", lambda **k: object())
    if stage == "public_names":
        monkeypatch.setattr(
            boards, "public_names", Mock(side_effect=MgeDatasetError("unavailable", "review"))
        )
    elif stage == "view":
        monkeypatch.setattr(boards, "_build_signup_view", lambda **k: None)
    else:
        row["SignupEmbedChannelId"] = 2
    bot = SimpleNamespace(get_channel=Mock(side_effect=AssertionError("Discord entered")))
    assert not await boards.sync_event_signup_embed(bot=bot, event_id=77, signup_channel_id=1)
    bot.get_channel.assert_not_called()


@pytest.mark.asyncio
async def test_valid_empty_updates_original_with_controls(monkeypatch):
    row = event()
    monkeypatch.setattr(boards, "fetch_event_for_embed", lambda *a, **k: row)
    monkeypatch.setattr(boards, "public_names", lambda *a, **k: [])
    view = object()
    monkeypatch.setattr(boards, "_build_signup_view", lambda **k: view)
    save = Mock(return_value=True)
    monkeypatch.setattr(boards, "update_event_embed_ids", save)
    message = SimpleNamespace(id=10, edit=AsyncMock())

    class Channel(discord.abc.Messageable):
        id = 1

        async def _get_channel(self):
            return self

        async def fetch_message(self, identity):
            assert identity == 10
            return message

    bot = SimpleNamespace(get_channel=lambda _: Channel())
    assert await boards.sync_event_signup_embed(bot=bot, event_id=77, signup_channel_id=1)
    assert message.edit.await_args.kwargs["view"] is view
    assert not message.edit.await_args.kwargs["allowed_mentions"].everyone
    assert save.call_args.kwargs["message_id"] == 10


@pytest.mark.parametrize("kind", ["wrong_event", "duplicate", "join", "status"])
def test_ambiguous_rows_are_not_renderable(kind):
    review = [dict(EventId=77, SignupId=1, GovernorId=101)]
    awards = [dict(EventId=77, SignupId=1, GovernorId=101, AwardId=11, AwardStatus="rejected")]
    if kind == "wrong_event":
        awards[0]["EventId"] = 88
    elif kind == "duplicate":
        review.append(dict(review[0]))
    elif kind == "join":
        awards[0]["GovernorId"] = 102
    else:
        awards[0]["AwardStatus"] = "invalid"
    with pytest.raises(MgeDatasetError):
        preparation.validate_join(review, awards, 77)


def test_historical_awards_without_active_signup_are_valid():
    preparation.validate_join(
        [], [dict(EventId=77, SignupId=1, GovernorId=101, AwardId=11, AwardStatus="removed")], 77
    )
