from __future__ import annotations

import logging
from typing import Any

import discord

from inventory import reporting_service
from inventory.models import (
    InventoryReportRange,
    InventoryReportView,
    InventoryReportVisibility,
    RegisteredGovernor,
)
from inventory.report_image_renderer import render_inventory_reports

logger = logging.getLogger(__name__)


async def _avatar_bytes(user: Any) -> bytes | None:
    avatar = getattr(user, "display_avatar", None)
    if avatar is None:
        return None
    try:
        return await avatar.read()
    except Exception:
        logger.debug("inventory_report_avatar_read_failed user_id=%s", getattr(user, "id", None))
        return None


def _discord_files(payload, avatar_bytes: bytes | None) -> list[discord.File]:
    rendered = render_inventory_reports(payload, avatar_bytes=avatar_bytes)
    return [discord.File(item.image_bytes, filename=item.filename) for item in rendered]


def _message_content(payload) -> str:
    categories = []
    if payload.resources:
        categories.append("Resources")
    if payload.speedups:
        categories.append("Speedups")
    if not categories:
        return (
            f"No approved {payload.view.value} inventory records found for GovernorID "
            f"`{payload.governor_id}` in range `{payload.range_key.value}`."
        )
    return (
        f"Inventory report for **{payload.governor_name}** (`{payload.governor_id}`) "
        f"- {', '.join(categories)} - `{payload.range_key.value}`"
    )


class InventoryRangeView(discord.ui.View):
    def __init__(
        self,
        *,
        requester_id: int,
        governor: RegisteredGovernor,
        report_view: InventoryReportView,
        range_key: InventoryReportRange,
        avatar_bytes: bytes | None,
    ) -> None:
        super().__init__(timeout=900)
        self.requester_id = int(requester_id)
        self.governor = governor
        self.report_view = report_view
        self.range_key = range_key
        self.avatar_bytes = avatar_bytes
        self._buttons: dict[InventoryReportRange, InventoryRangeButton] = {}
        for item in InventoryReportRange:
            button = InventoryRangeButton(parent=self, range_key=item)
            self._buttons[item] = button
            self.add_item(button)
        self._sync_styles()

    def _sync_styles(self) -> None:
        for key, button in self._buttons.items():
            button.style = (
                discord.ButtonStyle.primary
                if key == self.range_key
                else discord.ButtonStyle.secondary
            )

    async def refresh(self, interaction: discord.Interaction) -> None:
        if int(interaction.user.id) != self.requester_id:
            await interaction.response.send_message(
                "This inventory report is not yours. Run `/myinventory` to get your own.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        payload = await reporting_service.build_inventory_report_payload(
            discord_user_id=self.requester_id,
            governor=self.governor,
            view=self.report_view,
            range_key=self.range_key,
        )
        files = _discord_files(payload, self.avatar_bytes)
        self._sync_styles()
        if files:
            await interaction.edit_original_response(
                content=_message_content(payload),
                attachments=[],
                files=files,
                view=self,
            )
        else:
            await interaction.edit_original_response(
                content=_message_content(payload),
                attachments=[],
                view=self,
            )


class InventoryRangeButton(discord.ui.Button):
    def __init__(self, *, parent: InventoryRangeView, range_key: InventoryReportRange) -> None:
        super().__init__(
            label=range_key.value,
            style=discord.ButtonStyle.secondary,
            custom_id=f"inventory_report_range_{range_key.value.lower()}",
        )
        self.parent_view = parent
        self.range_key = range_key

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent_view.range_key = self.range_key
        await self.parent_view.refresh(interaction)


async def send_inventory_report(
    *,
    ctx: discord.ApplicationContext,
    governor: RegisteredGovernor,
    report_view: InventoryReportView,
    range_key: InventoryReportRange,
    visibility: InventoryReportVisibility,
) -> None:
    avatar = await _avatar_bytes(ctx.user)
    payload = await reporting_service.build_inventory_report_payload(
        discord_user_id=int(ctx.user.id),
        governor=governor,
        view=report_view,
        range_key=range_key,
    )
    view_obj = InventoryRangeView(
        requester_id=int(ctx.user.id),
        governor=governor,
        report_view=report_view,
        range_key=range_key,
        avatar_bytes=avatar,
    )
    files = _discord_files(payload, avatar)
    ephemeral = visibility == InventoryReportVisibility.ONLY_ME
    if files:
        await ctx.followup.send(
            content=_message_content(payload),
            files=files,
            view=view_obj,
            ephemeral=ephemeral,
        )
    else:
        await ctx.followup.send(
            content=_message_content(payload),
            view=view_obj,
            ephemeral=ephemeral,
        )


async def start_myinventory_command(
    *,
    ctx: discord.ApplicationContext,
    governor_id: int | None,
    report_view: InventoryReportView,
    range_key: InventoryReportRange,
    visibility: InventoryReportVisibility,
) -> None:
    governor = await reporting_service.resolve_governor_for_report(
        discord_user_id=int(ctx.user.id),
        governor_id=governor_id,
        discord_user=ctx.user,
    )
    if governor is None:
        governors = await reporting_service.get_registered_governors_for_user(int(ctx.user.id))
        if not governors:
            await ctx.followup.send(
                "I do not see any governors registered to you. Use `/register_governor` first.",
                ephemeral=True,
            )
            return
        await ctx.followup.send(
            "You have multiple registered governors. Use the `governor` option with `/myinventory`.",
            ephemeral=True,
        )
        return

    await send_inventory_report(
        ctx=ctx,
        governor=governor,
        report_view=report_view,
        range_key=range_key,
        visibility=visibility,
    )
