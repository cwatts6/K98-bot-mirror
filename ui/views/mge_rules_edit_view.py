from __future__ import annotations

import asyncio
import logging

import discord

from core.interaction_safety import send_ephemeral
from core.mge_permissions import is_admin_or_leadership_interaction
from mge import mge_embed_manager, mge_rules_service

logger = logging.getLogger(__name__)

_EMBED_RULES_LIMIT = mge_rules_service.RULES_EMBED_FIELD_LIMIT
_MAX_RULES_TEXT_LEN = mge_rules_service.RULES_STORAGE_LIMIT


class _RulesEditModal(discord.ui.Modal):
    def __init__(self, parent: MgeRulesEditView, current_rules_text: str) -> None:
        current_len = len(current_rules_text or "")
        super().__init__(
            title=f"Edit MGE Rules ({current_len}/{_EMBED_RULES_LIMIT})",
            timeout=300,
        )
        self.parent_view = parent
        self.rules_text = discord.ui.InputText(
            label=f"Rules Text — plain text, sections with # (max {_EMBED_RULES_LIMIT})",
            required=True,
            style=discord.InputTextStyle.long,
            value=current_rules_text,
            placeholder=(
                "Use plain text. Sections: '# Header', bullets: '- item', warnings: '! Warning'\n"
                f"Stay within {_EMBED_RULES_LIMIT} characters. No Discord markdown needed."
            ),
            max_length=_EMBED_RULES_LIMIT,
        )
        self.add_item(self.rules_text)

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await self.parent_view._guard(interaction):
            return

        new_text = str(self.rules_text.value or "").strip()
        text_len = len(new_text)
        if not new_text:
            await send_ephemeral(interaction, "❌ Rules text cannot be empty.")
            return
        if text_len > _EMBED_RULES_LIMIT:
            over_by = text_len - _EMBED_RULES_LIMIT
            await send_ephemeral(
                interaction,
                (
                    "❌ Rules text exceeds the Discord embed Rules field limit "
                    f"(actual: {text_len}, allowed: {_EMBED_RULES_LIMIT}, over by: {over_by})."
                ),
            )
            logger.info(
                "mge_rules_edit_validation_failed event_id=%s actor_discord_id=%s actual_len=%s allowed_len=%s",
                self.parent_view.event_id,
                int(interaction.user.id),
                text_len,
                _EMBED_RULES_LIMIT,
            )
            return

        result = await asyncio.to_thread(
            mge_rules_service.update_event_rules_text,
            event_id=self.parent_view.event_id,
            new_rules_text=new_text,
            actor_discord_id=int(interaction.user.id),
        )
        if not result.success:
            await send_ephemeral(interaction, f"❌ {result.message}")
            return

        refreshed = await self.parent_view._refresh_signup_embed(interaction.client)
        msg = f"✅ {result.message}"
        if not refreshed:
            msg += "\n⚠️ Rules saved, but embed refresh failed. Use Refresh Embed."
        await send_ephemeral(interaction, msg)


class MgeRulesEditView(discord.ui.View):
    """Leadership/admin rules editor with modal edit + reset-to-default."""

    def __init__(self, *, event_id: int, timeout: float | None = 300) -> None:
        super().__init__(timeout=timeout)
        self.event_id = int(event_id)

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if not is_admin_or_leadership_interaction(interaction):
            await send_ephemeral(interaction, "❌ Leadership/admin only.")
            return False
        return True

    async def _refresh_signup_embed(self, bot: discord.Client) -> bool:
        ctx = await asyncio.to_thread(mge_rules_service.get_event_rules_context, self.event_id)
        if not ctx:
            return False
        channel_id = ctx.get("SignupEmbedChannelId")
        if channel_id is None:
            return False
        try:
            return await mge_embed_manager.sync_event_signup_embed(
                bot=bot,
                event_id=self.event_id,
                signup_channel_id=int(channel_id),
            )
        except Exception:
            logger.exception("mge_rules_refresh_embed_failed event_id=%s", self.event_id)
            return False

    @discord.ui.button(
        label="Edit Rules Text",
        style=discord.ButtonStyle.primary,
        custom_id="mge_rules_edit_text",
    )
    async def edit_rules_text(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        if not await self._guard(interaction):
            return

        ctx = await asyncio.to_thread(mge_rules_service.get_event_rules_context, self.event_id)
        if not ctx:
            await send_ephemeral(interaction, "❌ Event not found.")
            return

        current_text = str(ctx.get("RulesText") or "")
        if len(current_text) > _MAX_RULES_TEXT_LEN:
            await send_ephemeral(
                interaction,
                (
                    f"⚠️ Current rules exceed {_MAX_RULES_TEXT_LEN} characters and cannot be safely prefilled in a modal.\n"
                    "Please use **Reset To Mode Default** first, then re-apply a shorter edited version."
                ),
            )
            return
        if len(current_text) > _EMBED_RULES_LIMIT:
            current_len = len(current_text)
            over_by = current_len - _EMBED_RULES_LIMIT
            await send_ephemeral(
                interaction,
                (
                    "⚠️ Current rules are too long for Discord embed publishing and cannot be edited safely here.\n"
                    f"Current length: {current_len} • Allowed: {_EMBED_RULES_LIMIT} • Over by: {over_by}\n"
                    "Use **Reset To Mode Default** first, then apply a shorter edited version."
                ),
            )
            return

        await interaction.response.send_modal(_RulesEditModal(self, current_text))

    @discord.ui.button(
        label="Reset To Mode Default",
        style=discord.ButtonStyle.secondary,
        custom_id="mge_rules_reset_mode_default",
    )
    async def reset_to_mode_default(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        if not await self._guard(interaction):
            return

        result = await asyncio.to_thread(
            mge_rules_service.reset_event_rules_to_mode_default,
            event_id=self.event_id,
            actor_discord_id=int(interaction.user.id),
        )
        if not result.success:
            await send_ephemeral(interaction, f"❌ {result.message}")
            return

        refreshed = await self._refresh_signup_embed(interaction.client)
        msg = f"✅ {result.message}"
        if not refreshed:
            msg += "\n⚠️ Rules reset, but embed refresh failed. Use Refresh Embed."
        await send_ephemeral(interaction, msg)

    @discord.ui.button(
        label="Close",
        style=discord.ButtonStyle.danger,
        custom_id="mge_rules_close",
    )
    async def close(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        self.stop()
        await send_ephemeral(interaction, "Closed rules editor.")
