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
    GUILD_ID,
    KVK_CRYSTALTECH_CHANNEL_ID,
    KVK_TARGET_CHANNEL_ID,
    LEADERSHIP_CHANNEL_ID,
    NOTIFY_CHANNEL_ID,
)
from commands.crystaltech_flow import run_crystaltech_flow as run_crystaltech_flow_service
from commands.deprecation_helpers import CommandRedirect, send_deprecated_command_redirect
from commands.player_profile_flow import send_profile_to_channel as send_profile_to_channel_service
from decoraters import (
    admin_or_leadership_in_allowed_channels,
    channel_only,
    track_usage,
)

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
from registry.account_slots import ACCOUNT_ORDER
from registry.registry_service import load_registry_as_dict
from services.governor_account_service import get_account_summary_for_user
from services.profile_lookup_service import resolve_profile_lookup
from target_utils import (
    autocomplete_governor_names,
    lookup_governor_id,
)
from ui.views.kvk_personal_views import (
    FuzzySelectView,
    MyKVKStatsSelectView,  # noqa: F401 — re-exported for Commands.py star-import consumers
    PostLookupActions,
    TargetLookupView,  # noqa: F401 — kept for external importers and smoke tests
)
from ui.views.registry_views import (
    GovernorSelectView,
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
ALLOWED_CHANNEL_IDS = {int(cid) for cid in (NOTIFY_CHANNEL_ID, LEADERSHIP_CHANNEL_ID) if cid}

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
        await safe_defer(ctx, ephemeral=True)
        await send_deprecated_command_redirect(
            ctx,
            CommandRedirect(
                old_path="/mykvktargets",
                new_path="/kvk targets",
                detail="The new command uses the modern KVK target card and keeps the same optional Governor ID flow.",
            ),
            ephemeral=True,
        )
        return

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
    @admin_or_leadership_in_allowed_channels(ALLOWED_CHANNEL_IDS)
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

        # --- Resolve target (accept autocomplete value as ID) ---
        lookup = resolve_profile_lookup(governor_id=governor_id, governor_name=governor_name)
        if lookup.status == "not_found":
            await ctx.respond(lookup.message, ephemeral=True)
            return
        if lookup.status == "matches":
            governor_matches = [(name, governor_id) for name, governor_id, *_ in lookup.matches]
            try:
                view = GovernorSelectView(governor_matches, author_id=ctx.user.id)
            except TypeError:
                view = GovernorSelectView(governor_matches)
            await ctx.respond(lookup.message, view=view, ephemeral=True)
            return
        target_id: int | None = lookup.governor_id

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
