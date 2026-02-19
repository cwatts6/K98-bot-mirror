# Commands.py
from __future__ import annotations

import asyncio
import builtins as _bi
from collections import deque
import csv
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
import io
from io import BytesIO
import json
import logging
from math import ceil
import os
import re
import signal
import sys
import tempfile
import time

# ——— Standard library ———
from typing import Any

import discord
from discord.ext import commands as ext_commands  # avoid name conflict
from discord.ui import View
from dotenv import load_dotenv

# ——— Third-party ———
import pyodbc

from admin_helpers import log_processing_result, prompt_admin_inputs
from bot_config import (
    ADMIN_USER_ID,
    GUILD_ID,
    KVK_CRYSTALTECH_CHANNEL_ID,
    KVK_EVENT_CHANNEL_ID,
    KVK_PLAYER_STATS_CHANNEL_ID,
    KVK_TARGET_CHANNEL_ID,
    LEADERSHIP_CHANNEL_ID,
    LOCATION_CHANNEL_ID,
    NOTIFY_CHANNEL_ID,
    STATS_ALERT_CHANNEL_ID,
)
from build_KVKrankings_embed import build_kvkrankings_embed
from constants import (
    CREDENTIALS_FILE,
    DATABASE,
    DEFAULT_REMINDER_TIMES,
    EXIT_CODE_FILE,
    KVK_SHEET_NAME,
    PASSWORD,
    RESTART_EXIT_CODE,
    RESTART_FLAG_PATH,
    SERVER,
    SHEET_ID,
    USAGE_TABLE,
    USERNAME,
    VALID_TYPES,
    _conn,
)
from crystaltech_di import get_crystaltech_service

try:
    # crystaltech_ui may perform imports that aren't available in certain test environments.
    # Import defensively so Commands can still be imported (tests can monkeypatch/override the views).
    from crystaltech_ui import ProgressView, SetupView
except Exception:
    ProgressView = None
    SetupView = None
    logging.getLogger(__name__).exception(
        "Optional import failed: crystaltech_ui.ProgressView/SetupView not available"
    )


from daily_KVK_overview_embed import post_or_update_daily_KVK_overview
from decoraters import (
    _actor_from_ctx,
    _has_leadership_role,
    _is_admin,
    _is_allowed_channel,
    channel_only,
    is_admin_and_notify_channel,
    is_admin_or_leadership,
    track_usage,
)
from dm_tracker_utils import (
    purge_user_from_dm_scheduled_tracker,
    purge_user_from_dm_sent_tracker,
)
from embed_my_stats import SliceButtons, build_embeds
from embed_player_profile import build_player_profile_embed
from embed_utils import (
    FailuresView,
    HistoryView,
    build_stats_embed,
    build_target_embed,
    format_event_embed,
    format_fight_embed,
    generate_summary_embed,
)
from event_cache import get_last_refreshed, is_cache_stale, refresh_event_cache
from event_embed_manager import update_live_event_embeds
from event_scheduler import dm_scheduled_tracker, dm_sent_tracker
from file_utils import append_csv_line, fetch_one_dict, read_summary_log_rows
from kvk_ui import make_kvk_targets_view
from stats_cache_helpers import load_last_kvk_map

# Provide a standard UTC alias
UTC = UTC

# ——— Local modules ———
# Direct, canonical imports for account picker functionality
from account_picker import (
    AccountPickerView,  # canonical View class
    build_unique_gov_options,  # canonical builder
)
from core.interaction_safety import (
    get_operation_lock,
    global_cmd_error_handler,
    safe_command,
    safe_defer,
)
from event_utils import serialize_event
import governor_registry
from governor_registry import (
    ConfirmRemoveView,
    ModifyGovernorView,
    RegisterGovernorView,
    get_user_main_governor_name,
    load_registry,
    save_registry,
)
from gsheet_module import (  # or run_kvk_proc_exports  # ← consolidated
    check_basic_gsheets_access,
    run_all_exports,
    run_kvk_export_test,
    run_kvk_proc_exports_with_alerts,
)
from honor_rankings_view import HonorRankingView, build_honor_rankings_embed
from kvk_history_view import KVKHistoryView
from location_importer import load_staging_and_merge, parse_output_csv
from logging_setup import CRASH_LOG_PATH, ERROR_LOG_PATH, FULL_LOG_PATH, flush_logs
from proc_config_import import run_proc_config_import_offload
from profile_cache import (
    autocomplete_choices,
    get_profile_cached,
    search_by_governor_name,
    warm_cache,
)
import registry_io
from registry_io import (
    apply_import_plan,
    build_error_csv_bytes,
    parse_csv_bytes,
    parse_xlsx_bytes,
    prepare_import_plan,
)
from rehydrate_views import save_view_tracker_with_retries as save_view_tracker_async
from reminder_task_registry import active_task_count, cancel_user_reminder_tasks
from stats_alerts.embeds.kvk import send_kvk_embed
from stats_alerts.honors import get_latest_honor_top, purge_latest_honor_scan
from stats_alerts.interface import send_stats_update_embed
from stats_alerts.kvk_meta import is_currently_kvk
from stats_module import run_stats_copy_archive
from stats_service import (
    get_registered_governor_ids_for_discord,
    get_registered_governor_names_for_discord,
    get_stats_payload,
)
from subscription_tracker import (
    get_all_subscribers,
    get_user_config,
    migrate_subscriptions,
    remove_user,
    set_user_config,
)
from target_utils import (
    _name_cache,
    autocomplete_governor_names,
    lookup_governor_id,
    run_target_lookup,
)
from ui.views.admin_views import ConfirmImportView, ConfirmRestartView, LogTailView
from ui.views.events_views import NextEventView, NextFightView
from ui.views.location_views import (
    LocationSelectView,
    ProfileLinksView,
    RefreshLocationView,
    configure_location_views,
)
from ui.views.registry_views import (
    GovernorSelectView,
    GovNameModal,
    MyRegsActionView,
    RegisterStartView,
    configure_registry_views,
)
from ui.views.stats_views import KVKRankingView
from ui.views.subscription_views import SubscriptionView
from utils import (
    get_next_events,
    get_next_fights,
    load_stat_cache,
    load_stat_row,
    normalize_governor_id,
    utcnow,
)
from versioning import versioned

logger = logging.getLogger(__name__)


def _pick_log_source(source: str):
    s = (source or "general").lower()
    if s.startswith("err"):
        return ERROR_LOG_PATH
    if s.startswith("cr"):
        return CRASH_LOG_PATH
    return FULL_LOG_PATH


ACCOUNT_ORDER = ["Main"] + [f"Alt {i}" for i in range(1, 6)] + [f"Farm {i}" for i in range(1, 11)]

# --- SHADOW GUARD (temporary; remove after diagnosis) ---
if os.getenv("DEBUG_SHADOW") == "1":
    import builtins as _bi

    for _n in ("str", "bool", "int"):
        _g = globals().get(_n)
        if _g is not None and _g is not getattr(_bi, _n):
            logger.error("[SHADOW] %s is shadowed: type=%s value=%r", _n, type(_g), _g)
# ---------------------------------------------------------

# Factory set inside register_commands() to bridge inner TargetLookupView to module scope
_TargetLookupView_factory = None  # set at runtime

load_dotenv()

# Safer construction (avoids int(None))
ALLOWED_CHANNEL_IDS = {int(cid) for cid in (NOTIFY_CHANNEL_ID, LEADERSHIP_CHANNEL_ID) if cid}

start_bot_time = datetime.now(UTC)

# --- Location refresh coordination (global, in-process) ---
_location_refresh_lock = asyncio.Lock()
_location_refresh_event = asyncio.Event()
_last_location_refresh_utc: datetime | None = None


def signal_location_refresh_complete() -> None:
    """Called by the CSV import flow when the location cache has been updated."""
    try:
        _location_refresh_event.set()
    except Exception:
        pass


def _safe_build_unique_gov_options(accounts: dict) -> list[discord.SelectOption]:
    """
    Use canonical account_picker.build_unique_gov_options; log and return an empty list on error.

    This avoids referencing any removed legacy fallback and keeps behaviour robust in production.
    """
    try:
        opts = build_unique_gov_options(accounts)
        if isinstance(opts, list):
            return opts
        # If the canonical helper returned some other iterable (unexpected), coerce to list
        logger.warning(
            "[AccountPicker] build_unique_gov_options returned non-list; coercing to list"
        )
        try:
            return list(opts) if opts is not None else []
        except Exception:
            logger.exception(
                "[AccountPicker] failed to coerce build_unique_gov_options result to list"
            )
            return []
    except Exception:
        logger.exception("[AccountPicker] build_unique_gov_options failed; returning empty options")
        return []


async def _send_find_all_to_location_channel(
    bot, *, interaction: discord.Interaction
) -> tuple[bool, str]:
    channel = bot.get_channel(LOCATION_CHANNEL_ID)
    if not channel:
        try:
            channel = await bot.fetch_channel(LOCATION_CHANNEL_ID)
        except Exception as e:
            return False, f"Could not resolve LOCATION_CHANNEL_ID: {e}"
    try:
        await channel.send("find-all")  # plain text command to your scanner bot
        return True, "OK"
    except Exception as e:
        return False, f"Failed to post 'find-all': {e}"


def _check_location_refresh_permission(interaction: discord.Interaction) -> bool:
    member = interaction.guild.get_member(interaction.user.id) if interaction.guild else None
    return bool(_is_admin(interaction.user) or _has_leadership_role(member))


def _is_location_refresh_running() -> bool:
    return _location_refresh_lock.locked()


def _is_location_refresh_rate_limited() -> tuple[bool, int]:
    if not _last_location_refresh_utc:
        return False, 0
    now = datetime.now(UTC)
    delta = (now - _last_location_refresh_utc).total_seconds()
    remain = 3600 - int(delta)
    return (remain > 0), max(0, remain)


def _mark_location_refresh_started() -> None:
    global _last_location_refresh_utc
    _last_location_refresh_utc = datetime.now(UTC)
    _location_refresh_event.clear()


async def _wait_for_location_refresh(timeout_seconds: float) -> bool:
    try:
        await asyncio.wait_for(_location_refresh_event.wait(), timeout=timeout_seconds)
        return True
    except TimeoutError:
        return False


async def _run_location_refresh_guarded(coro):
    async with _location_refresh_lock:
        await coro()


async def _notify_location_refresh_timeout(interaction: discord.Interaction) -> None:
    try:
        from bot_config import ADMIN_USER_ID

        if ADMIN_USER_ID:
            admin = await bot.fetch_user(ADMIN_USER_ID)
            await admin.send(
                "⚠️ Location refresh did not complete within 30 minutes. Please check the scanner/import."
            )
    except Exception:
        pass


async def _build_location_embed_for_target(
    target_id: int, *, refreshed: bool = False
) -> discord.Embed | None:
    try:
        warm_cache()
        p = get_profile_cached(target_id)
    except Exception:
        return None

    if not p:
        return None

    x = p.get("X")
    y = p.get("Y")
    updated = p.get("LocationUpdated")

    embed = discord.Embed(
        title="📍 Player Location (refreshed)" if refreshed else "📍 Player Location",
        description=f"**{p.get('GovernorName','Unknown')}** (`{target_id}`)",
        color=0x2ECC71 if refreshed else 0x5865F2,
    )
    embed.add_field(
        name="Coordinates",
        value=f"X **{x if x is not None else '—'}** • Y **{y if y is not None else '—'}**",
        inline=False,
    )

    if not refreshed and (x is None or y is None):
        embed.add_field(name="Note", value="No recent coordinates found", inline=False)

    if updated:
        if refreshed:
            embed.set_footer(
                text=f"Last updated: {updated} • Tip: Use the button below if it changes again"
            )
        else:
            dt = None
            if isinstance(updated, datetime):
                dt = updated if updated.tzinfo else updated.replace(tzinfo=UTC)
            else:
                try:
                    iso = str(updated).replace("Z", "+00:00")
                    dt = datetime.fromisoformat(iso)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=UTC)
                except Exception:
                    dt = None

            if dt:
                embed.timestamp = dt
                embed.set_footer(text="Last updated")
            else:
                embed.set_footer(text=f"Last updated: {updated}")

    return embed


async def _on_location_selected(
    interaction: discord.Interaction, gid: int, ephemeral: bool
) -> None:
    embed = await _build_location_embed_for_target(gid, refreshed=False)
    if not embed:
        await interaction.response.send_message(f"❌ GovernorID `{gid}` not found.", ephemeral=True)
        return

    try:
        if ephemeral:
            await interaction.response.edit_message(embed=embed, view=None)
        else:
            await interaction.channel.send(embed=embed)
            await interaction.response.edit_message(
                content=f"✅ Posted location for `{gid}`.", view=None
            )
    except discord.InteractionResponded:
        try:
            await interaction.edit_original_response(embed=embed, view=None)
        except Exception:
            pass


async def _load_last_kvk_map() -> dict[str, dict] | None:
    """
    Best-effort: read PLAYER_STATS_LAST_CACHE (JSON) off the event loop and return
    a map keyed by GovernorID (with '_meta' removed). Returns {} on any failure.
    """
    try:
        from constants import PLAYER_STATS_LAST_CACHE
        from file_utils import read_json_safe, run_blocking_in_thread
    except Exception:
        return {}

    try:
        # read_json_safe is sync; offload to thread
        data = await run_blocking_in_thread(
            lambda: read_json_safe(PLAYER_STATS_LAST_CACHE), name="read_last_kvk_cache", meta={}
        )
        if not isinstance(data, dict):
            return {}
        # copy minus _meta
        out = dict(data)
        out.pop("_meta", None)
        return out
    except Exception:
        logger.exception("[CACHE] Failed to read PLAYER_STATS_LAST_CACHE")
        return {}


def _resolve_kvk_no(c, kvk_no: int | None) -> int:
    if kvk_no and kvk_no > 0:
        return int(kvk_no)
    c.execute("""
        SELECT TOP 1 KVK_NO
        FROM dbo.KVK_Details             -- change to dbo.KVK_Details if your schema differs
        WHERE GETUTCDATE() BETWEEN KVK_REGISTRATION_DATE AND KVK_END_DATE
        ORDER BY KVK_NO DESC
    """)
    rowd = fetch_one_dict(c)
    if not rowd:
        raise ValueError("Could not resolve the current KVK window.")
    # return the first column's value (KVK_NO) using next(iter(...)) to satisfy RUF015
    return int(next(iter(rowd.values())))


async def async_load_registry():
    # run the blocking load off the event loop
    return await asyncio.to_thread(load_registry)


def atomic_json_write(path: str, data: dict | list, *, mode="w", encoding="utf-8"):
    d = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".cmdcache.", suffix=".tmp")
    try:
        with os.fdopen(fd, mode, encoding=encoding) as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)  # atomic on POSIX & Windows
    finally:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass


def _period_cutoff(period: str) -> datetime:
    # '24h', '7d', '30d'
    now = utcnow()
    if period == "24h":
        return now - timedelta(days=1)
    if period == "7d":
        return now - timedelta(days=7)
    return now - timedelta(days=30)


async def _fetch_rows(sql: str, params: tuple):
    def _run():
        with _conn() as cn:
            cur = cn.cursor()
            cur.execute(sql, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row, strict=False)) for row in cur.fetchall()]

    return await asyncio.to_thread(_run)


def _ctx_filter_sql(context: str) -> tuple[str, tuple]:
    if context == "all":
        return "", tuple()
    return " AND appcontext = ? ", (context,)


def _fmt_rate(numer: int, denom: int) -> str:
    if denom <= 0:
        return "0.0%"
    return f"{(numer/denom)*100:.1f}%"


# Autocomplete for "/usage_detail value" -> show command names when dimension=command
async def _usage_command_autocomplete(ctx: discord.AutocompleteContext):
    q = (ctx.value or "").lower().strip()
    names = [f"/{c.name}" for c in bot.application_commands]
    if q:
        names = [n for n in names if q in n.lower()]
    names = names[:25]
    try:
        OptionChoice = discord.OptionChoice
    except AttributeError:
        from discord import OptionChoice
    return [OptionChoice(name=n, value=n) for n in names]


async def _usage_detail_value_ac(ctx: discord.AutocompleteContext):
    dim = (ctx.options.get("dimension") or "").lower()
    if dim != "command":
        return []
    return await _usage_command_autocomplete(ctx)


# --- Autocomplete helper (keep at module top; used by multiple commands) ---
async def governor_name_autocomplete(ctx: discord.AutocompleteContext):
    """
    Return choices where:
      - name  -> 'GovernorName (GovernorID)'
      - value -> str(GovernorID)  (important: pass the ID to the command)
    """
    try:
        q = (ctx.value or "").strip()
        if len(q) < 2:
            return []

        try:
            OptionChoice = discord.OptionChoice  # py-cord
        except AttributeError:
            from discord import OptionChoice  # fallback

        choices = autocomplete_choices(q, limit=25)  # [(label, value), ...] value is str(gid)
        return [OptionChoice(name=label, value=value) for label, value in choices]

    except Exception:
        # Fail quietly to avoid breaking the slash UI
        return []


async def _resolve_governor_label(user_id: int, governor_id: str) -> str:
    """
    Look up a friendly label for this governor_id from governor_registry.json.
    Expected shape:
      registry[str(discord_id)]["accounts"][slot] = {"GovernorID": "...", "GovernorName": "..."}
    """
    gid_str = str(governor_id)
    try:
        registry = await asyncio.to_thread(load_registry)
        user_block = registry.get(str(user_id)) or {}
        accounts = user_block.get("accounts") or {}
        # accounts is a dict of slots -> {GovernorID, GovernorName}
        for _, rec in accounts.items():
            rec_gid = str(rec.get("GovernorID") or rec.get("governor_id") or "")
            if rec_gid == gid_str:
                name = rec.get("GovernorName") or rec.get("governor_name") or ""
                return f"{name} ({gid_str})" if name else f"Governor {gid_str}"
        return f"Governor {gid_str}"
    except Exception:
        return f"Governor help {governor_id}"


_ACTIVE_GOV_SESSIONS: dict[str, dict] = {}  # { governor_id: {"user_id": int, "expires": datetime} }
_SESSION_TTL = timedelta(minutes=10)


def _session_claim(governor_id: str, user_id: int) -> tuple[bool, str]:
    """Claim the governor for this user. If in-use by another user and not expired, block."""
    now = datetime.utcnow()
    gid = str(governor_id)
    slot = _ACTIVE_GOV_SESSIONS.get(gid)
    if slot and slot["expires"] > now and slot["user_id"] != user_id:
        return (
            False,
            "This governor is currently being edited by another user. Try again in a few minutes.",
        )
    _ACTIVE_GOV_SESSIONS[gid] = {"user_id": user_id, "expires": now + _SESSION_TTL}
    return True, ""


def _session_refresh(governor_id: str, user_id: int) -> None:
    """Refresh TTL while the same user keeps working."""
    now = datetime.utcnow()
    gid = str(governor_id)
    slot = _ACTIVE_GOV_SESSIONS.get(gid)
    if slot and slot["user_id"] == user_id:
        slot["expires"] = now + _SESSION_TTL


def _session_release(governor_id: str, user_id: int) -> None:
    """Release only if held by this user."""
    gid = str(governor_id)
    slot = _ACTIVE_GOV_SESSIONS.get(gid)
    if slot and slot["user_id"] == user_id:
        _ACTIVE_GOV_SESSIONS.pop(gid, None)


def _clone_file_to_bytes(dfile: discord.File | None) -> tuple[bytes | None, str | None]:
    """Return (bytes, filename) for a discord.File; logs size for debugging."""
    if not dfile:
        return None, None
    try:
        fp = getattr(dfile, "fp", None)
        if fp is None:
            logger.exception("[player_profile] discord.File has no 'fp'; cannot clone")
            return None, dfile.filename
        try:
            fp.seek(0)
        except Exception as e:
            logger.exception(f"[player_profile] could not seek file '{dfile.filename}': {e}")
        data = fp.read()
        size = len(data) if data else 0
        logger.info(f"[player_profile] cloned file '{dfile.filename}' to bytes: {size} bytes")
        return (data if size > 0 else None), dfile.filename
    except Exception as e:
        logger.exception(
            f"[player_profile] failed to clone file '{getattr(dfile,'filename',None)}' to bytes: {e}"
        )
        return None, getattr(dfile, "filename", None)


async def send_profile_to_channel(
    inter: discord.Interaction, gid: int, channel: discord.abc.Messageable
):
    logger.info(f"[player_profile] start gid={gid} channel={getattr(channel, 'id', '?')}")

    warm_cache()
    data = get_profile_cached(gid)
    if not data:
        msg = f"GovernorID **{gid}** not found."
        if inter.response.is_done():
            await inter.followup.send(msg, ephemeral=True)
        else:
            await inter.response.send_message(msg, ephemeral=True)
        logger.exception(f"[player_profile] not found gid={gid}")
        return

    # Build embed + files
    card_file, profile_embed, chart_file = await build_player_profile_embed(
        inter, data, card_scale=1.0
    )

    # Always reference the attachment in the embed so Discord doesn't render it separately.
    if card_file:
        try:
            profile_embed.set_image(url=f"attachment://{card_file.filename}")
        except Exception:
            pass

    # Clone bytes BEFORE sending (so we can re-use safely)
    card_bytes, card_name = _clone_file_to_bytes(card_file)
    # (Optional) don't attach chart unless you actually render it in an embed
    # chart_bytes, chart_name = _clone_file_to_bytes(chart_file)

    fresh_files: list[discord.File] = []
    if card_bytes:
        fresh_files.append(discord.File(BytesIO(card_bytes), filename=card_name))
    # If you decide to show the chart somewhere, re-enable this and also reference it in an embed.
    # if chart_bytes:
    #     fresh_files.append(discord.File(BytesIO(chart_bytes), filename=chart_name))

    # Defer ephemerally so our follow-up notice stays private ✅
    if not inter.response.is_done():
        try:
            await inter.response.defer(ephemeral=True)
        except Exception:
            pass

    # Send the primary message
    try:
        primary_msg = await channel.send(embeds=[profile_embed], files=fresh_files or None)
    except discord.Forbidden:
        logger.exception(
            "[player_profile] Forbidden to send in target channel; replying ephemerally instead."
        )
        try:
            await inter.followup.send(
                "⚠️ I don’t have permission to post in that channel. Sending your profile here instead.",
                ephemeral=True,
            )
            await inter.followup.send(
                embeds=[profile_embed], files=fresh_files or None, ephemeral=True
            )
        except Exception:
            pass
        return

    logger.info(
        f"[player_profile] sent message id={primary_msg.id}; attachments={len(primary_msg.attachments)}"
    )
    for i, att in enumerate(primary_msg.attachments):
        logger.info(
            f"[player_profile] attachment[{i}]: filename={att.filename} ct={att.content_type} url={att.url}"
        )

    # Fallback only if Discord stripped attachments (rare)
    fallback_msg = None
    if len(primary_msg.attachments) == 0 and card_bytes:
        try:
            fallback_msg = await channel.send(
                file=discord.File(BytesIO(card_bytes), filename=card_name)
            )
            logger.info(
                f"[player_profile] fallback upload id={fallback_msg.id}; attachments={len(fallback_msg.attachments)}"
            )
        except Exception as e:
            logger.exception(f"[player_profile] fallback upload failed: {e}")

    # Resolve which message to keep (prefer the one that actually has the attachment)
    target_msg = primary_msg
    if not primary_msg.attachments and fallback_msg and fallback_msg.attachments:
        try:
            await primary_msg.delete()
        except Exception as e:
            logger.exception(f"[player_profile] could not delete empty primary: {e}")
        target_msg = fallback_msg

    # Add the “Open full card” button (using the attachment URL if available)
    def resolve_card_url(msg: discord.Message | None) -> str | None:
        if not msg or not msg.attachments:
            return None
        for att in msg.attachments:
            if card_name and att.filename == card_name:
                return att.url
        for att in msg.attachments:
            if (att.content_type or "").lower().startswith("image/"):
                return att.url
        return None

    card_url = resolve_card_url(target_msg)
    view = ProfileLinksView(card_url=card_url)

    # IMPORTANT: Do NOT swap the embed image to CDN here.
    # Keeping attachment:// ensures the attachment is "consumed" by the embed and not rendered separately.

    try:
        await target_msg.edit(embeds=[profile_embed], view=view)
        logger.info(
            f"[player_profile] edited message id={target_msg.id} (button={'yes' if card_url else 'no'})"
        )
    except Exception as e:
        logger.exception(f"[player_profile] could not edit canonical message with button: {e}")

    # Quiet private ack
    try:
        await inter.followup.send(
            f"Posted profile for **{data.get('GovernorName') or gid}**.", ephemeral=True
        )
    except Exception:
        pass


configure_location_views(
    on_profile_selected=_on_location_selected,
    on_request_refresh=lambda interaction: _send_find_all_to_location_channel(
        bot, interaction=interaction
    ),
    on_wait_for_refresh=_wait_for_location_refresh,
    build_refreshed_location_embed=lambda target_id: _build_location_embed_for_target(
        target_id, refreshed=True
    ),
    check_refresh_permission=_check_location_refresh_permission,
    is_refresh_running=_is_location_refresh_running,
    is_refresh_rate_limited=_is_location_refresh_rate_limited,
    mark_refresh_started=_mark_location_refresh_started,
    run_refresh_guarded=_run_location_refresh_guarded,
    on_refresh_timeout=_notify_location_refresh_timeout,
)


configure_registry_views(
    async_load_registry=async_load_registry,
    lookup_governor_id=lookup_governor_id,
    target_lookup_view_factory=lambda matches, author_id: (
        _TargetLookupView_factory(matches, author_id) if _TargetLookupView_factory else None
    ),
    name_cache_getter=lambda: _name_cache,
    send_profile_to_channel=send_profile_to_channel,
    account_order_getter=lambda: ACCOUNT_ORDER,
)


class MyKVKStatsSelectView(discord.ui.View):
    """
    Ephemeral selector for /mykvkstats:
    - Dropdown of user's registered accounts (ordered by ACCOUNT_ORDER)
    - Buttons: Lookup Governor ID, Register New Account (reuses your existing flows)
    - On select -> posts PUBLIC stats embed(s) to the channel
    """

    def __init__(
        self, *, ctx: discord.ApplicationContext, accounts: dict, author_id: int, timeout: int = 120
    ):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.author_id = author_id
        self.accounts = accounts  # {slot: {GovernorID, GovernorName}}

        # Build options in your canonical order
        options: list[discord.SelectOption] = []
        for slot in ACCOUNT_ORDER:
            if slot in accounts:
                info = accounts[slot] or {}
                gid = str(info.get("GovernorID", "")).strip()
                gname = str(info.get("GovernorName", "")).strip()
                label = slot
                desc = f"{gname} • ID {gid}" if (gname or gid) else slot
                options.append(
                    discord.SelectOption(label=label[:100], description=desc[:100], value=gid)
                )

        self.select = discord.ui.Select(
            placeholder="Choose an account…", options=options[:25], min_values=1, max_values=1
        )
        self.select.callback = self._on_select
        self.add_item(self.select)

        # Reuse your existing flows
        self.btn_lookup = discord.ui.Button(
            label="🔎 Lookup Governor ID", style=discord.ButtonStyle.secondary
        )
        self.btn_lookup.callback = self._on_lookup
        self.add_item(self.btn_lookup)

        self.btn_register = discord.ui.Button(
            label="➕ Register New Account", style=discord.ButtonStyle.success
        )
        self.btn_register.callback = self._on_register
        self.add_item(self.btn_register)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ This menu isn’t for you.", ephemeral=True)
            return False
        return True

    async def _on_select(self, interaction: discord.Interaction):
        from embed_utils import build_stats_embed
        from utils import load_stat_row, normalize_governor_id

        # ACK the interaction quickly so Discord doesn't show "This interaction failed".
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            # Best-effort; proceed even if defer fails
            pass

        gid = normalize_governor_id(self.select.values[0])
        try:
            row = load_stat_row(gid)
        except Exception as e:
            logger.exception("[MyKVKStatsSelectView] load_stat_row failed")
            try:
                # Only notify the invoker if they're an admin; regular users don't need extra text.
                if _is_admin(interaction.user):
                    await interaction.followup.send(
                        f"❌ Couldn’t find stats for GovernorID `{gid}`: `{type(e).__name__}: {e}`",
                        ephemeral=True,
                    )
            except Exception:
                pass
            return

        if not row:
            try:
                if _is_admin(interaction.user):
                    await interaction.followup.send(
                        f"Couldn’t find stats for GovernorID `{gid}`.", ephemeral=True
                    )
            except Exception:
                pass
            return

        # Attach last_kvk if the view was provided one at init time
        try:
            lkmap = getattr(self, "_last_kvk_map", None)
            if lkmap:
                lk = lkmap.get(str(gid))
                if lk:
                    row["last_kvk"] = lk
        except Exception:
            logger.exception("[MyKVKStatsSelectView] failed attaching last_kvk to row")

        try:
            embeds, file = build_stats_embed(row, interaction.user)
            # build_stats_embed now returns (list[discord.Embed], discord.File)
        except Exception as e:
            logger.exception("[MyKVKStatsSelectView] build_stats_embed failed")
            try:
                if _is_admin(interaction.user):
                    await interaction.followup.send(
                        f"❌ Failed to build stats: `{type(e).__name__}: {e}`", ephemeral=True
                    )
            except Exception:
                pass
            return

        async def _send_to_channel(ch: discord.abc.Messageable, *, embeds_list, file_obj):
            """Attempt a single-channel send, returning True on success."""
            try:
                if file_obj is not None:
                    await ch.send(embeds=embeds_list, files=[file_obj])
                else:
                    await ch.send(embeds=embeds_list)
                return True
            except discord.Forbidden:
                logger.warning(
                    "[MyKVKStatsSelectView] missing send permissions in channel %s",
                    getattr(ch, "id", None),
                )
                return False
            except Exception as ex:
                logger.exception(
                    "[MyKVKStatsSelectView] error sending to channel %s: %s",
                    getattr(ch, "id", None),
                    ex,
                )
                return False

        def _bot_can_send_in_channel(ch: discord.abc.Messageable) -> bool:
            try:
                guild = getattr(ch, "guild", None)
                if not guild:
                    return True
                me = guild.get_member(bot.user.id) if hasattr(guild, "get_member") else None
                if me is None:
                    return True
                perms = ch.permissions_for(me)
                return perms.send_messages
            except Exception:
                return True

        # Try preferred original invoking channel first
        posted = False
        tried_channels = []
        try:
            orig_ch = getattr(self.ctx, "channel", None)
            if orig_ch and _bot_can_send_in_channel(orig_ch):
                tried_channels.append(("orig", getattr(orig_ch, "id", None)))
                posted = await _send_to_channel(orig_ch, embeds_list=embeds, file_obj=file)
        except Exception:
            posted = False

        # Fallbacks: KVK_PLAYER_STATS_CHANNEL_ID, NOTIFY_CHANNEL_ID
        if not posted:
            try:
                kvk_ch = bot.get_channel(KVK_PLAYER_STATS_CHANNEL_ID)
                if kvk_ch:
                    tried_channels.append(("kvk_channel", KVK_PLAYER_STATS_CHANNEL_ID))
                    if _bot_can_send_in_channel(kvk_ch):
                        posted = await _send_to_channel(kvk_ch, embeds_list=embeds, file_obj=file)
            except Exception:
                posted = False

        if not posted:
            try:
                notify_ch = bot.get_channel(NOTIFY_CHANNEL_ID)
                if notify_ch:
                    tried_channels.append(("notify_channel", NOTIFY_CHANNEL_ID))
                    if _bot_can_send_in_channel(notify_ch):
                        posted = await _send_to_channel(
                            notify_ch, embeds_list=embeds, file_obj=file
                        )
            except Exception:
                posted = False

        # If posted publicly -> only notify admins; regular users don't need an extra ephemeral.
        if posted:
            try:
                if _is_admin(interaction.user):
                    await interaction.followup.send(
                        "✅ Posted stats. If you can't see them in this channel, check the bot's send permissions.",
                        ephemeral=True,
                    )
                # regular users: no followup required (they see the posted stats)
            except Exception:
                pass
            return

        # If none of the public targets worked, try DM as a last resort.
        logger.warning(
            "[MyKVKStatsSelectView] failed to post public stats; tried channels=%s", tried_channels
        )

        dm_ok = False
        try:
            user_dm = interaction.user
            try:
                if file is not None:
                    await user_dm.send(embeds=embeds, files=[file])
                else:
                    await user_dm.send(embeds=embeds)
                dm_ok = True
            except discord.Forbidden:
                logger.info("[MyKVKStatsSelectView] cannot DM user %s", interaction.user.id)
            except Exception:
                logger.exception("[MyKVKStatsSelectView] failed to DM user %s", interaction.user.id)
        except Exception:
            pass

        # Only notify the invoker when they're an admin (actionable advice).
        try:
            if _is_admin(interaction.user):
                if dm_ok:
                    await interaction.followup.send(
                        "⚠️ Couldn't post publicly; sent stats to you via DM. Admins: please check channel permissions.",
                        ephemeral=True,
                    )
                else:
                    await interaction.followup.send(
                        "⚠️ Couldn't post publicly and couldn't DM the user. Admins: check bot/channel permissions.",
                        ephemeral=True,
                    )
            # regular users: no followup — they either see the public post or received the DM
        except Exception:
            pass

    async def _on_lookup(self, interaction: discord.Interaction):
        # Reuse your existing modal
        await interaction.response.send_modal(GovNameModal(author_id=self.author_id))

    async def _on_register(self, interaction: discord.Interaction):
        # Reuse your existing registration start view
        try:
            registry = await async_load_registry() or {}
        except Exception as e:
            await interaction.response.send_message(
                f"⚠️ Registry unavailable: {type(e).__name__}: {e}", ephemeral=True
            )
            return

        user_rec = registry.get(str(self.author_id)) or {}
        current = user_rec.get("accounts") or {}
        used = set(current.keys())
        free_slots = [slot for slot in ACCOUNT_ORDER if slot not in used]
        if not free_slots:
            await interaction.response.send_message(
                "All account slots are registered already. Use **/modify_registration** to change one.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            "Pick an account slot to register:",
            view=RegisterStartView(author_id=self.author_id, free_slots=free_slots),
            ephemeral=True,
        )

    async def on_timeout(self):
        for c in self.children:
            c.disabled = True
        try:
            await self.ctx.edit_original_response(view=self)
        except Exception:
            pass


def register_commands(bot_instance):
    global bot
    bot = bot_instance

    logger.info("[COMMANDS] Registering commands...")
    # Register global command error handler
    bot.add_listener(global_cmd_error_handler, "on_application_command_error")

    class TargetLookupView(View):
        def __init__(self, matches):
            super().__init__(timeout=60)
            self.matches = matches
            self.ctx = None
            self.message = None
            for match in matches:
                label = f"🎯 View KVK Targets for {match['GovernorName'][:50]}"
                button = discord.ui.Button(
                    label=label,
                    style=discord.ButtonStyle.primary,
                    custom_id=f"target_{match['GovernorID']}",
                )
                button.callback = self.make_callback(match["GovernorID"])
                self.add_item(button)

        def make_callback(self, governor_id):
            async def callback(interaction: discord.Interaction):
                await run_target_lookup(interaction, str(governor_id), ephemeral=True)

                from target_utils import get_cached_target_info, get_fallback_target_info

                logger.info(f"[BUTTON] GovernorID {governor_id} clicked by {interaction.user}")

                result = await get_cached_target_info(governor_id)

                if not result:
                    await interaction.edit_original_response(
                        content="⏳ Checking the database for additional records...",
                        embed=None,
                        view=None,
                    )
                    result = await get_fallback_target_info(governor_id)

                if result["status"] == "found":
                    embed = build_target_embed(result["data"])
                    await interaction.edit_original_response(embed=embed, view=None)
                else:
                    await interaction.edit_original_response(content=result["message"], view=None)

            return callback

        async def on_timeout(self):
            for item in self.children:
                item.disabled = True

            try:
                if self.message:
                    await self.message.edit(view=self)
            except discord.NotFound:
                # Message was deleted or expired – silently ignore
                pass
            except Exception as e:
                logger.exception(f"[VIEW TIMEOUT ERROR] {e}")

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user == self.ctx.user

        async def on_error(self, error: Exception, item, interaction: discord.Interaction) -> None:
            logger.error(f"[VIEW ERROR] {error}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"⚠️ An error occurred: {error}", ephemeral=True
                )

        async def send(self, interaction: discord.Interaction, embed: discord.Embed):
            self.ctx = interaction
            try:
                if not interaction.response.is_done():
                    # first reply: include the button
                    self.message = await interaction.response.send_message(
                        embed=embed, view=self, ephemeral=True
                    )
                else:
                    # editing the deferred/initial reply
                    self.message = await interaction.edit_original_response(embed=embed, view=self)
            except Exception:
                # last resort — a fresh ephemeral message with the button
                self.message = await interaction.followup.send(
                    embed=embed, view=self, ephemeral=True
                )

        # --- drop-in replacement ---
        class FuzzySelectView(View):
            def __init__(
                self, matches, author_id: int, *, show_targets: bool = False, timeout: float = 120
            ):
                super().__init__(timeout=timeout)
                self.matches = matches
                self.author_id = author_id
                self.show_targets = show_targets
                self.ctx = None
                self.message = None

                options = []
                for m in matches[:25]:
                    name = str(m.get("GovernorName") or "")[:75]
                    gid = str(m.get("GovernorID") or "")
                    desc = f"ID: {gid}"
                    options.append(discord.SelectOption(label=name, description=desc, value=gid))

                self.select = discord.ui.Select(
                    placeholder="Choose a governor…", options=options, min_values=1, max_values=1
                )
                self.select.callback = self.on_select
                self.add_item(self.select)

            async def on_select(self, interaction: discord.Interaction):
                if interaction.user.id != self.author_id:
                    await interaction.response.send_message(
                        "This selector isn’t for you.", ephemeral=True
                    )
                    return

                gid = str(self.select.values[0])  # keep as string for downstream .isdigit() checks

                if self.show_targets:
                    # Offer both actions for /mygovernorid
                    await interaction.response.send_message(
                        f"Governor **{gid}** selected. What would you like to do?",
                        view=TargetLookupView.PostLookupActions(
                            author_id=self.author_id, governor_id=gid
                        ),
                        ephemeral=True,
                    )
                    return

                # Register-only flow (used by My Registrations)
                registry = load_registry() or {}
                user_key = str(self.author_id)
                accounts = (registry.get(user_key) or {}).get("accounts", {}) or {}
                used_slots = set(accounts.keys())
                free_slots = [slot for slot in ACCOUNT_ORDER if slot not in used_slots]

                if not free_slots:
                    await interaction.response.send_message(
                        "All account slots are already registered. Use **Modify Registration** to change one.",
                        ephemeral=True,
                    )
                    return

                view = RegisterStartView(
                    author_id=self.author_id, free_slots=free_slots, prefill_id=gid
                )
                await interaction.response.send_message(
                    "Pick an account slot to register:", view=view, ephemeral=True
                )

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                return interaction.user.id == self.author_id

            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True
                try:
                    if self.message:
                        await self.message.edit(view=self)
                except Exception:
                    pass

            async def on_error(self, error: Exception, item, interaction: discord.Interaction):
                logger.error(f"[FUZZY SELECT VIEW ERROR] {error}")
                if interaction and not interaction.response.is_done():
                    await interaction.response.send_message(
                        "⚠️ Something went wrong.", ephemeral=True
                    )

            async def send_followup(self, interaction: discord.Interaction, embed: discord.Embed):
                self.ctx = interaction
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
                self.message = await interaction.followup.send(
                    embed=embed, view=self, ephemeral=True
                )

        # --- new helper (place right after FuzzySelectView) ---
        class PostLookupActions(View):
            def __init__(self, *, author_id: int, governor_id: str, timeout: float = 120):
                super().__init__(timeout=timeout)
                self.author_id = author_id
                self.governor_id = governor_id

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                return interaction.user.id == self.author_id

            @discord.ui.button(label="View KVK Targets", style=discord.ButtonStyle.primary)
            async def btn_targets(
                self, button: discord.ui.Button, interaction: discord.Interaction
            ):
                # Keep passing a string to avoid `.isdigit()` errors inside run_target_lookup
                await run_target_lookup(interaction, self.governor_id, ephemeral=True)

            @discord.ui.button(label="Register this Governor", style=discord.ButtonStyle.success)
            async def btn_register(
                self, button: discord.ui.Button, interaction: discord.Interaction
            ):
                registry = load_registry() or {}
                user_key = str(self.author_id)
                accounts = (registry.get(user_key) or {}).get("accounts", {}) or {}
                used_slots = set(accounts.keys())
                free_slots = [slot for slot in ACCOUNT_ORDER if slot not in used_slots]

                if not free_slots:
                    await interaction.response.send_message(
                        "All account slots are already registered. Use **Modify Registration** to change one.",
                        ephemeral=True,
                    )

                    return

                view = RegisterStartView(
                    author_id=self.author_id, free_slots=free_slots, prefill_id=self.governor_id
                )
                await interaction.response.send_message(
                    "Pick an account slot to register:", view=view, ephemeral=True
                )

    # -- expose inner class to module scope for modals & slash commands defined above --
    global _TargetLookupView_factory
    _TargetLookupView_factory = TargetLookupView.FuzzySelectView

    # === Slash Commands ===
    @bot.slash_command(
        name="summary", description="View today's file processing summary", guild_ids=[GUILD_ID]
    )
    @versioned("v1.04")
    @safe_command
    @track_usage()
    async def summary_command(ctx):
        logger.info("[COMMAND] /summary invoked")
        # Public by default (no ephemeral=True)
        try:
            await safe_defer(ctx)
        except Exception:
            # If already acknowledged elsewhere, continue gracefully
            pass

        try:
            embed = await generate_summary_embed(days=1)
            if embed:
                await ctx.interaction.edit_original_response(embed=embed)
            else:
                await ctx.interaction.edit_original_response(
                    content="⚠️ No summary log available or no files processed today."
                )
        except Exception as e:
            logger.exception("[COMMAND] /summary failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to build summary: `{type(e).__name__}: {e}`"
            )

    @bot.slash_command(
        name="weeksummary", description="View 7-day file processing summary", guild_ids=[GUILD_ID]
    )
    @versioned("v1.01")
    @safe_command
    @track_usage()
    async def weeksummary_command(ctx):

        logger.info("[COMMAND] /weeksummary invoked")

        try:
            await safe_defer(ctx)
        except Exception:
            pass  # already acknowledged elsewhere

        try:
            embed = await generate_summary_embed(days=7)
            if embed:
                await ctx.interaction.edit_original_response(embed=embed)
            else:
                await ctx.interaction.edit_original_response(
                    content="⚠️ No summary log available or no files processed in the last 7 days."
                )
        except Exception as e:
            logger.exception("[COMMAND] /weeksummary failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to build weekly summary: `{type(e).__name__}: {e}`"
            )

    @bot.slash_command(
        name="history", description="View recently processed files", guild_ids=[GUILD_ID]
    )
    @versioned("v1.02")
    @safe_command
    @track_usage()
    async def history_command(ctx, page: int = 1):

        logger.info("[COMMAND] /history invoked (page=%s) by %s", page, ctx.user)

        try:
            await safe_defer(ctx)
        except Exception:
            pass  # already acknowledged elsewhere

        # Admin gate
        if ctx.user.id != ADMIN_USER_ID:
            await ctx.interaction.edit_original_response(
                content="❌ This command is restricted to admins."
            )
            return

        log_file = "download_log.csv"
        if not os.path.exists(log_file):
            await ctx.interaction.edit_original_response(content="⚠️ No download log found.")
            return

        try:
            rows = await read_summary_log_rows(log_file)
        except Exception as e:
            logger.exception("[COMMAND] /history read_summary_log_rows failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to read log: `{type(e).__name__}: {e}`"
            )
            return

        if not rows:
            await ctx.interaction.edit_original_response(content="✅ No file history found.")
            return

        if "Timestamp" not in rows[0]:
            await ctx.interaction.edit_original_response(
                content="⚠️ Unexpected format in download log."
            )
            return

        rows = [
            row
            for row in rows
            if all(k in row for k in ("Timestamp", "Channel", "Filename", "Author", "SavedPath"))
        ]
        if not rows:
            await ctx.interaction.edit_original_response(
                content="✅ No valid file history entries found."
            )
            return

        entries_per_page = 5
        total_pages = max(1, ceil(len(rows) / entries_per_page))
        page = max(1, min(page, total_pages))

        view = HistoryView(ctx, rows, page, total_pages)

        # Send the real message as a follow-up and bind it to the view
        msg = await ctx.followup.send(embed=view.get_embed(), view=view)
        view.message = msg

        # Optionally clear the original placeholder to avoid clutter
        try:
            await ctx.interaction.edit_original_response(content="")  # or leave it as-is
        except Exception:
            pass

    @bot.slash_command(
        name="failures", description="View recently failed jobs", guild_ids=[GUILD_ID]
    )
    @versioned("v1.01")
    @safe_command
    @track_usage()
    async def failures_command(ctx, page: int = 1):

        logger.info("[COMMAND] /failures invoked (page=%s) by %s", page, ctx.user)

        try:
            await safe_defer(ctx)
        except Exception:
            pass  # already acknowledged

        # Admin gate
        if ctx.user.id != ADMIN_USER_ID:
            await ctx.interaction.edit_original_response(
                content="❌ This command is restricted to admins."
            )
            return

        log_file = "failed_log.csv"
        if not os.path.exists(log_file):
            await ctx.interaction.edit_original_response(content="⚠️ No failure log found.")
            return

        try:
            rows = await read_summary_log_rows(log_file)
        except Exception as e:
            logger.exception("[COMMAND] /failures read_summary_log_rows failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to read log: `{type(e).__name__}: {e}`"
            )
            return

        expected_keys = [
            "Timestamp",
            "Filename",
            "User",
            "Rank",
            "Seed",
            "Excel Success",
            "Archive Success",
            "SQL Success",
            "Export Success",
            "Duration (sec)",
        ]
        rows = [row for row in rows if all(k in row for k in expected_keys)]

        if not rows:
            await ctx.interaction.edit_original_response(content="✅ No failed jobs found.")
            return

        entries_per_page = 5
        total_pages = max(1, (len(rows) + entries_per_page - 1) // entries_per_page)
        page = max(1, min(page, total_pages))

        view = FailuresView(ctx, rows, page, total_pages)
        msg = await ctx.followup.send(embed=view.get_embed(), view=view)
        view.message = msg

        # Optional: clear the placeholder message to reduce clutter
        try:
            await ctx.interaction.edit_original_response(content="")
        except Exception:
            pass

    @bot.slash_command(name="ping", description="Test command", guild_ids=[GUILD_ID])
    @versioned("v1.0")
    @safe_command
    @track_usage()
    async def ping_command(ctx):
        await ctx.respond("Pong! 🏓")

    @bot.slash_command(
        name="run_sql_proc",
        description="Manually run the SQL stored procedure",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.03")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def run_sql_proc_command(ctx):

        logger.info("[COMMAND] /run_sql_proc invoked by %s", ctx.user)

        # Ack early; keep everything on the original response
        try:
            await safe_defer(ctx)
        except Exception:
            pass  # already acknowledged elsewhere

        # Hard admin gate (in addition to decorator)
        if ctx.user.id != ADMIN_USER_ID:
            await ctx.interaction.edit_original_response(
                content="❌ This command is restricted to admins."
            )
            return

        # Let the user know we’ve started
        try:
            await ctx.interaction.edit_original_response(
                content="⏳ Starting manual SQL run… collecting inputs."
            )
        except Exception:
            pass

        # Collect rank/seed
        try:
            rank, seed = await prompt_admin_inputs(bot, ctx.user, ctx.user.id)
        except Exception as e:
            logger.exception("[COMMAND] /run_sql_proc prompt_admin_inputs failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Could not collect inputs: `{type(e).__name__}: {e}`"
            )
            return

        # Execute the job
        start_time = datetime.utcnow()
        try:
            await ctx.interaction.edit_original_response(
                content=f"🏗️ Running SQL pipeline with rank `{rank}` and seed `{seed}`…"
            )
            success, log, steps = await run_stats_copy_archive(rank, seed)
        except Exception as e:
            logger.exception("[COMMAND] /run_sql_proc run_stats_copy_archive crashed")
            await ctx.interaction.edit_original_response(
                content=f"💥 SQL run crashed: `{type(e).__name__}: {e}`"
            )
            return

        # Post-process + audit/embed to notify channel
        try:
            await log_processing_result(
                bot=bot,
                notify_channel_id=NOTIFY_CHANNEL_ID,
                user=ctx.user,
                message=None,
                filename="Manual SQL Run",
                rank=rank,
                seed=seed,
                success_excel=(steps or {}).get("excel"),
                success_archive=(steps or {}).get("archive"),
                success_sql=(steps or {}).get("sql"),
                success_export=None,  # intentionally skipped here
                success_proc_import=None,  # intentionally skipped here
                combined_log=log,
                start_time=start_time,
                summary_log_path="summary_log.csv",
            )
        except Exception:
            logger.exception("[COMMAND] /run_sql_proc log_processing_result failed")
            # Fall through and still inform the invoker below

        # Summarize back to the invoker
        def mark(ok):
            return "✅" if ok else "❌"

        excel_ok = (steps or {}).get("excel", False)
        archive_ok = (steps or {}).get("archive", False)
        sql_ok = (steps or {}).get("sql", False)

        summary = (
            f"**Manual SQL Run Complete**\n"
            f"- Excel: {mark(excel_ok)}\n"
            f"- Archive: {mark(archive_ok)}\n"
            f"- SQL: {mark(sql_ok)}\n"
            f"\nDetailed results have been posted to <#{NOTIFY_CHANNEL_ID}>."
        )

        await ctx.interaction.edit_original_response(
            content=summary if success else f"⚠️ Completed with issues:\n{summary}"
        )

    @bot.slash_command(
        name="run_gsheets_export",
        description="Manually trigger Google Sheets export",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.04")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def run_gsheets_export_command(ctx):
        logger.info("[COMMAND] /run_gsheets_export invoked by %s", ctx.user)

        # Acknowledge first
        try:
            await safe_defer(ctx)
        except Exception:
            pass  # already acked

        # Extra admin gate (in addition to decorator)
        if ctx.user.id != ADMIN_USER_ID:
            await ctx.interaction.edit_original_response(
                content="❌ This command is restricted to admins."
            )
            return

        # Let caller know we're starting
        try:
            await ctx.interaction.edit_original_response(
                content="⏳ Starting Google Sheets export…"
            )
        except Exception:
            pass

        notify_channel = bot.get_channel(NOTIFY_CHANNEL_ID)

        # Run export in a thread (blocking IO)
        start_ts = datetime.utcnow()
        try:
            success, log = await asyncio.to_thread(
                run_all_exports,
                SERVER,
                DATABASE,
                USERNAME,
                PASSWORD,
                CREDENTIALS_FILE,
                notify_channel=notify_channel,
                bot_loop=bot.loop,
            )
        except Exception as e:
            logger.exception("[COMMAND] /run_gsheets_export crashed")
            await ctx.interaction.edit_original_response(
                content=f"💥 Export failed unexpectedly: `{type(e).__name__}: {e}`"
            )
            return

        # Build result embed
        duration_s = (datetime.utcnow() - start_ts).total_seconds()

        # Normalize log output: accept either list[str] or single string
        if isinstance(log, list):
            # use a descriptive iterator name to avoid E741
            raw_text = "\n".join(str(line) for line in log).strip()
        else:
            raw_text = (log or "").strip()

        # Present logs in a code block if present; mark when truncated
        if raw_text:
            max_len = 3900  # leave room for code fences
            clipped = raw_text[:max_len]
            if len(raw_text) > max_len:
                clipped += "\n…(truncated)"
            desc = f"```{clipped}```"
        else:
            if success:
                desc = (
                    "All configured exports completed successfully.\n\n"
                    f"Details have been posted to {notify_channel.mention}."
                )
            else:
                desc = (
                    "The export appears to have failed, but no log output was captured. "
                    "Please check the bot logs and the notify channel."
                )

        title = "📊 Sheets Export Complete" if success else "❌ Sheets Export Failed"
        color = 0x2ECC71 if success else 0xE74C3C

        embed = discord.Embed(title=title, description=desc, color=color)
        embed.add_field(name="Triggered by", value=f"<@{ctx.user.id}>", inline=True)
        embed.add_field(name="Duration", value=f"{duration_s:.1f}s", inline=True)
        if notify_channel:
            embed.add_field(name="Notify channel", value=notify_channel.mention, inline=True)

        embed.set_footer(text=f"{SERVER} · {DATABASE}")
        embed.timestamp = datetime.utcnow()

        await ctx.interaction.edit_original_response(content=None, embed=embed)

    @bot.slash_command(
        name="test_kvk_export",
        description="🧪 Admin: Test KVK Google Sheets export without performing an import",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def test_kvk_export(
        ctx,
        kvk_no: int = 0,
        sheet_name: str = None,
        create_primary: bool = True,
        export_pass4: bool = True,
        export_altar: bool = True,
        export_pass7: bool = True,
    ):
        """
        Admin-only command to run the export pipeline for a KVK without requiring an import.
        Returns structured metadata about which spreadsheets/tabs would be created/written.
        """
        logger.info("[COMMAND] /test_kvk_export invoked by %s (kvk_no=%s)", ctx.user, kvk_no)

        # Single ack (ephemeral)
        try:
            await safe_defer(ctx, ephemeral=True)
        except Exception:
            pass

        # Extra admin gate (decorator already limits usage)
        if ctx.user.id != ADMIN_USER_ID:
            await ctx.interaction.edit_original_response(
                content="❌ This command is restricted to admins."
            )
            return

        # Resolve current KVK if not provided (reuse existing helper)
        if kvk_no == 0:
            try:
                with _conn() as cn, cn.cursor() as c:
                    kvk_no = _resolve_kvk_no(c, None)
            except Exception:
                # Fallback to SQL resolution as used in other commands
                try:
                    with _conn() as cn, cn.cursor() as c:
                        kvk_no = _resolve_kvk_no(c, kvk_no)
                except Exception as e:
                    logger.exception("[COMMAND] /test_kvk_export could not resolve KVK")
                    await ctx.interaction.edit_original_response(
                        content=f"❌ Could not resolve the current KVK window: `{type(e).__name__}: {e}`"
                    )
                    return

        sheet_name = (sheet_name or KVK_SHEET_NAME).strip() or KVK_SHEET_NAME

        # Let the invoker know we're starting
        try:
            await ctx.interaction.edit_original_response(
                content=f"⏳ Running KVK export TEST for KVK `{kvk_no}` (primary sheet: **{sheet_name}**)…"
            )
        except Exception:
            pass

        start_ts = datetime.utcnow()

        try:
            # Run the test export in a thread (blocking IO / network)
            meta = await asyncio.to_thread(
                run_kvk_export_test,
                SERVER,
                DATABASE,
                USERNAME,
                PASSWORD,
                int(kvk_no),
                sheet_name,
                CREDENTIALS_FILE,
                create_primary,
                export_pass4,
                export_altar,
                export_pass7,
            )
        except Exception as e:
            logger.exception("[COMMAND] /test_kvk_export crashed")
            await ctx.interaction.edit_original_response(
                content=f"💥 Test export failed unexpectedly: `{type(e).__name__}: {e}`"
            )
            return

        dur = (datetime.utcnow() - start_ts).total_seconds()

        # Build a helpful embed summarising the metadata returned by run_kvk_export_test()
        try:
            embed = discord.Embed(
                title=f"🧪 KVK Export Test — KVK {kvk_no}",
                description=f"Test run completed in `{dur:.1f}s`.",
                color=discord.Color.green(),
            )

            embed.add_field(name="KVK", value=str(kvk_no), inline=True)
            embed.add_field(name="Primary sheet", value=sheet_name, inline=True)
            embed.add_field(name="Triggered by", value=f"<@{ctx.user.id}>", inline=True)

            # Primary metadata (if present)
            primary = meta.get("primary") if isinstance(meta, dict) else None
            if primary:
                p_written = primary.get("written_tabs", []) or []
                p_skipped = primary.get("skipped_tabs", []) or []
                p_url = primary.get("spreadsheet_url")
                lines = []
                if p_written:
                    lines.append(f"Written tabs: {len(p_written)}")
                if p_skipped:
                    lines.append(f"Empty tabs (created empty): {len(p_skipped)}")
                if p_url:
                    lines.append(f"[Open primary sheet]({p_url})")
                embed.add_field(
                    name="Primary result",
                    value="\n".join(lines) or "No primary metadata",
                    inline=False,
                )

            # Additional spreadsheets (PASS4 / 1st Altar / PASS7)
            additional = meta.get("additional") if isinstance(meta, dict) else {}
            if additional:
                for ss_name, ss_meta in additional.items():
                    created = ss_meta.get("created", False)
                    written = ss_meta.get("written_tabs", []) or []
                    skipped = ss_meta.get("skipped_tabs", []) or []
                    url = ss_meta.get("spreadsheet_url") or ""
                    status = (
                        "✅ Created"
                        if created
                        else "ℹ️ Skipped" if ss_meta.get("reason") == "no_data" else "❌ Failed"
                    )
                    value_lines = [status]
                    if written:
                        value_lines.append(f"Written: {len(written)}")
                    if skipped:
                        value_lines.append(f"Skipped: {len(skipped)}")
                    if url:
                        value_lines.append(f"[Open]({url})")
                    embed.add_field(name=ss_name, value="\n".join(value_lines), inline=False)
        except Exception:
            # Fallback summary if embed construction fails
            try:
                await ctx.interaction.edit_original_response(
                    content=f"✅ Test export finished in `{dur:.1f}s`. Inspect logs for details."
                )
            except Exception:
                pass
            return

        try:
            await ctx.interaction.edit_original_response(content=None, embed=embed)
        except Exception:
            try:
                await ctx.followup.send(embed=embed, ephemeral=True)
            except Exception:
                logger.exception("[COMMAND] /test_kvk_export failed to send result embed")

    @bot.slash_command(
        name="restart_bot", description="Forcefully restart the bot", guild_ids=[GUILD_ID]
    )
    @versioned("v1.06")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def restart_bot_command(ctx):
        view = ConfirmRestartView(ctx, bot=bot, notify_channel_id=NOTIFY_CHANNEL_ID)
        await ctx.respond("⚠️ Are you sure you want to restart the bot?", view=view, ephemeral=True)

        # Cache the original ephemeral message so the view can disable itself
        try:
            view.message = await ctx.interaction.original_response()
        except Exception:
            pass

        try:
            await asyncio.wait_for(view.confirmed.wait(), timeout=30)
        except TimeoutError:
            # Use followup after initial respond
            await view._try_disable_ui()
            await ctx.followup.send(
                "⏱️ Restart cancelled – no confirmation received.", ephemeral=True
            )
            return

        if view.cancelled:
            await ctx.followup.send("✅ Restart request cancelled.", ephemeral=True)
            return

        logger.info("[RESTART] Confirmation received – proceeding with restart.")
        await asyncio.sleep(2)

        restart_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": ctx.user.id,
            "reason": "slash_restart",
        }

        try:
            with open(RESTART_FLAG_PATH, "w", encoding="utf-8") as f:
                json.dump(restart_data, f)
                f.flush()
                os.fsync(f.fileno())
            logger.info("[RESTART] Restart flag file written")

            try:
                with open(RESTART_FLAG_PATH, encoding="utf-8") as f:
                    contents = f.read().strip()
                logger.info(f"[RESTART] Restart flag content: {contents}")
            except Exception as e:
                logger.exception(f"[RESTART] Failed to read back restart flag: {e}")

            ws_code, ws_reason, ws_time = "", "", ""
            if os.path.exists(".last_disconnect_reason"):
                try:
                    with open(".last_disconnect_reason", encoding="utf-8") as f:
                        ws_info = json.load(f)
                        ws_code = str(ws_info.get("code", ""))
                        ws_reason = ws_info.get("reason", "")
                        ws_time = ws_info.get("timestamp", "")
                except Exception as e:
                    logger.exception(
                        f"[RESTART] Failed to read .last_disconnect_reason for CSV: {e}"
                    )

            await append_csv_line(
                "restart_log.csv",
                [
                    restart_data["timestamp"],
                    restart_data["reason"],
                    restart_data["user_id"],
                    "success",
                    ws_code,
                    ws_reason,
                    ws_time,
                ],
            )

        except Exception as e:
            logger.exception(f"[RESTART] Failed to write restart flag or log: {e}")

        try:
            logger.info("[RESTART] Restarting bot via slash command.")
            logger.info(f"[RESTART] sys.executable = {sys.executable}")
            logger.info(f"[RESTART] sys.argv = {sys.argv}")

            # Followup (not respond) after the initial message
            await ctx.followup.send(
                "✅ Restarting now... This may take a few seconds.", ephemeral=True
            )
            await asyncio.sleep(3)

            flush_logs()

            with open(EXIT_CODE_FILE, "w", encoding="utf-8") as f:
                f.write(str(RESTART_EXIT_CODE))

            flush_logs()
            await asyncio.sleep(1)
            print("[RESTART] Restart flag written – sleeping before SIGTERM")
            print("[RESTART] Sending SIGTERM to self now.")
            os.kill(os.getpid(), signal.SIGTERM)

        except Exception as e:
            logger.exception(f"[RESTART ERROR] Restart attempt failed: {e}")
            try:
                await ctx.followup.send(
                    embed=discord.Embed(
                        title="❌ Restart Failed",
                        description=f"Bot restart failed: `{type(e).__name__}: {e}`",
                        color=0xE74C3C,
                    ),
                    ephemeral=True,
                )
            except Exception:
                pass

    # Commands.py — replace the whole function body of force_restart with this slimmer flow
    @bot.slash_command(
        name="force_restart",
        description="Force a restart via the watchdog mechanism (admin only).",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.07")
    @safe_command
    @is_admin_and_notify_channel()
    @ext_commands.has_permissions(administrator=True)
    @track_usage()
    async def force_restart(ctx):
        logger.info("[COMMAND] /force_restart invoked by %s", ctx.user)

        # 1) Ack ASAP (best-effort)
        try:
            await safe_defer(ctx, ephemeral=True)
        except Exception:
            pass

        # 2) Tell the user ONCE, before we begin teardown racing the gateway
        try:
            await ctx.interaction.edit_original_response(content="🔄 Restarting via watchdog…")
        except Exception:
            pass  # If we already disconnected, it's fine.

        # 3) Schedule the actual restart; DO NOT await long-running work here
        async def _do_restart():
            try:
                # Write restart flag + audit quickly
                restart_flag = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "reason": "slash_force_restart",
                    "user_id": str(ctx.user.id),
                }
                with open(RESTART_FLAG_PATH, "w", encoding="utf-8") as f:
                    json.dump(restart_flag, f)
                    f.flush()
                    os.fsync(f.fileno())
                logger.info("[RESTART] Flag written")

                # Optional CSV audit (best-effort)
                try:
                    await append_csv_line(
                        "restart_log.csv",
                        [
                            restart_flag["timestamp"],
                            restart_flag["reason"],
                            restart_flag["user_id"],
                            "success",
                            "",
                            "",
                            "",
                        ],
                    )
                except Exception:
                    pass

                # Exit code file for watchdog
                try:
                    with open(EXIT_CODE_FILE, "w", encoding="utf-8") as f:
                        f.write(str(RESTART_EXIT_CODE))
                except Exception:
                    pass

                # Small delay to let the response leave the socket
                await asyncio.sleep(0.25)
            finally:
                # Trigger graceful shutdown via SIGTERM (your handler will run)
                logger.info("[RESTART] Sending SIGTERM to self")
                try:
                    os.kill(os.getpid(), signal.SIGTERM)
                except Exception:
                    # Windows can still deliver SIGTERM; if it failed, fall back:
                    os._exit(RESTART_EXIT_CODE)

        asyncio.create_task(_do_restart())
        # IMPORTANT: return immediately so we don’t block the loop
        return

    @bot.slash_command(
        name="resync_commands",
        description="Force resync of slash commands and update command cache",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.09")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def resync_commands(ctx):
        async with get_operation_lock("resync"):
            await safe_defer(ctx, ephemeral=True)

            # === Sync commands with timeout
            try:
                await asyncio.wait_for(bot.sync_commands(guild_ids=[GUILD_ID]), timeout=5.0)
                logger.info("[COMMAND SYNC] Slash commands successfully resynced.")
            except TimeoutError:
                logger.exception("[COMMAND SYNC] Timed out during sync — skipping.")
                await ctx.interaction.edit_original_response(
                    embed=discord.Embed(
                        title="⚠️ Sync Timed Out",
                        description="The command sync request took too long and was skipped.",
                        color=0xF39C12,
                    )
                )
                return
            except Exception as e:
                logger.exception("[COMMAND SYNC] Resync failed")
                await ctx.interaction.edit_original_response(
                    embed=discord.Embed(
                        title="❌ Sync Failed",
                        description=f"```{type(e).__name__}: {e}```",
                        color=0xE74C3C,
                    )
                )
                return

            # === Update command_cache.json (atomically)
            try:
                # Load existing cache (if present)
                try:
                    with open("command_cache.json", encoding="utf-8") as f:
                        old_cache = {cmd["name"]: cmd for cmd in json.load(f)}
                except FileNotFoundError:
                    old_cache = {}
                except Exception as e:
                    logger.warning(
                        "[COMMAND SYNC] Could not read existing command_cache.json: %s", e
                    )
                    old_cache = {}

                new_cache = []
                updated = []

                for command in bot.application_commands:
                    name = command.name
                    version = getattr(command.callback, "__version__", "N/A")
                    description = command.description or ""
                    cached_version = old_cache.get(name, {}).get("version")

                    entry = {
                        "name": name,
                        "version": version,
                        "description": description,
                        "admin_only": True,  # keep as-is; refine later if we introspect decorators
                    }
                    new_cache.append(entry)

                    if cached_version != version:
                        updated.append(f"/{name} → `{cached_version}` ➜ `{version}`")

                # Atomic write helper (scoped here so this block is self-contained)
                def _atomic_json_write(path: str, data):
                    import json
                    import os
                    import tempfile

                    d = os.path.dirname(path) or "."
                    fd, tmp = tempfile.mkstemp(dir=d, prefix=".cmdcache.", suffix=".tmp")
                    try:
                        with os.fdopen(fd, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2)
                            f.flush()
                            os.fsync(f.fileno())
                        os.replace(tmp, path)  # atomic on POSIX + Windows
                    finally:
                        try:
                            if os.path.exists(tmp):
                                os.remove(tmp)
                        except Exception:
                            pass

                # Write atomically
                _atomic_json_write("command_cache.json", new_cache)

                summary = "\n".join(updated) if updated else "✅ No changes to cached versions."
                # Keep under embed description limit
                if len(summary) > 4000:
                    summary = summary[:3990] + "…"

                await ctx.interaction.edit_original_response(
                    embed=discord.Embed(
                        title="✅ Slash Commands Resynced & Cache Updated",
                        description=summary,
                        color=0x2ECC71,
                    )
                )

            except Exception as e:
                logger.exception("[COMMAND SYNC] Unexpected failure building/writing cache")
                await ctx.interaction.edit_original_response(
                    embed=discord.Embed(
                        title="❌ Cache Update Failed",
                        description=f"```{type(e).__name__}: {e}```",
                        color=0xE74C3C,
                    )
                )

    @bot.slash_command(
        name="show_command_versions",
        description="List all currently loaded slash commands with their versions",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.03")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def show_command_versions(ctx):

        await safe_defer(ctx, ephemeral=True)

        try:
            # Sort for stable output
            cmds = sorted(bot.application_commands, key=lambda c: c.name.lower())

            embed = discord.Embed(
                title="📦 Loaded Slash Command Versions",
                description="Showing all commands and their current version tags.",
                color=0x3498DB,
            )

            # Discord embeds allow max 25 fields. If we have more, use a description list.
            if len(cmds) <= 25:
                for command in cmds:
                    version = getattr(command.callback, "__version__", "N/A")
                    embed.add_field(
                        name=f"/{command.name}", value=f"Version: `{version}`", inline=False
                    )
            else:
                lines = []
                for command in cmds:
                    version = getattr(command.callback, "__version__", "N/A")
                    lines.append(f"/{command.name} — `{version}`")
                text = "\n".join(lines)
                # Keep under embed description limits (~4096 chars)
                if len(text) > 3900:
                    text = text[:3890] + "…"
                embed.description = (
                    f"Showing all commands and their current version tags.\n\n{text}"
                )

            await ctx.interaction.edit_original_response(embed=embed)

        except Exception as e:
            logger.exception("[COMMAND] /show_command_versions failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to build command version list: `{type(e).__name__}: {e}`"
            )

    @bot.slash_command(
        name="validate_command_cache",
        description="Check for mismatched or missing entries in command_cache.json",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.04")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def validate_command_cache(ctx):

        await safe_defer(ctx, ephemeral=True)

        # Load cache
        try:
            with open("command_cache.json", encoding="utf-8") as f:
                raw = json.load(f)
                cache = {entry["name"]: entry.get("version", "N/A") for entry in raw}
        except Exception as e:
            logger.exception("[COMMAND] /validate_command_cache load failed")
            await ctx.interaction.edit_original_response(
                embed=discord.Embed(
                    title="❌ Failed to Load Cache",
                    description=f"```{type(e).__name__}: {e}```",
                    color=0xE74C3C,
                )
            )
            return

        # Build checks
        loaded_cmds = sorted(bot.application_commands, key=lambda c: c.name.lower())
        loaded_names = {c.name for c in loaded_cmds}
        cache_names = set(cache.keys())

        issues = []

        # Missing or mismatched
        for command in loaded_cmds:
            name = command.name
            version = getattr(command.callback, "__version__", "N/A")
            cached = cache.get(name)
            if cached is None:
                issues.append(f"➕ `/{name}` is **missing** from cache (code=`{version}`)")
            elif cached != version:
                issues.append(f"🔁 `/{name}` version mismatch: cache=`{cached}`, code=`{version}`")

        # Stale entries (in cache but not loaded anymore)
        stale = sorted(cache_names - loaded_names)
        for name in stale:
            issues.append(f"➖ `/{name}` is in cache but not currently loaded")

        # Build response
        if issues:
            # Keep under embed description limit (~4096)
            full = "\n".join(issues)
            if len(full) > 3900:
                clipped = []
                total = 0
                for line in issues:
                    if total + len(line) + 1 > 3900:
                        break
                    clipped.append(line)
                    total += len(line) + 1
                remaining = len(issues) - len(clipped)
                full = "\n".join(clipped) + (f"\n…and {remaining} more." if remaining > 0 else "")
            embed = discord.Embed(
                title="🧩 Command Cache Validation", description=full, color=0xF1C40F
            )
        else:
            embed = discord.Embed(
                title="🧩 Command Cache Validation",
                description="✅ All commands are correctly versioned and cached.",
                color=0x2ECC71,
            )

        await ctx.interaction.edit_original_response(embed=embed)

    @bot.slash_command(
        name="view_restart_log", description="View recent bot restarts", guild_ids=[GUILD_ID]
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def view_restart_log(ctx, count: int = 5):
        await safe_defer(ctx, ephemeral=True)

        log_file = "restart_log.csv"
        if not os.path.exists(log_file):
            await ctx.interaction.edit_original_response(content="⚠️ No restart log found.")
            return

        # Clamp count to keep the embed manageable
        count = max(1, min(int(count or 5), 20))

        try:
            with open(log_file, encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            if not rows:
                await ctx.interaction.edit_original_response(
                    content="✅ No restart events have been recorded yet."
                )
                return

            # Take last N rows (most recent assumed at end of file)
            selected = rows[-count:]

            # Pick color from the most recent selected entry
            last_status = (selected[-1].get("Status", "") or "").lower()
            if "crash" in last_status:
                embed_color = discord.Color.red()
            elif "success" in last_status:
                embed_color = discord.Color.green()
            else:
                embed_color = discord.Color.orange()

            embed = discord.Embed(title="📜 Recent Bot Restarts", color=embed_color)

            # Add fields newest → oldest
            for row in reversed(selected):
                ts = row.get("Timestamp", "—")
                rsn = row.get("Reason", "—")
                uid = row.get("UserId", row.get("user_id", "SYSTEM"))  # support both header styles
                stat = row.get("Status", "—")

                ws_code = row.get("WS Code", row.get("ws_code", "")) or ""
                ws_desc = row.get("WS Reason", row.get("ws_reason", "")) or ""
                ws_time = row.get("WS Time", row.get("ws_time", "")) or ""

                trigger = f"<@{uid}>" if uid and uid != "SYSTEM" else "🛠️ System"
                reason_label = (rsn or "").replace("_", " ").capitalize()

                desc = (
                    f"👤 **Triggered By:** {trigger}\n"
                    f"📄 **Reason:** `{reason_label}`\n"
                    f"📌 **Status:** `{stat}`"
                )
                if ws_code and ws_desc:
                    desc += f"\n🔌 **Last Disconnect:** `{ws_code}` – {ws_desc}"
                    if ws_time:
                        desc += f"\n🕒 {ws_time}"

                embed.add_field(name=f"🕒 {ts}", value=desc, inline=False)

            embed.set_footer(text=f"Showing last {len(selected)} restarts")
            await ctx.interaction.edit_original_response(content=None, embed=embed)

        except Exception as e:
            logger.exception("[RESTART_LOG] Failed to read or parse restart log.")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to load restart log: `{type(e).__name__}: {e}`"
            )

    @bot.slash_command(
        name="import_proc_config",
        description="Manually run the ProcConfig import (admin only)",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.03")
    @safe_command
    @is_admin_and_notify_channel()
    @ext_commands.has_permissions(administrator=True)
    @track_usage()
    async def import_proc_config(ctx):
        """
        Run ProcConfig import from Discord command.
        Uses run_proc_config_import_offload to perform the heavy work in a subprocess/thread
        so we don't block the bot's event loop.
        """
        start_ts = None
        dur = None
        try:
            # Optionally defer the interaction if long-running
            try:
                await safe_defer(ctx, ephemeral=True)
            except Exception:
                # safe_defer may not be desired in all contexts; proceed if it fails
                logger.debug("safe_defer failed or skipped", exc_info=False)

            start_ts = datetime.utcnow()

            # Let the caller see progress
            try:
                await ctx.interaction.edit_original_response(
                    content="⏳ Starting ProcConfig import…"
                )
            except Exception:
                # If editing the original response fails, continue — we'll still try to send final status
                logger.debug("Could not send start progress message", exc_info=False)

            try:
                # Offload the synchronous import to a process/thread to avoid blocking
                success, report = await run_proc_config_import_offload(
                    dry_run=False, prefer_process=True
                )
            except Exception as e:
                logger.exception("[COMMAND] /import_proc_config crashed")
                # Try to inform the user of the unexpected crash
                try:
                    await ctx.interaction.edit_original_response(
                        content=f"💥 Import failed unexpectedly: `{type(e).__name__}: {e}`"
                    )
                except Exception:
                    logger.debug("Failed to notify user about unexpected crash", exc_info=False)
                return

            dur = (datetime.utcnow() - start_ts).total_seconds() if start_ts else None

            if success:
                logger.info(
                    "[COMMAND] /import_proc_config completed successfully in %.2fs", dur or 0.0
                )
                try:
                    await ctx.interaction.edit_original_response(
                        content=f"✅ ProcConfig import completed successfully in **{(dur or 0.0):.1f}s**."
                    )
                except Exception:
                    logger.debug("Failed to send success response to user", exc_info=False)
            else:
                logger.error(
                    "[COMMAND] /import_proc_config reported failure after %.2fs", dur or 0.0
                )

                # Ensure report is a dict before accessing keys
                report = report or {}
                errors = report.get("errors") or []
                short_err = "; ".join(errors[:3]) or "Unknown error"
                persisted = report.get("persisted_to") or report.get("manifest_path")
                msg = f"❌ ProcConfig import failed: {short_err} in **{(dur or 0.0):.1f}s**"
                if persisted:
                    msg += f" (report: {persisted})"

                try:
                    # edit_original_response typically doesn't accept ephemeral; omit it here
                    await ctx.interaction.edit_original_response(content=msg)
                except Exception:
                    # If editing the original response fails, try sending a followup or log
                    logger.debug(
                        "Failed to send failure response to user via edit_original_response",
                        exc_info=False,
                    )
                    try:
                        await ctx.send(msg, ephemeral=True)
                    except Exception:
                        logger.debug(
                            "Also failed to send failure response via ctx.send", exc_info=False
                        )

        except Exception as e:
            # Make sure we don't crash attempting to reference dur/start_ts
            logger.exception("import_proc_config handler failed: %s", e)
            dur_str = (
                f"{(datetime.utcnow() - start_ts).total_seconds():.1f}s" if start_ts else "unknown"
            )
            try:
                await ctx.interaction.edit_original_response(
                    content=(
                        "❌ Unexpected error starting ProcConfig import. "
                        f"Duration **{dur_str}**. Please check the logs for details."
                    )
                )
            except Exception:
                logger.debug("Failed to send failure response to user", exc_info=False)

    @bot.slash_command(
        name="dl_bot_status",
        description="Check if the bot is running and connected to SQL.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.03")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def status_command(ctx):
        await safe_defer(ctx, ephemeral=True)

        # Belt-and-braces admin gate (decorator already limits usage)
        if ctx.user.id != ADMIN_USER_ID:
            await ctx.interaction.edit_original_response(
                content="❌ This command is restricted to admins."
            )
            return

        # --- Check DB connection
        try:
            conn_str = (
                "DRIVER={ODBC Driver 17 for SQL Server};"
                f"SERVER={SERVER};"
                f"DATABASE={DATABASE};"
                f"UID={USERNAME};"
                f"PWD={PASSWORD};"
            )
            with pyodbc.connect(conn_str, timeout=5) as conn:
                conn.execute("SELECT 1")
            db_ok = True
            db_status = "🟢 SQL connected"
        except Exception as e:
            db_ok = False
            db_status = f"🔴 SQL ERROR: `{type(e).__name__}: {str(e)[:150]}`"

        # --- Check Google Sheets
        try:
            success, message = check_basic_gsheets_access(CREDENTIALS_FILE, SHEET_ID)
            gsheets_ok = bool(success)
            gsheets_status = f"🟢 {message}" if success else f"🟠 {message}"
        except Exception as e:
            gsheets_ok = False
            gsheets_status = f"🔴 ERROR: {type(e).__name__}: {str(e)[:120]}"

        # --- Uptime + latency
        now = datetime.now(UTC)
        delta = now - start_bot_time
        total_seconds = int(delta.total_seconds())
        days, rem_hours = divmod(total_seconds // 3600, 24)
        minutes = (total_seconds % 3600) // 60
        uptime = f"{int(days)}d {int(rem_hours)}h {int(minutes)}m"

        ws_latency_ms = int(getattr(bot, "latency", 0) * 1000)

        # Overall status colour
        if db_ok and gsheets_ok:
            colour = discord.Color.green()
            headline = "All systems operational ✅"
        elif db_ok or gsheets_ok:
            colour = discord.Color.orange()
            headline = "Degraded performance ⚠️"
        else:
            colour = discord.Color.red()
            headline = "Multiple issues detected ❌"

        embed = discord.Embed(title="📡 DL_Bot Status", description=headline, color=colour)
        embed.add_field(name="DL_Bot", value=f"✅ Online • {ws_latency_ms} ms latency", inline=True)
        embed.add_field(name="Database", value=db_status, inline=True)
        embed.add_field(name="Google Sheets", value=gsheets_status, inline=True)
        embed.add_field(name="Uptime", value=uptime, inline=False)
        embed.set_footer(text=f"Checked by {ctx.user.name} • {SERVER}/{DATABASE}")
        embed.timestamp = now

        await ctx.interaction.edit_original_response(embed=embed)

    @bot.slash_command(
        name="logs",
        description="Tail logs with filters & paging (general/error/crash).",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.10")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def logs_command(
        ctx,
        source: str = discord.Option(
            str, "Which log?", choices=["general", "error", "crash"], default="general"
        ),
        level: str = discord.Option(
            str,
            "Filter by level",
            choices=["INFO", "WARNING", "ERROR", "CRITICAL", "(none)"],
            required=False,
        ),
        contains: str = discord.Option(str, "Substring or regex", required=False),
        page: int = discord.Option(int, "Page number", required=False, default=1),
        page_size: int = discord.Option(int, "Lines per page (10-200)", required=False, default=50),
    ):
        await safe_defer(ctx, ephemeral=True)
        lvl = None if (level or "") == "(none)" else level
        path = _pick_log_source(source)

        if not os.path.exists(path):
            await ctx.interaction.edit_original_response(content=f"⚠️ Log file not found: `{path}`")
            return

        title = {
            "general": "📄 General Log",
            "error": "🚨 Error Log",
            "crash": "💥 Crash Log",
        }.get(source, "📄 Log")

        view = LogTailView(
            ctx, path, title, level=lvl, contains=contains, page=page, page_size=page_size
        )
        await view.render(ctx.interaction)
        await ctx.interaction.edit_original_response(view=view)

    @bot.slash_command(
        name="show_logs",
        description="Show recent entries from the general log file.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def show_logs_command(ctx, lines: int = 20):
        await safe_defer(ctx, ephemeral=True)

        # Clamp the number of lines for safety
        lines = max(1, min(int(lines or 20), 200))

        if not os.path.exists(FULL_LOG_PATH):
            await ctx.interaction.edit_original_response(
                content=f"⚠️ Log file not found: `{FULL_LOG_PATH}`"
            )
            return

        try:
            # Tail efficiently without loading the whole file
            dq = deque(maxlen=lines)
            with open(FULL_LOG_PATH, encoding="utf-8", errors="replace", newline="") as f:
                for ln in f:
                    dq.append(ln.rstrip("\n"))

            message = "\n".join(dq).strip()
            if not message:
                message = "(log is empty)"

            # Neutralize accidental code fence endings inside the log
            safe_text = message.replace("```", "`\u200b``")

            # Embed description budget (Discord ~4096 chars; leave margin for fences)
            BUDGET = 3800
            needs_file = len(safe_text) > BUDGET

            desc_body = safe_text[:BUDGET]
            if needs_file:
                desc_body += "\n…(truncated)"

            desc = f"```{desc_body}```"

            # Build embed
            mtime = datetime.fromtimestamp(os.path.getmtime(FULL_LOG_PATH))
            embed = discord.Embed(title="📄 Last Log Entries", description=desc, color=0x3498DB)
            embed.add_field(name="Lines", value=str(min(lines, len(dq))), inline=True)
            embed.add_field(name="File", value=os.path.basename(FULL_LOG_PATH), inline=True)
            embed.set_footer(text=f"Modified {mtime:%Y-%m-%d %H:%M:%S}")

            if needs_file:
                # Attach full tail as a file to avoid embed limits
                buf = io.BytesIO(message.encode("utf-8", "replace"))
                buf.seek(0)
                file = discord.File(buf, filename=f"log_tail_{lines}.txt")
                await ctx.interaction.edit_original_response(embed=embed, attachments=[file])
            else:
                await ctx.interaction.edit_original_response(embed=embed)

        except Exception as e:
            logger.exception("[COMMAND] /show_logs failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to read log: `{type(e).__name__}: {e}`"
            )

    @bot.slash_command(
        name="last_errors",
        description="Show recent entries from the error log.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def last_errors_command(ctx, lines: int = 20):

        await safe_defer(ctx, ephemeral=True)

        # Clamp lines for safety
        lines = max(1, min(int(lines or 20), 200))

        if not os.path.exists(ERROR_LOG_PATH):
            await ctx.interaction.edit_original_response(
                content=f"⚠️ Error log not found: `{ERROR_LOG_PATH}`"
            )
            return

        try:
            # Efficient tail
            dq = deque(maxlen=lines)
            with open(ERROR_LOG_PATH, encoding="utf-8", errors="replace", newline="") as f:
                for ln in f:
                    dq.append(ln.rstrip("\n"))

            message = "\n".join(dq).strip() or "(no errors logged)"

            # Neutralise accidental code-fence closures
            safe_text = message.replace("```", "`\u200b``")

            # Embed budget & attachment fallback
            BUDGET = 3800
            needs_file = len(safe_text) > BUDGET
            desc_body = safe_text[:BUDGET]
            if needs_file:
                desc_body += "\n…(truncated)"

            desc = f"```{desc_body}```"

            mtime = datetime.fromtimestamp(os.path.getmtime(ERROR_LOG_PATH))
            embed = discord.Embed(title="🚨 Last Error Entries", description=desc, color=0xE74C3C)
            embed.add_field(name="Lines", value=str(min(lines, len(dq))), inline=True)
            embed.add_field(name="File", value=os.path.basename(ERROR_LOG_PATH), inline=True)
            embed.set_footer(text=f"Modified {mtime:%Y-%m-%d %H:%M:%S}")
            embed.timestamp = datetime.utcnow()

            if needs_file:
                buf = io.BytesIO("\n".join(dq).encode("utf-8", "replace"))
                buf.seek(0)
                file = discord.File(buf, filename=f"error_tail_{lines}.txt")
                await ctx.interaction.edit_original_response(embed=embed, attachments=[file])
            else:
                await ctx.interaction.edit_original_response(embed=embed)

        except Exception as e:
            logger.exception("[COMMAND] /last_errors failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to read error log: `{type(e).__name__}: {e}`"
            )

    @bot.slash_command(
        name="crash_log",
        description="Show recent entries from the crash log.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def crash_log_command(ctx, lines: int = 20):

        await safe_defer(ctx, ephemeral=True)

        # Clamp for safety
        lines = max(1, min(int(lines or 20), 200))

        if not os.path.exists(CRASH_LOG_PATH):
            await ctx.interaction.edit_original_response(
                content=f"⚠️ Crash log not found: `{CRASH_LOG_PATH}`"
            )
            return

        try:
            # Efficient tail without loading whole file
            dq = deque(maxlen=lines)
            with open(CRASH_LOG_PATH, encoding="utf-8", errors="replace", newline="") as f:
                for ln in f:
                    dq.append(ln.rstrip("\n"))

            message = "\n".join(dq).strip() or "(no crash logs found)"

            # Neutralize accidental ``` inside the log
            safe_text = message.replace("```", "`\u200b``")

            # Embed budget + optional attachment
            BUDGET = 3800
            needs_file = len(safe_text) > BUDGET

            desc_body = safe_text[:BUDGET]
            if needs_file:
                desc_body += "\n…(truncated)"

            desc = f"```{desc_body}```"

            mtime = datetime.fromtimestamp(os.path.getmtime(CRASH_LOG_PATH))
            embed = discord.Embed(
                title="💥 Last Crash Log Entries",
                description=desc,
                color=0xFF6347,  # tomato; keep your original
            )
            embed.add_field(name="Lines", value=str(min(lines, len(dq))), inline=True)
            embed.add_field(name="File", value=os.path.basename(CRASH_LOG_PATH), inline=True)
            embed.set_footer(text=f"Modified {mtime:%Y-%m-%d %H:%M:%S}")
            embed.timestamp = datetime.utcnow()

            if needs_file:
                buf = io.BytesIO("\n".join(dq).encode("utf-8", "replace"))
                buf.seek(0)
                file = discord.File(buf, filename=f"crash_tail_{lines}.txt")
                await ctx.interaction.edit_original_response(embed=embed, attachments=[file])
            else:
                await ctx.interaction.edit_original_response(embed=embed)

        except Exception as e:
            logger.exception("[COMMAND] /crash_log failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to read crash log: `{type(e).__name__}: {e}`"
            )

    @bot.slash_command(
        name="test_embed",
        description="🧪 Manually trigger the stats update embed",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.07")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def test_embed_command(ctx):
        from datetime import datetime

        from bot_config import NOTIFY_CHANNEL_ID, OFFSEASON_STATS_CHANNEL_ID
        from stats_alerts.kvk_meta import is_currently_kvk

        await safe_defer(ctx, ephemeral=True)
        start_ts = datetime.now(datetime.UTC)

        # Where the embed will land (for the admin’s confirmation)
        notify_channel = bot.get_channel(NOTIFY_CHANNEL_ID)

        try:
            # Determine if KVK fighting is open (blocking) — run off the loop
            is_kvk = await asyncio.to_thread(is_currently_kvk)

            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

            # Send the test embed (async interface accepts (bot, timestamp, is_kvk, is_test=...))
            await send_stats_update_embed(bot, timestamp, is_kvk, is_test=True)

            dur = (datetime.now(datetime.UTC) - start_ts).total_seconds()
            where = notify_channel.mention if notify_channel else f"<#{OFFSEASON_STATS_CHANNEL_ID}>"
            await ctx.interaction.edit_original_response(
                content=(
                    "✅ **Test stats embed sent.**\n"
                    f"- KVK active: **{is_kvk}**\n"
                    f"- Timestamp: `{timestamp}`\n"
                    f"- Posted to: {where}\n"
                    f"- Duration: **{dur:.1f}s**"
                )
            )
            logger.info("[/test_embed] success (kvk=%s, dur=%.2fs)", is_kvk, dur)

        except Exception as e:
            logger.exception("[/test_embed] failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to send embed:\n```{type(e).__name__}: {e}```"
            )

    @bot.slash_command(
        name="mykvktargets",
        description="📊 View your DKP, Kill and Deads targets",
        guild_ids=[GUILD_ID],
    )
    @channel_only(KVK_TARGET_CHANNEL_ID, admin_override=True)
    @versioned("v3.11")
    @safe_command
    @track_usage()
    async def mykvktargets(
        ctx: discord.ApplicationContext,
        governorid: str = discord.Option(
            str,
            name="governorid",
            description="(Optional) Governor ID if you prefer to type it",
            required=False,
            default=None,
        ),
        only_me: bool = discord.Option(
            bool,
            name="only_me",
            description="Show only to me (ephemeral)",
            required=False,
            default=False,  # public by default
        ),
    ):
        await safe_defer(ctx, ephemeral=only_me)

        # Load last-KVK cache once (centralized helper)
        try:
            last_kvk_map = await load_last_kvk_map()
            if not isinstance(last_kvk_map, dict):
                last_kvk_map = {}
        except Exception:
            logger.exception("[/mykvktargets] load_last_kvk_map failed")
            last_kvk_map = {}

        # ---------------- Reused wrappers from /my_registrations ----------------
        # These are defined early so we can pass them as callbacks into make_kvk_targets_view
        async def kvk_open_registration_flow(interaction: discord.Interaction):
            """
            Open the same 'Pick an account slot to register' view used by /my_registrations.
            """
            try:
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
            except Exception:
                pass

            try:
                registry = await async_load_registry() or {}
                user_key_str = str(interaction.user.id)
                user_block = registry.get(user_key_str) or registry.get(interaction.user.id) or {}
                accounts = (
                    (user_block.get("accounts") or {}) if isinstance(user_block, dict) else {}
                )

                used_slots = set(accounts.keys())
                free_slots = [slot for slot in ACCOUNT_ORDER if slot not in used_slots]

                if not free_slots:
                    await interaction.followup.send(
                        "All account slots are already registered. Use **/my_registrations → Modify Registration** to change one.",
                        ephemeral=True,
                    )
                    return

                await interaction.followup.send(
                    "Pick an account slot to register:",
                    view=RegisterStartView(author_id=interaction.user.id, free_slots=free_slots),
                    ephemeral=True,
                )
            except Exception as e:
                logger.exception("[kvk_open_registration_flow] failed")
                try:
                    await interaction.followup.send(
                        f"⚠️ Failed to open registration flow: `{type(e).__name__}: {e}`",
                        ephemeral=True,
                    )
                except Exception:
                    pass

        async def kvk_open_governor_lookup(interaction: discord.Interaction):
            """
            Open the same lookup modal (fuzzy/ID) used by /my_registrations.
            IMPORTANT: first response must be the modal; don't defer before this.
            """
            try:
                await interaction.response.send_modal(GovNameModal(author_id=interaction.user.id))
            except Exception:
                try:
                    if not interaction.response.is_done():
                        await interaction.response.send_message(
                            "Use **/mygovernorid** and start typing your governor name to find your Governor ID.",
                            ephemeral=True,
                        )
                    else:
                        await interaction.followup.send(
                            "Use **/mygovernorid** and start typing your governor name to find your Governor ID.",
                            ephemeral=True,
                        )
                except Exception:
                    pass

        # ---------------- Helper used when a governor is chosen ----------------
        async def _handle_governor_display(
            interaction: discord.Interaction | None, governor_id: str, ephemeral: bool
        ):
            """
            Load the stat row, attach last_kvk if available, build the embed and send it.
            Prefers run_target_lookup (canonical path) for consistent embed rendering.
            This function does local imports of kvk helpers to avoid circular imports.
            """
            try:
                if interaction:
                    # Delegate to canonical helper that builds & sends the embed (keeps original formatting)
                    await run_target_lookup(interaction, governor_id, ephemeral=ephemeral)
                    return
                # Non-interactive/manual path: call run_target_lookup without interaction to get data,
                # then post results similarly to legacy behavior.
                res = await run_target_lookup(governor_id)
                if not isinstance(res, dict):
                    # unexpected shape, bail with a message
                    try:
                        await ctx.followup.send("Could not load targets.", ephemeral=True)
                    except Exception:
                        pass
                    return

                # If non-interactive returns a dict result, try to show a simple message via followup
                if res.get("status") == "found" and res.get("data"):
                    tgt = res["data"]
                    # Local imports to avoid circular references at module import time
                    try:
                        from kvk_state import get_kvk_context_today  # type: ignore
                    except Exception:
                        get_kvk_context_today = None

                    try:
                        from targets_embed import build_kvk_targets_embed  # type: ignore
                    except Exception:
                        build_kvk_targets_embed = None

                    if callable(get_kvk_context_today):
                        kvk_ctx = get_kvk_context_today() or {}
                    else:
                        kvk_ctx = {}

                    kvk_name = kvk_ctx.get("kvk_name")
                    gov_name = tgt.get("GovernorName") or "Governor"

                    if callable(build_kvk_targets_embed):
                        try:
                            embed = build_kvk_targets_embed(
                                gov_name=gov_name,
                                governor_id=governor_id,
                                targets=tgt,
                                kvk_name=kvk_name,
                            )
                            if ephemeral:
                                await ctx.followup.send(embed=embed, ephemeral=True)
                            else:
                                await ctx.channel.send(embed=embed)
                        except Exception:
                            logger.exception(
                                "[/mykvktargets] build_kvk_targets_embed failed for %s", governor_id
                            )
                            try:
                                await ctx.followup.send(
                                    "Failed to build targets embed.", ephemeral=True
                                )
                            except Exception:
                                pass
                    else:
                        # No embed builder available — provide a simple textual fallback
                        try:
                            body = f"Targets for Governor {gov_name} ({governor_id}):\n{tgt}"
                            await ctx.followup.send(body, ephemeral=True)
                        except Exception:
                            pass
                else:
                    # No data found — forward user-facing message if present
                    msg = res.get("message", "No targets found.")
                    try:
                        await ctx.followup.send(msg, ephemeral=True)
                    except Exception:
                        pass

            except Exception:
                logger.exception(
                    "[/mykvktargets] _handle_governor_display failed for %s", governor_id
                )
                try:
                    if interaction:
                        await interaction.followup.send(
                            "Failed to load targets for that governor.", ephemeral=True
                        )
                    else:
                        await ctx.followup.send(
                            "Failed to load targets for that governor.", ephemeral=True
                        )
                except Exception:
                    pass

        # 1) Manual ID path (immediate handling) — delegate to run_target_lookup for exact original behavior
        if governorid and governorid.strip().isdigit():
            gid = governorid.strip()
            await run_target_lookup(ctx.interaction, gid, ephemeral=only_me)
            try:
                await ctx.interaction.edit_original_response(content=" ", view=None)
            except Exception:
                pass
            return

        # 2) Registered accounts path
        try:
            registry = await asyncio.to_thread(load_registry)
            user_block = registry.get(str(ctx.user.id)) or {}
            accounts = user_block.get("accounts") or {}
        except Exception:
            logger.exception("[/mykvktargets] load_registry failed")
            await ctx.followup.send(
                "⚠️ Couldn’t load your registered accounts. Provide `governorid` or try again later.",
                ephemeral=True,
            )
            return

        options = _safe_build_unique_gov_options(accounts)

        # Single-account auto-open → use canonical helper
        if options and len(options) == 1:
            only_gid = options[0].value
            await run_target_lookup(ctx.interaction, only_gid, ephemeral=only_me)
            try:
                await ctx.interaction.edit_original_response(content=" ", view=None)
            except Exception:
                pass
            return

        # Multi-account path → build view with on_select handler delegating to run_target_lookup
        if options:

            async def _on_select(
                interaction: discord.Interaction, governor_id: str, ephemeral: bool
            ):
                await run_target_lookup(interaction, governor_id, ephemeral=ephemeral)

            try:
                view = make_kvk_targets_view(
                    ctx=ctx,
                    options=options,
                    on_select_governor=_on_select,
                    show_register_btn=True,
                    ephemeral=only_me,
                    last_kvk_map=last_kvk_map,
                    lookup_callback=kvk_open_governor_lookup,
                    register_callback=kvk_open_registration_flow,
                )
                await ctx.followup.send(
                    "Select an account to view its KVK targets:", view=view, ephemeral=only_me
                )
            except Exception:
                logger.exception("[/mykvktargets] Failed to create/send account selector view")
                await ctx.followup.send(
                    "Failed to show account selector. Try again later.", ephemeral=True
                )
            return

        # No registered accounts → show hint + account picker view
        hint = (
            "You don’t have any linked governor accounts yet.\n"
            "• Use `/link_account` (Register new account), or\n"
            "• Re-run this command with the `governorid` option."
        )
        try:

            async def _empty_on_select(i, gid, e):
                await run_target_lookup(i, gid, ephemeral=e)

            view = make_kvk_targets_view(
                ctx=ctx,
                options=[],
                on_select_governor=_empty_on_select,
                show_register_btn=True,
                ephemeral=only_me,
                last_kvk_map=last_kvk_map,
                lookup_callback=kvk_open_governor_lookup,
                register_callback=kvk_open_registration_flow,
            )
            await ctx.followup.send(hint, view=view, ephemeral=only_me)
        except Exception:
            logger.exception("[/mykvktargets] Failed to create/send empty account picker view")
            await ctx.followup.send(hint, ephemeral=only_me)

    @bot.slash_command(
        name="mygovernorid",
        description="🔍 Look up your GovernorID by entering your Governor Name",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.10")
    @safe_command
    @track_usage()
    async def mygovernorid(
        ctx: discord.ApplicationContext,
        governorname: str = discord.Option(
            str,
            "Enter your Governor Name",
            name="governorname",
            autocomplete=autocomplete_governor_names,
        ),
    ):
        # Single, ephemeral ack
        await safe_defer(ctx, ephemeral=True)

        # Input hygiene
        name = (governorname or "").strip()
        if not name:
            await ctx.interaction.edit_original_response(
                content="❌ Please enter a governor name.", embed=None, view=None
            )
            return
        if len(name) < 2:
            await ctx.interaction.edit_original_response(
                content="⚠️ Please enter at least **2 characters** for better matches.",
                embed=None,
                view=None,
            )
            return

        try:
            result = await lookup_governor_id(name)

            if result["status"] == "found":
                embed = discord.Embed(
                    title="🆔 Governor ID Lookup",
                    description=(
                        f"**Governor Name:** {result['data']['GovernorName']}\n"
                        f"**Governor ID:** `{result['data']['GovernorID']}`"
                    ),
                    color=discord.Color.green(),
                )
                actions = TargetLookupView.PostLookupActions(
                    author_id=ctx.user.id, governor_id=str(result["data"]["GovernorID"])
                )
                await ctx.interaction.edit_original_response(
                    content=None, embed=embed, view=actions
                )

            elif result["status"] == "fuzzy_matches":
                matches = result.get("matches", [])
                # Summarize in description (avoid 25-field limit)
                MAX_LINES = 15
                lines = [
                    f"• **{m['GovernorName']}** — `{m['GovernorID']}`" for m in matches[:MAX_LINES]
                ]
                more = len(matches) - MAX_LINES
                desc = "Pick a governor from the dropdown below.\n\n" + "\n".join(lines)
                if more > 0:
                    desc += f"\n…and **{more}** more."

                embed = discord.Embed(
                    title="🔍 Governor Name Search Results",
                    description=desc,
                    color=discord.Color.blue(),
                )
                # Restrict interactions to the invoker
                view = TargetLookupView.FuzzySelectView(matches, ctx.user.id, show_targets=True)
                await ctx.interaction.edit_original_response(content=None, embed=embed, view=view)

            else:
                # e.g., not found
                await ctx.interaction.edit_original_response(
                    content=result.get("message", "No results found."), embed=None, view=None
                )

        except Exception as e:
            logger.exception("[/mygovernorid] failed for query=%r", governorname)
            await ctx.interaction.edit_original_response(
                content=f"❌ Error: `{type(e).__name__}: {e}`", embed=None, view=None
            )

    @bot.slash_command(
        name="nextfight",
        description="Shows the next fight or up to the next 3 fights!",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.04")
    @safe_command
    @track_usage()
    async def nextfight(ctx):
        logger.info("[COMMAND] /nextfight used")
        await safe_defer(ctx, ephemeral=False)

        try:
            # Get up to 3 upcoming fight-worthy events in one shot.
            all_fights = get_next_fights(3) or []
            if not all_fights:
                await ctx.interaction.edit_original_response(
                    content="Fighting finished just chill now!"
                )
                return

            # Show just the next fight in the initial embed.
            initial_limit = 1
            embed = format_fight_embed(all_fights[:initial_limit])
            prefix = "nextfight"

            # Build the view. If your view can take the list/availability, pass it.
            # (These setters are optional; guarded with hasattr so it won't break older code.)
            view = NextFightView(initial_limit=initial_limit, prefix=prefix)
            # if hasattr(view, "set_available"):
            # view.set_available(len(all_fights))
            # if hasattr(view, "set_events"):
            # view.set_events(all_fights)

            # Send initial response
            await ctx.interaction.edit_original_response(embed=embed, view=view)

            # Bind the sent message back to the view (so it can safely edit itself later)
            try:
                sent_msg = await ctx.interaction.original_response()
                if hasattr(view, "message"):
                    view.message = sent_msg
            except Exception:
                sent_msg = None

            # Persist for rehydration (include a bit more context)
            try:
                await save_view_tracker_async(
                    "nextfight",
                    {
                        "message_id": getattr(sent_msg, "id", None),
                        "channel_id": getattr(
                            getattr(sent_msg, "channel", None),
                            "id",
                            ctx.channel.id if ctx.channel else None,
                        ),
                        "prefix": prefix,
                        "created_at": utcnow().isoformat(),
                        "initial_limit": initial_limit,
                        "available": len(all_fights),
                        "events": [
                            serialize_event(e)
                            for e in (getattr(view, "fights", None) or all_fights)
                        ],
                    },
                )
            except Exception as e:
                logger.exception("[nextfight] save_view_tracker_async failed: %s", e)

        except Exception as e:
            logger.exception("[COMMAND] /nextfight failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Unable to build next fights: `{type(e).__name__}: {e}`",
                embed=None,
                view=None,
            )

    @bot.slash_command(
        name="nextevent", description="Show the next upcoming events", guild_ids=[GUILD_ID]
    )
    @versioned("v1.03")
    @safe_command
    @track_usage()
    async def nextevent(ctx):
        logger.info("[COMMAND] /nextevent used")
        await safe_defer(ctx, ephemeral=False)

        try:
            all_events = get_next_events(limit=5) or []
            if not all_events:
                await ctx.interaction.edit_original_response(content="No upcoming events found.")
                return

            initial_limit = 1
            embed = format_event_embed(all_events[:initial_limit])
            prefix = "nextevent"
            view = NextEventView(initial_limit=initial_limit, prefix=prefix, preloaded=all_events)

            await ctx.interaction.edit_original_response(embed=embed, view=view)

            # Bind message so the view can safely edit later
            try:
                sent_msg = await ctx.interaction.original_response()
                if hasattr(view, "message"):
                    view.message = sent_msg
            except Exception:
                sent_msg = None

            # Save for rehydration
            try:
                await save_view_tracker_async(
                    "nextevent",
                    {
                        "message_id": getattr(sent_msg, "id", None),
                        "channel_id": getattr(
                            getattr(sent_msg, "channel", None),
                            "id",
                            ctx.channel.id if ctx.channel else None,
                        ),
                        "prefix": prefix,
                        "created_at": utcnow().isoformat(),
                        "initial_limit": initial_limit,
                        "available": len(all_events),
                        "events": [serialize_event(e) for e in (view.events or all_events)],
                    },
                )
            except Exception as e:
                logger.exception("[nextevent] save_view_tracker_async failed: %s", e)

        except Exception as e:
            logger.exception("[COMMAND] /nextevent failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Unable to build events: `{type(e).__name__}: {e}`",
                embed=None,
                view=None,
            )

    @bot.slash_command(
        name="refresh_events",
        description="Manually refresh the event cache and countdowns",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def refresh_events(ctx):
        await safe_defer(ctx, ephemeral=True)
        logger.info("[COMMAND] /refresh_events used by %s", ctx.author)

        started = datetime.now(UTC)
        try:
            # Refresh cached events
            await refresh_event_cache()

            # Update any live countdown embeds
            await update_live_event_embeds(bot, KVK_EVENT_CHANNEL_ID)

            # Format timestamp (fallback if attr missing or naive)
            from event_cache import get_last_refreshed

            ts = get_last_refreshed()
            if isinstance(ts, datetime):
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=UTC)
                ts_text = ts.strftime("%Y-%m-%d %H:%M:%S UTC")
            else:
                ts_text = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

            dur = (datetime.now(UTC) - started).total_seconds()
            await ctx.interaction.edit_original_response(
                content=f"✅ Event cache and countdown embeds refreshed.\n"
                f"🕒 Last refreshed: `{ts_text}` • ⏱ {dur:.1f}s"
            )

        except Exception as e:
            logger.exception("[COMMAND ERROR] /refresh_events failed.")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to refresh event cache or embeds:\n```{type(e).__name__}: {e}```"
            )

    @bot.slash_command(
        name="refresh_kvk_overview",
        description="📅 Refresh the Daily KVK Overview embed manually",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def refresh_kvk_overview(ctx):
        await safe_defer(ctx, ephemeral=True)
        logger.info("[COMMAND] /refresh_kvk_overview used by %s", ctx.author)

        started = utcnow()
        try:
            # 1) Refresh events if cache looks stale (keeps manual refresh honest)
            try:
                if is_cache_stale():
                    await refresh_event_cache()
            except Exception:
                logger.warning(
                    "[/refresh_kvk_overview] Cache refresh check failed; proceeding anyway.",
                    exc_info=True,
                )

            # 2) Post or update the overview
            await post_or_update_daily_KVK_overview(bot, KVK_EVENT_CHANNEL_ID)

            # 3) Build friendly admin message with cache timestamp + duration
            ts = get_last_refreshed()
            if isinstance(ts, datetime):
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=UTC)
                ts_text = ts.strftime("%Y-%m-%d %H:%M:%S UTC")
            else:
                ts_text = utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

            dur = (utcnow() - started).total_seconds()
            await ctx.interaction.edit_original_response(
                content=(
                    f"✅ Daily KVK Overview refreshed in **{dur:.1f}s** and posted to <#{KVK_EVENT_CHANNEL_ID}>.\n"
                    f"🕒 Event cache last refreshed: `{ts_text}`"
                )
            )

        except Exception as e:
            logger.exception("[COMMAND ERROR] /refresh_kvk_overview failed.")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to refresh KVK overview:\n```{type(e).__name__}: {e}```"
            )

    @bot.slash_command(
        name="subscribe",
        description="Subscribe to KVK event reminders via DM",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.11")
    @safe_command
    @track_usage()
    async def subscribe_command(ctx):
        user = ctx.user
        uid = user.id
        username = str(user)

        existing = get_user_config(uid)
        if existing:
            await ctx.respond(
                "❌ You're already subscribed. Use `/modify_subscription` to change your preferences.",
                ephemeral=True,
            )
            return

        async def _on_timeout_edit(view: SubscriptionView):
            try:
                msg = await ctx.interaction.original_response()
                await msg.edit(view=view)
            except Exception:
                pass

        async def _on_confirm(interaction: discord.Interaction, view: SubscriptionView):
            types = list(view.selected_types)
            times = list(view.selected_reminders)
            if not times:
                times = DEFAULT_REMINDER_TIMES
            if not types:
                await interaction.response.send_message(
                    "❌ Please select at least one event type.", ephemeral=True
                )
                return
            if not times:
                await interaction.response.send_message(
                    "❌ Please select at least one reminder time.", ephemeral=True
                )
                return

            valid_types = set(VALID_TYPES)
            invalid_types = [t for t in types if t not in valid_types]
            if invalid_types:
                await interaction.response.send_message(
                    f"❌ Invalid event types: {', '.join(invalid_types)}", ephemeral=True
                )
                return
            valid_times = set(DEFAULT_REMINDER_TIMES)
            invalid_times = [t for t in times if t not in valid_times]
            if invalid_times:
                await interaction.response.send_message(
                    f"❌ Invalid reminder times: {', '.join(invalid_times)}", ephemeral=True
                )
                return

            original_types = types.copy()
            if "all" in types:
                types = ["all"]
            elif "fights" in types:
                types = [t for t in types if t not in ("altars", "major")]
            try:
                set_user_config(view.uid, view.username, types, times)
            except Exception as e:
                logger.exception("[subscribe] set_user_config failed")
                await interaction.response.send_message(
                    f"❌ Failed to save your subscription: `{type(e).__name__}: {e}`",
                    ephemeral=True,
                )
                return

            embed = discord.Embed(
                title="👋 Subscribed to Event Reminders",
                description=f"Hi {view.user.mention}, you're now subscribed to event reminders!",
                color=0x2ECC71,
            )
            embed.add_field(name="Event Types", value=", ".join(types), inline=False)
            embed.add_field(name="Reminder Times", value=", ".join(times), inline=False)

            if set(types) != set(original_types):
                embed.add_field(
                    name="⚠️ Note",
                    value="Some selections were adjusted to avoid duplicate reminders (e.g., 'all' disables others).",
                    inline=False,
                )
            embed.set_footer(text="You can update these anytime with /modify_subscription")

            try:
                await view.user.send(embed=embed)
            except discord.Forbidden:
                await interaction.response.send_message(
                    "⚠️ Could not send DM. Please enable DMs from this server and try again.",
                    ephemeral=True,
                )
                return

            for c in view.children:
                c.disabled = True
            await interaction.response.edit_message(
                content="✅ Subscribed successfully! A confirmation has been sent via DM.",
                view=view,
            )
            view.stop()

        await ctx.respond(
            "📝 Please complete your subscription below:",
            view=SubscriptionView(
                user=user,
                uid=uid,
                username=username,
                selected_types=[],
                selected_reminders=[],
                confirm_label="✅ Confirm",
                include_unsubscribe=False,
                reminder_min_values=1,
                cid_prefix="sub",
                on_confirm=_on_confirm,
                on_timeout_edit=_on_timeout_edit,
            ),
            ephemeral=True,
        )

    @bot.slash_command(
        name="modify_subscription",
        description="Update your KVK event reminder preferences",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.09")
    @safe_command
    @track_usage()
    async def modify_subscribe_command(ctx):

        user = ctx.user
        uid = user.id
        username = str(user)

        existing = get_user_config(uid)
        if not existing:
            await ctx.respond(
                "❌ You're not currently subscribed. Use `/subscribe` to set your preferences.",
                ephemeral=True,
            )
            return

        existing_types = list(existing.get("subscriptions", []))
        existing_times = list(existing.get("reminder_times", []))

        async def _on_timeout_edit(view: SubscriptionView):
            try:
                msg = await ctx.interaction.original_response()
                await msg.edit(view=view)
            except Exception:
                pass

        async def _on_unsubscribe(interaction: discord.Interaction, view: SubscriptionView):
            try:
                cancelled = cancel_user_reminder_tasks(uid)
                sched_removed = purge_user_from_dm_scheduled_tracker(uid)
                sent_removed = purge_user_from_dm_sent_tracker(uid)
                remove_user(uid)
                logger.info(
                    "[unsubscribe] uid=%s | tasks_cancelled=%s scheduled_removed=%s sent_removed=%s",
                    uid,
                    cancelled,
                    sched_removed,
                    sent_removed,
                )

            except Exception as e:
                logger.exception("[modify_subscription] unsubscribe failed")
                await interaction.response.send_message(
                    f"❌ Failed to unsubscribe: `{type(e).__name__}: {e}`", ephemeral=True
                )
                return

            for c in view.children:
                c.disabled = True
            await interaction.response.edit_message(
                content="✅ You’ve been unsubscribed.", view=view
            )
            try:
                await user.send(
                    embed=discord.Embed(
                        title="🔕 Unsubscribed",
                        description=f"Hi {user.mention}, you’ve been unsubscribed from all event reminders.",
                        color=0xE74C3C,
                    )
                )
            except discord.Forbidden:
                pass
            view.stop()

        async def _on_confirm(interaction: discord.Interaction, view: SubscriptionView):
            types = list(view.selected_types)
            times = list(view.selected_reminders)
            if not times:
                times = DEFAULT_REMINDER_TIMES

            if not types:
                await interaction.response.send_message(
                    "❌ Please select at least one event type.", ephemeral=True
                )
                return
            if not times:
                await interaction.response.send_message(
                    "❌ Please select at least one reminder time.", ephemeral=True
                )
                return

            invalid_types = [t for t in types if t not in VALID_TYPES]
            if invalid_types:
                await interaction.response.send_message(
                    f"❌ Invalid event types: {', '.join(invalid_types)}", ephemeral=True
                )
                return
            invalid_times = [t for t in times if t not in DEFAULT_REMINDER_TIMES]
            if invalid_times:
                await interaction.response.send_message(
                    f"❌ Invalid reminder times: {', '.join(invalid_times)}", ephemeral=True
                )
                return

            original_types = types.copy()
            if "all" in types:
                types = ["all"]
            elif "fights" in types:
                types = [t for t in types if t not in ("altars", "major")]

            try:
                set_user_config(view.uid, view.username, types, times)
            except Exception as e:
                logger.exception("[modify_subscription] set_user_config failed")
                await interaction.response.send_message(
                    f"❌ Failed to save your preferences: `{type(e).__name__}: {e}`",
                    ephemeral=True,
                )
                return

            embed = discord.Embed(
                title="🔄 Preferences Updated",
                description=f"Hi {view.user.mention}, your event reminder preferences are now updated!",
                color=0xF1C40F,
            )
            embed.add_field(name="Event Types", value=", ".join(types), inline=False)
            embed.add_field(name="Reminder Times", value=", ".join(times), inline=False)

            if set(types) != set(original_types):
                embed.add_field(
                    name="⚠️ Note",
                    value="Some selections were adjusted to avoid duplicate reminders (e.g., 'all' disables others).",
                    inline=False,
                )
            embed.set_footer(text="You can update these anytime with /modify_subscription")

            try:
                await view.user.send(embed=embed)
            except discord.Forbidden:
                await interaction.response.send_message(
                    "⚠️ Could not send DM. Please enable DMs from this server.", ephemeral=True
                )
                return

            for c in view.children:
                c.disabled = True
            await interaction.response.edit_message(
                content="✅ Preferences updated! A confirmation has been sent via DM.",
                view=view,
            )
            view.stop()

        await ctx.respond(
            "🛠️ Update your preferences below:",
            view=SubscriptionView(
                user=user,
                uid=uid,
                username=username,
                selected_types=existing_types,
                selected_reminders=existing_times,
                confirm_label="✅ Update Preferences",
                include_unsubscribe=True,
                reminder_min_values=0,
                cid_prefix="modsub",
                on_confirm=_on_confirm,
                on_unsubscribe=_on_unsubscribe,
                on_timeout_edit=_on_timeout_edit,
            ),
            ephemeral=True,
        )

    @bot.slash_command(
        name="unsubscribe", description="Stop receiving KVK event reminders", guild_ids=[GUILD_ID]
    )
    @versioned("v1.04")
    @safe_command
    @track_usage()
    async def unsubscribe_command(ctx):

        await safe_defer(ctx, ephemeral=True)

        user = ctx.user
        uid = user.id

        # Look up existing config once
        existing = get_user_config(uid)
        if not existing:
            await ctx.interaction.edit_original_response(
                content="❌ You’re not currently subscribed to any reminders. Use `/subscribe` to get started."
            )
            return

        # Keep a copy for the DM summary
        prev_types = list(existing.get("subscriptions", []))
        prev_times = list(existing.get("reminder_times", []))

        # Remove from the store (cancel tasks, purge trackers, then remove config)
        try:
            cancelled = cancel_user_reminder_tasks(uid)  # no-op if none
            sched_removed = purge_user_from_dm_scheduled_tracker(uid)  # per-user, per-event buckets
            sent_removed = purge_user_from_dm_sent_tracker(uid)  # per-user, per-event buckets
            success = remove_user(uid)
            if success:
                logger.info(
                    "[UNSUBSCRIBE] uid=%s | success=1 tasks_cancelled=%s scheduled_removed=%s sent_removed=%s",
                    uid,
                    cancelled,
                    sched_removed,
                    sent_removed,
                )
            else:
                logger.info("[UNSUBSCRIBE] No subscription found for user %s (stale state)", uid)
        except Exception as e:
            logger.exception("[UNSUBSCRIBE] remove_user failed for %s", uid)
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to unsubscribe: `{type(e).__name__}: {e}`"
            )
            return

        # Build DM confirmation (include prior settings for the user's record)
        embed = discord.Embed(
            title="🔕 Unsubscribed",
            description=f"Hi {user.mention}, you’ve been unsubscribed from all event reminders.",
            color=0xE74C3C,
        )
        embed.add_field(
            name="Previous Event Types", value=", ".join(prev_types) or "None", inline=False
        )
        embed.add_field(
            name="Previous Reminder Times", value=", ".join(prev_times) or "None", inline=False
        )
        embed.set_footer(text="You can re-subscribe anytime with /subscribe")

        # Try sending DM first (doesn't affect the unsubscribe result)
        dm_sent = True
        try:
            await user.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            dm_sent = False

        # Confirm in the interaction (single-ack path)
        try:
            if dm_sent:
                await ctx.interaction.edit_original_response(
                    content="✅ You’ve been unsubscribed. A confirmation has been sent via DM."
                )
            else:
                await ctx.interaction.edit_original_response(
                    content="✅ You’ve been unsubscribed, but I couldn’t send you a DM. You’re all set!"
                )
        except discord.HTTPException:
            # If the original response was deleted or already acknowledged elsewhere, ignore.
            pass

    @bot.slash_command(
        name="list_subscribers",
        description="View all subscribed users (Admin only)",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.03")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def list_subscribers(ctx):

        await safe_defer(ctx, ephemeral=True)

        try:
            subs = get_all_subscribers() or {}
        except Exception as e:
            logger.exception("[/list_subscribers] get_all_subscribers failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to fetch subscribers: `{type(e).__name__}: {e}`"
            )
            return

        if not subs:
            await ctx.interaction.edit_original_response(
                content="📭 No users are currently subscribed."
            )
            return

        # Normalize + sort by username (case-insensitive)
        items = []
        for uid, data in subs.items():
            username = str(data.get("username", "Unknown"))
            types = ", ".join(data.get("subscriptions", [])) or "None"
            times = ", ".join(data.get("reminder_times", [])) or "None"
            uid_str = str(uid)  # mention formatting

            # Live stats (best-effort)
            try:
                # Count scheduled deltas and sent deltas for this user across all events
                scheduled = sum(
                    len(per_user.get(uid_str, set())) for per_user in dm_scheduled_tracker.values()
                )
                sent = sum(len(per_user.get(uid_str, [])) for per_user in dm_sent_tracker.values())
                tasks = active_task_count(uid_str)
            except Exception:
                scheduled = sent = tasks = 0

            items.append((username, uid_str, types, times, scheduled, sent, tasks))
        items.sort(key=lambda t: t[0].lower())

        embed = discord.Embed(
            title="📋 Subscribed Users",
            description=f"{len(items)} user(s) currently subscribed to reminders.",
            color=discord.Color.blurple(),
        )

        MAX_FIELDS = 25  # Discord embed field limit
        shown = items[:MAX_FIELDS]
        for username, uid_str, types, times, scheduled, sent, tasks in shown:
            mention = f"<@{uid_str}>" if uid_str.isdigit() else uid_str
            embed.add_field(
                name=f"{username} • {mention}",
                value=(
                    f"**Types:** {types}\n"
                    f"**Times:** {times}\n"
                    f"**Queues:** {scheduled} scheduled • {tasks} task(s) • {sent} sent"
                ),
                inline=False,
            )

        attachments = []
        if len(items) > MAX_FIELDS:
            # Attach the full list as CSV (includes live stats)
            buf = io.StringIO()
            buf.write("username,user_id,types,times,scheduled_sent,history_sent,active_tasks\n")
            for username, uid_str, types, times, scheduled, sent, tasks in items:
                buf.write(f"{username},{uid_str},{types},{times},{scheduled},{sent},{tasks}\n")
            data = io.BytesIO(buf.getvalue().encode("utf-8", "replace"))
            data.seek(0)
            attachments = [discord.File(data, filename="subscribers_full.csv")]
            embed.set_footer(text=f"Showing first {MAX_FIELDS}. Full list attached.")

        await ctx.interaction.edit_original_response(embed=embed, attachments=attachments)

    @bot.slash_command(
        name="register_governor",
        description="Register one of your accounts by Governor ID.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.02")
    @safe_command
    @track_usage()
    async def register_governor(
        ctx: discord.ApplicationContext,
        account_type: str = discord.Option(
            str,
            "Choose account type",
            choices=[
                "Main",
                "Alt 1",
                "Alt 2",
                "Alt 3",
                "Alt 4",
                "Alt 5",
                "Farm 1",
                "Farm 2",
                "Farm 3",
                "Farm 4",
                "Farm 5",
                "Farm 6",
                "Farm 7",
                "Farm 8",
                "Farm 9",
                "Farm 10",
            ],
        ),
        governor_id: str = discord.Option(str, "Your in-game Governor ID"),
    ):

        # Single, ephemeral ack
        await safe_defer(ctx, ephemeral=True)

        gid_raw = (governor_id or "").strip()
        if not gid_raw.isdigit():
            await ctx.interaction.edit_original_response(
                content="❌ Please enter a **numeric** Governor ID (e.g., `2441482`).\nTip: try `/mygovernorid` to look it up from your name.",
                embed=None,
                view=None,
            )
            return
        gid = gid_raw  # already numeric

        # Load registry (fail gracefully)
        try:
            registry = load_registry() or {}
        except Exception as e:
            logger.exception("[register_governor] load_registry failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Could not load the registry: `{type(e).__name__}: {e}`"
            )
            return

        # Prevent duplicate registration across users
        for uid, data in registry.items():
            for acc_type, details in (data.get("accounts", {}) or {}).items():
                if str(details.get("GovernorID", "")).strip() == gid:
                    existing_user = data.get("discord_name", f"<@{uid}>")
                    await ctx.interaction.edit_original_response(
                        content=(
                            f"❌ This Governor ID `{gid}` is already registered to **{existing_user}** ({acc_type}).\n"
                            "If you believe this is incorrect, please contact an admin."
                        ),
                        embed=None,
                        view=None,
                    )
                    return

        # Match against cached roster
        all_rows = (_name_cache or {}).get("rows", []) if isinstance(_name_cache, dict) else []
        matched_row = next(
            (r for r in all_rows if str(r.get("GovernorID", "")).strip() == gid), None
        )
        if not matched_row:
            await ctx.interaction.edit_original_response(
                content=(
                    f"❌ Governor ID `{gid}` was not found in the database.\n"
                    "Try `/mygovernorid` to look it up from your name."
                ),
                embed=None,
                view=None,
            )
            return

        governor_name = matched_row.get("GovernorName", "Unknown")

        # Hand off to the confirmation view
        view = RegisterGovernorView(ctx.user, account_type, gid, governor_name)
        await ctx.interaction.edit_original_response(
            content=f"⚙️ Register `{account_type}` as **{governor_name}** (ID: `{gid}`)?",
            embed=None,
            view=view,
        )

    @bot.slash_command(
        name="modify_registration",
        description="Update or REMOVE one of your registered Governor accounts.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.05")
    @safe_command
    @track_usage()
    async def modify_registration(
        ctx: discord.ApplicationContext,
        account_type: str = discord.Option(
            str,
            "Which account do you want to update or REMOVE?",
            choices=[
                "Main",
                "Alt 1",
                "Alt 2",
                "Alt 3",
                "Alt 4",
                "Alt 5",
                "Farm 1",
                "Farm 2",
                "Farm 3",
                "Farm 4",
                "Farm 5",
                "Farm 6",
                "Farm 7",
                "Farm 8",
                "Farm 9",
                "Farm 10",
            ],
        ),
        new_governor_id: str = discord.Option(str, "New Governor ID to assign or REMOVE"),
    ):

        await safe_defer(ctx, ephemeral=True)

        # --- Load registry + cache safely
        try:
            registry = load_registry() or {}
        except Exception as e:
            logger.exception("[modify_registration] load_registry failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Could not load your registrations: `{type(e).__name__}: {e}`",
                embed=None,
                view=None,
            )
            return

        all_rows = (_name_cache or {}).get("rows", []) if isinstance(_name_cache, dict) else []

        # Registry keys may be str or int; support both
        uid_str = str(ctx.user.id)
        uid_int = ctx.user.id
        user_rec = registry.get(uid_str) or registry.get(uid_int) or {}
        user_accounts = user_rec.get("accounts") or {}

        # Ensure this slot exists
        if account_type not in user_accounts:
            await ctx.interaction.edit_original_response(
                content=f"❌ You haven't registered `{account_type}` yet. Use `/register_governor` instead.",
                embed=None,
                view=None,
            )
            return

        raw = (new_governor_id or "").strip()

        # --- Remove flow
        if raw.upper() == "REMOVE":
            view = ConfirmRemoveView(ctx.user, account_type)
            await ctx.interaction.edit_original_response(
                content=f"⚠️ Are you sure you want to **remove** `{account_type}` from your registration?",
                embed=None,
                view=view,
            )
            return

        # --- Update flow: validate numeric GovernorID
        if not raw.isdigit():
            await ctx.interaction.edit_original_response(
                content="❌ Please enter a **numeric** Governor ID (or type `REMOVE` to delete). "
                "Tip: try `/mygovernorid` to look it up from your name.",
                embed=None,
                view=None,
            )
            return
        gid = raw

        # Look up in roster cache
        matched_row = next(
            (r for r in all_rows if str(r.get("GovernorID", "")).strip() == gid), None
        )
        if not matched_row:
            await ctx.interaction.edit_original_response(
                content=(
                    f"❌ Governor ID `{gid}` not found in the database.\n"
                    "Try `/mygovernorid` to look it up from your name."
                ),
                embed=None,
                view=None,
            )
            return

        # Prevent duplicate registration across other users
        for other_uid, data in registry.items():
            if str(other_uid) == uid_str:
                continue
            for acc_type, details in (data.get("accounts") or {}).items():
                if str(details.get("GovernorID", "")).strip() == gid:
                    existing_user = data.get("discord_name", f"<@{other_uid}>")
                    await ctx.interaction.edit_original_response(
                        content=(
                            f"❌ This Governor ID `{gid}` is already registered to "
                            f"**{existing_user}** ({acc_type})."
                        ),
                        embed=None,
                        view=None,
                    )
                    return

        gov_name = matched_row.get("GovernorName", "Unknown")
        view = ModifyGovernorView(ctx.user, account_type, gid, gov_name)
        await ctx.interaction.edit_original_response(
            content=f"⚙️ Update `{account_type}` to **{gov_name}** (ID: `{gid}`)?",
            embed=None,
            view=view,
        )

    # --- helpers (reuse if already present) ---
    def _get_user_key(registry: dict, user_id: int) -> str | None:
        if not registry:
            return None
        s = str(user_id)
        if s in registry:
            return s
        if user_id in registry:
            registry[s] = registry.pop(user_id)
            return s
        return None

    def _parse_user_id(text: str | None) -> int | None:
        if not text:
            return None
        try:
            import re

            m = re.search(r"\d{15,22}", str(text))
            return int(m.group(0)) if m else None
        except Exception:
            return None

    # --- UNIFIED autocomplete for account_type (works with both commands) ---
    async def _account_type_ac(ctx: discord.AutocompleteContext):
        try:
            # Prefer resolved member if present (for /remove_registration)
            opt_user = ctx.options.get("discord_user")
            if isinstance(opt_user, discord.User):
                target_id = opt_user.id
            else:
                # Fall back to the pasted ID field (works for both commands)
                target_id = _parse_user_id(ctx.options.get("user_id"))

            fallback = [
                "Main",
                "Alt 1",
                "Alt 2",
                "Alt 3",
                "Alt 4",
                "Alt 5",
                "Farm 1",
                "Farm 2",
                "Farm 3",
                "Farm 4",
                "Farm 5",
                "Farm 6",
                "Farm 7",
                "Farm 8",
                "Farm 9",
                "Farm 10",
            ]
            if not target_id:
                return fallback

            registry = load_registry() or {}
            user_key = _get_user_key(registry, target_id)
            accounts = (registry.get(user_key) or {}).get("accounts", {})
            if not accounts:
                return []

            existing = list(accounts.keys())
            prefix = (ctx.value or "").lower()
            if prefix:
                existing = [x for x in existing if x.lower().startswith(prefix)]
            return existing[:25]
        except Exception:
            return [
                "Main",
                "Alt 1",
                "Alt 2",
                "Alt 3",
                "Alt 4",
                "Alt 5",
                "Farm 1",
                "Farm 2",
                "Farm 3",
                "Farm 4",
                "Farm 5",
                "Farm 6",
                "Farm 7",
                "Farm 8",
                "Farm 9",
                "Farm 10",
            ]

    # === Normal command (member picker OR raw ID) ===
    @bot.slash_command(
        name="remove_registration",
        description="Admin-only: Remove a registered Governor account from a user.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.08")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def remove_registration(
        ctx: discord.ApplicationContext,
        # ✅ REQUIRED FIRST
        account_type: str = discord.Option(
            str, "Which account to remove", autocomplete=_account_type_ac, required=True
        ),
        # optional pick-a-member (works if they’re resolvable)
        discord_user: discord.User = discord.Option(
            discord.User, "Pick a server user (if present)", required=False
        ),
        # optional raw ID (works even if they left / invalid USER)
        user_id: str = discord.Option(str, "Or paste a Discord user ID", required=False),
    ):
        await safe_defer(ctx, ephemeral=True)

        # Resolve target ID (unchanged)
        target_user_id = (
            discord_user.id if isinstance(discord_user, discord.User) else _parse_user_id(user_id)
        )
        if not target_user_id:
            await ctx.interaction.edit_original_response(
                content="❌ Please pick a user **or** paste a valid Discord ID."
            )
            return

        # Load registry safely
        try:
            registry = load_registry() or {}
        except Exception as e:
            logger.exception("[remove_registration] load_registry failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to load registry: `{type(e).__name__}: {e}`"
            )
            return

        user_key = _get_user_key(registry, target_user_id)
        user_rec = registry.get(user_key) if user_key is not None else None
        accounts = (user_rec or {}).get("accounts", {})

        if not user_rec or account_type not in accounts:
            target_display = (
                discord_user.mention
                if isinstance(discord_user, discord.User)
                else f"`{target_user_id}`"
            )
            await ctx.interaction.edit_original_response(
                content=f"⚠️ `{account_type}` is not registered for {target_display}."
            )
            return

        removed = accounts.pop(account_type, None)

        if not accounts:
            registry.pop(user_key, None)
        else:
            user_rec["accounts"] = accounts
            registry[user_key] = user_rec

        try:
            save_registry(registry)
        except Exception as e:
            logger.exception("[remove_registration] save_registry failed")
            # Best-effort rollback
            try:
                registry.setdefault(user_key, {}).setdefault("accounts", {})[account_type] = (
                    removed or {}
                )
                save_registry(registry)
            except Exception:
                pass
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to save changes: `{type(e).__name__}: {e}`"
            )
            return

        gov_name = (removed or {}).get("GovernorName", "Unknown")
        gov_id = (removed or {}).get("GovernorID", "Unknown")
        target_display = (
            discord_user.mention
            if isinstance(discord_user, discord.User)
            else f"`{target_user_id}`"
        )

        logger.info(
            "[ADMIN] %s removed %s (%s – ID: %s) from %s",
            getattr(ctx, "user", None) or getattr(ctx, "author", None),
            account_type,
            gov_name,
            gov_id,
            target_display,
        )

        await ctx.interaction.edit_original_response(
            content=(
                f"🗑️ Removed `{account_type}` "
                f"({gov_name} – ID: `{gov_id}`) from {target_display}."
            )
        )

    # === ID-only cleanup command (bypasses Discord USER validation entirely) ===
    @bot.slash_command(
        name="remove_registration_by_id",
        description="Admin: remove a registered account by Discord ID (works if user not in server)",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def remove_registration_by_id(
        ctx: discord.ApplicationContext,
        user_id: str = discord.Option(str, "Paste a Discord user ID or mention", required=True),
        account_type: str = discord.Option(
            str, "Which account to remove", autocomplete=_account_type_ac, required=True
        ),
    ):
        await safe_defer(ctx, ephemeral=True)

        target_id = _parse_user_id(user_id)
        if not target_id:
            await ctx.interaction.edit_original_response(
                content="❌ Please paste a valid Discord user ID (15–22 digits) or a mention."
            )
            return

        try:
            registry = load_registry() or {}
        except Exception as e:
            logger.exception("[remove_registration_by_id] load_registry failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to load registry: `{type(e).__name__}: {e}`"
            )
            return

        user_key = _get_user_key(registry, target_id)
        user_rec = registry.get(user_key) if user_key is not None else None
        accounts = (user_rec or {}).get("accounts", {})

        if not user_rec:
            await ctx.interaction.edit_original_response(
                content=f"⚠️ No registry entry found for ID `{target_id}`."
            )
            return

        if account_type not in accounts:
            await ctx.interaction.edit_original_response(
                content=f"⚠️ `{account_type}` is not registered for ID `{target_id}`."
            )
            return

        removed = accounts.pop(account_type, None)

        if not accounts:
            registry.pop(user_key, None)
        else:
            user_rec["accounts"] = accounts
            registry[user_key] = user_rec

        try:
            save_registry(registry)
        except Exception as e:
            logger.exception("[remove_registration_by_id] save_registry failed")
            try:
                registry.setdefault(user_key, {}).setdefault("accounts", {})[account_type] = (
                    removed or {}
                )
                save_registry(registry)
            except Exception:
                pass
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to save changes: `{type(e).__name__}: {e}`"
            )
            return

        gov_name = (removed or {}).get("GovernorName", "Unknown")
        gov_id = (removed or {}).get("GovernorID", "Unknown")

        logger.info(
            "[ADMIN] %s removed %s (%s – ID: %s) from DiscordID %s",
            getattr(ctx, "user", None) or getattr(ctx, "author", None),
            account_type,
            gov_name,
            gov_id,
            target_id,
        )

        await ctx.interaction.edit_original_response(
            content=(
                f"🗑️ Removed `{account_type}` "
                f"({gov_name} – GovID: `{gov_id}`) from DiscordID `{target_id}`."
            )
        )

    @bot.slash_command(
        name="mykvkstats",
        description="View your personal KVK stats for each registered game account.",
        guild_ids=[GUILD_ID],
    )
    @channel_only(KVK_PLAYER_STATS_CHANNEL_ID, admin_override=True)
    @versioned("v2.20")
    @safe_command
    @track_usage()
    async def mykvkstats(ctx: discord.ApplicationContext):
        # We always keep the selector private to the caller
        await safe_defer(ctx, ephemeral=True)

        # Load registry (support str/int keys)
        try:
            # Offload file/IO-bound registry load to a thread to avoid blocking the event loop
            registry = await asyncio.to_thread(load_registry)
            registry = registry or {}
        except Exception as e:
            logger.exception("[/mykvkstats] load_registry failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Could not load registry: `{type(e).__name__}: {e}`"
            )
            return

        uid_str, uid_int = str(ctx.user.id), ctx.user.id
        user_data = registry.get(uid_str) or registry.get(uid_int)

        if not user_data or not user_data.get("accounts"):
            # Reuse your existing action view as a nice fallback
            view = MyRegsActionView(author_id=ctx.user.id, has_regs=False)
            msg = await ctx.interaction.edit_original_response(
                content="You don’t have any Governor accounts registered yet. Use the options below:",
                view=view,
            )
            view.set_message_ref(msg)
            return

        accounts = user_data["accounts"]

        # Best-effort: load last-KVK cache once so we can attach it to any governor rows we fetch.
        # This is offloaded to a thread to avoid blocking the event loop.
        last_kvk_map = {}
        try:
            from constants import PLAYER_STATS_LAST_CACHE
            from file_utils import read_json_safe, run_blocking_in_thread

            try:
                data = await run_blocking_in_thread(
                    lambda: read_json_safe(PLAYER_STATS_LAST_CACHE),
                    name="read_last_kvk_cache",
                    meta={"cmd": "mykvkstats"},
                )
                if isinstance(data, dict):
                    # normalize into a simple map keyed by GovernorID
                    data.pop("_meta", None)
                    last_kvk_map = {k: v for k, v in data.items() if k != "_meta"}
                else:
                    last_kvk_map = {}
            except FileNotFoundError:
                # not present yet — that's fine
                last_kvk_map = {}
            except Exception:
                logger.exception("[/mykvkstats] reading PLAYER_STATS_LAST_CACHE failed")
                last_kvk_map = {}
        except Exception:
            # If file_utils/constant import fails for any reason, continue without last-kvk data.
            last_kvk_map = {}

        # Single-account path → post PUBLIC embed immediately
        if len(accounts) == 1:
            ((_, info),) = accounts.items()
            gid = normalize_governor_id(info.get("GovernorID"))
            if not gid:
                await ctx.interaction.edit_original_response(
                    content="❌ Your registration has no valid Governor ID."
                )
                return

            try:
                # Offload potential IO-bound stat row load
                row = await asyncio.to_thread(load_stat_row, gid)
            except Exception as e:
                logger.exception("[/mykvkstats] load_stat_row failed")
                await ctx.interaction.edit_original_response(
                    content=f"❌ Could not load stats: `{type(e).__name__}: {e}`"
                )
                return

            if not row:
                await ctx.interaction.edit_original_response(
                    content=f"❌ Stats not found for Governor ID `{gid}`."
                )
                return

            # Attach last-KVK row (if available) to the loaded stat row so embed builders can use it
            try:
                lk = last_kvk_map.get(str(gid))
                if lk:
                    # shallow attach; embed builders expect governor_data['last_kvk']
                    row["last_kvk"] = lk
            except Exception:
                logger.exception("[/mykvkstats] Failed to attach last_kvk for %s", gid)

            try:
                embeds, file = build_stats_embed(row, ctx.user)
                # build_stats_embed returns (list[discord.Embed], discord.File)
            except Exception as e:
                logger.exception("[/mykvkstats] build_stats_embed failed")
                await ctx.interaction.edit_original_response(
                    content=f"❌ Failed to build stats: `{type(e).__name__}: {e}`"
                )
                return

            # PUBLIC post (send all embeds together)
            try:
                if file is not None:
                    await ctx.channel.send(embeds=embeds, files=[file])
                else:
                    await ctx.channel.send(embeds=embeds)
            except Exception:
                # fallback: send embeds only if file send fails
                try:
                    await ctx.channel.send(embeds=embeds)
                except Exception:
                    logger.exception("[/mykvkstats] failed to send stats embed(s) to channel")

            # Silence the ephemeral placeholder instead of confirming
            try:
                await ctx.interaction.edit_original_response(content=" ", view=None)
            except Exception:
                pass
            return

        # Multi-account path → ephemeral dropdown + helper buttons
        try:
            # Keep preferred ordering first, then append any remaining slots deterministically
            ordered_accounts = {slot: accounts[slot] for slot in ACCOUNT_ORDER if slot in accounts}
            # append remaining keys not in ACCOUNT_ORDER in sorted order
            remaining = [s for s in sorted(accounts.keys()) if s not in ordered_accounts]
            for s in remaining:
                ordered_accounts[s] = accounts[s]
            view = MyKVKStatsSelectView(ctx=ctx, accounts=ordered_accounts, author_id=ctx.user.id)
            # Attach last_kvk_map to the view so callbacks can reuse it when they load stat rows.
            # (The view callback should check for `self._last_kvk_map` and attach when building embeds.)
            try:
                view._last_kvk_map = last_kvk_map
            except Exception:
                # non-fatal; view may not accept new attrs in some contexts, but that's unlikely
                pass
        except Exception as e:
            logger.exception("[/mykvkstats] MyKVKStatsSelectView init failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to build account selector: `{type(e).__name__}: {e}`"
            )
            return

        await ctx.interaction.edit_original_response(
            content="Select an account below to view your stats:", view=view
        )

    @bot.slash_command(
        name="refresh_stats_cache",
        description="Admin only: Refresh player stats cache",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.10")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def refresh_stats_cache(ctx):

        await safe_defer(ctx, ephemeral=True)

        try:
            # Build the main player stats cache (existing behaviour)
            main_started = datetime.now(UTC)
            from player_stats_cache import (
                build_lastkvk_player_stats_cache,
                build_player_stats_cache,
            )

            main_result = None
            main_count = None
            main_error = None
            try:
                main_result = await build_player_stats_cache()
                if isinstance(main_result, int):
                    main_count = main_result
                elif isinstance(main_result, dict):
                    # prefer top-level "_meta".count if present, otherwise "count"
                    main_count = (main_result.get("_meta") or {}).get("count") or main_result.get(
                        "count"
                    )
            except Exception as e:
                main_error = f"{type(e).__name__}: {e}"
                logger.exception("[/refresh_stats_cache] build_player_stats_cache failed")

            main_dur = (datetime.now(UTC) - main_started).total_seconds()

            # Build the last-KVK cache (best-effort, report separately)
            last_started = datetime.now(UTC)
            last_result = None
            last_count = None
            last_error = None
            try:
                last_result = await build_lastkvk_player_stats_cache()
                if isinstance(last_result, dict):
                    # last_result expected shape: { "_meta": {...}, "<GovernorID>": {...}, ... }
                    last_count = (last_result.get("_meta") or {}).get("count") or last_result.get(
                        "count"
                    )
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                logger.exception("[/refresh_stats_cache] build_lastkvk_player_stats_cache failed")

            last_dur = (datetime.now(UTC) - last_started).total_seconds()

            # Compose human-friendly message summarising both builds
            parts = []
            if main_error:
                parts.append(f"❌ Player stats cache build failed: `{main_error}`")
            else:
                if main_count is not None:
                    parts.append(
                        f"✅ Player stats cache refreshed ({main_count} records) ⏱ {main_dur:.1f}s"
                    )
                else:
                    parts.append(f"✅ Player stats cache refreshed ⏱ {main_dur:.1f}s")

            if last_error:
                parts.append(
                    f"⚠️ Last-KVK cache build failed (non-fatal): `{last_error}` — the main cache is available."
                )
            else:
                if last_count is not None:
                    parts.append(
                        f"✅ Last-KVK cache refreshed ({last_count} records) ⏱ {last_dur:.1f}s"
                    )
                else:
                    parts.append(f"✅ Last-KVK cache refreshed ⏱ {last_dur:.1f}s")

            # Final combined message
            msg = " \n".join(parts)
            logger.info("[/refresh_stats_cache] %s", msg.replace("\n", " | "))

            await ctx.interaction.edit_original_response(content=msg)

        except Exception as e:
            logger.exception("[/refresh_stats_cache] failed")
            try:
                await ctx.interaction.edit_original_response(
                    content=f"❌ Failed to refresh cache:\n```{type(e).__name__}: {e}```"
                )
            except Exception:
                # If editing the original response failed, try to send a followup
                try:
                    await ctx.followup.send(
                        f"❌ Failed to refresh cache: `{type(e).__name__}: {e}`", ephemeral=True
                    )
                except Exception:
                    logger.exception("[/refresh_stats_cache] failed to report error to user")

    @bot.slash_command(
        name="player_profile",
        description="Show a player's profile (Admin/Leadership only)",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.11")
    @safe_command
    @track_usage()
    async def player_profile_command(
        ctx: discord.ApplicationContext,
        governor_id: int | None = discord.Option(int, "Governor ID", required=False),
        governor_name: str | None = discord.Option(
            str,
            "Governor name",
            autocomplete=governor_name_autocomplete,
            required=False,
        ),
    ):

        # --- Gates BEFORE any defer (keep ephemeral one-shot replies here) ---
        if not _is_allowed_channel(ctx.channel):
            mentions = " or ".join(f"<#{cid}>" for cid in ALLOWED_CHANNEL_IDS)
            await ctx.respond(f"🔒 This command can only be used in {mentions}.", ephemeral=True)
            return

        member = ctx.author if isinstance(ctx.author, discord.Member) else None
        if not (_is_admin(ctx.user) or _has_leadership_role(member)):
            await ctx.respond(
                "❌ This command is restricted to Admin or Leadership.", ephemeral=True
            )
            return

        # --- Resolve target (accept autocomplete value as ID) ---
        target_id: int | None = None

        if governor_id is not None:
            # Option is int already; clamp to positive
            if int(governor_id) > 0:
                target_id = int(governor_id)

        elif governor_name:
            name = governor_name.strip()
            if name.isdigit():
                # User picked an autocomplete value (ID as string)
                target_id = int(name)
            else:
                # Free-text fuzzy pass
                matches = search_by_governor_name(name, limit=10)  # -> [(name, gid), ...]
                if not matches:
                    await ctx.respond("No matches found.", ephemeral=True)
                    return
                if len(matches) > 1:
                    # Prefer a view that restricts interaction to the invoker if available
                    # In player_profile_command when multiple matches:
                    try:
                        view = GovernorSelectView(matches, author_id=ctx.user.id)
                    except TypeError:
                        # Back-compat if the class signature differs
                        view = GovernorSelectView(matches)
                    await ctx.respond("Multiple matches — pick one:", view=view, ephemeral=True)
                    return
                target_id = int(matches[0][1])

        if not target_id:
            await ctx.respond(
                "Provide either **governor_id** or pick a name from the list.", ephemeral=True
            )
            return

        # --- Hand off to the helper; make sure we don't leave the interaction hanging on error
        try:
            # Helper is expected to handle its own defer + posting to the channel
            await send_profile_to_channel(ctx.interaction, target_id, ctx.channel)
        except Exception as e:
            logger.exception("[/player_profile] send_profile_to_channel failed (gid=%s)", target_id)
            # If nothing has acknowledged yet, send a clean error; otherwise use followup.
            if not ctx.interaction.response.is_done():
                await ctx.respond(
                    f"❌ Failed to load profile: `{type(e).__name__}: {e}`", ephemeral=True
                )
            else:
                try:
                    await ctx.followup.send(
                        f"❌ Failed to load profile: `{type(e).__name__}: {e}`", ephemeral=True
                    )
                except Exception:
                    pass

    @bot.slash_command(
        name="import_locations",
        description="Admin: import player locations from an attached output.csv",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def import_locations(
        ctx: discord.ApplicationContext,
        file: discord.Attachment | None = discord.Option(
            discord.Attachment, "Upload output.csv", required=False
        ),
    ):

        await safe_defer(ctx, ephemeral=True)
        started = datetime.now(UTC)

        # --- find the attachment (prefer option, fallback to ctx.attachments) ---
        attach = file
        if attach is None:
            try:
                attach = next(
                    (a for a in (ctx.attachments or []) if a.filename.lower().endswith(".csv")),
                    None,
                )
            except Exception:
                attach = None

        if not attach:
            await ctx.interaction.edit_original_response(
                content="❌ Please attach your CSV (e.g., `output.csv`) using the `file` option."
            )
            return

        # --- basic validation ---
        fname = (attach.filename or "").lower()
        if not fname.endswith(".csv"):
            await ctx.interaction.edit_original_response(
                content=f"❌ `{attach.filename}` isn’t a CSV file. Please upload a `.csv` (e.g., `output.csv`)."
            )
            return

        # Optional: size guard (e.g., 10 MB)
        try:
            fsize = getattr(attach, "size", None)
            if isinstance(fsize, int) and fsize > 10 * 1024 * 1024:
                await ctx.interaction.edit_original_response(
                    content=f"❌ File too large ({fsize/1024/1024:.1f} MB). Please keep CSV under **10 MB**."
                )
                return
        except Exception:
            pass

        # --- read + parse ---
        try:
            csv_bytes = await attach.read()
        except Exception as e:
            logger.exception("[/import_locations] failed to read attachment")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to read file: `{type(e).__name__}: {e}`"
            )
            return

        try:
            rows = parse_output_csv(csv_bytes)
        except Exception as e:
            logger.exception("[/import_locations] parse_output_csv crashed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to parse CSV: `{type(e).__name__}: {e}`"
            )
            return

        if not rows:
            await ctx.interaction.edit_original_response(
                content="⚠️ No valid rows found in the CSV."
            )
            return

        # --- merge into staging (likely blocking) ---
        try:
            staging_rows, total_tracked = await asyncio.to_thread(load_staging_and_merge, rows)
        except Exception as e:
            logger.exception("[/import_locations] load_staging_and_merge failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to import rows: `{type(e).__name__}: {e}`"
            )
            return

        dur = (datetime.now(UTC) - started).total_seconds()
        count_part = f"Imported **{staging_rows}** row{'s' if staging_rows != 1 else ''}."
        tracked_part = (
            f" Total tracked now **{total_tracked}**." if total_tracked is not None else ""
        )
        msg = f"✅ {count_part}{tracked_part} ⏱ {dur:.1f}s"

        await ctx.interaction.edit_original_response(content=msg)

    @bot.slash_command(
        name="player_location",
        description="Show last-known (X,Y) for a Governor (by ID or Name).",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.07")
    @safe_command
    @track_usage()
    async def player_location(
        ctx: discord.ApplicationContext,
        governor_id: int | None = discord.Option(int, "Governor ID", required=False),
        governor_name: str | None = discord.Option(
            str,
            "Governor name",
            autocomplete=governor_name_autocomplete,  # reuse the same autocomplete
            required=False,
        ),
        ephemeral: bool = discord.Option(bool, "Only show to me", required=False, default=False),
    ):
        # Channel + role gates (same model used in /player_profile)
        if not _is_allowed_channel(ctx.channel):
            mentions = " or ".join(f"<#{cid}>" for cid in ALLOWED_CHANNEL_IDS)
            await ctx.respond(f"🔒 This command can only be used in {mentions}.", ephemeral=True)
            return

        member = ctx.author if isinstance(ctx.author, discord.Member) else None
        if not (_is_admin(ctx.user) or _has_leadership_role(member)):
            await ctx.respond(
                "❌ This command is restricted to Admin or Leadership.", ephemeral=True
            )
            return

        # Resolve target ID (ID takes precedence; name can be autocomplete-id or fuzzy free-text)
        target_id: int | None = None
        if governor_id is not None:
            if int(governor_id) > 0:
                target_id = int(governor_id)
        elif governor_name:
            name = governor_name.strip()
            if name.isdigit():
                target_id = int(name)  # user selected an autocomplete value (ID as string)
            else:
                # final fuzzy pass for free-typed names
                matches = search_by_governor_name(name, limit=10)  # -> [(name, gid), ...]
                if not matches:
                    await ctx.respond("No matches found.", ephemeral=True)
                    return
                if len(matches) > 1:
                    # Ephemeral chooser; lock to the invoker; final post will respect `ephemeral`
                    try:
                        view = LocationSelectView(
                            matches, ephemeral=ephemeral, author_id=ctx.user.id
                        )
                    except TypeError:
                        # Back-compat if the view doesn't accept author_id yet
                        view = LocationSelectView(matches, ephemeral=ephemeral)
                    await ctx.respond("Multiple matches — pick one:", view=view, ephemeral=True)
                    return
                target_id = int(matches[0][1])

        if not target_id:
            await ctx.respond(
                "Provide either **governor_id** or pick a name from the list.", ephemeral=True
            )
            return

        # Single-ack from here on
        await safe_defer(ctx, ephemeral=ephemeral)

        try:
            warm_cache()  # loads/refreshes the profile cache
            p = get_profile_cached(target_id)
        except Exception as e:
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to read cache: `{type(e).__name__}: {e}`", embed=None, view=None
            )
            return

        if not p:
            await ctx.interaction.edit_original_response(
                content=f"❌ GovernorID `{target_id}` not found.", embed=None, view=None
            )
            return

        x = p.get("X")
        y = p.get("Y")
        updated = p.get("LocationUpdated")

        embed = discord.Embed(
            title="📍 Player Location",
            description=f"**{p.get('GovernorName','Unknown')}** (`{target_id}`)",
            color=0x5865F2,
        )
        embed.add_field(
            name="Coordinates",
            value=f"X **{x if x is not None else '—'}** • Y **{y if y is not None else '—'}**",
            inline=False,
        )
        if x is None or y is None:
            embed.add_field(name="Note", value="No recent coordinates found", inline=False)
        # ...existing embed building...
        if updated:
            dt = None
            if isinstance(updated, datetime):
                dt = updated if updated.tzinfo else updated.replace(tzinfo=UTC)
            else:
                # Try ISO parse (supports "...Z")
                try:
                    iso = str(updated).replace("Z", "+00:00")
                    dt = datetime.fromisoformat(iso)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=UTC)
                except Exception:
                    dt = None

            if dt:
                embed.timestamp = dt  # ✅ Discord renders this automatically
                embed.set_footer(text="Last updated")
            else:
                embed.set_footer(text=f"Last updated: {updated}")  # fallback if unparsable

        await ctx.interaction.edit_original_response(
            embed=embed, view=RefreshLocationView(target_id=target_id, ephemeral=ephemeral)
        )

    @bot.slash_command(
        name="my_registrations",
        description="See which Governor accounts you’ve registered to your Discord user.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.09")
    @safe_command
    @track_usage()
    async def my_registrations(ctx: discord.ApplicationContext):
        logger.info(
            "[my_registrations] user=%s (%s)", ctx.user.id, getattr(ctx.user, "display_name", "?")
        )

        # --- Defer ASAP (ephemeral) so the token stays alive
        async def ensure_deferred(ephemeral: bool = True) -> None:
            try:
                ir = getattr(ctx, "interaction", None)
                if ir and hasattr(ir, "response") and not ir.response.is_done():
                    await ir.response.defer(ephemeral=ephemeral)
                else:
                    if hasattr(ctx, "defer"):
                        try:
                            await ctx.defer(ephemeral=ephemeral)
                        except Exception:
                            pass
            except Exception:
                logger.debug("[my_registrations] defer skipped/failed; continuing.")

        await ensure_deferred(ephemeral=True)

        # --- Load registry off the event loop
        async def load_registry_async():
            return await asyncio.to_thread(load_registry)

        try:
            registry: dict[str, Any] = await load_registry_async() or {}
        except Exception:
            logger.exception("[my_registrations] load_registry failed")
            msg = "⚠️ Sorry, I couldn’t load your registrations. Please try again shortly."
            try:
                await ctx.interaction.edit_original_response(content=msg, embed=None, view=None)
            except Exception:
                try:
                    await ctx.followup.send(msg, ephemeral=True)
                except Exception:
                    pass
            return

        user_key_str = str(ctx.user.id)
        user_data = registry.get(user_key_str) or registry.get(ctx.user.id) or {}
        accounts = user_data.get("accounts", {}) or {}

        # --- Build lines in a predictable order; fall back to sorted keys
        try:
            order = list(ACCOUNT_ORDER)
        except NameError:
            order = sorted(accounts.keys())

        lines: list[str] = []
        for slot in order:
            info = accounts.get(slot)
            if info:
                gid = str(info.get("GovernorID", "")).strip()
                gname = str(info.get("GovernorName", "")).strip()
                label = f"**{gname}** (`{gid}`)" if (gname or gid) else "—"
                lines.append(f"• **{slot}** — {label}")

        has_regs = len(lines) > 0
        desc = "\n".join(lines) if has_regs else "You don’t have any accounts registered yet."

        # --- Guard Discord 4096-char embed description limit
        if len(desc) > 4000:
            logger.warning("[my_registrations] description too long (%d); truncating", len(desc))
            desc = desc[:3970] + "\n… (truncated)"

        embed = discord.Embed(
            title="Your Registered Accounts",
            description=desc,
            colour=discord.Colour.green() if has_regs else discord.Colour.orange(),
        )
        embed.set_footer(text=f"Requested by {getattr(ctx.user, 'display_name', ctx.user.name)}")

        # --- Build the action view defensively
        view = None
        try:
            view = MyRegsActionView(author_id=ctx.user.id, has_regs=has_regs)
        except Exception:
            logger.exception(
                "[my_registrations] MyRegsActionView init failed; continuing without view"
            )

        # --- Deliver response: edit the deferred original; if not found, followup
        sent_msg = None
        try:
            sent_msg = await ctx.interaction.edit_original_response(embed=embed, view=view)
        except discord.NotFound:
            sent_msg = await ctx.followup.send(embed=embed, view=view, ephemeral=True)
        except discord.InteractionResponded:
            sent_msg = await ctx.followup.send(embed=embed, view=view, ephemeral=True)
        except Exception:
            logger.exception("[my_registrations] edit/respond failed")
            try:
                sent_msg = await ctx.followup.send(
                    "Here are your registrations:", embed=embed, view=view, ephemeral=True
                )
            except Exception:
                pass

        # Hand the message to the view so it can disable itself on timeout
        try:
            if view and hasattr(view, "set_message_ref") and sent_msg:
                view.set_message_ref(sent_msg)
        except Exception:
            pass

    # --- Admin-only: register a governor for another user ---
    @bot.slash_command(
        name="admin_register_governor",
        description="Admin: register a player's account by Discord user + Governor ID.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def admin_register_governor(
        ctx: discord.ApplicationContext,
        discord_user: discord.Option(discord.User, "Player's Discord account"),
        account_type: discord.Option(
            str,
            "Account type",
            choices=[
                "Main",
                "Alt 1",
                "Alt 2",
                "Alt 3",
                "Alt 4",
                "Alt 5",
                "Farm 1",
                "Farm 2",
                "Farm 3",
                "Farm 4",
                "Farm 5",
                "Farm 6",
                "Farm 7",
                "Farm 8",
                "Farm 9",
                "Farm 10",
            ],
        ),
        governor_id: discord.Option(str, "Governor ID to register"),
    ):
        await safe_defer(ctx, ephemeral=True)

        # Validate governor exists in cache
        all_rows = _name_cache.get("rows", [])
        row = next(
            (r for r in all_rows if str(r.get("GovernorID")).strip() == governor_id.strip()), None
        )
        if not row:
            await ctx.respond(
                f"❌ Governor ID `{governor_id}` not found in the database. Ask the player to try `/mygovernorid`.",
                ephemeral=True,
            )
            return

        gov_name = row.get("GovernorName", "Unknown")

        registry = load_registry()

        # Hard rule: prevent duplicates across users
        for uid, data in registry.items():
            for acc_type, details in data.get("accounts", {}).items():
                if str(details.get("GovernorID")) == governor_id.strip():
                    await ctx.respond(
                        f"❌ `{governor_id}` (**{gov_name}**) is already registered to **{data.get('discord_name','another user')}** ({acc_type}).",
                        ephemeral=True,
                    )
                    return

        uid = str(discord_user.id)
        entry = registry.setdefault(
            uid, {"discord_id": uid, "discord_name": str(discord_user), "accounts": {}}
        )
        entry["discord_name"] = str(discord_user)  # keep fresh

        # Upsert the slot
        entry["accounts"][account_type] = {
            "GovernorID": governor_id.strip(),
            "GovernorName": gov_name,
        }
        save_registry(registry)

        # DM the player if possible
        try:
            embed = discord.Embed(
                title="✅ Registration Added",
                description=f"Your **{account_type}** has been set to **{gov_name}** (`{governor_id}`) by an admin.",
                color=0x2ECC71,
            )
            await discord_user.send(embed=embed)
        except discord.Forbidden:
            pass

        await ctx.respond(
            f"✅ Registered **{gov_name}** (`{governor_id}`) as **{account_type}** for {discord_user.mention}.",
            ephemeral=True,
        )

    # --- Admin-only: audit registrations and gaps ---
    @bot.slash_command(
        name="registration_audit",
        description="Admin: visualise who is registered, who isn't, and which GovernorIDs are unregistered.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.15")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def registration_audit(ctx: discord.ApplicationContext):
        """
        Builds three CSVs:
          1) registered_accounts.csv  – all accounts in registry (+roles where resolvable)
          2) unregistered_current_governors.csv – CURRENT (SQL view) governors missing from registry
          3) members_without_registration.csv – guild members without any registration
        """
        from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

        await safe_defer(ctx, ephemeral=True)

        guild: discord.Guild | None = ctx.guild
        if not guild:
            await ctx.interaction.edit_original_response(
                content="❌ This command must be used in a server."
            )
            return

        # ---------- GovernorID normalizer & extractor ----------
        def _norm_gid(val) -> str:
            """
            Normalize GovernorID to a canonical string:
            - safe on None
            - unwrap Excel-safe form ="12345"
            - if numeric (int/float/Decimal or numeric-looking string), convert via Decimal(...).to_integral_value()
            - strip leading zeros
            """
            if val is None:
                return ""
            # numeric types first
            if isinstance(val, int):
                s = str(val)
            elif isinstance(val, float):
                try:
                    s = str(Decimal(str(val)).to_integral_value(rounding=ROUND_HALF_UP))
                except Exception:
                    s = str(int(val))
            elif isinstance(val, Decimal):
                s = str(val.to_integral_value(rounding=ROUND_HALF_UP))
            else:
                s = str(val).strip()
                if s.startswith('="') and s.endswith('"') and len(s) >= 3:
                    s = s[2:-1]
                s = s.replace(",", "")  # drop thousands separators if any
                # numeric-looking string? handle decimals/scientific
                if re.fullmatch(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", s):
                    try:
                        s = str(Decimal(s).to_integral_value(rounding=ROUND_HALF_UP))
                    except (InvalidOperation, ValueError):
                        pass
            # finally, ensure digits & remove leading zeros
            digits = re.findall(r"\d+", s)
            if digits:
                s = "".join(digits)
            return s.lstrip("0") or ("0" if s else "")

        def _extract_gov_id(details: dict) -> str:
            """
            Pull a GovernorID out of a registry account dict.
            Accepts many key spellings: 'GovernorID', 'Governor ID', 'GovernorId', 'gov_id', 'govid', etc.
            """
            if not isinstance(details, dict):
                return ""
            for k in (
                "GovernorID",
                "Governor Id",
                "GovernorId",
                "gov_id",
                "govid",
                "GovID",
                "Gov Id",
            ):
                if details.get(k):
                    return str(details[k])
            for k, v in details.items():
                nk = re.sub(r"[^a-z0-9]", "", str(k).lower())
                if (
                    ("governor" in nk and "id" in nk)
                    or nk in ("govid", "govidnumber", "governorid")
                ) and v:
                    return str(v)
            return ""

        # ---------- SQL (via your existing _conn helper) ----------
        def _fetch_active_players():
            sql = """
            SELECT [PowerRank],
                   [GovernorName],
                   [GovernorID],
                   [Alliance],
                   [Power],
                   [KillPoints],
                   [Deads],
                   [T1_Kills],
                   [T2_Kills],
                   [T3_Kills],
                   [T4_Kills],
                   [T5_Kills],
                   [T4&T5_KILLS],
                   [TOTAL_KILLS],
                   [RSS_Gathered],
                   [RSSAssistance],
                   [Helps],
                   [ScanDate],
                   [Troops Power],
                   [City Hall],
                   [Tech Power],
                   [Building Power],
                   [Commander Power],
                   [LOCATION]
            FROM [ROK_TRACKER].[dbo].[v_Active_Players]
            WITH (NOLOCK);
            """
            conn = _conn()
            try:
                cur = conn.cursor()
                cur.execute(sql)
                cols = [c[0] for c in cur.description]
                rows = [dict(zip(cols, r, strict=False)) for r in cur.fetchall()]
                return rows
            finally:
                try:
                    cur.close()
                except Exception:
                    pass
                try:
                    conn.close()
                except Exception:
                    pass

        try:
            sql_rows = await asyncio.to_thread(_fetch_active_players)
        except Exception as e:
            logger.exception("[registration_audit] SQL fetch failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to query SQL view `v_Active_Players`: `{type(e).__name__}: {e}`"
            )
            return

        # ---------- Registry & guild helpers ----------
        registry = load_registry() or {}

        def role_names(member: discord.Member | None) -> tuple[str, str]:
            if member is None:
                return "", ""
            names = [r.name for r in member.roles if r.name != "@everyone"]
            return ";".join(names), (member.top_role.name if names else "")

        def excel_safe_formula(value: str) -> str:
            v = (value or "").strip()
            return f'="{v}"' if v else ""

        cached_members: dict[str, discord.Member] = (
            {str(m.id): m for m in guild.members} if guild.members else {}
        )
        fetch_cache: dict[str, discord.Member | None] = {}

        async def get_member(uid_str: str):
            m = cached_members.get(uid_str)
            if m is not None:
                return m
            if uid_str in fetch_cache:
                return fetch_cache[uid_str]
            try:
                m = await guild.fetch_member(int(uid_str))
            except Exception:
                m = None
            fetch_cache[uid_str] = m
            return m

        # ---------- Build REGISTERED rows + set of normalized registered GovernorIDs ----------
        registered_ids: set[str] = set()
        registered_rows: list[dict] = []
        registered_rows_with_id = 0  # diagnostics

        for uid, data in registry.items():
            uid_str = str(uid).strip()
            accounts = data.get("accounts", {})
            if not isinstance(accounts, dict):
                continue
            for acc_type, details in accounts.items():
                gov_id_raw = _extract_gov_id(details)
                gov_id_norm = _norm_gid(gov_id_raw)
                gov_name = str(details.get("GovernorName") or "Unknown").strip()

                if gov_id_norm:
                    registered_ids.add(gov_id_norm)
                    registered_rows_with_id += 1

                registered_rows.append(
                    {
                        "discord_id": uid_str,
                        "discord_id_excel": excel_safe_formula(uid_str),
                        "discord_user": str(data.get("discord_name", uid_str)).strip(),
                        "account_type": str(acc_type).strip(),
                        "governor_id": str(gov_id_raw or "").strip(),  # raw for humans
                        "governor_id_excel": excel_safe_formula(str(gov_id_raw or "")),
                        "governor_name": gov_name,
                        "_member": None,
                        "roles": "",
                        "top_role": "",
                    }
                )

        # Resolve member objects for registered rows (roles/top_role)
        for row in registered_rows:
            uid = row["discord_id"]
            member = cached_members.get(uid) or await get_member(uid)
            row["_member"] = member
        for row in registered_rows:
            roles_str, top = role_names(row["_member"])
            row["roles"], row["top_role"] = roles_str, top
            row.pop("_member", None)

        # ---------- CURRENT governors from SQL → normalized sets & lookup ----------
        # SQL now returns BIGINT for GovernorID, so just stringify it.
        current_ids: set[str] = set()
        row_by_id: dict[str, dict] = {}

        for r in sql_rows:
            gid_val = r.get("GovernorID")
            if gid_val is None:
                continue
            gid_sql = str(int(gid_val))  # bigint -> "123456"
            current_ids.add(gid_sql)
            if gid_sql not in row_by_id:
                row_by_id[gid_sql] = r

        unregistered_ids = sorted(current_ids - registered_ids)

        logger.info(
            "[registration_audit] SQL current=%d, registry=%d (with_gov_id=%d), unmatched=%d",
            len(current_ids),
            len(registry),
            len(registered_ids),
            len(unregistered_ids),
        )
        if registered_ids and len(unregistered_ids) == len(current_ids):
            sample_sql = list(sorted(current_ids))[:5]
            sample_reg = list(sorted(registered_ids))[:5]
            logger.exception(
                "[registration_audit] All current appear unregistered. Sample SQL: %s | Sample REG: %s",
                sample_sql,
                sample_reg,
            )

        # ---------- Guild members without any registration ----------
        try:
            members = [m for m in guild.members if not m.bot]
        except Exception:
            members = []
        registered_user_ids = set(str(k).strip() for k in registry.keys())
        members_without_reg = [m for m in members if str(m.id) not in registered_user_ids]

        # ---------- Build members_info mapping and files via registry_io (CSV + XLSX) ----------
        members_info: dict[str, dict] = {}
        all_members_source = {str(m.id): m for m in guild.members} if guild.members else {}
        for uid in set(list(all_members_source.keys()) + [str(m.id) for m in members_without_reg]):
            mem = all_members_source.get(uid)
            if mem:
                roles_str, top_role = role_names(mem)
                members_info[uid] = {
                    "discord_user": str(mem),
                    "roles": roles_str,
                    "top_role": top_role,
                }
            else:
                members_info[uid] = {"discord_user": uid, "roles": "", "top_role": ""}

        files = registry_io.export_registration_audit_files(registry, members_info, sql_rows)
        # Also produce an XLSX workbook with three sheets
        try:
            xlsx_bytes = registry_io.export_registration_audit_xlsx_bytes(
                registry, members_info, sql_rows
            )
        except Exception:
            logger.exception("Failed to produce XLSX audit workbook")
            xlsx_bytes = None

        # ---------- Compute counts for the audit embed ----------
        # Total registered account rows (accounts per user)
        registered_accounts_total = 0
        registered_ids_set: set[str] = set()
        for uid, data in (registry or {}).items():
            accs = data.get("accounts") or {}
            if isinstance(accs, dict):
                registered_accounts_total += len(accs)
                for det in accs.values():
                    # attempt to find GovernorID from common keys
                    gid = ""
                    if isinstance(det, dict):
                        for k in (
                            "GovernorID",
                            "Governor Id",
                            "GovernorId",
                            "gov_id",
                            "govid",
                            "GovID",
                            "Gov Id",
                        ):
                            v = det.get(k)
                            if v:
                                gid = str(v).strip()
                                break
                        if not gid:
                            # fallback: check any value keys containing governor+id
                            for k2, v2 in det.items():
                                nk = re.sub(r"[^a-z0-9]", "", str(k2).lower())
                                if (
                                    ("governor" in nk and "id" in nk)
                                    or nk in ("govid", "governorid")
                                ) and v2:
                                    gid = str(v2).strip()
                                    break
                    if gid:
                        # normalize numeric-like from audit normalizer (strip wrappers/commas)
                        try:
                            gid_norm = registry_io._norm_gid(gid)
                        except Exception:
                            gid_norm = gid
                        if gid_norm:
                            registered_ids_set.add(gid_norm)

        # compute current IDs from SQL rows (as per prior logic)
        current_ids: set[str] = set()
        for r in sql_rows:
            gid_val = r.get("GovernorID")
            if gid_val is None:
                continue
            try:
                gid_sql = str(int(gid_val))
            except Exception:
                gid_sql = str(gid_val)
            current_ids.add(gid_sql)

        unregistered_ids = sorted(current_ids - registered_ids_set)
        unregistered_count = len(unregistered_ids)
        members_without_registration_count = len(members_without_reg)

        # ---------- Summary embed ----------
        embed = discord.Embed(
            title="🧾 Registration Audit (Current Governors)", color=discord.Color.blurple()
        )
        embed.add_field(
            name="Registered accounts", value=f"{registered_accounts_total:,}", inline=True
        )
        embed.add_field(
            name="Unregistered current governors (SQL)",
            value=f"{unregistered_count:,}",
            inline=True,
        )
        embed.add_field(
            name="Discord members without registration",
            value=f"{members_without_registration_count:,}",
            inline=True,
        )
        embed.set_footer(
            text="CSV exports attached (Excel-safe IDs; roles included where applicable)."
        )

        # ---------- Respond ----------
        await ctx.interaction.edit_original_response(embed=embed, content=None)
        send_files = []
        try:
            send_files = [
                discord.File(files["registered_accounts.csv"], filename="registered_accounts.csv"),
                discord.File(
                    files["unregistered_current_governors.csv"],
                    filename="unregistered_current_governors.csv",
                ),
                discord.File(
                    files["members_without_registration.csv"],
                    filename="members_without_registration.csv",
                ),
            ]
            if xlsx_bytes:
                send_files.append(discord.File(xlsx_bytes, filename="registration_audit.xlsx"))

            await ctx.followup.send(files=send_files, ephemeral=True)
        except Exception:
            # fallback to non-ephemeral delivery
            try:
                await ctx.followup.send(
                    content="⚠️ Ephemeral file delivery failed, sending files non-ephemerally instead.",
                    files=send_files,
                    ephemeral=False,
                )
            except Exception:
                logger.exception("Failed to send registration_audit files.")

    # ---------- EXPORT (now includes roles and excel safe RAW fields) ----------
    @bot.slash_command(
        name="bulk_export_registrations",
        description="Admin: export current registrations as CSV (with roles).",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.03")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def bulk_export_registrations(ctx: discord.ApplicationContext):
        """
        Exports current registrations to CSV with:
          - UTF-8 BOM for safe Windows Excel Unicode handling
          - Dual ID columns: raw + Excel-safe formula form (e.g., =\"123...\")
          - Stable sorting for easier audits (discord_user, then account_type)
        """
        import csv as _csv

        await safe_defer(ctx, ephemeral=True)

        guild: discord.Guild | None = ctx.guild
        if guild is None:
            await ctx.interaction.edit_original_response(
                content="❌ This command must be used in a server (guild) channel."
            )
            return

        registry = load_registry()

        # Helper: stringify a member's roles (exclude @everyone)
        def role_names(member: discord.Member | None) -> tuple[str, str]:
            if member is None:
                return "", ""
            names = [r.name for r in member.roles if r.name != "@everyone"]
            roles_str = ";".join(names)
            top = member.top_role.name if names else ""
            return roles_str, top

        # Helper: Excel-safe formula wrapper to prevent numeric coercion on open
        def excel_safe_formula(value: str) -> str:
            v = (value or "").strip()
            return f'="{v}"' if v else ""

        # Build a quick lookup from cached members (best case when Members Intent is enabled)
        # Use len(guild.members) to avoid relying on private attributes.
        cached_members: dict[str, discord.Member] = (
            {str(m.id): m for m in guild.members} if guild.members else {}
        )

        rows = []
        missing_ids: set[str] = set()  # users not in cache; we'll try fetching lazily

        for uid, data in registry.items():
            member = cached_members.get(uid)
            if member is None:
                missing_ids.add(uid)

            accounts = data.get("accounts", {})
            if not isinstance(accounts, dict):
                continue

            for acc_type, details in accounts.items():
                gov_id_raw = str(details.get("GovernorID", "")).strip()
                rows.append(
                    {
                        "discord_id": str(uid).strip(),
                        "discord_id_excel": excel_safe_formula(str(uid).strip()),
                        "discord_user": data.get("discord_name", str(uid).strip()),
                        "account_type": str(acc_type).strip(),
                        "governor_id": gov_id_raw,
                        "governor_id_excel": excel_safe_formula(gov_id_raw),
                        "governor_name": details.get("GovernorName", ""),
                        "_roles_member": member,  # temp; fill roles/top_role later
                        "roles": "",
                        "top_role": "",
                    }
                )

        # Try to fetch any members that weren't cached (if Members Intent isn’t populating guild.members)
        if missing_ids:
            fetched: dict[str, discord.Member | None] = {}
            for uid in list(missing_ids):
                try:
                    m = await guild.fetch_member(int(uid))
                    fetched[uid] = m
                except Exception:
                    fetched[uid] = None  # keep None if not found (left the server, etc.)

            # fill roles/top_role for missing via fetched
            for r in rows:
                if r["_roles_member"] is None:
                    mem = fetched.get(r["discord_id"])
                    r["_roles_member"] = mem

        # Now populate roles/top_role and strip temp field
        for r in rows:
            roles_str, top = role_names(r["_roles_member"])
            r["roles"] = roles_str
            r["top_role"] = top
            r.pop("_roles_member", None)

        if not rows:
            await ctx.interaction.edit_original_response(
                content="📭 No registrations found to export."
            )
            return

        # Stable sort: discord_user (casefolded) then account_type
        rows.sort(
            key=lambda r: (
                str(r.get("discord_user", "")).casefold(),
                str(r.get("account_type", "")).casefold(),
            )
        )

        # Write CSV with UTF-8 BOM (utf-8-sig) so Excel handles Unicode cleanly
        buf = io.StringIO()
        headers = [
            "discord_id",  # raw (machine-readable)
            "discord_id_excel",  # Excel-safe display (=\"...\")
            "discord_user",
            "account_type",
            "governor_id",  # raw (machine-readable)
            "governor_id_excel",  # Excel-safe display (=\"...\")
            "governor_name",
            "roles",
            "top_role",
        ]
        writer = _csv.DictWriter(buf, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in headers})

        # Encode with BOM for Excel
        csv_bytes = io.BytesIO(buf.getvalue().encode("utf-8-sig"))

        # Also produce XLSX for the same rows (preserve roles, excel-safe columns)
        try:
            xlsx_bytes = registry_io.rows_to_xlsx_bytes(rows, headers, sheet_name="registrations")
        except Exception:
            logger.exception("Failed to produce XLSX export for registrations")
            xlsx_bytes = None

        await ctx.interaction.edit_original_response(
            content="📤 Exported current registrations (CSV and XLSX)."
        )
        send_files = [discord.File(csv_bytes, filename="registrations_export.csv")]
        if xlsx_bytes:
            send_files.append(discord.File(xlsx_bytes, filename="registrations_export.xlsx"))
        try:
            await ctx.followup.send(files=send_files, ephemeral=True)
        except Exception:
            await ctx.followup.send(
                content="⚠️ Ephemeral file delivery failed, sending files non-ephemerally instead.",
                files=send_files,
                ephemeral=False,
            )

    # ===== BULK IMPORT (FOLLOW-UP ATTACHMENT FLOW) =====

    # ---------- helper: wait for user's next message with a CSV attachment ----------
    async def _await_csv_attachment(
        ctx: discord.ApplicationContext,
        prompt_text: str,
        *,
        timeout: int = 180,
        max_size_bytes: int = 5_000_000,
    ) -> tuple[discord.Attachment | None, str]:
        """
        Prompt the invoker to upload a CSV or XLSX as their next message in this channel.
        Returns (attachment_or_None, detected_type) where detected_type in {"csv","xlsx","unknown"}.
        """
        await ctx.interaction.edit_original_response(content=prompt_text)

        def check(msg: discord.Message) -> bool:
            if msg.author.id != ctx.user.id:
                return False
            if msg.channel.id != ctx.channel_id:
                return False
            return any(
                att.filename.lower().endswith((".csv", ".xlsx", ".xls")) for att in msg.attachments
            )

        try:
            msg: discord.Message = await ctx.bot.wait_for("message", check=check, timeout=timeout)
        except TimeoutError:
            await ctx.interaction.edit_original_response(
                content=f"⏳ Timed out after {timeout}s waiting for your file. Please run the command again."
            )
            return None, "none"

        attach = next(
            (a for a in msg.attachments if a.filename.lower().endswith((".csv", ".xlsx", ".xls"))),
            None,
        )
        if not attach:
            await ctx.interaction.edit_original_response(
                content="❌ I saw your message but it had no `.csv` or `.xlsx` attachment. Please run the command again."
            )
            return None, "none"

        if attach.size > max_size_bytes:
            await ctx.interaction.edit_original_response(
                content=f"❌ File too large ({attach.size:,} bytes). Max allowed is {max_size_bytes:,} bytes."
            )
            return None, "none"

        fname = (attach.filename or "").lower()
        if fname.endswith(".csv"):
            return attach, "csv"
        if fname.endswith(".xlsx") or fname.endswith(".xls"):
            return attach, "xlsx"
        return attach, "unknown"

    # ---------- normalization helpers ----------

    _BOM = "\ufeff"
    _SCI_RE = re.compile(r"^\s*[+-]?\d+(?:\.\d+)?[eE][+-]?\d+\s*$")
    _DOT_ZERO_RE = re.compile(r"\.0+$")
    _DIGITS_RE = re.compile(r"^\d+$")
    _ALT_RE = re.compile(r"^alt[\s\-_]*0*([1-9]\d*)$", re.IGNORECASE)
    _FARM_RE = re.compile(r"^farm[\s\-_]*0*([1-9]\d*)$", re.IGNORECASE)

    def _strip_excel_formula(val: str) -> tuple[str, bool]:
        """If the value is in the form =\"123...\", extract inner content. Returns (value, did_change)."""
        v = (val or "").strip()
        if len(v) >= 4 and v.startswith('="') and v.endswith('"'):
            return v[2:-1], True
        return v, False

    def normalize_id(
        raw_val: str | None, excel_val: str | None, *, field: str
    ) -> tuple[str | None, list[str]]:
        """
        Normalize an ID coming from CSV.
        **Preference order:** excel_val first, then raw_val (to avoid Excel-coerced numbers).
        Returns (normalized_string_or_None, notes), where notes include 'formula', 'sci', 'dotzero', 'commas', 'spaces', 'prefer_excel'.
        """
        notes: list[str] = []

        def _pipeline(value: str | None) -> tuple[str | None, list[str]]:
            local_notes: list[str] = []
            if value is None:
                return None, local_notes
            v = value.lstrip(_BOM).strip()
            if not v:
                return None, local_notes

            # Extract from ="123..."
            v2, changed = _strip_excel_formula(v)
            if changed:
                v = v2
                local_notes.append("formula")

            # Strip wrapping quotes if any
            if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
                v = v[1:-1]

            # Remove commas/spaces
            if "," in v:
                v = v.replace(",", "")
                local_notes.append("commas")
            if " " in v:
                v = v.replace(" ", "")
                local_notes.append("spaces")

            # Scientific notation -> exact integer string
            if _SCI_RE.match(v):
                try:
                    v = f"{int(Decimal(v))}"
                    local_notes.append("sci")
                except (InvalidOperation, ValueError):
                    return None, local_notes

            # Strip trailing .0
            if _DOT_ZERO_RE.search(v):
                v = _DOT_ZERO_RE.sub("", v)
                local_notes.append("dotzero")

            # Final validation
            if not _DIGITS_RE.fullmatch(v):
                return None, local_notes
            if len(v) < 6:
                return None, local_notes

            return v, local_notes

        # Prefer the Excel-safe column first
        for idx, candidate in enumerate((excel_val, raw_val)):
            normalized, local = _pipeline(candidate)
            notes.extend(local)
            if normalized:
                if idx == 0:  # picked excel_val
                    notes.append("prefer_excel")
                return normalized, notes

        return None, notes

    def normalize_account_type(s: str) -> tuple[str | None, bool, str | None]:
        """
        Canonicalize account types to: 'Main', 'Alt N', 'Farm N'.
        Returns (normalized_value_or_None, did_canonicalize, error_message_if_any)
        """
        raw = (s or "").strip()
        if not raw:
            return None, False, "account_type is empty"

        low = raw.lower().strip()

        if low == "main":
            return "Main", (raw != "Main"), None

        m = _ALT_RE.match(low)
        if m:
            n = int(m.group(1))
            return f"Alt {n}", True, None

        m = _FARM_RE.match(low)
        if m:
            n = int(m.group(1))
            return f"Farm {n}", True, None

        # Also accept patterns like 'Alt 01', 'Farm-03'
        low_spaces = re.sub(r"[\-_]+", " ", low)
        parts = low_spaces.split()
        if len(parts) == 2 and parts[0] in ("alt", "farm") and parts[1].isdigit():
            n = int(parts[1])
            if parts[0] == "alt":
                return f"Alt {n}", True, None
            else:
                return f"Farm {n}", True, None

        return None, False, f"Unrecognized account_type '{s}'. Use Main, Alt N, or Farm N."

    # ---------- shared importer with rich summary ----------
    async def _import_regs_impl(ctx: discord.ApplicationContext, *, dry_run: bool) -> None:
        """
        Accept a CSV or XLSX upload, delegate parse/validation to registry_io, and optionally commit.
        """
        ask = (
            "📎 Please upload the **CSV or XLSX file** now (as a new message in this channel).\n"
            "Required logical columns: `discord_id OR discord_id_excel`, `account_type`, `governor_id OR governor_id_excel`.\n"
            "_Tip: You can export from `/bulk_export_registrations` or `/registration_audit` and edit that file._"
        )
        attach, ftype = await _await_csv_attachment(ctx, ask)
        if not attach:
            return

        try:
            raw = await attach.read()
        except Exception as e:
            logger.exception("Failed reading attachment bytes: %s", e)
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to read uploaded file: {type(e).__name__}: {e}"
            )
            return

        rows = []
        if ftype == "csv":
            rows = parse_csv_bytes(raw)
        elif ftype == "xlsx":
            try:
                rows = parse_xlsx_bytes(raw)
            except Exception as e:
                # If XLSX parse failed, attempt to parse as CSV as fallback
                logger.exception("XLSX parse error; attempting CSV fallback: %s", e)
                rows = parse_csv_bytes(raw)
        else:
            # try CSV then XLSX fallback
            rows = parse_csv_bytes(raw)
            if not rows:
                try:
                    rows = parse_xlsx_bytes(raw)
                except Exception:
                    rows = []

        if not rows:
            await ctx.interaction.edit_original_response(
                content="❌ Uploaded file could not be parsed as CSV or XLSX or appears to have no data."
            )
            return

        registry = load_registry()
        all_rows = _name_cache.get("rows", [])  # source-of-truth governor list as before
        valid_ids = {str(x.get("GovernorID")).strip(): x for x in all_rows if x.get("GovernorID")}

        changes, errors, warnings, error_rows = prepare_import_plan(
            rows, registry, valid_ids=valid_ids
        )

        if errors:
            err_file_bytes = build_error_csv_bytes(error_rows)
            file_obj = discord.File(err_file_bytes, filename="import_errors.csv")
            embed = discord.Embed(
                title="❌ Import validation failed",
                description=f"Errors: {len(errors)}. Warnings: {len(warnings)}.\n\nFirst issues:\n"
                + "\n".join(errors[:20])
                + (f"\n… and {len(errors)-20} more" if len(errors) > 20 else ""),
                color=0xE74C3C,
            )
            await ctx.interaction.edit_original_response(embed=embed, content=None)
            try:
                await ctx.followup.send(file=file_obj, ephemeral=True)
            except Exception:
                await ctx.followup.send(
                    content="⚠️ Ephemeral file delivery failed, sending error file non-ephemerally instead.",
                    file=file_obj,
                    ephemeral=False,
                )
            return

        if dry_run:
            planned = [
                f"Row {c['source_row']}: {c['discord_id']} {c['account_type']} -> {c['governor_id']} ({c.get('governor_name','')})"
                for c in changes[:20]
            ]
            more = f"\n… and {len(changes)-20} more" if len(changes) > 20 else ""
            embed = discord.Embed(
                title="✅ Dry Run OK",
                description=f"{len(changes)} changes proposed.\n\nPlanned changes:\n"
                + "\n".join(planned)
                + more
                + (("\n\nWarnings:\n" + "\n".join(warnings)) if warnings else ""),
                color=0x2ECC71,
            )
            await ctx.interaction.edit_original_response(embed=embed, content=None)
            return

        # commit
        try:
            new_registry, summary = apply_import_plan(changes, registry, dry_run=False)
        except Exception as e:
            logger.exception("Failed to apply import plan: %s", e)
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to apply import: {type(e).__name__}: {e}"
            )
            return

        embed = discord.Embed(
            title="✅ Import Complete",
            description=f"{len(summary)} changes applied.\n\n"
            + "\n".join(summary[:50])
            + (("\n\nWarnings:\n" + "\n".join(warnings)) if warnings else ""),
            color=0x2ECC71,
        )
        await ctx.interaction.edit_original_response(embed=embed, content=None)

    # ---------- IMPORT (DRY RUN) ----------
    @bot.slash_command(
        name="bulk_import_registrations_dryrun",
        description="Admin: validate a registrations CSV without saving.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.11")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def bulk_import_registrations_dryrun(ctx: discord.ApplicationContext):
        """
        Dry-run: prompt user for CSV, validate using registry_io, and summarize proposed changes and warnings.
        Keeps the UI/Discord flow within Commands.py; heavy validation is delegated to registry_io.
        """
        # Acknowledge quickly (UI)
        deferred = await safe_defer(ctx, ephemeral=True)

        attach, ftype = await _await_csv_attachment(
            ctx,
            "📎 Please upload the **CSV or XLSX file** now (as a new message in this channel).\n"
            "Required logical columns: `discord_id OR discord_id_excel`, `account_type`, `governor_id OR governor_id_excel`.\n"
            "_Tip: You can export from `/bulk_export_registrations` or `/registration_audit` and edit that file._",
        )
        if not attach:
            return

        try:
            raw = await attach.read()
        except Exception as e:
            logger.exception("Failed reading attachment bytes: %s", e)
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to read uploaded file: {type(e).__name__}: {e}"
            )
            return

        # Parse according to detected type (csv/xlsx) with sensible fallback
        rows = []
        if ftype == "csv":
            rows = parse_csv_bytes(raw)
        elif ftype == "xlsx":
            try:
                rows = parse_xlsx_bytes(raw)
            except Exception as e:
                logger.exception("Failed parsing uploaded XLSX, attempting CSV fallback: %s", e)
                rows = parse_csv_bytes(raw)
        else:
            # unknown: try CSV first, then XLSX
            rows = parse_csv_bytes(raw)
            if not rows:
                try:
                    rows = parse_xlsx_bytes(raw)
                except Exception:
                    rows = []

        if not rows:
            await ctx.interaction.edit_original_response(
                content="❌ Uploaded file could not be parsed as CSV or XLSX or appears to have no data."
            )
            return

        existing = governor_registry.load_registry()
        changes, errors, warnings, error_rows = prepare_import_plan(rows, existing)

        # deliver via followup if we deferred earlier
        send = ctx.followup.send if deferred else ctx.respond

        if errors:
            # build an error CSV and XLSX workbook for user to download and inspect
            err_csv_bytes = registry_io.build_error_csv_bytes(error_rows)
            err_xlsx_bytes = None
            try:
                err_xlsx_bytes = registry_io.build_error_xlsx_bytes(error_rows)
            except Exception:
                logger.exception("Failed to build XLSX error workbook; falling back to CSV only.")

            files = [discord.File(err_csv_bytes, filename="import_errors.csv")]
            if err_xlsx_bytes:
                files.append(discord.File(err_xlsx_bytes, filename="import_errors.xlsx"))

            short_msg = f"❌ Import validation failed: {len(errors)} error(s). See attached import_errors.csv (and XLSX) for details."
            # If there are a small number of errors, include them inline
            if len(errors) <= 10:
                details = "\n".join(errors[:50])
                content = short_msg + "\n\nFirst issues:\n" + details
                if len(content) <= 1900:
                    await send(content=content, files=files, ephemeral=True)
                    return

            await send(content=short_msg, files=files, ephemeral=True)
            return

        # No fatal errors: show interactive confirm UI (Confirm / Cancel)
        # Build an embed summary
        preview = []
        for c in changes[:20]:
            preview.append(
                f"Row {c.get('source_row')}: {c['discord_id']} {c['account_type']} -> {c['governor_id']}"
            )

        embed = discord.Embed(title="✅ Import Dry-Run OK", color=discord.Color.green())
        embed.description = f"{len(changes)} changes proposed.\n\n" + (
            "\n".join(preview) + (f"\n… and {len(changes)-20} more" if len(changes) > 20 else "")
        )
        if warnings:
            embed.add_field(
                name="Warnings",
                value="\n".join(warnings[:10])
                + (f"\n… and {len(warnings)-10} more" if len(warnings) > 10 else ""),
                inline=False,
            )

        # Interactive view for confirmation
        async def _apply_import(interaction: discord.Interaction):
            try:
                _new_registry, summary = apply_import_plan(changes, existing, dry_run=False)
            except Exception as e:
                logger.exception("Failed to apply import plan: %s", e)
                try:
                    await interaction.followup.send(
                        f"❌ Failed to apply import: {type(e).__name__}: {e}",
                        ephemeral=True,
                    )
                except Exception:
                    pass
                return

            preview_text = "\n".join(summary[:50])
            message_text = (
                f"✅ Import applied successfully. {len(summary)} changes made.\n" + preview_text
            )
            if len(message_text) <= 1900:
                await interaction.followup.send(message_text, ephemeral=True)
            else:
                full = "Import full summary:\n\n" + "\n".join(summary)
                bio = io.BytesIO(full.encode("utf-8"))
                await interaction.followup.send(
                    "✅ Import applied successfully. Full summary attached.",
                    file=discord.File(bio, filename="import_summary.txt"),
                    ephemeral=True,
                )

        view = ConfirmImportView(
            author_id=ctx.user.id,
            ephemeral=True,
            on_confirm_apply=_apply_import,
        )

        try:
            await send(embed=embed, view=view, ephemeral=True)
        except Exception:
            # Fall back to sending the embed without view if that fails
            await send(embed=embed, ephemeral=True)
        return

    # ---------- IMPORT (COMMIT) ----------
    @bot.slash_command(
        name="bulk_import_registrations",
        description="Admin: import registrations from CSV (commits changes).",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.11")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def bulk_import_registrations(ctx: discord.ApplicationContext):
        """
        Full import: prompt user for CSV, validate via registry_io, then apply changes atomically.
        """
        deferred = await safe_defer(ctx, ephemeral=True)

        attach, ftype = await _await_csv_attachment(
            ctx,
            "📎 Please upload the **CSV or XLSX file** now (as a new message in this channel).\n"
            "Required logical columns: `discord_id OR discord_id_excel`, `account_type`, `governor_id OR governor_id_excel`.\n"
            "_Tip: You can export from `/bulk_export_registrations` or `/registration_audit` and edit that file._",
        )
        if not attach:
            return

        try:
            raw = await attach.read()
        except Exception as e:
            logger.exception("Failed reading attachment bytes: %s", e)
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to read uploaded file: {type(e).__name__}: {e}"
            )
            return

        # Parse according to detected type (csv/xlsx) with sensible fallback
        rows = []
        if ftype == "csv":
            rows = parse_csv_bytes(raw)
        elif ftype == "xlsx":
            try:
                rows = parse_xlsx_bytes(raw)
            except Exception as e:
                logger.exception("Failed parsing uploaded XLSX, attempting CSV fallback: %s", e)
                rows = parse_csv_bytes(raw)
        else:
            # unknown: try CSV first, then XLSX
            rows = parse_csv_bytes(raw)
            if not rows:
                try:
                    rows = parse_xlsx_bytes(raw)
                except Exception:
                    rows = []

        if not rows:
            await ctx.interaction.edit_original_response(
                content="❌ Uploaded file could not be parsed as CSV or XLSX or appears to have no data."
            )
            return

        existing = governor_registry.load_registry()
        changes, errors, warnings, error_rows = prepare_import_plan(rows, existing)

        send = ctx.followup.send if deferred else ctx.respond

        if errors:
            # Build CSV error file
            err_csv_bytes = registry_io.build_error_csv_bytes(error_rows)
            files = [discord.File(err_csv_bytes, filename="import_errors.csv")]

            # Try to build XLSX error workbook too (best-effort)
            try:
                err_xlsx_bytes = registry_io.build_error_xlsx_bytes(error_rows)
                files.append(discord.File(err_xlsx_bytes, filename="import_errors.xlsx"))
            except Exception:
                logger.exception("Failed to build XLSX error workbook; sending CSV only.")

            short_msg = f"❌ Import validation failed: {len(errors)} error(s). See attached import_errors.csv for details."

            # If there are a small number of errors, attempt to include a short inline preview (subject to length)
            if len(errors) <= 10:
                details = "\n".join(errors[:50])
                content = short_msg + "\n\nFirst issues:\n" + details
                if len(content) <= 1900:
                    await send(content=content, files=files, ephemeral=True)
                    return

            # Otherwise send short message with attachments
            await send(content=short_msg, files=files, ephemeral=True)
            return

        # Apply changes (atomic save via registry_io.apply_import_plan)
        try:
            new_registry, summary = apply_import_plan(changes, existing, dry_run=False)
        except Exception as e:
            logger.exception("Failed to apply import plan: %s", e)
            await send(f"❌ Failed to apply import: {type(e).__name__}: {e}", ephemeral=True)
            return

        preview = "\n".join(summary[:50])
        text_preview = f"✅ Import applied successfully. {len(summary)} changes made.\n" + preview
        if warnings:
            text_preview += "\n\nWarnings:\n" + "\n".join(f"- {w}" for w in warnings[:20])

        if len(text_preview) <= 1900:
            await send(text_preview, ephemeral=True)
        else:
            full = "Import full summary:\n\n" + "\n".join(summary)
            if warnings:
                full += "\n\nWarnings:\n" + "\n".join(warnings)
            bio = io.BytesIO(full.encode("utf-8"))
            file_obj = discord.File(bio, filename="import_summary.txt")
            await send(
                content=f"✅ Import applied successfully. {len(summary)} changes made. Full summary attached.",
                file=file_obj,
                ephemeral=True,
            )

    @bot.slash_command(
        name="usage",
        description="View bot usage summary (admin/leadership)",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_or_leadership()
    @track_usage()
    async def usage_command(
        ctx: discord.ApplicationContext,
        period: str = discord.Option(str, "Time window", choices=["day", "week"], default="day"),
        by: str = discord.Option(
            str, "Group by", choices=["command", "user", "reliability"], default="command"
        ),
        context_filter: str = discord.Option(
            str,
            "Filter by context",
            choices=["slash", "component", "autocomplete", "all"],
            default="slash",
        ),
        limit: int = discord.Option(int, "Max rows", default=10),
    ):
        await safe_defer(ctx, ephemeral=True)
        limit = max(1, min(int(limit or 10), 50))
        since = utcnow() - (timedelta(days=7) if period == "week" else timedelta(days=1))

        # context WHERE clause
        ctx_sql, ctx_params = _ctx_filter_sql(context_filter)

        try:
            if by == "user":
                sql = f"""
                    SELECT TOP {limit} UserId,
                           MAX(UserDisplay) AS UserDisplay,
                           COUNT(*) AS Uses,
                           COUNT(DISTINCT CommandName) AS UniqueCommands
                    FROM {USAGE_TABLE}
                    WHERE ExecutedAtUtc >= ?{ctx_sql}
                    GROUP BY UserId
                    ORDER BY Uses DESC, UserId ASC;
                """
                rows = await _fetch_rows(sql, (since, *ctx_params))
                lines = [
                    f"<@{r['UserId']}> · uses **{r['Uses']}** · cmds **{r['UniqueCommands']}**"
                    for r in rows
                ]
                title = f"Usage by user (last {period})"

            elif by == "reliability":
                sql = f"""
                    SELECT CommandName,
                           COUNT(*) AS Total,
                           SUM(CASE WHEN Success=1 THEN 1 ELSE 0 END) AS Successes
                    FROM {USAGE_TABLE}
                    WHERE ExecutedAtUtc >= ?{ctx_sql}
                    GROUP BY CommandName
                """
                rows = await _fetch_rows(sql, (since, *ctx_params))
                # compute success % in python and sort by worst
                stats = []
                for r in rows:
                    total = int(r["Total"] or 0)
                    ok = int(r["Successes"] or 0)
                    rate = (ok / total * 100.0) if total else 0.0
                    stats.append((r["CommandName"], total, ok, rate))
                stats.sort(key=lambda t: (100.0 - t[3], -t[1]))
                stats = stats[:limit]
                lines = [
                    f"`/{n}` · **{rate:.1f}%** success ({ok}/{tot})" for n, tot, ok, rate in stats
                ]
                title = f"Reliability by command (last {period})"

            else:
                # by == command
                sql = f"""
                    SELECT CommandName,
                           COUNT(*) AS Uses,
                           SUM(CASE WHEN Success=1 THEN 1 ELSE 0 END) AS Successes,
                           AVG(CAST(LatencyMs AS float)) AS AvgLatencyMs
                    FROM {USAGE_TABLE}
                    WHERE ExecutedAtUtc >= ?{ctx_sql}
                    GROUP BY CommandName
                    ORDER BY Uses DESC, CommandName ASC;
                """
                rows = await _fetch_rows(sql, (since, *ctx_params))
                rows = rows[:limit]
                lines = [
                    f"`/{r['CommandName']}` · uses **{r['Uses']}** · ok **{r['Successes']}** · avg {int(r['AvgLatencyMs'] or 0)}ms"
                    for r in rows
                ]
                title = f"Usage by command (last {period})"

            embed = discord.Embed(
                title=title,
                description=("\n".join(lines) or "_No data_"),
                colour=discord.Colour.blurple(),
            )
            await ctx.interaction.edit_original_response(embed=embed)
        except Exception as e:
            logger.exception("[/usage] failed")
            await ctx.interaction.edit_original_response(
                content=f"Sorry, I couldn't load usage stats: `{type(e).__name__}: {e}`"
            )

    @bot.slash_command(
        name="usage_detail",
        description="Drill down into a specific command or user (admin/leadership)",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_or_leadership()
    @track_usage()
    async def usage_detail_command(
        ctx: discord.ApplicationContext,
        # ✅ REQUIRED FIRST
        dimension: str = discord.Option(str, "Filter by", choices=["command", "user"]),
        value: str = discord.Option(
            str, "Command name or user mention/ID", autocomplete=_usage_detail_value_ac
        ),
        # ✅ OPTIONALS AFTER
        period: str = discord.Option(str, "Time window", choices=["day", "week"], default="day"),
        context_filter: str = discord.Option(
            str,
            "Filter by context",
            choices=["slash", "component", "autocomplete", "all"],
            default="slash",
        ),
    ):
        await safe_defer(ctx, ephemeral=True)
        since = utcnow() - (timedelta(days=7) if period == "week" else timedelta(days=1))
        ctx_sql, ctx_params = _ctx_filter_sql(context_filter)

        try:
            if dimension == "command":
                cmd = value.lstrip("/").strip()
                sql_pct = f"""
                    WITH s AS (
                      SELECT LatencyMs, Success
                      FROM {USAGE_TABLE}
                      WHERE ExecutedAtUtc >= ? AND CommandName = ?{ctx_sql}
                    )
                    SELECT
                      (SELECT COUNT(*) FROM s) AS Total,
                      (SELECT SUM(CASE WHEN Success=1 THEN 1 ELSE 0 END) FROM s) AS Successes,
                      (SELECT SUM(CASE WHEN Success=0 THEN 1 ELSE 0 END) FROM s) AS Failures,
                      (SELECT TOP 1 CAST(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY CAST(LatencyMs AS float)) OVER () AS int)
                         FROM s WHERE LatencyMs IS NOT NULL) AS P50,
                      (SELECT TOP 1 CAST(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY CAST(LatencyMs AS float)) OVER () AS int)
                         FROM s WHERE LatencyMs IS NOT NULL) AS P95;
                """
                rows = await _fetch_rows(sql_pct, (since, cmd, *ctx_params))
                row = rows[0] if rows else {}
                total = int(row.get("Total") or 0)
                successes = int(row.get("Successes") or 0)
                failures = int(row.get("Failures") or 0)
                p50 = row.get("P50")
                p95 = row.get("P95")

                sql_errs = f"""
                    SELECT TOP 10 ErrorCode, COUNT(*) AS Cnt
                    FROM {USAGE_TABLE}
                    WHERE ExecutedAtUtc >= ? AND CommandName = ? AND Success = 0{ctx_sql}
                    GROUP BY ErrorCode
                    ORDER BY Cnt DESC, ErrorCode ASC;
                """
                errs = await _fetch_rows(sql_errs, (since, cmd, *ctx_params))
                err_lines = [f"`{e['ErrorCode']}` · {e['Cnt']}" for e in errs] or ["_No failures_"]

                desc = (
                    f"**/{cmd}** · last **{period}**\n"
                    f"Total **{total}** · Successes **{successes}** · Failures **{failures}**\n"
                    f"P50 **{(str(int(p50))+'ms') if p50 is not None else '–'}** · "
                    f"P95 **{(str(int(p95))+'ms') if p95 is not None else '–'}**\n\n"
                    f"**Top failure reasons:**\n" + "\n".join(err_lines)
                )
                embed = discord.Embed(
                    title="Usage detail — command",
                    description=desc,
                    colour=discord.Colour.blurple(),
                )
                await ctx.interaction.edit_original_response(embed=embed)

            else:
                # dimension == user
                # accept mention or raw ID
                m = re.search(r"\d{15,22}", value or "")
                uid = int(m.group(0)) if m else int(value)

                sql = f"""
                    SELECT CommandName,
                           COUNT(*) AS Uses,
                           SUM(CASE WHEN Success=1 THEN 1 ELSE 0 END) AS Successes,
                           AVG(CAST(LatencyMs AS float)) AS AvgLatencyMs
                    FROM {USAGE_TABLE}
                    WHERE ExecutedAtUtc >= ? AND UserId = ?{ctx_sql}
                    GROUP BY CommandName
                    ORDER BY Uses DESC, CommandName ASC;
                """
                rows = await _fetch_rows(sql, (since, uid, *ctx_params))
                lines = [
                    f"`/{r['CommandName']}` · uses **{r['Uses']}** · ok **{r['Successes']}** · avg {int(r['AvgLatencyMs'] or 0)}ms"
                    for r in rows
                ] or ["_No data_"]
                embed = discord.Embed(
                    title=f"Usage detail — user <@{uid}>",
                    description="\n".join(lines),
                    colour=discord.Colour.blurple(),
                )
                await ctx.interaction.edit_original_response(embed=embed)

        except Exception as e:
            logger.exception("[/usage_detail] failed")
            await ctx.interaction.edit_original_response(
                content=f"Sorry, I couldn't load usage detail: `{type(e).__name__}: {e}`"
            )

    @bot.slash_command(
        name="my_stats",
        description="View your Rise of Kingdoms stats across your registered accounts",
        guild_ids=[GUILD_ID],
    )
    @channel_only(KVK_PLAYER_STATS_CHANNEL_ID, admin_override=True)
    @versioned("v1.14")
    @safe_command
    @track_usage()
    async def my_stats_command(ctx):
        # Defer so the token stays alive (ephemeral)
        await safe_defer(ctx, ephemeral=True)

        # Resolve user/guild safely
        user_obj, guild_obj = _actor_from_ctx(ctx)
        user_id = user_obj.id

        gov_ids = await get_registered_governor_ids_for_discord(user_id)
        if not gov_ids:
            await ctx.followup.send(
                "I don’t see any governor accounts linked to you. Use `/link_account` first.",
                ephemeral=True,
            )
            return

        # Friendly account names for the dropdown
        account_names = await get_registered_governor_names_for_discord(user_id)

        # Build name -> id map from the same registry
        reg = await asyncio.to_thread(load_registry)
        block = reg.get(str(user_id)) or {}
        name_to_id: dict[str, int] = {}
        for slot, acc in (block.get("accounts") or {}).items():
            if not acc:
                continue
            gname = str(acc.get("GovernorName") or "").strip()
            gid = acc.get("GovernorID")
            if gname and gid:
                name_to_id[gname] = int(gid)

        # Initial slice & payload
        slice_key = "wtd"

        # Find the user's Main from the same registry block
        main_name = get_user_main_governor_name(reg, user_id)
        if main_name and main_name in name_to_id:
            default_choice = main_name
        elif account_names:
            default_choice = account_names[0]
        else:
            default_choice = "ALL"

        # Governor IDs to load for the initial render
        if default_choice == "ALL":
            initial_gov_ids = gov_ids
        else:
            gid = name_to_id.get(default_choice)
            initial_gov_ids = [gid] if gid else gov_ids  # fallback if mapping missing

        payload = await get_stats_payload(user_id, initial_gov_ids, slice_key)
        rows = (payload or {}).get("rows") or []
        if not rows:
            await ctx.followup.send(
                "No stats available yet for your linked accounts. Try again after the next scan.",
                ephemeral=True,
            )
            return

        # If registry names are missing, derive from payload (PER rows)
        if not account_names:
            per_names = sorted(
                {
                    str(r.get("GovernorName") or "").strip()
                    for r in rows
                    if r.get("Grouping") == "PER" and r.get("GovernorName")
                }
            )
            account_names = per_names

        # ---- NEW: build view + embeds, send message, and store handles ----
        view = SliceButtons(
            requester_id=user_id,
            initial_slice=slice_key,
            account_options=account_names,
            current_choice=default_choice,
            governor_ids=gov_ids,
            name_to_id=name_to_id,
            # timeout defaults to STATS_VIEW_TIMEOUT
        )

        gid_for_choice = None if default_choice == "ALL" else name_to_id.get(default_choice)

        # Performance monitoring: track initial load time
        import time

        start = time.time()

        embeds, files = await build_embeds(
            slice_key, default_choice, payload, governor_id_for_choice=gid_for_choice
        )

        elapsed = time.time() - start
        try:
            from file_utils import emit_telemetry_event

            emit_telemetry_event(
                {
                    "event": "my_stats_initial_load",
                    "user_id": user_id,
                    "slice": slice_key,
                    "num_governors": len(gov_ids),
                    "num_accounts": len(account_names),
                    "elapsed_seconds": round(elapsed, 3),
                    "num_embeds": len(embeds),
                    "num_charts": len(files),
                }
            )
        except Exception:
            pass

        # Send ephemerally; store message + followup on the view so callbacks/timeout can edit/clean up
        try:
            msg = await ctx.followup.send(embeds=embeds, files=files, view=view, ephemeral=True)
        except Exception:
            # If something goes wrong sending with files, retry without attachments
            msg = await ctx.followup.send(embeds=embeds, view=view, ephemeral=True)

        view.message = msg
        view.followup = ctx.followup
        view.mark_live()

    @bot.slash_command(
        name="my_stats_export",
        description="Export your registered accounts’ stats to Excel, CSV, or Google Sheets format",
        guild_ids=[GUILD_ID],
    )
    @versioned("v3.02")  # bump version
    @safe_command
    @track_usage()
    async def my_stats_export(
        ctx: discord.ApplicationContext,
        format: str = discord.Option(
            str,
            name="format",
            description="Choose export format",
            choices=["Excel", "CSV", "GoogleSheets"],
            default="Excel",
            required=False,
        ),
        days: int = discord.Option(
            int,
            name="days",
            description="Number of days to include (min: 30, max: 360)",
            min_value=30,
            max_value=360,
            default=90,
            required=False,
        ),
    ):
        """
        Export your stats to a downloadable file.

        Supports Excel (.xlsx), CSV, and Google Sheets-compatible formats.
        """
        await safe_defer(ctx, ephemeral=True)

        # Track temp files for cleanup
        temp_dir = None
        file_path = None

        try:
            from datetime import datetime
            import tempfile

            import pandas as pd

            from file_utils import emit_telemetry_event, get_conn_with_retries
            from stats_exporter import build_user_stats_excel
            from stats_exporter_csv import build_user_stats_csv
            from stats_service import get_registered_governor_ids_for_discord

            user_id = ctx.author.id
            username = ctx.author.display_name or ctx.author.name

            # Use existing stats_service function
            governor_ids = await get_registered_governor_ids_for_discord(user_id)

            if not governor_ids:
                await ctx.respond(
                    "❌ You have no registered accounts. Use `/register_governor` first.",
                    ephemeral=True,
                )
                return

            # Fetch daily stats from DB
            def _fetch_daily():
                conn = get_conn_with_retries()
                try:
                    cursor = conn.cursor()
                    placeholders = ",".join("?" * len(governor_ids))
                    query = f"""
                    SELECT GovernorID, GovernorName, Alliance, AsOfDate,
                        Power, PowerDelta, TroopPower, TroopPowerDelta,
                        KillPoints, KillPointsDelta, Deads, DeadsDelta,
                        RSS_Gathered, RSS_GatheredDelta, RSSAssist, RSSAssistDelta,
                        Helps, HelpsDelta, BuildingMinutes, TechDonations,
                        FortsTotal, FortsLaunched, FortsJoined,
                        AOOJoined, AOOJoinedDelta, AOOWon, AOOWonDelta,
                        AOOAvgKill, AOOAvgKillDelta, AOOAvgDead, AOOAvgDeadDelta,
                        AOOAvgHeal, AOOAvgHealDelta,
                        T4_Kills, T4_KillsDelta, T5_Kills, T5_KillsDelta,
                        T4T5_Kills, T4T5_KillsDelta,
                        HealedTroops, HealedTroopsDelta,
                        RangedPoints, RangedPointsDelta,
                        HighestAcclaim, HighestAcclaimDelta,
                        AutarchTimes, AutarchTimesDelta
                    FROM vDaily_PlayerExport
                    WHERE GovernorID IN ({placeholders})
                    ORDER BY GovernorID, AsOfDate DESC
                    """
                    cursor.execute(query, governor_ids)

                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()

                    return pd.DataFrame.from_records(rows, columns=columns)
                finally:
                    conn.close()

            # Offload to thread
            df_daily = await asyncio.to_thread(_fetch_daily)

            if df_daily.empty:
                await ctx.respond("❌ No stats data found for your accounts.", ephemeral=True)
                return

            # Generate temp directory and filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_dir = tempfile.mkdtemp()

            # Build file based on format
            if format == "CSV":
                file_path = os.path.join(temp_dir, f"stats_{username}_{timestamp}.csv")
                await asyncio.to_thread(
                    build_user_stats_csv,
                    df_daily,
                    None,  # df_targets (not used)
                    out_path=file_path,
                    days_for_daily_table=days,
                )
                file_obj = discord.File(file_path, filename=f"stats_{username}_{timestamp}.csv")
                format_emoji = "📄"
                format_name = "CSV"
                description = "**Lightweight text-based format**\nOpen with any spreadsheet app."
                instructions = (
                    "**💻 Desktop:**\n"
                    "1. Download the attached file\n"
                    "2. Open with Excel, Google Sheets, or any spreadsheet app\n\n"
                    "**📱 Mobile:**\n"
                    "• **iPhone/iPad:** Tap attachment → Share → Save to Files → Open with Numbers or Google Sheets\n"
                    "• **Android:** Tap attachment → Download → Open with Google Sheets or Excel"
                )

            elif format == "GoogleSheets":
                # Generate Excel file (Google Sheets natively imports .xlsx)
                file_path = os.path.join(temp_dir, f"stats_{username}_{timestamp}.xlsx")
                await asyncio.to_thread(
                    build_user_stats_excel,
                    df_daily,
                    None,  # df_targets (not used)
                    out_path=file_path,
                    days_for_daily_table=days,
                )
                file_obj = discord.File(file_path, filename=f"stats_{username}_{timestamp}.xlsx")
                format_emoji = "📊"
                format_name = "Google Sheets"
                description = (
                    "**Google Sheets-compatible format**\nUpload to Google Drive to open in Sheets."
                )
                instructions = (
                    "**💻 Desktop:**\n"
                    "1. Download the attached file\n"
                    "2. Go to [drive.google.com](https://drive.google.com)\n"
                    "3. Click **New** → **File upload**\n"
                    "4. Upload this file → Double-click to open in Google Sheets\n\n"
                    "**📱 Mobile:**\n"
                    "• **iPhone/iPad:**\n"
                    "  1. Tap attachment → Share → Save to Files\n"
                    "  2. Open Google Drive app\n"
                    "  3. Tap **+** → **Upload** → Select file from Files\n"
                    "  4. Tap file in Drive to open in Sheets\n\n"
                    "• **Android:**\n"
                    "  1. Tap attachment → Download\n"
                    "  2. Open Google Drive app\n"
                    "  3. Tap **+** → **Upload** → Select downloaded file\n"
                    "  4. Tap file in Drive to open in Sheets"
                )

            else:  # Excel (default)
                file_path = os.path.join(temp_dir, f"stats_{username}_{timestamp}.xlsx")
                await asyncio.to_thread(
                    build_user_stats_excel,
                    df_daily,
                    None,  # df_targets (not used)
                    out_path=file_path,
                    days_for_daily_table=days,
                )
                file_obj = discord.File(file_path, filename=f"stats_{username}_{timestamp}.xlsx")
                format_emoji = "📗"
                format_name = "Excel"
                description = "**Full-featured Excel workbook**\nIncludes charts, formatting, and multiple sheets."
                instructions = (
                    "**💻 Desktop:**\n"
                    "1. Download the attached file\n"
                    "2. Open with Microsoft Excel, LibreOffice, or Numbers\n\n"
                    "**📱 Mobile:**\n"
                    "• **iPhone/iPad:** Tap attachment → Share → Open in Excel or Numbers\n"
                    "• **Android:** Tap attachment → Open with Excel or Google Sheets"
                )

            # Build response embed
            embed = discord.Embed(
                title=f"{format_emoji} Stats Export ({format_name})",
                description=description,
                color=0x2ECC71,
            )
            embed.add_field(
                name="📂 File Info",
                value=(
                    f"**Accounts:** {len(governor_ids)}\n"
                    f"**Daily Records:** {len(df_daily):,}\n"
                    f"**Date Range:** {days} days"
                ),
                inline=False,
            )
            embed.add_field(
                name="📖 How to Open",
                value=instructions,
                inline=False,
            )
            embed.set_footer(
                text=(
                    f"Exported {len(df_daily):,} records for {len(governor_ids)} account(s) • "
                    f"Data refreshed daily at ~06:00 UTC"
                )
            )

            await ctx.respond(embed=embed, file=file_obj, ephemeral=True)

            # Emit telemetry
            try:
                emit_telemetry_event(
                    {
                        "event": "my_stats_export",
                        "user_id": user_id,
                        "format": format,
                        "days": days,
                        "num_governors": len(governor_ids),
                        "num_rows": len(df_daily),
                    }
                )
            except Exception:
                pass

        except Exception as exc:
            logger.exception("Failed to export stats for user %s", ctx.author.id)
            await ctx.respond(
                f"❌ Export failed: {type(exc).__name__}\n\nPlease try again or contact support.",
                ephemeral=True,
            )

        finally:
            # CRITICAL: Always cleanup temp files, even on error
            if file_path and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                    logger.debug("Cleaned up temp file: %s", file_path)
                except Exception as e:
                    logger.warning("Failed to cleanup temp file %s: %s", file_path, e)

            if temp_dir and os.path.exists(temp_dir):
                try:
                    os.rmdir(temp_dir)
                    logger.debug("Cleaned up temp directory: %s", temp_dir)
                except Exception as e:
                    logger.warning("Failed to cleanup temp directory %s: %s", temp_dir, e)

    @bot.slash_command(
        name="player_stats",
        description="(Leadership) View stats for a player by GovernorID or fuzzy name",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.02")
    @safe_command
    @is_admin_or_leadership()
    @track_usage()
    async def player_stats_command(ctx, governor_id: int = 0, name: str = ""):
        await safe_defer(ctx, ephemeral=True)

        # Resolve actor (robust across forks)
        user_obj, _ = _actor_from_ctx(ctx)
        requester_id = user_obj.id

        # Resolve GovernorID(s)
        gov_ids: list[int] = []
        if governor_id:
            gov_ids = [int(governor_id)]
        elif name.strip():
            # Fuzzy match from your cached helper (label, value=str(gid)) pairs expected
            try:
                matches = autocomplete_choices(name.strip(), limit=5)  # -> List[Tuple[str, str]]
            except Exception:
                matches = []
            # Dedupe and coerce to int
            seen = set()
            for _, val in matches:
                try:
                    gid = int(val)
                except (TypeError, ValueError):
                    continue
                if gid not in seen:
                    seen.add(gid)
                    gov_ids.append(gid)
        else:
            await ctx.followup.send(
                "Provide a **GovernorID** or a **partial name**.", ephemeral=True
            )
            return

        if not gov_ids:
            await ctx.followup.send("No matching governors found.", ephemeral=True)
            return

        # Initial slice & payload
        slice_key = "wtd"
        payload = await get_stats_payload(requester_id, gov_ids, slice_key)
        rows = (payload or {}).get("rows") or []
        if not rows:
            await ctx.followup.send(
                "No stats available yet for that player/selection.", ephemeral=True
            )
            return

        # Build account names & name->id map
        # Prefer PER rows for names; fall back to fuzzy labels if needed
        per_names = sorted(
            {
                r.get("GovernorName", "")
                for r in rows
                if r.get("Grouping") == "PER" and r.get("GovernorName")
            }
        )
        account_options = per_names[:]  # dropdown labels

        name_to_id: dict[str, int] = {}
        # From payload (authoritative)
        for r in rows:
            if r.get("Grouping") == "PER":
                gname = str(r.get("GovernorName") or "").strip()
                try:
                    gid = int(r.get("GovernorID"))
                except (TypeError, ValueError):
                    continue
                if gname and gid:
                    name_to_id[gname] = gid
        # If empty (e.g., ALL rows only), seed from fuzzy match labels if available
        if not name_to_id and name.strip():
            try:
                matches = autocomplete_choices(name.strip(), limit=5)
            except Exception:
                matches = []
            for label, val in matches:
                try:
                    name_to_id[str(label).strip()] = int(val)
                except (TypeError, ValueError):
                    continue
            if not account_options:
                account_options = list(name_to_id.keys())

        # Decide initial choice
        choice = "ALL" if len(gov_ids) > 1 else (account_options[0] if account_options else "ALL")

        # Build embed & view
        embeds, files = build_embeds(slice_key, choice, payload)
        view = SliceButtons(
            requester_id=requester_id,
            initial_slice=slice_key,
            account_options=account_options,  # names for dropdown
            current_choice=choice,
            governor_ids=gov_ids,
            name_to_id=name_to_id or None,  # enables per-account switching
            timeout=14 * 60,
        )

        if files:
            msg = await ctx.followup.send(embeds=embeds, files=files, view=view, ephemeral=True)
        else:
            msg = await ctx.followup.send(embeds=embeds, view=view, ephemeral=True)

        # Let the View edit this message on timeout
        try:
            view.message = msg
        except Exception:
            pass

    def _send_report_text_or_file(interaction: discord.Interaction, title: str, summary: str):
        """
        Edits the original interaction with a short message and (if needed) a full report file.
        """
        MAX_DISCORD = 1900  # be safe under 2000 incl. code fences etc.
        ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        if len(summary) <= MAX_DISCORD:
            return interaction.edit_original_response(
                content=f"**{title}**\n```text\n{summary}\n```"
            )
        # attach as file
        buf = io.BytesIO(summary.encode("utf-8", "replace"))
        file = discord.File(buf, filename=f"subscription_migration_report_{ts}.txt")
        return interaction.edit_original_response(
            content=f"**{title}**\nReport was long; attached full details.", attachments=[file]
        )

    @bot.slash_command(
        name="migrate_subscriptions_dryrun",
        description="(Admin) Show what would change in the subscription file (no writes)",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def migrate_subscriptions_dryrun(ctx):
        await ctx.defer(ephemeral=True)
        try:
            before, after, summary = migrate_subscriptions(dry_run=True)
            await _send_report_text_or_file(
                ctx.interaction, title=f"Dry Run: subscriptions {before} → {after}", summary=summary
            )
        except Exception as e:
            await ctx.interaction.edit_original_response(
                content=f"❌ Dry run failed: `{type(e).__name__}: {e}`"
            )

    @bot.slash_command(
        name="migrate_subscriptions_apply",
        description="(Admin) Apply the subscription migration (writes file; backup created)",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def migrate_subscriptions_apply(ctx):
        await ctx.defer(ephemeral=True)
        try:
            before, after, summary = migrate_subscriptions(dry_run=False)
            await _send_report_text_or_file(
                ctx.interaction, title=f"Applied: subscriptions {before} → {after}", summary=summary
            )
        except Exception as e:
            await ctx.interaction.edit_original_response(
                content=f"❌ Migration failed: `{type(e).__name__}: {e}`"
            )

    @bot.slash_command(
        name="mykvkhistory",
        description="View your KVK-by-KVK history as a chart and table.",
        guild_ids=[GUILD_ID],
    )
    @channel_only(KVK_PLAYER_STATS_CHANNEL_ID, admin_override=False)
    @versioned("v1.09")
    @safe_command
    @track_usage()
    async def mykvkhistory(
        ctx: discord.ApplicationContext,
        ephemeral: bool = discord.Option(bool, "Only show to me", required=False, default=False),
        governor_id: int = discord.Option(
            int, "Governor ID (optional)", required=False, default=None
        ),
    ):
        await ctx.defer(ephemeral=ephemeral)

        registry = load_registry()
        user_id = str(ctx.user.id)
        payload = registry.get(user_id) or {}
        account_map = payload.get("accounts") or {}  # {label: {GovernorID, GovernorName}}

        # If a Governor ID is provided, build a minimal map for it (works even with no registry)
        if governor_id:
            # Best-effort name discovery; fall back to the ID string
            try:
                from kvk_history_utils import fetch_history_for_governors

                df_lookup = fetch_history_for_governors([governor_id])
                gov_name = None
                for col in ("GovernorName", "Gov_Name", "Name"):
                    if col in df_lookup.columns and not df_lookup[col].dropna().empty:
                        gov_name = str(df_lookup[col].dropna().iloc[0])
                        break
                gov_name = gov_name or str(governor_id)
            except Exception:
                gov_name = str(governor_id)
            account_map = {"Lookup": {"GovernorID": int(governor_id), "GovernorName": gov_name}}
        elif not account_map:
            await ctx.respond(
                "❌ You haven't registered any accounts yet. Use `/register_governor` or pass a Governor ID here.",
                ephemeral=True,
            )
            return

        def pick_default_id(m: dict) -> str:
            for label, meta in m.items():
                if str(label).lower().startswith("main"):
                    return str(meta["GovernorID"])
            return str(next(iter(m.values()))["GovernorID"])

        # Start on the provided governor_id when present, else Main/first
        default_id = str(governor_id) if governor_id else pick_default_id(account_map)

        view = KVKHistoryView(
            user=ctx.user,
            account_map=account_map,
            selected_ids=[default_id],  # start with just Main (or first)
            allow_all=True,
            ephemeral=ephemeral,  # <- pass through the user's choice
        )
        await view.initial_send(ctx)

    @bot.slash_command(
        name="kvk_rankings",
        description="Leaderboard for current KVK: Power, Kills, % Kill Target, Deads, or DKP.",
        guild_ids=[GUILD_ID],
    )
    @channel_only(KVK_PLAYER_STATS_CHANNEL_ID, admin_override=True)
    @versioned("v2.00")  # Updated version for PR3
    @safe_command
    @track_usage()
    async def kvk_rankings(ctx: discord.ApplicationContext):
        """
        Show KVK leaderboard with multi-column view.

        Default: Power (highest to lowest), Top 10, Page 1

        Features:
        - 5 sort metrics: Power, Kills, % Kill Target, Deads, DKP
        - 4 limit options: Top 10, 25, 50, 100
        - Automatic pagination for Top 100 (50 per page)
        - Excel-style sort indicator (▼) on active column

        Users can change sort metric and limit via dropdown/buttons.
        """
        await ctx.defer()

        cache = load_stat_cache()
        rows = [r for k, r in cache.items() if k != "_meta"]
        if not rows:
            await ctx.respond(
                "⚠️ No stats cache available yet. Try again after the next scan/export."
            )
            return

        # Default: Power sort, Top 10, Page 1
        view = KVKRankingView(cache, metric="power", limit=10, timeout=120.0)
        embed = build_kvkrankings_embed(rows, "power", 10, page=1)

        # Fallback footer if helper didn't set one
        if not embed.footer or not embed.footer.text:
            last_ref = cache.get("_meta", {}).get("generated_at") or "unknown"
            embed.set_footer(text=f"Last refreshed: {last_ref}")

        resp = await ctx.respond(embed=embed, view=view)
        try:
            view.message = await ctx.interaction.original_response()
        except Exception:
            try:
                view.message = await resp.original_response()
            except Exception:
                view.message = None

    @bot.slash_command(
        name="kvk_export_all",
        description="Export all-kingdom KVK tabs",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.05")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def kvk_export_all(ctx, kvk_no: int = 0, sheet_name: str = None):
        await safe_defer(ctx, ephemeral=True)

        # Resolve current KVK if not provided
        if kvk_no == 0:
            with _conn() as cn, cn.cursor() as c:
                c.execute("""
                    SELECT TOP 1 KVK_NO
                    FROM dbo.KVK_Details
                    WHERE GETUTCDATE() BETWEEN KVK_REGISTRATION_DATE AND KVK_END_DATE
                    ORDER BY KVK_NO DESC
                """)
                row = c.fetchone()
            if not row:
                await ctx.followup.send(
                    "❌ Could not resolve the current KVK window.", ephemeral=True
                )
                return
            kvk_no = int(row[0])

        # Default sheet name from constants (allows slash arg override)
        sheet_name = (sheet_name or KVK_SHEET_NAME).strip() or KVK_SHEET_NAME

        await ctx.followup.send(f"⏳ Exporting KVK `{kvk_no}` to **{sheet_name}**…", ephemeral=True)

        ok = await asyncio.to_thread(
            run_kvk_proc_exports_with_alerts,
            SERVER,
            DATABASE,
            USERNAME,
            PASSWORD,
            kvk_no,
            sheet_name,
            CREDENTIALS_FILE,
            ctx.channel,
            ctx.bot.loop,
        )

        if ok:
            await ctx.followup.send(
                f"✅ Exported KVK `{kvk_no}` to **{sheet_name}**.", ephemeral=True
            )
        else:
            await ctx.followup.send(
                f"💥 Export failed for KVK `{kvk_no}`. Check logs.", ephemeral=True
            )

    @bot.slash_command(
        name="kvk_recompute",
        description="Recompute windowed outputs for the current KVK",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def kvk_recompute(ctx, kvk_no: int = 0):
        await safe_defer(ctx, ephemeral=True)
        try:

            def _run():
                t0 = time.perf_counter()
                with _conn() as cn, cn.cursor() as c:
                    kvk = _resolve_kvk_no(c, kvk_no)
                    c.execute("EXEC KVK.sp_KVK_Recompute_Windows @KVK_NO=?", (kvk,))
                    cn.commit()
                    dur = time.perf_counter() - t0
                    return kvk, dur

            kvk, dur = await asyncio.to_thread(_run)
            await ctx.followup.send(f"✅ Recomputed KVK `{kvk}` in `{dur:.2f}s`.", ephemeral=True)
        except Exception as e:
            await ctx.followup.send(f"💥 {type(e).__name__}: {e}", ephemeral=True)

    @bot.slash_command(
        name="kvk_list_scans",
        description="List recent scans for a KVK",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def kvk_list_scans(ctx, kvk_no: int = 0, limit: int = 20):
        await safe_defer(ctx, ephemeral=True)
        limit = max(1, min(int(limit), 100))
        try:

            def _run():
                with _conn() as cn, cn.cursor() as c:
                    kvk = _resolve_kvk_no(c, kvk_no)
                    c.execute(
                        """
                        SELECT TOP (?)
                               ScanID, ScanTimestampUTC, Row_Count, SourceFileName, ImportedAtUTC
                        FROM KVK.KVK_Scan
                        WHERE KVK_NO = ?
                        ORDER BY ScanID DESC
                    """,
                        (limit, kvk),
                    )
                    return kvk, c.fetchall()

            kvk, rows = await asyncio.to_thread(_run)

            lines = [
                "```",
                f"{'ScanID':>6}  {'Scan UTC':19}  {'Rows':>6}  {'Imported UTC':19}  Source",
            ]
            for scan_id, ts, rows_cnt, src, imp in rows:
                lines.append(
                    f"{scan_id:>6}  {str(ts)[:19]:19}  {rows_cnt:>6}  {str(imp)[:19]:19}  {str(src)[:50]}"
                )
            lines.append("```")

            await ctx.followup.send(
                content=f"**KVK {kvk} — Recent Scans (Top {limit})**\n" + "\n".join(lines),
                ephemeral=True,
            )
        except Exception as e:
            await ctx.followup.send(f"❌ {type(e).__name__}: {e}", ephemeral=True)

    @bot.slash_command(
        name="test_kvk_embed",
        description="🧪 Post the KVK daily embed in test mode",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.04")  # bump to force re-register
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def test_kvk_embed(
        ctx: discord.ApplicationContext,
        post_here: bool = discord.Option(  # <-- TYPE first, not default
            bool,
            "Post in THIS channel? (False → Stats Alert channel)",
            required=False,
            default=True,
        ),
    ):
        await safe_defer(ctx, ephemeral=True)

        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        # Whether the season is currently KVK (for the send_stats_update_embed path)
        is_kvk = await asyncio.to_thread(is_currently_kvk, SERVER, DATABASE, USERNAME, PASSWORD)

        try:
            if post_here:
                # Directly call the internal builder to post in the invoking channel, test-mode (no ping)
                await send_kvk_embed(ctx.bot, ctx.channel, ts, is_test=True)
                where = ctx.channel.mention
            else:
                # Use the public entrypoint; test-mode skips daily-send guards and pings, posts to Stats channel
                await send_stats_update_embed(ctx.bot, ts, True, is_test=True)
                where = f"<#{STATS_ALERT_CHANNEL_ID}>"

            await ctx.followup.send(
                f"✅ Sent KVK test embed to {where} (is_kvk={is_kvk}).", ephemeral=True
            )
        except Exception as e:
            logger.exception("[/test_kvk_embed] failed")
            await ctx.followup.send(
                f"❌ Failed to send test embed:\n`{type(e).__name__}: {e}`", ephemeral=True
            )

    @bot.slash_command(
        name="kvk_window_preview",
        description="Show KVK windows with scan edges, scan counts, and row counts",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.08")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def kvk_window_preview(ctx, kvk_no: int = 0):
        await safe_defer(ctx, ephemeral=True)

        def _run():
            with _conn() as cn, cn.cursor() as c:
                kvk = _resolve_kvk_no(c, kvk_no)

                # Precompute max ScanID for this KVK (used for 'open' end)
                c.execute("SELECT MAX(ScanID) FROM KVK.KVK_Scan WHERE KVK_NO=?", (kvk,))
                _row = fetch_one_dict(c)
                # fetch_one_dict returns None if no rows, else dict mapping column -> value
                if _row:
                    # extract first (and only) column's value in a safe way:
                    first_val = next(iter(_row.values()))
                    max_scan = int(first_val or 0)
                else:
                    max_scan = 0

                # One shot query with per-window counts/timestamps
                c.execute(
                    """
                    WITH MaxScan AS (
                      SELECT ? AS KVK_NO, ? AS MaxScanID
                    )
                    SELECT
                      w.WindowName,
                      w.StartScanID,
                      w.EndScanID,
                      s1.ScanTimestampUTC AS StartTS,
                      s2.ScanTimestampUTC AS EndTS,
                      CASE
                        WHEN w.StartScanID IS NULL THEN NULL
                        ELSE (
                          SELECT COUNT(*) FROM KVK.KVK_Scan s
                          WHERE s.KVK_NO=w.KVK_NO
                            AND s.ScanID BETWEEN w.StartScanID AND COALESCE(w.EndScanID, m.MaxScanID)
                        )
                      END AS NumScans,
                      (SELECT COUNT(*) FROM KVK.KVK_Player_Windowed p
                         WHERE p.KVK_NO=w.KVK_NO AND p.WindowName=w.WindowName) AS RowCount
                    FROM KVK.KVK_Windows w
                    JOIN MaxScan m ON m.KVK_NO=w.KVK_NO
                    LEFT JOIN KVK.KVK_Scan s1 ON s1.KVK_NO=w.KVK_NO AND s1.ScanID=w.StartScanID
                    LEFT JOIN KVK.KVK_Scan s2 ON s2.KVK_NO=w.KVK_NO AND s2.ScanID=COALESCE(w.EndScanID, m.MaxScanID)
                    WHERE w.KVK_NO=?
                    ORDER BY CASE WHEN w.StartScanID IS NULL THEN 1 ELSE 0 END, w.WindowName;
                """,
                    (kvk, max_scan, kvk),
                )

                cols = [d[0] for d in c.description]
                rows = [dict(zip(cols, r, strict=False)) for r in c.fetchall()]

                # quick validations
                bad_ranges = [
                    r
                    for r in rows
                    if r["StartScanID"] is not None
                    and r["EndScanID"] is not None
                    and r["EndScanID"] < r["StartScanID"]
                ]
                return kvk, rows, bad_ranges

        kvk, rows, bad = await asyncio.to_thread(_run)

        def _fmt_ts(dtval):
            try:
                if not dtval:
                    return "—"
                # KVK tables should be UTC; format compact
                return dtval.strftime("%d %b %H:%M")
            except Exception:
                return "—"

        # build a neat monospace table
        header = f"{'Window':20} {'Start':>8} {'End':>8} {'#Scans':>7} {'Rows':>7}"
        lines = [header, "-" * len(header)]
        for r in rows:
            nm = (r["WindowName"] or "")[:20]
            st = str(r["StartScanID"]) if r["StartScanID"] is not None else "—"
            en = str(r["EndScanID"]) if r["EndScanID"] is not None else "open"
            sc = str(r["NumScans"]) if r["NumScans"] is not None else "—"
            rc = str(r["RowCount"] or 0)
            lines.append(f"{nm:20} {st:>8} {en:>8} {sc:>7} {rc:>7}")

        # second line with timestamps for context
        lines.append("")
        lines.append("Timestamps (UTC):")
        lines.append(f"{'Window':20} {'StartTS':>16} {'EndTS':>16}")
        lines.append("-" * 56)
        for r in rows:
            nm = (r["WindowName"] or "")[:20]
            st = _fmt_ts(r["StartTS"])
            en = _fmt_ts(r["EndTS"])
            lines.append(f"{nm:20} {st:>16} {en:>16}")

        body = "```\n" + "\n".join(lines[:400]) + "\n```"  # safety bound

        desc = (
            f"KVK **{kvk}** — window preview at {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}"
        )
        if bad:
            desc += f"\n⚠️ {len(bad)} window(s) have End < Start."

        embed = discord.Embed(
            title="KVK Window Preview", description=desc, color=discord.Color.blurple()
        )
        embed.add_field(name="Windows", value=body, inline=False)

        await ctx.followup.send(embed=embed, ephemeral=True)

    def _format_validate_embed(report) -> discord.Embed:
        embed = discord.Embed(
            title="CrystalTech Validation",
            description=report.summary(),
            color=discord.Color.green() if report.ok else discord.Color.red(),
        )
        # Show up to 10 issues for brevity
        shown = 0
        for issue in report.issues:
            if shown >= 10:
                remaining = len(report.issues) - shown
                if remaining > 0:
                    embed.add_field(
                        name="…", value=f"+{remaining} more issues not shown", inline=False
                    )
                break
            loc = []
            if issue.path_id:
                loc.append(f"path={issue.path_id}")
            if issue.step_uid:
                loc.append(f"step={issue.step_uid}")
            where = f" ({', '.join(loc)})" if loc else ""
            embed.add_field(
                name=f"[{issue.level}] {issue.code}{where}",
                value=(issue.message[:512] + ("…" if len(issue.message) > 512 else "")) or "—",
                inline=False,
            )
            shown += 1
        return embed

    @bot.slash_command(
        name="crystaltech_validate",
        description="Validate CrystalTech config & assets.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @is_admin_and_notify_channel()
    @safe_command
    @track_usage()
    async def crystaltech_validate(ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)
        try:
            service = get_crystaltech_service()
        except Exception as e:
            await ctx.respond(f"❌ Service not initialized: `{e}`", ephemeral=True)
            return

        report = service.report()
        if report is None:
            # If not yet loaded for any reason, trigger a fresh load here
            report = await service.reload(fail_on_warn=False)

        embed = _format_validate_embed(report)
        await ctx.respond(embed=embed, ephemeral=True)

    @bot.slash_command(
        name="crystaltech_reload",
        description="Reload CrystalTech config (hot).",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @is_admin_and_notify_channel()
    @safe_command
    @track_usage()
    async def crystaltech_reload(ctx: discord.ApplicationContext, fail_on_warn: bool = False):
        await ctx.defer(ephemeral=True)
        try:
            service = get_crystaltech_service()
        except Exception as e:
            await ctx.respond(f"❌ Service not initialized: `{e}`", ephemeral=True)
            return

        report = await service.reload(fail_on_warn=fail_on_warn)
        embed = _format_validate_embed(report)
        await ctx.respond(embed=embed, ephemeral=True)

    # ---------- CrystalTech runner using the generic picker ----------
    async def run_crystaltech_flow(
        interaction: discord.Interaction, governor_id: str, ephemeral: bool
    ):
        from crystaltech_di import get_crystaltech_service

        # 0) Claim the governor for this user (one session at a time)
        claimed, why = _session_claim(governor_id, interaction.user.id)
        if not claimed:
            msg = f"🔒 {why}"
            if not interaction.response.is_done():
                await interaction.response.send_message(msg, ephemeral=True)
            else:
                await interaction.followup.send(msg, ephemeral=True)
            return

        # release helper (used by views on timeout/reset, and by error paths here)
        async def _release():
            _session_release(governor_id, interaction.user.id)

        try:
            try:
                service = get_crystaltech_service()
            except Exception as e:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        f"❌ CrystalTech is unavailable: `{e}`", ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"❌ CrystalTech is unavailable: `{e}`", ephemeral=True
                    )
                await _release()
                return

            rep = service.report()
            if not service.is_ready:
                msg = rep.summary() if rep else "Service not initialized."
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ {msg}", ephemeral=True)
                await _release()
                return

            entry = service.get_user_entry(governor_id)
            if entry:
                # Existing user → open progress panel as a fresh ephemeral message
                path_id = entry.get("selected_path_id")
                troop = entry.get("selected_troop_type", "unknown")

                view = ProgressView(
                    author_id=interaction.user.id,
                    governor_id=governor_id,
                    path_id=path_id,
                    troop=troop,
                    timeout=300,
                    on_release=_release,  # <-- important
                )
                embed, files = await view.render_embed()

                # Ack the picker (no files on edit), then send panel
                try:
                    await interaction.response.edit_message(
                        content="Opening progress…", embed=None, view=None, attachments=[]
                    )
                except Exception:
                    pass

                sent = await interaction.followup.send(
                    embed=embed, files=files, ephemeral=ephemeral, view=view
                )
                view.message = sent
                _session_refresh(governor_id, interaction.user.id)
                return

            # ---------- FIRST-TIME SETUP ----------
            label = await _resolve_governor_label(interaction.user.id, governor_id)
            accounts = [(governor_id, label)]
            view = SetupView(
                author_id=interaction.user.id,
                accounts=accounts,
                timeout=300,
                on_release=_release,  # <-- important
            )
            embed = view.make_embed()

            # 1) Ack the picker message (no components or files)
            try:
                await interaction.response.edit_message(
                    content="Opening setup…", embed=None, view=None, attachments=[]
                )
            except Exception:
                pass

            # 2) Send a NEW ephemeral message with the Setup view (so components render reliably)
            sent = await interaction.followup.send(embed=embed, ephemeral=ephemeral, view=view)
            view.message = sent
            _session_refresh(governor_id, interaction.user.id)

        except Exception as e:
            logger.exception("[CrystalTech] run_crystaltech_flow unhandled: %s", e, exc_info=True)
            # best-effort notify and release
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"❌ Unexpected error: `{type(e).__name__}: {e}`", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"❌ Unexpected error: `{type(e).__name__}: {e}`", ephemeral=True
                )
            await _release()

    @bot.slash_command(
        name="mykvkcrystaltech",
        description="🔬 Guide and track your KVK Crystal Tech path",
        guild_ids=[GUILD_ID],
    )
    @channel_only(KVK_CRYSTALTECH_CHANNEL_ID, admin_override=True)
    @versioned("v2.20")
    @safe_command
    @track_usage()
    async def mykvkcrystaltech(
        ctx: discord.ApplicationContext,
        governorid: str = discord.Option(
            str,
            name="governorid",
            description="(Optional) Governor ID if you prefer to type it",
            required=False,
            default=None,
        ),
        only_me: bool = discord.Option(
            bool,
            name="only_me",
            description="Show only to me (ephemeral)",
            required=False,
            default=True,  # CrystalTech is personal; default to ephemeral
        ),
    ):
        await safe_defer(ctx, ephemeral=only_me)

        # 1) Manual ID path
        if governorid and governorid.strip().isdigit():
            await run_crystaltech_flow(ctx.interaction, governorid.strip(), ephemeral=only_me)
            return

        # 2) Registered accounts path — reuse same registry logic & helpers as /mykvktargets
        try:
            registry = await asyncio.to_thread(load_registry)
            user_block = registry.get(str(ctx.user.id)) or {}
            accounts = user_block.get("accounts") or {}
        except Exception:
            logger.exception("[/mykvkcrystaltech] load_registry failed")
            await ctx.followup.send(
                "⚠️ Couldn’t load your registered accounts. Provide `governorid` or try again later.",
                ephemeral=only_me,
            )
            return

        # Use canonical builder (safe fallback included)
        options = _safe_build_unique_gov_options(accounts)

        if options:
            if len(options) == 1:
                only_gid = options[0].value
                await run_crystaltech_flow(ctx.interaction, only_gid, ephemeral=only_me)
                return

            # Build the AccountPickerView directly (no lazy-resolve helper anymore)
            async def _on_select(i, gid, ep):
                # ensure we pass the interaction into run_crystaltech_flow
                await run_crystaltech_flow(i, gid, ephemeral=ep)

            view = AccountPickerView(
                ctx=ctx,
                options=options,
                on_select_governor=_on_select,
                heading="Select an account to manage its Crystal Tech:",
                show_register_btn=True,
                ephemeral=only_me,
            )
            await ctx.followup.send(view.heading, view=view, ephemeral=only_me)
        else:
            hint = (
                "You don’t have any linked governor accounts yet.\n"
                "• Use `/link_account` (Register new account), or\n"
                "• Re-run this command with the `governorid` option."
            )

            async def _on_select(i, gid, ep):
                await run_crystaltech_flow(i, gid, ephemeral=ep)

            view = AccountPickerView(
                ctx=ctx,
                options=[],
                on_select_governor=_on_select,
                heading="Select an account to manage its Crystal Tech:",
                show_register_btn=True,
                ephemeral=only_me,
            )
            await ctx.followup.send(hint, view=view, ephemeral=only_me)

    @bot.slash_command(
        name="crystaltech_admin_reset",
        description="Archive CrystalTech progress and reset for the next KVK.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @is_admin_and_notify_channel()
    @safe_command
    @track_usage()
    async def crystaltech_admin_reset(
        ctx: discord.ApplicationContext,
        next_kvk_no: int = discord.Option(
            int,
            name="next_kvk_no",
            description="Optional: set the KVK number for the new season (e.g., 14).",
            required=False,
            default=None,
        ),
        only_me: bool = discord.Option(
            bool,
            name="only_me",
            description="Show only to me (ephemeral).",
            required=False,
            default=True,
        ),
    ):
        await safe_defer(ctx, ephemeral=only_me)
        from crystaltech_di import get_crystaltech_service

        try:
            service = get_crystaltech_service()
            if not service.is_ready:
                rep = service.report()
                msg = rep.summary() if rep else "Service not initialized."
                await ctx.followup.send(f"❌ {msg}", ephemeral=only_me)
                return

            # archive + reset
            archive_path = await service.archive_and_reset_all(next_kvk_no=next_kvk_no)
            await ctx.followup.send(
                f"✅ Archived current progress and reset for the next KVK."
                f"\n• Archive file: `{archive_path}`"
                f"\n• Next KVK: `{next_kvk_no if next_kvk_no is not None else 'unchanged'}`",
                ephemeral=only_me,
            )
        except Exception as e:
            logger.exception("[/crystaltech_admin_reset] failed")
            await ctx.followup.send(f"❌ Failed: `{type(e).__name__}: {e}`", ephemeral=only_me)

    @bot.slash_command(
        name="honor_rankings",
        description="Show the latest Honour Top-N (default 10, max 50).",
        guild_ids=[GUILD_ID],
    )
    @channel_only(KVK_PLAYER_STATS_CHANNEL_ID, admin_override=False)
    @versioned("v1.04")
    @safe_command
    @track_usage()
    async def honor_rankings(ctx: discord.ApplicationContext):
        """
        /honor_rankings - show Top 10 honor by default and let user switch Top 10/25/50/100 with buttons.
        """
        # Defer to allow DB fetch
        await safe_defer(ctx, ephemeral=False)

        initial_limit = 10

        try:
            rows = await get_latest_honor_top(initial_limit)
        except Exception:
            logger.exception("[HONOR] get_latest_honor_top failed")
            rows = []

        if not rows:
            # graceful response if DB has no honor data
            await ctx.respond("No honor data found for the latest KVK.", ephemeral=False)
            return

        embed = build_honor_rankings_embed(rows, limit=initial_limit)
        view = HonorRankingView()
        await ctx.respond(embed=embed, view=view, ephemeral=False)

    @bot.slash_command(
        name="honor_purge_last",
        description="Purge the latest Honour scan (test cleanup).",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @is_admin_and_notify_channel()
    @safe_command
    @track_usage()
    async def honor_purge_last(ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)

        deleted = await asyncio.to_thread(purge_latest_honor_scan)

        if deleted > 0:
            title = "✅ Purged latest Honour scan"
            desc = f"Deleted **{deleted}** player rows and the scan header."
            color = discord.Color.orange()
        else:
            title = "ℹ️ Nothing to purge"
            desc = "No KVK or scan was found."
            color = discord.Color.dark_grey()

        embed = discord.Embed(title=title, description=desc, color=color)
        await ctx.respond(embed=embed, ephemeral=True)
