from __future__ import annotations

import asyncio
import logging
from typing import Any

import discord

from prekvk import report_service
from prekvk.models import PREKVK_REPORT_LIMITS, PreKvkReportPayload, PreKvkReportSort
from prekvk.report_image_renderer import render_prekvk_report

logger = logging.getLogger(__name__)


async def _discord_file(payload: PreKvkReportPayload) -> discord.File | None:
    rendered = await asyncio.to_thread(render_prekvk_report, payload)
    if rendered is None:
        return None
    return discord.File(rendered.image_bytes, filename=rendered.filename)


def _content(payload: PreKvkReportPayload) -> str:
    if not payload.rows:
        return f"No PreKvK import found for KVK `{payload.kvk_no}`."
    return (
        f"PreKvK report for KVK `{payload.kvk_no}` - "
        f"sorted by **{report_service.SORT_LABELS[payload.sort_by]}**, Top `{payload.limit}`."
    )


class PreKvkReportView(discord.ui.View):
    def __init__(
        self,
        *,
        requester_id: int,
        kvk_no: int,
        sort_by: PreKvkReportSort,
        limit: int,
        timeout: float = 300.0,
    ) -> None:
        super().__init__(timeout=timeout)
        self.requester_id = int(requester_id)
        self.kvk_no = int(kvk_no)
        self.sort_by = sort_by
        self.limit = int(limit)
        self.message: discord.Message | None = None
        self.sort_select = discord.ui.Select(
            placeholder="Sort by",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="Overall", value=PreKvkReportSort.OVERALL.value),
                discord.SelectOption(label="Stage 1", value=PreKvkReportSort.STAGE1.value),
                discord.SelectOption(label="Stage 2", value=PreKvkReportSort.STAGE2.value),
                discord.SelectOption(label="Stage 3", value=PreKvkReportSort.STAGE3.value),
            ],
            row=0,
        )
        self.sort_select.callback = self.on_sort_change
        self.add_item(self.sort_select)
        for option_limit in PREKVK_REPORT_LIMITS:
            button = discord.ui.Button(
                label=f"Top {option_limit}",
                style=discord.ButtonStyle.secondary,
                custom_id=f"prekvk_report_top_{option_limit}",
                row=1,
            )
            button.callback = self._make_limit_handler(option_limit)
            self.add_item(button)
        self._sync_controls()

    def _sync_controls(self) -> None:
        for option in self.sort_select.options:
            option.default = option.value == self.sort_by.value
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.label and item.label.startswith("Top "):
                item.style = (
                    discord.ButtonStyle.primary
                    if item.label == f"Top {self.limit}"
                    else discord.ButtonStyle.secondary
                )

    async def _refresh(self, interaction: discord.Interaction) -> None:
        if int(interaction.user.id) != self.requester_id:
            await interaction.response.send_message(
                "This PreKvK report control is not yours. Run `/prekvk report` to open a fresh report.",
                ephemeral=True,
            )
            return
        try:
            await interaction.response.defer()
        except Exception:
            pass
        try:
            payload = await report_service.build_prekvk_report_payload(
                kvk_no=self.kvk_no,
                sort_by=self.sort_by,
                limit=self.limit,
            )
            self._sync_controls()
            file = await _discord_file(payload)
            kwargs: dict[str, Any] = {
                "content": _content(payload),
                "attachments": [],
                "view": self,
            }
            if file is not None:
                kwargs["files"] = [file]
            message = getattr(interaction, "message", None)
            if message is not None:
                self.message = message
                try:
                    await message.edit(**kwargs)
                    return
                except Exception:
                    logger.debug("prekvk_report_host_message_edit_failed", exc_info=True)
            await interaction.edit_original_response(**kwargs)
        except Exception:
            logger.exception(
                "prekvk_report_refresh_failed actor_discord_id=%s kvk_no=%s sort_by=%s limit=%s",
                getattr(interaction.user, "id", None),
                self.kvk_no,
                self.sort_by.value,
                self.limit,
            )
            try:
                await interaction.followup.send(
                    "PreKvK report refresh failed. Please try again or run `/prekvk report` for a fresh report.",
                    ephemeral=True,
                )
            except Exception:
                logger.debug("prekvk_report_refresh_error_response_failed", exc_info=True)

    async def on_sort_change(self, interaction: discord.Interaction) -> None:
        self.sort_by = report_service.parse_report_sort(self.sort_select.values[0])
        await self._refresh(interaction)

    def _make_limit_handler(self, limit: int):
        async def _handler(interaction: discord.Interaction) -> None:
            self.limit = report_service.normalize_report_limit(limit)
            await self._refresh(interaction)

        return _handler

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            logger.debug("prekvk_report_view_timeout_edit_failed", exc_info=True)


async def send_prekvk_report(
    *,
    ctx: discord.ApplicationContext,
    kvk_no: int | None,
    sort_by: PreKvkReportSort,
    limit: int,
) -> None:
    payload = await report_service.build_prekvk_report_payload(
        kvk_no=kvk_no,
        sort_by=sort_by,
        limit=limit,
    )
    view = PreKvkReportView(
        requester_id=int(ctx.user.id),
        kvk_no=payload.kvk_no,
        sort_by=payload.sort_by,
        limit=payload.limit,
    )
    file = await _discord_file(payload)
    kwargs: dict[str, Any] = {"content": _content(payload), "view": view}
    if file is not None:
        kwargs["file"] = file
    try:
        channel = getattr(ctx, "channel", None)
        if channel is not None:
            view.message = await channel.send(**kwargs)
            try:
                await ctx.followup.send("PreKvK report posted.", ephemeral=True)
            except Exception:
                logger.debug("prekvk_report_post_ack_failed", exc_info=True)
            return
        view.message = await ctx.followup.send(wait=True, ephemeral=False, **kwargs)
    except TypeError:
        await ctx.followup.send(ephemeral=False, **kwargs)
        view.message = None
    except Exception:
        logger.debug("prekvk_report_send_failed", exc_info=True)
        view.message = None
        raise
