# commands/registry_cmds.py
from __future__ import annotations

import asyncio
import logging
from typing import Any

import discord
from discord.ext import commands as ext_commands

from bot_config import GUILD_ID
from core.interaction_safety import safe_command, safe_defer
from decoraters import is_admin_and_notify_channel, track_usage
from registry.account_slots import ACCOUNT_ORDER
from registry.dal.audit_dal import get_active_players
from registry.governor_registry import (
    ConfirmRemoveView,
    ModifyGovernorView,
    RegisterGovernorView,
)
from registry.registry_command_service import (
    apply_import_changes,
    build_import_preview,
    build_import_summary_file_bytes,
    build_import_summary_text,
    build_registration_audit_payload,
    build_registration_export_payload,
    parse_attachment_bytes,
)
import registry.registry_service as registry_service
from registry.registry_service import (
    VALID_ACCOUNT_TYPES,
    admin_register_or_replace,
    get_user_accounts,
    remove_governor,
)
from services.governor_account_service import (
    filter_account_slots,
    get_accounts_for_user as get_user_accounts_async,
    parse_discord_user_id,
    registered_account_slots,
)
import target_utils
from ui.views.admin_views import ConfirmImportView
from ui.views.registry_views import MyRegsActionView
from versioning import versioned

logger = logging.getLogger(__name__)


def register_registry(bot: ext_commands.Bot) -> None:

    # --- helpers (reuse if already present) ---
    # --- UNIFIED autocomplete for account_type (works with both commands) ---
    async def _account_type_ac(ctx: discord.AutocompleteContext):
        try:
            # Prefer resolved member if present (for /remove_registration)
            opt_user = ctx.options.get("discord_user")
            if isinstance(opt_user, discord.User):
                target_id = opt_user.id
            else:
                # Fall back to the pasted ID field (works for both commands)
                target_id = parse_discord_user_id(ctx.options.get("user_id"))

            if not target_id:
                return filter_account_slots(ctx.value)

            lookup = await get_user_accounts_async(target_id)
            if not lookup.ok:
                return []
            return registered_account_slots(lookup.accounts, ctx.value)
        except Exception:
            return filter_account_slots(ctx.value)

    async def _account_type_all_ac(ctx: discord.AutocompleteContext):
        return filter_account_slots(ctx.value)

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

        matched_row = await target_utils.lookup_governor_row_by_id(gid)
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
        description="Modify or remove one of your registered Governor accounts.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.06")
    @safe_command
    @track_usage()
    async def modify_registration(
        ctx: discord.ApplicationContext,
        account_type: str = discord.Option(
            str,
            "Which account do you want to modify or remove?",
            autocomplete=_account_type_ac,  # keep existing — filters to user's registered slots
        ),
        new_governor_id: str = discord.Option(str, "New Governor ID to assign or REMOVE"),
    ):

        await safe_defer(ctx, ephemeral=True)

        # --- Load registry account state safely
        try:
            accounts_lookup = await get_user_accounts_async(ctx.user.id)
            if not accounts_lookup.ok:
                raise RuntimeError(accounts_lookup.error or "registry unavailable")
        except Exception as e:
            logger.exception("[modify_registration] get_user_accounts failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Could not load your registrations: `{type(e).__name__}: {e}`",
                embed=None,
                view=None,
            )
            return

        user_accounts = accounts_lookup.accounts

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

        # --- Modify flow: validate numeric GovernorID
        if not raw.isdigit():
            await ctx.interaction.edit_original_response(
                content="❌ Please enter a **numeric** Governor ID (or type `REMOVE` to remove). "
                "Tip: try `/mygovernorid` to look it up from your name.",
                embed=None,
                view=None,
            )
            return
        gid = raw

        matched_row = await target_utils.lookup_governor_row_by_id(gid)
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
        try:
            claimed_by_other = await asyncio.to_thread(
                registry_service.check_governor_claimed_by_other, gid, ctx.user.id
            )
        except Exception as e:
            logger.exception("[modify_registration] claimed check failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Could not validate Governor ID ownership: `{type(e).__name__}: {e}`",
                embed=None,
                view=None,
            )
            return
        if claimed_by_other:
            await ctx.interaction.edit_original_response(
                content=f"❌ This Governor ID `{gid}` is already registered to another user.",
                embed=None,
                view=None,
            )
            return

        gov_name = matched_row.get("GovernorName", "Unknown")
        view = ModifyGovernorView(ctx.user, account_type, gid, gov_name)
        await ctx.interaction.edit_original_response(
            content=f"⚙️ Modify `{account_type}` to **{gov_name}** (ID: `{gid}`)?",
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
            discord_user.id
            if isinstance(discord_user, discord.User)
            else parse_discord_user_id(user_id)
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

        # Pre-check: confirm slot exists so we can give a clear message before acting
        accounts = await asyncio.to_thread(get_user_accounts, target_user_id)
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

        target_id = parse_discord_user_id(user_id)
        if not target_id:
            await ctx.interaction.edit_original_response(
                content="❌ Please paste a valid Discord user ID (15–22 digits) or a mention."
            )
            return

        from registry.registry_service import get_user_accounts, remove_governor

        accounts = await asyncio.to_thread(get_user_accounts, target_id)
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

        try:
            registry: dict[str, Any] = (
                await asyncio.to_thread(registry_service.load_registry_as_dict) or {}
            )
        except Exception:
            logger.exception("[my_registrations] load_registry_as_dict failed")
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

        row = await target_utils.lookup_governor_row_by_id(gid)
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
        await safe_defer(ctx, ephemeral=True)

        guild: discord.Guild | None = ctx.guild
        if not guild:
            await ctx.interaction.edit_original_response(
                content="❌ This command must be used in a server."
            )
            return

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

        members_info: dict[str, dict] = {}
        for member in (m for m in guild.members if not getattr(m, "bot", False)):
            roles_str, top_role = role_names(member)
            members_info[str(member.id)] = {
                "discord_user": str(member),
                "roles": roles_str,
                "top_role": top_role,
            }
        missing_registered_uids = {
            str(uid).strip()
            for uid in (registry or {}).keys()
            if str(uid).strip() and str(uid).strip() not in members_info
        }
        for uid in missing_registered_uids:
            try:
                member = await guild.fetch_member(int(uid))
            except Exception:
                members_info[uid] = {"discord_user": uid, "roles": "", "top_role": ""}
                continue
            roles_str, top_role = role_names(member)
            members_info[uid] = {
                "discord_user": str(member),
                "roles": roles_str,
                "top_role": top_role,
            }

        audit_payload = build_registration_audit_payload(registry, members_info, sql_rows)

        logger.info(
            "[registration_audit] registered_accounts=%d unregistered_current=%d members_without_registration=%d",
            audit_payload.registered_accounts_total,
            audit_payload.unregistered_current_governors_count,
            audit_payload.members_without_registration_count,
        )

        # ---------- Summary embed ----------
        embed = discord.Embed(
            title="🧾 Registration Audit (Current Governors)", color=discord.Color.blurple()
        )
        embed.add_field(
            name="Registered accounts",
            value=f"{audit_payload.registered_accounts_total:,}",
            inline=True,
        )
        embed.add_field(
            name="Unregistered current governors (SQL)",
            value=f"{audit_payload.unregistered_current_governors_count:,}",
            inline=True,
        )
        embed.add_field(
            name="Discord members without registration",
            value=f"{audit_payload.members_without_registration_count:,}",
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
                discord.File(
                    audit_payload.files["registered_accounts.csv"],
                    filename="registered_accounts.csv",
                ),
                discord.File(
                    audit_payload.files["unregistered_current_governors.csv"],
                    filename="unregistered_current_governors.csv",
                ),
                discord.File(
                    audit_payload.files["members_without_registration.csv"],
                    filename="members_without_registration.csv",
                ),
            ]
            if audit_payload.xlsx_bytes:
                send_files.append(
                    discord.File(audit_payload.xlsx_bytes, filename="registration_audit.xlsx")
                )

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

        def role_names(member: discord.Member | None) -> tuple[str, str]:
            if member is None:
                return "", ""
            names = [r.name for r in member.roles if r.name != "@everyone"]
            roles_str = ";".join(names)
            top = member.top_role.name if names else ""
            return roles_str, top

        members_info: dict[str, dict] = {}
        cached_members: dict[str, discord.Member] = (
            {str(m.id): m for m in guild.members} if guild.members else {}
        )
        missing_ids = {
            str(uid).strip() for uid in registry.keys() if str(uid).strip() not in cached_members
        }
        fetched: dict[str, discord.Member | None] = {}
        for uid in missing_ids:
            try:
                fetched[uid] = await guild.fetch_member(int(uid))
            except Exception:
                fetched[uid] = None

        for uid, member in {**cached_members, **fetched}.items():
            roles_str, top = role_names(member)
            members_info[uid] = {"roles": roles_str, "top_role": top}

        export_payload = build_registration_export_payload(registry, members_info)
        if export_payload.row_count == 0:
            await ctx.interaction.edit_original_response(
                content="📭 No registrations found to export."
            )
            return

        await ctx.interaction.edit_original_response(
            content="📤 Exported current registrations (CSV and XLSX)."
        )
        send_files = [discord.File(export_payload.csv_bytes, filename="registrations_export.csv")]
        if export_payload.xlsx_bytes:
            send_files.append(
                discord.File(export_payload.xlsx_bytes, filename="registrations_export.xlsx")
            )
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
            export_payload.row_count,
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

        rows = parse_attachment_bytes(raw, ftype)
        if not rows:
            await ctx.interaction.edit_original_response(
                content="❌ File could not be parsed or appears to have no data."
            )
            return

        try:
            existing = registry_service.load_registry_as_dict()
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

        preview = build_import_preview(rows, existing)

        logger.info(
            "[IMPORT] dry-run complete — file: %s rows_parsed: %d proposed_changes: %d "
            "errors: %d warnings: %d actor: %s (%s)",
            attach.filename,
            len(rows),
            len(preview.changes),
            len(preview.errors),
            len(preview.warnings),
            ctx.user,
            ctx.user.id,
        )

        send = ctx.followup.send if deferred else ctx.respond

        if preview.errors:
            files = []
            if preview.error_csv_bytes:
                files.append(discord.File(preview.error_csv_bytes, filename="import_errors.csv"))
            if preview.error_xlsx_bytes:
                files.append(discord.File(preview.error_xlsx_bytes, filename="import_errors.xlsx"))

            short_msg = (
                f"❌ Validation failed: {len(preview.errors)} error(s). "
                "Correct the highlighted rows and re-upload. See attached file(s) for details."
            )
            if len(preview.errors) <= 10:
                content = short_msg + "\n\nErrors:\n" + "\n".join(preview.errors[:10])
                if len(content) <= 1900:
                    await send(content=content, files=files, ephemeral=True)
                    return
            await send(content=short_msg, files=files, ephemeral=True)
            return

        embed = discord.Embed(
            title="✅ Dry-Run Validation Passed",
            color=discord.Color.green(),
        )
        embed.description = (
            f"**{len(preview.changes)} change(s) proposed.**\n"
            f"Conflict behaviour: **Overwrite** — existing active slots will be superseded "
            f"and replaced with the imported values.\n\n"
            + "\n".join(preview.preview_lines)
            + (f"\n… and {len(preview.changes) - 20} more" if len(preview.changes) > 20 else "")
        )
        if preview.warnings:
            embed.add_field(
                name=f"⚠️ Warnings ({len(preview.warnings)})",
                value="\n".join(preview.warnings[:10])
                + (
                    f"\n… and {len(preview.warnings) - 10} more"
                    if len(preview.warnings) > 10
                    else ""
                ),
                inline=False,
            )
        embed.set_footer(text="Click Confirm to apply, or Cancel to abort.")

        async def _apply_import(interaction: discord.Interaction):
            try:
                apply_result = apply_import_changes(preview.changes)
                if apply_result.errors:
                    logger.warning(
                        "[IMPORT] %d row(s) failed during apply: %s",
                        len(apply_result.errors),
                        apply_result.errors,
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
                apply_result.applied_count,
                attach.filename,
            )

            text = "✅ " + build_import_summary_text(
                apply_result,
                include_apply_errors=False,
            )
            if len(text) <= 1900:
                await interaction.followup.send(text, ephemeral=True)
            else:
                bio = build_import_summary_file_bytes(apply_result)
                await interaction.followup.send(
                    f"✅ Import applied: {apply_result.applied_count} change(s). Full summary attached.",
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

        rows = parse_attachment_bytes(raw, ftype)
        if not rows:
            await ctx.interaction.edit_original_response(
                content="❌ File could not be parsed or appears to have no data."
            )
            return

        try:
            existing = registry_service.load_registry_as_dict()
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

        preview = build_import_preview(rows, existing)

        send = ctx.followup.send if deferred else ctx.respond

        if preview.errors:
            files = []
            if preview.error_csv_bytes:
                files.append(discord.File(preview.error_csv_bytes, filename="import_errors.csv"))
            if preview.error_xlsx_bytes:
                files.append(discord.File(preview.error_xlsx_bytes, filename="import_errors.xlsx"))

            logger.warning(
                "[IMPORT] live import aborted — validation failed: %d error(s) "
                "actor: %s (%s) file: %s",
                len(preview.errors),
                ctx.user,
                ctx.user.id,
                attach.filename,
            )

            short_msg = (
                f"❌ Validation failed: {len(preview.errors)} error(s). "
                "No changes have been applied. Correct the highlighted rows and re-upload."
            )
            if len(preview.errors) <= 10:
                content = short_msg + "\n\nErrors:\n" + "\n".join(preview.errors[:10])
                if len(content) <= 1900:
                    await send(content=content, files=files, ephemeral=True)
                    return
            await send(content=short_msg, files=files, ephemeral=True)
            return

        try:
            apply_result = apply_import_changes(preview.changes)
        except Exception as e:
            logger.exception("[IMPORT] apply_import_plan failed")
            await send(f"❌ Failed to apply import: {type(e).__name__}: {e}", ephemeral=True)
            return

        logger.info(
            "[IMPORT] live import complete — %d change(s) applied, %d warning(s) "
            "actor: %s (%s) file: %s",
            apply_result.applied_count,
            len(preview.warnings),
            ctx.user,
            ctx.user.id,
            attach.filename,
        )

        text = "✅ " + build_import_summary_text(apply_result, preview.warnings)

        if len(text) <= 1900:
            await send(text, ephemeral=True)
        else:
            bio = build_import_summary_file_bytes(apply_result, preview.warnings)
            await send(
                content=f"✅ Import applied: {apply_result.applied_count} change(s). Full summary attached.",
                file=discord.File(bio, filename="import_summary.txt"),
                ephemeral=True,
            )
