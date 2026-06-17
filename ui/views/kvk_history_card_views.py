from __future__ import annotations

import asyncio
from io import BytesIO
import logging

import discord

from kvk.models.kvk_history_payload import KvkHistoryPayload, RenderedKvkHistoryCard
from kvk.rendering.kvk_history_renderer import (
    build_last3_text_fallback,
    render_kvk_history_summary_card,
)
from kvk_history_utils import build_history_csv
from services import kvk_history_service

logger = logging.getLogger(__name__)


class KvkHistoryCardView(discord.ui.View):
    def __init__(
        self,
        *,
        payload: KvkHistoryPayload,
        rendered: RenderedKvkHistoryCard,
        author_id: int,
        avatar_bytes: bytes | None = None,
        timeout: float = 300.0,
    ) -> None:
        super().__init__(timeout=timeout)
        self.payload = payload
        self.author_id = author_id
        self.avatar_bytes = avatar_bytes
        self._history_bytes = rendered.image_bytes.getvalue()
        self._history_filename = rendered.filename
        self._summary_bytes: bytes | None = None
        self._summary_filename: str | None = None
        self.message: discord.Message | None = None

    def _history_file(self) -> discord.File:
        return discord.File(BytesIO(self._history_bytes), filename=self._history_filename)

    def _summary_file(self) -> discord.File | None:
        if self._summary_bytes is None or self._summary_filename is None:
            return None
        return discord.File(BytesIO(self._summary_bytes), filename=self._summary_filename)

    async def _check_user(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.author_id:
            return True
        await interaction.response.send_message("This control isn't for you.", ephemeral=True)
        return False

    async def _defer_interaction(self, interaction: discord.Interaction) -> None:
        try:
            if not interaction.response.is_done():
                await interaction.response.defer()
        except Exception:
            pass

    async def _edit_host_message(self, interaction: discord.Interaction, **kwargs) -> None:
        await self._defer_interaction(interaction)
        message = getattr(interaction, "message", None)
        if message is not None:
            self.message = message
            await message.edit(**kwargs)
            return
        await interaction.edit_original_response(**kwargs)

    async def _show_history(self, interaction: discord.Interaction) -> None:
        if not await self._check_user(interaction):
            return
        await self._edit_host_message(
            interaction,
            content=None,
            embeds=[],
            attachments=[],
            files=[self._history_file()],
            view=self,
        )

    async def _show_summary(self, interaction: discord.Interaction) -> None:
        if not await self._check_user(interaction):
            return
        await self._defer_interaction(interaction)
        try:
            if self._summary_bytes is None or self._summary_filename is None:
                rendered = await asyncio.to_thread(
                    render_kvk_history_summary_card,
                    self.payload,
                    avatar_bytes=self.avatar_bytes,
                )
                if rendered is not None:
                    self._summary_bytes = rendered.image_bytes.getvalue()
                    self._summary_filename = rendered.filename
            file = self._summary_file()
            if file is not None:
                await self._edit_host_message(
                    interaction,
                    content=None,
                    embeds=[],
                    attachments=[],
                    files=[file],
                    view=self,
                )
                return
        except Exception:
            logger.exception(
                "kvk_history_summary_card_render_or_send_failed governor_id=%s",
                self.payload.governor_id,
            )
        await self._edit_host_message(
            interaction,
            content=build_last3_text_fallback(self.payload),
            embeds=[],
            attachments=[],
            view=self,
        )

    async def _export_csv(self, interaction: discord.Interaction) -> None:
        if not await self._check_user(interaction):
            return
        await self._defer_interaction(interaction)
        try:
            df = await asyncio.to_thread(
                kvk_history_service.fetch_history_export_for_governors,
                [self.payload.governor_id],
            )
            csv_name, csv_buf = await asyncio.to_thread(build_history_csv, df, "kvk_history.csv")
            data = csv_buf.getvalue() if hasattr(csv_buf, "getvalue") else csv_buf
            await interaction.followup.send(
                content="Here's your CSV export.",
                file=discord.File(fp=BytesIO(data), filename=csv_name),
                ephemeral=True,
            )
        except Exception:
            logger.exception(
                "kvk_history_card_csv_export_failed governor_id=%s",
                self.payload.governor_id,
            )
            await interaction.followup.send("Failed to build CSV export.", ephemeral=True)

    @discord.ui.button(label="History", style=discord.ButtonStyle.primary)
    async def history(self, _button: discord.ui.Button, interaction: discord.Interaction) -> None:
        await self._show_history(interaction)

    @discord.ui.button(label="Summary", style=discord.ButtonStyle.secondary)
    async def summary(self, _button: discord.ui.Button, interaction: discord.Interaction) -> None:
        await self._show_summary(interaction)

    @discord.ui.button(label="Export CSV", style=discord.ButtonStyle.secondary)
    async def export_csv(
        self, _button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        await self._export_csv(interaction)

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            logger.debug("kvk_history_card_view_timeout_edit_failed", exc_info=True)
