"""Private selected-governor Inventory reports for the ``/me`` command centre."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from io import BytesIO
import logging
from math import ceil
import time
from typing import Any

import discord

from bot_config import INVENTORY_UPLOAD_CHANNEL_ID
from core.interaction_safety import safe_defer
from inventory import export_service, reporting_service
from inventory.models import (
    InventoryExportFormat,
    InventoryReportPayload,
    InventoryReportRange,
    InventoryReportView,
)
from inventory.report_image_renderer import render_inventory_reports
from player_self_service.governor_dashboard_models import (
    GovernorDashboardContext,
    GovernorDashboardOption,
    GovernorDashboardResolution,
)
from player_self_service.governor_dashboard_service import resolve_dashboard_context

logger = logging.getLogger(__name__)

ContextResolver = Callable[..., Awaitable[GovernorDashboardResolution]]
PayloadLoader = Callable[..., Awaitable[InventoryReportPayload]]

_SELECT_PAGE_SIZE = 25
_VIEW_TIMEOUT_SECONDS = 180.0


def _safe_name(value: Any, *, fallback: str) -> str:
    text = " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())
    text = text.replace("@", "@\u200b").replace("<", "‹").replace(">", "›")
    return (text or fallback)[:100]


def _upload_guidance() -> str:
    if INVENTORY_UPLOAD_CHANNEL_ID:
        return (
            "No approved data is recorded for this report yet. Use `/inventory import` or "
            f"upload the matching screenshot in <#{int(INVENTORY_UPLOAD_CHANNEL_ID)}> ."
        ).replace("> .", ">.")
    return (
        "No approved data is recorded for this report yet. Use `/inventory import` in the "
        "Inventory upload channel."
    )


def _has_requested_data(payload: InventoryReportPayload) -> bool:
    if payload.view == InventoryReportView.RESOURCES:
        return bool(payload.resources)
    if payload.view == InventoryReportView.SPEEDUPS:
        return bool(payload.speedups)
    if payload.view == InventoryReportView.MATERIALS:
        return bool(payload.materials)
    return bool(payload.resources or payload.speedups or payload.materials)


def _report_label(view: InventoryReportView) -> str:
    return {
        InventoryReportView.RESOURCES: "Resources",
        InventoryReportView.MATERIALS: "Materials",
        InventoryReportView.SPEEDUPS: "Speedups",
        InventoryReportView.ALL: "Inventory",
    }[view]


def _report_content(payload: InventoryReportPayload) -> str:
    name = _safe_name(payload.governor_name, fallback=str(payload.governor_id))
    return (
        f"Inventory report for **{name}** (`{payload.governor_id}`) — "
        f"{_report_label(payload.view)} — `{payload.range_key.value}`"
    )


def build_report_fallback_embed(payload: InventoryReportPayload) -> discord.Embed:
    has_data = _has_requested_data(payload)
    embed = discord.Embed(
        title=f"{_report_label(payload.view)} Inventory",
        description=(
            f"Governor **{_safe_name(payload.governor_name, fallback=str(payload.governor_id))}** "
            f"(`{payload.governor_id}`) · `{payload.range_key.value}`"
        ),
        color=discord.Color.blue() if has_data else discord.Color.orange(),
    )
    if has_data:
        if payload.view == InventoryReportView.RESOURCES and payload.resources:
            point = payload.resources[-1]
            value = (
                f"Total RSS: `{point.total:,}`\nFood: `{point.food:,}` · Wood: `{point.wood:,}`\n"
                f"Stone: `{point.stone:,}` · Gold: `{point.gold:,}`"
            )
        elif payload.view == InventoryReportView.SPEEDUPS and payload.speedups:
            point = payload.speedups[-1]
            total_days = sum(
                (
                    float(point.building_days),
                    float(point.research_days),
                    float(point.training_days),
                    float(point.healing_days),
                    float(point.universal_days),
                )
            )
            value = (
                f"Total: `{total_days:,.1f} days`\nTraining: `{point.training_days:,.1f}d` · "
                f"Healing: `{point.healing_days:,.1f}d` · Universal: `{point.universal_days:,.1f}d`"
            )
        elif payload.view == InventoryReportView.MATERIALS and payload.materials:
            point = payload.materials[-1]
            value = (
                f"Total legendary equivalent: `{point.total_legendary:,.1f}`\n"
                f"Fixed materials: `{point.fixed_total_legendary:,.1f}` · "
                f"Choice chests: `{point.choice_chest_legendary:,.1f}`"
            )
        else:
            value = "Authorized report data loaded. Use the report controls to try again."
        embed.add_field(name="Latest approved values", value=value, inline=False)
        embed.set_footer(text="Image delivery failed; this fallback uses the authorized payload.")
    else:
        embed.add_field(name="Upload Inventory", value=_upload_guidance(), inline=False)
    return embed


def build_selector_embed(
    options: tuple[GovernorDashboardOption, ...],
    *,
    page: int,
) -> discord.Embed:
    total_pages = max(1, ceil(len(options) / _SELECT_PAGE_SIZE))
    default = next((option for option in options if option.is_default), options[0])
    return discord.Embed(
        title="Choose a Governor",
        description=(
            "Select one of your linked governors. Access is checked again before Inventory "
            "data is loaded.\n\n"
            f"**Default account**\n{_safe_name(default.governor_name, fallback=default.governor_id_str)} "
            f"(`{default.governor_id}`)\n\nPrivate selector · Page {page + 1} of {total_pages}"
        ),
        color=discord.Color.blue(),
    )


def _close_files(files: list[discord.File] | None) -> None:
    for file in files or []:
        try:
            file.close()
        except Exception:
            logger.debug("player_inventory_report_file_close_failed", exc_info=True)
        stream = getattr(file, "fp", None)
        try:
            if stream is not None and not getattr(stream, "closed", False):
                stream.close()
        except Exception:
            logger.debug("player_inventory_report_stream_close_failed", exc_info=True)


async def _defer_private(interaction: discord.Interaction) -> None:
    try:
        if interaction.response.is_done():
            return
        if getattr(interaction, "message", None) is not None:
            await interaction.response.defer()
        else:
            await interaction.response.defer(ephemeral=True)
    except TypeError:
        try:
            if not interaction.response.is_done():
                await interaction.response.defer()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.debug("player_inventory_report_interaction_defer_failed", exc_info=True)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug("player_inventory_report_interaction_defer_failed", exc_info=True)


async def _private_error(interaction: discord.Interaction, content: str) -> None:
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(content, ephemeral=True)
        else:
            await interaction.followup.send(content, ephemeral=True)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug("player_inventory_report_private_error_failed", exc_info=True)


async def _render_files(payload: InventoryReportPayload) -> list[discord.File]:
    rendered = await asyncio.to_thread(render_inventory_reports, payload, avatar_bytes=None)
    files: list[discord.File] = []
    try:
        for item in rendered:
            stream = item.image_bytes
            if isinstance(stream, (bytes, bytearray)):
                stream = BytesIO(stream)
            else:
                stream.seek(0)
            try:
                files.append(discord.File(stream, filename=item.filename))
            except Exception:
                stream.close()
                raise
        return files
    except Exception:
        _close_files(files)
        raise


class _ActionButton(discord.ui.Button):
    def __init__(
        self,
        *,
        label: str,
        custom_id: str,
        row: int,
        style: discord.ButtonStyle,
        action: Callable[[discord.Interaction], Awaitable[None]],
        disabled: bool = False,
    ) -> None:
        super().__init__(
            label=label,
            custom_id=custom_id,
            row=row,
            style=style,
            disabled=disabled,
        )
        self._action = action

    async def callback(self, interaction: discord.Interaction) -> None:
        await self._action(interaction)


class _GovernorSelect(discord.ui.Select):
    def __init__(
        self,
        parent: PlayerInventoryReportView,
        options: tuple[GovernorDashboardOption, ...],
        *,
        row: int,
        placeholder: str,
    ) -> None:
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            row=row,
            options=[
                discord.SelectOption(
                    label=_safe_name(item.governor_name, fallback=item.governor_id_str),
                    value=item.governor_id_str,
                    description=str(item.account_type)[:100],
                    default=(
                        parent.resolution.context is not None
                        and parent.resolution.context.selected_governor_id == item.governor_id
                    ),
                )
                for item in options
            ],
        )
        self.parent_view = parent

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.parent_view.select_governor(interaction, self.values[0])


class PlayerInventoryReportView(discord.ui.View):
    """Author-gated, non-persistent selected-governor report controller."""

    def __init__(
        self,
        *,
        author_id: int,
        display_name: str,
        resolution: GovernorDashboardResolution,
        report_view: InventoryReportView,
        range_key: InventoryReportRange = InventoryReportRange.ONE_MONTH,
        selector_page: int | None = None,
        context_resolver: ContextResolver = resolve_dashboard_context,
        payload_loader: PayloadLoader = reporting_service.build_self_service_inventory_report_payload,
        timeout: float = _VIEW_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(timeout=timeout, disable_on_timeout=True)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.resolution = resolution
        self.report_view = report_view
        self.range_key = range_key
        self.selector_page = max(0, int(selector_page or 0))
        self._selector_page_explicit = selector_page is not None
        self.context_resolver = context_resolver
        self.payload_loader = payload_loader
        self._message_ref: Any | None = None
        self._timeout_editor: Callable[..., Awaitable[Any]] | None = None
        self._busy = False
        self._expired = False
        self._timed_out = False
        self._active_transition_id: int | None = None
        self._build_controls()

    def set_message_ref(self, message: Any | None) -> None:
        self._message_ref = message

    def set_timeout_target(self, target: Any) -> None:
        editor = getattr(target, "edit_original_response", None)
        if callable(editor):
            self._timeout_editor = editor

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self._expired or self._timed_out:
            await _private_error(
                interaction,
                "This private Inventory report has expired. Run `/me resources`, `/me materials`, or `/me speedups` again.",
            )
            return False
        if not interaction.user or int(interaction.user.id) != self.author_id:
            await _private_error(interaction, "This private Inventory report is not for you.")
            return False
        return True

    async def _claim(self, interaction: discord.Interaction) -> bool:
        if self._busy or self._active_transition_id is not None:
            await _private_error(interaction, "Another report action is already being processed.")
            return False
        self._busy = True
        self._active_transition_id = id(interaction)
        return True

    def _is_current(self, interaction: discord.Interaction) -> bool:
        return bool(not self._timed_out and self._active_transition_id == id(interaction))

    def _release(self, interaction: discord.Interaction) -> None:
        if self._active_transition_id == id(interaction):
            self._active_transition_id = None
            self._busy = False

    def _timeout_remaining(self) -> float:
        expiry = getattr(self, "_timeout_expiry", None)
        if expiry is None:
            return float(self.timeout or _VIEW_TIMEOUT_SECONDS)
        return max(0.001, float(expiry) - time.monotonic())

    def _page_options(self) -> tuple[GovernorDashboardOption, ...]:
        total_pages = max(1, ceil(len(self.resolution.options) / _SELECT_PAGE_SIZE))
        if not self._selector_page_explicit and self.resolution.context is not None:
            selected = self.resolution.context.selected_governor_id
            index = next(
                (
                    i
                    for i, option in enumerate(self.resolution.options)
                    if option.governor_id == selected
                ),
                0,
            )
            self.selector_page = index // _SELECT_PAGE_SIZE
        self.selector_page = min(self.selector_page, total_pages - 1)
        start = self.selector_page * _SELECT_PAGE_SIZE
        return self.resolution.options[start : start + _SELECT_PAGE_SIZE]

    def _build_controls(self) -> None:
        if self.resolution.state == "requires_selection" and self.resolution.options:
            self.add_item(
                _GovernorSelect(
                    self,
                    self._page_options(),
                    row=0,
                    placeholder="Select a linked governor",
                )
            )
            if len(self.resolution.options) > _SELECT_PAGE_SIZE:
                self.add_item(
                    _ActionButton(
                        label="Previous",
                        custom_id="me:report:selector:previous",
                        row=1,
                        style=discord.ButtonStyle.secondary,
                        action=lambda i: self.page_governors(i, -1),
                    )
                )
                self.add_item(
                    _ActionButton(
                        label="Next",
                        custom_id="me:report:selector:next",
                        row=1,
                        style=discord.ButtonStyle.secondary,
                        action=lambda i: self.page_governors(i, 1),
                    )
                )
            return

        if self.resolution.state != "selected":
            return

        for label, report_view in (
            ("Resources", InventoryReportView.RESOURCES),
            ("Materials", InventoryReportView.MATERIALS),
            ("Speedups", InventoryReportView.SPEEDUPS),
        ):
            self.add_item(
                _ActionButton(
                    label=label,
                    custom_id=f"me:report:type:{report_view.value}",
                    row=0,
                    style=(
                        discord.ButtonStyle.primary
                        if report_view == self.report_view
                        else discord.ButtonStyle.secondary
                    ),
                    disabled=report_view == self.report_view,
                    action=lambda i, target=report_view: self.change_report(i, report_view=target),
                )
            )
        for range_key in InventoryReportRange:
            self.add_item(
                _ActionButton(
                    label=range_key.value,
                    custom_id=f"me:report:range:{range_key.value.lower()}",
                    row=1,
                    style=(
                        discord.ButtonStyle.primary
                        if range_key == self.range_key
                        else discord.ButtonStyle.secondary
                    ),
                    disabled=range_key == self.range_key,
                    action=lambda i, target=range_key: self.change_report(i, range_key=target),
                )
            )
        for label, export_format in (
            ("Export Excel", InventoryExportFormat.EXCEL),
            ("Export CSV", InventoryExportFormat.CSV),
            ("Export Sheets", InventoryExportFormat.GOOGLE_SHEETS),
        ):
            self.add_item(
                _ActionButton(
                    label=label,
                    custom_id=f"me:report:export:{export_format.value}",
                    row=2,
                    style=discord.ButtonStyle.secondary,
                    action=lambda i, target=export_format: self.export_report(i, target),
                )
            )
        self.add_item(
            _ActionButton(
                label="Dashboard",
                custom_id="me:report:dashboard",
                row=3,
                style=discord.ButtonStyle.primary,
                action=self.open_dashboard,
            )
        )

        if len(self.resolution.options) > _SELECT_PAGE_SIZE:
            self.add_item(
                _ActionButton(
                    label="Previous",
                    custom_id="me:report:change:previous",
                    row=3,
                    style=discord.ButtonStyle.secondary,
                    action=lambda i: self.page_governors(i, -1),
                )
            )
            self.add_item(
                _ActionButton(
                    label="Next",
                    custom_id="me:report:change:next",
                    row=3,
                    style=discord.ButtonStyle.secondary,
                    action=lambda i: self.page_governors(i, 1),
                )
            )
        if len(self.resolution.options) > 1:
            self.add_item(
                _GovernorSelect(
                    self,
                    self._page_options(),
                    row=4,
                    placeholder="Change Governor",
                )
            )

    async def _resolve_current(self) -> GovernorDashboardResolution:
        context = self.resolution.context
        governor_id = context.selected_governor_id if context is not None else None
        if governor_id is None:
            return GovernorDashboardResolution(
                state="denied", options=self.resolution.options, reason="missing governor"
            )
        return await self.context_resolver(self.author_id, governor_id, viewer_mode="self")

    async def change_report(
        self,
        interaction: discord.Interaction,
        *,
        report_view: InventoryReportView | None = None,
        range_key: InventoryReportRange | None = None,
    ) -> None:
        if not await self._claim(interaction):
            return
        try:
            await _defer_private(interaction)
            resolution = await self._resolve_current()
            await _render_resolution(
                interaction,
                author_id=self.author_id,
                display_name=self.display_name,
                resolution=resolution,
                report_view=report_view or self.report_view,
                range_key=range_key or self.range_key,
                context_resolver=self.context_resolver,
                payload_loader=self.payload_loader,
                timeout=self.timeout or _VIEW_TIMEOUT_SECONDS,
                can_edit=lambda: self._is_current(interaction),
                timeout_remaining=self._timeout_remaining,
            )
            if self._is_current(interaction):
                self.stop()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("player_inventory_report_change_failed user_id=%s", self.author_id)
            await _private_error(interaction, "The report could not be updated. Please try again.")
        finally:
            self._release(interaction)

    async def select_governor(self, interaction: discord.Interaction, governor_id: str) -> None:
        if not await self._claim(interaction):
            return
        try:
            await _defer_private(interaction)
            resolution = await self.context_resolver(
                self.author_id, governor_id, viewer_mode="self"
            )
            await _render_resolution(
                interaction,
                author_id=self.author_id,
                display_name=self.display_name,
                resolution=resolution,
                report_view=self.report_view,
                range_key=self.range_key,
                context_resolver=self.context_resolver,
                payload_loader=self.payload_loader,
                timeout=self.timeout or _VIEW_TIMEOUT_SECONDS,
                can_edit=lambda: self._is_current(interaction),
                timeout_remaining=self._timeout_remaining,
            )
            if self._is_current(interaction):
                self.stop()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("player_inventory_report_selection_failed user_id=%s", self.author_id)
            await _private_error(
                interaction, "That governor could not be opened. Please try again."
            )
        finally:
            self._release(interaction)

    async def page_governors(self, interaction: discord.Interaction, direction: int) -> None:
        if not await self._claim(interaction):
            return
        try:
            total_pages = max(1, ceil(len(self.resolution.options) / _SELECT_PAGE_SIZE))
            next_page = min(max(0, self.selector_page + direction), total_pages - 1)
            view = PlayerInventoryReportView(
                author_id=self.author_id,
                display_name=self.display_name,
                resolution=self.resolution,
                report_view=self.report_view,
                range_key=self.range_key,
                selector_page=next_page,
                context_resolver=self.context_resolver,
                payload_loader=self.payload_loader,
                timeout=self.timeout or _VIEW_TIMEOUT_SECONDS,
            )
            kwargs: dict[str, Any] = {"view": view}
            if self.resolution.state == "requires_selection":
                kwargs.update(
                    embed=build_selector_embed(self.resolution.options, page=next_page),
                    attachments=[],
                )
            if not self._is_current(interaction):
                return
            edited = await asyncio.wait_for(
                interaction.response.edit_message(**kwargs),
                timeout=self._timeout_remaining(),
            )
            if not self._is_current(interaction):
                return
            view.set_message_ref(getattr(interaction, "message", None) or edited)
            view.set_timeout_target(interaction)
            self.stop()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("player_inventory_report_paging_failed user_id=%s", self.author_id)
            await _private_error(interaction, "The governor list could not be updated.")
        finally:
            self._release(interaction)

    async def open_dashboard(self, interaction: discord.Interaction) -> None:
        if not await self._claim(interaction):
            return
        try:
            from ui.views.player_self_service_governor_dashboard_views import (
                show_governor_dashboard_for_interaction,
            )

            context = self.resolution.context
            await asyncio.wait_for(
                show_governor_dashboard_for_interaction(
                    interaction,
                    author_id=self.author_id,
                    display_name=self.display_name,
                    governor_id=context.selected_governor_id if context else None,
                    timeout=self.timeout or _VIEW_TIMEOUT_SECONDS,
                ),
                timeout=self._timeout_remaining(),
            )
            self.stop()
        except asyncio.CancelledError:
            raise
        except TimeoutError:
            logger.info("player_inventory_report_dashboard_timed_out user_id=%s", self.author_id)
        except Exception:
            logger.exception("player_inventory_report_dashboard_failed user_id=%s", self.author_id)
            await _private_error(
                interaction, "The dashboard could not be opened. Please try again."
            )
        finally:
            self._release(interaction)

    async def export_report(
        self,
        interaction: discord.Interaction,
        export_format: InventoryExportFormat,
    ) -> None:
        if not await self._claim(interaction):
            return
        export_file = None
        discord_file = None
        try:
            await _defer_private(interaction)
            resolution = await self._resolve_current()
            context = resolution.context
            if (
                context is None
                or not context.access_allowed
                or context.selected_governor_id is None
            ):
                raise PermissionError(
                    "You can only export Inventory for governors registered to you."
                )
            export_file = await export_service.build_inventory_export_file(
                discord_user_id=self.author_id,
                username=self.display_name,
                export_format=export_format,
                view=self.report_view,
                governor_id=context.selected_governor_id,
                lookback_days=reporting_service.REPORT_RANGE_DAYS[self.range_key],
                is_admin=False,
                discord_user=None,
            )
            if not self._is_current(interaction):
                return
            discord_file = discord.File(str(export_file.path), filename=export_file.filename)
            await interaction.followup.send(
                content=f"Private Inventory export ready — `{export_file.row_count}` approved row(s).",
                file=discord_file,
                ephemeral=True,
            )
        except asyncio.CancelledError:
            raise
        except (PermissionError, ValueError) as exc:
            await interaction.followup.send(str(exc), ephemeral=True)
        except Exception:
            logger.exception("player_inventory_report_export_failed user_id=%s", self.author_id)
            await interaction.followup.send(
                "Inventory export failed. Please try again.", ephemeral=True
            )
        finally:
            if discord_file is not None:
                try:
                    discord_file.close()
                except Exception:
                    logger.debug("player_inventory_export_stream_close_failed", exc_info=True)
            export_service.cleanup_export_file(export_file)
            self._release(interaction)

    async def on_timeout(self) -> None:
        self._timed_out = True
        self._expired = True
        self._busy = False
        self._active_transition_id = None
        for child in self.children:
            child.disabled = True
        kwargs = {
            "content": "This private Inventory report has expired. Run a `/me` report command again.",
            "embed": None,
            "view": self,
            "attachments": [],
        }
        try:
            if self._timeout_editor is not None:
                await self._timeout_editor(**kwargs)
            elif self._message_ref is not None:
                await self._message_ref.edit(**kwargs)
        except Exception:
            logger.debug("player_inventory_report_timeout_edit_failed", exc_info=True)
        await super().on_timeout()


async def _edit_report_response(
    target: Any,
    *,
    content: str | None,
    embed: discord.Embed | None,
    fallback_embed: discord.Embed | None,
    view: PlayerInventoryReportView,
    files: list[discord.File] | None = None,
    can_edit: Callable[[], bool] | None = None,
    timeout_remaining: Callable[[], float] | None = None,
) -> bool:
    files = files or []
    if can_edit is not None and not can_edit():
        _close_files(files)
        return False
    try:
        kwargs: dict[str, Any] = {
            "content": content,
            "embed": embed,
            "view": view,
            "attachments": [],
        }
        if files:
            kwargs["files"] = files
        call = target.edit_original_response(**kwargs)
        edited = (
            await asyncio.wait_for(call, timeout_remaining()) if timeout_remaining else await call
        )
        if can_edit is not None and not can_edit():
            return False
        view.set_message_ref(getattr(target, "message", None) or edited)
        view.set_timeout_target(target)
        return True
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug("player_inventory_report_image_edit_failed", exc_info=True)
        if can_edit is not None and not can_edit():
            return False
        try:
            call = target.edit_original_response(
                content=None,
                embed=fallback_embed,
                view=view,
                attachments=[],
            )
            edited = (
                await asyncio.wait_for(call, timeout_remaining())
                if timeout_remaining
                else await call
            )
            if can_edit is not None and not can_edit():
                return False
            view.set_message_ref(getattr(target, "message", None) or edited)
            view.set_timeout_target(target)
            return True
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.debug("player_inventory_report_fallback_edit_failed", exc_info=True)
            if can_edit is not None and not can_edit():
                return False
            sent = await target.followup.send(embed=fallback_embed, view=view, ephemeral=True)
            if can_edit is not None and not can_edit():
                return False
            view.set_message_ref(sent)
            return True
    finally:
        _close_files(files)


async def _render_resolution(
    target: Any,
    *,
    author_id: int,
    display_name: str,
    resolution: GovernorDashboardResolution,
    report_view: InventoryReportView,
    range_key: InventoryReportRange,
    context_resolver: ContextResolver,
    payload_loader: PayloadLoader,
    timeout: float,
    can_edit: Callable[[], bool] | None = None,
    timeout_remaining: Callable[[], float] | None = None,
) -> bool:
    payload = None
    files: list[discord.File] = []
    content = None
    embed = None
    fallback_embed = None
    if resolution.state == "selected" and resolution.context is not None:
        context: GovernorDashboardContext = resolution.context
        if (
            context.viewer_mode != "self"
            or context.viewer_discord_id != int(author_id)
            or not context.is_linked_to_viewer
            or not context.access_allowed
            or context.selected_governor_id is None
        ):
            resolution = GovernorDashboardResolution(
                state="denied", options=resolution.options, reason="access denied"
            )
        else:
            try:
                payload = await payload_loader(
                    discord_user_id=int(author_id),
                    governor_id=int(context.selected_governor_id),
                    view=report_view,
                    range_key=range_key,
                )
                fallback_embed = build_report_fallback_embed(payload)
                if _has_requested_data(payload):
                    try:
                        files = await _render_files(payload)
                        content = _report_content(payload)
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        logger.exception(
                            "player_inventory_report_render_failed user_id=%s governor_id=%s",
                            author_id,
                            context.selected_governor_id,
                        )
                        embed = fallback_embed
                else:
                    embed = fallback_embed
            except PermissionError:
                logger.warning("player_inventory_report_access_denied user_id=%s", author_id)
                resolution = GovernorDashboardResolution(
                    state="denied", options=resolution.options, reason="access denied"
                )
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("player_inventory_report_payload_failed user_id=%s", author_id)
                embed = discord.Embed(
                    title="Inventory temporarily unavailable",
                    description="The report could not be loaded. Please try again.",
                    color=discord.Color.orange(),
                )

    if resolution.state == "requires_selection":
        embed = build_selector_embed(resolution.options, page=0)
    elif resolution.state == "requires_setup":
        embed = discord.Embed(
            title="Set up Inventory",
            description="No linked governors were found. Use `/me accounts` to register a governor, then upload Inventory screenshots.",
            color=discord.Color.orange(),
        )
    elif resolution.state == "unavailable":
        embed = discord.Embed(
            title="Inventory temporarily unavailable",
            description="Your linked governors could not be loaded. Please try again.",
            color=discord.Color.orange(),
        )
    elif resolution.state == "denied":
        embed = discord.Embed(
            title="Inventory access denied",
            description="That governor is not currently linked to your Discord account.",
            color=discord.Color.red(),
        )

    view = PlayerInventoryReportView(
        author_id=author_id,
        display_name=display_name,
        resolution=resolution,
        report_view=report_view,
        range_key=range_key,
        context_resolver=context_resolver,
        payload_loader=payload_loader,
        timeout=timeout,
    )
    return await _edit_report_response(
        target,
        content=content,
        embed=embed,
        fallback_embed=fallback_embed or embed,
        view=view,
        files=files,
        can_edit=can_edit,
        timeout_remaining=timeout_remaining,
    )


async def show_player_inventory_report_for_interaction(
    interaction: discord.Interaction,
    *,
    author_id: int,
    display_name: str,
    report_view: InventoryReportView,
    governor_id: int | str | None = None,
    range_key: InventoryReportRange = InventoryReportRange.ONE_MONTH,
    context_resolver: ContextResolver = resolve_dashboard_context,
    payload_loader: PayloadLoader = reporting_service.build_self_service_inventory_report_payload,
    timeout: float = _VIEW_TIMEOUT_SECONDS,
) -> None:
    await _defer_private(interaction)
    try:
        resolution = await context_resolver(
            int(author_id),
            governor_id,
            viewer_mode="self",
        )
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("player_inventory_report_resolution_failed user_id=%s", author_id)
        resolution = GovernorDashboardResolution(
            state="unavailable", options=(), reason="account source unavailable"
        )
    await _render_resolution(
        interaction,
        author_id=int(author_id),
        display_name=display_name,
        resolution=resolution,
        report_view=report_view,
        range_key=range_key,
        context_resolver=context_resolver,
        payload_loader=payload_loader,
        timeout=timeout,
    )


async def send_player_inventory_report(
    ctx: discord.ApplicationContext,
    *,
    report_view: InventoryReportView,
) -> None:
    await safe_defer(ctx, ephemeral=True)
    user = ctx.user
    display_name = str(getattr(user, "display_name", None) or getattr(user, "name", "player"))
    await show_player_inventory_report_for_interaction(
        ctx.interaction,
        author_id=int(user.id),
        display_name=display_name,
        report_view=report_view,
    )
