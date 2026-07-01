from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import logging
from typing import Any

import discord

from ui.views.vote_post_view import disabled_vote_view
from voting import dal
from voting.discord_presentation import (
    build_close_embed,
    build_reminder_embed,
    build_vote_embed,
    build_vote_file,
    configured_everyone_mentions,
    mention_content,
    no_broad_mentions,
)
from voting.service import close_vote

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 60


async def _fetch_channel(bot: discord.Client, channel_id: int) -> Any | None:
    channel = bot.get_channel(int(channel_id))
    if channel is not None:
        return channel
    try:
        return await bot.fetch_channel(int(channel_id))
    except Exception:
        logger.exception("vote_channel_fetch_failed channel_id=%s", channel_id)
        return None


async def _fetch_message(channel: Any, message_id: int) -> Any | None:
    try:
        return await channel.fetch_message(int(message_id))
    except Exception:
        logger.exception(
            "vote_message_fetch_failed channel_id=%s message_id=%s",
            getattr(channel, "id", None),
            message_id,
        )
        return None


async def _refresh_vote_message(bot: discord.Client, snapshot, *, disabled: bool = False) -> None:
    if snapshot.message_id is None:
        return
    channel = await _fetch_channel(bot, snapshot.channel_id)
    if channel is None:
        return
    message = await _fetch_message(channel, snapshot.message_id)
    if message is None:
        await dal.insert_audit(
            vote_post_id=snapshot.vote_post_id,
            actor_discord_user_id=None,
            action_type="MessageEditFailed",
            details={"source": "scheduler_fetch_missing"},
        )
        return
    try:
        view = disabled_vote_view(snapshot) if disabled else None
        await message.edit(
            embed=build_vote_embed(snapshot),
            attachments=[build_vote_file(snapshot)],
            view=view,
            allowed_mentions=no_broad_mentions(),
        )
    except Exception:
        logger.exception(
            "vote_message_edit_failed vote_post_id=%s message_id=%s",
            snapshot.vote_post_id,
            snapshot.message_id,
        )
        await dal.insert_audit(
            vote_post_id=snapshot.vote_post_id,
            actor_discord_user_id=None,
            action_type="MessageEditFailed",
            details={"source": "scheduler_refresh"},
        )


async def _send_reminder(bot: discord.Client, reminder_row: dict[str, Any], now: datetime) -> None:
    vote_post_id = int(reminder_row["VotePostID"])
    reminder_id = int(reminder_row["ReminderID"])
    snapshot = await dal.get_vote_snapshot(vote_post_id)
    if snapshot is None or snapshot.status != "Open":
        return
    channel = await _fetch_channel(bot, snapshot.channel_id)
    if channel is None:
        return
    try:
        message = await channel.send(
            content=mention_content(snapshot.reminder_mention_everyone, "Vote reminder"),
            embed=build_reminder_embed(snapshot),
            allowed_mentions=configured_everyone_mentions(snapshot.reminder_mention_everyone),
        )
        await dal.mark_reminder_sent(reminder_id, message_id=int(message.id), now_utc=now)
        await dal.insert_audit(
            vote_post_id=vote_post_id,
            actor_discord_user_id=None,
            action_type="ReminderSent",
            details={"reminder_id": reminder_id, "message_id": int(message.id)},
            now_utc=now,
        )
        logger.info(
            "vote_reminder_sent vote_post_id=%s reminder_id=%s message_id=%s",
            vote_post_id,
            reminder_id,
            int(message.id),
        )
    except Exception:
        logger.exception("vote_reminder_send_failed vote_post_id=%s reminder_id=%s", vote_post_id, reminder_id)


async def _close_due_vote(bot: discord.Client, vote_post_id: int, now: datetime) -> None:
    result, snapshot = await close_vote(
        vote_post_id=vote_post_id,
        actor_discord_user_id=None,
        reason="deadline",
        now_utc=now,
    )
    if snapshot is None:
        logger.info("vote_close_due_skipped vote_post_id=%s status=%s", vote_post_id, result.status)
        return
    await _refresh_vote_message(bot, snapshot, disabled=True)
    channel = await _fetch_channel(bot, snapshot.channel_id)
    if channel is None:
        return
    try:
        await channel.send(
            content=mention_content(snapshot.close_mention_everyone, "Vote closed"),
            embed=build_close_embed(snapshot),
            allowed_mentions=configured_everyone_mentions(snapshot.close_mention_everyone),
        )
    except Exception:
        logger.exception("vote_close_announcement_failed vote_post_id=%s", vote_post_id)


async def run_voting_scheduler_tick(bot: discord.Client, *, now_utc: datetime | None = None) -> dict[str, int]:
    now = now_utc or datetime.now(UTC)
    summary = {"reminders": 0, "closes": 0}
    for reminder in await dal.claim_due_reminders(now):
        await _send_reminder(bot, reminder, now)
        summary["reminders"] += 1
    for vote_post_id in await dal.list_due_closes(now):
        await _close_due_vote(bot, vote_post_id, now)
        summary["closes"] += 1
    return summary


async def schedule_voting_lifecycle(bot: discord.Client) -> None:
    logger.info("vote_scheduler_started interval_seconds=%s", POLL_INTERVAL_SECONDS)
    try:
        while True:
            try:
                summary = await run_voting_scheduler_tick(bot)
                if summary["reminders"] or summary["closes"]:
                    logger.info(
                        "vote_scheduler_tick reminders=%s closes=%s",
                        summary["reminders"],
                        summary["closes"],
                    )
            except Exception:
                logger.exception("vote_scheduler_tick_failed")
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
    except asyncio.CancelledError:
        logger.info("vote_scheduler_cancelled")
        raise
    finally:
        logger.info("vote_scheduler_stopped")
