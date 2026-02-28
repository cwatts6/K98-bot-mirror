# commands/stats_cmds.py
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import logging
import os
import time

import discord
from discord.ext import commands as ext_commands

from bot_config import (
    ADMIN_USER_ID,
    GUILD_ID,
    KVK_PLAYER_STATS_CHANNEL_ID,
    NOTIFY_CHANNEL_ID,
    STATS_ALERT_CHANNEL_ID,
)
from build_KVKrankings_embed import build_kvkrankings_embed
from constants import CREDENTIALS_FILE, DATABASE, KVK_SHEET_NAME, PASSWORD, SERVER, USERNAME, _conn
from core.interaction_safety import safe_command, safe_defer
from decoraters import (
    _actor_from_ctx,
    _is_admin,
    channel_only,
    is_admin_and_notify_channel,
    is_admin_or_leadership,
    track_usage,
)
from embed_my_stats import SliceButtons, build_embeds
from embed_utils import build_stats_embed
from file_utils import fetch_one_dict
from governor_registry import get_user_main_governor_name, load_registry
from gsheet_module import run_kvk_export_test, run_kvk_proc_exports_with_alerts
from honor_rankings_view import HonorRankingView, build_honor_rankings_embed
from kvk_history_view import KVKHistoryView
from profile_cache import autocomplete_choices
from stats_alerts.embeds.kvk import send_kvk_embed
from stats_alerts.honors import get_latest_honor_top, purge_latest_honor_scan
from stats_alerts.interface import send_stats_update_embed
from stats_alerts.kvk_meta import is_currently_kvk
from stats_service import (
    get_registered_governor_ids_for_discord,
    get_registered_governor_names_for_discord,
    get_stats_payload,
)
from ui.views.registry_views import GovNameModal, MyRegsActionView, RegisterStartView
from ui.views.stats_views import KVKRankingView
from utils import load_stat_cache, load_stat_row, normalize_governor_id
from versioning import versioned

logger = logging.getLogger(__name__)
bot: ext_commands.Bot | None = None
ACCOUNT_ORDER = ["Main"] + [f"Alt {i}" for i in range(1, 6)] + [f"Farm {i}" for i in range(1, 11)]


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
    return await asyncio.to_thread(load_registry)


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


def register_stats(bot_instance: ext_commands.Bot) -> None:
    global bot
    bot = bot_instance

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
        kvk_no: int = discord.Option(int, "KVK number (0 = current)", required=False, default=0),
        sheet_name: str = discord.Option(
            str,
            "Primary Google Sheet name",
            required=False,
            default=KVK_SHEET_NAME,
        ),
        create_primary: bool = discord.Option(
            bool,
            "Create/write the primary KVK sheet",
            required=False,
            default=True,
        ),
        export_pass4: bool = discord.Option(
            bool,
            "Export Pass 4 data",
            required=False,
            default=True,
        ),
        export_altar: bool = discord.Option(
            bool,
            "Export Altar data",
            required=False,
            default=True,
        ),
        export_pass7: bool = discord.Option(
            bool,
            "Export Pass 7 data",
            required=False,
            default=True,
        ),
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
    async def player_stats_command(
        ctx,
        governor_id: int = discord.Option(
            int,
            "Governor ID (optional if using name)",
            required=False,
            default=0,
        ),
        name: str = discord.Option(
            str,
            "Partial governor name (optional if using ID)",
            required=False,
            default="",
        ),
    ):
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
    async def kvk_export_all(
        ctx,
        kvk_no: int = discord.Option(int, "KVK number (0 = current)", required=False, default=0),
        sheet_name: str = discord.Option(
            str,
            "Primary Google Sheet name",
            required=False,
            default=KVK_SHEET_NAME,
        ),
    ):
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
    async def kvk_recompute(
        ctx,
        kvk_no: int = discord.Option(int, "KVK number (0 = current)", required=False, default=0),
    ):
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
    async def kvk_list_scans(
        ctx,
        kvk_no: int = discord.Option(int, "KVK number (0 = current)", required=False, default=0),
        limit: int = discord.Option(
            int,
            "How many recent scans to show",
            required=False,
            default=20,
        ),
    ):
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
    async def kvk_window_preview(
        ctx,
        kvk_no: int = discord.Option(int, "KVK number (0 = current)", required=False, default=0),
    ):
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
