# commands/telemetry_cmds.py

from __future__ import annotations

import asyncio
import builtins as _bi
from datetime import UTC, datetime, timedelta
from io import BytesIO
import json
import logging
import os
import tempfile

# ——— Standard library ———
import discord
from discord.ext import commands as ext_commands  # avoid name conflict
from discord.ui import View
from dotenv import load_dotenv

# ——— Third-party ———
from bot_config import (
    GUILD_ID,
    KVK_CRYSTALTECH_CHANNEL_ID,
    KVK_PLAYER_STATS_CHANNEL_ID,
    KVK_TARGET_CHANNEL_ID,
    LEADERSHIP_CHANNEL_ID,
    NOTIFY_CHANNEL_ID,
)
from constants import (
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


from decoraters import (
    _has_leadership_role,
    _is_admin,
    _is_allowed_channel,
    channel_only,
    track_usage,
)
from embed_player_profile import build_player_profile_embed
from embed_utils import (
    build_stats_embed,
    build_target_embed,
)
from file_utils import fetch_one_dict
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
    global_cmd_error_handler,
    safe_command,
    safe_defer,
)
from governor_registry import (
    load_registry,
)
from logging_setup import CRASH_LOG_PATH, ERROR_LOG_PATH, FULL_LOG_PATH
from profile_cache import (
    autocomplete_choices,
    get_profile_cached,
    search_by_governor_name,
    warm_cache,
)
from target_utils import (
    _name_cache,
    autocomplete_governor_names,
    lookup_governor_id,
    run_target_lookup,
)
from ui.views.location_views import ProfileLinksView
from ui.views.registry_views import (
    GovernorSelectView,
    GovNameModal,
    RegisterStartView,
    configure_registry_views,
)
from utils import (
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


async def run_crystaltech_flow(interaction: discord.Interaction, governor_id: str, ephemeral: bool):
    """Open CrystalTech setup/progress flow for a governor."""

    claimed, why = _session_claim(governor_id, interaction.user.id)
    if not claimed:
        msg = f"🔒 {why}"
        if not interaction.response.is_done():
            await interaction.response.send_message(msg, ephemeral=True)
        else:
            await interaction.followup.send(msg, ephemeral=True)
        return

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
            path_id = entry.get("selected_path_id")
            troop = entry.get("selected_troop_type", "unknown")

            view = ProgressView(
                author_id=interaction.user.id,
                governor_id=governor_id,
                path_id=path_id,
                troop=troop,
                timeout=300,
                on_release=_release,
            )
            embed, files = await view.render_embed()

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

        label = await _resolve_governor_label(interaction.user.id, governor_id)
        accounts = [(governor_id, label)]
        view = SetupView(
            author_id=interaction.user.id,
            accounts=accounts,
            timeout=300,
            on_release=_release,
        )
        embed = view.make_embed()

        try:
            await interaction.response.edit_message(
                content="Opening setup…", embed=None, view=None, attachments=[]
            )
        except Exception:
            pass

        sent = await interaction.followup.send(embed=embed, ephemeral=ephemeral, view=view)
        view.message = sent
        _session_refresh(governor_id, interaction.user.id)

    except Exception as e:
        logger.exception("[CrystalTech] run_crystaltech_flow unhandled: %s", e, exc_info=True)
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"❌ Unexpected error: `{type(e).__name__}: {e}`", ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"❌ Unexpected error: `{type(e).__name__}: {e}`", ephemeral=True
            )
        await _release()


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

    @bot.slash_command(name="ping", description="Test command", guild_ids=[GUILD_ID])
    @versioned("v1.0")
    @safe_command
    @track_usage()
    async def ping_command(ctx):
        await ctx.respond("Pong! 🏓")

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


def register_telemetry(bot: ext_commands.Bot) -> None:
    register_commands(bot)
