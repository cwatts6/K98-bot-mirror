"""Service layer for MGE target generation, publish/republish, and unpublish flow."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
import inspect
import logging
from typing import Any, Protocol

from mge.dal import mge_publish_dal
from mge.mge_constants import DEFAULT_TARGET_DECREMENT_SCORE
from mge.mge_embed_manager import build_publish_change_summary_lines
from mge.mge_simplified_flow_service import evaluate_publish_readiness, get_ordered_leadership_rows

logger = logging.getLogger(__name__)

# Retained only so older tests or downstream monkeypatches fail softly after
# Discord IO moved behind MgePublishIoAdapter.
MGE_AWARD_CHANNEL_ID: str | int = 0
MGE_MAIL_DM_USER_IDS: list[int] = []


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


@dataclass(slots=True)
class RefreshAwardRemindersResult:
    success: bool
    message: str
    event_id: int | None = None
    status: str | None = None
    updated_existing: bool = False
    reposted_missing: bool = False
    skipped_no_awards: bool = False


class _MessageRef(Protocol):
    message_id: int
    channel_id: int


class _MessageIoResult(Protocol):
    status: str
    message_ref: _MessageRef | None


class _AwardMailResult(Protocol):
    sent: bool
    status: str


class MgePublishIoAdapter(Protocol):
    @property
    def default_award_channel_id(self) -> int: ...

    async def send_awards_embed(
        self,
        *,
        channel_id: int,
        event_row: dict[str, Any],
        awarded_rows: list[dict[str, Any]],
        waitlist_rows: list[dict[str, Any]],
        publish_version: int,
        published_utc: datetime,
    ) -> _MessageIoResult: ...

    async def send_republish_change_log(
        self,
        *,
        channel_id: int,
        change_lines: list[str],
    ) -> _MessageIoResult: ...

    async def send_award_reminders_embed(
        self,
        *,
        channel_id: int,
        event_row: dict[str, Any],
        reminders_text: str,
        published_utc: datetime,
    ) -> _MessageIoResult: ...

    async def update_award_reminders_embed(
        self,
        *,
        channel_id: int,
        message_id: int,
        event_row: dict[str, Any],
        reminders_text: str,
        published_utc: datetime,
    ) -> _MessageIoResult: ...

    async def delete_message(self, *, channel_id: int, message_id: int) -> _MessageIoResult: ...

    async def check_award_channel_available(self, channel_id: int) -> bool: ...

    async def refresh_boards(
        self,
        *,
        event_id: int,
        refresh_public: bool = True,
        refresh_leadership: bool = True,
        refresh_awards: bool = False,
    ) -> dict[str, bool]: ...

    async def send_award_mail(
        self,
        *,
        event_id: int,
        dm_text: str,
    ) -> _AwardMailResult: ...


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


def _target_millions_to_score(value_millions: float) -> int:
    return round(float(value_millions) * 1_000_000)


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


def _plain_text_safe(value: Any) -> str:
    """Sanitize text for plain-text DM output."""
    text = str(value or "").strip()
    text = text.replace("<", "‹").replace(">", "›")
    text = text.replace("*", "＊").replace("_", "＿")
    text = text.replace("`", "｀").replace("~", "～")
    text = text.replace("|", "｜")
    return text


def _build_award_mail_text(
    ctx: dict[str, Any],
    awarded_rows: list[dict[str, Any]],
) -> str:
    """Build a copy-friendly in-game mail body for the MGE award list DM.

    The result is plain text (no Discord markdown) intended to be copied
    directly into an in-game mail.
    """
    rule_mode = str(ctx.get("RuleMode") or "fixed").strip().lower()

    lines: list[str] = ["All", "", f"This is a {rule_mode} MGE", "", "MGE List:", ""]

    sorted_rows = sorted(
        awarded_rows,
        key=lambda r: _to_int(r.get("AwardedRank") or r.get("FinalAwardedRank"), 9999),
    )
    for row in sorted_rows:
        gov = _plain_text_safe(row.get("GovernorNameSnapshot") or "Unknown")
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
    rank1_target_millions: int | float,
    actor_discord_id: int,
    now_utc: datetime | None = None,
) -> PublishResult:
    try:
        rank1_fval = float(rank1_target_millions)
    except Exception:
        return PublishResult(False, "Invalid rank 1 target.")
    if rank1_fval <= 0 or rank1_fval % 0.5 != 0:
        return PublishResult(
            False,
            "Rank 1 target must be a positive whole number or .5 value (e.g. 13 or 13.5).",
        )

    now = _now_utc(now_utc)
    dataset = _current_award_dataset(event_id)
    roster_rows = _current_roster_rows_from_dataset(dataset)
    if not roster_rows:
        return PublishResult(False, "No roster rows found for target generation.")

    rank1 = _target_millions_to_score(rank1_fval)
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
    adapter: MgePublishIoAdapter,
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

    channel_id = int(adapter.default_award_channel_id)
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

    if not await adapter.check_award_channel_available(channel_id):
        return PublishResult(False, "Award channel unavailable.")

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

    awards_send = await adapter.send_awards_embed(
        channel_id=channel_id,
        event_row=ctx,
        awarded_rows=awarded,
        waitlist_rows=waitlist,
        publish_version=new_version,
        published_utc=now,
    )
    if awards_send.status == "channel_unavailable":
        return PublishResult(False, "Award channel unavailable.", publish_version=new_version)
    if awards_send.status != "sent" or awards_send.message_ref is None:
        return PublishResult(
            False,
            "Publish persisted in DB, but posting the Discord embed failed. "
            "Please fix channel permissions and run republish.",
            publish_version=new_version,
        )

    await asyncio.to_thread(
        mge_publish_dal.update_award_embed_ids,
        event_id=event_id,
        message_id=int(awards_send.message_ref.message_id),
        channel_id=int(awards_send.message_ref.channel_id),
        now_utc=now,
    )

    latest_rows = await asyncio.to_thread(
        mge_publish_dal.fetch_published_snapshot, event_id, new_version
    )
    changes = build_publish_change_summary_lines(previous_rows, latest_rows)

    if new_version > 1 and changes:
        await adapter.send_republish_change_log(
            channel_id=channel_id,
            change_lines=changes,
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
                reminder_send = await adapter.send_award_reminders_embed(
                    channel_id=channel_id,
                    event_row=ctx,
                    reminders_text=final_reminders_text,
                    published_utc=now,
                )
                if reminder_send.status == "sent" and reminder_send.message_ref is not None:
                    reminders_embed_sent = True
                    reminder_ids_updated = await asyncio.to_thread(
                        mge_publish_dal.update_award_reminder_message_ids,
                        event_id=event_id,
                        message_id=int(reminder_send.message_ref.message_id),
                        channel_id=int(reminder_send.message_ref.channel_id),
                        now_utc=now,
                    )
                    reminders_marked_sent = await asyncio.to_thread(
                        mge_publish_dal.mark_award_reminders_sent,
                        event_id=event_id,
                        actor_discord_id=actor_discord_id,
                        now_utc=now,
                    )
                    if not reminder_ids_updated and not reminders_marked_sent:
                        reminders_embed_status = "ids_persist_and_mark_failed"
                        logger.warning(
                            "mge_publish_reminders_id_and_mark_failed event_id=%s actor_discord_id=%s channel_id=%s version=%s",
                            event_id,
                            actor_discord_id,
                            channel_id,
                            new_version,
                        )
                    elif not reminder_ids_updated:
                        reminders_embed_status = "ids_persist_failed"
                        logger.warning(
                            "mge_publish_reminders_id_persist_failed event_id=%s actor_discord_id=%s channel_id=%s version=%s",
                            event_id,
                            actor_discord_id,
                            channel_id,
                            new_version,
                        )
                    elif reminders_marked_sent:
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
                else:
                    reminders_embed_status = reminder_send.status or "send_failed"
                    logger.warning(
                        "mge_publish_reminders_send_failed event_id=%s actor_discord_id=%s channel_id=%s version=%s",
                        event_id,
                        actor_discord_id,
                        channel_id,
                        new_version,
                    )

    refresh_result = adapter.refresh_boards(
        event_id=event_id,
        refresh_public=True,
        refresh_leadership=True,
        refresh_awards=True,
    )
    maybe_refresh = _maybe_await(refresh_result)
    if maybe_refresh is not None:
        await maybe_refresh

    award_mail_dm_sent = False
    award_mail_dm_status: str | None = None
    try:
        dm_text = _build_award_mail_text(ctx, awarded)
        dm_result = await adapter.send_award_mail(event_id=event_id, dm_text=dm_text)
        award_mail_dm_sent = bool(dm_result.sent)
        award_mail_dm_status = str(dm_result.status)
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


async def refresh_award_reminders(
    *,
    adapter: MgePublishIoAdapter,
    event_id: int | None,
    actor_discord_id: int,
    allow_completed: bool = False,
    now_utc: datetime | None = None,
) -> RefreshAwardRemindersResult:
    """Refresh the persisted award-reminders post without reallocating awards."""
    now = _now_utc(now_utc)
    resolved_event_id = int(event_id or 0)
    if resolved_event_id <= 0:
        resolved = await asyncio.to_thread(
            mge_publish_dal.fetch_refreshable_award_reminder_event_id
        )
        if not resolved:
            return RefreshAwardRemindersResult(
                False,
                "No active or upcoming MGE event was found.",
                status="no_event",
            )
        resolved_event_id = int(resolved)

    ctx = await asyncio.to_thread(mge_publish_dal.fetch_event_publish_context, resolved_event_id)
    if not ctx:
        return RefreshAwardRemindersResult(
            False,
            "Event not found.",
            event_id=resolved_event_id,
            status="event_not_found",
        )

    status = str(ctx.get("Status") or "").strip().lower()
    if status == "completed" and not allow_completed:
        return RefreshAwardRemindersResult(
            False,
            "Completed MGE events require an explicit admin-selected event id.",
            event_id=resolved_event_id,
            status="completed_not_allowed",
        )

    if _to_int(ctx.get("PublishVersion"), 0) <= 0:
        logger.info(
            "mge_refresh_award_reminders_skipped_no_awards event_id=%s actor_discord_id=%s",
            resolved_event_id,
            actor_discord_id,
        )
        return RefreshAwardRemindersResult(
            False,
            "Awards have not been published for this event.",
            event_id=resolved_event_id,
            status="no_awards_published",
            skipped_no_awards=True,
        )

    channel_id = _to_int(ctx.get("AwardRemindersChannelId"), 0)
    if channel_id <= 0:
        channel_id = _to_int(ctx.get("AwardEmbedChannelId"), 0)
    if channel_id <= 0:
        channel_id = int(adapter.default_award_channel_id)
    if channel_id <= 0:
        return RefreshAwardRemindersResult(
            False,
            "MGE award channel is not configured.",
            event_id=resolved_event_id,
            status="missing_channel",
        )

    rule_mode = str(ctx.get("RuleMode") or "").strip().lower()
    latest_default = await asyncio.to_thread(
        mge_publish_dal.fetch_default_award_reminders_text, rule_mode
    )
    persisted_reminders_text = str(ctx.get("AwardRemindersText") or "").strip()
    reminders_text = persisted_reminders_text or str(latest_default or "").strip()
    should_persist_reminders_text = reminders_text != persisted_reminders_text
    if not reminders_text:
        return RefreshAwardRemindersResult(
            False,
            "No award reminder text is configured for this event/rule mode.",
            event_id=resolved_event_id,
            status="missing_text",
        )
    if len(reminders_text) > 4000:
        return RefreshAwardRemindersResult(
            False,
            "Award reminders text is too long (max 4000 characters).",
            event_id=resolved_event_id,
            status="text_too_long",
        )

    async def _persist_reminders_text_if_needed(
        *,
        failure_message: str,
        failure_status: str,
        updated_existing: bool = False,
        reposted_missing: bool = False,
    ) -> RefreshAwardRemindersResult | None:
        if not should_persist_reminders_text:
            return None
        updated = await asyncio.to_thread(
            mge_publish_dal.update_event_award_reminders_text,
            event_id=resolved_event_id,
            reminders_text=reminders_text,
            now_utc=now,
        )
        if updated:
            return None
        return RefreshAwardRemindersResult(
            False,
            failure_message,
            event_id=resolved_event_id,
            status=failure_status,
            updated_existing=updated_existing,
            reposted_missing=reposted_missing,
        )

    old_message_id = _to_int(ctx.get("AwardRemindersMessageId"), 0)

    if old_message_id > 0:
        update_result = await adapter.update_award_reminders_embed(
            channel_id=channel_id,
            message_id=old_message_id,
            event_row=ctx,
            reminders_text=reminders_text,
            published_utc=now,
        )
        if update_result.status == "updated":
            logger.info(
                "mge_refresh_award_reminders_updated event_id=%s actor_discord_id=%s message_id=%s channel_id=%s",
                resolved_event_id,
                actor_discord_id,
                old_message_id,
                channel_id,
            )
            text_persist_failure = await _persist_reminders_text_if_needed(
                failure_message="Award reminders were updated in Discord, but persisting reminder text failed.",
                failure_status="updated_persist_text_failed",
                updated_existing=True,
            )
            if text_persist_failure is not None:
                return text_persist_failure
            return RefreshAwardRemindersResult(
                True,
                "Award reminders updated.",
                event_id=resolved_event_id,
                status="updated",
                updated_existing=True,
            )
        if update_result.status in {"not_found", "message_fetch_unavailable"}:
            logger.info(
                "mge_refresh_award_reminders_missing_message event_id=%s message_id=%s",
                resolved_event_id,
                old_message_id,
            )
        elif update_result.status == "permission_failed":
            return RefreshAwardRemindersResult(
                False,
                "Missing permission to update the existing award reminders message.",
                event_id=resolved_event_id,
                status="permission_failed",
            )
        elif update_result.status == "channel_unavailable":
            return RefreshAwardRemindersResult(
                False,
                "Award reminders channel is unavailable or not messageable.",
                event_id=resolved_event_id,
                status="channel_unavailable",
            )
        elif update_result.status == "edit_failed":
            return RefreshAwardRemindersResult(
                False,
                "Failed to update the existing award reminders message.",
                event_id=resolved_event_id,
                status="edit_failed",
            )

    post_result = await adapter.send_award_reminders_embed(
        channel_id=channel_id,
        event_row=ctx,
        reminders_text=reminders_text,
        published_utc=now,
    )
    if post_result.status == "permission_failed":
        return RefreshAwardRemindersResult(
            False,
            "Missing permission to post award reminders.",
            event_id=resolved_event_id,
            status="permission_failed",
        )
    if post_result.status == "channel_unavailable":
        return RefreshAwardRemindersResult(
            False,
            "Award reminders channel is unavailable or not messageable.",
            event_id=resolved_event_id,
            status="channel_unavailable",
        )
    if post_result.status != "sent" or post_result.message_ref is None:
        return RefreshAwardRemindersResult(
            False,
            "Failed to post award reminders.",
            event_id=resolved_event_id,
            status="post_failed",
        )

    text_persist_failure = await _persist_reminders_text_if_needed(
        failure_message="Award reminders reposted in Discord, but persisting reminder text failed.",
        failure_status="reposted_persist_text_failed",
        reposted_missing=True,
    )
    if text_persist_failure is not None:
        return text_persist_failure

    message_ids_updated = await asyncio.to_thread(
        mge_publish_dal.update_award_reminder_message_ids,
        event_id=resolved_event_id,
        message_id=int(post_result.message_ref.message_id),
        channel_id=int(post_result.message_ref.channel_id),
        now_utc=now,
    )
    reminders_marked_sent = await asyncio.to_thread(
        mge_publish_dal.mark_award_reminders_sent,
        event_id=resolved_event_id,
        actor_discord_id=actor_discord_id,
        now_utc=now,
    )
    if not message_ids_updated and not reminders_marked_sent:
        logger.warning(
            "mge_refresh_award_reminders_reposted_persist_and_mark_failed event_id=%s actor_discord_id=%s message_id=%s channel_id=%s",
            resolved_event_id,
            actor_discord_id,
            int(post_result.message_ref.message_id),
            int(post_result.message_ref.channel_id),
        )
        return RefreshAwardRemindersResult(
            False,
            "Award reminders reposted, but failed to save reminder message details and mark reminders sent.",
            event_id=resolved_event_id,
            status="reposted_persist_and_mark_failed",
            reposted_missing=True,
        )
    if not message_ids_updated:
        logger.warning(
            "mge_refresh_award_reminders_reposted_persist_failed event_id=%s actor_discord_id=%s message_id=%s channel_id=%s",
            resolved_event_id,
            actor_discord_id,
            int(post_result.message_ref.message_id),
            int(post_result.message_ref.channel_id),
        )
        return RefreshAwardRemindersResult(
            False,
            "Award reminders reposted, but failed to save reminder message details.",
            event_id=resolved_event_id,
            status="reposted_persist_failed",
            reposted_missing=True,
        )
    if not reminders_marked_sent:
        logger.warning(
            "mge_refresh_award_reminders_reposted_mark_sent_failed event_id=%s actor_discord_id=%s message_id=%s channel_id=%s",
            resolved_event_id,
            actor_discord_id,
            int(post_result.message_ref.message_id),
            int(post_result.message_ref.channel_id),
        )
        return RefreshAwardRemindersResult(
            False,
            "Award reminders reposted, but failed to mark reminders sent.",
            event_id=resolved_event_id,
            status="reposted_mark_sent_failed",
            reposted_missing=True,
        )
    logger.info(
        "mge_refresh_award_reminders_reposted event_id=%s actor_discord_id=%s message_id=%s channel_id=%s",
        resolved_event_id,
        actor_discord_id,
        int(post_result.message_ref.message_id),
        int(post_result.message_ref.channel_id),
    )
    return RefreshAwardRemindersResult(
        True,
        "Award reminders reposted.",
        event_id=resolved_event_id,
        status="reposted",
        reposted_missing=True,
    )


async def unpublish_event_awards(
    *,
    adapter: MgePublishIoAdapter,
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
        delete_result = await adapter.delete_message(channel_id=channel_id, message_id=message_id)
        embed_deleted = delete_result.status == "deleted"

    refresh_result = adapter.refresh_boards(
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
