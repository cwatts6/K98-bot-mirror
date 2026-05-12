"""Discord IO adapter for MGE publish workflows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Any

import discord

from bot_config import MGE_AWARD_CHANNEL_ID, MGE_MAIL_DM_USER_IDS
from mge.mge_embed_manager import (
    build_award_notifications_content,
    build_mge_award_reminders_embed,
    build_mge_awards_embed,
    refresh_mge_boards,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class MessageRef:
    message_id: int
    channel_id: int


@dataclass(slots=True)
class MessageIoResult:
    status: str
    message_ref: MessageRef | None = None


@dataclass(slots=True)
class AwardMailResult:
    sent: bool
    status: str


class MgePublishDiscordAdapter:
    """Boundary object for Discord message operations used by MGE publish flows."""

    def __init__(self, bot: discord.Client) -> None:
        self.bot = bot

    @property
    def default_award_channel_id(self) -> int:
        try:
            return int(MGE_AWARD_CHANNEL_ID)
        except Exception:
            return 0

    async def _resolve_messageable_channel(self, channel_id: int) -> discord.abc.Messageable | None:
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception:
                logger.exception("mge_channel_fetch_failed channel_id=%s", channel_id)
                return None
        if not hasattr(channel, "send"):
            logger.error("mge_channel_not_messageable channel_id=%s", channel_id)
            return None
        return channel

    async def send_awards_embed(
        self,
        *,
        channel_id: int,
        event_row: dict[str, Any],
        awarded_rows: list[dict[str, Any]],
        waitlist_rows: list[dict[str, Any]],
        publish_version: int,
        published_utc: datetime,
    ) -> MessageIoResult:
        channel = await self._resolve_messageable_channel(channel_id)
        if channel is None:
            return MessageIoResult("channel_unavailable")

        embed = build_mge_awards_embed(
            event_row=event_row,
            awarded_rows=awarded_rows,
            waitlist_rows=waitlist_rows,
            publish_version=publish_version,
            published_utc=published_utc,
        )
        try:
            mention_content = build_award_notifications_content(awarded_rows + waitlist_rows)
            message = await channel.send(
                content=mention_content if mention_content else None,
                embed=embed,
                allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True),
            )
        except Exception:
            logger.exception(
                "mge_publish_embed_send_failed channel_id=%s version=%s",
                channel_id,
                publish_version,
            )
            return MessageIoResult("send_failed")

        return MessageIoResult(
            "sent",
            MessageRef(message_id=int(message.id), channel_id=int(channel.id)),
        )

    async def send_republish_change_log(
        self,
        *,
        channel_id: int,
        change_lines: list[str],
    ) -> MessageIoResult:
        channel = await self._resolve_messageable_channel(channel_id)
        if channel is None:
            return MessageIoResult("channel_unavailable")
        try:
            await channel.send(
                "📌 **MGE Republish Change Log**\n"
                + "\n".join(f"- {line}" for line in change_lines[:50]),
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except Exception:
            logger.exception("mge_publish_change_log_send_failed channel_id=%s", channel_id)
            return MessageIoResult("send_failed")
        return MessageIoResult("sent")

    async def send_award_reminders_embed(
        self,
        *,
        channel_id: int,
        event_row: dict[str, Any],
        reminders_text: str,
        published_utc: datetime,
    ) -> MessageIoResult:
        channel = await self._resolve_messageable_channel(channel_id)
        if channel is None:
            return MessageIoResult("channel_unavailable")
        embed = build_mge_award_reminders_embed(
            event_row=event_row,
            reminders_text=reminders_text,
            published_utc=published_utc,
        )
        try:
            message = await channel.send(
                content="@everyone",
                embed=embed,
                allowed_mentions=discord.AllowedMentions(
                    everyone=True,
                    roles=False,
                    users=False,
                ),
            )
        except discord.Forbidden:
            logger.exception("mge_award_reminders_post_forbidden channel_id=%s", channel_id)
            return MessageIoResult("permission_failed")
        except Exception:
            logger.exception("mge_award_reminders_post_failed channel_id=%s", channel_id)
            return MessageIoResult("post_failed")
        return MessageIoResult(
            "sent",
            MessageRef(message_id=int(message.id), channel_id=int(channel.id)),
        )

    async def update_award_reminders_embed(
        self,
        *,
        channel_id: int,
        message_id: int,
        event_row: dict[str, Any],
        reminders_text: str,
        published_utc: datetime,
    ) -> MessageIoResult:
        channel = await self._resolve_messageable_channel(channel_id)
        if channel is None:
            return MessageIoResult("channel_unavailable")
        if not hasattr(channel, "fetch_message"):
            return MessageIoResult("message_fetch_unavailable")

        embed = build_mge_award_reminders_embed(
            event_row=event_row,
            reminders_text=reminders_text,
            published_utc=published_utc,
        )
        try:
            message = await channel.fetch_message(message_id)
            await message.edit(
                content="@everyone",
                embed=embed,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except discord.NotFound:
            return MessageIoResult("not_found")
        except discord.Forbidden:
            logger.exception(
                "mge_award_reminders_update_forbidden channel_id=%s message_id=%s",
                channel_id,
                message_id,
            )
            return MessageIoResult("permission_failed")
        except Exception:
            logger.exception(
                "mge_award_reminders_update_failed channel_id=%s message_id=%s",
                channel_id,
                message_id,
            )
            return MessageIoResult("edit_failed")
        return MessageIoResult(
            "updated",
            MessageRef(message_id=int(message_id), channel_id=int(channel_id)),
        )

    async def delete_message(self, *, channel_id: int, message_id: int) -> MessageIoResult:
        channel = await self._resolve_messageable_channel(channel_id)
        if channel is None:
            return MessageIoResult("channel_unavailable")
        if not hasattr(channel, "fetch_message"):
            return MessageIoResult("message_fetch_unavailable")
        try:
            message = await channel.fetch_message(message_id)
            await message.delete()
        except discord.NotFound:
            return MessageIoResult("not_found")
        except discord.Forbidden:
            return MessageIoResult("permission_failed")
        except Exception:
            logger.exception(
                "mge_message_delete_failed channel_id=%s message_id=%s",
                channel_id,
                message_id,
            )
            return MessageIoResult("delete_failed")
        return MessageIoResult("deleted")

    async def refresh_boards(
        self,
        *,
        event_id: int,
        refresh_public: bool = True,
        refresh_leadership: bool = True,
        refresh_awards: bool = False,
    ) -> dict[str, bool]:
        return await refresh_mge_boards(
            bot=self.bot,
            event_id=event_id,
            refresh_public=refresh_public,
            refresh_leadership=refresh_leadership,
            refresh_awards=refresh_awards,
        )

    async def send_award_mail(
        self,
        *,
        event_id: int,
        dm_text: str,
    ) -> AwardMailResult:
        mail_user_ids = [uid for uid in MGE_MAIL_DM_USER_IDS if uid > 0]
        if not mail_user_ids:
            logger.info(
                "mge_publish_award_dm_skipped reason=MGE_MAIL_DM_USER_IDS_not_set event_id=%s",
                event_id,
            )
            return AwardMailResult(sent=False, status="skipped_no_recipient")

        sent_count = 0
        fail_count = 0
        for mail_user_id in mail_user_ids:
            try:
                mail_user = await self.bot.fetch_user(mail_user_id)
                await mail_user.send(
                    dm_text,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
                sent_count += 1
                logger.info(
                    "mge_publish_award_dm_sent event_id=%s recipient_discord_id=%s",
                    event_id,
                    mail_user_id,
                )
            except Exception:
                fail_count += 1
                logger.exception(
                    "mge_publish_award_dm_failed event_id=%s recipient_discord_id=%s",
                    event_id,
                    mail_user_id,
                )

        if fail_count == 0:
            return AwardMailResult(sent=True, status=f"sent:{sent_count}")
        if sent_count > 0:
            return AwardMailResult(
                sent=True,
                status=f"partial:{sent_count}_ok_{fail_count}_failed",
            )
        return AwardMailResult(sent=False, status=f"all_failed:{fail_count}")
