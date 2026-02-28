"""
account_picker.py

Small utility module to provide the account-select option builder used across
Commands and UI modules. This decouples the account picker helper from Commands.py
so UI modules (kvk_ui, crystaltech UI, etc.) don't need to import Commands at runtime.

Exports:
- build_unique_gov_options(accounts: dict) -> list[discord.SelectOption]
- AccountPickerView(...) -> reusable discord.ui.View for account selection
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
import logging

import discord

logger = logging.getLogger(__name__)

# Preferred stable ordering for account slots
_PREFERRED_ORDER = (
    ["Main"] + [f"Alt {i}" for i in range(1, 11)] + [f"Farm {i}" for i in range(1, 21)]
)


def _slot_rank(slot_name: str) -> int:
    """
    Give a small stable rank for a slot. Slots appearing in _PREFERRED_ORDER rank first,
    then others ordered lexically.
    """
    try:
        return _PREFERRED_ORDER.index(slot_name)
    except ValueError:
        # push unknown slots after preferred list, but keep deterministic ordering
        return len(_PREFERRED_ORDER) + hash(slot_name) % 10000


def build_unique_gov_options(accounts: dict[str, dict]) -> list[discord.SelectOption]:
    """
    Build a list of discord.SelectOption objects from a mapping of account slot -> account dict.
    accounts: { slot_name: { "GovernorID": "...", "GovernorName": "..." }, ... }

    Behavior:
    - Keeps one option per unique GovernorID (first seen by slot preference).
    - Labels are GovernorName (if present) or slot fallback.
    - Value is the governor id (string).
    - Description is the slot name.
    """
    if not accounts:
        return []

    # Flatten and preserve order using preferred slot ranking
    items: list[tuple[str, dict]] = sorted(
        accounts.items(), key=lambda kv: (_slot_rank(kv[0]), kv[0])
    )

    seen_gids: set[str] = set()
    options: list[discord.SelectOption] = []

    for slot, acc in items:
        if not acc or not isinstance(acc, dict):
            continue
        gid = acc.get("GovernorID") or acc.get("GovernorId") or acc.get("GovernorIdStr") or ""
        gid = str(gid).strip()
        if not gid:
            # If there's no numeric id, skip this entry
            continue
        if gid in seen_gids:
            continue
        seen_gids.add(gid)
        name = acc.get("GovernorName") or acc.get("Governor") or slot
        label = str(name)[:100] if name is not None else slot
        desc = str(slot) if slot else None
        opt = discord.SelectOption(label=label, value=gid, description=desc)
        options.append(opt)

    return options


# ----------------- AccountPickerView (reusable) -----------------
OnSelectGovernor = Callable[[discord.Interaction, str, bool], Awaitable[None]]
LookupCallback = Callable[[discord.Interaction], Awaitable[None]]
RegisterCallback = Callable[[discord.Interaction], Awaitable[None]]


async def _rebuild_options_from_registry(
    ctx: discord.ApplicationContext,
) -> list[discord.SelectOption]:
    """
    Helper to rebuild options by loading the user's registry. Mirrors the
    behaviour used in kvk_ui._rebuild_options. Returns empty list on error.
    """
    try:
        from utils import load_registry  # late import to avoid circulars

        registry = await asyncio.to_thread(load_registry)
        user_block = registry.get(str(ctx.user.id)) or {}
        accounts = user_block.get("accounts") or {}
        # Use the canonical builder in this module
        return build_unique_gov_options(accounts)
    except Exception:
        logger.exception("[AccountPicker] _rebuild_options_from_registry failed")
        return []


class AccountPickerView(discord.ui.View):
    """
    Reusable account picker view.

    Parameters:
      - ctx: discord.ApplicationContext (used for refresh behavior that needs the invoking user)
      - options: Sequence[discord.SelectOption] (initial options)
      - on_select_governor: async callback (interaction, governor_id, ephemeral)
      - heading: optional heading text used for followup content when sending the view
      - show_register_btn: whether to show the "Register" button
      - ephemeral: whether interactions should be handled as ephemeral by default (passed to callbacks)
      - timeout: view timeout
      - last_kvk_map: optional map attached for reference
      - lookup_callback, register_callback: optional callbacks invoked by corresponding buttons
    """

    def __init__(
        self,
        ctx: discord.ApplicationContext,
        options: Sequence[discord.SelectOption],
        on_select_governor: OnSelectGovernor,
        *,
        heading: str | None = None,
        show_register_btn: bool = True,
        ephemeral: bool = True,
        timeout: float = 300.0,
        last_kvk_map: dict | None = None,
        lookup_callback: LookupCallback | None = None,
        register_callback: RegisterCallback | None = None,
    ):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.ephemeral = ephemeral
        self._last_kvk_map = last_kvk_map or {}
        self.heading = heading or "Select an account to view:"
        self._on_select_governor = on_select_governor
        self._lookup_cb = lookup_callback
        self._register_cb = register_callback
        self._show_register_btn = show_register_btn

        if options:
            self.add_item(_AccountSelect(options, self, on_select_governor))

        # Lookup button
        self.add_item(_LookupGovIDButton(self._lookup_cb))

        # Optional register button
        if show_register_btn:
            self.add_item(_RegisterAccountButton(self._register_cb))

        # Refresh
        self.add_item(_RefreshSelectorButton(ctx, self, on_select_governor, show_register_btn))

    async def on_timeout(self) -> None:
        # disable children to visually indicate expiry
        for it in self.children:
            it.disabled = True
        try:
            if getattr(self, "message", None):
                await self.message.edit(content="Session timed out.", view=self)
        except Exception:
            pass


class _AccountSelect(discord.ui.Select):
    def __init__(
        self,
        choices: Sequence[discord.SelectOption],
        parent: AccountPickerView,
        on_select: OnSelectGovernor,
    ):
        super().__init__(
            placeholder="Choose an account to view…", min_values=1, max_values=1, options=choices
        )
        self.parent = parent
        self._on_select = on_select

    async def callback(self, interaction: discord.Interaction):
        gid = self.values[0]
        try:
            await interaction.response.defer(ephemeral=self.parent.ephemeral)
        except Exception:
            pass
        try:
            await self._on_select(interaction, gid, self.parent.ephemeral)
        except Exception:
            logger.exception("[AccountPicker] on_select handler failed for %s", gid)
            try:
                await interaction.followup.send("Failed to handle selection.", ephemeral=True)
            except Exception:
                pass
        finally:
            try:
                self.parent.stop()
            except Exception:
                pass


class _LookupGovIDButton(discord.ui.Button):
    def __init__(self, lookup_cb: LookupCallback | None):
        super().__init__(label="Look up Governor ID", style=discord.ButtonStyle.primary, emoji="🔎")
        self._lookup_cb = lookup_cb

    async def callback(self, interaction: discord.Interaction):
        try:
            if self._lookup_cb:
                await self._lookup_cb(interaction)
            else:
                await interaction.followup.send("Lookup not available here.", ephemeral=True)
        except Exception:
            logger.exception("[AccountPicker] lookup_callback failed")
            try:
                await interaction.followup.send("Lookup failed.", ephemeral=True)
            except Exception:
                pass


class _RegisterAccountButton(discord.ui.Button):
    def __init__(self, register_cb: RegisterCallback | None):
        super().__init__(
            label="Register New Account", style=discord.ButtonStyle.success, emoji="🧾"
        )
        self._register_cb = register_cb

    async def callback(self, interaction: discord.Interaction):
        try:
            if self._register_cb:
                await self._register_cb(interaction)
            else:
                await interaction.followup.send(
                    "Registration flow not available here.", ephemeral=True
                )
        except Exception:
            logger.exception("[AccountPicker] register_callback failed")
            try:
                await interaction.followup.send("Failed to open registration flow.", ephemeral=True)
            except Exception:
                pass


class _RefreshSelectorButton(discord.ui.Button):
    def __init__(
        self,
        ctx: discord.ApplicationContext,
        parent_view: AccountPickerView,
        on_select: OnSelectGovernor,
        show_register_btn: bool,
    ):
        super().__init__(label="Refresh", style=discord.ButtonStyle.secondary, emoji="🔄")
        self._ctx = ctx
        self._parent_view_ref = parent_view
        self._on_select = on_select
        self._show_register_btn = show_register_btn

    async def callback(self, interaction: discord.Interaction):
        try:
            options2 = await _rebuild_options_from_registry(self._ctx)
            new_view = AccountPickerView(
                ctx=self._ctx,
                options=options2,
                on_select_governor=self._on_select,
                heading=(
                    self._parent_view_ref.heading
                    if getattr(self._parent_view_ref, "heading", None)
                    else None
                ),
                show_register_btn=self._show_register_btn,
                ephemeral=self._parent_view_ref.ephemeral,
                last_kvk_map=getattr(self._parent_view_ref, "_last_kvk_map", {}),
                lookup_callback=getattr(self._parent_view_ref, "_lookup_cb", None),
                register_callback=getattr(self._parent_view_ref, "_register_cb", None),
            )
            # Attempt to edit the message where the view was attached. If that fails, send a fresh message.
            try:
                await interaction.response.edit_message(
                    content=(
                        "Select an account to view its KVK targets:"
                        if options2
                        else "No registered accounts found."
                    ),
                    view=new_view,
                )
            except Exception:
                # If edit_message fails, try to respond with a followup (ephemeral if parent said so)
                try:
                    await interaction.followup.send(
                        "Selector refreshed.",
                        view=new_view,
                        ephemeral=self._parent_view_ref.ephemeral,
                    )
                except Exception:
                    logger.exception("[AccountPicker] Refresh selector failed completely")
        except Exception:
            logger.exception("[AccountPicker] Refresh callback failed")
            try:
                await interaction.response.send_message(
                    "Refresh failed. Try again.", ephemeral=True
                )
            except Exception:
                pass
