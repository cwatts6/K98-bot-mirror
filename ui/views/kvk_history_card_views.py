from __future__ import annotations

import asyncio
from collections.abc import Callable
from io import BytesIO
import logging

import discord

from kvk.models.kvk_history_payload import KvkHistoryPayload, RenderedKvkHistoryCard
from kvk.rendering.kvk_history_renderer import (
    build_last3_text_fallback,
    render_kvk_history_summary_card,
    render_kvk_history_trends_card,
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
        self._trends_bytes: bytes | None = None
        self._trends_filename: str | None = None
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

    async def _send_unavailable_notice(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.followup.send(
                "This history card message is no longer available. Run `/kvk history` again.",
                ephemeral=True,
            )
        except Exception:
            logger.debug("kvk_history_unavailable_notice_failed", exc_info=True)

    async def _edit_host_message(
        self,
        interaction: discord.Interaction,
        *,
        build_kwargs: Callable[[], dict] | None = None,
        **kwargs,
    ) -> bool:
        def fresh_kwargs() -> dict:
            return build_kwargs() if build_kwargs is not None else dict(kwargs)

        await self._defer_interaction(interaction)
        message = getattr(interaction, "message", None)
        flags = getattr(message, "flags", None)
        is_ephemeral_message = bool(getattr(flags, "ephemeral", False))
        if message is not None and not is_ephemeral_message:
            self.message = message
            try:
                await message.edit(**fresh_kwargs())
                return True
            except discord.NotFound:
                logger.warning(
                    "kvk_history_host_message_missing governor_id=%s",
                    self.payload.governor_id,
                    exc_info=True,
                )
            except Exception:
                logger.debug("kvk_history_host_message_edit_failed", exc_info=True)
        try:
            await interaction.edit_original_response(**fresh_kwargs())
            return True
        except discord.NotFound:
            logger.warning(
                "kvk_history_original_response_missing governor_id=%s",
                self.payload.governor_id,
                exc_info=True,
            )
        except Exception:
            logger.debug("kvk_history_original_response_edit_failed", exc_info=True)
        await self._send_unavailable_notice(interaction)
        return False

    async def _show_history(self, interaction: discord.Interaction) -> None:
        if not await self._check_user(interaction):
            return
        await self._edit_host_message(
            interaction,
            build_kwargs=lambda: {
                "content": None,
                "embeds": [],
                "attachments": [],
                "files": [self._history_file()],
                "view": self,
            },
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
            summary_bytes = self._summary_bytes
            summary_filename = self._summary_filename
            if summary_bytes is not None and summary_filename is not None:
                await self._edit_host_message(
                    interaction,
                    build_kwargs=lambda: {
                        "content": None,
                        "embeds": [],
                        "attachments": [],
                        "files": [discord.File(BytesIO(summary_bytes), filename=summary_filename)],
                        "view": self,
                    },
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

    async def _show_trends(self, interaction: discord.Interaction) -> None:
        if not await self._check_user(interaction):
            return
        await self._defer_interaction(interaction)
        try:
            if self._trends_bytes is None or self._trends_filename is None:
                rendered = await asyncio.to_thread(
                    render_kvk_history_trends_card,
                    self.payload,
                    avatar_bytes=self.avatar_bytes,
                )
                if rendered is not None:
                    self._trends_bytes = rendered.image_bytes.getvalue()
                    self._trends_filename = rendered.filename
            trends_bytes = self._trends_bytes
            trends_filename = self._trends_filename
            if trends_bytes is not None and trends_filename is not None:
                await self._edit_host_message(
                    interaction,
                    build_kwargs=lambda: {
                        "content": None,
                        "embeds": [],
                        "attachments": [],
                        "files": [discord.File(BytesIO(trends_bytes), filename=trends_filename)],
                        "view": self,
                    },
                )
                return
        except Exception:
            logger.exception(
                "kvk_history_trends_card_render_or_send_failed governor_id=%s",
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

    @discord.ui.button(label="Trends", style=discord.ButtonStyle.secondary)
    async def trends(self, _button: discord.ui.Button, interaction: discord.Interaction) -> None:
        await self._show_trends(interaction)

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
