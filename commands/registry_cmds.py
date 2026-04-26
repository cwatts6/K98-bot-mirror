# commands/registry_cmds.py
from __future__ import annotations

import asyncio
from decimal import Decimal, InvalidOperation
import io
import logging
import re
from typing import Any

import discord
from discord.ext import commands as ext_commands

from account_picker import ACCOUNT_ORDER
from bot_config import GUILD_ID
from core.interaction_safety import safe_command, safe_defer
from decoraters import is_admin_and_notify_channel, track_usage
from registry.governor_registry import (
    ConfirmRemoveView,
    ModifyGovernorView,
    RegisterGovernorView,
    load_registry,
)
from registry.registry_io import (
    apply_import_plan,
    build_error_csv_bytes,
    build_error_xlsx_bytes,
    export_registration_audit_files,
    export_registration_audit_xlsx_bytes,
    parse_csv_bytes,
    parse_xlsx_bytes,
    prepare_import_plan,
    rows_to_xlsx_bytes,
)
import registry.registry_service as registry_service
from registry.registry_service import VALID_ACCOUNT_TYPES
import target_utils
from ui.views.admin_views import ConfirmImportView
from ui.views.registry_views import MyRegsActionView
from versioning import versioned

logger = logging.getLogger(__name__)

def register_registry(bot: ext_commands.Bot) -> None:

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
            m = re.search(r"\d{15,22}", str(text))
            return int(m.group(0)) if m else None
        except Exception:
            return None

    # --- shared attachment parser ---
    def _parse_attachment(raw: bytes, ftype: str) -> list[dict]:
        """Parse CSV or XLSX bytes to rows. Returns empty list on failure."""
        if ftype == "csv":
            return parse_csv_bytes(raw)
        if ftype == "xlsx":
            try:
                return parse_xlsx_bytes(raw)
            except Exception:
                logger.exception("[IMPORT] XLSX parse failed, attempting CSV fallback")
                return parse_csv_bytes(raw)
        # unknown: try CSV first, then XLSX
        rows = parse_csv_bytes(raw)
        if not rows:
            try:
                rows = parse_xlsx_bytes(raw)
            except Exception:
                rows = []
        return rows

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

    async def _account_type_all_ac(ctx: discord.AutocompleteContext):
        all_types = [
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
            "Farm 11",
            "Farm 12",
            "Farm 13",
            "Farm 14",
            "Farm 15",
            "Farm 16",
            "Farm 17",
            "Farm 18",
            "Farm 19",
            "Farm 20",
        ]
        prefix = (ctx.value or "").lower()
        if prefix:
            return [t for t in all_types if t.lower().startswith(prefix)][:25]
        return all_types[:25]

    @bot.slash_command(
        name="register_governor",
        description="Register one of your accounts by Governor ID.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.06")
    @safe_command
    @track_usage()
    async def register_governor(
        ctx: discord.ApplicationContext,
        account_type: str = discord.Option(
            str,
            "Choose account type",
            autocomplete=_account_type_all_ac,
        ),
        governor_id: str = discord.Option(str, "Your in-game Governor ID"),
    ):
        await safe_defer(ctx, ephemeral=True)

        # Validate account type (autocomplete does not enforce server-side)
        if account_type not in VALID_ACCOUNT_TYPES:
            await ctx.interaction.edit_original_response(
                content=(
                    f"❌ `{account_type}` is not a valid account type. "
                    "Please choose from the list (Main, Alt 1–5, Farm 1–20)."
                ),
                embed=None,
                view=None,
            )
            return

        # Validate numeric GovernorID
        gid_raw = (governor_id or "").strip()
        if not gid_raw.isdigit():
            await ctx.interaction.edit_original_response(
                content=(
                    "❌ Please enter a **numeric** Governor ID (e.g., `2441482`).\n"
                    "Tip: try `/mygovernorid` to look it up from your name."
                ),
                embed=None,
                view=None,
            )
            return
        gid = gid_raw

        # Match against cached roster — read through module to survive cache refreshes
        # Warm the cache if empty — guards against cold start or failed background refresh
        _cache_rows = (
            (target_utils._name_cache or {}).get("rows", [])
            if isinstance(target_utils._name_cache, dict)
            else []
        )
        if not _cache_rows:
            try:
                await target_utils.refresh_name_cache_from_sql()
            except Exception:
                logger.exception("[register_governor] name cache warm failed")

        all_rows = (
            (target_utils._name_cache or {}).get("rows", [])
            if isinstance(target_utils._name_cache, dict)
            else []
        )
        logger.info(
            "[DEBUG] name_cache rows=%d last_updated=%s",
            len(all_rows),
            target_utils._name_cache.get("last_updated", 0),
        )
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

        # Hand off to the confirmation view.
        # Duplicate ownership checks are enforced atomically by sp_Registry_Insert
        # when the user confirms — no pre-scan of the full registry needed here.
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
    @versioned("v1.06")
    @safe_command
    @track_usage()
    async def modify_registration(
        ctx: discord.ApplicationContext,
        account_type: str = discord.Option(
            str,
            "Which account do you want to update or REMOVE?",
            autocomplete=_account_type_ac,  # keep existing — filters to user's registered slots
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

        from target_utils import _name_cache

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

    # === Normal command (member picker OR raw ID) ===
    @bot.slash_command(
        name="remove_registration",
        description="Admin-only: Remove a registered Governor account from a user.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v2.00")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def remove_registration(
        ctx: discord.ApplicationContext,
        account_type: str = discord.Option(
            str, "Which account to remove", autocomplete=_account_type_ac, required=True
        ),
        discord_user: discord.User = discord.Option(
            discord.User, "Pick a server user (if present)", required=False
        ),
        user_id: str = discord.Option(str, "Or paste a Discord user ID", required=False),
    ):
        await safe_defer(ctx, ephemeral=True)

        target_user_id = (
            discord_user.id if isinstance(discord_user, discord.User) else _parse_user_id(user_id)
        )
        if not target_user_id:
            await ctx.interaction.edit_original_response(
                content="❌ Please pick a user **or** paste a valid Discord ID."
            )
            return

        target_display = (
            discord_user.mention
            if isinstance(discord_user, discord.User)
            else f"`{target_user_id}`"
        )

        from registry.registry_service import get_user_accounts, remove_governor

        # Pre-check: confirm slot exists so we can give a clear message before acting
        accounts = get_user_accounts(target_user_id)
        if account_type not in accounts:
            await ctx.interaction.edit_original_response(
                content=f"⚠️ `{account_type}` is not registered for {target_display}."
            )
            return

        gov_name = accounts[account_type].get("GovernorName", "Unknown")
        gov_id = accounts[account_type].get("GovernorID", "Unknown")

        ok, err = remove_governor(
            discord_user_id=target_user_id,
            account_type=account_type,
            removed_by=ctx.user.id,
        )

        if not ok:
            await ctx.interaction.edit_original_response(
                content=f"❌ {err or 'Failed to remove registration.'}"
            )
            return

        logger.info(
            "[ADMIN] %s removed %s (%s – ID: %s) from %s",
            ctx.user,
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

    @bot.slash_command(
        name="remove_registration_by_id",
        description="Admin: remove a registered account by Discord ID (works if user not in server)",
        guild_ids=[GUILD_ID],
    )
    @versioned("v2.00")
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

        from registry.registry_service import get_user_accounts, remove_governor

        accounts = get_user_accounts(target_id)
        if not accounts:
            await ctx.interaction.edit_original_response(
                content=f"⚠️ No registry entry found for ID `{target_id}`."
            )
            return

        if account_type not in accounts:
            await ctx.interaction.edit_original_response(
                content=f"⚠️ `{account_type}` is not registered for ID `{target_id}`."
            )
            return

        gov_name = accounts[account_type].get("GovernorName", "Unknown")
        gov_id = accounts[account_type].get("GovernorID", "Unknown")

        ok, err = remove_governor(
            discord_user_id=target_id,
            account_type=account_type,
            removed_by=ctx.user.id,
        )

        if not ok:
            await ctx.interaction.edit_original_response(
                content=f"❌ {err or 'Failed to remove registration.'}"
            )
            return

        logger.info(
            "[ADMIN] %s removed %s (%s – ID: %s) from DiscordID %s",
            ctx.user,
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

    # === ID-only cleanup command (bypasses Discord USER validation entirely) ===

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
    @versioned("v2.00")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def admin_register_governor(
        ctx: discord.ApplicationContext,
        discord_user: discord.User = discord.Option(discord.User, "Player's Discord account"),
        account_type: str = discord.Option(
            str,
            "Account type",
            autocomplete=_account_type_all_ac,
        ),
        governor_id: str = discord.Option(str, "Governor ID to register"),
    ):
        await safe_defer(ctx, ephemeral=True)

        # Validate account type (autocomplete does not enforce server-side)
        if account_type not in VALID_ACCOUNT_TYPES:
            await ctx.interaction.edit_original_response(
                content=(
                    f"❌ `{account_type}` is not a valid account type. "
                    "Please choose from the list (Main, Alt 1–5, Farm 1–20)."
                ),
                embed=None,
                view=None,
            )
            return

        # Validate GovernorID is numeric
        gid = (governor_id or "").strip()
        if not gid.isdigit():
            await ctx.interaction.edit_original_response(
                content=(
                    "❌ Please enter a **numeric** Governor ID (e.g., `2441482`).\n"
                    "Tip: try `/mygovernorid` to look it up from your name."
                ),
                embed=None,
                view=None,
            )
            return

        # Validate governor exists in cache — read through module to survive cache refreshes
        all_rows = (
            (target_utils._name_cache or {}).get("rows", [])
            if isinstance(target_utils._name_cache, dict)
            else []
        )
        row = next((r for r in all_rows if str(r.get("GovernorID", "")).strip() == gid), None)
        if not row:
            await ctx.interaction.edit_original_response(
                content=(
                    f"❌ Governor ID `{gid}` not found in the database. "
                    "Ask the player to try `/mygovernorid`."
                ),
                embed=None,
                view=None,
            )
            return

        gov_name = row.get("GovernorName", "Unknown")

        # Write via service layer.
        # admin_register_or_replace overwrites an existing slot if present,
        # rather than rejecting with RC_DUPE_SLOT.
        from registry.registry_service import admin_register_or_replace

        ok, err = admin_register_or_replace(
            target_discord_user_id=discord_user.id,
            target_discord_name=str(discord_user),
            account_type=account_type,
            governor_id=gid,
            governor_name=gov_name,
            admin_discord_id=ctx.user.id,
        )

        if not ok:
            await ctx.interaction.edit_original_response(content=f"❌ {err}", embed=None, view=None)
            return

        logger.info(
            "[ADMIN] %s registered GovernorID=%s (%s) as %s for %s",
            ctx.user,
            gid,
            gov_name,
            account_type,
            discord_user,
        )

        # DM the player if possible
        try:
            embed = discord.Embed(
                title="✅ Registration Added",
                description=(
                    f"Your **{account_type}** has been set to "
                    f"**{gov_name}** (`{gid}`) by an admin."
                ),
                color=0x2ECC71,
            )
            await discord_user.send(embed=embed)
        except discord.Forbidden:
            pass

        await ctx.interaction.edit_original_response(
            content=(
                f"✅ Registered **{gov_name}** (`{gid}`) as "
                f"**{account_type}** for {discord_user.mention}."
            ),
            embed=None,
            view=None,
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
        from decimal import ROUND_HALF_UP

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

        # ---------- SQL via audit_dal ----------
        from registry.dal.audit_dal import get_active_players

        try:
            sql_rows = await asyncio.to_thread(get_active_players)
        except Exception as e:
            logger.exception("[registration_audit] SQL fetch failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to query SQL view `v_Active_Players`: `{type(e).__name__}: {e}`"
            )
            return

        # ---------- Registry & guild helpers ----------
        try:
            registry = registry_service.load_registry_as_dict(allow_stale_on_error=False)
        except Exception as e:
            logger.exception("[registration_audit] load_registry_as_dict failed")
            await ctx.interaction.edit_original_response(
                content=(
                    "❌ Could not load the registry from SQL. "
                    "The audit cannot run until the database is available.\n"
                    f"`{type(e).__name__}: {e}`"
                )
            )
            return
        if not registry:
            # load_registry_as_dict() returned empty — treat as failure
            # since an empty registry at audit time is almost certainly wrong.
            logger.error(
                "[registration_audit] load_registry_as_dict returned empty dict — "
                "possible SQL failure; aborting audit to avoid misleading output."
            )
            await ctx.interaction.edit_original_response(
                content=(
                    "⚠️ The registry appears empty. This may indicate a SQL connectivity issue.\n"
                    "The audit has been aborted to prevent misleading results. "
                    "Please check the bot logs and retry."
                )
            )
            return

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

        files = export_registration_audit_files(registry, members_info, sql_rows)
        # Also produce an XLSX workbook with three sheets
        try:
            xlsx_bytes = export_registration_audit_xlsx_bytes(registry, members_info, sql_rows)
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
                            gid_norm = _norm_gid(gid)
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

        try:
            registry = registry_service.load_registry_as_dict(allow_stale_on_error=False)
        except Exception as e:
            logger.exception("[bulk_export_registrations] load_registry_as_dict failed")
            await ctx.interaction.edit_original_response(
                content=(
                    "❌ Could not load the registry from SQL. "
                    "Export cannot proceed until the database is available.\n"
                    f"`{type(e).__name__}: {e}`"
                )
            )
            return
        if not registry:
            logger.error(
                "[bulk_export_registrations] load_registry_as_dict returned empty dict — "
                "possible SQL failure; aborting export."
            )
            await ctx.interaction.edit_original_response(
                content=(
                    "⚠️ The registry appears empty. This may indicate a SQL connectivity issue.\n"
                    "Export has been aborted to prevent producing an empty file. "
                    "Please check the bot logs and retry."
                )
            )
            return

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
            uid_str = str(uid).strip()
            member = cached_members.get(uid_str)
            if member is None:
                missing_ids.add(uid_str)

            accounts = data.get("accounts", {})
            if not isinstance(accounts, dict):
                continue

            for acc_type, details in accounts.items():
                gov_id_raw = str(details.get("GovernorID", "")).strip()
                rows.append(
                    {
                        "discord_id": uid_str,
                        "discord_id_excel": excel_safe_formula(uid_str),
                        "discord_user": data.get("discord_name", uid_str),
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
            xlsx_bytes = rows_to_xlsx_bytes(rows, headers, sheet_name="registrations")
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

        logger.info(
            "[EXPORT] bulk export by %s (%s) — %d registration row(s)",
            ctx.user,
            ctx.user.id,
            len(rows),
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

    @bot.slash_command(
        name="bulk_import_registrations_dryrun",
        description="Admin: validate a registrations CSV without saving.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v2.00")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def bulk_import_registrations_dryrun(ctx: discord.ApplicationContext):
        deferred = await safe_defer(ctx, ephemeral=True)

        attach, ftype = await _await_csv_attachment(
            ctx,
            "📎 Please upload the **CSV or XLSX file** now (as a new message in this channel).\n"
            "Required columns: `discord_user_id`, `account_type`, `governor_id`.\n"
            "Optional: `governor_name`.\n"
            "_Tip: export from `/bulk_export_registrations` or `/registration_audit` and edit that file._",
        )
        if not attach:
            return

        logger.info(
            "[IMPORT] dry-run started by %s (%s) — file: %s (%d bytes)",
            ctx.user,
            ctx.user.id,
            attach.filename,
            attach.size,
        )

        try:
            raw = await attach.read()
        except Exception as e:
            logger.exception("[IMPORT] dry-run failed reading attachment")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to read uploaded file: {type(e).__name__}: {e}"
            )
            return

        rows = _parse_attachment(raw, ftype)
        if not rows:
            await ctx.interaction.edit_original_response(
                content="❌ File could not be parsed or appears to have no data."
            )
            return

        from registry.registry_service import load_registry_as_dict

        try:
            existing = load_registry_as_dict()
        except Exception as e:
            logger.exception("[IMPORT] load_registry_as_dict failed")
            await ctx.interaction.edit_original_response(
                content=(
                    "❌ Could not load the registry from SQL. "
                    "Import cannot proceed until the database is available.\n"
                    f"`{type(e).__name__}: {e}`"
                )
            )
            return

        changes, errors, warnings, error_rows = prepare_import_plan(rows, existing)

        logger.info(
            "[IMPORT] dry-run complete — file: %s rows_parsed: %d proposed_changes: %d "
            "errors: %d warnings: %d actor: %s (%s)",
            attach.filename,
            len(rows),
            len(changes),
            len(errors),
            len(warnings),
            ctx.user,
            ctx.user.id,
        )

        send = ctx.followup.send if deferred else ctx.respond

        if errors:
            err_csv_bytes = build_error_csv_bytes(error_rows)
            err_xlsx_bytes = None
            try:
                err_xlsx_bytes = build_error_xlsx_bytes(error_rows)
            except Exception:
                logger.exception("[IMPORT] failed to build XLSX error workbook")

            files = [discord.File(err_csv_bytes, filename="import_errors.csv")]
            if err_xlsx_bytes:
                files.append(discord.File(err_xlsx_bytes, filename="import_errors.xlsx"))

            short_msg = (
                f"❌ Validation failed: {len(errors)} error(s). "
                "Correct the highlighted rows and re-upload. See attached file(s) for details."
            )
            if len(errors) <= 10:
                content = short_msg + "\n\nErrors:\n" + "\n".join(errors[:10])
                if len(content) <= 1900:
                    await send(content=content, files=files, ephemeral=True)
                    return
            await send(content=short_msg, files=files, ephemeral=True)
            return

        # Build preview embed
        preview = [
            f"Row {c.get('source_row')}: {c['discord_id']} | "
            f"{c['account_type']} → {c['governor_id']}"
            for c in changes[:20]
        ]
        embed = discord.Embed(
            title="✅ Dry-Run Validation Passed",
            color=discord.Color.green(),
        )
        embed.description = (
            f"**{len(changes)} change(s) proposed.**\n"
            f"Conflict behaviour: **Overwrite** — existing active slots will be superseded "
            f"and replaced with the imported values.\n\n"
            + "\n".join(preview)
            + (f"\n… and {len(changes) - 20} more" if len(changes) > 20 else "")
        )
        if warnings:
            embed.add_field(
                name=f"⚠️ Warnings ({len(warnings)})",
                value="\n".join(warnings[:10])
                + (f"\n… and {len(warnings) - 10} more" if len(warnings) > 10 else ""),
                inline=False,
            )
        embed.set_footer(text="Click Confirm to apply, or Cancel to abort.")

        async def _apply_import(interaction: discord.Interaction):
            # Reload existing registry fresh at confirm time — avoids stale
            # dict from dry-run phase, though SQL constraints protect integrity
            # regardless.
            fresh_existing = load_registry()
            try:
                _new_registry, summary, apply_errors = apply_import_plan(
                    changes, fresh_existing, dry_run=False
                )
                if apply_errors:
                    logger.warning(
                        "[IMPORT] %d row(s) failed during apply: %s",
                        len(apply_errors),
                        apply_errors,
                    )
            except Exception as e:
                logger.exception("[IMPORT] apply_import_plan failed at confirm")
                try:
                    await interaction.followup.send(
                        f"❌ Failed to apply import: {type(e).__name__}: {e}",
                        ephemeral=True,
                    )
                except Exception:
                    pass
                return

            logger.info(
                "[IMPORT] confirmed and applied by %s (%s) — %d change(s) from file: %s",
                interaction.user,
                interaction.user.id,
                len(summary),
                attach.filename,
            )

            text = f"✅ Import applied: {len(summary)} change(s) made.\n" + "\n".join(summary[:50])
            if len(text) <= 1900:
                await interaction.followup.send(text, ephemeral=True)
            else:
                bio = io.BytesIO(("\n".join(summary)).encode("utf-8"))
                await interaction.followup.send(
                    f"✅ Import applied: {len(summary)} change(s). Full summary attached.",
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
            await send(embed=embed, ephemeral=True)

    # ---------- IMPORT (COMMIT) ----------
    @bot.slash_command(
        name="bulk_import_registrations",
        description="Admin: import registrations from CSV or XLSX (commits changes).",
        guild_ids=[GUILD_ID],
    )
    @versioned("v2.00")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def bulk_import_registrations(ctx: discord.ApplicationContext):
        deferred = await safe_defer(ctx, ephemeral=True)

        attach, ftype = await _await_csv_attachment(
            ctx,
            "📎 Please upload the **CSV or XLSX file** now (as a new message in this channel).\n"
            "Required columns: `discord_user_id`, `account_type`, `governor_id`.\n"
            "Optional: `governor_name`.\n"
            "_Tip: export from `/bulk_export_registrations` or `/registration_audit` and edit that file._",
        )
        if not attach:
            return

        logger.info(
            "[IMPORT] live import started by %s (%s) — file: %s (%d bytes)",
            ctx.user,
            ctx.user.id,
            attach.filename,
            attach.size,
        )

        try:
            raw = await attach.read()
        except Exception as e:
            logger.exception("[IMPORT] failed reading attachment")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to read uploaded file: {type(e).__name__}: {e}"
            )
            return

        rows = _parse_attachment(raw, ftype)
        if not rows:
            await ctx.interaction.edit_original_response(
                content="❌ File could not be parsed or appears to have no data."
            )
            return

        from registry.registry_service import load_registry_as_dict

        try:
            existing = load_registry_as_dict()
        except Exception as e:
            logger.exception("[IMPORT] load_registry_as_dict failed")
            await ctx.interaction.edit_original_response(
                content=(
                    "❌ Could not load the registry from SQL. "
                    "Import cannot proceed until the database is available.\n"
                    f"`{type(e).__name__}: {e}`"
                )
            )
            return

        changes, errors, warnings, error_rows = prepare_import_plan(rows, existing)

        send = ctx.followup.send if deferred else ctx.respond

        if errors:
            err_csv_bytes = build_error_csv_bytes(error_rows)
            files = [discord.File(err_csv_bytes, filename="import_errors.csv")]
            try:
                err_xlsx_bytes = build_error_xlsx_bytes(error_rows)
                files.append(discord.File(err_xlsx_bytes, filename="import_errors.xlsx"))
            except Exception:
                logger.exception("[IMPORT] failed to build XLSX error workbook")

            logger.warning(
                "[IMPORT] live import aborted — validation failed: %d error(s) "
                "actor: %s (%s) file: %s",
                len(errors),
                ctx.user,
                ctx.user.id,
                attach.filename,
            )

            short_msg = (
                f"❌ Validation failed: {len(errors)} error(s). "
                "No changes have been applied. Correct the highlighted rows and re-upload."
            )
            if len(errors) <= 10:
                content = short_msg + "\n\nErrors:\n" + "\n".join(errors[:10])
                if len(content) <= 1900:
                    await send(content=content, files=files, ephemeral=True)
                    return
            await send(content=short_msg, files=files, ephemeral=True)
            return

        try:
            _new_registry, summary, apply_errors = apply_import_plan(
                changes, existing, dry_run=False
            )
            text = f"✅ Import applied: {len(summary)} change(s) made.\n" + "\n".join(summary[:50])
            if apply_errors:
                text += f"\n\n⚠️ {len(apply_errors)} row(s) failed:\n" + "\n".join(
                    f"- {e}" for e in apply_errors[:20]
                )
        except Exception as e:
            logger.exception("[IMPORT] apply_import_plan failed")
            await send(f"❌ Failed to apply import: {type(e).__name__}: {e}", ephemeral=True)
            return

        logger.info(
            "[IMPORT] live import complete — %d change(s) applied, %d warning(s) "
            "actor: %s (%s) file: %s",
            len(summary),
            len(warnings),
            ctx.user,
            ctx.user.id,
            attach.filename,
        )

        text = f"✅ Import applied: {len(summary)} change(s) made.\n" + "\n".join(summary[:50])
        if warnings:
            text += "\n\n⚠️ Warnings:\n" + "\n".join(f"- {w}" for w in warnings[:20])

        if len(text) <= 1900:
            await send(text, ephemeral=True)
        else:
            full = "\n".join(summary)
            if warnings:
                full += "\n\nWarnings:\n" + "\n".join(warnings)
            bio = io.BytesIO(full.encode("utf-8"))
            await send(
                content=f"✅ Import applied: {len(summary)} change(s). Full summary attached.",
                file=discord.File(bio, filename="import_summary.txt"),
                ephemeral=True,
            )
