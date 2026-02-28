from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, time as dt_time, timedelta
import logging
from typing import Any

from ark.confirmation_flow import ArkConfirmationController
from ark.dal.ark_dal import (
    get_alliance,
    get_config,
    get_match,
    get_reminder_prefs,
    get_roster,
    insert_audit_log,
    list_open_matches,
    lock_match,
    update_match_confirmation_message,
)
from ark.embeds import build_ark_locked_embed_from_match, resolve_ark_match_datetime
from ark.registration_messages import disable_registration_message
from ark.reminder_prefs import is_dm_allowed
from ark.reminder_state import (
    ArkReminderState,
    make_channel_daily_key,
    make_channel_key,
    make_dm_key,
)
from ark.reminder_types import (
    REMINDER_1H,
    REMINDER_4H,
    REMINDER_24H,
    REMINDER_CHECKIN_12H,
    REMINDER_DAILY,
    REMINDER_FINAL_DAY,
    REMINDER_START,
)
from ark.state.ark_state import ArkJsonState, ArkMessageRef, ArkMessageState
from utils import ensure_aware_utc, utcnow

logger = logging.getLogger(__name__)

REMINDER_GRACE = timedelta(minutes=15)
DAILY_REMINDER_TIME_UTC = dt_time(20, 0, tzinfo=UTC)


@dataclass
class ArkSchedulerState:
    tasks: dict[str, asyncio.Task] = field(default_factory=dict)
    match_locks: dict[int, asyncio.Lock] = field(default_factory=lambda: defaultdict(asyncio.Lock))
    reminder_state: ArkReminderState = field(default_factory=ArkReminderState.load)

    def set_task(self, key: str, task: asyncio.Task) -> None:
        self.tasks[key] = task

    def clear_task(self, key: str) -> None:
        self.tasks.pop(key, None)


def _task_key(match_id: int, kind: str) -> str:
    return f"{match_id}:{kind}"


def _utcnow() -> datetime:
    return ensure_aware_utc(utcnow())


def _build_jump_url(guild_id: int, channel_id: int, message_id: int) -> str:
    return f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"


async def _sleep_until(target: datetime) -> None:
    now = _utcnow()
    delay = (ensure_aware_utc(target) - now).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)


async def lock_match_and_post_confirmation(
    *, client, match_id: int, config: dict[str, Any]
) -> None:
    match = await get_match(match_id)
    if not match:
        return

    locked = await lock_match(match_id, actor_discord_id=None)
    if not locked:
        match = await get_match(match_id)
        if not match or (match.get("Status") or "").lower() != "locked":
            return

    alliance_row = await get_alliance((match.get("Alliance") or "").strip())
    if not alliance_row:
        logger.warning("[ARK_SCHED] Alliance not found for match %s", match_id)
        return

    confirmation_channel_id = alliance_row.get("ConfirmationChannelId")
    if not confirmation_channel_id:
        logger.warning("[ARK_SCHED] Missing confirmation channel for %s", match_id)
        return

    roster = await get_roster(match_id)

    controller = ArkConfirmationController(match_id=match_id, config=config)
    embed, view = await controller.build_payload(
        match,
        roster=roster,
        show_check_in=False,
        updates=None,
    )

    channel = client.get_channel(int(confirmation_channel_id))
    if not channel:
        logger.warning("[ARK_SCHED] Confirmation channel %s not found.", confirmation_channel_id)
        return

    msg = await channel.send(embed=embed, view=view)

    state = ArkJsonState()
    await state.load_async()
    existing_state = state.messages.get(match_id)
    confirmation_ref = ArkMessageRef(channel_id=msg.channel.id, message_id=msg.id)
    if isinstance(existing_state, ArkMessageState):
        existing_state.confirmation = confirmation_ref
        state.messages[match_id] = existing_state
    else:
        state.messages[match_id] = ArkMessageState(confirmation=confirmation_ref)
    await state.save_async()

    await update_match_confirmation_message(match_id, msg.channel.id, msg.id)

    locked_embed = build_ark_locked_embed_from_match(
        match,
        players_cap=int(config["PlayersCap"]),
        subs_cap=int(config["SubsCap"]),
        roster=roster,
    )

    await disable_registration_message(
        client=client,
        state=state,
        match_id=match_id,
        embed=locked_embed,
    )

    await insert_audit_log(
        action_type="match_lock",
        actor_discord_id=0,
        match_id=match_id,
        governor_id=None,
        details_json={"source": "Scheduler"},
    )


async def ensure_confirmation_message(
    *, client, match_id: int, config: dict[str, Any], show_check_in: bool
) -> bool:
    match = await get_match(match_id)
    if not match:
        return False

    alliance_row = await get_alliance((match.get("Alliance") or "").strip())
    if not alliance_row:
        return False

    confirmation_channel_id = alliance_row.get("ConfirmationChannelId")
    if not confirmation_channel_id:
        return False

    controller = ArkConfirmationController(match_id=match_id, config=config)
    result = await controller.refresh_confirmation_message(
        client=client,
        target_channel_id=int(confirmation_channel_id),
        show_check_in=show_check_in,
    )
    return bool(result)


async def activate_check_in(*, client, match_id: int, config: dict[str, Any]) -> bool:
    return await ensure_confirmation_message(
        client=client,
        match_id=match_id,
        config=config,
        show_check_in=True,
    )


async def _schedule_once(
    *, state: ArkSchedulerState, key: str, when: datetime, coro_factory
) -> None:
    if key in state.tasks:
        return

    async def _runner():
        try:
            await _sleep_until(when)
            await coro_factory()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("[ARK_SCHED] Task %s failed", key)
        finally:
            state.clear_task(key)

    state.set_task(key, asyncio.create_task(_runner(), name=f"ark:{key}"))


async def _send_channel_reminder(
    *,
    client,
    state: ArkSchedulerState,
    match: dict[str, Any],
    reminder_type: str,
    channel_id: int,
    text: str,
    scheduled_for: datetime,
    dedupe_key: str | None = None,  # NEW
) -> bool:
    key = dedupe_key or make_channel_key(int(match["MatchId"]), int(channel_id), reminder_type)
    now = _utcnow()
    if not state.reminder_state.should_send_with_grace(
        key=key, scheduled_for=ensure_aware_utc(scheduled_for), now=now, grace=REMINDER_GRACE
    ):
        return False

    channel = client.get_channel(int(channel_id))
    if not channel:
        return False

    await channel.send(text)
    state.reminder_state.mark_sent(key, sent_at=now)
    state.reminder_state.save()
    return True


async def _dispatch_dm_reminders_for_match(
    *,
    client,
    state: ArkSchedulerState,
    match: dict[str, Any],
    reminder_type: str,
    scheduled_for: datetime,
    include_checkin_line: bool = False,
) -> dict[str, int]:
    counters = {"attempted": 0, "sent": 0, "skipped_optout": 0, "skipped_dedupe": 0, "failed": 0}
    roster = await get_roster(int(match["MatchId"]))
    prefs_cache: dict[int, dict | None] = {}

    for row in roster:
        if (row.get("Status") or "").lower() != "active":
            continue
        uid = row.get("DiscordUserId")
        if not uid:
            continue

        user_id = int(uid)
        dkey = make_dm_key(int(match["MatchId"]), user_id, reminder_type)
        now = _utcnow()

        if not state.reminder_state.should_send_with_grace(
            key=dkey,
            scheduled_for=ensure_aware_utc(scheduled_for),
            now=now,
            grace=REMINDER_GRACE,
        ):
            counters["skipped_dedupe"] += 1
            continue

        if user_id not in prefs_cache:
            prefs_cache[user_id] = await get_reminder_prefs(user_id)
        prefs = prefs_cache[user_id]

        if not is_dm_allowed(reminder_type, prefs):
            counters["skipped_optout"] += 1
            continue

        user = client.get_user(user_id)
        if user is None:
            try:
                user = await client.fetch_user(user_id)
            except Exception:
                logger.exception(
                    "[ARK_REMINDER] failed to resolve user for DM match_id=%s type=%s user_id=%s",
                    match.get("MatchId"),
                    reminder_type,
                    user_id,
                )
                counters["failed"] += 1
                continue

        content = f"Ark reminder ({reminder_type}) for {match.get('Alliance', 'Alliance')}"
        if include_checkin_line:
            content += "\nCheck-in is now available."

        counters["attempted"] += 1
        try:
            await user.send(content)
            counters["sent"] += 1
            state.reminder_state.mark_sent(dkey, sent_at=now)
        except Exception:
            logger.exception(
                "[ARK_REMINDER] failed to send DM match_id=%s type=%s user_id=%s",
                match.get("MatchId"),
                reminder_type,
                user_id,
            )
            counters["failed"] += 1

    state.reminder_state.save()
    return counters


async def _run_match_reminder_dispatch(
    client, state: ArkSchedulerState, match: dict[str, Any]
) -> None:
    match_id = int(match["MatchId"])
    async with state.match_locks[match_id]:
        latest = await get_match(match_id)
        if latest:
            match = latest

        status = (match.get("Status") or "").strip().lower()
        if status in {"cancelled", "completed"}:
            return

        alliance_row = await get_alliance((match.get("Alliance") or "").strip())
        if not alliance_row:
            return

        reg_channel_id = alliance_row.get("RegistrationChannelId")
        conf_channel_id = alliance_row.get("ConfirmationChannelId")

        msg_state = ArkJsonState()
        await msg_state.load_async()
        registration_jump = None
        block = msg_state.messages.get(match_id)
        if block and getattr(block, "registration", None):
            guild_raw = getattr(client, "guild_id", None)
            if guild_raw:
                guild_id = int(guild_raw)
                if guild_id:
                    registration_jump = _build_jump_url(
                        guild_id,
                        int(block.registration.channel_id),
                        int(block.registration.message_id),
                    )

        match_dt = ensure_aware_utc(
            resolve_ark_match_datetime(
                match["ArkWeekendDate"],
                match["MatchDay"],
                match["MatchTimeUtc"],
            )
        )
        now = _utcnow()

        close_dt = match.get("SignupCloseUtc")
        if close_dt:
            close_dt = ensure_aware_utc(close_dt)

        require_jump_link = True

        # Pre-close reminders in registration channel
        if status != "locked" and reg_channel_id and close_dt and now < close_dt:
            daily_sched = now.replace(
                hour=DAILY_REMINDER_TIME_UTC.hour,
                minute=DAILY_REMINDER_TIME_UTC.minute,
                second=0,
                microsecond=0,
            )
            if now >= daily_sched and (now - daily_sched) <= REMINDER_GRACE:
                if not require_jump_link or registration_jump:
                    jump = f"\nSign up here: {registration_jump}" if registration_jump else ""
                    daily_key = make_channel_daily_key(
                        int(match["MatchId"]), int(reg_channel_id), REMINDER_DAILY, now.date()
                    )
                    logger.info(
                        "[ARK_REMINDER] sending channel reminder match_id=%s type=%s channel_id=%s key=%s",
                        match_id,
                        REMINDER_DAILY,
                        int(reg_channel_id),
                        daily_key,
                    )
                    await _send_channel_reminder(
                        client=client,
                        state=state,
                        match=match,
                        reminder_type=REMINDER_DAILY,
                        channel_id=int(reg_channel_id),
                        text=f"📣 **Ark signup reminder (daily)**{jump}",
                        scheduled_for=daily_sched,
                        dedupe_key=daily_key,
                    )
                else:
                    logger.info(
                        "[ARK_REMINDER] skip pre-close reminder (missing jump link) match_id=%s type=%s",
                        match_id,
                        REMINDER_DAILY,
                    )

            final_sched = close_dt.replace(hour=12, minute=0, second=0, microsecond=0)
            if now >= final_sched and (now - final_sched) <= REMINDER_GRACE:
                if not require_jump_link or registration_jump:
                    jump = f"\nSign up here: {registration_jump}" if registration_jump else ""
                    logger.info(
                        "[ARK_REMINDER] sending channel reminder match_id=%s type=%s channel_id=%s",
                        match_id,
                        REMINDER_FINAL_DAY,
                        int(reg_channel_id),
                    )
                    await _send_channel_reminder(
                        client=client,
                        state=state,
                        match=match,
                        reminder_type=REMINDER_FINAL_DAY,
                        channel_id=int(reg_channel_id),
                        text=f"🚨 **Final-day Ark signup reminder**{jump}",
                        scheduled_for=final_sched,
                    )
                else:
                    logger.info(
                        "[ARK_REMINDER] skip pre-close reminder (missing jump link) match_id=%s type=%s",
                        match_id,
                        REMINDER_FINAL_DAY,
                    )

        # Match-start reminders to confirmation/planning + DM
        windows = [
            (REMINDER_24H, timedelta(hours=24)),
            (REMINDER_4H, timedelta(hours=4)),
            (REMINDER_1H, timedelta(hours=1)),
            (REMINDER_START, timedelta(hours=0)),
        ]
        for rtype, offset in windows:
            scheduled_for = ensure_aware_utc(match_dt - offset)
            if now >= scheduled_for and (now - scheduled_for) <= REMINDER_GRACE:
                if conf_channel_id:
                    await _send_channel_reminder(
                        client=client,
                        state=state,
                        match=match,
                        reminder_type=rtype,
                        channel_id=int(conf_channel_id),
                        text=f"⏰ **Ark reminder ({rtype})**",
                        scheduled_for=scheduled_for,
                    )
                await _dispatch_dm_reminders_for_match(
                    client=client,
                    state=state,
                    match=match,
                    reminder_type=rtype,
                    scheduled_for=scheduled_for,
                )

        checkin_sched = ensure_aware_utc(match_dt - timedelta(hours=12))
        if now >= checkin_sched and (now - checkin_sched) <= REMINDER_GRACE:
            await _dispatch_dm_reminders_for_match(
                client=client,
                state=state,
                match=match,
                reminder_type=REMINDER_CHECKIN_12H,
                scheduled_for=checkin_sched,
                include_checkin_line=True,
            )


async def schedule_ark_lifecycle(client, poll_interval_seconds: int = 300) -> None:
    state = ArkSchedulerState()

    while True:
        try:
            config = await get_config()
            if not config:
                await asyncio.sleep(poll_interval_seconds)
                continue

            matches = await list_open_matches()
            now = _utcnow()
            checkin_offset = int(config.get("CheckInActivationOffsetHours") or 12)

            active_ids = {int(m["MatchId"]) for m in matches}

            for key in list(state.tasks):
                mid = int(key.split(":")[0])
                if mid not in active_ids:
                    task = state.tasks.pop(key, None)
                    if task and not task.done():
                        task.cancel()

            for match in matches:
                match_id = int(match["MatchId"])
                match_dt = ensure_aware_utc(
                    resolve_ark_match_datetime(
                        match["ArkWeekendDate"],
                        match["MatchDay"],
                        match["MatchTimeUtc"],
                    )
                )
                signup_close = ensure_aware_utc(match["SignupCloseUtc"])
                checkin_at = ensure_aware_utc(match_dt - timedelta(hours=checkin_offset))

                status = (match.get("Status") or "").lower()

                if status == "scheduled":
                    if now >= signup_close:
                        await lock_match_and_post_confirmation(
                            client=client, match_id=match_id, config=config
                        )
                    else:
                        await _schedule_once(
                            state=state,
                            key=_task_key(match_id, "lock"),
                            when=signup_close,
                            coro_factory=lambda mid=match_id: lock_match_and_post_confirmation(
                                client=client, match_id=mid, config=config
                            ),
                        )

                if now >= checkin_at:
                    await ensure_confirmation_message(
                        client=client,
                        match_id=match_id,
                        config=config,
                        show_check_in=True,
                    )
                else:
                    await _schedule_once(
                        state=state,
                        key=_task_key(match_id, "checkin"),
                        when=checkin_at,
                        coro_factory=lambda mid=match_id: activate_check_in(
                            client=client, match_id=mid, config=config
                        ),
                    )

                await _run_match_reminder_dispatch(client=client, state=state, match=match)

            await asyncio.sleep(poll_interval_seconds)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("[ARK_SCHED] Scheduler loop failed")
            await asyncio.sleep(poll_interval_seconds)
