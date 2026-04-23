# ui/views/kvk_personal_views.py
"""KVK personal stats and targets views.

Extracted from commands/telemetry_cmds.py as part of the UI separation refactor.
"""
from __future__ import annotations

import asyncio
import logging
import time

import discord

from core.interaction_safety import send_ephemeral
from decoraters import _is_admin

logger = logging.getLogger(__name__)

ACCOUNT_ORDER = ["Main"] + [f"Alt {i}" for i in range(1, 6)] + [f"Farm {i}" for i in range(1, 11)]


class MyKVKStatsSelectView(discord.ui.View):
    """
    Ephemeral selector for /mykvkstats.
    Provides a dropdown of the user's registered accounts plus lookup/register buttons.
    On select, this view orchestrates the account stats response flow and posts the
    resulting public stats embed to the channel.
    """

    def __init__(
        self,
        *,
        ctx: discord.ApplicationContext,
        accounts: dict,
        author_id: int,
        timeout: int = 120,
    ):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.author_id = author_id
        self.accounts = accounts

        options: list[discord.SelectOption] = []
        for slot in ACCOUNT_ORDER:
            if slot in accounts:
                info = accounts[slot] or {}
                gid = str(info.get("GovernorID", "")).strip()
                gname = str(info.get("GovernorName", "")).strip()
                desc = f"{gname} • ID {gid}" if (gname or gid) else slot
                options.append(
                    discord.SelectOption(label=slot[:100], description=desc[:100], value=gid)
                )

        self.select = discord.ui.Select(
            placeholder="Choose an account…", options=options[:25], min_values=1, max_values=1
        )
        self.select.callback = self._on_select
        self.add_item(self.select)

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
            await send_ephemeral(interaction, "❌ This menu isn't for you.")
            return False
        return True

    async def _on_select(self, interaction: discord.Interaction):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            logger.debug(
                "[MyKVKStatsSelectView] interaction defer failed in _on_select",
                exc_info=True,
            )

        from embed_utils import build_stats_embed
        from stats_cache_helpers import load_last_kvk_map
        from utils import load_stat_row, normalize_governor_id

        gid = normalize_governor_id(self.select.values[0])
        t0 = time.monotonic()

        try:
            row = load_stat_row(gid)
        except Exception:
            logger.exception(
                "[MyKVKStatsSelectView] load_stat_row failed governor_id=%s", gid
            )
            if _is_admin(interaction.user):
                await interaction.followup.send(
                    f"❌ Couldn't load stats for GovernorID `{gid}`.", ephemeral=True
                )
            return

        if not row:
            if _is_admin(interaction.user):
                await interaction.followup.send(
                    f"Couldn't find stats for GovernorID `{gid}`.", ephemeral=True
                )
            return

        try:
            lkmap = await load_last_kvk_map()
            if lkmap:
                lk = lkmap.get(str(gid))
                if lk:
                    row["last_kvk"] = lk
        except Exception:
            logger.exception(
                "[MyKVKStatsSelectView] failed attaching last_kvk governor_id=%s", gid
            )

        try:
            embeds, file = build_stats_embed(row, interaction.user)
        except Exception:
            logger.exception(
                "[MyKVKStatsSelectView] build_stats_embed failed governor_id=%s", gid
            )
            if _is_admin(interaction.user):
                await interaction.followup.send("❌ Failed to build stats embed.", ephemeral=True)
            return

        elapsed_ms = (time.monotonic() - t0) * 1000
        logger.info(
            "[MyKVKStatsSelectView] stats loaded governor_id=%s elapsed_ms=%.1f",
            gid, elapsed_ms,
        )
        await self._post_public_stats(interaction, embeds, file)

    async def _post_public_stats(
        self,
        interaction: discord.Interaction,
        embeds: list,
        file,
    ) -> None:
        async def _try_send(ch: discord.abc.Messageable) -> bool:
            try:
                if file is not None:
                    await ch.send(embeds=embeds, files=[file])
                else:
                    await ch.send(embeds=embeds)
                return True
            except discord.Forbidden:
                logger.warning(
                    "[MyKVKStatsSelectView] Forbidden sending to channel %s",
                    getattr(ch, "id", None),
                )
                return False
            except Exception:
                logger.exception(
                    "[MyKVKStatsSelectView] error sending to channel %s",
                    getattr(ch, "id", None),
                )
                return False

        posted = False
        orig_ch = getattr(self.ctx, "channel", None)
        if orig_ch:
            posted = await _try_send(orig_ch)

        if not posted:
            try:
                from bot_config import KVK_PLAYER_STATS_CHANNEL_ID, NOTIFY_CHANNEL_ID
                guild = getattr(interaction, "guild", None)
                if guild:
                    for cid in (KVK_PLAYER_STATS_CHANNEL_ID, NOTIFY_CHANNEL_ID):
                        if cid:
                            ch = guild.get_channel(int(cid))
                            if ch:
                                posted = await _try_send(ch)
                                if posted:
                                    break
            except Exception:
                logger.exception("[MyKVKStatsSelectView] fallback channel lookup failed")

        if posted:
            if _is_admin(interaction.user):
                try:
                    await interaction.followup.send("✅ Posted stats.", ephemeral=True)
                except Exception:
                    pass
            return

        dm_ok = False
        try:
            if file is not None:
                await interaction.user.send(embeds=embeds, files=[file])
            else:
                await interaction.user.send(embeds=embeds)
            dm_ok = True
        except discord.Forbidden:
            logger.info("[MyKVKStatsSelectView] cannot DM user %s", interaction.user.id)
        except Exception:
            logger.exception("[MyKVKStatsSelectView] failed to DM user %s", interaction.user.id)

        if _is_admin(interaction.user):
            try:
                msg = (
                    "⚠️ Sent stats via DM (couldn't post publicly)."
                    if dm_ok
                    else "⚠️ Couldn't post publicly or send DM."
                )
                await interaction.followup.send(msg, ephemeral=True)
            except Exception:
                pass

    async def _on_lookup(self, interaction: discord.Interaction):
        from ui.views.registry_views import GovNameModal
        await interaction.response.send_modal(GovNameModal(author_id=self.author_id))

    async def _on_register(self, interaction: discord.Interaction):
        from registry.governor_registry import load_registry
        from ui.views.registry_views import RegisterStartView

        try:
            registry = await asyncio.to_thread(load_registry) or {}
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

    async def on_timeout(self) -> None:
        for c in self.children:
            c.disabled = True
        try:
            await self.ctx.edit_original_response(view=self)
        except Exception:
            pass


class PostLookupActions(discord.ui.View):
    """
    Actions available after a governor lookup via /mygovernorid:
    - View KVK Targets
    - Register this Governor
    """

    def __init__(self, *, author_id: int, governor_id: str, timeout: float = 120):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.governor_id = governor_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await send_ephemeral(interaction, "❌ This menu isn't for you.")
            return False
        return True

    @discord.ui.button(label="View KVK Targets", style=discord.ButtonStyle.primary)
    async def btn_targets(self, button: discord.ui.Button, interaction: discord.Interaction):
        from target_utils import run_target_lookup
        await run_target_lookup(interaction, self.governor_id, ephemeral=True)

    @discord.ui.button(label="Register this Governor", style=discord.ButtonStyle.success)
    async def btn_register(self, button: discord.ui.Button, interaction: discord.Interaction):
        from registry.governor_registry import load_registry
        from ui.views.registry_views import RegisterStartView

        try:
            registry = await asyncio.to_thread(load_registry)
        except Exception:
            logger.exception("Failed to load governor registry for registration.")
            await interaction.response.send_message(
                "❌ Failed to load registration data. Please try again later.",
                ephemeral=True,
            )
            return

        registry = registry or {}
        accounts = (registry.get(str(self.author_id)) or {}).get("accounts", {}) or {}
        free_slots = [s for s in ACCOUNT_ORDER if s not in accounts]

        if not free_slots:
            await interaction.response.send_message(
                "All account slots are already registered. Use **Modify Registration** to change one.",
                ephemeral=True,
            )
            return

        view = RegisterStartView(
            author_id=self.author_id, free_slots=free_slots, prefill_id=self.governor_id
        )
        await interaction.response.send_message(
            "Pick an account slot to register:", view=view, ephemeral=True
        )
