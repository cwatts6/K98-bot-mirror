# ui/views/kvk_personal_views.py
"""
Canonical view classes for /mykvktargets and /mykvkstats personal command flows.

Single source of truth for:
- MyKVKStatsSelectView
- TargetLookupView
- FuzzySelectView (top-level, promoted from nested class)
- PostLookupActions

All interaction routing only — no business logic inline.
Business logic lives in services/kvk_personal_service.py.
"""

from __future__ import annotations

import asyncio
import logging

import discord
from discord.ui import View

from account_picker import ACCOUNT_ORDER
from decoraters import _is_admin

logger = logging.getLogger(__name__)


async def _send_targets_to_channel(interaction: discord.Interaction, governor_id: str) -> None:
    """
    Fetch target data for a resolved numeric governor_id and post the embed
    directly to interaction.channel, creating a new public message regardless
    of whether the triggering button/select was inside an ephemeral message.

    The caller must have already acknowledged the interaction (e.g. with
    ``defer(ephemeral=True)``) before calling this helper.
    """
    try:
        from kvk_state import get_kvk_context_today
        from target_utils import run_target_lookup
        from targets_embed import build_kvk_targets_embed

        # Non-interactive call — returns a data dict without touching the interaction
        result = await run_target_lookup(str(governor_id))
        channel = interaction.channel

        if result and result.get("status") == "found":
            tgt = result["data"]
            kvk_ctx = get_kvk_context_today() or {}
            kvk_name = kvk_ctx.get("kvk_name")
            gov_name = tgt.get("GovernorName") or str(governor_id)
            embed = build_kvk_targets_embed(
                gov_name=gov_name,
                governor_id=int(governor_id),
                targets=tgt,
                kvk_name=kvk_name,
            )
            if channel is not None:
                try:
                    await channel.send(embed=embed)
                    return
                except Exception:
                    logger.exception(
                        "[kvk_personal_views] channel.send failed for governor_id=%s", governor_id
                    )
            # Fallback if channel unavailable
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            msg = (result or {}).get("message", "No targets found for this governor.")
            if channel is not None:
                try:
                    await channel.send(content=msg)
                    return
                except Exception:
                    logger.exception(
                        "[kvk_personal_views] channel.send (error msg) failed for governor_id=%s",
                        governor_id,
                    )
            await interaction.followup.send(content=msg, ephemeral=True)
    except Exception:
        logger.exception(
            "[kvk_personal_views] _send_targets_to_channel failed governor_id=%s", governor_id
        )
        try:
            await interaction.followup.send(
                "⚠️ Something went wrong loading targets.", ephemeral=True
            )
        except Exception:
            pass


class MyKVKStatsSelectView(discord.ui.View):
    """
    Ephemeral selector for /mykvkstats.

    - Dropdown of user's registered accounts (ordered by ACCOUNT_ORDER)
    - Buttons: Lookup Governor ID, Register New Account
    - On select -> calls kvk_personal_service.post_stats_embeds via the channel fallback chain
    """

    def __init__(
        self,
        *,
        ctx: discord.ApplicationContext,
        accounts: dict,
        author_id: int,
        bot=None,
        timeout: int = 120,
    ):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.author_id = author_id
        self.accounts = accounts
        self._bot = bot if bot is not None else getattr(ctx, "bot", None)
        self._last_kvk_map: dict = {}

        # Build options in canonical order
        options: list[discord.SelectOption] = []
        for slot in ACCOUNT_ORDER:
            if slot in accounts:
                info = accounts[slot] or {}
                gid = str(info.get("GovernorID", "")).strip()
                gname = str(info.get("GovernorName", "")).strip()
                label = slot
                desc = f"{gname} • ID {gid}" if (gname or gid) else slot
                options.append(
                    discord.SelectOption(label=label[:100], description=desc[:100], value=gid)
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
            await interaction.response.send_message("❌ This menu isn't for you.", ephemeral=True)
            return False
        return True

    async def _on_select(self, interaction: discord.Interaction):
        # ACK the interaction quickly.
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        from utils import load_stat_row, normalize_governor_id

        gid = normalize_governor_id(self.select.values[0])

        try:
            row = await asyncio.to_thread(load_stat_row, gid)
        except Exception as e:
            logger.exception("[MyKVKStatsSelectView] load_stat_row failed governor_id=%s", gid)
            try:
                if _is_admin(interaction.user):
                    await interaction.followup.send(
                        f"❌ Couldn't find stats for GovernorID `{gid}`: `{type(e).__name__}: {e}`",
                        ephemeral=True,
                    )
            except Exception:
                pass
            return

        if not row:
            try:
                if _is_admin(interaction.user):
                    await interaction.followup.send(
                        f"Couldn't find stats for GovernorID `{gid}`.", ephemeral=True
                    )
            except Exception:
                pass
            return

        # Attach last_kvk from the map if available
        try:
            lkmap = self._last_kvk_map
            if lkmap:
                lk = lkmap.get(str(gid))
                if lk:
                    row["last_kvk"] = lk
        except Exception:
            logger.exception("[MyKVKStatsSelectView] failed attaching last_kvk for %s", gid)

        try:
            from embed_utils import build_stats_embed

            embeds, file = build_stats_embed(row, interaction.user)
        except Exception as e:
            logger.exception("[MyKVKStatsSelectView] build_stats_embed failed governor_id=%s", gid)
            try:
                if _is_admin(interaction.user):
                    await interaction.followup.send(
                        f"❌ Failed to build stats: `{type(e).__name__}: {e}`", ephemeral=True
                    )
            except Exception:
                pass
            return

        try:
            from services import kvk_personal_service

            posted, _ = await kvk_personal_service.post_stats_embeds(
                self._bot, self.ctx, embeds, file
            )
        except Exception:
            logger.exception("[MyKVKStatsSelectView] post_stats_embeds failed governor_id=%s", gid)
            posted = False

        if posted:
            try:
                if _is_admin(interaction.user):
                    await interaction.followup.send(
                        "✅ Posted stats. If you can't see them in this channel, check the bot's send permissions.",
                        ephemeral=True,
                    )
            except Exception:
                pass
        else:
            try:
                if _is_admin(interaction.user):
                    await interaction.followup.send(
                        "⚠️ Couldn't post publicly and couldn't DM the user. Admins: check bot/channel permissions.",
                        ephemeral=True,
                    )
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

    async def on_timeout(self):
        for c in self.children:
            c.disabled = True
        try:
            await self.ctx.edit_original_response(view=self)
        except Exception:
            pass


class TargetLookupView(View):
    """
    View shown after a fuzzy governor search in /mygovernorid.
    One button per match — each delegates to run_target_lookup.
    """

    def __init__(self, matches: list):
        super().__init__(timeout=60)
        self.matches = matches
        self.ctx = None
        self.message = None
        for match in matches:
            label = f"🎯 View KVK Targets for {match['GovernorName'][:50]}"
            button = discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.primary,
                custom_id=f"target_{match['GovernorID']}",
            )
            button.callback = self.make_callback(match["GovernorID"])
            self.add_item(button)

    def make_callback(self, governor_id):
        async def callback(interaction: discord.Interaction):
            try:
                await interaction.response.defer(ephemeral=True)
            except Exception:
                pass
            await _send_targets_to_channel(interaction, str(governor_id))

        return callback

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except discord.NotFound:
            pass
        except Exception as e:
            logger.exception("[TargetLookupView] timeout edit failed: %s", e)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == self.ctx.user

    async def on_error(self, error: Exception, item, interaction: discord.Interaction) -> None:
        logger.error("[TargetLookupView] error: %s", error)
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"⚠️ An error occurred: {error}", ephemeral=True
            )

    async def send(self, interaction: discord.Interaction, embed: discord.Embed):
        self.ctx = interaction
        try:
            if not interaction.response.is_done():
                self.message = await interaction.response.send_message(
                    embed=embed, view=self, ephemeral=True
                )
            else:
                self.message = await interaction.edit_original_response(embed=embed, view=self)
        except Exception:
            self.message = await interaction.followup.send(embed=embed, view=self, ephemeral=True)


class FuzzySelectView(View):
    """
    Dropdown to pick one governor from fuzzy search results.
    Used by /mygovernorid for multi-match scenarios.
    Promoted from being nested inside TargetLookupView.
    """

    def __init__(
        self,
        matches: list,
        author_id: int,
        *,
        show_targets: bool = False,
        timeout: float = 120,
    ):
        super().__init__(timeout=timeout)
        self.matches = matches
        self.author_id = author_id
        self.show_targets = show_targets
        self.ctx = None
        self.message = None

        options = []
        for m in matches[:25]:
            name = str(m.get("GovernorName") or "")[:75]
            gid = str(m.get("GovernorID") or "")
            desc = f"ID: {gid}"
            options.append(discord.SelectOption(label=name, description=desc, value=gid))

        self.select = discord.ui.Select(
            placeholder="Choose a governor…", options=options, min_values=1, max_values=1
        )
        self.select.callback = self.on_select
        self.add_item(self.select)

    async def on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This selector isn't for you.", ephemeral=True)
            return

        gid = str(self.select.values[0])

        if self.show_targets:
            await interaction.response.send_message(
                f"Governor **{gid}** selected. What would you like to do?",
                view=PostLookupActions(author_id=self.author_id, governor_id=gid),
                ephemeral=True,
            )
            return

        # Register-only flow
        from registry.governor_registry import load_registry
        from ui.views.registry_views import RegisterStartView

        try:
            registry = await asyncio.to_thread(load_registry) or {}
        except Exception:
            logger.exception("[FuzzySelectView] Failed to load registry during register-only flow")
            await interaction.response.send_message(
                "Sorry, I couldn't load your registrations right now. Please try again in a moment.",
                ephemeral=True,
            )
            return

        user_key = str(self.author_id)
        accounts = (registry.get(user_key) or {}).get("accounts", {}) or {}
        used_slots = set(accounts.keys())
        free_slots = [slot for slot in ACCOUNT_ORDER if slot not in used_slots]

        if not free_slots:
            await interaction.response.send_message(
                "All account slots are already registered. Use **Modify Registration** to change one.",
                ephemeral=True,
            )
            return

        view = RegisterStartView(author_id=self.author_id, free_slots=free_slots, prefill_id=gid)
        await interaction.response.send_message(
            "Pick an account slot to register:", view=view, ephemeral=True
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            pass

    async def on_error(self, error: Exception, item, interaction: discord.Interaction):
        logger.error("[FuzzySelectView] error: %s", error)
        if interaction and not interaction.response.is_done():
            await interaction.response.send_message("⚠️ Something went wrong.", ephemeral=True)

    async def send_followup(self, interaction: discord.Interaction, embed: discord.Embed):
        self.ctx = interaction
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
        self.message = await interaction.followup.send(embed=embed, view=self, ephemeral=True)


class PostLookupActions(View):
    """
    Action buttons shown after a governor lookup (fuzzy search or direct ID entry).

    Buttons:
    - View KVK Stats      — load and post stats for the selected governor
    - View KVK Targets    — open the full target embed for the selected governor
    - Register this Governor
    """

    def __init__(self, *, author_id: int, governor_id: str, timeout: float = 120):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.governor_id = governor_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    @discord.ui.button(label="View KVK Stats", style=discord.ButtonStyle.danger)
    async def btn_stats(self, button: discord.ui.Button, interaction: discord.Interaction):
        # Acknowledge the interaction ephemerally so the button doesn't error.
        # We then post directly via interaction.channel.send() which is completely
        # outside the interaction response system and always creates a new public
        # message, regardless of whether the button panel was originally ephemeral.
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        try:
            from embed_utils import build_stats_embed
            from services import kvk_personal_service
            from stats_cache_helpers import get_last_kvk_for_governor_sync
            from utils import normalize_governor_id

            gid = normalize_governor_id(self.governor_id)
            row = await kvk_personal_service.load_kvk_personal_stats(gid)
            if not row:
                await interaction.followup.send(
                    f"❌ Couldn't find stats for Governor ID `{gid}`.", ephemeral=True
                )
                return

            try:
                lk = get_last_kvk_for_governor_sync(str(gid))
                if lk:
                    row["last_kvk"] = lk
            except Exception:
                logger.exception("[PostLookupActions] failed attaching last_kvk for %s", gid)

            embeds, file = build_stats_embed(row, interaction.user)
            # Send directly to the channel — this is always a brand-new public message
            # and is unaffected by the ephemeral nature of the button's parent message.
            channel = interaction.channel
            if channel is not None:
                try:
                    if file is not None:
                        await channel.send(embeds=embeds, files=[file])
                    else:
                        await channel.send(embeds=embeds)
                    return
                except Exception:
                    logger.exception("[PostLookupActions] channel.send failed governor_id=%s", gid)
            # Fallback: if channel is unavailable post as ephemeral followup
            send_kwargs: dict = {"embeds": embeds, "ephemeral": True}
            if file is not None:
                send_kwargs["files"] = [file]
            await interaction.followup.send(**send_kwargs)
        except Exception:
            logger.exception(
                "[PostLookupActions] btn_stats failed governor_id=%s", self.governor_id
            )
            try:
                await interaction.followup.send(
                    "⚠️ Something went wrong loading stats.", ephemeral=True
                )
            except Exception:
                pass

    @discord.ui.button(label="View KVK Targets", style=discord.ButtonStyle.primary)
    async def btn_targets(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass
        await _send_targets_to_channel(interaction, self.governor_id)

    @discord.ui.button(label="Register this Governor", style=discord.ButtonStyle.success)
    async def btn_register(self, button: discord.ui.Button, interaction: discord.Interaction):
        from registry.governor_registry import load_registry
        from ui.views.registry_views import RegisterStartView

        try:
            registry = await asyncio.to_thread(load_registry)
        except Exception:
            logger.exception(
                "[PostLookupActions] Failed to load governor registry during registration flow"
            )
            await interaction.response.send_message(
                "Registration is temporarily unavailable because the registry could not be loaded.",
                ephemeral=True,
            )
            return

        registry = registry or {}
        user_key = str(self.author_id)
        accounts = (registry.get(user_key) or {}).get("accounts", {}) or {}
        used_slots = set(accounts.keys())
        free_slots = [slot for slot in ACCOUNT_ORDER if slot not in used_slots]

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
