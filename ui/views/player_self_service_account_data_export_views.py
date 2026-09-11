"""Private Account Summary Download data interaction flow."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import logging
from time import monotonic
from typing import Any

import discord

from file_utils import emit_telemetry_event
from player_self_service.account_data_export_contract import (
    ALLOWED_HISTORY_DAYS,
    DEFAULT_HISTORY_DAYS,
    AccountDataExportFile,
    AccountDataOutputKind,
)
from services import account_data_export_service

logger = logging.getLogger(__name__)

_OPTIONS_TIMEOUT_SECONDS = 300


def _user_display_name(user: Any, fallback: str) -> str:
    return (
        str(getattr(user, "display_name", "") or "").strip()
        or str(getattr(user, "name", "") or "").strip()
        or str(fallback or "").strip()
        or "player"
    )


async def _defer_private(interaction: discord.Interaction) -> None:
    try:
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
    except TypeError:
        try:
            if not interaction.response.is_done():
                await interaction.response.defer()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.debug("account_data_export_defer_failed", exc_info=True)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug("account_data_export_defer_failed", exc_info=True)


async def _send_private_error(interaction: discord.Interaction, message: str) -> None:
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(message, ephemeral=True)
            return
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug("account_data_export_initial_error_send_failed", exc_info=True)
    await interaction.followup.send(message, ephemeral=True)


async def _send_private_message(
    interaction: discord.Interaction,
    message: str,
    *,
    view: discord.ui.View | None = None,
) -> object | None:
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(message, view=view, ephemeral=True)
            try:
                return await interaction.original_response()
            except asyncio.CancelledError:
                raise
            except Exception:
                return None
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug("account_data_export_initial_options_send_failed", exc_info=True)
    try:
        return await interaction.followup.send(message, view=view, ephemeral=True, wait=True)
    except TypeError:
        return await interaction.followup.send(message, view=view, ephemeral=True)


def _date_text(value: object | None) -> str:
    return "Not applicable" if value is None else str(value)


def _output_label(output_kind: AccountDataOutputKind) -> str:
    return {
        AccountDataOutputKind.FULL_WORKBOOK: "Full workbook (.xlsx)",
        AccountDataOutputKind.CURRENT_SNAPSHOT: "Current account snapshot (.csv)",
        AccountDataOutputKind.RAW_HISTORY: "Raw stats history (.csv)",
    }[output_kind]


def _result_embed(export_file: AccountDataExportFile) -> discord.Embed:
    metadata = export_file.metadata
    embed = discord.Embed(
        title="Account Data download",
        description=f"**{_output_label(metadata.output_kind)}**",
        color=discord.Color.dark_teal(),
    )
    scope_lines = [f"Authorised distinct governors: {metadata.authorised_governor_count}"]
    if metadata.snapshot_row_count is not None:
        scope_lines.append(f"Current snapshot rows: {metadata.snapshot_row_count}")
    if metadata.history_row_count is not None:
        scope_lines.append(f"History rows written: {metadata.history_row_count}")
    embed.add_field(name="Scope", value="\n".join(scope_lines), inline=False)

    if metadata.requested_days is not None:
        embed.add_field(
            name="History window",
            value=(
                f"Requested: {metadata.requested_days} days\n"
                f"Selected: {_date_text(metadata.window_start)} to {_date_text(metadata.window_end)}\n"
                f"Written: {_date_text(metadata.written_start)} to {_date_text(metadata.written_end)}"
            ),
            inline=False,
        )

    freshness = []
    if metadata.stats_freshness is not None:
        freshness.append(f"Stats: {metadata.stats_freshness}")
    if metadata.governor_scan_freshness is not None:
        freshness.append(f"Governor scan: {metadata.governor_scan_freshness}")
    if metadata.inventory_reporting_count is not None:
        freshness.append(
            "Inventory: "
            f"{metadata.inventory_reporting_count}/{metadata.inventory_expected_count} rows; "
            f"{_date_text(metadata.inventory_oldest)} to {_date_text(metadata.inventory_latest)}"
        )
    if freshness:
        embed.add_field(name="Source freshness", value="\n".join(freshness), inline=False)

    if metadata.output_kind is AccountDataOutputKind.FULL_WORKBOOK:
        embed.add_field(
            name="Excel / Google Sheets compatible",
            value="Open in Excel, or upload the `.xlsx` file to Google Drive and open it with Google Sheets.",
            inline=False,
        )
    embed.set_footer(
        text=f"Private download • Generated {metadata.generated_at_utc.isoformat(timespec='seconds')}"
    )
    return embed


async def send_account_data_export(
    interaction: discord.Interaction,
    *,
    display_name: str,
    output_kind: AccountDataOutputKind,
    days: int | None,
) -> bool:
    await _defer_private(interaction)
    export_file: AccountDataExportFile | None = None
    discord_file: discord.File | None = None
    started = monotonic()
    try:
        outcome = await account_data_export_service.build_account_data_export(
            discord_user_id=int(interaction.user.id),
            display_name=_user_display_name(interaction.user, display_name),
            requested_kind=output_kind,
            requested_days=days,
        )
        if outcome.status != "ok" or outcome.export_file is None:
            await _send_private_error(
                interaction,
                f"Account Data download unavailable: {outcome.message or 'Please try again.'}",
            )
            return False

        export_file = outcome.export_file
        discord_file = discord.File(str(export_file.file_path), filename=export_file.filename)
        await interaction.followup.send(
            embed=_result_embed(export_file),
            file=discord_file,
            ephemeral=True,
        )
        try:
            emit_telemetry_event(
                account_data_export_service.telemetry_payload(
                    export_file,
                    discord_user_id=int(interaction.user.id),
                    duration_ms=int((monotonic() - started) * 1000),
                )
            )
        except Exception:
            logger.debug("account_data_export_telemetry_failed", exc_info=True)
        return True
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception(
            "account_data_export_delivery_failed user_id=%s kind=%s",
            getattr(getattr(interaction, "user", None), "id", None),
            output_kind.value,
        )
        await _send_private_error(
            interaction,
            "Account Data download is temporarily unavailable. Please try again.",
        )
        return False
    finally:
        if discord_file is not None:
            try:
                discord_file.close()
            except Exception:
                logger.debug("account_data_export_discord_file_close_failed", exc_info=True)
        account_data_export_service.cleanup_export_file(export_file)


class AccountDataOptionsView(discord.ui.View):
    expired_message = "This private Download data window has expired. Open `/me accounts` again."

    def __init__(self, *, author_id: int, display_name: str) -> None:
        super().__init__(timeout=_OPTIONS_TIMEOUT_SECONDS, disable_on_timeout=True)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.selected_kind = AccountDataOutputKind.FULL_WORKBOOK
        self.selected_days = DEFAULT_HISTORY_DAYS
        self._message_ref: object | None = None
        self._timeout_editor: Callable[..., Awaitable[object]] | None = None
        self._expired = False
        self._terminal = False
        self._busy = False
        self.kind_select = AccountDataKindSelect(self)
        self.days_select = AccountDataDaysSelect(self)
        self.add_item(self.kind_select)
        self.add_item(self.days_select)
        self._sync_controls()

    def set_message_ref(self, message: object | None) -> None:
        self._message_ref = message
        if message is not None and hasattr(message, "flags") and hasattr(message, "channel"):
            try:
                self.message = message
            except Exception:
                logger.debug("account_data_export_message_ref_failed", exc_info=True)

    def set_timeout_target(self, target: object) -> None:
        editor = getattr(target, "edit_original_response", None)
        if callable(editor):
            self._timeout_editor = editor

    def _sync_controls(self) -> None:
        for option in self.kind_select.options:
            option.default = option.value == self.selected_kind.value
        for option in self.days_select.options:
            option.default = option.value == str(self.selected_days)
        self.days_select.disabled = self.selected_kind is AccountDataOutputKind.CURRENT_SNAPSHOT

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if int(interaction.user.id) != self.author_id:
            await interaction.response.send_message(
                "This Download data window is not for you.", ephemeral=True
            )
            return False
        if self._expired:
            await interaction.response.send_message(self.expired_message, ephemeral=True)
            return False
        if self._terminal:
            await interaction.response.send_message(
                "This Download data window is already complete. Open a new one from Account Summary.",
                ephemeral=True,
            )
            return False
        if self._busy:
            await interaction.response.send_message(
                "Your download is already being prepared.", ephemeral=True
            )
            return False
        return True

    async def _edit_window(self, interaction: discord.Interaction) -> None:
        self._sync_controls()
        await interaction.response.edit_message(content=_options_copy(self), view=self)

    async def _finish(self, content: str) -> None:
        self._terminal = True
        self._busy = False
        for child in self.children:
            child.disabled = True
        message = self._message_ref or getattr(self, "message", None)
        if message is not None and hasattr(message, "edit"):
            try:
                await message.edit(content=content, view=self)
            except Exception:
                logger.debug("account_data_export_terminal_edit_failed", exc_info=True)
        self.stop()

    @discord.ui.button(
        label="Download",
        style=discord.ButtonStyle.success,
        custom_id="me:account-data:download",
        row=2,
    )
    async def download_button(
        self,
        _button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        self._busy = True
        succeeded = await send_account_data_export(
            interaction,
            display_name=self.display_name,
            output_kind=self.selected_kind,
            days=(
                None
                if self.selected_kind is AccountDataOutputKind.CURRENT_SNAPSHOT
                else self.selected_days
            ),
        )
        if succeeded:
            await self._finish("Download generated. Open Account Summary to create another file.")
        else:
            self._busy = False

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary,
        custom_id="me:account-data:cancel",
        row=2,
    )
    async def cancel_button(
        self,
        _button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        self._terminal = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="Download data cancelled.", view=self)
        self.stop()

    async def on_timeout(self) -> None:
        self._expired = True
        self._busy = False
        for child in self.children:
            child.disabled = True
        message = self._message_ref or getattr(self, "message", None)
        try:
            if message is not None and hasattr(message, "edit"):
                await message.edit(content=self.expired_message, view=self)
            elif self._timeout_editor is not None:
                await self._timeout_editor(content=self.expired_message, view=self)
        except Exception:
            logger.debug("account_data_export_options_timeout_edit_failed", exc_info=True)


class AccountDataKindSelect(discord.ui.Select):
    def __init__(self, parent_view: AccountDataOptionsView) -> None:
        super().__init__(
            placeholder="Download type",
            min_values=1,
            max_values=1,
            options=(
                discord.SelectOption(
                    label="Full workbook (.xlsx)",
                    value=AccountDataOutputKind.FULL_WORKBOOK.value,
                    description="Account Summary and selected Stats history; Excel / Google Sheets compatible.",
                    default=True,
                ),
                discord.SelectOption(
                    label="Current account snapshot (.csv)",
                    value=AccountDataOutputKind.CURRENT_SNAPSHOT.value,
                    description="The current 29-column Account Summary; history days do not apply.",
                ),
                discord.SelectOption(
                    label="Raw stats history (.csv)",
                    value=AccountDataOutputKind.RAW_HISTORY.value,
                    description="One row per governor per source date in the selected history window.",
                ),
            ),
            custom_id="me:account-data:kind",
            row=0,
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent_view.selected_kind = AccountDataOutputKind(self.values[0])
        await self.parent_view._edit_window(interaction)


class AccountDataDaysSelect(discord.ui.Select):
    def __init__(self, parent_view: AccountDataOptionsView) -> None:
        super().__init__(
            placeholder="History days",
            min_values=1,
            max_values=1,
            options=tuple(
                discord.SelectOption(
                    label=f"{days} days",
                    value=str(days),
                    default=days == DEFAULT_HISTORY_DAYS,
                )
                for days in ALLOWED_HISTORY_DAYS
            ),
            custom_id="me:account-data:days",
            row=1,
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent_view.selected_days = int(self.values[0])
        await self.parent_view._edit_window(interaction)


def _options_copy(view: AccountDataOptionsView) -> str:
    days = (
        "Not applicable"
        if view.selected_kind is AccountDataOutputKind.CURRENT_SNAPSHOT
        else f"{view.selected_days} days"
    )
    return (
        "Choose your private Account Data download.\n"
        f"Output: **{_output_label(view.selected_kind)}**\n"
        f"History: **{days}**\n"
        "Scope: all governors linked to your account when you press Download.\n"
        f"This window expires after {_OPTIONS_TIMEOUT_SECONDS // 60} minutes."
    )


async def send_account_data_options(
    interaction: discord.Interaction,
    *,
    display_name: str,
) -> None:
    view = AccountDataOptionsView(
        author_id=int(interaction.user.id),
        display_name=display_name,
    )
    view.set_timeout_target(interaction)
    message = await _send_private_message(
        interaction,
        _options_copy(view),
        view=view,
    )
    view.set_message_ref(message)
