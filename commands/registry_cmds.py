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

from bot_config import GUILD_ID
from constants import _conn
from core.interaction_safety import safe_command, safe_defer
from decoraters import is_admin_and_notify_channel, track_usage
import governor_registry
from governor_registry import (
    ConfirmRemoveView,
    ModifyGovernorView,
    RegisterGovernorView,
    load_registry,
    save_registry,
)
import registry_io
from registry_io import (
    apply_import_plan,
    parse_csv_bytes,
    parse_xlsx_bytes,
    prepare_import_plan,
)
from target_utils import _name_cache
from ui.views.admin_views import ConfirmImportView
from ui.views.registry_views import MyRegsActionView
from versioning import versioned

logger = logging.getLogger(__name__)

ACCOUNT_ORDER = ["Main"] + [f"Alt {i}" for i in range(1, 6)] + [f"Farm {i}" for i in range(1, 11)]


def register_registry(bot: ext_commands.Bot) -> None:
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
