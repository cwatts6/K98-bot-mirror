"""I1: real board and publication adapters cannot restore stale message identities."""

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import discord
import pytest

from mge import mge_embed_manager as boards, mge_publish_service as service
from mge.dal import mge_board_identity_dal as identity
from mge.mge_publish_discord_adapter import MgePublishDiscordAdapter


@pytest.mark.asyncio
async def test_invalid_render_after_settlement_returns_saved_publication(monkeypatch):
    from mge.dataset_errors import MgeDatasetError
    from tests.test_mge_publish_service import _qualified_context

    now = datetime(2026, 10, 28, tzinfo=UTC)
    event = _qualified_context(7, {})
    committed = []
    monkeypatch.setattr(
        service.mge_publish_dal, "fetch_event_publish_context", lambda *a, **k: event
    )
    monkeypatch.setattr(
        service.mge_publish_dal, "fetch_awards_with_signup_user", lambda *a, **k: []
    )

    def commit(**kwargs):
        committed.append(1)
        return 2

    monkeypatch.setattr(service.mge_publish_dal, "apply_publish_atomic", commit)
    adapter = SimpleNamespace(
        send_awards_embed=AsyncMock(side_effect=MgeDatasetError("invalid", "payload"))
    )
    result, version, _, _ = await service._publish_primary(
        adapter=adapter,
        event_id=7,
        expected=event,
        channel_id=1,
        publish_rows=[],
        waitlist_rows=[],
        clear_rank_award_ids=[],
        actor_discord_id=1,
        now=now,
    )
    assert committed == [1] and version == result.publish_version == 2
    assert not result.success and "Publication was saved" in result.message
    assert "before repeating" in result.message


@pytest.mark.asyncio
@pytest.mark.parametrize("transition", ["publish", "unpublish"])
@pytest.mark.parametrize("refresh_first", [True, False])
async def test_primary_transition_and_refresh_share_owner(monkeypatch, transition, refresh_first):
    now = datetime(2026, 10, 28, tzinfo=UTC)
    state = dict(
        EventId=7,
        EventName="Fixture",
        VariantName="Infantry",
        RuleMode="fixed",
        Status="published",
        PublishVersion=1,
        UpdatedUtc=now,
        UpdatedUtcToken="2026-10-28T00:00:00.0000001",
        AwardEmbedChannelId=1,
        AwardEmbedMessageId=10,
    )
    entered, release = asyncio.Event(), asyncio.Event()
    trace = []

    async def edit(**kwargs):
        trace.append("edit")
        if refresh_first:
            entered.set()
            await release.wait()

    class Channel(discord.abc.Messageable):
        id = 1

        async def _get_channel(self):
            return self

        async def fetch_message(self, message_id):
            return SimpleNamespace(id=message_id, edit=edit)

        async def send(self, **kwargs):
            trace.append("send")
            if not refresh_first:
                entered.set()
                await release.wait()
            return SimpleNamespace(id=20)

    channel = Channel()
    bot = SimpleNamespace(get_channel=lambda _: channel)
    adapter = MgePublishDiscordAdapter(bot)

    async def delete(**kwargs):
        trace.append("delete")
        if not refresh_first:
            entered.set()
            await release.wait()
        return SimpleNamespace(status="deleted")

    monkeypatch.setattr(adapter, "delete_message", delete)
    monkeypatch.setattr(adapter, "refresh_boards", AsyncMock())
    monkeypatch.setattr(boards, "fetch_event_publish_context", lambda *a, **k: dict(state))
    monkeypatch.setattr(
        service.mge_publish_dal, "fetch_event_publish_context", lambda *a, **k: dict(state)
    )
    monkeypatch.setattr(boards, "fetch_awards_with_signup_user", lambda *a, **k: [])
    monkeypatch.setattr(
        service.mge_publish_dal, "fetch_awards_with_signup_user", lambda *a, **k: []
    )

    def save(**kwargs):
        assert kwargs["expected"]["AwardEmbedMessageId"] == state["AwardEmbedMessageId"]
        trace.append("save")
        state.update(
            AwardEmbedMessageId=kwargs["message_id"],
            AwardEmbedChannelId=kwargs["channel_id"],
            UpdatedUtc=kwargs["now_utc"],
        )
        return True

    monkeypatch.setattr(boards, "update_award_embed_ids", save)
    monkeypatch.setattr(service.mge_publish_dal, "update_award_embed_ids", save)

    def publish(**kwargs):
        trace.append("publish")
        state.update(PublishVersion=2, Status="published", UpdatedUtc=now)
        return 2

    def unpublish(**kwargs):
        trace.append("unpublish")
        state.update(
            PublishVersion=0,
            Status="signup_closed",
            UpdatedUtc=now,
            UpdatedUtcToken="2026-10-28T00:00:00.0000001",
            AwardEmbedMessageId=None,
            AwardEmbedChannelId=None,
        )
        return dict(embed_channel_id=1, embed_message_id=10)

    monkeypatch.setattr(service.mge_publish_dal, "apply_publish_atomic", publish)
    monkeypatch.setattr(service.mge_publish_dal, "apply_unpublish_atomic", unpublish)

    async def primary():
        if transition == "unpublish":
            return await service.unpublish_event_awards(
                adapter=adapter, event_id=7, actor_discord_id=1, now_utc=now
            )

        async def operation():
            return await service._publish_primary(
                adapter=adapter,
                event_id=7,
                expected=dict(state),
                channel_id=1,
                publish_rows=[],
                waitlist_rows=[],
                clear_rank_award_ids=[],
                actor_discord_id=1,
                now=now,
            )

        return await adapter.run_primary(7, operation)

    async def refresh():
        return await boards.sync_event_awards_embed(
            bot=bot, event_id=7, existing_only=True, now_utc=now
        )

    first = asyncio.create_task(refresh() if refresh_first else primary())
    await entered.wait()
    second = asyncio.create_task(primary() if refresh_first else refresh())
    await asyncio.sleep(0)
    assert not second.done()
    if refresh_first:
        assert transition not in trace
    else:
        assert "edit" not in trace
    release.set()
    await asyncio.gather(first, second)
    assert state["AwardEmbedMessageId"] == (20 if transition == "publish" else None)
    assert trace.count(transition) == 1
    await boards.drain_refreshes()


@pytest.mark.parametrize("affected,expected", [(1, True), (0, False), (None, False)])
def test_conditional_identity_requires_exact_snapshot_and_settled_rowcount(
    monkeypatch, affected, expected
):
    now = datetime(2026, 10, 28, tzinfo=UTC)
    snapshot = dict(
        EventId=7,
        Status="published",
        RuleMode="fixed",
        PublishVersion=2,
        UpdatedUtc=now,
        UpdatedUtcToken="2026-10-28T00:00:00.0000001",
        AwardEmbedChannelId=1,
        AwardEmbedMessageId=20,
    )
    executed = []
    cur = SimpleNamespace(
        execute=lambda sql, params: executed.append((sql, params)), rowcount=affected
    )

    def execute(callback):
        if affected is None:
            return None
        return callback(cur)

    monkeypatch.setattr(identity, "exec_with_cursor", execute)
    assert (
        identity.persist_identity(
            kind="awards", event_id=7, channel_id=1, message_id=10, expected=snapshot, now_utc=now
        )
        is expected
    )
    if executed:
        sql, params = executed[0]
        assert "PublishVersion = ? AND UpdatedUtc = CONVERT(datetime2(7), ?, 126)" in sql
        assert "AwardEmbedMessageId IS NULL" in sql
        assert params[-2:] == (20, 20)
