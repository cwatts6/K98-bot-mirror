# kvk_ui.py
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
import logging

import discord

logger = logging.getLogger(__name__)

# Type of the callback invoked when a governor is selected.
OnSelectGovernor = Callable[[discord.Interaction, str, bool], Awaitable[None]]
LookupCallback = Callable[[discord.Interaction], Awaitable[None]]
RegisterCallback = Callable[[discord.Interaction], Awaitable[None]]


def make_kvk_targets_view(
    ctx: discord.ApplicationContext,
    options: Sequence[discord.SelectOption],
    on_select_governor: OnSelectGovernor,
    *,
    show_register_btn: bool = True,
    ephemeral: bool = True,
    last_kvk_map: dict[str, dict] | None = None,
    timeout: float = 300.0,
    lookup_callback: LookupCallback | None = None,
    register_callback: RegisterCallback | None = None,
) -> discord.ui.View:
    """
    Factory: returns a View wired to call on_select_governor(interaction, gid, ephemeral)
    when the user picks an account.

    Optional:
      - lookup_callback(interaction) will be invoked when "Look up Governor ID" is clicked
      - register_callback(interaction) will be invoked when "Register New Account" clicked

    The returned view has attribute `_last_kvk_map` (may be None).
    """

    class _KVKTargetsView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=timeout)
            self.ctx = ctx
            self.ephemeral = ephemeral
            self._last_kvk_map = last_kvk_map or {}
            if options:
                self.add_item(_KVKTargetsSelect(options, self))
            self.add_item(_LookupGovIDButton())
            if show_register_btn:
                self.add_item(_RegisterAccountButton())
            self.add_item(_RefreshSelectorButton())

        async def on_timeout(self):
            for item in self.children:
                item.disabled = True
            try:
                new_view = make_kvk_targets_view(
                    ctx=self.ctx,
                    options=await _rebuild_options(self.ctx),
                    on_select_governor=on_select_governor,
                    show_register_btn=show_register_btn,
                    ephemeral=self.ephemeral,
                    last_kvk_map=getattr(self, "_last_kvk_map", {}),
                    lookup_callback=lookup_callback,
                    register_callback=register_callback,
                )
                await self.ctx.followup.send(
                    "⌛ Selector expired. Click **Refresh** to reopen, or pick an account below:",
                    view=new_view,
                    ephemeral=self.ephemeral,
                )
            except Exception:
                logger.exception("[KVK_UI] Failed to refresh expired KVKTargetsView")

    class _KVKTargetsSelect(discord.ui.Select):
        def __init__(self, choices: Sequence[discord.SelectOption], parent: _KVKTargetsView):
            super().__init__(
                placeholder="Choose an account to view…",
                min_values=1,
                max_values=1,
                options=choices,
            )
            self.parent = parent

        async def callback(self, interaction: discord.Interaction):
            gid = self.values[0]
            try:
                await interaction.response.defer(ephemeral=self.parent.ephemeral)
            except Exception:
                pass
            try:
                await on_select_governor(interaction, gid, self.parent.ephemeral)
            except Exception:
                logger.exception("[KVK_UI] on_select_governor handler failed for %s", gid)
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
        def __init__(self):
            super().__init__(
                label="Look up Governor ID", style=discord.ButtonStyle.primary, emoji="🔎"
            )

        async def callback(self, interaction: discord.Interaction):
            try:
                if lookup_callback:
                    await lookup_callback(interaction)
                else:
                    # fallback: inform user this action is not available here
                    await interaction.followup.send("Lookup not available.", ephemeral=True)
            except Exception:
                logger.exception("[KVK_UI] lookup_callback failed")
                try:
                    await interaction.followup.send("Lookup failed.", ephemeral=True)
                except Exception:
                    pass

    class _RegisterAccountButton(discord.ui.Button):
        def __init__(self):
            super().__init__(
                label="Register New Account", style=discord.ButtonStyle.success, emoji="🧾"
            )

        async def callback(self, interaction: discord.Interaction):
            try:
                if register_callback:
                    await register_callback(interaction)
                else:
                    await interaction.followup.send(
                        "Registration flow not available here.", ephemeral=True
                    )
            except Exception:
                logger.exception("[KVK_UI] register_callback failed")
                try:
                    await interaction.followup.send(
                        "Failed to open registration flow.", ephemeral=True
                    )
                except Exception:
                    pass

    class _RefreshSelectorButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Refresh", style=discord.ButtonStyle.secondary, emoji="🔄")

        async def callback(self, interaction: discord.Interaction):
            try:
                options2 = await _rebuild_options(ctx)
                new_view = make_kvk_targets_view(
                    ctx=ctx,
                    options=options2,
                    on_select_governor=on_select_governor,
                    show_register_btn=show_register_btn,
                    ephemeral=ephemeral,
                    last_kvk_map=getattr(self.view, "_last_kvk_map", {}),
                    lookup_callback=lookup_callback,
                    register_callback=register_callback,
                )
                await interaction.response.edit_message(
                    content=(
                        "Select an account to view its KVK targets:"
                        if options2
                        else "No registered accounts found."
                    ),
                    view=new_view,
                )
            except Exception:
                logger.exception("[KVK_UI] Refresh selector failed")
                try:
                    await interaction.response.send_message(
                        "Refresh failed. Try again.", ephemeral=True
                    )
                except Exception:
                    pass

    async def _rebuild_options(ctx_inner: discord.ApplicationContext):
        try:
            from utils import load_registry  # lazy import to reuse existing registry loader

            registry = await asyncio.to_thread(load_registry)
            user_block = registry.get(str(ctx_inner.user.id)) or {}
            accounts = user_block.get("accounts") or {}
            # Try to use centralized account_picker helper if present
            try:
                from account_picker import build_unique_gov_options  # type: ignore
            except Exception:
                # Fallback: minimal inline builder (keeps compatibility)
                def build_unique_gov_options_fallback(accounts_map):
                    opts = []
                    seen = set()
                    # deterministic order: sort by slot name
                    for slot in sorted(accounts_map.keys()):
                        a = accounts_map.get(slot) or {}
                        gid = str(a.get("GovernorID") or "").strip()
                        if not gid or gid in seen:
                            continue
                        seen.add(gid)
                        label = str(a.get("GovernorName") or slot)[:100]
                        opts.append(discord.SelectOption(label=label, value=gid, description=slot))
                    return opts

                build_unique_gov_options = build_unique_gov_options_fallback

            return build_unique_gov_options(accounts)
        except Exception:
            logger.exception("[KVK_UI] _rebuild_options failed")
            return []

    return _KVKTargetsView()
