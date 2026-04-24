# governor_registry.py
"""
Governor registry façade and Discord UI views.

Persistence and business logic are now owned by:
  registry_dal.py     — SQL data access layer
  registry_service.py — validation, duplicate rules, orchestration

This module is retained for:
  1. Backward-compatible load_registry() / save_registry() signatures
     called throughout the codebase during the transition period.
  2. register_account() called by RegisterGovernorView and ModifyGovernorView.
  3. get_discord_name_for_governor() called by stats/embed helpers.
  4. get_user_main_governor_id / get_user_main_governor_name dict-based helpers.
  5. All Discord UI View classes (RegisterGovernorView, ModifyGovernorView,
     ConfirmRemoveView, KVKStatsView, KVKAccountButton).

save_registry() is now a no-op.  All writes go through registry_service.
"""

from __future__ import annotations

import logging

import discord

from embed_utils import build_stats_embed
from utils import load_stat_row

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Backward-compat persistence façade
# ---------------------------------------------------------------------------


def load_registry() -> dict:
    """
    Return current Active registrations as the legacy dict format.
    Reads from SQL via registry_service.load_registry_as_dict().

    Returns {} on SQL failure after logging at ERROR level.
    Commands that present registry data to users must treat an empty
    result from this function as a possible SQL failure, not as
    "no registrations exist", and should guard accordingly.

    Commands that already wrap load_registry() in try/except
    (e.g. my_registrations) are unaffected.
    Commands that use the result for safety guards
    (e.g. duplicate pre-checks before a write) are safe — the
    stored procedure enforces constraints regardless.
    Commands that present registry data as their primary output
    (registration_audit, bulk_export_registrations) must wrap
    this call in try/except and fail explicitly.
    """
    try:
        from registry.registry_service import load_registry_as_dict

        return load_registry_as_dict()
    except Exception:
        logger.exception(
            "[governor_registry] load_registry FAILED — SQL unavailable or query error. "
            "Commands relying on registry read data will behave as if registry is empty."
        )
        return {}


def save_registry(data: dict) -> None:
    """
    Deprecated no-op.

    All writes now go through registry_service (register_governor,
    modify_governor, remove_governor) which call the DAL directly.
    Callers that relied on save_registry() have been updated to use
    the service layer.  This stub is retained to prevent AttributeErrors
    from any residual call sites during the transition period.
    """
    logger.warning(
        "[governor_registry] save_registry() called — this is a no-op since Phase 3. "
        "All writes must go through registry_service. "
        "Caller: %s",
        _caller_name(),
    )


def _caller_name() -> str:
    """Return a best-effort caller description for the save_registry deprecation warning."""
    import traceback

    stack = traceback.extract_stack()
    # Return the frame two levels above this helper (save_registry → _caller_name → here)
    if len(stack) >= 3:
        frame = stack[-3]
        return f"{frame.filename}:{frame.lineno} in {frame.name}"
    return "unknown"


# ---------------------------------------------------------------------------
# register_account — used by RegisterGovernorView and ModifyGovernorView
# ---------------------------------------------------------------------------


def register_account(
    discord_id: str,
    discord_name: str,
    account_type: str,
    governor_id: str,
    governor_name: str,
    *,
    created_by: int | None = None,
    provenance: str = "bot_command",
) -> tuple[bool, str | None]:
    """
    Register or update a governor account slot.

    Routes to registry_service.register_governor().
    If the slot already exists, automatically calls modify_governor()
    so that both RegisterGovernorView and ModifyGovernorView can share
    this single entry point without worrying about which SP to call.
    """
    from registry.registry_service import (
        modify_governor,
        register_governor,
    )

    uid = int(discord_id)

    # Check if the slot is already active for this user (→ modify path)
    from registry.dal import registry_dal

    existing_rows = registry_dal.get_by_discord_id(uid)
    slot_exists = any(r.get("AccountType") == account_type for r in existing_rows)

    if slot_exists:
        ok, err = modify_governor(
            discord_user_id=uid,
            discord_name=discord_name,
            account_type=account_type,
            new_governor_id=governor_id,
            new_governor_name=governor_name,
            updated_by=created_by,
        )
    else:
        ok, err = register_governor(
            discord_user_id=uid,
            discord_name=discord_name,
            account_type=account_type,
            governor_id=governor_id,
            governor_name=governor_name,
            created_by=created_by,
            provenance=provenance,
        )

    return ok, err


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------


def get_discord_name_for_governor(governor_id: str) -> str | None:
    """Return the registered Discord display name for a GovernorID, or None."""
    from registry.registry_service import get_discord_user_for_governor

    info = get_discord_user_for_governor(governor_id)
    if not info:
        return None
    return info.get("DiscordName") or None


def get_user_main_governor_id(registry: dict, user_id: str | int) -> str | None:
    """
    Return the GovernorID string for the user's Main slot.

    Accepts the legacy registry dict for backward compat, but also
    falls back to a direct SQL lookup if the slot isn't in the dict
    (e.g. stale caller that built the dict before a recent write).
    """
    rec = registry.get(str(user_id)) or registry.get(user_id)
    if rec:
        main = (rec.get("accounts") or {}).get("Main")
        gid = (main or {}).get("GovernorID")
        if gid:
            return str(gid)
    # Fallback: live SQL lookup
    from registry.registry_service import get_user_main_governor_id as svc_main

    return svc_main(int(user_id))


def get_user_main_governor_name(registry: dict, user_id: str | int) -> str | None:
    """
    Return the GovernorName string for the user's Main slot.

    Accepts the legacy registry dict for backward compat with a live SQL fallback.
    """
    rec = registry.get(str(user_id)) or registry.get(user_id)
    if rec:
        main = (rec.get("accounts") or {}).get("Main")
        name = (main or {}).get("GovernorName")
        if name:
            return str(name)
    from registry.registry_service import get_user_main_governor_name as svc_name

    return svc_name(int(user_id))


# ---------------------------------------------------------------------------
# Discord UI Views
# (No persistence logic — all writes go through register_account() above)
# ---------------------------------------------------------------------------


class RegisterGovernorView(discord.ui.View):
    def __init__(self, user, account_type, governor_id, governor_name):
        super().__init__(timeout=60)
        self.user = user
        self.account_type = account_type
        self.governor_id = governor_id
        self.governor_name = governor_name

    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "This isn't your registration to confirm!", ephemeral=True
            )
            return

        ok, err = register_account(
            discord_id=str(self.user.id),
            discord_name=str(self.user),
            account_type=self.account_type,
            governor_id=self.governor_id,
            governor_name=self.governor_name,
        )

        if not ok:
            await interaction.response.edit_message(
                content=f"❌ Registration failed: {err or 'Unknown error.'}", view=None
            )
        else:
            await interaction.response.edit_message(
                content=(
                    f"✅ Registered `{self.account_type}` as "
                    f"**{self.governor_name}** (ID: `{self.governor_id}`)"
                ),
                view=None,
            )

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id == self.user.id:
            await interaction.response.edit_message(content="❌ Registration cancelled.", view=None)


class ModifyGovernorView(discord.ui.View):
    def __init__(self, user, account_type, new_gov_id, new_gov_name):
        super().__init__(timeout=60)
        self.user = user
        self.account_type = account_type
        self.new_gov_id = new_gov_id
        self.new_gov_name = new_gov_name

    @discord.ui.button(label="✅ Confirm Change", style=discord.ButtonStyle.success)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "This isn't your registration to change!", ephemeral=True
            )
            return

        ok, err = register_account(
            discord_id=str(self.user.id),
            discord_name=str(self.user),
            account_type=self.account_type,
            governor_id=self.new_gov_id,
            governor_name=self.new_gov_name,
        )

        if not ok:
            await interaction.response.edit_message(
                content=f"❌ Update failed: {err or 'Unknown error.'}", view=None
            )
        else:
            await interaction.response.edit_message(
                content=(
                    f"✅ `{self.account_type}` updated to "
                    f"**{self.new_gov_name}** (ID: `{self.new_gov_id}`)"
                ),
                view=None,
            )

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id == self.user.id:
            await interaction.response.edit_message(content="❌ Modification cancelled.", view=None)


class ConfirmRemoveView(discord.ui.View):
    def __init__(self, user, account_type):
        super().__init__(timeout=60)
        self.user = user
        self.account_type = account_type

    @discord.ui.button(label="✅ Confirm Remove", style=discord.ButtonStyle.danger)
    async def confirm(self, button, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "You cannot modify someone else's registration.", ephemeral=True
            )
            return

        from registry.registry_service import remove_governor

        ok, err = remove_governor(
            discord_user_id=interaction.user.id,
            account_type=self.account_type,
            removed_by=interaction.user.id,
        )

        if ok:
            await interaction.response.send_message(
                f"✅ `{self.account_type}` has been removed from your registered accounts.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"❌ {err or 'Could not remove registration.'}", ephemeral=True
            )
        self.stop()

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, button, interaction: discord.Interaction):
        if interaction.user.id == self.user.id:
            await interaction.response.edit_message(content="❌ Removal cancelled.", view=None)
        self.stop()


class KVKStatsView(discord.ui.View):
    def __init__(
        self, user: discord.User, accounts: dict, *, ephemeral: bool = False, timeout: float = 120
    ):
        super().__init__(timeout=timeout)
        self.user = user
        self.author_id = user.id
        self.accounts = accounts
        self.ephemeral = ephemeral

        def _sort_key(item):
            label, _info = item
            lc = label.lower().strip()
            if lc == "main":
                return (0, 0, lc)
            if lc.startswith("alt"):
                try:
                    n = int("".join(c for c in lc if c.isdigit()) or 0)
                except Exception:
                    n = 0
                return (1, n, lc)
            if lc.startswith("farm"):
                try:
                    n = int("".join(c for c in lc if c.isdigit()) or 0)
                except Exception:
                    n = 0
                return (2, n, lc)
            return (3, 0, lc)

        for idx, (label, info) in enumerate(sorted(accounts.items(), key=_sort_key)[:25]):
            gov_id = str(info.get("GovernorID", "")).strip()
            if not gov_id:
                continue
            btn = KVKAccountButton(
                label=label,
                governor_id=gov_id,
                author_id=self.author_id,
                ephemeral=self.ephemeral,
            )
            try:
                btn.row = min(idx // 5, 4)
            except Exception:
                pass
            self.add_item(btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            try:
                await interaction.response.send_message(
                    "❌ This selector isn't for you.", ephemeral=True
                )
            except Exception:
                pass
            return False
        return True

    async def on_timeout(self):
        for c in self.children:
            c.disabled = True


class KVKAccountButton(discord.ui.Button):
    def __init__(self, *, label: str, governor_id: str, author_id: int, ephemeral: bool):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self._label = label
        self.governor_id = str(governor_id)
        self.author_id = author_id
        self.ephemeral = ephemeral

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ This selector isn't for you.", ephemeral=True
            )
            return

        try:
            await interaction.response.defer(ephemeral=self.ephemeral)
        except Exception:
            pass

        gov_data = load_stat_row(self.governor_id)
        if not gov_data:
            await interaction.followup.send(
                "❌ Stats not found for that Governor ID.", ephemeral=True
            )
            return

        try:
            result = build_stats_embed(gov_data, interaction.user)
        except Exception as e:
            await interaction.followup.send(
                f"❌ Failed to build stats: `{type(e).__name__}: {e}`", ephemeral=True
            )
            return

        embeds = None
        file = None
        try:
            if isinstance(result, tuple) and isinstance(result[0], list):
                embeds, file = result
            elif isinstance(result, list):
                embeds, file = result, None
            else:
                try:
                    possible_embed, possible_file = result
                    if isinstance(possible_embed, discord.Embed):
                        embeds, file = [possible_embed], possible_file
                    else:
                        embeds, file = [possible_embed], possible_file
                except Exception:
                    embeds, file = (
                        [result] if isinstance(result, discord.Embed) else [result]
                    ), None
        except Exception:
            embeds, file = [result], None

        try:
            if file is not None:
                await interaction.followup.send(
                    content=f"📊 Showing stats for `{self._label}`:",
                    embeds=embeds,
                    files=[file],
                    ephemeral=self.ephemeral,
                )
            else:
                await interaction.followup.send(
                    content=f"📊 Showing stats for `{self._label}`:",
                    embeds=embeds,
                    ephemeral=self.ephemeral,
                )
        except Exception as e:
            logger.exception("[KVKAccountButton] failed to send embeds: %s", e)
            try:
                if embeds:
                    await interaction.followup.send(
                        content=f"📊 Showing stats for `{self._label}`:",
                        embed=embeds[0],
                        file=file,
                        ephemeral=self.ephemeral,
                    )
            except Exception:
                pass
