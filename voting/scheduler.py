from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import logging
from typing import Any

import discord

from ui.views.survey_post_view import disabled_survey_view
from ui.views.vote_post_view import disabled_vote_view
from voting import dal, survey_dal
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
from voting.survey_presentation import (
    build_survey_close_embed,
    build_survey_embed,
    build_survey_file,
    build_survey_reminder_embed,
)
from voting.survey_service import close_survey

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
            attachments=[],
            files=[build_vote_file(snapshot)],
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


async def _send_reminder(bot: discord.Client, reminder_row: dict[str, Any], now: datetime) -> bool:
    vote_post_id = int(reminder_row["VotePostID"])
    reminder_id = int(reminder_row["ReminderID"])
    snapshot = await dal.get_vote_snapshot(vote_post_id)
    if snapshot is None or snapshot.status != "Open" or snapshot.closes_at_utc <= now:
        return False
    channel = await _fetch_channel(bot, snapshot.channel_id)
    if channel is None:
        return False
    try:
        message = await channel.send(
            content=mention_content(snapshot.reminder_mention_everyone, "Vote reminder"),
            embed=build_reminder_embed(snapshot),
            allowed_mentions=configured_everyone_mentions(snapshot.reminder_mention_everyone),
        )
        marked = await dal.mark_reminder_sent(reminder_id, message_id=int(message.id), now_utc=now)
        if not marked:
            await dal.insert_audit(
                vote_post_id=vote_post_id,
                actor_discord_user_id=None,
                action_type="ReminderMarkFailed",
                details={"reminder_id": reminder_id, "message_id": int(message.id)},
                now_utc=now,
            )
            logger.warning(
                "vote_reminder_mark_failed vote_post_id=%s reminder_id=%s message_id=%s",
                vote_post_id,
                reminder_id,
                int(message.id),
            )
            return False
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
        return True
    except Exception:
        logger.exception(
            "vote_reminder_send_failed vote_post_id=%s reminder_id=%s", vote_post_id, reminder_id
        )
        return False


async def _refresh_survey_message(bot: discord.Client, snapshot, *, disabled: bool = False) -> None:
    if snapshot.message_id is None:
        return
    channel = await _fetch_channel(bot, snapshot.channel_id)
    if channel is None:
        return
    message = await _fetch_message(channel, snapshot.message_id)
    if message is None:
        await survey_dal.insert_audit(
            survey_id=snapshot.survey_id,
            actor_discord_user_id=None,
            action_type="MessageEditFailed",
            details={"source": "scheduler_fetch_missing"},
        )
        return
    try:
        view = disabled_survey_view(snapshot) if disabled else None
        await message.edit(
            embed=build_survey_embed(snapshot),
            attachments=[],
            files=[build_survey_file(snapshot)],
            view=view,
            allowed_mentions=no_broad_mentions(),
        )
    except Exception:
        logger.exception(
            "survey_message_edit_failed survey_id=%s message_id=%s",
            snapshot.survey_id,
            snapshot.message_id,
        )
        await survey_dal.insert_audit(
            survey_id=snapshot.survey_id,
            actor_discord_user_id=None,
            action_type="MessageEditFailed",
            details={"source": "scheduler_refresh"},
        )


async def _send_survey_reminder(
    bot: discord.Client, reminder_row: dict[str, Any], now: datetime
) -> bool:
    survey_id = int(reminder_row["SurveyID"])
    reminder_id = int(reminder_row["ReminderID"])
    snapshot = await survey_dal.get_survey_snapshot(survey_id)
    if snapshot is None or snapshot.status != "Open" or snapshot.closes_at_utc <= now:
        return False
    channel = await _fetch_channel(bot, snapshot.channel_id)
    if channel is None:
        return False
    try:
        message = await channel.send(
            content=mention_content(snapshot.reminder_mention_everyone, "Survey reminder"),
            embed=build_survey_reminder_embed(snapshot),
            allowed_mentions=configured_everyone_mentions(snapshot.reminder_mention_everyone),
        )
        marked = await survey_dal.mark_reminder_sent(
            reminder_id, message_id=int(message.id), now_utc=now
        )
        if not marked:
            logger.warning(
                "survey_reminder_mark_failed survey_id=%s reminder_id=%s message_id=%s",
                survey_id,
                reminder_id,
                int(message.id),
            )
            await survey_dal.insert_audit(
                survey_id=survey_id,
                actor_discord_user_id=None,
                action_type="ReminderMarkFailed",
                details={"reminder_id": reminder_id, "message_id": int(message.id)},
                now_utc=now,
            )
            return False
        await survey_dal.insert_audit(
            survey_id=survey_id,
            actor_discord_user_id=None,
            action_type="ReminderSent",
            details={"reminder_id": reminder_id, "message_id": int(message.id)},
            now_utc=now,
        )
        logger.info(
            "survey_reminder_sent survey_id=%s reminder_id=%s message_id=%s",
            survey_id,
            reminder_id,
            int(message.id),
        )
        return True
    except Exception:
        logger.exception(
            "survey_reminder_send_failed survey_id=%s reminder_id=%s", survey_id, reminder_id
        )
        return False


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


async def _close_due_survey(bot: discord.Client, survey_id: int, now: datetime) -> None:
    result, snapshot = await close_survey(
        survey_id=survey_id,
        actor_discord_user_id=None,
        reason="deadline",
        now_utc=now,
    )
    if snapshot is None:
        logger.info("survey_close_due_skipped survey_id=%s status=%s", survey_id, result.status)
        return
    await _refresh_survey_message(bot, snapshot, disabled=True)
    channel = await _fetch_channel(bot, snapshot.channel_id)
    if channel is None:
        return
    try:
        await channel.send(
            content=mention_content(snapshot.close_mention_everyone, "Survey closed"),
            embed=build_survey_close_embed(snapshot),
            allowed_mentions=configured_everyone_mentions(snapshot.close_mention_everyone),
        )
    except Exception:
        logger.exception("survey_close_announcement_failed survey_id=%s", survey_id)


async def run_voting_scheduler_tick(
    bot: discord.Client, *, now_utc: datetime | None = None
) -> dict[str, int]:
    now = now_utc or datetime.now(UTC)
    summary = {"reminders": 0, "closes": 0, "survey_reminders": 0, "survey_closes": 0}
    for vote_post_id in await dal.list_due_closes(now):
        await _close_due_vote(bot, vote_post_id, now)
        summary["closes"] += 1
    for survey_id in await survey_dal.list_due_closes(now):
        await _close_due_survey(bot, survey_id, now)
        summary["survey_closes"] += 1
    for reminder in await dal.claim_due_reminders(now):
        if await _send_reminder(bot, reminder, now):
            summary["reminders"] += 1
    for reminder in await survey_dal.claim_due_reminders(now):
        if await _send_survey_reminder(bot, reminder, now):
            summary["survey_reminders"] += 1
    return summary


async def schedule_voting_lifecycle(bot: discord.Client) -> None:
    logger.info("vote_scheduler_started interval_seconds=%s", POLL_INTERVAL_SECONDS)
    try:
        while True:
            try:
                summary = await run_voting_scheduler_tick(bot)
                if (
                    summary["reminders"]
                    or summary["closes"]
                    or summary["survey_reminders"]
                    or summary["survey_closes"]
                ):
                    logger.info(
                        "vote_scheduler_tick reminders=%s closes=%s survey_reminders=%s survey_closes=%s",
                        summary["reminders"],
                        summary["closes"],
                        summary["survey_reminders"],
                        summary["survey_closes"],
                    )
            except Exception:
                logger.exception("vote_scheduler_tick_failed")
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
    except asyncio.CancelledError:
        logger.info("vote_scheduler_cancelled")
        raise
    finally:
        logger.info("vote_scheduler_stopped")
