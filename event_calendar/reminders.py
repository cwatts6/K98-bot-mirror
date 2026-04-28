from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import logging
from typing import Any

import discord

from constants import (
    EVENT_CALENDAR_REMINDER_GRACE_MINUTES,
    EVENT_CALENDAR_REMINDER_LOOP_SECONDS,
    EVENT_CALENDAR_REMINDERS_DRY_RUN,
)
from core.interaction_safety import get_operation_lock
from event_calendar.reminder_metrics import get_reminder_status_service
from event_calendar.reminder_prefs import is_dm_allowed, normalize_prefs
from event_calendar.reminder_prefs_store import load_all_user_prefs
from event_calendar.reminder_state import CalendarReminderState, make_key
from event_calendar.reminder_types import REMINDER_OFFSET_TO_DELTA
from event_calendar.runtime_cache import filter_events, list_event_types, load_runtime_cache
from file_utils import emit_telemetry_event

logger = logging.getLogger(__name__)


@dataclass
class ReminderDispatchSummary:
    ok: bool
    status: str
    candidates: int = 0
    attempted: int = 0
    sent: int = 0
    skipped_prefs: int = 0
    skipped_already_sent: int = 0
    skipped_unknown_type: int = 0
    failures: int = 0
    failed_forbidden: int = 0
    failed_not_found: int = 0
    failed_http_exception: int = 0
    failed_unknown: int = 0


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _parse_event_start_utc(event: dict[str, Any]) -> datetime | None:
    raw = str(event.get("start_utc") or "").strip()
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    except Exception:
        return None


def _iter_due_event_offsets(
    *,
    events: list[dict[str, Any]],
    now: datetime,
    grace: timedelta,
) -> list[tuple[dict[str, Any], str, datetime]]:
    due: list[tuple[dict[str, Any], str, datetime]] = []
    for e in events:
        start = _parse_event_start_utc(e)
        if not start:
            continue

        for reminder_type, delta in REMINDER_OFFSET_TO_DELTA.items():
            scheduled_for = start - delta
            if now < scheduled_for:
                continue
            if now - scheduled_for > grace:
                continue
            due.append((e, reminder_type, scheduled_for))
    return due


def _discord_ts(dt: datetime, style: str = "F") -> str:
    return f"<t:{int(dt.timestamp())}:{style}>"


def _event_display_name(event: dict[str, Any]) -> str:
    title = str(event.get("title") or event.get("Title") or "(untitled)").strip()
    variant = str(event.get("variant") or event.get("Variant") or "").strip()
    return f"{title} ({variant})" if variant else title


def build_reminder_dm_content(*, event: dict[str, Any], reminder_type: str) -> str:
    emoji = str(event.get("emoji") or event.get("Emoji") or "📅").strip()
    name = _event_display_name(event)

    raw_start = event.get("start_utc") or event.get("StartUTC")
    if isinstance(raw_start, datetime):
        start_dt = raw_start
    else:
        start_dt = datetime.fromisoformat(str(raw_start).replace("Z", "+00:00"))
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=UTC)
    start_dt = start_dt.astimezone(UTC)

    link = str(event.get("link_url") or event.get("LinkURL") or "").strip()

    lines = [
        f"{emoji} **Calendar reminder ({reminder_type})**",
        f"**Event:** {name}",
        f"**When:** {_discord_ts(start_dt, 'F')} ({_discord_ts(start_dt, 'R')})",
    ]
    if link:
        lines.append(f"**Link:** {link}")
    return "\n".join(lines)


def build_reminder_dm_embed(*, event: dict[str, Any], reminder_type: str) -> discord.Embed:
    emoji = str(event.get("emoji") or event.get("Emoji") or "📅").strip()
    name = _event_display_name(event)

    raw_start = event.get("start_utc") or event.get("StartUTC")
    if isinstance(raw_start, datetime):
        start_dt = raw_start
    else:
        start_dt = datetime.fromisoformat(str(raw_start).replace("Z", "+00:00"))
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=UTC)
    start_dt = start_dt.astimezone(UTC)

    link = str(event.get("link_url") or event.get("LinkURL") or "").strip()
    description = str(event.get("description") or event.get("Description") or "").strip()

    embed = discord.Embed(
        title=f"{emoji} Calendar reminder ({reminder_type})",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Event", value=name, inline=False)
    embed.add_field(
        name="When",
        value=f"{_discord_ts(start_dt, 'F')} ({_discord_ts(start_dt, 'R')})",
        inline=False,
    )
    if link:
        embed.add_field(name="Link", value=link, inline=False)
    if description:
        short = description if len(description) <= 300 else (description[:297] + "...")
        embed.add_field(name="Details", value=short, inline=False)

    return embed


async def dispatch_due_calendar_reminders(bot: discord.Client) -> ReminderDispatchSummary:
    now = _now_utc()
    grace = timedelta(minutes=EVENT_CALENDAR_REMINDER_GRACE_MINUTES)

    cache_state = load_runtime_cache()
    if not cache_state.get("ok"):
        summary = ReminderDispatchSummary(ok=False, status="cache_unavailable")
        get_reminder_status_service().record_summary(
            summary=summary, dry_run=EVENT_CALENDAR_REMINDERS_DRY_RUN
        )
        return summary

    events = filter_events(
        cache_state.get("events", []),
        now=now - timedelta(days=7),
        days=365,
        event_type="all",
        importance="all",
    )

    due = _iter_due_event_offsets(events=events, now=now, grace=grace)
    if not due:
        summary = ReminderDispatchSummary(ok=True, status="no_due_reminders")
        get_reminder_status_service().record_summary(
            summary=summary, dry_run=EVENT_CALENDAR_REMINDERS_DRY_RUN
        )
        return summary

    all_prefs = load_all_user_prefs()
    if not all_prefs:
        summary = ReminderDispatchSummary(ok=True, status="no_opted_in_users")
        get_reminder_status_service().record_summary(
            summary=summary, dry_run=EVENT_CALENDAR_REMINDERS_DRY_RUN
        )
        return summary

    known_types = set(list_event_types(cache_state))
    state = CalendarReminderState.load(path=None)

    summary = ReminderDispatchSummary(ok=True, status="completed", candidates=len(due))

    for user_id_raw, raw_prefs in all_prefs.items():
        try:
            user_id = int(user_id_raw)
        except Exception:
            continue

        prefs = normalize_prefs(raw_prefs)
        for event, reminder_type, scheduled_for in due:
            et = str(event.get("type") or "").strip().lower()
            if et not in known_types:
                summary.skipped_unknown_type += 1
                continue

            instance_id = str(event.get("instance_id") or "").strip()
            if not instance_id:
                continue

            key = make_key(instance_id, user_id, reminder_type)

            if not state.should_send_with_grace(
                key=key,
                scheduled_for=scheduled_for,
                now=now,
                grace=grace,
            ):
                summary.skipped_already_sent += 1
                continue

            try:
                allowed = is_dm_allowed(
                    reminder_type=reminder_type,
                    event_type=et,
                    prefs=prefs,
                    known_event_types=known_types,
                )
            except ValueError:
                summary.skipped_unknown_type += 1
                continue

            if not allowed:
                summary.skipped_prefs += 1
                continue

            summary.attempted += 1
            if EVENT_CALENDAR_REMINDERS_DRY_RUN:
                logger.info(
                    "[CALENDAR][REMINDER][DRY_RUN] user_id=%s instance_id=%s type=%s event_type=%s",
                    user_id,
                    instance_id,
                    reminder_type,
                    et,
                )
                state.mark_sent(key, sent_at=now)
                summary.sent += 1
                continue

            try:
                user = bot.get_user(user_id) or await bot.fetch_user(user_id)
                msg_text = build_reminder_dm_content(event=event, reminder_type=reminder_type)
                msg_embed = build_reminder_dm_embed(event=event, reminder_type=reminder_type)

                try:
                    await user.send(content=msg_text, embed=msg_embed)
                except discord.HTTPException:
                    await user.send(msg_text)

                state.mark_sent(key, sent_at=now)
                summary.sent += 1
            except discord.Forbidden:
                summary.failures += 1
                summary.failed_forbidden += 1
            except discord.NotFound:
                summary.failures += 1
                summary.failed_not_found += 1
            except discord.HTTPException:
                summary.failures += 1
                summary.failed_http_exception += 1
            except Exception:
                summary.failures += 1
                summary.failed_unknown += 1

    state.save()
    get_reminder_status_service().record_summary(
        summary=summary, dry_run=EVENT_CALENDAR_REMINDERS_DRY_RUN
    )

    logger.info(
        "[CALENDAR][REMINDER] status=%s candidates=%s attempted=%s sent=%s skipped_prefs=%s skipped_already_sent=%s skipped_unknown_type=%s failures=%s forbidden=%s not_found=%s http=%s unknown=%s dry_run=%s",
        summary.status,
        summary.candidates,
        summary.attempted,
        summary.sent,
        summary.skipped_prefs,
        summary.skipped_already_sent,
        summary.skipped_unknown_type,
        summary.failures,
        summary.failed_forbidden,
        summary.failed_not_found,
        summary.failed_http_exception,
        summary.failed_unknown,
        EVENT_CALENDAR_REMINDERS_DRY_RUN,
    )

    emit_telemetry_event(
        {
            "event": "calendar_reminder_dispatch",
            "ok": summary.ok,
            "status": summary.status,
            "candidates": summary.candidates,
            "attempted": summary.attempted,
            "sent": summary.sent,
            "skipped_prefs": summary.skipped_prefs,
            "skipped_already_sent": summary.skipped_already_sent,
            "skipped_unknown_type": summary.skipped_unknown_type,
            "failures": summary.failures,
            "failed_forbidden": summary.failed_forbidden,
            "failed_not_found": summary.failed_not_found,
            "failed_http_exception": summary.failed_http_exception,
            "failed_unknown": summary.failed_unknown,
            "dry_run": EVENT_CALENDAR_REMINDERS_DRY_RUN,
        }
    )

    return summary


async def run_calendar_reminder_loop(
    bot: discord.Client, *, interval_seconds: int | None = None
) -> None:
    interval = int(interval_seconds or EVENT_CALENDAR_REMINDER_LOOP_SECONDS)
    if interval < 1:
        raise ValueError("interval_seconds must be >= 1")

    while True:
        try:
            async with get_operation_lock("calendar_reminders"):
                await dispatch_due_calendar_reminders(bot)
        except Exception as e:
            logger.exception("[CALENDAR][REMINDER] loop iteration failed")
            get_reminder_status_service().record_failure(
                status="loop_iteration_failed",
                error_message=f"{type(e).__name__}: {e}",
                dry_run=EVENT_CALENDAR_REMINDERS_DRY_RUN,
            )
        await asyncio.sleep(interval)
