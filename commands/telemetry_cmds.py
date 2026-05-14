# commands/telemetry_cmds.py

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import logging
import os

# ——— Standard library ———
import discord
from discord.ext import commands as ext_commands  # avoid name conflict
from dotenv import load_dotenv

# ——— Third-party ———
from bot_config import (
    ARK_SETUP_CHANNEL_ID,
    GUILD_ID,
    KVK_CRYSTALTECH_CHANNEL_ID,
    KVK_TARGET_CHANNEL_ID,
    LEADERSHIP_CHANNEL_ID,
    NOTIFY_CHANNEL_ID,
)
from commands.crystaltech_flow import run_crystaltech_flow as run_crystaltech_flow_service
from commands.player_profile_flow import send_profile_to_channel as send_profile_to_channel_service
from decoraters import (
    _has_leadership_role,
    _is_admin,
    _is_allowed_channel,
    channel_only,
    track_usage,
)
from kvk_ui import make_kvk_targets_view
from stats_cache_helpers import load_last_kvk_map

# Provide a standard UTC alias
UTC = UTC

# ——— Local modules ———
# Direct, canonical imports for account picker functionality
from account_picker import (
    AccountPickerView,  # canonical View class
    safe_build_unique_gov_options,
)
from core.interaction_safety import (
    global_cmd_error_handler,
    safe_command,
    safe_defer,
)
from logging_setup import CRASH_LOG_PATH, ERROR_LOG_PATH, FULL_LOG_PATH
from profile_cache import search_by_governor_name
from registry.account_slots import ACCOUNT_ORDER
from registry.registry_service import load_registry_as_dict
from services.governor_account_service import get_account_summary_for_user
from target_utils import (
    _name_cache,
    autocomplete_governor_names,
    lookup_governor_id,
    run_target_lookup,
)
from ui.views.kvk_personal_views import (
    FuzzySelectView,
    MyKVKStatsSelectView,  # noqa: F401 — re-exported for Commands.py star-import consumers
    PostLookupActions,
    TargetLookupView,  # noqa: F401 — kept for external importers and smoke tests
)
from ui.views.registry_views import (
    GovernorSelectView,
    GovNameModal,
    RegisterStartView,
    configure_registry_views,
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


# ACCOUNT_ORDER imported from account_picker — single canonical definition.

# --- SHADOW GUARD (temporary; remove after diagnosis) ---
if os.getenv("DEBUG_SHADOW") == "1":
    import builtins as _bi

    for _n in ("str", "bool", "int"):
        _g = globals().get(_n)
        if _g is not None and _g is not getattr(_bi, _n):
            logger.error("[SHADOW] %s is shadowed: type=%s value=%r", _n, type(_g), _g)
# ---------------------------------------------------------

load_dotenv()

# Safer construction (avoids int(None))
ALLOWED_CHANNEL_IDS = {
    int(cid) for cid in (NOTIFY_CHANNEL_ID, LEADERSHIP_CHANNEL_ID, ARK_SETUP_CHANNEL_ID) if cid
}

start_bot_time = datetime.now(UTC)


async def async_registry_dict():
    return await asyncio.to_thread(load_registry_as_dict)


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


configure_registry_views(
    async_load_registry=async_registry_dict,
    lookup_governor_id=lookup_governor_id,
    target_lookup_view_factory=lambda matches, author_id: FuzzySelectView(
        matches, author_id, show_targets=True
    ),
    name_cache_getter=lambda: _name_cache,
    send_profile_to_channel=send_profile_to_channel_service,
    account_order_getter=lambda: ACCOUNT_ORDER,
)


send_profile_to_channel = send_profile_to_channel_service
run_crystaltech_flow = run_crystaltech_flow_service


def register_commands(bot_instance):
    global bot
    bot = bot_instance

    logger.info("[COMMANDS] Registering commands...")
    # Register global command error handler
    bot.add_listener(global_cmd_error_handler, "on_application_command_error")

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
                account_summary = await get_account_summary_for_user(interaction.user.id)
                if not account_summary.ok:
                    await interaction.followup.send(
                        "Registry is temporarily unavailable. Please try again later.",
                        ephemeral=True,
                    )
                    return
                free_slots = account_summary.free_slots()

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
            account_summary = await get_account_summary_for_user(ctx.user.id)
            if not account_summary.ok:
                raise RuntimeError(account_summary.error or "registry unavailable")
        except Exception:
            logger.exception("[/mykvktargets] load_registry failed")
            await ctx.followup.send(
                "⚠️ Couldn’t load your registered accounts. Provide `governorid` or try again later.",
                ephemeral=True,
            )
            return

        options = safe_build_unique_gov_options(account_summary)

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
                # architecture-check: allow
                await ctx.followup.send(
                    "Select an account to view its KVK targets:",  # architecture-check: allow
                    view=view,
                    ephemeral=only_me,
                )
            # architecture-check: allow
            except Exception:
                logger.exception(
                    "[/mykvktargets] Failed to create/send account selector view"  # architecture-check: allow
                )
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
        # architecture-check: allow
        except Exception:
            logger.exception(
                "[/mykvktargets] Failed to create/send empty account picker view"  # architecture-check: allow
            )
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
                actions = PostLookupActions(
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
                view = FuzzySelectView(matches, ctx.user.id, show_targets=True)
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
            autocomplete=autocomplete_governor_names,
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
            await send_profile_to_channel_service(ctx.interaction, target_id, ctx.channel)
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
            await run_crystaltech_flow_service(
                ctx.interaction, governorid.strip(), ephemeral=only_me
            )
            return

        # 2) Registered accounts path — reuse same registry logic & helpers as /mykvktargets
        try:
            account_summary = await get_account_summary_for_user(ctx.user.id)
            if not account_summary.ok:
                raise RuntimeError(account_summary.error or "registry unavailable")
        except Exception:
            logger.exception("[/mykvkcrystaltech] load_registry failed")
            await ctx.followup.send(
                "⚠️ Couldn’t load your registered accounts. Provide `governorid` or try again later.",
                ephemeral=only_me,
            )
            return

        # Use canonical builder (safe fallback included)
        options = safe_build_unique_gov_options(account_summary)

        if options:
            if len(options) == 1:
                only_gid = options[0].value
                await run_crystaltech_flow_service(ctx.interaction, only_gid, ephemeral=only_me)
                return

            # Build the AccountPickerView directly (no lazy-resolve helper anymore)
            async def _on_select(i, gid, ep):
                # ensure we pass the interaction into run_crystaltech_flow
                await run_crystaltech_flow_service(i, gid, ephemeral=ep)

            # architecture-check: allow
            view = AccountPickerView(
                ctx=ctx,
                options=options,
                on_select_governor=_on_select,
                heading="Select an account to manage its Crystal Tech:",  # architecture-check: allow
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
                await run_crystaltech_flow_service(i, gid, ephemeral=ep)

            # architecture-check: allow
            view = AccountPickerView(
                ctx=ctx,
                options=[],
                on_select_governor=_on_select,
                heading="Select an account to manage its Crystal Tech:",  # architecture-check: allow
                show_register_btn=True,
                ephemeral=only_me,
            )
            await ctx.followup.send(hint, view=view, ephemeral=only_me)


def register_telemetry(bot: ext_commands.Bot) -> None:
    register_commands(bot)
