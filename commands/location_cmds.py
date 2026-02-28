# commands/location_cmds.py
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import logging

import discord
from discord.ext import commands as ext_commands

from bot_config import GUILD_ID, LEADERSHIP_CHANNEL_ID, LOCATION_CHANNEL_ID, NOTIFY_CHANNEL_ID
from core.interaction_safety import safe_command, safe_defer
from decoraters import (
    _has_leadership_role,
    _is_admin,
    _is_allowed_channel,
    is_admin_and_notify_channel,
    track_usage,
)
from location_importer import load_staging_and_merge, parse_output_csv
from profile_cache import (
    autocomplete_choices,
    get_profile_cached,
    search_by_governor_name,
    warm_cache,
)
from ui.views.location_views import (
    LocationSelectView,
    RefreshLocationView,
    configure_location_views,
)
from versioning import versioned

logger = logging.getLogger(__name__)
UTC = UTC
ALLOWED_CHANNEL_IDS = {int(cid) for cid in (NOTIFY_CHANNEL_ID, LEADERSHIP_CHANNEL_ID) if cid}

# --- Location refresh coordination (global, in-process) ---
_location_refresh_lock = asyncio.Lock()
_location_refresh_event = asyncio.Event()
_last_location_refresh_utc: datetime | None = None


def signal_location_refresh_complete() -> None:
    """Called by the CSV import flow when the location cache has been updated."""
    try:
        _location_refresh_event.set()
    except Exception:
        logger.exception("Failed to signal location refresh completion")


async def _send_find_all_to_location_channel(
    bot: ext_commands.Bot, *, interaction: discord.Interaction
) -> tuple[bool, str]:
    channel = bot.get_channel(LOCATION_CHANNEL_ID)
    if not channel:
        try:
            channel = await bot.fetch_channel(LOCATION_CHANNEL_ID)
        except Exception as e:
            return False, f"Could not resolve LOCATION_CHANNEL_ID: {e}"
    try:
        await channel.send("find-all")
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


async def _notify_location_refresh_timeout(
    bot: ext_commands.Bot, interaction: discord.Interaction
) -> None:
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


async def governor_name_autocomplete(ctx: discord.AutocompleteContext):
    try:
        q = (ctx.value or "").strip()
        if len(q) < 2:
            return []

        try:
            OptionChoice = discord.OptionChoice
        except AttributeError:
            from discord import OptionChoice

        choices = autocomplete_choices(q, limit=25)
        return [OptionChoice(name=label, value=value) for label, value in choices]
    except Exception:
        return []


def register_location(bot: ext_commands.Bot) -> None:
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
        on_refresh_timeout=lambda interaction: _notify_location_refresh_timeout(bot, interaction),
    )

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
