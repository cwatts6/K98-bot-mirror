from __future__ import annotations

import asyncio
import logging
from typing import Any

import discord

from inventory import export_service, reporting_service
from inventory.models import (
    InventoryExportFormat,
    InventoryReportRange,
    InventoryReportView,
    InventoryReportVisibility,
    RegisteredGovernor,
)
from inventory.report_image_renderer import render_inventory_reports

logger = logging.getLogger(__name__)

REPORT_VIEW_OPTIONS = {
    "All": InventoryReportView.ALL,
    "RSS": InventoryReportView.RESOURCES,
    "Speedups": InventoryReportView.SPEEDUPS,
    "Materials": InventoryReportView.MATERIALS,
}


async def _avatar_bytes(user: Any) -> bytes | None:
    avatar = getattr(user, "display_avatar", None)
    if avatar is None:
        return None
    try:
        return await avatar.read()
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug("inventory_report_avatar_read_failed user_id=%s", getattr(user, "id", None))
        return None


async def _discord_files(payload, avatar_bytes: bytes | None) -> list[discord.File]:
    rendered = await asyncio.to_thread(render_inventory_reports, payload, avatar_bytes=avatar_bytes)
    return [discord.File(item.image_bytes, filename=item.filename) for item in rendered]


def _message_content(payload) -> str:
    categories = []
    if payload.resources:
        categories.append("Resources")
    if payload.speedups:
        categories.append("Speedups")
    if payload.materials:
        categories.append("Materials")
    if not categories:
        view_label = "inventory" if payload.view == InventoryReportView.ALL else payload.view.value
        return (
            f"No approved {view_label} records found for GovernorID "
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
        requester_name: str = "user",
        ephemeral: bool = False,
    ) -> None:
        super().__init__(timeout=900)
        self.requester_id = int(requester_id)
        self.governor = governor
        self.report_view = report_view
        self.range_key = range_key
        self.avatar_bytes = avatar_bytes
        self.requester_name = requester_name
        self.ephemeral = ephemeral
        self._buttons: dict[InventoryReportRange, InventoryRangeButton] = {}
        for item in InventoryReportRange:
            button = InventoryRangeButton(parent=self, range_key=item)
            self._buttons[item] = button
            self.add_item(button)
        for export_format in (
            InventoryExportFormat.EXCEL,
            InventoryExportFormat.CSV,
            InventoryExportFormat.GOOGLE_SHEETS,
        ):
            self.add_item(InventoryExportButton(parent=self, export_format=export_format))
        self._sync_styles()

    def _sync_styles(self) -> None:
        for key, button in self._buttons.items():
            button.style = (
                discord.ButtonStyle.primary
                if key == self.range_key
                else discord.ButtonStyle.secondary
            )

    async def refresh_report(self, interaction: discord.Interaction) -> None:
        if int(interaction.user.id) != self.requester_id:
            await interaction.response.send_message(
                "This inventory report is not yours. Run `/myinventory` to get your own.",
                ephemeral=True,
            )
            return

        try:
            await interaction.response.defer(ephemeral=self.ephemeral)
        except Exception:
            pass
        payload = await reporting_service.build_inventory_report_payload(
            discord_user_id=self.requester_id,
            governor=self.governor,
            view=self.report_view,
            range_key=self.range_key,
        )
        files = await _discord_files(payload, self.avatar_bytes)
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
        await self.parent_view.refresh_report(interaction)


class InventoryExportButton(discord.ui.Button):
    def __init__(self, *, parent: InventoryRangeView, export_format: InventoryExportFormat) -> None:
        label = {
            InventoryExportFormat.EXCEL: "Export Excel",
            InventoryExportFormat.CSV: "Export CSV",
            InventoryExportFormat.GOOGLE_SHEETS: "Export Sheets",
        }[export_format]
        super().__init__(
            label=label,
            style=discord.ButtonStyle.secondary,
            custom_id=f"inventory_report_export_{export_format.value}",
            row=1,
        )
        self.parent_view = parent
        self.export_format = export_format

    async def callback(self, interaction: discord.Interaction) -> None:
        parent = self.parent_view
        if int(interaction.user.id) != parent.requester_id:
            await interaction.response.send_message(
                "This inventory report is not yours. Run `/myinventory` to export your own.",
                ephemeral=True,
            )
            return
        await interaction.response.defer(ephemeral=True)
        export_file = None
        try:
            export_file = await export_service.build_inventory_export_file(
                discord_user_id=parent.requester_id,
                username=parent.requester_name,
                export_format=self.export_format,
                view=parent.report_view,
                governor_id=parent.governor.governor_id,
                lookback_days=reporting_service.REPORT_RANGE_DAYS[parent.range_key],
                discord_user=interaction.user,
            )
            file_obj = discord.File(str(export_file.path), filename=export_file.filename)
            await interaction.followup.send(
                content=(
                    "Inventory export ready. "
                    f"`{export_file.row_count}` raw approved row(s), "
                    f"`{len(export_file.governor_ids)}` governor(s)."
                ),
                file=file_obj,
                ephemeral=True,
            )
        except PermissionError as exc:
            await interaction.followup.send(str(exc), ephemeral=True)
        except ValueError as exc:
            await interaction.followup.send(str(exc), ephemeral=True)
        except Exception:
            logger.exception(
                "inventory_report_export_button_failed user_id=%s governor_id=%s",
                parent.requester_id,
                parent.governor.governor_id,
            )
            await interaction.followup.send(
                "Inventory export failed. Please try again or contact an admin.",
                ephemeral=True,
            )
        finally:
            export_service.cleanup_export_file(export_file)


async def _send_inventory_report_message(
    *,
    send: Any,
    user: Any,
    requester_id: int,
    governor: RegisteredGovernor,
    report_view: InventoryReportView,
    range_key: InventoryReportRange,
    visibility: InventoryReportVisibility,
) -> None:
    avatar = await _avatar_bytes(user)
    payload = await reporting_service.build_inventory_report_payload(
        discord_user_id=int(requester_id),
        governor=governor,
        view=report_view,
        range_key=range_key,
    )
    ephemeral = visibility == InventoryReportVisibility.ONLY_ME
    view_obj = InventoryRangeView(
        requester_id=int(requester_id),
        governor=governor,
        report_view=report_view,
        range_key=range_key,
        avatar_bytes=avatar,
        requester_name=getattr(user, "display_name", None) or getattr(user, "name", "user"),
        ephemeral=ephemeral,
    )
    files = await _discord_files(payload, avatar)
    if files:
        await send(
            content=_message_content(payload),
            files=files,
            view=view_obj,
            ephemeral=ephemeral,
        )
    else:
        await send(
            content=_message_content(payload),
            view=view_obj,
            ephemeral=ephemeral,
        )


async def send_inventory_report(
    *,
    ctx: discord.ApplicationContext,
    governor: RegisteredGovernor,
    report_view: InventoryReportView,
    range_key: InventoryReportRange,
    visibility: InventoryReportVisibility,
) -> None:
    await _send_inventory_report_message(
        send=ctx.followup.send,
        user=ctx.user,
        requester_id=int(ctx.user.id),
        governor=governor,
        report_view=report_view,
        range_key=range_key,
        visibility=visibility,
    )


class InventoryPreferenceView(discord.ui.View):
    def __init__(self, *, requester_id: int) -> None:
        super().__init__(timeout=300)
        self.requester_id = int(requester_id)

    async def _save(
        self, interaction: discord.Interaction, visibility: InventoryReportVisibility
    ) -> None:
        if int(interaction.user.id) != self.requester_id:
            await interaction.response.send_message(
                "This preference prompt is not for you.", ephemeral=True
            )
            return
        await interaction.response.defer(ephemeral=True)
        result = await reporting_service.write_visibility_preference(
            self.requester_id,
            visibility,
        )
        if not result.ok or result.visibility != visibility:
            await interaction.followup.send(
                "Inventory report preference could not be saved. "
                "Your previous setting is unchanged. Please try again in a moment.",
                ephemeral=True,
            )
            return
        for item in self.children:
            item.disabled = True
        self.stop()
        await interaction.followup.send(
            "Inventory report preference saved. Run `/myinventory` again to view your report. "
            "You can change this later with `/inventory_preferences`.",
            ephemeral=True,
        )
        try:
            await interaction.edit_original_response(view=self)
        except Exception:
            logger.debug("inventory_preference_prompt_update_failed", exc_info=True)

    @discord.ui.button(
        label="Only Me",
        style=discord.ButtonStyle.primary,
        custom_id="inventory_pref_only_me",
    )
    async def only_me(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        await self._save(interaction, InventoryReportVisibility.ONLY_ME)

    @discord.ui.button(
        label="Public",
        style=discord.ButtonStyle.secondary,
        custom_id="inventory_pref_public",
    )
    async def public(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        await self._save(interaction, InventoryReportVisibility.PUBLIC)


async def send_inventory_preference_prompt(ctx: discord.ApplicationContext) -> None:
    await ctx.followup.send(
        "Choose how `/myinventory` should post your reports. "
        "Governor VIP is managed from `/me accounts` → Manage Accounts → Update VIP.",
        view=InventoryPreferenceView(requester_id=int(ctx.user.id)),
        ephemeral=True,
    )


class InventoryReportSelectionView(discord.ui.View):
    def __init__(
        self,
        *,
        ctx: discord.ApplicationContext,
        governors: list[RegisteredGovernor],
        visibility: InventoryReportVisibility,
    ) -> None:
        super().__init__(timeout=300)
        self.ctx = ctx
        self.requester_id = int(ctx.user.id)
        self.governors_by_id = {item.governor_id: item for item in governors}
        self.selected_governor_id = governors[0].governor_id if len(governors) == 1 else None
        self.selected_view = InventoryReportView.ALL
        self.visibility = visibility
        self._completed = False
        if len(governors) > 1:
            self.add_item(InventoryGovernorSelect(governors))
        self.add_item(InventoryOutputSelect())

    async def send_report(self, interaction: discord.Interaction) -> None:
        if int(interaction.user.id) != self.requester_id:
            await interaction.response.send_message(
                "This inventory selector is not for you. Run `/myinventory` to get your own.",
                ephemeral=True,
            )
            return
        if self._completed:
            await interaction.response.send_message(
                "This inventory selector has already been used. Run `/myinventory` again to choose another report.",
                ephemeral=True,
            )
            return
        if self.selected_governor_id is None:
            await interaction.response.send_message("Choose a governor first.", ephemeral=True)
            return
        governor = self.governors_by_id.get(int(self.selected_governor_id))
        if governor is None:
            await interaction.response.send_message(
                "Selected governor is no longer available. Run `/myinventory` again.",
                ephemeral=True,
            )
            return
        await interaction.response.defer(
            ephemeral=self.visibility == InventoryReportVisibility.ONLY_ME
        )
        self._completed = True
        for item in self.children:
            item.disabled = True
        self.stop()
        try:
            await interaction.edit_original_response(
                content="Inventory report selected.",
                view=self,
            )
        except Exception:
            logger.debug("inventory_report_selector_complete_update_failed", exc_info=True)
        await _send_inventory_report_message(
            send=interaction.followup.send,
            user=interaction.user,
            requester_id=self.requester_id,
            governor=governor,
            report_view=self.selected_view,
            range_key=InventoryReportRange.ONE_MONTH,
            visibility=self.visibility,
        )

    @discord.ui.button(
        label="Show Report",
        style=discord.ButtonStyle.primary,
        custom_id="inventory_report_show",
        row=2,
    )
    async def show_report(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        await self.send_report(interaction)


class InventoryGovernorSelect(discord.ui.Select):
    def __init__(self, governors: list[RegisteredGovernor]) -> None:
        options = [
            discord.SelectOption(
                label=item.governor_name[:100],
                value=str(item.governor_id),
                description=item.account_type[:100],
            )
            for item in governors
        ]
        super().__init__(
            placeholder="Select Governor",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, InventoryReportSelectionView):
            return
        if getattr(view, "_completed", False):
            await interaction.response.send_message(
                "This inventory selector has already been used.", ephemeral=True
            )
            return
        if int(interaction.user.id) != view.requester_id:
            await interaction.response.send_message("This selector is not for you.", ephemeral=True)
            return
        view.selected_governor_id = int(self.values[0])
        await interaction.response.defer(ephemeral=True)


class InventoryOutputSelect(discord.ui.Select):
    def __init__(self) -> None:
        options = [
            discord.SelectOption(label=label, value=view.value)
            for label, view in REPORT_VIEW_OPTIONS.items()
        ]
        super().__init__(
            placeholder="Select Output",
            min_values=1,
            max_values=1,
            options=options,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, InventoryReportSelectionView):
            return
        if getattr(view, "_completed", False):
            await interaction.response.send_message(
                "This inventory selector has already been used.", ephemeral=True
            )
            return
        if int(interaction.user.id) != view.requester_id:
            await interaction.response.send_message("This selector is not for you.", ephemeral=True)
            return
        view.selected_view = InventoryReportView(self.values[0])
        await interaction.response.defer(ephemeral=True)


async def start_myinventory_command(
    *,
    ctx: discord.ApplicationContext,
    visibility: InventoryReportVisibility,
) -> None:
    governors = await reporting_service.get_registered_governors_for_user(int(ctx.user.id))
    if not governors:
        await ctx.followup.send(
            "I do not see any governors registered to you. Use `/register_governor` first.",
            ephemeral=True,
        )
        return
    await ctx.followup.send(
        "Choose the inventory report to view:",
        view=InventoryReportSelectionView(ctx=ctx, governors=governors, visibility=visibility),
        ephemeral=True,
    )
