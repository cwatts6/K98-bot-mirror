from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, time as dt_time, timedelta
import logging
from typing import Any

import discord

from ark.ark_auto_create_service import sync_ark_matches_from_calendar
from ark.confirmation_flow import ArkConfirmationController
from ark.dal.ark_dal import (
    get_alliance,
    get_config,
    get_match,
    get_reminder_prefs,
    get_roster,
    insert_audit_log,
    list_completed_matches_pending_completion,
    list_match_team_rows,  # ← NEW (Phase C)
    list_matches_pending_registration_open,
    list_open_matches,
    lock_match,
    mark_match_completed,
    mark_match_completion_posted,
)
from ark.embeds import build_ark_locked_embed_from_match, resolve_ark_match_datetime
from ark.registration_flow import ArkRegistrationController
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
    REMINDER_CHECKIN_12H,
    REMINDER_DAILY,
    REMINDER_REGISTRATION_CLOSE_1H,
    REMINDER_START,
)
from ark.state.ark_state import ArkJsonState
from utils import ensure_aware_utc, utcnow

logger = logging.getLogger(__name__)

REMINDER_GRACE = timedelta(minutes=15)
DAILY_REMINDER_TIME_UTC = dt_time(20, 0, tzinfo=UTC)


async def _build_team_name_fields(
    match_id: int,
    roster: list[dict[str, Any]] | None = None,
) -> tuple[str, str] | None:
    """
    Return (team1_names_str, team2_names_str) from finalised SQL team rows,
    or None if no finalised teams exist.

    Names are comma-separated GovernorNameSnapshot values.
    Only IsFinal=1 rows are used — draft rows are not shown in reminders.
    If roster is not provided, it is fetched from SQL.
    """
    try:
        all_rows = await list_match_team_rows(match_id=match_id, draft_only=False)
        final_rows = [r for r in (all_rows or []) if int(r.get("IsFinal") or 0) == 1]
        if not final_rows:
            return None

        if roster is None:
            roster = await get_roster(match_id)

        name_map: dict[int, str] = {}
        for r in roster or []:
            gid = r.get("GovernorId")
            name = r.get("GovernorNameSnapshot")
            if gid is not None and name:
                name_map[int(gid)] = str(name)

        team1_names: list[str] = []
        team2_names: list[str] = []
        for row in final_rows:
            gid = row.get("GovernorId")
            team_no = row.get("TeamNumber")
            if gid is None or team_no is None:
                continue
            name = name_map.get(int(gid), str(gid))
            if int(team_no) == 1:
                team1_names.append(name)
            elif int(team_no) == 2:
                team2_names.append(name)

        return (", ".join(team1_names), ", ".join(team2_names))
    except Exception:
        logger.exception(
            "[ARK_REMINDER] Failed building team name fields for match_id=%s", match_id
        )
        return None


async def _build_channel_reminder_embed(
    *,
    match: dict[str, Any],
    reminder_type: str,
    text: str,
    roster: list[dict[str, Any]] | None = None,
) -> discord.Embed:
    title = f"Ark Reminder ({reminder_type})"
    alliance = str(match.get("Alliance") or "Alliance")
    embed = discord.Embed(title=title, color=discord.Color.blurple())
    embed.add_field(name="Alliance", value=alliance, inline=False)
    embed.add_field(name="Message", value=text, inline=False)

    team_fields = await _build_team_name_fields(int(match["MatchId"]), roster=roster)
    if team_fields:
        t1_names, t2_names = team_fields
        embed.add_field(name="Team 1", value=t1_names or "—", inline=False)
        embed.add_field(name="Team 2", value=t2_names or "—", inline=False)

    return embed


async def _build_dm_reminder_embed(
    *,
    match: dict[str, Any],
    reminder_type: str,
    include_checkin_line: bool = False,
    roster: list[dict[str, Any]] | None = None,
) -> discord.Embed:
    alliance = str(match.get("Alliance") or "Alliance")
    embed = discord.Embed(
        title=f"Ark DM Reminder ({reminder_type})",
        description=f"Reminder for **{alliance}**",
        color=discord.Color.green(),
    )
    if include_checkin_line:
        embed.add_field(name="Check-in", value="Check-in is now available.", inline=False)

    team_fields = await _build_team_name_fields(int(match["MatchId"]), roster=roster)
    if team_fields:
        t1_names, t2_names = team_fields
        embed.add_field(name="Team 1", value=t1_names or "—", inline=False)
        embed.add_field(name="Team 2", value=t2_names or "—", inline=False)

    return embed


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

    posted = await ensure_confirmation_message(
        client=client,
        match_id=match_id,
        config=config,
        show_check_in=False,
    )

    if not posted:
        logger.warning("[ARK_SCHED] lock->confirmation upsert failed match_id=%s", match_id)

    roster = await get_roster(match_id)
    state = ArkJsonState()
    await state.load_async()

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
        details_json={"source": "Scheduler", "confirmation_upsert_ok": bool(posted)},
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


async def _run_completion_update(*, client, match_id: int, config: dict[str, Any]) -> bool:
    ok = await ensure_confirmation_message(
        client=client,
        match_id=match_id,
        config=config,
        show_check_in=False,
    )
    if ok:
        await mark_match_completion_posted(match_id)
    return ok


async def _complete_match_if_needed(*, match_id: int) -> bool:
    match = await get_match(match_id)
    if not match:
        return False

    status = (match.get("Status") or "").strip().lower()
    if status == "completed":
        return True

    if status in {"locked", "scheduled"}:
        logger.info(
            "[ARK_SCHED] completion_fallback match_id=%s status=%s reason=no_admin_result",
            match_id,
            status,
        )
        return await mark_match_completed(match_id, actor_discord_id=0)

    return False


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
    dedupe_key: str | None = None,
    announce: bool = False,  # ← PRESERVED from Phase B+D — do not remove
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

    embed = await _build_channel_reminder_embed(  # ← now awaited
        match=match, reminder_type=reminder_type, text=text
    )
    await channel.send(
        content=text,
        embed=embed,
        allowed_mentions=(
            discord.AllowedMentions(everyone=True) if announce else discord.AllowedMentions.none()
        ),
    )
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

        embed = await _build_dm_reminder_embed(
            match=match,
            reminder_type=reminder_type,
            include_checkin_line=include_checkin_line,
            roster=roster,  # ← pass through from the already-fetched roster
        )

        counters["attempted"] += 1
        try:
            await user.send(embed=embed)
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

        match_dt = ensure_aware_utc(
            resolve_ark_match_datetime(
                match["ArkWeekendDate"],
                match["MatchDay"],
                match["MatchTimeUtc"],
            )
        )
        now = _utcnow()

        # Guard: do not run any reminder or repost logic until registration is open
        starts_at = match.get("RegistrationStartsAtUtc")
        if starts_at:
            starts_at_utc = ensure_aware_utc(starts_at)
            if starts_at_utc > now:
                logger.info(
                    "[ARK_SCHED] reminder_dispatch_skip match_id=%s reason=registration_not_open "
                    "registration_starts_at_utc=%s",
                    match_id,
                    starts_at_utc.isoformat(),
                )
                return

        close_dt = match.get("SignupCloseUtc")
        if close_dt:
            close_dt = ensure_aware_utc(close_dt)

        # Registration channel behavior:
        # - keep daily "repost/refresh visibility"
        # - registration_close_1h fires @everyone 1h before SignupCloseUtc
        if status != "locked" and reg_channel_id and close_dt and now < close_dt:
            daily_sched = now.replace(
                hour=DAILY_REMINDER_TIME_UTC.hour,
                minute=DAILY_REMINDER_TIME_UTC.minute,
                second=0,
                microsecond=0,
            )
            if now >= daily_sched and (now - daily_sched) <= REMINDER_GRACE:
                daily_key = make_channel_daily_key(
                    int(match["MatchId"]), int(reg_channel_id), REMINDER_DAILY, now.date()
                )
                if state.reminder_state.should_send_with_grace(
                    key=daily_key,
                    scheduled_for=daily_sched,
                    now=now,
                    grace=REMINDER_GRACE,
                ):
                    config = await get_config()
                    if not config:
                        logger.warning(
                            "[ARK_REGISTRATION] missing config for daily visibility refresh match_id=%s",
                            match_id,
                        )
                    else:
                        logger.info(
                            "[ARK_REGISTRATION] refreshing active registration visibility match_id=%s channel_id=%s key=%s",
                            match_id,
                            int(reg_channel_id),
                            daily_key,
                        )
                        controller = ArkRegistrationController(match_id=match_id, config=config)
                        ref = await controller.ensure_registration_message(
                            client=client,
                            announce=False,
                            force_announce=False,
                            force_repost=True,
                            target_channel_id=int(reg_channel_id),
                            update_refresh_timestamp=True,
                        )
                        if ref:
                            state.reminder_state.mark_sent(daily_key, sent_at=now)
                            state.reminder_state.save()
                        else:
                            logger.warning(
                                "[ARK_REGISTRATION] daily visibility refresh failed match_id=%s",
                                match_id,
                            )

            # Registration closing soon — fires 1h before SignupCloseUtc with @everyone
            close_1h_sched = ensure_aware_utc(close_dt - timedelta(hours=1))
            if now >= close_1h_sched and (now - close_1h_sched) <= REMINDER_GRACE:
                close_1h_key = make_channel_key(
                    int(match["MatchId"]),
                    int(reg_channel_id),
                    REMINDER_REGISTRATION_CLOSE_1H,
                )
                if state.reminder_state.should_send_with_grace(
                    key=close_1h_key,
                    scheduled_for=close_1h_sched,
                    now=now,
                    grace=REMINDER_GRACE,
                ):
                    # Build jump URL if registration message ref is available
                    reg_msg_link: str | None = None
                    reg_cid = int(match.get("RegistrationChannelId") or 0)
                    reg_mid = int(match.get("RegistrationMessageId") or 0)
                    if reg_cid and reg_mid:
                        reg_channel_obj = client.get_channel(reg_cid)
                        guild_id = getattr(getattr(reg_channel_obj, "guild", None), "id", None)
                        if guild_id:
                            reg_msg_link = (
                                f"https://discord.com/channels/{guild_id}/{reg_cid}/{reg_mid}"
                            )

                    link_line = f"\n👉 {reg_msg_link}" if reg_msg_link else ""
                    text = (
                        f"@everyone ⚠️ **Ark signups close in 1 hour — {match.get('Alliance', '')}!**"
                        f"{link_line}"
                    )
                    sent = await _send_channel_reminder(
                        client=client,
                        state=state,
                        match=match,
                        reminder_type=REMINDER_REGISTRATION_CLOSE_1H,
                        channel_id=int(reg_channel_id),
                        text=text,
                        scheduled_for=close_1h_sched,
                        dedupe_key=close_1h_key,
                        announce=True,
                    )
                    if sent:
                        logger.info(
                            "[ARK_REGISTRATION] close_1h_reminder_sent match_id=%s channel_id=%s",
                            match_id,
                            int(reg_channel_id),
                        )

        windows = [
            (REMINDER_4H, timedelta(hours=4)),
            (REMINDER_1H, timedelta(hours=1)),
            (REMINDER_START, timedelta(hours=0)),
        ]
        for rtype, offset in windows:
            scheduled_for = ensure_aware_utc(match_dt - offset)
            if now >= scheduled_for and (now - scheduled_for) <= REMINDER_GRACE:
                # H2: at 4h, warn if a locked match has no final team rows
                if rtype == REMINDER_4H and conf_channel_id:
                    team_rows = await list_match_team_rows(match_id, draft_only=False)
                    final_rows = [r for r in team_rows if int(r.get("IsFinal") or 0) == 1]
                    if not final_rows:
                        logger.warning(
                            "[ARK_SCHED] no_final_teams_at_4h_reminder match_id=%s",
                            match_id,
                        )

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

        # Phase G: Check-in open channel announcement — fires once per match
        # when the checkin window opens. No @everyone — confirmation channel
        # audience is already signed-up players only.
        # Gated only by was_sent (no grace window) so a delayed scheduler
        # still fires this if it was missed during the grace window.
        if conf_channel_id and now >= checkin_sched:
            checkin_open_key = make_channel_key(
                match_id,
                int(conf_channel_id),
                REMINDER_CHECKIN_12H,
            )
            if not state.reminder_state.was_sent(checkin_open_key):
                # H2: warn if locked match has no final team rows at check-in time
                team_rows = await list_match_team_rows(match_id, draft_only=False)
                final_rows = [r for r in team_rows if int(r.get("IsFinal") or 0) == 1]
                if not final_rows:
                    logger.warning(
                        "[ARK_SCHED] no_final_teams_at_checkin_reminder match_id=%s",
                        match_id,
                    )

                checkin_text = (
                    f"🔔 **Check-in is now open — {match.get('Alliance', '')}!** "
                    f"Use the button on the match post to check in."
                )
                await _send_channel_reminder(
                    client=client,
                    state=state,
                    match=match,
                    reminder_type=REMINDER_CHECKIN_12H,
                    channel_id=int(conf_channel_id),
                    text=checkin_text,
                    scheduled_for=checkin_sched,
                    dedupe_key=checkin_open_key,
                )


async def _open_pending_registrations(*, client, config: dict[str, Any], now: datetime) -> None:
    logger.info("[ARK_REGISTRATION] pending-open scan start now=%s", now.isoformat())
    candidates = await list_matches_pending_registration_open(now)
    logger.info(
        "[ARK_REGISTRATION] pending-open candidates=%s now=%s",
        len(candidates),
        now.isoformat(),
    )

    for match in candidates:
        match_id = int(match["MatchId"])
        status = (match.get("Status") or "").strip().lower()
        starts_at = match.get("RegistrationStartsAtUtc")
        close_at = match.get("SignupCloseUtc")
        reg_channel = match.get("RegistrationChannelId")
        reg_message = match.get("RegistrationMessageId")

        if status != "scheduled":
            logger.info(
                "[ARK_REGISTRATION] pending-open skip match_id=%s reason=status status=%s",
                match_id,
                status,
            )
            continue

        if not starts_at:
            logger.info(
                "[ARK_REGISTRATION] pending-open skip match_id=%s reason=missing_start",
                match_id,
            )
            continue

        starts_at_utc = ensure_aware_utc(starts_at)
        if starts_at_utc > now:
            logger.info(
                "[ARK_REGISTRATION] pending-open skip match_id=%s reason=not_yet_open registration_starts_at_utc=%s",
                match_id,
                starts_at_utc.isoformat(),
            )
            continue

        if not close_at or ensure_aware_utc(close_at) <= now:
            logger.info(
                "[ARK_REGISTRATION] pending-open skip match_id=%s reason=outside_window signup_close_utc=%s",
                match_id,
                ensure_aware_utc(close_at).isoformat() if close_at else None,
            )
            continue

        if reg_channel and reg_message:
            logger.info(
                "[ARK_REGISTRATION] pending-open skip match_id=%s reason=already_posted channel_id=%s message_id=%s",
                match_id,
                int(reg_channel),
                int(reg_message),
            )
            continue

        alliance_row = await get_alliance((match.get("Alliance") or "").strip())
        target_channel_id = (alliance_row or {}).get("RegistrationChannelId")
        if not target_channel_id:
            logger.warning(
                "[ARK_REGISTRATION] pending-open skip match_id=%s reason=missing_registration_channel",
                match_id,
            )
            continue

        announce_already_sent = bool(match.get("AnnouncementSent"))
        logger.info(
            "[ARK_REGISTRATION] pending-open opening match_id=%s requested_announce=true announcement_sent=%s registration_starts_at_utc=%s signup_close_utc=%s",
            match_id,
            announce_already_sent,
            starts_at_utc.isoformat(),
            ensure_aware_utc(close_at).isoformat() if close_at else None,
        )

        controller = ArkRegistrationController(match_id=match_id, config=config)
        ref = await controller.ensure_registration_message(
            client=client,
            announce=True,
            force_announce=False,
            force_repost=False,
            target_channel_id=int(target_channel_id),
            update_refresh_timestamp=False,
        )
        if ref:
            logger.info(
                "[ARK_REGISTRATION] pending-open posted match_id=%s channel_id=%s message_id=%s",
                match_id,
                int(ref.channel_id),
                int(ref.message_id),
            )
        else:
            logger.warning(
                "[ARK_REGISTRATION] pending-open failed match_id=%s requested_announce=true",
                match_id,
            )

    logger.info("[ARK_REGISTRATION] pending-open scan end now=%s", now.isoformat())


async def schedule_ark_lifecycle(client, poll_interval_seconds: int = 300) -> None:
    state = ArkSchedulerState()

    while True:
        try:
            # CR4: Reload reminder state from disk each tick so that external clears
            # (e.g. reschedule_match_reminders) take effect within one poll interval.
            state.reminder_state = ArkReminderState.load()

            config = await get_config()
            if not config:
                await asyncio.sleep(poll_interval_seconds)
                continue

            auto_create_result = await sync_ark_matches_from_calendar(
                client=client,
                now_utc=_utcnow(),
                config=config,
            )
            logger.info(
                "[ARK_SCHED] auto-create tick scanned=%s created=%s existing=%s skipped_cancelled_match=%s invalid_title=%s errors=%s",
                auto_create_result.scanned,
                auto_create_result.created,
                auto_create_result.existing,
                auto_create_result.skipped_cancelled_match,
                auto_create_result.invalid_title,
                auto_create_result.errors,
            )

            matches = await list_open_matches()
            logger.info(
                "[ARK_SCHED] open_matches ids=%s statuses=%s",
                [int(m["MatchId"]) for m in matches],
                [str(m.get("Status")) for m in matches],
            )
            completed_matches = await list_completed_matches_pending_completion()
            now = _utcnow()
            checkin_offset = int(config.get("CheckInActivationOffsetHours") or 12)

            await _open_pending_registrations(client=client, config=config, now=now)

            active_ids = {int(m["MatchId"]) for m in matches} | {
                int(m["MatchId"]) for m in completed_matches
            }

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
                post_start_at = ensure_aware_utc(match_dt + timedelta(minutes=30))

                status = (match.get("Status") or "").lower()

                logger.info(
                    "[ARK_SCHED] match_loop match_id=%s status=%s signup_close=%s match_day=%s match_time=%s",
                    match_id,
                    status,
                    str(match.get("SignupCloseUtc")),
                    str(match.get("MatchDay")),
                    str(match.get("MatchTimeUtc")),
                )

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

                if status == "locked":
                    try:
                        checkin_flag = bool(now >= checkin_at)
                        logger.info(
                            "[ARK_SCHED] locked_refresh match_id=%s now=%s checkin_at=%s show_check_in=%s",
                            match_id,
                            now.isoformat(),
                            checkin_at.isoformat(),
                            checkin_flag,
                        )
                        ok = await ensure_confirmation_message(
                            client=client,
                            match_id=match_id,
                            config=config,
                            show_check_in=checkin_flag,
                        )
                        logger.info(
                            "[ARK_SCHED] locked_refresh_result match_id=%s ok=%s",
                            match_id,
                            ok,
                        )
                    except Exception:
                        logger.exception("[ARK_SCHED] locked_refresh failed match_id=%s", match_id)

                    if now >= post_start_at:
                        await ensure_confirmation_message(
                            client=client,
                            match_id=match_id,
                            config=config,
                            show_check_in=False,
                        )
                    else:
                        await _schedule_once(
                            state=state,
                            key=_task_key(match_id, "post_start"),
                            when=post_start_at,
                            coro_factory=lambda mid=match_id: ensure_confirmation_message(
                                client=client,
                                match_id=mid,
                                config=config,
                                show_check_in=False,
                            ),
                        )

                await _run_match_reminder_dispatch(client=client, state=state, match=match)

            for match in completed_matches:
                match_id = int(match["MatchId"])
                match_dt = ensure_aware_utc(
                    resolve_ark_match_datetime(
                        match["ArkWeekendDate"],
                        match["MatchDay"],
                        match["MatchTimeUtc"],
                    )
                )
                complete_at = ensure_aware_utc(match_dt + timedelta(hours=1))

                if now >= complete_at:
                    await _complete_match_if_needed(match_id=match_id)
                    await _run_completion_update(
                        client=client,
                        match_id=match_id,
                        config=config,
                    )
                else:
                    await _schedule_once(
                        state=state,
                        key=_task_key(match_id, "complete"),
                        when=complete_at,
                        coro_factory=lambda mid=match_id: _run_completion_update(
                            client=client, match_id=mid, config=config
                        ),
                    )

            await asyncio.sleep(poll_interval_seconds)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("[ARK_SCHED] Scheduler loop failed")
            await asyncio.sleep(poll_interval_seconds)
