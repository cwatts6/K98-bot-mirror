# Commands.py
from __future__ import annotations

import asyncio
import builtins as _bi
from collections import deque
import csv
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
import functools
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
from discord import Embed
from discord.errors import HTTPException, NotFound
from discord.ext import commands as ext_commands  # avoid name conflict
from discord.ui import View
from dotenv import load_dotenv
import pandas as pd

# ——— Third-party ———
import pyodbc

from admin_helpers import log_processing_result, prompt_admin_inputs
from bot_config import (
    ADMIN_USER_ID,
    GUILD_ID,
    KVK_EVENT_CHANNEL_ID,
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
from crystaltech_ui import ProgressView, SetupView
from daily_KVK_overview_embed import post_or_update_daily_KVK_overview
from decoraters import (
    _actor_from_ctx,
    _has_leadership_role,
    _is_admin,
    _is_allowed_channel,
    is_admin_and_notify_channel,
    is_admin_or_leadership,
    track_usage,
)
from dm_tracker_utils import (
    purge_user_from_dm_scheduled_tracker,
    purge_user_from_dm_sent_tracker,
)
from embed_my_stats import SliceButtons, build_embeds
from embed_offseason_stats import send_offseason_stats_embed_v2
from embed_player_profile import build_player_profile_embed
from embed_utils import (
    FailuresView,
    HistoryView,
    LocalTimeToggleView,
    build_stats_embed,
    build_target_embed,
    format_event_embed,
    format_fight_embed,
    generate_summary_embed,
)
from event_cache import get_last_refreshed, is_cache_stale, refresh_event_cache
from event_embed_manager import update_live_event_embeds
from event_scheduler import dm_scheduled_tracker, dm_sent_tracker
from file_utils import append_csv_line, read_summary_log_rows

# Provide a standard UTC alias
UTC = UTC

# ——— Local modules ———
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
    run_kvk_proc_exports_with_alerts,
)
from kvk_history_view import KVKHistoryView
from location_importer import load_staging_and_merge, parse_output_csv
from logging_setup import CRASH_LOG_PATH, ERROR_LOG_PATH, FULL_LOG_PATH, flush_logs
from player_stats_cache import build_player_stats_cache
from proc_config_import import run_proc_config_import
from profile_cache import (
    autocomplete_choices,
    get_profile_cached,
    search_by_governor_name,
    warm_cache,
)
from rehydrate_views import save_view_tracker, serialize_event
from reminder_task_registry import active_task_count, cancel_user_reminder_tasks
from stats_alert_utils import (
    _send_kvk_embed,
    get_latest_honor_top,
    is_currently_kvk,
    purge_latest_honor_scan,
    send_stats_update_embed,
)
from stats_exporter import build_user_stats_excel
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
from utils import (
    get_next_events,
    get_next_fights,
    load_stat_cache,
    load_stat_row,
    make_cid,
    normalize_governor_id,
    utcnow,
)
from versioning import versioned

logger = logging.getLogger(__name__)

# --- Operation locks (serialize sensitive ops) -----------------------------
_op_locks = {
    "resync": asyncio.Lock(),
    "restart": asyncio.Lock(),
    "import_regs": asyncio.Lock(),
}


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


# === Global error handler for slash commands (registered in register_commands) ===
async def _global_cmd_error_handler(ctx, error):
    logger.exception(
        "[CMD ERROR] %s",
        getattr(getattr(ctx, "command", None), "qualified_name", "unknown"),
        exc_info=error,
    )
    try:
        inter = getattr(ctx, "interaction", None) or ctx
        if not inter.response.is_done():
            responder = getattr(ctx, "respond", None)
            if responder is not None:
                await responder(
                    "⚠️ Sorry, something went wrong. The team has been notified.", ephemeral=True
                )
            else:
                await inter.response.send_message(
                    "⚠️ Sorry, something went wrong. The team has been notified.", ephemeral=True
                )
        else:
            await inter.followup.send(
                "⚠️ Sorry, something went wrong. The team has been notified.", ephemeral=True
            )
    except Exception:
        pass


load_dotenv()

# Safer construction (avoids int(None))
ALLOWED_CHANNEL_IDS = {int(cid) for cid in (NOTIFY_CHANNEL_ID, LEADERSHIP_CHANNEL_ID) if cid}

start_bot_time = datetime.now(UTC)


def safe_command(fn):
    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except Exception:
            logger.exception("[CMD ERROR] %s", getattr(fn, "__name__", "unknown"))
            # best-effort user feedback (ephemeral) without double-acking
            ctx = args[0] if args else None
            try:
                inter = getattr(ctx, "interaction", None) or ctx
                if hasattr(ctx, "respond") and not inter.response.is_done():
                    await ctx.respond(
                        "⚠️ Something went wrong. The team has been notified.", ephemeral=True
                    )
                else:
                    await inter.followup.send(
                        "⚠️ Something went wrong. The team has been notified.", ephemeral=True
                    )
            except Exception:
                pass
            return None

    return wrapper


# Ensure safe_defer available across the file
async def safe_defer(ctx, *, ephemeral: bool = True) -> bool:
    """Best-effort defer that won't crash on unknown/expired interaction."""
    try:
        ir = getattr(ctx, "interaction", None)
        if ir and hasattr(ir, "response") and not ir.response.is_done():
            await ir.response.defer(ephemeral=ephemeral)
            return True
        # discord.py variants also expose ctx.defer()
        if hasattr(ctx, "defer"):
            await ctx.defer(ephemeral=ephemeral)
            return True
    except (NotFound, HTTPException):
        # Interaction expired or the bot disconnected mid-flight
        pass
    except Exception:
        pass
    return False


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


def _resolve_kvk_no(c, kvk_no: int | None) -> int:
    if kvk_no and kvk_no > 0:
        return int(kvk_no)
    c.execute(
        """
        SELECT TOP 1 KVK_NO
        FROM dbo.KVK_Details             -- change to dbo.KVK_Details if your schema differs
        WHERE GETUTCDATE() BETWEEN KVK_REGISTRATION_DATE AND KVK_END_DATE
        ORDER BY KVK_NO DESC
    """
    )
    row = c.fetchone()
    if not row:
        raise ValueError("Could not resolve the current KVK window.")
    return int(row[0])


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


def _build_unique_gov_options(accounts: dict) -> list[discord.SelectOption]:
    """
    Build a unique, ordered list of SelectOptions from a user's accounts.
    - Ensures unique 'value' (GovernorID) to satisfy Discord.
    - Prefers ACCOUNT_ORDER if available; otherwise falls back to sorted keys.
    - Trims label lengths to Discord's 100-char limit.
    - Caps the result to 25 options (Discord limit).
    """
    # Order slots predictably
    try:
        slot_order = list(ACCOUNT_ORDER)
    except NameError:
        slot_order = sorted(accounts.keys())

    seen: set[str] = set()
    opts: list[discord.SelectOption] = []

    for slot in slot_order:
        rec = (accounts or {}).get(slot) or {}
        gid = str(rec.get("GovernorID", "")).strip()
        if not gid or gid in seen:
            continue  # skip empties/duplicates
        gname = str(rec.get("GovernorName") or slot).strip()
        # Label format: "Name • ID" (trim to 100 chars for Discord)
        label = f"{gname} • {gid}"
        if len(label) > 100:
            # keep the tail (ID) and as much name as possible
            label = (gname[: 100 - (3 + len(gid))] + "...") + f" • {gid}"
        opts.append(discord.SelectOption(label=label, value=gid))
        seen.add(gid)
        if len(opts) >= 25:  # Discord hard cap
            break

    return opts


class LogTailView(discord.ui.View):
    def __init__(self, ctx, src_path, title, level=None, contains=None, page=1, page_size=50):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.src_path = src_path
        self.title = title
        self.level = (level or "").upper().strip() or None
        self.contains = contains.strip() if contains else None
        self.page = max(1, int(page or 1))
        self.page_size = max(10, min(int(page_size or 50), 200))

        self.prev.disabled = self.page <= 1

    def _match(self, line: str) -> bool:
        if self.level:
            # naive level check (works with standard logging format)
            # e.g., "INFO", "WARNING", "ERROR", "CRITICAL"
            if self.level not in line:
                return False
        if self.contains:
            try:
                if re.search(self.contains, line, re.IGNORECASE) is None:
                    return False
            except re.error:
                if self.contains.lower() not in line.lower():
                    return False
        return True

    def _tail_filtered(self):
        if not os.path.exists(self.src_path):
            return [], 0, 0, 0

        total_lines = 0
        dq = deque(maxlen=50000)
        with open(self.src_path, encoding="utf-8", errors="replace", newline="") as f:
            for ln in f:
                total_lines += 1
                dq.append(ln.rstrip("\n"))

        # NEW: newest-first by iterating reversed(dq)
        matched = []
        for ln in reversed(dq):
            if self._match(ln):
                matched.append(ln)

        total_matches = len(matched)
        total_pages = max(1, (total_matches + self.page_size - 1) // self.page_size)
        self.page = min(self.page, total_pages)

        start = (self.page - 1) * self.page_size
        end = start + self.page_size
        return matched[start:end], total_lines, total_matches, total_pages

    def _color(self):
        name = os.path.basename(self.src_path).lower()
        if "error" in name:
            return 0xE74C3C
        if "crash" in name:
            return 0xFF6347
        return 0x3498DB

    async def render(self, interaction: discord.Interaction):
        # 1) Compute page slice
        lines, total_lines, total_matches, total_pages = self._tail_filtered()
        body = "\n".join(lines).strip() or "(no matching lines)"
        body = body.replace("```", "`\u200b``")  # fence safety

        # 2) Budget + description
        BUDGET = 3800
        needs_file = len(body) > BUDGET
        desc_body = body[:BUDGET]
        if needs_file:
            desc_body += "\n…(truncated)"
        desc = f"```{desc_body}```"

        # 3) File stats for footer
        try:
            mtime = os.path.getmtime(self.src_path)
            mtime_dt = datetime.utcfromtimestamp(mtime)
            size_kb = os.path.getsize(self.src_path) // 1024
        except Exception:
            mtime_dt, size_kb = datetime.utcnow(), 0

        # 4) Build the embed (DEFINE IT BEFORE kwargs)
        filters = []
        if self.level:
            filters.append(f"level={self.level}")
        if self.contains:
            filters.append(f"contains=/{self.contains}/")
        filter_text = " • ".join(filters) if filters else "none"

        embed = discord.Embed(
            title=self.title,
            description=desc,
            color=self._color(),
        )
        embed.add_field(name="Page", value=f"{self.page}/{total_pages}", inline=True)
        embed.add_field(name="Matches", value=str(total_matches), inline=True)
        embed.add_field(
            name="File Stats",
            value=f"{os.path.basename(self.src_path)} • {size_kb} KB",
            inline=True,
        )
        embed.set_footer(text=f"Modified {mtime_dt:%Y-%m-%d %H:%M:%S} UTC • Filters: {filter_text}")
        embed.timestamp = datetime.utcnow()

        # 5) Prepare kwargs correctly
        kwargs = {"embed": embed, "view": self}

        if needs_file:
            # Upload a fresh file for this page
            buf = io.BytesIO(("\n".join(lines)).encode("utf-8", "replace"))
            buf.seek(0)
            file = discord.File(buf, filename=f"log_page_{self.page}.txt")
            kwargs["files"] = [file]
        else:
            # If a previous page attached a file, clear it now
            kwargs["attachments"] = []

        # 6) Edit depending on interaction state
        if interaction.response.is_done():
            await interaction.edit_original_response(**kwargs)
        else:
            await interaction.response.edit_message(**kwargs)

    @discord.ui.button(label="◀️ Newer", style=discord.ButtonStyle.secondary)
    async def prev(self, _, interaction: discord.Interaction):
        if self.page > 1:
            self.page -= 1
        self.prev.disabled = self.page <= 1
        await self.render(interaction)

    @discord.ui.button(label="Older ▶️", style=discord.ButtonStyle.secondary)
    async def next(self, _, interaction: discord.Interaction):
        self.page += 1
        self.prev.disabled = self.page <= 1
        await self.render(interaction)

    @discord.ui.button(label="🔎 Toggle Filter", style=discord.ButtonStyle.primary)
    async def show_filters(self, _, interaction: discord.Interaction):
        txt = (
            f"**Current filters**\n"
            f"- level: `{self.level or 'none'}`\n"
            f"- contains: `{self.contains or 'none'}`\n"
            f"- page_size: `{self.page_size}`\n\n"
            f"Tip: Use command options to set filters, e.g.:\n"
            f'`/logs source:error level:ERROR contains:"sql" page_size:100`'
        )
        await interaction.response.send_message(txt, ephemeral=True)


def _pick_log_source(source: str):
    s = (source or "general").lower()
    if s.startswith("err"):
        return ERROR_LOG_PATH
    if s.startswith("cr"):
        return CRASH_LOG_PATH
    return FULL_LOG_PATH


ACCOUNT_ORDER = ["Main"] + [f"Alt {i}" for i in range(1, 6)] + [f"Farm {i}" for i in range(1, 11)]


class MyRegsActionView(discord.ui.View):
    def __init__(self, *, author_id: int, has_regs: bool, timeout: float = 120):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self._message: discord.Message | None = None

        # Disable "Modify Registration" if no regs, robustly
        if not has_regs:
            for child in self.children:
                try:
                    if (
                        isinstance(child, discord.ui.Button)
                        and child.label == "Modify Registration"
                    ):
                        child.disabled = True
                except Exception:
                    pass

    def set_message_ref(self, message: discord.Message):
        self._message = message

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and interaction.user.id == self.author_id:
            return True
        try:
            await interaction.response.send_message("❌ This menu isn’t for you.", ephemeral=True)
        except Exception:
            pass
        return False

    async def on_timeout(self):
        for c in self.children:
            c.disabled = True
        try:
            if self._message:
                await self._message.edit(view=self)
        except Exception:
            pass

    async def on_error(self, interaction: discord.Interaction, error: Exception, item) -> None:
        logger.exception("[MyRegsActionView] handler error", exc_info=error)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "⚠️ Something went wrong. Please try again.", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "⚠️ Something went wrong. Please try again.", ephemeral=True
                )
        except Exception:
            pass

    @discord.ui.button(label="Look up Governor ID", style=discord.ButtonStyle.primary, emoji="🔎")
    async def btn_lookup(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ This menu isn’t for you.", ephemeral=True)
            return
        # IMPORTANT: do NOT defer here; open the modal as the first response
        try:
            await interaction.response.send_modal(GovNameModal(author_id=self.author_id))
        except Exception:
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

    @discord.ui.button(label="Modify Registration", style=discord.ButtonStyle.secondary, emoji="🛠️")
    async def btn_modify(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ This menu isn’t for you.", ephemeral=True)
            return
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            pass
        try:
            registry = await async_load_registry() or {}
            user_key_str = str(self.author_id)
            user_key_int = self.author_id
            accounts = (registry.get(user_key_str) or registry.get(user_key_int) or {}).get(
                "accounts", {}
            ) or {}
            if not accounts:
                await interaction.followup.send(
                    "You don’t have any accounts to modify. Use **Register New Account** instead.",
                    ephemeral=True,
                )
                return
            await interaction.followup.send(
                "Select which registered account you want to modify:",
                view=ModifyStartView(author_id=self.author_id, accounts=accounts),
                ephemeral=True,
            )
        except Exception as e:
            logger.exception("[MyRegsActionView] btn_modify failed")
            try:
                await interaction.followup.send(
                    f"⚠️ Failed to open modify flow: `{type(e).__name__}: {e}`", ephemeral=True
                )
            except Exception:
                pass

    @discord.ui.button(label="Register New Account", style=discord.ButtonStyle.success, emoji="➕")
    async def btn_register(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ This menu isn’t for you.", ephemeral=True)
            return
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            pass
        try:
            registry = await async_load_registry() or {}
            user_key_str = str(self.author_id)
            user_key_int = self.author_id
            accounts = (registry.get(user_key_str) or registry.get(user_key_int) or {}).get(
                "accounts", {}
            ) or {}
            used_slots = set(accounts.keys())
            free_slots = [slot for slot in ACCOUNT_ORDER if slot not in used_slots]
            if not free_slots:
                await interaction.followup.send(
                    "All account slots are registered already. Use **Modify Registration** to change one.",
                    ephemeral=True,
                )
                return
            await interaction.followup.send(
                "Pick an account slot to register:",
                view=RegisterStartView(author_id=self.author_id, free_slots=free_slots),
                ephemeral=True,
            )
        except Exception as e:
            logger.exception("[MyRegsActionView] btn_register failed")
            try:
                await interaction.followup.send(
                    f"⚠️ Failed to open registration flow: `{type(e).__name__}: {e}`", ephemeral=True
                )
            except Exception:
                pass


class GovNameModal(discord.ui.Modal):
    def __init__(self, author_id: int):
        super().__init__(title="Look up Governor ID")
        self.author_id = author_id
        self.add_item(
            discord.ui.InputText(label="Governor Name", placeholder="Type your governor name")
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ You can't use someone else's modal.", ephemeral=True
            )
            return

        governorname = (self.children[0].value or "").strip()
        if not governorname:
            await interaction.response.send_message("Please enter a governor name.", ephemeral=True)
            return

        # Ack first to avoid timeouts on fuzzy lookups
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        try:
            # If lookup_governor_id is async, this is perfect.
            # If it's CPU/IO bound sync, wrap it:
            # result = await asyncio.to_thread(lookup_governor_id, governorname)
            result = await lookup_governor_id(governorname)
        except Exception as e:
            await interaction.followup.send(
                f"❌ Lookup failed: `{type(e).__name__}: {e}`", ephemeral=True
            )
            return

        if result["status"] == "found":
            embed = discord.Embed(
                title="🆔 Governor ID Lookup",
                description=(
                    f"**Governor Name:** {result['data']['GovernorName']}\n"
                    f"**Governor ID:** `{result['data']['GovernorID']}`"
                ),
                color=discord.Color.green(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

        elif result["status"] == "fuzzy_matches":
            embed = discord.Embed(
                title="🔍 Governor Name Search Results",
                description="Pick a governor from the dropdown below.",
                color=discord.Color.blue(),
            )
            for entry in result["matches"]:
                embed.add_field(
                    name=entry["GovernorName"],
                    value=f"`Governor ID: {entry['GovernorID']}`",
                    inline=False,
                )
            view = (
                _TargetLookupView_factory(result["matches"], interaction.user.id)
                if _TargetLookupView_factory
                else None
            )
            if view:
                await view.send_followup(interaction, embed)  # ephemeral follow-up
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(
                result.get("message", "No results found."), ephemeral=True
            )


class ModifyStartView(discord.ui.View):
    def __init__(self, *, author_id: int, accounts: dict, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        options = []
        for slot in ACCOUNT_ORDER:
            if slot in accounts:
                info = accounts.get(slot) or {}
                gid = str(info.get("GovernorID", "")).strip()
                gname = str(info.get("GovernorName", "")).strip()
                label = f"{slot} — {gname} ({gid})" if (gname or gid) else f"{slot}"
                options.append(discord.SelectOption(label=label[:100], value=slot))
        select = discord.ui.Select(
            placeholder="Choose an account to modify",
            options=options[:25],
            min_values=1,
            max_values=1,
        )

        async def on_select(interaction: discord.Interaction):
            if interaction.user.id != self.author_id:
                await interaction.response.send_message(
                    "❌ This menu isn't for you.", ephemeral=True
                )
                return
            await interaction.response.send_modal(
                EnterGovernorIDModal(
                    author_id=self.author_id, mode="modify", account_type=select.values[0]
                )
            )

        select.callback = on_select
        self.add_item(select)

    async def on_timeout(self):
        for c in self.children:
            c.disabled = True

    async def on_error(self, interaction: discord.Interaction, error: Exception, item) -> None:
        logger.exception("[ModifyStartView] handler error", exc_info=error)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "⚠️ Something went wrong. Please try again.", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "⚠️ Something went wrong. Please try again.", ephemeral=True
                )
        except Exception:
            pass


class RegisterStartView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        free_slots: list,
        timeout: float = 180,
        prefill_id: str | None = None,
    ):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.prefill_id = prefill_id
        options = [discord.SelectOption(label=slot, value=slot) for slot in free_slots[:25]]
        select = discord.ui.Select(
            placeholder="Choose a slot to register", options=options, min_values=1, max_values=1
        )

        async def on_select(interaction: discord.Interaction):
            if interaction.user.id != self.author_id:
                await interaction.response.send_message(
                    "❌ This menu isn't for you.", ephemeral=True
                )
                return
            await interaction.response.send_modal(
                EnterGovernorIDModal(
                    author_id=self.author_id,
                    mode="register",
                    account_type=select.values[0],
                    prefill_id=self.prefill_id,
                )
            )

        select.callback = on_select
        self.add_item(select)

    async def on_timeout(self):
        for c in self.children:
            c.disabled = True

    async def on_error(self, interaction: discord.Interaction, error: Exception, item) -> None:
        logger.exception("[RegisterStartView] handler error", exc_info=error)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "⚠️ Something went wrong. Please try again.", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "⚠️ Something went wrong. Please try again.", ephemeral=True
                )
        except Exception:
            pass


class EnterGovernorIDModal(discord.ui.Modal):
    def __init__(
        self, *, author_id: int, mode: str, account_type: str, prefill_id: str | None = None
    ):
        title = "Modify Registration" if mode == "modify" else "Register New Account"
        super().__init__(title=title)
        self.author_id = author_id
        self.mode = mode
        self.account_type = account_type
        placeholder = (
            "Enter new Governor ID, or type REMOVE"
            if mode == "modify"
            else "Enter Governor ID to register"
        )
        self.add_item(
            discord.ui.InputText(
                label="Governor ID", placeholder=placeholder, value=(prefill_id or "")
            )
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ You can't use someone else's modal.", ephemeral=True
            )
            return

        governor_id = (self.children[0].value or "").strip()

        # MODIFY => REMOVE shortcut; respond fast
        if self.mode == "modify" and governor_id.upper() == "REMOVE":
            view = ConfirmRemoveView(interaction.user, self.account_type)
            await interaction.response.send_message(
                f"⚠️ Are you sure you want to **remove** `{self.account_type}` from your registration?",
                view=view,
                ephemeral=True,
            )
            return

        # Ack early so we’re safe against 3s timeout
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        if not governor_id.isdigit():
            await interaction.followup.send(
                "❌ Please enter a **numeric** Governor ID (or type `REMOVE` to delete when modifying).",
                ephemeral=True,
            )
            return

        try:
            registry = await async_load_registry() or {}
        except Exception as e:
            await interaction.followup.send(
                f"❌ Could not load registry: `{type(e).__name__}: {e}`", ephemeral=True
            )
            return

        all_rows = (_name_cache or {}).get("rows", []) if isinstance(_name_cache, dict) else []
        matched_row = next(
            (r for r in all_rows if str(r.get("GovernorID", "")).strip() == governor_id), None
        )
        if not matched_row:
            await interaction.followup.send(
                f"❌ Governor ID `{governor_id}` not found in the database. Try **Look up Governor ID** first.",
                ephemeral=True,
            )
            return

        # Prevent duplicates across other users
        for uid, data in registry.items():
            if self.mode == "modify" and str(uid) == str(self.author_id):
                continue
            for acc_type, details in (data.get("accounts") or {}).items():
                if str(details.get("GovernorID", "")).strip() == governor_id:
                    existing_user = data.get("discord_name", f"<@{uid}>")
                    await interaction.followup.send(
                        f"❌ This Governor ID `{governor_id}` is already registered to **{existing_user}** ({acc_type}).",
                        ephemeral=True,
                    )
                    return

        gov_name = matched_row.get("GovernorName", "Unknown")
        if self.mode == "modify":
            view = ModifyGovernorView(interaction.user, self.account_type, governor_id, gov_name)
            await interaction.followup.send(
                f"⚙️ Update `{self.account_type}` to **{gov_name}** (ID: `{governor_id}`)?",
                view=view,
                ephemeral=True,
            )
        else:
            view = RegisterGovernorView(interaction.user, self.account_type, governor_id, gov_name)
            await interaction.followup.send(
                f"⚙️ Register `{self.account_type}` as **{gov_name}** (ID: `{governor_id}`)?",
                view=view,
                ephemeral=True,
            )


# ---------- Select UI for fuzzy matches ----------
class GovernorSelect(discord.ui.Select):
    def __init__(self, matches: list[tuple[str, int]], *, author_id: int | None = None):
        self.author_id = author_id
        options = [
            discord.SelectOption(label=name, description=str(gid), value=str(gid))
            for name, gid in matches[:25]
        ]
        super().__init__(
            placeholder="Multiple matches — pick one", min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        if self.author_id is not None and interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Only the requester can use this menu.", ephemeral=True
            )
            return

        gid = int(self.values[0])

        # Defer immediately; sending a profile can be slow
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        try:
            await send_profile_to_channel(interaction, gid, interaction.channel)
        except Exception as e:
            logger.exception("[GovernorSelect] send_profile_to_channel failed")
            try:
                await interaction.followup.send(
                    f"⚠️ Failed to send profile: `{type(e).__name__}: {e}`", ephemeral=True
                )
            except Exception:
                pass
            return

        # Confirmation
        text = f"Sent profile for **{self.values[0]}**."
        try:
            await interaction.followup.send(text, ephemeral=True)
        except Exception:
            try:
                await interaction.edit_original_response(content=text, view=None)
            except Exception:
                try:
                    await interaction.message.edit(content=text, view=None)
                except Exception:
                    pass


class GovernorSelectView(discord.ui.View):
    def __init__(
        self, matches: list[tuple[str, int]], *, author_id: int | None = None, timeout: int = 60
    ):
        super().__init__(timeout=timeout)
        self.add_item(GovernorSelect(matches, author_id=author_id))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

    async def on_error(self, interaction: discord.Interaction, error: Exception, item) -> None:
        logger.exception("[GovernorSelectView] handler error", exc_info=error)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "⚠️ Something went wrong. Please try again.", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "⚠️ Something went wrong. Please try again.", ephemeral=True
                )
        except Exception:
            pass


class _LocationSelect(discord.ui.Select):
    def __init__(
        self, matches: list[tuple[str, int]], *, ephemeral: bool, author_id: int | None = None
    ):
        self._ephemeral = ephemeral
        self._author_id = author_id
        options = [
            discord.SelectOption(label=name, description=str(gid), value=str(gid))
            for name, gid in matches[:25]
        ]
        super().__init__(
            placeholder="Multiple matches — pick one", min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        # Optional: restrict to invoker
        if self._author_id is not None and interaction.user.id != self._author_id:
            await interaction.response.send_message(
                "❌ Only the requester can use this menu.", ephemeral=True
            )
            return

        from profile_cache import get_profile_cached, warm_cache

        gid = int(self.values[0])
        warm_cache()
        p = get_profile_cached(gid)
        if not p:
            await interaction.response.send_message(
                f"❌ GovernorID `{gid}` not found.", ephemeral=True
            )
            return

        x = p.get("X")
        y = p.get("Y")
        updated = p.get("LocationUpdated")
        embed = discord.Embed(
            title="📍 Player Location",
            description=f"**{p.get('GovernorName','Unknown')}** (`{gid}`)",
            color=0x5865F2,
        )
        embed.add_field(
            name="Coordinates",
            value=f"X **{x if x is not None else '—'}** • Y **{y if y is not None else '—'}**",
            inline=False,
        )
        if updated:
            embed.set_footer(text=f"Last updated: {updated}")

        try:
            if self._ephemeral:
                # Keep result private by reusing the component message
                await interaction.response.edit_message(embed=embed, view=None)
            else:
                # Post publicly, then replace the selector with a confirmation
                await interaction.channel.send(embed=embed)
                await interaction.response.edit_message(
                    content=f"✅ Posted location for `{gid}`.", view=None
                )
        except discord.InteractionResponded:
            # As a fallback try editing the original response
            try:
                await interaction.edit_original_response(embed=embed, view=None)
            except Exception:
                pass


class LocationSelectView(discord.ui.View):
    def __init__(
        self,
        matches: list[tuple[str, int]],
        *,
        ephemeral: bool,
        author_id: int | None = None,
        timeout: int = 60,
    ):
        super().__init__(timeout=timeout)
        self.add_item(_LocationSelect(matches, ephemeral=ephemeral, author_id=author_id))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        # best-effort; we don't hold a message reference here


class OpenFullSizeView(discord.ui.View):
    def __init__(self, url: str, *, label: str = "Open full size"):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.link,
                url=url,
            )
        )


class ProfileLinksView(discord.ui.View):
    def __init__(self, card_url: str | None = None):
        super().__init__(timeout=None)
        if card_url:
            self.add_item(
                discord.ui.Button(
                    style=discord.ButtonStyle.link, label="Open full card", url=card_url
                )
            )


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


class MyKVKStatsSelectView(discord.ui.View):
    """
    Ephemeral selector for /mykvkstats:
    - Dropdown of user's registered accounts (ordered by ACCOUNT_ORDER)
    - Buttons: Lookup Governor ID, Register New Account (reuses your existing flows)
    - On select -> posts PUBLIC stats embed to the channel
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

        gid = normalize_governor_id(self.select.values[0])
        row = load_stat_row(gid)
        if not row:
            await interaction.response.send_message(
                f"Couldn’t find stats for GovernorID `{gid}`.", ephemeral=True
            )
            return

        embed, file = build_stats_embed(row, interaction.user)

        # 1) Post PUBLIC stats to the channel
        await self.ctx.channel.send(embed=embed, file=file)

        # 2) Quietly close the ephemeral selector (no extra message)
        for c in self.children:
            c.disabled = True

        try:
            # Edit the original ephemeral message in-place (no new follow-up)
            await interaction.response.edit_message(content=" ", view=self)
        except discord.InteractionResponded:
            # Fallback: edit the command's original response
            try:
                await self.ctx.edit_original_response(content=" ", view=self)
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


class RefreshLocationView(discord.ui.View):
    def __init__(self, *, target_id: int, ephemeral: bool):
        super().__init__(timeout=None)
        self.target_id = target_id
        self.ephemeral = ephemeral

        # Build the button manually (unique custom_id just in case)
        self.btn = discord.ui.Button(
            label="🔄 Refresh locations",
            style=discord.ButtonStyle.primary,
            custom_id="kvk:refresh_locations",
        )
        self.btn.callback = self._on_refresh  # bind callback
        self.add_item(self.btn)

    async def _on_refresh(self, interaction: discord.Interaction):
        # Permission gate mirrors /player_location
        member = interaction.guild.get_member(interaction.user.id) if interaction.guild else None
        from Decoraters import _has_leadership_role, _is_admin

        if not (_is_admin(interaction.user) or _has_leadership_role(member)):
            await interaction.response.send_message("❌ Admin/Leadership only.", ephemeral=True)
            return

        # Prevent concurrent runs
        global _last_location_refresh_utc
        if _location_refresh_lock.locked():
            await interaction.response.send_message(
                "⏳ A refresh is already running. Please wait for it to finish.", ephemeral=True
            )
            return

        # 1 per hour rate limit (soft, with remaining time)
        now = datetime.now(UTC)
        if _last_location_refresh_utc:
            delta = (now - _last_location_refresh_utc).total_seconds()
            remain = 3600 - int(delta)
            if remain > 0:
                mins, secs = divmod(remain, 60)
                await interaction.response.send_message(
                    f"🕒 Location refresh is limited to **once per hour**. Try again in **{mins}m {secs}s**.",
                    ephemeral=True,
                )
                return

        await interaction.response.defer(ephemeral=True)

        # Start guarded refresh
        async with _location_refresh_lock:
            _last_location_refresh_utc = now
            _location_refresh_event.clear()

            ok, err = await _send_find_all_to_location_channel(bot, interaction=interaction)
            if not ok:
                await interaction.followup.send(
                    f"❌ Couldn’t trigger refresh: `{err}`", ephemeral=True
                )
                return

            await interaction.followup.send(
                "📡 Refresh requested. This usually takes ~5–15 minutes. I’ll update this when it’s done.",
                ephemeral=True,
            )

            # Wait up to 30 minutes for the CSV import hook to signal completion
            try:
                await asyncio.wait_for(_location_refresh_event.wait(), timeout=30 * 60)
            except TimeoutError:
                try:
                    from bot_config import ADMIN_USER_ID

                    if ADMIN_USER_ID:
                        admin = await bot.fetch_user(ADMIN_USER_ID)
                        await admin.send(
                            "⚠️ Location refresh did not complete within 30 minutes. Please check the scanner/import."
                        )
                except Exception:
                    pass
                await interaction.followup.send(
                    "⚠️ No update received after 30 minutes. Please try again later.", ephemeral=True
                )
                return

            # Success: warm cache and update the embed with fresh XY
            try:
                from profile_cache import get_profile_cached, warm_cache

                warm_cache()
                p = get_profile_cached(self.target_id)
                if not p:
                    await interaction.followup.send(
                        f"❌ GovernorID `{self.target_id}` not found after refresh.", ephemeral=True
                    )
                    return

                x, y, updated = p.get("X"), p.get("Y"), p.get("LocationUpdated")
                embed = discord.Embed(
                    title="📍 Player Location (refreshed)",
                    description=f"**{p.get('GovernorName','Unknown')}** (`{self.target_id}`)",
                    color=0x2ECC71,
                )
                embed.add_field(
                    name="Coordinates",
                    value=f"X **{x if x is not None else '—'}** • Y **{y if y is not None else '—'}**",
                    inline=False,
                )
                if updated:
                    embed.set_footer(
                        text=f"Last updated: {updated} • Tip: Use the button below if it changes again"
                    )

                try:
                    await interaction.message.edit(embed=embed, view=self)
                except Exception:
                    await interaction.followup.send(embed=embed, ephemeral=self.ephemeral)

            except Exception as e:
                await interaction.followup.send(
                    f"❌ Failed to update location after refresh: `{type(e).__name__}: {e}`",
                    ephemeral=True,
                )


class KVKRankingView(discord.ui.View):
    def __init__(
        self, cache: dict, metric: str = "kills", limit: int = 10, *, timeout: float = 120.0
    ):
        super().__init__(timeout=timeout)
        self.cache = cache
        self.metric = (metric or "kills").lower()
        self.limit = limit
        self.message: discord.Message | None = None

        self.rows = [r for k, r in cache.items() if k != "_meta"]
        self.meta = cache.get("_meta", {})

        # Metric dropdown
        self.metric_select = discord.ui.Select(
            placeholder="Choose metric…",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Kills (T4+T5)", value="kills", default=(self.metric == "kills")
                ),
                discord.SelectOption(
                    label="Deads", value="deads", default=(self.metric == "deads")
                ),
                discord.SelectOption(label="DKP", value="dkp", default=(self.metric == "dkp")),
            ],
        )
        self.metric_select.callback = self.on_metric_change
        self.add_item(self.metric_select)

        # Limit buttons
        for n in (10, 25, 50, 100):
            btn = discord.ui.Button(
                label=f"Top {n}",
                style=(
                    discord.ButtonStyle.primary
                    if n == self.limit
                    else discord.ButtonStyle.secondary
                ),
                custom_id=f"kvk_top_{n}",
            )
            btn.callback = self._make_limit_handler(n)
            self.add_item(btn)

    async def _safe_edit(self, interaction: discord.Interaction, *, embed: discord.Embed):
        """Safely edit the message for a component interaction.

        Strategy:
        1) If we haven't responded yet, defer immediately (keeps token alive).
        2) Prefer editing the original response.
        3) Fall back to followup.edit_message(message_id=...) if needed.
        4) Final fallback: edit the cached self.message directly (if available).
        """
        # 1) Keep the token valid
        try:
            if not interaction.response.is_done():
                # For component interactions, defer quickly to avoid 10062
                await interaction.response.defer()
        except Exception:
            pass  # if already responded or race, continue

        # 2) Try editing the original app response
        try:
            await interaction.edit_original_response(embed=embed, view=self)
            return
        except Exception:
            pass

        # 3) Try editing via followup + known message id
        try:
            if interaction.message:
                await interaction.followup.edit_message(
                    interaction.message.id, embed=embed, view=self
                )
                return
        except Exception:
            pass

        # 4) Last resort: edit the stored message reference (non-ephemeral only)
        if self.message:
            try:
                await self.message.edit(embed=embed, view=self)
            except Exception:
                pass

    async def _redraw(self, interaction: discord.Interaction):
        # update selected state on UI items
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.label.startswith("Top "):
                item.style = (
                    discord.ButtonStyle.primary
                    if item.label == f"Top {self.limit}"
                    else discord.ButtonStyle.secondary
                )
            if isinstance(item, discord.ui.Select):
                for opt in item.options:
                    opt.default = opt.value == self.metric

        embed = build_kvkrankings_embed(self.rows, self.metric, self.limit)
        if not embed.footer or not embed.footer.text:
            last_ref = self.meta.get("generated_at") or "unknown"
            embed.set_footer(text=f"Last refreshed: {last_ref}")

        await self._safe_edit(interaction, embed=embed)

    async def on_metric_change(self, interaction: discord.Interaction):
        self.metric = self.metric_select.values[0]
        await self._redraw(interaction)

    def _make_limit_handler(self, n: int):
        async def _handler(interaction: discord.Interaction):
            self.limit = n
            await self._redraw(interaction)

        return _handler

    async def on_timeout(self):
        # disable UI gracefully after timeout
        for child in self.children:
            child.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            pass


def register_commands(bot_instance):
    global bot
    bot = bot_instance

    logger.info("[COMMANDS] Registering commands...")
    # Register global command error handler
    bot.add_listener(_global_cmd_error_handler, "on_application_command_error")

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

    class NextFightView(LocalTimeToggleView):
        def __init__(self, initial_limit: int = 1, prefix: str = "nextfight"):
            # Preload up to 3 for local-time toggle and button availability
            self.limit = max(1, int(initial_limit))
            self._all3 = get_next_fights(3) or []
            self.fights = self._all3[: self.limit]
            super().__init__(
                events=self.fights, prefix=prefix, timeout=None
            )  # sets self.events in parent
            self.message: discord.Message | None = None  # set by command after send
            self._apply_button_state()

        # --- helpers -------------------------------------------------------------

        def _btns(self):
            one = next(
                (
                    c
                    for c in self.children
                    if isinstance(c, discord.ui.Button)
                    and (c.label or "").lower().startswith("next fight only")
                ),
                None,
            )
            three = next(
                (
                    c
                    for c in self.children
                    if isinstance(c, discord.ui.Button)
                    and "next" in (c.label or "").lower()
                    and "fight" in (c.label or "").lower()
                    and "only" not in (c.label or "").lower()
                ),
                None,
            )
            return one, three

        def _apply_button_state(self):
            """Update button disabled/style/label based on availability + selected limit."""
            one, three = self._btns()
            available = len(self._all3)

            # Style the 'selected' choice as primary, the other as secondary
            if one:
                one.style = (
                    discord.ButtonStyle.primary
                    if self.limit == 1
                    else discord.ButtonStyle.secondary
                )

            if three:
                n = min(3, available)
                # Rename to reflect how many we can actually show
                three.label = f"Next {n} Fight{'s' if n != 1 else ''}"
                # Disable if showing multiple isn't possible
                three.disabled = n <= 1
                three.style = (
                    discord.ButtonStyle.primary if self.limit > 1 else discord.ButtonStyle.secondary
                )

        async def _refresh(self, interaction: discord.Interaction):
            """Ack + update message and view; safe even if already responded."""
            self._apply_button_state()
            try:
                await interaction.response.edit_message(
                    embed=format_fight_embed(self.fights), view=self
                )
            except discord.InteractionResponded:
                # Fallback: edit the message directly if response was already used
                try:
                    if self.message:
                        await self.message.edit(embed=format_fight_embed(self.fights), view=self)
                    else:
                        # As a last resort, try original_response (if this was the original interaction)
                        msg = await interaction.original_response()
                        await msg.edit(embed=format_fight_embed(self.fights), view=self)
                except Exception:
                    pass

        async def _recompute(self, desired_limit: int, interaction: discord.Interaction):
            """Recompute list given desired limit, keep LocalTimeToggleView in sync, and refresh."""
            # If user clicked the currently selected option, just ack quietly
            if (desired_limit == 1 and self.limit == 1) or (desired_limit > 1 and self.limit > 1):
                await interaction.response.defer()  # silent ack; no edit
                return

            # Refresh source list (in case time advanced), then slice
            self._all3 = get_next_fights(3) or []
            available = len(self._all3)
            self.limit = (
                1 if desired_limit == 1 else min(3, max(2, available))
            )  # if asking for "3", clamp to available>=2

            self.fights = self._all3[: self.limit]
            self.events = self.fights  # keep LocalTimeToggleView in sync

            if not self.fights:
                # Nothing left—close the UI
                try:
                    await interaction.response.edit_message(
                        content="Fighting finished just chill now!", embed=None, view=None
                    )
                except discord.InteractionResponded:
                    if self.message:
                        await self.message.edit(
                            content="Fighting finished just chill now!", embed=None, view=None
                        )
                return

            await self._refresh(interaction)

        # --- buttons -------------------------------------------------------------

        @discord.ui.button(label="Next Fight Only", style=discord.ButtonStyle.primary)
        async def show_one(self, button: discord.ui.Button, interaction: discord.Interaction):
            await self._recompute(desired_limit=1, interaction=interaction)

        @discord.ui.button(label="Next 3 Fights", style=discord.ButtonStyle.secondary)
        async def show_three(self, button: discord.ui.Button, interaction: discord.Interaction):
            await self._recompute(desired_limit=3, interaction=interaction)

    class NextEventView(LocalTimeToggleView):
        def __init__(
            self, initial_limit: int = 1, prefix: str = "nextevent", preloaded: list | None = None
        ):
            self.limit = max(1, int(initial_limit))
            # Preload up to 5 once
            self._all5 = (preloaded or get_next_events(limit=5)) or []
            self.events = self._all5[: self.limit]
            super().__init__(
                events=self.events, prefix=prefix, timeout=None
            )  # sets self.events in parent
            self.message: discord.Message | None = None  # set by the command after send
            self._apply_button_state()

        # ---- helpers ------------------------------------------------------------

        def _btns(self):
            one = next(
                (
                    c
                    for c in self.children
                    if isinstance(c, discord.ui.Button)
                    and (c.label or "").lower().startswith("next event only")
                ),
                None,
            )
            five = next(
                (
                    c
                    for c in self.children
                    if isinstance(c, discord.ui.Button)
                    and "next" in (c.label or "").lower()
                    and "event" in (c.label or "").lower()
                    and "only" not in (c.label or "").lower()
                ),
                None,
            )
            return one, five

        def _apply_button_state(self):
            one, five = self._btns()
            available = len(self._all5)

            if one:
                one.style = (
                    discord.ButtonStyle.primary
                    if self.limit == 1
                    else discord.ButtonStyle.secondary
                )

            if five:
                n = min(5, available)
                five.label = f"Next {n} Event{'s' if n != 1 else ''}"
                five.disabled = n <= 1
                five.style = (
                    discord.ButtonStyle.primary if self.limit > 1 else discord.ButtonStyle.secondary
                )

        async def _refresh(self, interaction: discord.Interaction):
            """Ack + update the message; safe even if already responded."""
            self._apply_button_state()
            embed = format_event_embed(self.events)
            try:
                await interaction.response.edit_message(embed=embed, view=self)
            except discord.InteractionResponded:
                try:
                    if self.message:
                        await self.message.edit(embed=embed, view=self)
                    else:
                        msg = await interaction.original_response()
                        await msg.edit(embed=embed, view=self)
                except Exception:
                    pass

        async def update_embed(self, interaction: discord.Interaction, *, desired_limit: int):
            """Recompute list given desired limit and refresh."""
            # No-op? quietly ack to avoid red 'interaction failed'
            if (desired_limit == 1 and self.limit == 1) or (desired_limit > 1 and self.limit > 1):
                await interaction.response.defer()
                return

            # Refresh the source list (time may have advanced)
            self._all5 = get_next_events(limit=5) or self._all5
            available = len(self._all5)

            self.limit = 1 if desired_limit == 1 else min(5, max(2, available))
            self.events = self._all5[: self.limit]  # keep LocalTimeToggleView state aligned

            if not self.events:
                try:
                    await interaction.response.edit_message(
                        content="No upcoming events found.", embed=None, view=None
                    )
                except discord.InteractionResponded:
                    if self.message:
                        await self.message.edit(
                            content="No upcoming events found.", embed=None, view=None
                        )
                return

            logger.info(f"[COMMAND] /nextevent – showing {len(self.events)} event(s)")
            await self._refresh(interaction)

        # ---- buttons ------------------------------------------------------------

        @discord.ui.button(label="Next Event Only", style=discord.ButtonStyle.primary)
        async def show_one(self, button: discord.ui.Button, interaction: discord.Interaction):
            await self.update_embed(interaction, desired_limit=1)

        @discord.ui.button(label="Next 5 Events", style=discord.ButtonStyle.secondary)
        async def show_five(self, button: discord.ui.Button, interaction: discord.Interaction):
            await self.update_embed(interaction, desired_limit=5)

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
    @versioned("v1.03")
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

    class ConfirmRestartView(View):
        def __init__(self, ctx, timeout: int = 30):
            super().__init__(timeout=timeout)
            self.ctx = ctx
            self.confirmed = asyncio.Event()
            self.cancelled = False
            self.message: discord.Message | None = None

        def _disable_all(self):
            for c in self.children:
                c.disabled = True

        async def _try_disable_ui(self):
            try:
                if self.message is None:
                    # fetch the ephemeral original if not cached yet
                    self.message = await self.ctx.interaction.original_response()
                self._disable_all()
                await self.message.edit(view=self)
            except Exception:
                pass

        @discord.ui.button(label="✅ Confirm Restart", style=discord.ButtonStyle.danger)
        async def confirm(self, _button: discord.ui.Button, interaction: discord.Interaction):
            if interaction.user.id != ADMIN_USER_ID:
                await interaction.response.send_message(
                    "❌ Only the admin can confirm this action.", ephemeral=True
                )
                return

            embed_user = Embed(
                title="🔄 Bot Restart Initiated",
                description="Attempting to restart the bot now. If it doesn't come back online, check your host.",
                color=0xF39C12,
            )
            embed_user.set_footer(text="Restart requested by admin")
            embed_user.timestamp = datetime.utcnow()
            await interaction.response.send_message(embed=embed_user, ephemeral=True)

            try:
                notify_channel = bot.get_channel(NOTIFY_CHANNEL_ID)
                if notify_channel:
                    embed_broadcast = Embed(
                        title="🛠️ Bot Restart Requested",
                        description=f"Admin <@{interaction.user.id}> initiated a restart via slash command.",
                        color=0xF39C12,
                    )
                    embed_broadcast.timestamp = datetime.utcnow()
                    await notify_channel.send(embed=embed_broadcast)
            except Exception as e:
                logger.exception(f"[RESTART AUDIT] Failed to broadcast restart: {e}")

            await self._try_disable_ui()
            self.confirmed.set()
            self.stop()

        @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
        async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
            if interaction.user.id != ADMIN_USER_ID:
                await interaction.response.send_message(
                    "❌ Only the admin can cancel this action.", ephemeral=True
                )
                return
            await interaction.response.send_message("❎ Bot restart cancelled.", ephemeral=True)
            self.cancelled = True
            await self._try_disable_ui()
            self.confirmed.set()
            self.stop()

    @bot.slash_command(
        name="restart_bot", description="Forcefully restart the bot", guild_ids=[GUILD_ID]
    )
    @versioned("v1.06")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def restart_bot_command(ctx):
        view = ConfirmRestartView(ctx)
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
        async with _op_locks["resync"]:
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
    @versioned("v1.02")
    @safe_command
    @is_admin_and_notify_channel()
    @ext_commands.has_permissions(administrator=True)
    @track_usage()
    async def import_proc_config(ctx):
        await safe_defer(ctx, ephemeral=True)
        start_ts = datetime.utcnow()

        # Let the caller see progress
        try:
            await ctx.interaction.edit_original_response(content="⏳ Starting ProcConfig import…")
        except Exception:
            pass

        try:
            # ⬇️ move the blocking work off the event loop
            success = await asyncio.to_thread(run_proc_config_import)
        except Exception as e:
            logger.exception("[COMMAND] /import_proc_config crashed")
            await ctx.interaction.edit_original_response(
                content=f"💥 Import failed unexpectedly: `{type(e).__name__}: {e}`"
            )
            return

        dur = (datetime.utcnow() - start_ts).total_seconds()
        if success:
            logger.info("[COMMAND] /import_proc_config completed successfully in %.2fs", dur)
            await ctx.interaction.edit_original_response(
                content=f"✅ ProcConfig import completed successfully in **{dur:.1f}s**."
            )
        else:
            logger.error("[COMMAND] /import_proc_config reported failure after %.2fs", dur)
            await ctx.interaction.edit_original_response(
                content=(
                    "❌ ProcConfig import encountered errors. "
                    f"Duration **{dur:.1f}s**. Please check the logs for details."
                )
            )

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
    @versioned("v1.02")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def test_embed_command(ctx):

        await safe_defer(ctx, ephemeral=True)
        start_ts = datetime.now(UTC)

        sql_conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};"
        )

        # Where the embed will land (for the admin’s confirmation)
        notify_channel = bot.get_channel(NOTIFY_CHANNEL_ID)

        try:
            # If this hits SQL synchronously, push it off the event loop
            is_kvk = await asyncio.to_thread(is_currently_kvk, SERVER, DATABASE, USERNAME, PASSWORD)

            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
            # Send the test embed (helper handles building/posting)
            await send_stats_update_embed(bot, timestamp, is_kvk, sql_conn_str, is_test=True)

            dur = (datetime.now(UTC) - start_ts).total_seconds()
            where = notify_channel.mention if notify_channel else f"<#{NOTIFY_CHANNEL_ID}>"
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
    @versioned("v2.07")
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

        # 1) Manual ID path
        if governorid and governorid.strip().isdigit():
            await run_target_lookup(ctx.interaction, governorid.strip(), ephemeral=only_me)
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

        options = _build_unique_gov_options(accounts)

        if options:
            if len(options) == 1:
                # Auto-open targets for the only unique GovernorID
                only_gid = options[0].value
                await run_target_lookup(ctx.interaction, only_gid, ephemeral=only_me)
                return

            view = _KVKTargetsView(ctx, options, show_register_btn=True, ephemeral=only_me)
            await ctx.followup.send(
                "Select an account to view its KVK targets:",
                view=view,
                ephemeral=only_me,
            )
        else:
            # (unchanged) show hint + buttons
            hint = (
                "You don’t have any linked governor accounts yet.\n"
                "• Use `/link_account` (Register new account), or\n"
                "• Re-run this command with the `governorid` option."
            )
            view = _KVKTargetsView(ctx, [], show_register_btn=True, ephemeral=only_me)
            await ctx.followup.send(hint, view=view, ephemeral=only_me)

    # ---------------- Reused wrappers from /my_registrations ----------------

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
            accounts = (user_block.get("accounts") or {}) if isinstance(user_block, dict) else {}

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

    # ---------------- UI components ----------------

    class _KVKTargetsView(discord.ui.View):
        """Account selector + action buttons (match /my_registrations minus Modify)."""

        def __init__(
            self,
            ctx: discord.ApplicationContext,
            options: list[discord.SelectOption],
            show_register_btn: bool,
            ephemeral: bool,
        ):
            super().__init__(timeout=300)  # 5 minutes
            self.ctx = ctx
            self.ephemeral = ephemeral

            if options:
                self.add_item(_KVKTargetsSelect(options, self))

            # Row 1 — mirror registrations UI: Lookup + Register New
            self.add_item(_LookupGovIDButton())
            if show_register_btn:
                self.add_item(_RegisterAccountButton())

            # Row 2 — utility
            self.add_item(_RefreshSelectorButton())

        async def on_timeout(self):
            # Disable stale controls
            for item in self.children:
                item.disabled = True
            # Post a fresh live selector so the user can continue without rerunning the command
            try:
                options = await _rebuild_options(self.ctx)
                new_view = _KVKTargetsView(
                    self.ctx, options, show_register_btn=True, ephemeral=self.ephemeral
                )
                content = (
                    "⌛ Selector expired. Click **Refresh** to reopen, or pick an account below:"
                )
                await self.ctx.followup.send(content, view=new_view, ephemeral=self.ephemeral)
            except Exception:
                pass

    class _KVKTargetsSelect(discord.ui.Select):
        def __init__(self, options: list[discord.SelectOption], parent: _KVKTargetsView):
            super().__init__(
                placeholder="Choose an account to view…",
                min_values=1,
                max_values=1,
                options=options,
            )
            self.parent = parent

        async def callback(self, interaction: discord.Interaction):
            gid = self.values[0]
            try:
                await run_target_lookup(interaction, gid, ephemeral=self.parent.ephemeral)
            finally:
                if not interaction.response.is_done():
                    try:
                        await interaction.response.defer()
                    except Exception:
                        pass
                self.parent.stop()

    class _LookupGovIDButton(discord.ui.Button):
        def __init__(self):
            # was: ButtonStyle.secondary
            super().__init__(
                label="Look up Governor ID", style=discord.ButtonStyle.primary, emoji="🔎"
            )

        async def callback(self, interaction: discord.Interaction):
            await kvk_open_governor_lookup(interaction)

    class _RegisterAccountButton(discord.ui.Button):
        def __init__(self):
            super().__init__(
                label="Register New Account", style=discord.ButtonStyle.success, emoji="🧾"
            )

        async def callback(self, interaction: discord.Interaction):
            await kvk_open_registration_flow(interaction)

    class _RefreshSelectorButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Refresh", style=discord.ButtonStyle.secondary, emoji="🔄")

        async def callback(self, interaction: discord.Interaction):
            try:
                options = await _rebuild_options(self.view.ctx)
                new_view = _KVKTargetsView(
                    self.view.ctx, options, show_register_btn=True, ephemeral=self.view.ephemeral
                )
                content = (
                    "Select an account to view its KVK targets:"
                    if options
                    else (
                        "No registered accounts found.\n"
                        "• Use `/link_account` (Register new account), or\n"
                        "• Provide `governorid` directly."
                    )
                )
                await interaction.response.edit_message(content=content, view=new_view)
            except Exception:
                logger.exception("[/mykvktargets] refresh failed")
                await interaction.response.send_message(
                    "Refresh failed. Try `/mykvktargets` again.", ephemeral=True
                )

    # Helper: rebuild options from registry (used by Refresh and timeout)
    async def _rebuild_options(ctx: discord.ApplicationContext) -> list[discord.SelectOption]:
        try:
            registry = await asyncio.to_thread(load_registry)
            user_block = registry.get(str(ctx.user.id)) or {}
            accounts = user_block.get("accounts") or {}
        except Exception:
            return []
        return _build_unique_gov_options(accounts)

    # ---------- Generic Account Picker (reusable across commands) ----------

    class _AccountPickerSelect(discord.ui.Select):
        """
        Generic account select that calls a supplied coroutine with the chosen GovernorID.
        """

        def __init__(self, options: list[discord.SelectOption], parent_view: AccountPickerView):
            super().__init__(
                placeholder="Choose an account…", min_values=1, max_values=1, options=options
            )
            self.parent_view = parent_view

        async def callback(self, interaction: discord.Interaction):
            gid = self.values[0]
            try:
                # Let the feature handler respond (edit or send). It MUST respond or raise.
                await self.parent_view.on_select_governor(
                    interaction, gid, self.parent_view.ephemeral
                )
                # If handler returned without responding, at least ack to avoid "interaction failed".
                if not interaction.response.is_done():
                    await interaction.response.defer()  # simple ack; no UI change
            except Exception as e:
                # Never fail silently—log + show a friendly error to the user
                logger.exception("[AccountPicker] on_select_governor failed: %s", e, exc_info=True)
                try:
                    if not interaction.response.is_done():
                        await interaction.response.send_message(
                            f"❌ Failed to open: `{type(e).__name__}: {e}`",
                            ephemeral=True,
                        )
                    else:
                        await interaction.followup.send(
                            f"❌ Failed to open: `{type(e).__name__}: {e}`",
                            ephemeral=True,
                        )
                except Exception:
                    # Last resort: swallow—Discord already shows a red banner
                    pass
            finally:
                self.parent_view.stop()

    class _RefreshAccountPickerButton(discord.ui.Button):
        """
        Refresh button that rebuilds options via _rebuild_options() and re-renders the same AccountPickerView.
        """

        def __init__(self):
            super().__init__(label="Refresh", style=discord.ButtonStyle.secondary, emoji="🔄")

        async def callback(self, interaction: discord.Interaction):
            view: AccountPickerView = self.view  # type: ignore
            try:
                options = await _rebuild_options(view.ctx)
                new_view = AccountPickerView(
                    ctx=view.ctx,
                    options=options,
                    on_select_governor=view.on_select_governor,
                    heading=view.heading,
                    show_register_btn=view.show_register_btn,
                    ephemeral=view.ephemeral,
                )
                content = (
                    view.heading
                    if options
                    else (
                        "No registered accounts found.\n"
                        "• Use `/link_account` (Register new account), or\n"
                        "• Provide the `governorid` option directly."
                    )
                )
                await interaction.response.edit_message(content=content, view=new_view)
            except Exception:
                logger.exception("[AccountPicker] refresh failed")
                await interaction.response.send_message(
                    "Refresh failed. Try the command again.", ephemeral=True
                )

    class AccountPickerView(discord.ui.View):
        """
        Generic 'pick an account' view with:
          - account dropdown (if options exist)
          - 'Look up Governor ID' button (reuses kvk_open_governor_lookup)
          - 'Register New Account' button (reuses kvk_open_registration_flow)
          - 'Refresh' button
        You pass in the coroutine to run when an account is chosen.

        on_select_governor signature:
            async def on_select_governor(interaction: discord.Interaction, governor_id: str, ephemeral: bool) -> None
        """

        def __init__(
            self,
            ctx: discord.ApplicationContext,
            options: list[discord.SelectOption],
            on_select_governor,  # async def (interaction, governor_id: str, ephemeral: bool)
            heading: str,
            show_register_btn: bool,
            ephemeral: bool,
        ):
            super().__init__(timeout=300)
            self.ctx = ctx
            self.on_select_governor = on_select_governor
            self.heading = heading
            self.show_register_btn = show_register_btn
            self.ephemeral = ephemeral

            if options:
                self.add_item(_AccountPickerSelect(options, self))

            # Reuse existing flows/buttons you already have
            self.add_item(_LookupGovIDButton())
            if show_register_btn:
                self.add_item(_RegisterAccountButton())
            self.add_item(_RefreshAccountPickerButton())

        async def on_timeout(self):
            for item in self.children:
                item.disabled = True
            try:
                options = await _rebuild_options(self.ctx)
                new_view = AccountPickerView(
                    ctx=self.ctx,
                    options=options,
                    on_select_governor=self.on_select_governor,
                    heading=self.heading,
                    show_register_btn=self.show_register_btn,
                    ephemeral=self.ephemeral,
                )
                content = (
                    "⌛ Selector expired. Click **Refresh** to reopen, or pick an account below:"
                )
                await self.ctx.followup.send(content, view=new_view, ephemeral=self.ephemeral)
            except Exception:
                pass

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
                save_view_tracker(
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
                logger.exception("[nextfight] save_view_tracker failed: %s", e)

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
                save_view_tracker(
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
                logger.exception("[nextevent] save_view_tracker failed: %s", e)

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

        # Make per-view custom_ids to avoid collisions
        EVENT_SELECT_ID = make_cid("sub:event", uid)
        REMINDER_SELECT_ID = make_cid("sub:remind", uid)
        CONFIRM_BUTTON_ID = make_cid("sub:confirm", uid)

        def option_desc(key: str) -> str:
            return {
                "ruins": "Ruins events",
                "altars": "Altar fights",
                "major": "Major timeline events",
                "fights": "All fights (altars + major FIGHTs)",
                "all": "Every event type",
            }.get(key, "")

        def _is_owner(interaction: discord.Interaction, expected_uid: int) -> bool:
            return interaction.user and interaction.user.id == expected_uid

        class DynamicEventSelect(discord.ui.Select):
            def __init__(self, selected=None):
                selected = selected or []
                options = [
                    discord.SelectOption(
                        label=typ,
                        value=typ,
                        description=option_desc(typ),
                        default=(typ in selected),
                    )
                    for typ in VALID_TYPES
                ]
                super().__init__(
                    placeholder="Select event types...",
                    min_values=0,  # allow none -> defaults
                    max_values=len(options),
                    options=options,
                    custom_id=EVENT_SELECT_ID,
                    row=0,
                )

            async def callback(self, interaction: discord.Interaction):
                if not _is_owner(interaction, uid):
                    await interaction.response.send_message(
                        "This selector isn't for you.", ephemeral=True
                    )
                    return
                view: SubscriptionView = self.view  # type: ignore
                selected = self.values
                view.selected_types = selected

                # Rebuild view with updated defaults (exclusivity enforced on confirm)
                view.clear_items()
                view.add_item(type(self)(selected))  # Event select (row 0)
                view.add_item(ReminderSelect(view.selected_reminders))  # (row 1)
                view.add_item(ConfirmButton())  # (row 2)
                await interaction.response.edit_message(view=view)

        class ReminderSelect(discord.ui.Select):
            def __init__(self, selected=None):
                selected = selected or []
                options = [
                    discord.SelectOption(
                        label=t,
                        value=t,
                        description=f"{t.upper()} reminder",
                        default=(t in selected),
                    )
                    for t in DEFAULT_REMINDER_TIMES
                ]
                super().__init__(
                    placeholder="Select reminder times...",
                    min_values=1,  # set to 0 if you want users to clear and fall back to defaults on confirm
                    max_values=len(options),
                    options=options,
                    custom_id=REMINDER_SELECT_ID,
                    row=1,
                )

            async def callback(self, interaction: discord.Interaction):
                if not _is_owner(interaction, uid):
                    await interaction.response.send_message(
                        "This selector isn't for you.", ephemeral=True
                    )
                    return
                self.view.selected_reminders = self.values  # type: ignore
                await interaction.response.defer()  # ack quietly

        class ConfirmButton(discord.ui.Button):
            def __init__(self):
                super().__init__(
                    label="✅ Confirm",
                    style=discord.ButtonStyle.success,
                    custom_id=CONFIRM_BUTTON_ID,
                    row=2,
                )
                self._clicked = False

            async def callback(self, interaction: discord.Interaction):
                if not _is_owner(interaction, uid):
                    await interaction.response.send_message(
                        "This button isn't for you.", ephemeral=True
                    )
                    return
                # Debounce double-clicks
                if self._clicked:
                    await interaction.response.defer()
                    return
                self._clicked = True
                view: SubscriptionView = self.view  # type: ignore
                await view.on_confirm(interaction)

        class SubscriptionView(discord.ui.View):
            def __init__(self, user, uid, username):
                super().__init__(timeout=180)
                self.user = user
                self.uid = uid
                self.username = username
                self.selected_types = []
                self.selected_reminders = []
                self.add_item(DynamicEventSelect())
                self.add_item(ReminderSelect())
                self.add_item(ConfirmButton())

            async def on_timeout(self):
                for c in self.children:
                    c.disabled = True
                try:
                    msg = await ctx.interaction.original_response()
                    await msg.edit(view=self)
                except Exception:
                    pass

            async def on_confirm(self, interaction: discord.Interaction):
                types = list(self.selected_types)
                times = list(self.selected_reminders)
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

                # Validate selections against allowed values
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

                # Enforce exclusivity
                if "all" in types:
                    types = ["all"]
                elif "fights" in types:
                    types = [t for t in types if t not in ("altars", "major")]

                # Persist
                try:
                    set_user_config(self.uid, self.username, types, times)
                except Exception as e:
                    logger.exception("[subscribe] set_user_config failed")
                    await interaction.response.send_message(
                        f"❌ Failed to save your subscription: `{type(e).__name__}: {e}`",
                        ephemeral=True,
                    )
                    return

                # Build DM confirmation
                embed = discord.Embed(
                    title="👋 Subscribed to Event Reminders",
                    description=f"Hi {self.user.mention}, you're now subscribed to event reminders!",
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

                # Try DM first
                try:
                    await self.user.send(embed=embed)
                except discord.Forbidden:
                    await interaction.response.send_message(
                        "⚠️ Could not send DM. Please enable DMs from this server and try again.",
                        ephemeral=True,
                    )
                    return

                # Disable UI and confirm in-place
                for c in self.children:
                    c.disabled = True
                await interaction.response.edit_message(
                    content="✅ Subscribed successfully! A confirmation has been sent via DM.",
                    view=self,
                )
                self.stop()

        await ctx.respond(
            "📝 Please complete your subscription below:",
            view=SubscriptionView(user, uid, username),
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

        # Per-view IDs prevent collisions when multiple users open the UI
        EVENT_SELECT_ID = make_cid("modsub:event", uid)
        REMINDER_SELECT_ID = make_cid("modsub:remind", uid)
        CONFIRM_BUTTON_ID = make_cid("modsub:confirm", uid)
        UNSUB_BUTTON_ID = make_cid("modsub:unsubscribe", uid)

        def option_desc(key: str) -> str:
            return {
                "ruins": "Ruins events",
                "altars": "Altar fights",
                "major": "Major timeline events",
                "fights": "All fights (altars + major FIGHTs)",
                "all": "Every event type",
            }.get(key, "")

        def _is_owner(interaction: discord.Interaction, expected_uid: int) -> bool:
            return interaction.user and interaction.user.id == expected_uid

        class DynamicEventSelect(discord.ui.Select):
            def __init__(self, selected=None):
                selected = selected or existing_types
                options = [
                    discord.SelectOption(
                        label=typ,
                        value=typ,
                        description=option_desc(typ),
                        default=(typ in selected),
                    )
                    for typ in VALID_TYPES
                ]
                super().__init__(
                    placeholder="Select event types...",
                    min_values=0,  # allow none -> defaults
                    max_values=len(options),
                    options=options,
                    custom_id=EVENT_SELECT_ID,
                    row=0,
                )

            async def callback(self, interaction: discord.Interaction):
                if not _is_owner(interaction, uid):
                    await interaction.response.send_message(
                        "This selector isn't for you.", ephemeral=True
                    )
                    return
                view: SubscriptionView = self.view  # type: ignore
                selected = self.values
                view.selected_types = selected

                # Rebuild options to reflect current defaults; we can’t truly disable per-option in selects,
                # but we enforce the rules on confirm and keep defaults aligned in the UI.
                new = type(self)(selected)
                view.clear_items()
                view.add_item(new)  # row 0
                view.add_item(ReminderSelect(view.selected_reminders))  # row 1
                view.add_item(ConfirmButton())  # row 2 (or 3 if you prefer)
                view.add_item(UnsubscribeButton())  # row 2 (or 3 to sit below confirm)
                await interaction.response.edit_message(view=view)

        class ReminderSelect(discord.ui.Select):
            def __init__(self, selected=None):
                selected = selected or existing_times
                options = [
                    discord.SelectOption(
                        label=t,
                        value=t,
                        description=f"{t.upper()} reminder",
                        default=(t in selected),
                    )
                    for t in DEFAULT_REMINDER_TIMES
                ]
                super().__init__(
                    placeholder="Select reminder times...",
                    min_values=0,
                    max_values=len(options),
                    options=options,
                    custom_id=REMINDER_SELECT_ID,
                    row=1,
                )

            async def callback(self, interaction: discord.Interaction):
                if not _is_owner(interaction, uid):
                    await interaction.response.send_message(
                        "This selector isn't for you.", ephemeral=True
                    )
                    return
                self.view.selected_reminders = self.values  # type: ignore
                await interaction.response.defer()  # silent ack

        class ConfirmButton(discord.ui.Button):
            def __init__(self):
                super().__init__(
                    label="✅ Update Preferences",
                    style=discord.ButtonStyle.success,
                    custom_id=CONFIRM_BUTTON_ID,
                    row=2,
                )
                self._clicked = False

            async def callback(self, interaction: discord.Interaction):
                if not _is_owner(interaction, uid):
                    await interaction.response.send_message(
                        "This button isn't for you.", ephemeral=True
                    )
                    return
                if self._clicked:
                    await interaction.response.defer()
                    return
                self._clicked = True
                view: SubscriptionView = self.view  # type: ignore
                await view.on_confirm(interaction)

        class UnsubscribeButton(discord.ui.Button):
            def __init__(self):
                super().__init__(
                    label="🔕 Unsubscribe",
                    style=discord.ButtonStyle.danger,
                    custom_id=UNSUB_BUTTON_ID,
                    row=3,  # place under the confirm
                )
                self._clicked = False

            async def callback(self, interaction: discord.Interaction):
                if not _is_owner(interaction, uid):
                    await interaction.response.send_message(
                        "This button isn't for you.", ephemeral=True
                    )
                    return
                if self._clicked:
                    await interaction.response.defer()
                    return
                self._clicked = True
                try:
                    # Cancel any pending DM tasks for this user
                    cancelled = cancel_user_reminder_tasks(uid)
                    # Purge trackers (per-user, per-event buckets removed)
                    sched_removed = purge_user_from_dm_scheduled_tracker(uid)
                    sent_removed = purge_user_from_dm_sent_tracker(uid)
                    # Remove subscription config
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

                # disable UI and confirm
                for c in self.view.children:
                    c.disabled = True
                await interaction.response.edit_message(
                    content="✅ You’ve been unsubscribed.", view=self.view
                )
                # optional DM
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
                self.view.stop()

        class SubscriptionView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=180)
                self.user = user
                self.uid = uid
                self.username = username
                self.selected_types = existing_types.copy()
                self.selected_reminders = existing_times.copy()
                self.add_item(DynamicEventSelect(self.selected_types))
                self.add_item(ReminderSelect(self.selected_reminders))
                self.add_item(ConfirmButton())
                self.add_item(UnsubscribeButton())

            async def on_timeout(self):
                for c in self.children:
                    c.disabled = True
                try:
                    msg = await ctx.interaction.original_response()
                    await msg.edit(view=self)
                except Exception:
                    pass

            async def on_confirm(self, interaction: discord.Interaction):
                types = list(self.selected_types)
                times = list(self.selected_reminders)
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

                # Validate selections
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

                # Enforce exclusivity
                if "all" in types:
                    types = ["all"]
                elif "fights" in types:
                    types = [t for t in types if t not in ("altars", "major")]

                try:
                    set_user_config(self.uid, self.username, types, times)
                except Exception as e:
                    logger.exception("[modify_subscription] set_user_config failed")
                    await interaction.response.send_message(
                        f"❌ Failed to save your preferences: `{type(e).__name__}: {e}`",
                        ephemeral=True,
                    )
                    return

                # DM confirmation
                embed = discord.Embed(
                    title="🔄 Preferences Updated",
                    description=f"Hi {self.user.mention}, your event reminder preferences are now updated!",
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
                    await self.user.send(embed=embed)
                except discord.Forbidden:
                    await interaction.response.send_message(
                        "⚠️ Could not send DM. Please enable DMs from this server.", ephemeral=True
                    )
                    return

                # Disable UI and confirm in place
                for c in self.children:
                    c.disabled = True
                await interaction.response.edit_message(
                    content="✅ Preferences updated! A confirmation has been sent via DM.",
                    view=self,
                )
                self.stop()

        await ctx.respond(
            "🛠️ Update your preferences below:", view=SubscriptionView(), ephemeral=True
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
    @versioned("v1.10")
    @safe_command
    @track_usage()
    async def mykvkstats(ctx: discord.ApplicationContext):
        # We always keep the selector private to the caller
        await safe_defer(ctx, ephemeral=True)

        # Load registry (support str/int keys)
        try:
            registry = load_registry() or {}
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
                row = load_stat_row(gid)
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

            try:
                embed, file = build_stats_embed(row, ctx.user)
            except Exception as e:
                logger.exception("[/mykvkstats] build_stats_embed failed")
                await ctx.interaction.edit_original_response(
                    content=f"❌ Failed to build stats: `{type(e).__name__}: {e}`"
                )
                return

            # PUBLIC post
            await ctx.channel.send(embed=embed, file=file)

            # Silence the ephemeral placeholder instead of confirming
            try:
                await ctx.interaction.edit_original_response(content=" ", view=None)
            except Exception:
                pass
            return

        # Multi-account path → ephemeral dropdown + helper buttons
        try:
            ordered_accounts = {slot: accounts[slot] for slot in ACCOUNT_ORDER if slot in accounts}
            view = MyKVKStatsSelectView(ctx=ctx, accounts=ordered_accounts, author_id=ctx.user.id)
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
        description="Admin only: Refresh player stats cache from Google Sheet.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def refresh_stats_cache(ctx):

        await safe_defer(ctx, ephemeral=True)
        started = datetime.now(UTC)

        try:
            # If build_player_stats_cache returns a count or dict, surface it
            result = await build_player_stats_cache()
            count = None
            if isinstance(result, int):
                count = result
            elif isinstance(result, dict) and "count" in result:
                count = result["count"]

            dur = (datetime.now(UTC) - started).total_seconds()
            msg = "✅ Player stats cache has been refreshed."
            if count is not None:
                msg += f" ({count} records)"
            msg += f" ⏱ {dur:.1f}s"

            logger.info(
                "[/refresh_stats_cache] success %s", f"(count={count})" if count is not None else ""
            )
            await ctx.interaction.edit_original_response(content=msg)

        except Exception as e:
            logger.exception("[/refresh_stats_cache] failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to refresh cache:\n```{type(e).__name__}: {e}```"
            )

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

        await ctx.interaction.edit_original_response(embed=embed)

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
    @versioned("v1.14")
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
        import csv as _csv
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

        # ---------- CSV writers ----------
        def to_csv_bytes(headers: list[str], rows: list[dict]) -> io.BytesIO:
            buf = io.StringIO()
            writer = _csv.DictWriter(buf, fieldnames=headers, lineterminator="\n")
            writer.writeheader()
            for r in rows:
                writer.writerow({h: r.get(h, "") for h in headers})
            return io.BytesIO(buf.getvalue().encode("utf-8-sig"))  # Excel-friendly BOM

        registered_rows.sort(
            key=lambda r: (
                str(r.get("discord_user", "")).casefold(),
                str(r.get("account_type", "")).casefold(),
            )
        )
        reg_headers = [
            "discord_id",
            "discord_id_excel",
            "discord_user",
            "account_type",
            "governor_id",
            "governor_id_excel",
            "governor_name",
            "roles",
            "top_role",
        ]
        reg_file = discord.File(
            to_csv_bytes(reg_headers, registered_rows), filename="registered_accounts.csv"
        )

        # Unregistered CURRENT governors from SQL (choose useful cols)
        unreg_rows: list[dict] = []
        for gid_sql in unregistered_ids:
            rr = row_by_id.get(gid_sql, {})
            unreg_rows.append(
                {
                    "governor_id": gid_sql,  # straight from SQL (bigint -> str)
                    "governor_id_excel": excel_safe_formula(gid_sql),
                    "governor_name": str(rr.get("GovernorName", "Unknown")).strip(),
                    "alliance": str(rr.get("Alliance") or "").strip(),
                    "power_rank": rr.get("PowerRank", ""),
                    "power": rr.get("Power", ""),
                    "kill_points": rr.get("KillPoints", ""),
                    "deads": rr.get("Deads", ""),
                    "city_hall": rr.get("City Hall", ""),
                    "location": rr.get("LOCATION", ""),
                    "scan_date": rr.get("ScanDate", ""),
                }
            )
        unreg_rows.sort(
            key=lambda r: (
                str(r.get("governor_name", "")).casefold(),
                str(r.get("governor_id", "")),
            )
        )
        unreg_headers = [
            "governor_id",
            "governor_id_excel",
            "governor_name",
            "alliance",
            "power_rank",
            "power",
            "kill_points",
            "deads",
            "city_hall",
            "location",
            "scan_date",
        ]
        unreg_file = discord.File(
            to_csv_bytes(unreg_headers, unreg_rows), filename="unregistered_current_governors.csv"
        )

        # Members without registration
        mw_rows: list[dict] = []
        for m in members_without_reg:
            roles_str, top = role_names(m)
            mw_rows.append(
                {
                    "discord_id": str(m.id),
                    "discord_id_excel": excel_safe_formula(str(m.id)),
                    "discord_user": str(m),
                    "roles": roles_str,
                    "top_role": top,
                }
            )
        mw_rows.sort(key=lambda r: str(r.get("discord_user", "")).casefold())
        mw_headers = ["discord_id", "discord_id_excel", "discord_user", "roles", "top_role"]
        mw_file = discord.File(
            to_csv_bytes(mw_headers, mw_rows), filename="members_without_registration.csv"
        )

        # ---------- Summary embed ----------
        embed = discord.Embed(
            title="🧾 Registration Audit (Current Governors)", color=discord.Color.blurple()
        )
        embed.add_field(name="Registered accounts", value=f"{len(registered_rows):,}", inline=True)
        embed.add_field(
            name="Unregistered current governors (SQL)", value=f"{len(unreg_rows):,}", inline=True
        )
        embed.add_field(
            name="Discord members without registration", value=f"{len(mw_rows):,}", inline=True
        )
        embed.set_footer(
            text="CSV exports attached (Excel-safe IDs; roles included where applicable)."
        )

        # ---------- Respond ----------
        await ctx.interaction.edit_original_response(embed=embed, content=None)
        try:
            await ctx.followup.send(files=[reg_file, unreg_file, mw_file], ephemeral=True)
        except Exception:
            await ctx.followup.send(
                content="⚠️ Ephemeral file delivery failed, sending files non-ephemerally instead.",
                files=[reg_file, unreg_file, mw_file],
                ephemeral=False,
            )

    # ---------- EXPORT (now includes roles and excel safe RAW fields) ----------
    @bot.slash_command(
        name="bulk_export_registrations",
        description="Admin: export current registrations as CSV (with roles).",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.02")
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
        b = io.BytesIO(buf.getvalue().encode("utf-8-sig"))

        await ctx.interaction.edit_original_response(
            content="📤 Exported current registrations (Excel-safe, with roles)."
        )
        await ctx.followup.send(file=discord.File(b, filename="registrations_export.csv"))

    # ===== BULK IMPORT (FOLLOW-UP ATTACHMENT FLOW) =====

    # ---------- helper: wait for user's next message with a CSV attachment ----------
    async def _await_csv_attachment(
        ctx: discord.ApplicationContext,
        prompt_text: str,
        *,
        timeout: int = 180,
        max_size_bytes: int = 5_000_000,
    ) -> discord.Attachment | None:
        """Prompt the invoker to upload a .csv as their next message in this channel; wait up to `timeout` seconds."""
        await ctx.interaction.edit_original_response(content=prompt_text)

        def check(msg: discord.Message) -> bool:
            if msg.author.id != ctx.user.id:
                return False
            if msg.channel.id != ctx.channel_id:
                return False
            return any(att.filename.lower().endswith(".csv") for att in msg.attachments)

        try:
            msg: discord.Message = await ctx.bot.wait_for("message", check=check, timeout=timeout)
        except TimeoutError:
            await ctx.interaction.edit_original_response(
                content=f"⏳ Timed out after {timeout}s waiting for your CSV. Please run the command again."
            )
            return None

        attach = next((a for a in msg.attachments if a.filename.lower().endswith(".csv")), None)
        if not attach:
            await ctx.interaction.edit_original_response(
                content="❌ I saw your message but it had no `.csv` attachment. Please run the command again."
            )
            return None

        if attach.size > max_size_bytes:
            await ctx.interaction.edit_original_response(
                content=f"❌ File too large ({attach.size:,} bytes). Max allowed is {max_size_bytes:,} bytes."
            )
            return None

        return attach

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
        ask = (
            "📎 Please upload the **CSV file** now (as a new message in this channel).\n"
            "Required logical columns: `discord_id OR discord_id_excel`, `account_type`, `governor_id OR governor_id_excel`.\n"
            "_Tip: You can export from `/bulk_export_registrations` or `/registration_audit` and edit that file._"
        )
        attach = await _await_csv_attachment(ctx, ask)
        if not attach:
            return  # message already sent

        import csv as _csv

        csv_bytes = await attach.read()
        # Use utf-8-sig to strip BOM cleanly
        f = io.StringIO(csv_bytes.decode("utf-8-sig", errors="ignore"))
        reader = _csv.DictReader(f)

        if not reader.fieldnames:
            await ctx.interaction.edit_original_response(
                content="❌ CSV appears to have no header row."
            )
            return

        # Case-insensitive field lookup
        headers_lower = {h.lower(): h for h in reader.fieldnames if isinstance(h, str)}

        def get_field(row: dict, logical: str) -> str:
            # logical is the lowercase name we're asking for
            name = headers_lower.get(logical)
            return "" if name is None else str(row.get(name, "") or "")

        # Validate logical requirements
        have_discord_raw = "discord_id" in headers_lower
        have_discord_excel = "discord_id_excel" in headers_lower
        have_governor_raw = "governor_id" in headers_lower
        have_governor_excel = "governor_id_excel" in headers_lower
        have_account_type = "account_type" in headers_lower

        if (
            not have_account_type
            or not (have_discord_raw or have_discord_excel)
            or not (have_governor_raw or have_governor_excel)
        ):
            await ctx.interaction.edit_original_response(
                content=(
                    "❌ CSV missing required logical columns. Need:\n"
                    "- `account_type`\n"
                    "- `discord_id` **or** `discord_id_excel`\n"
                    "- `governor_id` **or** `governor_id_excel`"
                )
            )
            return

        registry = load_registry()
        all_rows = _name_cache.get("rows", [])  # source-of-truth governor list
        valid_ids = {str(x.get("GovernorID")).strip(): x for x in all_rows if x.get("GovernorID")}

        # --- helpers for summary accounting ---
        def _count_accounts(reg):
            total_accounts = 0
            users_with_accounts = 0
            for _uid, _data in reg.items():
                n = len(_data.get("accounts", {}))
                total_accounts += n
                if n:
                    users_with_accounts += 1
            return total_accounts, users_with_accounts

        before_total_accounts, before_users_with_accounts = _count_accounts(registry)

        # Work on a copy; only save if not dry_run
        work = json.loads(json.dumps(registry))

        # Build reverse index for fast conflict checks: GovID -> (uid, account_type)
        gid_to_owner: dict[str, tuple[str, str]] = {}
        for uid0, data0 in work.items():
            accs0 = data0.get("accounts", {}) or {}
            for at0, det0 in accs0.items():
                g0 = str(det0.get("GovernorID", "")).strip()
                if g0:
                    gid_to_owner[g0] = (str(uid0), str(at0))

        # CSV processing bookkeeping
        errors: list[str] = []
        error_rows: list[dict] = []  # for error CSV
        changes: list[str] = []
        adds = updates = unchanged = 0
        affected_user_ids = set()

        # In-file duplicate detection
        seen_combo: dict[tuple[str, str], str] = {}  # (discord_id, account_type) -> governor_id
        seen_gid_infile: dict[str, str] = {}  # governor_id -> discord_id

        # Normalization counters
        norm_counts = {
            "discord_id_formula": 0,
            "discord_id_sci": 0,
            "governor_id_formula": 0,
            "governor_id_sci": 0,
            "account_type_canon": 0,
        }

        # Process rows
        for i, row in enumerate(reader, start=2):  # data starts at line 2
            # Fetch raw + excel columns (case-insensitive)
            did_raw = get_field(row, "discord_id")
            did_xls = get_field(row, "discord_id_excel")
            gid_raw = get_field(row, "governor_id")
            gid_xls = get_field(row, "governor_id_excel")
            acc_raw = get_field(row, "account_type")
            discord_user_hint = get_field(row, "discord_user")
            governor_name_hint = get_field(row, "governor_name")

            # Normalize IDs
            did, did_notes = normalize_id(did_raw, did_xls, field="discord_id")
            gid, gid_notes = normalize_id(gid_raw, gid_xls, field="governor_id")

            if did_notes:
                if "formula" in did_notes:
                    norm_counts["discord_id_formula"] += 1
                if "sci" in did_notes:
                    norm_counts["discord_id_sci"] += 1
            if gid_notes:
                if "formula" in gid_notes:
                    norm_counts["governor_id_formula"] += 1
                if "sci" in gid_notes:
                    norm_counts["governor_id_sci"] += 1

            if not did or not gid:
                msg = f"Row {i}: invalid IDs (discord_id='{did_raw or did_xls}', governor_id='{gid_raw or gid_xls}')."
                errors.append(msg)
                error_rows.append(
                    {
                        "row": i,
                        "discord_id": did_raw or did_xls,
                        "account_type": acc_raw,
                        "governor_id": gid_raw or gid_xls,
                        "error": "Invalid discord_id or governor_id after normalization",
                    }
                )
                continue

            # Normalize account type
            acc_norm, did_canon, acc_err = normalize_account_type(acc_raw)
            if acc_err:
                msg = f"Row {i}: {acc_err}"
                errors.append(msg)
                error_rows.append(
                    {
                        "row": i,
                        "discord_id": did,
                        "account_type": acc_raw,
                        "governor_id": gid,
                        "error": acc_err,
                    }
                )
                continue
            if did_canon:
                norm_counts["account_type_canon"] += 1

            # Validate governor against source-of-truth
            src_row = valid_ids.get(gid)
            if not src_row:
                msg = f"Row {i}: governor_id `{gid}` not found in source data."
                errors.append(msg)
                error_rows.append(
                    {
                        "row": i,
                        "discord_id": did,
                        "account_type": acc_norm,
                        "governor_id": gid,
                        "error": "GovernorID not found in source data",
                    }
                )
                continue

            # In-file duplicate checks
            key = (did, acc_norm)
            prev_gid_same_combo = seen_combo.get(key)
            if prev_gid_same_combo and prev_gid_same_combo != gid:
                msg = f"Row {i}: duplicate account row for {did} {acc_norm} with conflicting governor_id ({prev_gid_same_combo} vs {gid})."
                errors.append(msg)
                error_rows.append(
                    {
                        "row": i,
                        "discord_id": did,
                        "account_type": acc_norm,
                        "governor_id": gid,
                        "error": "Conflicting duplicate of (discord_id, account_type) in CSV",
                    }
                )
                continue
            seen_combo[key] = gid

            prev_csv_owner = seen_gid_infile.get(gid)
            if prev_csv_owner and prev_csv_owner != did:
                msg = f"Row {i}: governor_id `{gid}` assigned to multiple discord_ids in CSV ({prev_csv_owner} and {did})."
                errors.append(msg)
                error_rows.append(
                    {
                        "row": i,
                        "discord_id": did,
                        "account_type": acc_norm,
                        "governor_id": gid,
                        "error": "GovernorID appears multiple times for different users in this CSV",
                    }
                )
                continue
            seen_gid_infile[gid] = did

            # Cross-user conflict with existing registry
            owner = gid_to_owner.get(gid)
            if owner and owner[0] != did:
                existing_owner_uid, existing_acc = owner
                msg = (
                    f"Row {i}: governor_id `{gid}` already registered to "
                    f"{work.get(existing_owner_uid, {}).get('discord_name', existing_owner_uid)} ({existing_acc})."
                )
                errors.append(msg)
                error_rows.append(
                    {
                        "row": i,
                        "discord_id": did,
                        "account_type": acc_norm,
                        "governor_id": gid,
                        "error": "GovernorID already registered to another user",
                    }
                )
                continue

            # Ready to apply to working copy
            gv_name = (governor_name_hint or src_row.get("GovernorName") or "Unknown").strip()
            user_label = (discord_user_hint or did).strip()

            entry = work.setdefault(
                did, {"discord_id": did, "discord_name": user_label, "accounts": {}}
            )
            entry["discord_name"] = user_label
            affected_user_ids.add(did)

            prev = entry["accounts"].get(acc_norm)
            new_payload = {"GovernorID": gid, "GovernorName": gv_name}

            if prev is None:
                entry["accounts"][acc_norm] = new_payload
                gid_to_owner[gid] = (did, acc_norm)  # update reverse index
                adds += 1
                changes.append(f"Row {i}: ADD {did} {acc_norm} -> {gv_name} ({gid})")
            else:
                prev_gid = str(prev.get("GovernorID", "")).strip()
                prev_gn = str(prev.get("GovernorName", "")).strip()
                if prev_gid == gid and prev_gn == gv_name:
                    unchanged += 1
                else:
                    entry["accounts"][acc_norm] = new_payload
                    gid_to_owner[gid] = (did, acc_norm)
                    updates += 1
                    # If only the name changed, still treat as update (names do change)
                    changes.append(f"Row {i}: UPDATE {did} {acc_norm} -> {gv_name} ({gid})")

        after_total_accounts, after_users_with_accounts = _count_accounts(work)

        # Build summary
        summary_lines = [
            f"• Adds: **{adds}**",
            f"• Updates: **{updates}**",
            f"• Unchanged: **{unchanged}**",
            f"• Errors: **{len(errors)}**",
            "",
            f"• Accounts total: **{before_total_accounts} → {after_total_accounts}** "
            f"(Δ **{after_total_accounts - before_total_accounts}**)",
            f"• Users with ≥1 account: **{before_users_with_accounts} → {after_users_with_accounts}** "
            f"(Δ **{after_users_with_accounts - before_users_with_accounts}**)",
            f"• Distinct users affected in CSV: **{len(affected_user_ids)}**",
            "",
            "• Normalizations applied:"
            f"\n  - discord_id from Excel formula: **{norm_counts['discord_id_formula']}**"
            f"\n  - discord_id from scientific notation: **{norm_counts['discord_id_sci']}**"
            f"\n  - governor_id from Excel formula: **{norm_counts['governor_id_formula']}**"
            f"\n  - governor_id from scientific notation: **{norm_counts['governor_id_sci']}**"
            f"\n  - account_type canonicalized: **{norm_counts['account_type_canon']}**",
        ]
        summary_block = "\n".join(summary_lines)

        # If errors, attach error CSV and return
        if errors:
            import csv as _csv

            # Create error CSV (utf-8-sig for Excel)
            err_buf = io.StringIO()
            err_headers = ["row", "discord_id", "account_type", "governor_id", "error"]
            w = _csv.DictWriter(err_buf, fieldnames=err_headers, lineterminator="\n")
            w.writeheader()
            for er in sorted(error_rows, key=lambda x: int(x.get("row", 0))):
                w.writerow({h: er.get(h, "") for h in err_headers})
            err_file = io.BytesIO(err_buf.getvalue().encode("utf-8-sig"))
            file_obj = discord.File(err_file, filename="import_errors.csv")

            embed = discord.Embed(
                title="❌ Import validation failed",
                description=summary_block
                + "\n\n**First issues:**\n"
                + "\n".join(errors[:20])
                + (f"\n… and {len(errors)-20} more" if len(errors) > 20 else ""),
                color=0xE74C3C,
            )
            await ctx.interaction.edit_original_response(embed=embed, content=None)

            # Try ephemeral first; if that fails, fall back to non-ephemeral
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
            detail = "\n".join(changes[:20]) or "_(No changes detected.)_"
            more = f"\n… and {len(changes)-20} more" if len(changes) > 20 else ""
            embed = discord.Embed(
                title="✅ Dry Run OK",
                description=summary_block + "\n\n**Planned changes:**\n" + detail + more,
                color=0x2ECC71,
            )
            await ctx.interaction.edit_original_response(embed=embed, content=None)
            return

        # Commit
        save_registry(work)
        embed = discord.Embed(
            title="✅ Import Complete",
            description=summary_block + "\n\n_All changes applied successfully._",
            color=0x2ECC71,
        )
        await ctx.interaction.edit_original_response(embed=embed, content=None)

    # ---------- IMPORT (DRY RUN) ----------
    @bot.slash_command(
        name="bulk_import_registrations_dryrun",
        description="Admin: validate a registrations CSV without saving.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.10")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def bulk_import_registrations_dryrun(ctx: discord.ApplicationContext):
        await safe_defer(ctx, ephemeral=True)
        await asyncio.wait_for(_import_regs_impl(ctx, dry_run=True), timeout=120)

    # ---------- IMPORT (COMMIT) ----------
    @bot.slash_command(
        name="bulk_import_registrations",
        description="Admin: import registrations from CSV (commits changes).",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.10")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def bulk_import_registrations(ctx: discord.ApplicationContext):
        await safe_defer(ctx, ephemeral=True)
        await _import_regs_impl(ctx, dry_run=False)

    @bot.slash_command(
        name="test_offseason_embed2",
        description="🧪 Manually trigger the off-season dashboard (DAILY) here",
        guild_ids=[GUILD_ID],
    )
    @versioned("v2.12")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def test_offseason_embed2(ctx: discord.ApplicationContext):
        # optional: defer ephemeral
        try:
            ir = getattr(ctx, "interaction", None)
            if ir and hasattr(ir, "response") and not ir.response.is_done():
                await ir.response.defer(ephemeral=True)
        except Exception:
            pass

        try:
            await send_offseason_stats_embed_v2(
                ctx.bot,
                ctx=ctx,
                is_weekly=False,
                mention_everyone=False,  # ← explicit: never ping in tests
            )
            await ctx.followup.send(
                "✅ Sent daily off-season test embed (no @everyone).", ephemeral=True
            )
        except Exception as e:
            await ctx.followup.send(f"❌ Failed:\n{e}", ephemeral=True)

    # WEEKLY
    @bot.slash_command(
        name="test_weekly_offseason_embed2",
        description="🧪 Manually trigger the off-season dashboard (WEEKLY) here",
        guild_ids=[GUILD_ID],
    )
    @versioned("v2.12")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def test_weekly_offseason_embed2(ctx: discord.ApplicationContext):
        try:
            ir = getattr(ctx, "interaction", None)
            if ir and hasattr(ir, "response") and not ir.response.is_done():
                await ir.response.defer(ephemeral=True)
        except Exception:
            pass

        try:
            await send_offseason_stats_embed_v2(
                ctx.bot,
                ctx=ctx,
                is_weekly=True,
                mention_everyone=False,  # ← explicit: never ping in tests
            )
            await ctx.followup.send(
                "✅ Sent weekly off-season test embed (no @everyone).", ephemeral=True
            )
        except Exception as e:
            await ctx.followup.send(f"❌ Failed:\n{e}", ephemeral=True)

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
    @versioned("v1.11")
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
            timeout=840,  # e.g., 14 minutes
        )

        gid_for_choice = None if default_choice == "ALL" else name_to_id.get(default_choice)
        embeds, files = build_embeds(
            slice_key, default_choice, payload, governor_id_for_choice=gid_for_choice
        )

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
        description="Export your registered accounts’ stats to Excel (last 6 months, tabs & charts).",
        guild_ids=[GUILD_ID],
    )
    @versioned("v2.04")  # bump version
    @safe_command
    @track_usage()
    async def my_stats_export(ctx: discord.ApplicationContext):
        # ✅ Only visible to the caller
        await ctx.defer(ephemeral=True)

        # 1) Resolve the caller’s registered GovernorIDs
        registry = load_registry()
        accounts = (registry.get(str(ctx.user.id)) or {}).get("accounts", {})
        gov_ids = [int(a["GovernorID"]) for a in accounts.values() if a and a.get("GovernorID")]

        if not gov_ids:
            await ctx.interaction.edit_original_response(
                content="❌ You have no registered accounts yet. Use `/register_governor` first."
            )
            return

        # 2) Pull DAILY data for the fixed 6-month window
        conn = _conn()
        csv_ids = ",".join(str(i) for i in gov_ids)
        days = 180  # fixed window

        sql_daily = f"""
        SELECT *
        FROM dbo.vDaily_PlayerExport
        WHERE GovernorID IN ({csv_ids})
          AND AsOfDate >= DATEADD(DAY, -{days}, CAST(GETDATE() AS date))
        ORDER BY GovernorID, AsOfDate;
        """
        df_daily = pd.read_sql(sql_daily, conn)

        if df_daily.empty:
            await ctx.interaction.edit_original_response(
                content="⚠️ No rows found for your accounts in the last 6 months."
            )
            return

        # 3) Optional targets
        sql_targets = f"""
        SELECT GovernorID, DKP_TARGET, DKP_SCORE, Kill_Target, Deads_Target
        FROM dbo.EXCEL_OUTPUT_KVK_TARGETS_CURRENT WITH (NOLOCK)
        WHERE GovernorID IN ({csv_ids});
        """
        try:
            df_targets = pd.read_sql(sql_targets, conn)
        except Exception:
            df_targets = pd.DataFrame()

        # 4) Build Excel (six-month tables & charts are already handled in stats_exporter)
        out_dir = "exports"
        os.makedirs(out_dir, exist_ok=True)
        fname = f"my_stats_{ctx.user.id}_{datetime.utcnow():%Y%m%d_%H%M}.xlsx"
        path = os.path.join(out_dir, fname)

        build_user_stats_excel(df_daily, df_targets, out_path=path, days_for_daily_table=180)

        # 5) Send file ephemerally (edits the deferred ephemeral response)
        await ctx.interaction.edit_original_response(file=discord.File(path))

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
        name="my_kvkhistory",
        description="View your KVK-by-KVK history as a chart and table.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.08")
    @safe_command
    @track_usage()
    async def my_kvkhistory(
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
        name="kvkrankings",
        description="Leaderboard for current KVK: Kills, Deads, or DKP.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.03")
    @safe_command
    @track_usage()
    async def kvkrankings(ctx: discord.ApplicationContext):
        # No initial choices; show immediately as Kills / Top 10
        await ctx.defer()  # standard defer; not ephemeral

        cache = load_stat_cache()
        rows = [r for k, r in cache.items() if k != "_meta"]
        if not rows:
            await ctx.respond(
                "⚠️ No stats cache available yet. Try again after the next scan/export."
            )
            return

        # Defaults: Kills + Top 10
        view = KVKRankingView(cache, metric="kills", limit=10, timeout=120.0)
        embed = build_kvkrankings_embed(rows, "kills", 10)

        # Fallback footer if helper didn’t set one (e.g., no LAST_REFRESH on slice)
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
                c.execute(
                    """
                    SELECT TOP 1 KVK_NO
                    FROM dbo.KVK_Details
                    WHERE GETUTCDATE() BETWEEN KVK_REGISTRATION_DATE AND KVK_END_DATE
                    ORDER BY KVK_NO DESC
                """
                )
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
        sql_conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};"
        )

        # Whether the season is currently KVK (for the send_stats_update_embed path)
        is_kvk = await asyncio.to_thread(is_currently_kvk, SERVER, DATABASE, USERNAME, PASSWORD)

        try:
            if post_here:
                # Directly call the internal builder to post in the invoking channel, test-mode (no ping)
                await _send_kvk_embed(ctx.bot, ctx.channel, ts, sql_conn_str, is_test=True)
                where = ctx.channel.mention
            else:
                # Use the public entrypoint; test-mode skips daily-send guards and pings, posts to Stats channel
                await send_stats_update_embed(ctx.bot, ts, True, sql_conn_str, is_test=True)
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
                max_scan = int(c.fetchone()[0] or 0)

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
        name="my_kvkcrystaltech",
        description="🔬 Guide and track your KVK Crystal Tech path",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.05")
    @safe_command
    @track_usage()
    async def my_kvkcrystaltech(
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
            logger.exception("[/my_kvkcrystaltech] load_registry failed")
            await ctx.followup.send(
                "⚠️ Couldn’t load your registered accounts. Provide `governorid` or try again later.",
                ephemeral=only_me,
            )
            return

        options = _build_unique_gov_options(accounts)

        if options:
            if len(options) == 1:
                only_gid = options[0].value
                await run_crystaltech_flow(ctx.interaction, only_gid, ephemeral=only_me)
                return

            view = AccountPickerView(
                ctx=ctx,
                options=options,
                on_select_governor=run_crystaltech_flow,
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
            view = AccountPickerView(
                ctx=ctx,
                options=[],
                on_select_governor=run_crystaltech_flow,
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
    @versioned("v1.00")
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
        if not _is_admin(ctx):
            await ctx.respond("❌ You don’t have permission to run this command.", ephemeral=True)
            return

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
        name="honor_top",
        description="Show the latest Honour Top-N (default 10, max 50).",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @is_admin_and_notify_channel()
    @safe_command
    @track_usage()
    async def honor_top(ctx: discord.ApplicationContext, limit: int = 10):
        await ctx.defer(ephemeral=True)

        # Clamp and fetch
        try:
            n = max(1, min(50, int(limit)))
        except Exception:
            n = 10

        rows = await asyncio.to_thread(get_latest_honor_top, n)
        if not rows:
            await ctx.respond(
                "ℹ️ No Honour data available yet (or the top score is 0).", ephemeral=True
            )
            return

        # Format (🥇/🥈/🥉 then #4…)
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for idx, r in enumerate(rows[:n]):
            rank = medals[idx] if idx < 3 else f"#{idx+1}"
            name = r.get("GovernorName") or "Unknown"
            pts = int(r.get("HonorPoints") or 0)
            lines.append(f"{rank} **{name}** — `{pts:,}`")

        embed = discord.Embed(
            title=f"🏅 Honour Top {min(n, len(rows))}",
            description="\n".join(lines),
            color=discord.Color.gold(),
        )
        await ctx.respond(embed=embed, ephemeral=True)

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
