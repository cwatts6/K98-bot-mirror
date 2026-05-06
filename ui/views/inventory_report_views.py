from __future__ import annotations

import asyncio
import logging
from typing import Any

import discord

from inventory import export_service, profile_service, reporting_service
from inventory.models import (
    InventoryExportFormat,
    InventoryGovernorProfile,
    InventoryReportRange,
    InventoryReportView,
    InventoryReportVisibility,
    RegisteredGovernor,
)
from inventory.report_image_renderer import render_inventory_reports
from inventory.vip_levels import VIP_LABELS, InventoryVipLevel, normalize_vip_level

logger = logging.getLogger(__name__)

REPORT_VIEW_OPTIONS = {
    "All": InventoryReportView.ALL,
    "RSS": InventoryReportView.RESOURCES,
    "Speedups": InventoryReportView.SPEEDUPS,
    "Materials": InventoryReportView.MATERIALS,
}

VIP_SELECT_OPTIONS = [
    InventoryVipLevel.UNKNOWN,
    InventoryVipLevel.VIP_14_OR_LESS,
    InventoryVipLevel.VIP_15,
    InventoryVipLevel.VIP_16,
    InventoryVipLevel.VIP_17,
    InventoryVipLevel.VIP_18,
    InventoryVipLevel.VIP_19,
    InventoryVipLevel.SVIP,
]


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

    async def refresh(self, interaction: discord.Interaction) -> None:
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
        await self.parent_view.refresh(interaction)


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
        await reporting_service.resolve_visibility(
            discord_user_id=self.requester_id,
            selected_visibility=visibility,
        )
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

    @discord.ui.button(
        label="Update Governor VIP",
        style=discord.ButtonStyle.secondary,
        custom_id="inventory_pref_vip",
    )
    async def update_vip(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        if int(interaction.user.id) != self.requester_id:
            await interaction.response.send_message(
                "This preference prompt is not for you.", ephemeral=True
            )
            return
        await interaction.response.defer(ephemeral=True)
        governors = await reporting_service.get_registered_governors_for_user(self.requester_id)
        if not governors:
            await interaction.followup.send(
                "I do not see any governors registered to you. Use `/register_governor` first.",
                ephemeral=True,
            )
            return
        profiles = await asyncio.gather(
            *(profile_service.fetch_inventory_profile(g.governor_id) for g in governors)
        )
        profiles_by_governor_id = {p.governor_id: p for p in profiles}
        await interaction.followup.send(
            "Choose a governor and VIP level:",
            view=InventoryVipPreferenceView(
                requester_id=self.requester_id,
                governors=governors,
                profiles_by_governor_id=profiles_by_governor_id,
            ),
            ephemeral=True,
        )


class InventoryVipPreferenceView(discord.ui.View):
    def __init__(
        self,
        *,
        requester_id: int,
        governors: list[RegisteredGovernor],
        profiles_by_governor_id: dict[int, InventoryGovernorProfile] | None = None,
    ) -> None:
        super().__init__(timeout=300)
        self.requester_id = int(requester_id)
        self.governors_by_id = {item.governor_id: item for item in governors}
        self.profiles_by_governor_id: dict[int, InventoryGovernorProfile] = (
            profiles_by_governor_id or {}
        )
        self.message: discord.Message | None = None
        initial_governor_id = governors[0].governor_id if len(governors) == 1 else None
        self.selected_governor_id = initial_governor_id
        initial_profile = (
            self.profiles_by_governor_id.get(initial_governor_id)
            if initial_governor_id is not None
            else None
        )
        self.selected_vip_level = normalize_vip_level(
            initial_profile.vip_level_code if initial_profile else None
        )
        self._completed = False
        if len(governors) > 1:
            self.add_item(InventoryVipGovernorSelect(governors))
        self.add_item(
            InventoryVipLevelSelect(
                initial_level=(
                    self.selected_vip_level
                    if initial_profile and initial_profile.vip_level_code
                    else None
                )
            )
        )

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            pass

    async def save(self, interaction: discord.Interaction) -> None:
        if int(interaction.user.id) != self.requester_id:
            await interaction.response.send_message(
                "This VIP preference prompt is not for you.", ephemeral=True
            )
            return
        if self._completed:
            await interaction.response.send_message(
                "This VIP preference prompt has already been used. Run `/inventory_preferences` again to update another governor.",
                ephemeral=True,
            )
            return
        if self.selected_governor_id is None:
            await interaction.response.send_message("Choose a governor first.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        try:
            profile = await profile_service.update_inventory_vip(
                discord_user_id=self.requester_id,
                governor_id=int(self.selected_governor_id),
                vip_level_code=self.selected_vip_level.value,
                discord_user=interaction.user,
            )
        except PermissionError as exc:
            await interaction.followup.send(
                str(exc) or "You do not have permission to update this governor's VIP preference.",
                ephemeral=True,
            )
            return
        except ValueError as exc:
            await interaction.followup.send(
                str(exc) or "The selected VIP preference is invalid.",
                ephemeral=True,
            )
            return
        except Exception:
            logger.exception("inventory_vip_preference_save_failed")
            await interaction.followup.send(
                "Unable to save the VIP preference right now. Please try again later.",
                ephemeral=True,
            )
            return
        self._completed = True
        for item in self.children:
            item.disabled = True
        self.stop()
        governor = self.governors_by_id.get(int(self.selected_governor_id))
        governor_label = (
            f"{governor.governor_name} (`{governor.governor_id}`)"
            if governor
            else f"`{self.selected_governor_id}`"
        )
        await interaction.followup.send(
            _vip_saved_message(governor_label, profile.vip_level_label),
            ephemeral=True,
        )
        try:
            await interaction.edit_original_response(view=self)
        except Exception:
            logger.debug("inventory_vip_preference_prompt_update_failed", exc_info=True)

    @discord.ui.button(
        label="Save VIP",
        style=discord.ButtonStyle.primary,
        custom_id="inventory_vip_save",
        row=2,
    )
    async def save_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        await self.save(interaction)


class InventoryVipGovernorSelect(discord.ui.Select):
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
        if not isinstance(view, InventoryVipPreferenceView):
            return
        if view._completed:
            await interaction.response.send_message(
                "This VIP preference prompt has already been used.", ephemeral=True
            )
            return
        if int(interaction.user.id) != view.requester_id:
            await interaction.response.send_message("This selector is not for you.", ephemeral=True)
            return
        view.selected_governor_id = int(self.values[0])
        profile = view.profiles_by_governor_id.get(view.selected_governor_id)
        view.selected_vip_level = normalize_vip_level(profile.vip_level_code if profile else None)
        for option in self.options:
            option.default = option.value == self.values[0]
        for child in view.children:
            if isinstance(child, InventoryVipLevelSelect):
                child.sync_default(
                    view.selected_vip_level if profile and profile.vip_level_code else None
                )
        await _refresh_select_message(interaction, view)


class InventoryVipLevelSelect(discord.ui.Select):
    def __init__(self, initial_level: InventoryVipLevel | None = None) -> None:
        options = [
            discord.SelectOption(
                label=VIP_LABELS[level],
                value=level.value,
                default=initial_level is not None and level == initial_level,
            )
            for level in VIP_SELECT_OPTIONS
        ]
        super().__init__(
            placeholder="Select VIP",
            min_values=1,
            max_values=1,
            options=options,
            row=1,
        )

    def sync_default(self, selected_level: InventoryVipLevel | None) -> None:
        for option in self.options:
            option.default = selected_level is not None and option.value == selected_level.value

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, InventoryVipPreferenceView):
            return
        if view._completed:
            await interaction.response.send_message(
                "This VIP preference prompt has already been used.", ephemeral=True
            )
            return
        if int(interaction.user.id) != view.requester_id:
            await interaction.response.send_message("This selector is not for you.", ephemeral=True)
            return
        view.selected_vip_level = normalize_vip_level(self.values[0])
        self.sync_default(view.selected_vip_level)
        await _refresh_select_message(interaction, view)


async def _refresh_select_message(interaction: discord.Interaction, view: discord.ui.View) -> None:
    try:
        await interaction.response.edit_message(view=view)
    except Exception:
        logger.debug("inventory_select_message_refresh_failed", exc_info=True)
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass


def _vip_saved_message(governor_label: str, vip_level_label: str) -> str:
    message = f"VIP saved for {governor_label}: **{vip_level_label}**."
    if vip_level_label == VIP_LABELS[InventoryVipLevel.UNKNOWN]:
        return f"{message} Default capacity assumptions will be used."
    return message


async def send_inventory_preference_prompt(ctx: discord.ApplicationContext) -> None:
    await ctx.followup.send(
        "Choose how `/myinventory` should post your reports, or update a governor VIP level.",
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
