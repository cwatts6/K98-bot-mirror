from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
import logging
from typing import Any

import discord

from bot_config import (
    MGE_LEADERSHIP_CHANNEL_ID,
    MGE_SIGNUP_CHANNEL_ID,
    MGE_SIGNUP_MENTION_ON_CREATE,
    MGE_SIGNUP_MENTION_TEXT,
    MGE_SIMPLIFIED_FLOW_ENABLED,
)
from embed_utils import fmt_short
from mge.dal.mge_event_dal import (
    fetch_event_for_embed,
    fetch_public_signup_names,
    update_event_embed_ids,
)
from mge.dal.mge_leadership_dal import (
    fetch_leadership_embed_state,
    update_leadership_embed_state,
)
from mge.dal.mge_publish_dal import (
    fetch_awards_with_signup_user,
    fetch_event_publish_context,
    update_award_embed_ids,
)
from mge.mge_content_renderer import render_mge_content_to_embed_fields
from mge.mge_simplified_leadership_service import get_leadership_board_payload
from ui.views.mge_admin_view import MGEAdminViewDeps

logger = logging.getLogger(__name__)


# ---- Lifecycle state derivation ----
def _derive_signup_lifecycle_state(event_row: dict[str, Any]) -> str:
    """Derive signup lifecycle state from event row.

    Returns one of: "open", "closed", "finished".
    """
    status = str(event_row.get("Status") or "").strip().lower()
    if status in {"completed", "finished"}:
        return "finished"

    close_utc = event_row.get("SignupCloseUtc")
    if close_utc is not None:
        now = datetime.now(UTC)
        if isinstance(close_utc, datetime):
            close_aware = close_utc.replace(tzinfo=UTC) if close_utc.tzinfo is None else close_utc
            if now >= close_aware:
                return "closed"
        elif isinstance(close_utc, str):
            try:
                parsed = datetime.fromisoformat(close_utc)
                close_aware = parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed
                if now >= close_aware:
                    return "closed"
            except Exception:
                pass

    return "open"


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _fmt_short_number(value: Any) -> str:
    parsed = _to_int(value, default=-1)
    if parsed < 0:
        return "—"
    try:
        return fmt_short(parsed)
    except Exception:
        return f"{parsed:,}"


def resolve_public_signup_channel_id() -> tuple[int, Any, str]:
    """
    Return the public MGE signup channel id plus diagnostics.

    Returns:
        (channel_id, raw_value, source)

    - channel_id: parsed positive channel id, or 0 on failure
    - raw_value: the original configured value that was attempted
    - source: always "signup_channel"
    """
    raw_value = MGE_SIGNUP_CHANNEL_ID
    channel_id = _to_int(raw_value, default=0)
    if channel_id > 0:
        return channel_id, raw_value, "signup_channel"
    return 0, raw_value, "signup_channel"


def _build_signup_view(
    *,
    bot: discord.Client,
    event_id: int,
    signup_channel_id: int,
    lifecycle_state: str = "open",
) -> discord.ui.View | None:
    """Build persistent signup view with concrete admin deps for scheduler/embed sync.

    Returns None if the lifecycle state is closed or finished (buttons should not be shown).
    """
    if lifecycle_state in {"closed", "finished"}:
        logger.info(
            "mge_embed_signup_view_suppressed event_id=%s lifecycle_state=%s reason=buttons_hidden",
            event_id,
            lifecycle_state,
        )
        return None

    try:

        def _refresh_embed(target_event_id: int) -> None:
            # Fire-and-forget async refresh from sync/edit paths.
            async def _runner() -> None:
                await asyncio.sleep(0.5)  # avoid editing same message in same interaction cycle
                await sync_event_signup_embed(
                    bot=bot,
                    event_id=int(target_event_id),
                    signup_channel_id=int(signup_channel_id),
                    announce_everyone=False,
                    is_rehydrate=True,
                )

            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_runner())
            except RuntimeError:
                logger.warning(
                    "mge_embed_refresh_schedule_failed reason=no_running_loop event_id=%s",
                    target_event_id,
                )

        def _is_admin(interaction: discord.Interaction) -> bool:
            from core.mge_permissions import is_admin_interaction

            return bool(is_admin_interaction(interaction))

        deps = MGEAdminViewDeps(
            refresh_embed=_refresh_embed,
            is_admin=_is_admin,
        )
        if MGE_SIMPLIFIED_FLOW_ENABLED:
            from ui.views.mge_simplified_signup_view import MGESimplifiedSignupView

            view_cls = MGESimplifiedSignupView
        else:
            from ui.views.mge_signup_view import MGESignupView

            view_cls = MGESignupView
        return view_cls(event_id=int(event_id), admin_deps=deps, timeout=None)
    except Exception:
        logger.exception("mge_embed_sync_view_build_failed event_id=%s", event_id)
        return None


def _render_public_signup_list(names: list[str], limit: int = 1024) -> str:
    if not names:
        return "No signups yet."

    lines: list[str] = []
    used = 0
    for idx, name in enumerate(names):
        safe_name = str(name).replace("<", "‹").replace(">", "›")
        line = f"- {safe_name}\n"
        if used + len(line) > limit:
            remaining = len(names) - idx
            suffix = f"...and {remaining} more"
            if used + len(suffix) <= limit:
                lines.append(suffix)
            break
        lines.append(line)
        used += len(line)

    return "".join(lines).rstrip() or "No signups yet."


def _safe_text(value: Any) -> str:
    """Sanitize display text to avoid accidental mention rendering artifacts."""
    return str(value or "").replace("<", "‹").replace(">", "›").strip()


def _fit_lines_from_rows(
    rows: list[dict[str, Any]],
    make_line: Callable[[dict[str, Any]], str],
    limit: int = 1024,
) -> str:
    if not rows:
        return "None"

    out: list[str] = []
    used = 0
    total = len(rows)
    for idx, row in enumerate(rows):
        line = make_line(row)
        chunk = f"{line}\n"
        if used + len(chunk) > limit:
            remaining = total - idx
            suffix = f"...and {remaining} more"
            if used + len(suffix) <= limit:
                out.append(suffix)
            break
        out.append(line)
        used += len(chunk)
    return "\n".join(out) if out else "None"


def _score_to_millions(score: Any) -> str:
    try:
        s = int(score)
        return f"{s:,} ({s/1_000_000:.1f}m)"
    except Exception:
        return "N/A"


def build_mge_leadership_embed(
    *, event_row: dict[str, Any], board_payload: dict[str, Any]
) -> discord.Embed:
    """Build the persistent simplified leadership control-center embed."""
    counts = board_payload.get("counts", {})
    publish = board_payload.get("publish", {})
    guidance_lines = board_payload.get("guidance_lines", [])
    display_chunks = board_payload.get("display_chunks", ["None"])

    embed = discord.Embed(
        title=f"🧭 {event_row.get('EventName', 'MGE Leadership')} — Leadership Control Center",
        description="\n".join(guidance_lines),
        color=0x5865F2,
        timestamp=datetime.now(UTC),
    )
    embed.add_field(
        name="Summary",
        value=(
            f"Total: **{int(counts.get('total_signups', 0))}**\n"
            f"Roster: **{int(counts.get('roster_count', 0))}**\n"
            f"Waitlist: **{int(counts.get('waitlist_count', 0))}**\n"
            f"Rejected: **{int(counts.get('rejected_count', 0))}**"
        ),
        inline=True,
    )
    embed.add_field(
        name="Publish Status",
        value=str(publish.get("publish_status_text") or "Unknown"),
        inline=True,
    )
    embed.add_field(
        name="Variant / Mode",
        value=(
            f"{event_row.get('VariantName', 'Unknown')} / "
            f"{event_row.get('EventMode', 'controlled')}"
        ),
        inline=True,
    )

    for idx, chunk in enumerate(display_chunks, start=1):
        embed.add_field(
            name=("MGE Ordered Roster" if idx == 1 else f"MGE Ordered Roster ({idx})"),
            value=chunk,
            inline=False,
        )

    embed.set_footer(
        text="Leadership-only • Refresh is display-only and does not recalculate ranks"
    )
    return embed


def _build_leadership_view(*, event_id: int, board_payload: dict[str, Any]) -> discord.ui.View:
    from ui.views.mge_simplified_leadership_view import MGESimplifiedLeadershipView

    return MGESimplifiedLeadershipView(
        event_id=int(event_id),
        action_state=dict(board_payload.get("actions", {})),
        timeout=None,
    )


def build_mge_signup_embed(
    event_row: dict[str, Any],
    public_signup_names: list[str] | None = None,
    lifecycle_state: str = "open",
) -> discord.Embed:
    # Lifecycle-aware colour and description
    if lifecycle_state == "finished":
        color = 0x95A5A6  # grey
        description = "This MGE event has been completed."
    elif lifecycle_state == "closed":
        color = 0xFFA500  # amber
        description = "Signups are now closed. Contact leadership for changes."
    else:
        color = 0x2ECC71  # green (existing)
        description = "MGE signup is now open."

    event_name = event_row.get("EventName", "MGE Sign-Up")
    variant = event_row.get("VariantName") or "Unknown"

    embed = discord.Embed(
        title=f"🏆 {event_name} - {variant}",
        description=description,
        color=color,
        timestamp=datetime.now(UTC),
    )
    embed.set_thumbnail(url="https://i.ibb.co/fz06sLMB/mge-signup-thumbnail.png")
    embed.add_field(
        name="Variant", value=str(event_row.get("VariantName") or "Unknown"), inline=True
    )
    embed.add_field(name="Mode", value=str(event_row.get("EventMode") or "controlled"), inline=True)
    embed.add_field(name="Status", value=str(event_row.get("Status") or "signup_open"), inline=True)

    if event_row.get("StartUtc"):
        embed.add_field(name="Start", value=fmt_short(event_row["StartUtc"]), inline=True)
    if event_row.get("EndUtc"):
        embed.add_field(name="End", value=fmt_short(event_row["EndUtc"]), inline=True)
    if event_row.get("SignupCloseUtc"):
        embed.add_field(
            name="Signup Closes", value=fmt_short(event_row["SignupCloseUtc"]), inline=True
        )

    names = public_signup_names or []
    embed.add_field(name="Signup Count", value=str(len(names)), inline=True)
    embed.add_field(name="Signups (Public)", value=_render_public_signup_list(names), inline=False)

    rules_raw = str(event_row.get("RulesText") or "").strip()
    if rules_raw:
        for field_name, field_value in render_mge_content_to_embed_fields(
            rules_raw, fallback_name="Rules"
        ):
            embed.add_field(name=field_name, value=field_value, inline=False)

    embed.set_footer(text="MGE • Auto-created from calendar")
    return embed


def _mentionable_user_ids_from_rows(rows: list[dict[str, Any]]) -> list[int]:
    user_ids: list[int] = []
    seen: set[int] = set()
    for row in rows:
        try:
            uid = int(row.get("DiscordUserId") or 0)
        except Exception:
            uid = 0
        if uid > 0 and uid not in seen:
            seen.add(uid)
            user_ids.append(uid)
    return user_ids


def build_award_notifications_content(rows: list[dict[str, Any]]) -> str:
    user_ids = _mentionable_user_ids_from_rows(rows)
    if not user_ids:
        return ""
    mentions = " ".join(f"<@{uid}>" for uid in user_ids)
    return f"{mentions}\n\n📣 MGE awards have been posted/updated. Please review your placement and targets."


def build_mge_awards_embed(
    *,
    event_row: dict[str, Any],
    awarded_rows: list[dict[str, Any]],
    waitlist_rows: list[dict[str, Any]],
    publish_version: int,
    published_utc: datetime,
) -> discord.Embed:
    event_name = str(event_row.get("EventName") or f"MGE Event {event_row.get('EventId')}")
    variant = str(event_row.get("VariantName") or "Unknown")
    embed = discord.Embed(
        title=f"🏅 {event_name} — Awards",
        description=f"Variant: **{variant}**",
        color=0xF1C40F,
        timestamp=published_utc.astimezone(UTC),
    )
    embed.set_thumbnail(url="https://i.ibb.co/fVXfJRfB/mge-awards-thumbnail.png")

    # Top 3 Spotlight
    MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}
    top3 = [r for r in awarded_rows if _to_int(r.get("AwardedRank"), 99) <= 3]
    top3.sort(key=lambda r: _to_int(r.get("AwardedRank"), 99))
    if top3:
        spotlight_lines = []
        for row in top3:
            rank = _to_int(row.get("AwardedRank"), 0)
            medal = MEDALS.get(rank, f"#{rank}")
            gov = _safe_text(row.get("GovernorNameSnapshot"))
            cmd = _safe_text(row.get("RequestedCommanderName"))
            target = _fmt_short_number(row.get("TargetScore"))
            spotlight_lines.append(f"{medal} **{gov}** — *{cmd}* — Target: {target}")
        embed.add_field(
            name="🔥 Top 3",
            value="\n".join(spotlight_lines),
            inline=False,
        )

    embed.add_field(
        name=f"Awarded ({len(awarded_rows)})",
        value=_fit_lines_from_rows(
            awarded_rows,
            lambda row: (
                f"#{row.get('AwardedRank')} • "
                f"**{_safe_text(row.get('GovernorNameSnapshot'))}** • "
                f"*{_safe_text(row.get('RequestedCommanderName'))}* • "
                f"Target: {_fmt_short_number(row.get('TargetScore'))}"
            ),
            1024,
        ),
        inline=False,
    )

    if waitlist_rows:
        embed.add_field(
            name=f"Waitlist ({len(waitlist_rows)})",
            value=_fit_lines_from_rows(
                waitlist_rows,
                lambda row: (
                    f"W{row.get('WaitlistOrder')} • "
                    f"{_safe_text(row.get('GovernorNameSnapshot'))} • "
                    f"{_safe_text(row.get('RequestedCommanderName'))}"
                ),
                1024,
            ),
            inline=False,
        )

    embed.set_footer(text=f"Publish v{publish_version} • published {fmt_short(published_utc)}")
    return embed


def build_mge_award_reminders_embed(
    *,
    event_row: dict[str, Any],
    reminders_text: str,
    published_utc: datetime,
) -> discord.Embed:
    event_name = str(event_row.get("EventName") or f"MGE Event {event_row.get('EventId')}")
    variant = str(event_row.get("VariantName") or "Unknown")
    rule_mode = str(event_row.get("RuleMode") or "unknown").strip().lower() or "unknown"
    reminders_str = str(reminders_text or "").strip()
    embed = discord.Embed(
        title="📣 MGE Award Reminders",
        description="Review the reminders below before the event.",
        color=0xE67E22,
        timestamp=published_utc.astimezone(UTC),
    )
    embed.set_thumbnail(url="https://i.ibb.co/xKYp2FLg/mge-reminders-thumbnail.png")

    # Inject bold points cap from event data (not via regex/text parsing)
    try:
        cap_millions = _to_int(event_row.get("PointCapMillions"), default=-1)
    except Exception:
        cap_millions = -1
    if cap_millions > 0:
        embed.add_field(
            name="⚠️ Points Cap",
            value=f"If you are not on the list you can NOT go over **{cap_millions} million** points",
            inline=False,
        )

    # Structured content fields
    if reminders_str:
        for field_name, field_value in render_mge_content_to_embed_fields(
            reminders_str, fallback_name="Reminders"
        ):
            embed.add_field(name=field_name, value=field_value, inline=False)
    else:
        embed.add_field(name="Reminders", value="No reminders configured.", inline=False)
    embed.add_field(name="Event", value=event_name[:1024], inline=True)
    embed.add_field(name="Variant", value=variant[:1024], inline=True)
    embed.add_field(name="Rule Mode", value=rule_mode[:1024], inline=True)
    embed.set_footer(text="Leadership guidance • one-time reminders post")
    return embed


def build_publish_change_summary_lines(
    old_rows: list[dict[str, Any]],
    new_rows: list[dict[str, Any]],
) -> list[str]:
    old_map = {int(r.get("AwardId") or 0): r for r in old_rows if int(r.get("AwardId") or 0) > 0}
    new_map = {int(r.get("AwardId") or 0): r for r in new_rows if int(r.get("AwardId") or 0) > 0}

    lines: list[str] = []
    old_ids = set(old_map)
    new_ids = set(new_map)

    for aid in sorted(new_ids - old_ids):
        r = new_map[aid]
        lines.append(
            f"Added: {_safe_text(r.get('GovernorNameSnapshot'))} ({_safe_text(r.get('AwardStatus'))})"
        )

    for aid in sorted(old_ids - new_ids):
        r = old_map[aid]
        lines.append(
            f"Removed: {_safe_text(r.get('GovernorNameSnapshot'))} ({_safe_text(r.get('AwardStatus'))})"
        )

    for aid in sorted(old_ids.intersection(new_ids)):
        o = old_map[aid]
        n = new_map[aid]

        if (o.get("AwardedRank") or 0) != (n.get("AwardedRank") or 0):
            lines.append(
                f"Rank changed: {_safe_text(n.get('GovernorNameSnapshot'))} "
                f"{o.get('AwardedRank')} → {n.get('AwardedRank')}"
            )

        if (o.get("TargetScore") or 0) != (n.get("TargetScore") or 0):
            lines.append(
                f"Target changed: {_safe_text(n.get('GovernorNameSnapshot'))} "
                f"{_score_to_millions(o.get('TargetScore'))} → {_score_to_millions(n.get('TargetScore'))}"
            )

        if str(o.get("RequestedCommanderName") or "") != str(n.get("RequestedCommanderName") or ""):
            lines.append(
                f"Commander changed: {_safe_text(n.get('GovernorNameSnapshot'))} "
                f"{_safe_text(o.get('RequestedCommanderName'))} → "
                f"{_safe_text(n.get('RequestedCommanderName'))}"
            )

    return lines


async def sync_event_signup_embed(
    *,
    bot: discord.Client,
    event_id: int,
    signup_channel_id: int,
    now_utc: datetime | None = None,
    announce_everyone: bool = False,
    is_rehydrate: bool = False,
) -> bool:
    row = fetch_event_for_embed(event_id)
    if not row:
        logger.warning("mge_embed_sync_skip reason=event_not_found event_id=%s", event_id)
        return False

    # Derive lifecycle state
    lifecycle_state = _derive_signup_lifecycle_state(row)
    logger.info(
        "mge_embed_sync_lifecycle event_id=%s lifecycle_state=%s",
        event_id,
        lifecycle_state,
    )

    if MGE_SIMPLIFIED_FLOW_ENABLED:
        from mge.mge_simplified_flow_service import get_public_signup_rows

        public_signup_names = [
            str(row.get("GovernorNameSnapshot") or "Unknown")
            for row in get_public_signup_rows(event_id)
        ]
    else:
        public_signup_names = fetch_public_signup_names(event_id)

    channel = bot.get_channel(signup_channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(signup_channel_id)
        except Exception:
            logger.exception(
                "mge_embed_sync_failed reason=channel_unavailable channel_id=%s", signup_channel_id
            )
            return False

    if not isinstance(channel, discord.abc.Messageable):
        logger.error(
            "mge_embed_sync_failed reason=channel_not_messageable channel_id=%s", signup_channel_id
        )
        return False

    embed = build_mge_signup_embed(
        row, public_signup_names=public_signup_names, lifecycle_state=lifecycle_state
    )
    msg_id = row.get("SignupEmbedMessageId")
    message = None

    view = _build_signup_view(
        bot=bot,
        event_id=event_id,
        signup_channel_id=signup_channel_id,
        lifecycle_state=lifecycle_state,
    )

    # Determine if @everyone mention should be sent on first post
    should_mention = False
    if (
        not msg_id
        and not is_rehydrate
        and MGE_SIGNUP_MENTION_ON_CREATE
        and lifecycle_state == "open"
    ):
        should_mention = True
        logger.info(
            "mge_embed_sync_mention_scheduled event_id=%s mention_text=%s",
            event_id,
            MGE_SIGNUP_MENTION_TEXT,
        )

    allowed_mentions = discord.AllowedMentions(
        everyone=bool(should_mention), roles=False, users=True
    )

    if msg_id:
        try:
            message = await channel.fetch_message(int(msg_id))
            await message.edit(
                embed=embed,
                view=view,
                allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True),
            )
            view_attached = view is not None
            logger.info(
                "mge_embed_sync_updated event_id=%s message_id=%s channel_id=%s view_attached=%s lifecycle_state=%s",
                event_id,
                int(message.id),
                int(channel.id),
                view_attached,
                lifecycle_state,
            )
        except discord.NotFound:
            message = None
        except Exception:
            logger.exception(
                "mge_embed_sync_edit_failed event_id=%s message_id=%s", event_id, msg_id
            )

    if message is None:
        try:
            content = str(MGE_SIGNUP_MENTION_TEXT) if should_mention else None
            message = await channel.send(
                content=content,
                embed=embed,
                view=view,
                allowed_mentions=allowed_mentions,
            )
            view_attached = view is not None
            logger.info(
                "mge_embed_sync_created event_id=%s message_id=%s channel_id=%s view_attached=%s mention_sent=%s is_rehydrate=%s lifecycle_state=%s",
                event_id,
                int(message.id),
                int(channel.id),
                view_attached,
                should_mention,
                is_rehydrate,
                lifecycle_state,
            )
        except Exception:
            logger.exception("mge_embed_sync_send_failed event_id=%s", event_id)
            return False

    timestamp = now_utc.astimezone(UTC) if now_utc else datetime.now(UTC)
    return update_event_embed_ids(
        event_id=event_id,
        message_id=int(message.id),
        channel_id=int(channel.id),
        now_utc=timestamp,
    )


async def sync_event_awards_embed(
    *,
    bot: discord.Client,
    event_id: int,
    announce_players: bool = False,
    now_utc: datetime | None = None,
) -> bool:
    row = fetch_event_publish_context(event_id)
    if not row:
        logger.warning("mge_awards_sync_skip reason=event_not_found event_id=%s", event_id)
        return False

    rows = fetch_awards_with_signup_user(event_id)
    awarded = [r for r in rows if str(r.get("AwardStatus") or "").strip().lower() == "awarded"]
    waitlist = [r for r in rows if str(r.get("AwardStatus") or "").strip().lower() == "waitlist"]

    channel_id = int(row.get("AwardEmbedChannelId") or 0)
    if channel_id <= 0:
        logger.warning("mge_awards_sync_skip reason=no_channel event_id=%s", event_id)
        return False

    channel = bot.get_channel(channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except Exception:
            logger.exception(
                "mge_awards_sync_failed reason=channel_unavailable channel_id=%s event_id=%s",
                channel_id,
                event_id,
            )
            return False

    if not isinstance(channel, discord.abc.Messageable):
        logger.error(
            "mge_awards_sync_failed reason=channel_not_messageable channel_id=%s event_id=%s",
            channel_id,
            event_id,
        )
        return False

    old_version = _to_int(row.get("PublishVersion"), 0)
    embed = build_mge_awards_embed(
        event_row=row,
        awarded_rows=awarded,
        waitlist_rows=waitlist,
        publish_version=max(old_version, 1),
        published_utc=now_utc or datetime.now(UTC),
    )

    msg_id = _to_int(row.get("AwardEmbedMessageId"), 0)
    message = None
    allowed_mentions = discord.AllowedMentions(
        everyone=False,
        roles=False,
        users=bool(announce_players),
    )

    if msg_id > 0:
        try:
            message = await channel.fetch_message(msg_id)
            await message.edit(embed=embed, allowed_mentions=allowed_mentions)
        except discord.NotFound:
            message = None
        except Exception:
            logger.exception(
                "mge_awards_sync_edit_failed event_id=%s message_id=%s",
                event_id,
                msg_id,
            )

    if message is None:
        try:
            content = (
                build_award_notifications_content(awarded + waitlist) if announce_players else ""
            )
            message = await channel.send(
                content=content if content else None,
                embed=embed,
                allowed_mentions=allowed_mentions,
            )
        except Exception:
            logger.exception("mge_awards_sync_send_failed event_id=%s", event_id)
            return False

    timestamp = now_utc.astimezone(UTC) if now_utc else datetime.now(UTC)
    return update_award_embed_ids(
        event_id=event_id,
        message_id=int(message.id),
        channel_id=int(channel.id),
        now_utc=timestamp,
    )


async def sync_event_leadership_embed(
    *,
    bot: discord.Client,
    event_id: int,
    channel_id: int | None = None,
    now_utc: datetime | None = None,
) -> bool:
    """Create or refresh the persistent leadership-channel embed for an event."""
    event_row = fetch_event_for_embed(event_id)
    if not event_row:
        logger.warning("mge_leadership_sync_skip reason=event_not_found event_id=%s", event_id)
        return False

    resolved_channel_id = _to_int(channel_id or MGE_LEADERSHIP_CHANNEL_ID, 0)
    if resolved_channel_id <= 0:
        logger.warning("mge_leadership_sync_skip reason=no_channel event_id=%s", event_id)
        return False

    board_payload = get_leadership_board_payload(event_id)
    embed = build_mge_leadership_embed(event_row=event_row, board_payload=board_payload)
    view = _build_leadership_view(event_id=event_id, board_payload=board_payload)

    channel = bot.get_channel(resolved_channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(resolved_channel_id)
        except Exception:
            logger.exception(
                "mge_leadership_sync_failed reason=channel_unavailable channel_id=%s event_id=%s",
                resolved_channel_id,
                event_id,
            )
            return False

    if not isinstance(channel, discord.abc.Messageable):
        logger.error(
            "mge_leadership_sync_failed reason=channel_not_messageable channel_id=%s event_id=%s",
            resolved_channel_id,
            event_id,
        )
        return False

    state = fetch_leadership_embed_state(event_id)
    msg_id = _to_int(state.get("message_id"), 0)
    message = None
    if msg_id > 0:
        try:
            message = await channel.fetch_message(msg_id)
            await message.edit(
                embed=embed,
                view=view,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except discord.NotFound:
            message = None
        except Exception:
            logger.exception(
                "mge_leadership_sync_edit_failed event_id=%s message_id=%s",
                event_id,
                msg_id,
            )

    if message is None:
        try:
            message = await channel.send(
                embed=embed,
                view=view,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except Exception:
            logger.exception("mge_leadership_sync_send_failed event_id=%s", event_id)
            return False

    timestamp = now_utc.astimezone(UTC) if now_utc else datetime.now(UTC)
    return update_leadership_embed_state(
        event_id=event_id,
        message_id=int(message.id),
        channel_id=int(channel.id),
        now_utc=timestamp,
    )


async def refresh_mge_boards(
    *,
    bot: discord.Client,
    event_id: int,
    refresh_public: bool = True,
    refresh_leadership: bool = True,
    refresh_awards: bool = False,
) -> dict[str, bool]:
    """Refresh public, award, and/or leadership boards using the established routing rules."""
    results = {"public": False, "leadership": False, "awards": False}
    if refresh_public:
        channel_id, _, _ = resolve_public_signup_channel_id()
        results["public"] = await sync_event_signup_embed(
            bot=bot,
            event_id=event_id,
            signup_channel_id=channel_id,
            announce_everyone=False,
            is_rehydrate=True,
        )
    if refresh_awards:
        results["awards"] = await sync_event_awards_embed(
            bot=bot,
            event_id=event_id,
            announce_players=False,
        )
    if refresh_leadership:
        results["leadership"] = await sync_event_leadership_embed(
            bot=bot,
            event_id=event_id,
        )
    return results


def build_mge_main_embed(event: dict, public_signup_names: list[str]) -> discord.Embed:
    mode = str(event.get("EventMode", "controlled")).lower()
    title = event.get("EventName", "MGE Event")
    variant = event.get("VariantName", "Unknown")
    start_utc = event.get("StartUtc")
    end_utc = event.get("EndUtc")
    close_utc = event.get("SignupCloseUtc")
    rules_text = event.get("RulesText") or "No rules configured."

    embed = discord.Embed(title=f"🏆 {title} - {variant}", description=f"Variant: **{variant}**")
    embed.add_field(name="Start", value=fmt_short(start_utc), inline=True)
    embed.add_field(name="End", value=fmt_short(end_utc), inline=True)
    embed.add_field(name="Signup Close", value=fmt_short(close_utc), inline=True)
    embed.add_field(name="Mode", value=mode, inline=True)
    embed.add_field(name="Signup Count", value=str(len(public_signup_names)), inline=True)

    signup_block = (
        "\n".join(f"- {name}" for name in public_signup_names[:50])
        if public_signup_names
        else "No signups yet."
    )
    embed.add_field(name="Signups (Public)", value=signup_block, inline=False)
    embed.add_field(name="Rules", value=rules_text[:1024], inline=False)
    return embed
