"""Service layer for MGE target generation, publish/republish, and unpublish flow."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
import inspect
import logging
from typing import Any

import discord

from bot_config import MGE_AWARD_CHANNEL_ID, MGE_MAIL_DM_USER_ID
from mge.dal import mge_publish_dal
from mge.mge_embed_manager import (
    build_award_notifications_content,
    build_mge_award_reminders_embed,
    build_mge_awards_embed,
    build_publish_change_summary_lines,
    refresh_mge_boards,
)
from mge.mge_simplified_flow_service import evaluate_publish_readiness, get_ordered_leadership_rows

logger = logging.getLogger(__name__)

DEFAULT_TARGET_DECREMENT_SCORE = 500_000


@dataclass(slots=True)
class PublishResult:
    success: bool
    message: str
    publish_version: int | None = None
    change_lines: list[str] | None = None
    reminders_embed_sent: bool | None = None
    reminders_embed_status: str | None = None
    award_mail_dm_sent: bool | None = None
    award_mail_dm_status: str | None = None


@dataclass(slots=True)
class UnpublishResult:
    success: bool
    message: str
    embed_deleted: bool = False
    old_status: str | None = None
    restored_status: str | None = None
    old_publish_version: int | None = None


def _now_utc(now_utc: datetime | None = None) -> datetime:
    if now_utc is None:
        return datetime.now(UTC)
    if now_utc.tzinfo is None:
        return now_utc.replace(tzinfo=UTC)
    return now_utc.astimezone(UTC)


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _status(v: Any) -> str:
    return str(v or "").strip().lower()


def _target_millions_to_score(value_millions: int) -> int:
    return int(value_millions) * 1_000_000


def _maybe_await(result: Any) -> Any:
    if inspect.isawaitable(result):
        return result
    return None


def _fmt_target_millions(target_raw: Any) -> str:
    """Format a target score (raw integer) as a human-readable millions string."""
    try:
        t = int(target_raw)
        # e.g. 14_000_000 → "14.0M", 13_500_000 → "13.5M"
        return f"{t / 1_000_000:.1f}M"
    except Exception:
        return "—"


def _build_award_mail_text(
    ctx: dict[str, Any],
    awarded_rows: list[dict[str, Any]],
) -> str:
    """Build a copy-friendly in-game mail body for the MGE award list DM.

    The result is plain text (no Discord markdown) intended to be copied
    directly into an in-game mail.
    """
    event_name = str(ctx.get("EventName") or "MGE Event")
    rule_mode = str(ctx.get("RuleMode") or "fixed").strip().lower()

    lines: list[str] = ["All", "", f"This is a {rule_mode} MGE", "", "MGE List:", ""]

    sorted_rows = sorted(
        awarded_rows,
        key=lambda r: _to_int(r.get("AwardedRank") or r.get("FinalAwardedRank"), 9999),
    )
    for row in sorted_rows:
        gov = str(row.get("GovernorNameSnapshot") or "Unknown")
        target_raw = row.get("TargetScore")
        target_fmt = _fmt_target_millions(target_raw)
        lines.append(f"{gov} - Target: {target_fmt}")

    lines.append("")

    cap_millions = _to_int(ctx.get("PointCapMillions"), 0)
    if cap_millions > 0:
        lines.append(f"If you are not on the list you can NOT go over {cap_millions}m points.")
        lines.append("")

    lines.extend(
        [
            "Please see discord for full details",
            "",
            "Thank you",
            "Leadership",
        ]
    )
    return "\n".join(lines)


def _current_award_dataset(event_id: int) -> dict[str, Any]:
    return get_ordered_leadership_rows(event_id)


def _current_roster_rows_from_dataset(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in dataset.get("roster_rows", []):
        award_id = _to_int(row.get("AwardId"), 0)
        if award_id <= 0:
            continue
        rows.append(row)
    return rows


def _current_non_roster_award_ids_from_dataset(dataset: dict[str, Any]) -> list[int]:
    out: list[int] = []
    for key in ("waitlist_rows", "rejected_rows", "unassigned_rows"):
        for row in dataset.get(key, []):
            award_id = _to_int(row.get("AwardId"), 0)
            if award_id > 0:
                out.append(award_id)
    return out


def _build_publish_sets(
    event_id: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[int]]:
    dataset = _current_award_dataset(event_id)
    publish_rows: list[dict[str, Any]] = []
    waitlist_rows: list[dict[str, Any]] = []
    clear_rank_award_ids: list[int] = []

    for row in dataset.get("roster_rows", []):
        award_id = _to_int(row.get("AwardId"), 0)
        if award_id <= 0:
            continue
        publish_rows.append(
            {
                **row,
                "AwardId": award_id,
                "FinalAwardedRank": _to_int(
                    row.get("ComputedAwardedRank") or row.get("AwardedRank"), 0
                ),
            }
        )

    for row in dataset.get("waitlist_rows", []):
        award_id = _to_int(row.get("AwardId"), 0)
        if award_id <= 0:
            continue
        waitlist_rows.append(
            {
                **row,
                "AwardId": award_id,
                "FinalWaitlistOrder": _to_int(
                    row.get("ComputedWaitlistOrder") or row.get("WaitlistOrder"), 0
                ),
            }
        )
        clear_rank_award_ids.append(award_id)

    for row in dataset.get("rejected_rows", []):
        award_id = _to_int(row.get("AwardId"), 0)
        if award_id > 0:
            clear_rank_award_ids.append(award_id)

    for row in dataset.get("unassigned_rows", []):
        award_id = _to_int(row.get("AwardId"), 0)
        if award_id > 0:
            clear_rank_award_ids.append(award_id)

    return publish_rows, waitlist_rows, clear_rank_award_ids


def generate_targets_from_rank1(
    *,
    event_id: int,
    rank1_target_millions: int,
    actor_discord_id: int,
    now_utc: datetime | None = None,
) -> PublishResult:
    if rank1_target_millions <= 0:
        return PublishResult(False, "Rank 1 target must be > 0.")

    now = _now_utc(now_utc)
    dataset = _current_award_dataset(event_id)
    roster_rows = _current_roster_rows_from_dataset(dataset)
    if not roster_rows:
        return PublishResult(False, "No roster rows found for target generation.")

    rank1 = _target_millions_to_score(rank1_target_millions)
    roster_targets: dict[int, dict[str, Any]] = {}
    for row in roster_rows:
        award_id = _to_int(row.get("AwardId"), 0)
        rank = _to_int(row.get("ComputedAwardedRank") or row.get("AwardedRank"), 0)
        if award_id <= 0 or rank <= 0:
            continue
        target = max(rank1 - ((rank - 1) * DEFAULT_TARGET_DECREMENT_SCORE), 0)
        roster_targets[award_id] = {
            "target_score": target,
            "awarded_rank": rank,
        }

    if not roster_targets:
        return PublishResult(False, "No ranked roster rows found.")

    clear_award_ids = _current_non_roster_award_ids_from_dataset(dataset)
    count = mge_publish_dal.apply_generated_targets(
        event_id=event_id,
        roster_targets=roster_targets,
        clear_award_ids=clear_award_ids,
        actor_discord_id=actor_discord_id,
        now_utc=now,
    )
    if count <= 0:
        return PublishResult(False, "Failed to generate targets.")

    logger.info(
        "mge_publish_generate_targets_success event_id=%s actor_discord_id=%s roster_updated=%s cleared_non_roster=%s",
        event_id,
        actor_discord_id,
        count,
        len(clear_award_ids),
    )
    return PublishResult(True, f"Generated default targets for {count} roster rows.")


def override_target_score(
    *,
    award_id: int,
    target_score: int,
    actor_discord_id: int,
    now_utc: datetime | None = None,
) -> PublishResult:
    if target_score < 0:
        return PublishResult(False, "Target score must be >= 0.")
    award_row = mge_publish_dal.fetch_award_target_row(award_id)
    if not award_row:
        return PublishResult(False, "Award row not found.")
    if _status(award_row.get("AwardStatus")) != "awarded":
        return PublishResult(False, "Only current roster rows can have targets overridden.")
    now = _now_utc(now_utc)
    ok = mge_publish_dal.apply_manual_target_override(
        award_id=award_id,
        target_score=target_score,
        actor_discord_id=actor_discord_id,
        now_utc=now,
    )
    if not ok:
        return PublishResult(False, "Failed to update target.")
    logger.info(
        "mge_publish_override_target_success award_id=%s actor_discord_id=%s target=%s",
        award_id,
        actor_discord_id,
        target_score,
    )
    return PublishResult(True, "Target updated.")


async def publish_event_awards(
    *,
    bot: discord.Client,
    event_id: int,
    actor_discord_id: int,
    reminders_text_override: str | None = None,
    now_utc: datetime | None = None,
) -> PublishResult:
    now = _now_utc(now_utc)
    readiness = await asyncio.to_thread(evaluate_publish_readiness, event_id)
    if not readiness.get("publish_ready", False):
        logger.warning(
            "mge_publish_blocked_not_ready event_id=%s actor_discord_id=%s reasons=%s",
            event_id,
            actor_discord_id,
            readiness.get("publish_block_reason_codes", []),
        )
        return PublishResult(False, str(readiness.get("publish_status_text") or "Publish blocked."))

    ctx = await asyncio.to_thread(mge_publish_dal.fetch_event_publish_context, event_id)
    if not ctx:
        return PublishResult(False, "Event not found.")

    publish_rows, waitlist_rows, clear_rank_award_ids = await asyncio.to_thread(
        _build_publish_sets, event_id
    )
    if not publish_rows and not waitlist_rows:
        return PublishResult(False, "No awarded or waitlist rows available to publish.")

    channel_id = int(MGE_AWARD_CHANNEL_ID)
    if channel_id <= 0:
        return PublishResult(False, "MGE_AWARD_CHANNEL_ID is not configured.")

    old_version = _to_int(ctx.get("PublishVersion"), 0)
    reminders_already_sent = ctx.get("AwardRemindersSentUtc") is not None
    rule_mode = str(ctx.get("RuleMode") or "").strip().lower()
    reminders_text = str(ctx.get("AwardRemindersText") or "").strip()
    if reminders_text_override is not None:
        reminders_text = str(reminders_text_override or "").strip()
    if reminders_text and len(reminders_text) > 4000:
        return PublishResult(False, "Award reminders text is too long (max 4000 characters).")

    previous_rows = (
        await asyncio.to_thread(mge_publish_dal.fetch_published_snapshot, event_id, old_version)
        if old_version > 0
        else []
    )

    channel = bot.get_channel(channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except Exception:
            logger.exception("mge_publish_channel_fetch_failed channel_id=%s", channel_id)
            return PublishResult(False, "Award channel unavailable.")

    if not hasattr(channel, "send"):
        return PublishResult(False, "Award channel is not messageable.")

    new_version = await asyncio.to_thread(
        mge_publish_dal.apply_publish_atomic,
        event_id=event_id,
        publish_rows=publish_rows,
        waitlist_rows=waitlist_rows,
        clear_rank_award_ids=clear_rank_award_ids,
        actor_discord_id=actor_discord_id,
        now_utc=now,
    )
    if new_version is None:
        return PublishResult(False, "Failed to persist publish state.")

    posted_rows = await asyncio.to_thread(mge_publish_dal.fetch_awards_with_signup_user, event_id)
    awarded = [r for r in posted_rows if _status(r.get("AwardStatus")) == "awarded"]
    waitlist = [r for r in posted_rows if _status(r.get("AwardStatus")) == "waitlist"]

    embed = build_mge_awards_embed(
        event_row=ctx,
        awarded_rows=awarded,
        waitlist_rows=waitlist,
        publish_version=new_version,
        published_utc=now,
    )

    allowed_mentions = discord.AllowedMentions(everyone=False, roles=False, users=True)

    try:
        mention_content = build_award_notifications_content(awarded + waitlist)
        message = await channel.send(
            content=mention_content if mention_content else None,
            embed=embed,
            allowed_mentions=allowed_mentions,
        )
    except Exception:
        logger.exception(
            "mge_publish_embed_send_failed event_id=%s channel_id=%s version=%s",
            event_id,
            channel_id,
            new_version,
        )
        return PublishResult(
            False,
            "Publish persisted in DB, but posting the Discord embed failed. "
            "Please fix channel permissions and run republish.",
            publish_version=new_version,
        )

    await asyncio.to_thread(
        mge_publish_dal.update_award_embed_ids,
        event_id=event_id,
        message_id=int(message.id),
        channel_id=int(channel.id),
        now_utc=now,
    )

    latest_rows = await asyncio.to_thread(
        mge_publish_dal.fetch_published_snapshot, event_id, new_version
    )
    changes = build_publish_change_summary_lines(previous_rows, latest_rows)

    if new_version > 1 and changes:
        await channel.send(
            "📌 **MGE Republish Change Log**\n" + "\n".join(f"- {line}" for line in changes[:50]),
            allowed_mentions=discord.AllowedMentions.none(),
        )

    reminders_embed_sent = False
    reminders_embed_status = "already_sent"
    should_send_reminders = (not reminders_already_sent) and new_version >= 1
    if should_send_reminders:
        final_reminders_text = reminders_text
        if not final_reminders_text:
            final_reminders_text = (
                await asyncio.to_thread(
                    mge_publish_dal.fetch_default_award_reminders_text, rule_mode
                )
                or ""
            )
        if not final_reminders_text:
            reminders_embed_status = "missing_default"
            logger.warning(
                "mge_publish_reminders_skipped_missing_default event_id=%s actor_discord_id=%s rule_mode=%s",
                event_id,
                actor_discord_id,
                rule_mode,
            )
        else:
            reminders_text_persisted = await asyncio.to_thread(
                mge_publish_dal.update_event_award_reminders_text,
                event_id=event_id,
                reminders_text=final_reminders_text,
                now_utc=now,
            )
            if not reminders_text_persisted:
                reminders_embed_status = "persist_failed"
                logger.warning(
                    "mge_publish_reminders_persist_failed event_id=%s actor_discord_id=%s version=%s",
                    event_id,
                    actor_discord_id,
                    new_version,
                )
            else:
                reminders_embed = build_mge_award_reminders_embed(
                    event_row=ctx,
                    reminders_text=final_reminders_text,
                    published_utc=now,
                )
                try:
                    await channel.send(
                        content="@everyone",
                        embed=reminders_embed,
                        allowed_mentions=discord.AllowedMentions(
                            everyone=True,
                            roles=False,
                            users=False,
                        ),
                    )
                    reminders_embed_sent = True
                    reminders_marked_sent = await asyncio.to_thread(
                        mge_publish_dal.mark_award_reminders_sent,
                        event_id=event_id,
                        actor_discord_id=actor_discord_id,
                        now_utc=now,
                    )
                    if reminders_marked_sent:
                        reminders_embed_status = "sent"
                    else:
                        reminders_embed_status = "mark_failed"
                        logger.error(
                            "mge_publish_reminders_mark_sent_failed event_id=%s actor_discord_id=%s channel_id=%s version=%s",
                            event_id,
                            actor_discord_id,
                            channel_id,
                            new_version,
                        )
                except Exception:
                    reminders_embed_status = "send_failed"
                    logger.exception(
                        "mge_publish_reminders_send_failed event_id=%s actor_discord_id=%s channel_id=%s version=%s",
                        event_id,
                        actor_discord_id,
                        channel_id,
                        new_version,
                    )

    refresh_result = refresh_mge_boards(
        bot=bot,
        event_id=event_id,
        refresh_public=True,
        refresh_leadership=True,
        refresh_awards=True,
    )
    maybe_refresh = _maybe_await(refresh_result)
    if maybe_refresh is not None:
        await maybe_refresh

    # --- Award mail DM: send a single copy-friendly in-game mail to MGE_MAIL_DM_USER_ID ---
    award_mail_dm_sent = False
    award_mail_dm_status: str | None = None
    try:
        mail_user_id = _to_int(MGE_MAIL_DM_USER_ID, 0)
        if mail_user_id <= 0:
            award_mail_dm_status = "skipped_no_recipient"
            logger.info(
                "mge_publish_award_dm_skipped reason=MGE_MAIL_DM_USER_ID_not_set event_id=%s",
                event_id,
            )
        else:
            dm_text = _build_award_mail_text(ctx, awarded)
            try:
                mail_user = await bot.fetch_user(mail_user_id)
                await mail_user.send(dm_text)
                award_mail_dm_sent = True
                award_mail_dm_status = "sent"
                logger.info(
                    "mge_publish_award_dm_sent event_id=%s recipient_discord_id=%s",
                    event_id,
                    mail_user_id,
                )
            except Exception:
                award_mail_dm_sent = False
                award_mail_dm_status = "send_failed"
                logger.exception(
                    "mge_publish_award_dm_failed event_id=%s recipient_discord_id=%s",
                    event_id,
                    mail_user_id,
                )
    except Exception:
        award_mail_dm_sent = False
        award_mail_dm_status = "dm_error"
        logger.exception(
            "mge_publish_award_dm_error event_id=%s",
            event_id,
        )

    logger.info(
        "mge_publish_success event_id=%s actor_discord_id=%s publish_version=%s awarded=%s waitlist=%s reminders_status=%s",
        event_id,
        actor_discord_id,
        new_version,
        len(awarded),
        len(waitlist),
        reminders_embed_status,
    )
    logger.info(
        "mge_publish_award_embed_sent event_id=%s actor_discord_id=%s publish_version=%s channel_id=%s",
        event_id,
        actor_discord_id,
        new_version,
        channel_id,
    )
    if reminders_embed_status == "sent":
        logger.info(
            "mge_publish_reminders_embed_sent event_id=%s actor_discord_id=%s publish_version=%s",
            event_id,
            actor_discord_id,
            new_version,
        )
    else:
        logger.info(
            "mge_publish_reminders_embed_skipped event_id=%s actor_discord_id=%s publish_version=%s reason=%s",
            event_id,
            actor_discord_id,
            new_version,
            reminders_embed_status,
        )
    return PublishResult(
        True,
        "Published awards roster.",
        new_version,
        changes,
        reminders_embed_sent=reminders_embed_sent,
        reminders_embed_status=reminders_embed_status,
        award_mail_dm_sent=award_mail_dm_sent,
        award_mail_dm_status=award_mail_dm_status,
    )


async def unpublish_event_awards(
    *,
    bot: discord.Client,
    event_id: int,
    actor_discord_id: int,
    now_utc: datetime | None = None,
) -> UnpublishResult:
    now = _now_utc(now_utc)
    ctx = await asyncio.to_thread(mge_publish_dal.fetch_event_publish_context, event_id)
    if not ctx:
        return UnpublishResult(False, "Event not found.")

    old_status = str(ctx.get("Status") or "")
    old_publish_version = _to_int(ctx.get("PublishVersion"), 0)
    if old_publish_version <= 0 and old_status.strip().lower() not in {"published", "completed"}:
        return UnpublishResult(False, "Event is not currently published.")

    restore_status = "reopened" if old_status == "completed" else "signup_closed"

    result = await asyncio.to_thread(
        mge_publish_dal.apply_unpublish_atomic,
        event_id=event_id,
        actor_discord_id=actor_discord_id,
        now_utc=now,
        restore_status=restore_status,
    )
    if not result:
        return UnpublishResult(False, "Failed to unpublish event.")

    embed_deleted = False
    channel_id = _to_int(result.get("embed_channel_id"), 0)
    message_id = _to_int(result.get("embed_message_id"), 0)

    if channel_id > 0 and message_id > 0:
        try:
            channel = bot.get_channel(channel_id)
            if channel is None:
                channel = await bot.fetch_channel(channel_id)
            if hasattr(channel, "fetch_message"):
                message = await channel.fetch_message(message_id)
                await message.delete()
                embed_deleted = True
        except discord.NotFound:
            embed_deleted = False
        except discord.Forbidden:
            embed_deleted = False
        except Exception:
            logger.exception(
                "mge_publish_unpublish_embed_delete_failed event_id=%s channel_id=%s message_id=%s",
                event_id,
                channel_id,
                message_id,
            )

    refresh_result = refresh_mge_boards(
        bot=bot,
        event_id=event_id,
        refresh_public=True,
        refresh_leadership=True,
        refresh_awards=True,
    )
    maybe_refresh = _maybe_await(refresh_result)
    if maybe_refresh is not None:
        await maybe_refresh

    logger.info(
        "mge_publish_unpublish_success event_id=%s actor_discord_id=%s old_status=%s restore_status=%s old_publish_version=%s",
        event_id,
        actor_discord_id,
        old_status,
        restore_status,
        old_publish_version,
    )
    return UnpublishResult(
        True,
        "Event unpublished and rolled back to editable state.",
        embed_deleted=embed_deleted,
        old_status=old_status,
        restored_status=restore_status,
        old_publish_version=old_publish_version,
    )
