from __future__ import annotations

import asyncio
import io
import json
import logging
from typing import Any

import discord

from account_picker import AccountPickerView, build_unique_gov_options
from bot_config import INVENTORY_ADMIN_DEBUG_CHANNEL_ID
from decoraters import _is_admin
from inventory import inventory_service, material_service
from inventory.material_calculations import MATERIAL_RARITIES, normalize_material_values
from inventory.models import (
    InventoryAnalysisSummary,
    InventoryFlowType,
    InventoryImagePayload,
    InventoryImportType,
)
from inventory.parsing import (
    apply_resource_total_corrections,
    apply_speedup_duration_corrections,
    format_resource_value,
    format_speedup_duration,
    parse_resource_value,
)
from services import inventory_import_audit_service as inventory_audit

logger = logging.getLogger(__name__)

SCREENSHOT_GUIDELINES = (
    "Upload a full screenshot.\n"
    "Do not crop the image.\n"
    "Make sure all rows and values are visible.\n"
    "Use English game language if possible.\n"
    "Do not upload edited or compressed screenshots."
)
INVENTORY_REVIEW_TIMEOUT_SECONDS = 900
INVENTORY_REVIEW_UI_TIMEOUT_SECONDS = 870


def _format_values_for_display(summary: InventoryAnalysisSummary) -> str:
    if summary.import_type == InventoryImportType.RESOURCES:
        resources = summary.values.get("resources") or {}
        lines = []
        for key in ("food", "wood", "stone", "gold"):
            row = resources.get(key) or {}
            total = row.get("total_resources_value")
            total_text = format_resource_value(total) if total is not None else "unreadable"
            lines.append(f"{key.title()}: `{total_text}`")
        return "\n".join(lines)
    if summary.import_type == InventoryImportType.SPEEDUPS:
        speedups = summary.values.get("speedups") or {}
        lines = []
        for key in ("building", "research", "training", "healing", "universal"):
            row = speedups.get(key) or {}
            minutes = row.get("total_minutes")
            duration = format_speedup_duration(minutes) if minutes is not None else "unreadable"
            lines.append(f"{key.title()}: `{duration}`")
        return "\n".join(lines)
    if summary.import_type == InventoryImportType.MATERIALS:
        try:
            materials = normalize_material_values(summary.values)
        except ValueError:
            return "No readable Materials values detected."
        return "\n".join(material_service.format_material_review_lines(materials))
    return "No Phase 1A values detected."


def _resource_modal_value(value: Any) -> str:
    try:
        parsed = parse_resource_value(value)
    except ValueError:
        return ""
    compact = format_resource_value(parsed)
    try:
        if parse_resource_value(compact) == parsed:
            return compact
    except ValueError:
        pass
    return str(parsed)


def _analysis_embed(
    *, governor_id: int, summary: InventoryAnalysisSummary, corrected: bool = False
) -> discord.Embed:
    color = 0x2ECC71 if summary.ok else 0xE74C3C
    if summary.ok and summary.confidence_score < 0.90:
        color = 0xF1C40F
    title = "Inventory Import Review"
    if corrected:
        title = "Inventory Import Review (Corrected)"
    embed = discord.Embed(title=title, color=color)
    embed.add_field(name="GovernorID", value=f"`{governor_id}`", inline=True)
    embed.add_field(name="Detected Type", value=f"`{summary.import_type.value}`", inline=True)
    review_status = "Ready for approval"
    if summary.confidence_score < 0.90 or summary.warnings:
        review_status = "Needs careful review"
    embed.add_field(name="Review Status", value=review_status, inline=True)
    if summary.warnings:
        embed.add_field(name="Warnings", value="\n".join(summary.warnings)[:1024], inline=False)
    if summary.error:
        embed.add_field(name="Error", value=summary.error[:1024], inline=False)
    embed.add_field(
        name="Detected Values", value=_format_values_for_display(summary)[:1024], inline=False
    )
    return embed


async def _send_private(interaction: discord.Interaction, content: str, **kwargs: Any) -> None:
    response_done = getattr(interaction.response, "is_done", None)
    done = False
    if callable(response_done):
        try:
            result = response_done()
            if asyncio.iscoroutine(result):
                done = bool(await result)
            else:
                done = bool(result)
        except (AttributeError, TypeError) as exc:
            logger.debug("Failed to check response.is_done(): %r", exc)
            done = False
    elif response_done is not None:
        done = bool(response_done)
    if done:
        await interaction.followup.send(content, ephemeral=True, **kwargs)
    else:
        await interaction.response.send_message(content, ephemeral=True, **kwargs)


async def _send_followup_capture_message(interaction: discord.Interaction, **kwargs: Any) -> Any:
    try:
        return await interaction.followup.send(wait=True, **kwargs)
    except TypeError:
        return await interaction.followup.send(**kwargs)


async def _safe_followup_send(interaction: discord.Interaction, **kwargs: Any) -> Any:
    try:
        return await interaction.followup.send(**kwargs)
    except discord.NotFound:
        logger.debug("inventory_followup_webhook_expired", exc_info=True)
        return None


async def _send_review_message(
    *,
    interaction: discord.Interaction | None,
    original_message: discord.Message | None,
    actor_discord_id: int,
    content: str,
    embed: discord.Embed,
    view: discord.ui.View,
) -> discord.Message | None:
    if original_message is not None:
        return await original_message.channel.send(
            f"<@{actor_discord_id}> {content}",
            embed=embed,
            view=view,
            delete_after=INVENTORY_REVIEW_TIMEOUT_SECONDS,
        )
    if interaction is None:
        return None
    try:
        return await _send_followup_capture_message(
            interaction,
            content=content,
            embed=embed,
            view=view,
            ephemeral=True,
            delete_after=INVENTORY_REVIEW_UI_TIMEOUT_SECONDS,
        )
    except discord.NotFound:
        logger.warning(
            "inventory_review_followup_expired actor=%s",
            actor_discord_id,
            exc_info=True,
        )
        return None


async def _post_admin_debug(
    *,
    bot: Any,
    batch_id: int,
    governor_id: int,
    discord_user_id: int,
    status: str,
    payload: InventoryImagePayload,
    summary: InventoryAnalysisSummary | None,
    corrected_json: dict[str, Any] | None = None,
    final_json: dict[str, Any] | None = None,
    error_json: dict[str, Any] | None = None,
) -> None:
    if not INVENTORY_ADMIN_DEBUG_CHANNEL_ID:
        logger.warning("inventory_admin_debug_channel_missing batch_id=%s", batch_id)
        return
    channel = bot.get_channel(INVENTORY_ADMIN_DEBUG_CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(INVENTORY_ADMIN_DEBUG_CHANNEL_ID)
        except Exception:
            logger.warning(
                "inventory_admin_debug_channel_fetch_failed batch_id=%s channel_id=%s",
                batch_id,
                INVENTORY_ADMIN_DEBUG_CHANNEL_ID,
                exc_info=True,
            )
            return

    embed = discord.Embed(title="Inventory Import Debug", color=0xE67E22)
    embed.add_field(name="Batch ID", value=f"`{batch_id}`", inline=True)
    embed.add_field(name="GovernorID", value=f"`{governor_id}`", inline=True)
    embed.add_field(name="DiscordUserID", value=f"`{discord_user_id}`", inline=True)
    embed.add_field(name="Status", value=f"`{status}`", inline=True)
    if summary:
        embed.add_field(name="Import Type", value=f"`{summary.import_type.value}`", inline=True)
        embed.add_field(name="Confidence", value=f"`{summary.confidence_score:.2f}`", inline=True)
        embed.add_field(name="Model", value=f"`{summary.model}`", inline=True)
        embed.add_field(name="Prompt", value=f"`{summary.prompt_version}`", inline=True)
        embed.add_field(
            name="Fallback", value="yes" if summary.fallback_used else "no", inline=True
        )
        if summary.warnings:
            embed.add_field(name="Warnings", value="\n".join(summary.warnings)[:1024], inline=False)
    debug_payload = inventory_service.build_admin_debug_payload(
        summary=summary,
        corrected_json=corrected_json,
        final_json=final_json,
        error_json=error_json,
    )
    embed.add_field(
        name="JSON",
        value=f"```json\n{json.dumps(debug_payload, ensure_ascii=False, sort_keys=True)[:900]}\n```",
        inline=False,
    )
    file = discord.File(fp=io.BytesIO(payload.image_bytes), filename=payload.filename)
    message = await channel.send(embed=embed, file=file)
    await inventory_service.update_debug_reference(
        import_batch_id=batch_id,
        admin_debug_channel_id=message.channel.id,
        admin_debug_message_id=message.id,
    )


class InventoryConfirmationView(discord.ui.View):
    def __init__(
        self,
        *,
        bot: Any,
        actor_discord_id: int,
        governor_id: int,
        batch_id: int,
        payload: InventoryImagePayload,
        summary: InventoryAnalysisSummary,
        original_message: discord.Message | None = None,
        audit_batch_ref: Any | None = None,
        flow_type: str = InventoryFlowType.UPLOAD_FIRST.value,
    ) -> None:
        super().__init__(timeout=INVENTORY_REVIEW_UI_TIMEOUT_SECONDS)
        self.bot = bot
        self.actor_discord_id = int(actor_discord_id)
        self.governor_id = int(governor_id)
        self.batch_id = int(batch_id)
        self.payload = payload
        self.summary = summary
        self.original_message = original_message
        self.audit_batch_ref = audit_batch_ref
        self.flow_type = flow_type
        self.corrected_values: dict[str, Any] | None = None
        self._terminal = False
        self._expired = False
        self._significant_change_confirmed = False
        self._significant_change_warnings: list[str] = []
        self.message: discord.Message | None = None
        self._timeout_task: asyncio.Task[None] | None = None

        if summary.import_type == InventoryImportType.UNKNOWN:
            for child in self.children:
                if getattr(child, "custom_id", "") == "inventory_import_approve":
                    child.disabled = True

    def start_timeout_watch(self, *, timeout_seconds: float | None = None) -> None:
        if self._timeout_task is not None and not self._timeout_task.done():
            return
        delay = float(timeout_seconds or INVENTORY_REVIEW_UI_TIMEOUT_SECONDS)
        self._timeout_task = asyncio.create_task(self._timeout_watch(delay))

    async def _timeout_watch(self, delay: float) -> None:
        try:
            await asyncio.sleep(delay)
            if not self._terminal:
                await self.on_timeout()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.debug(
                "inventory_review_timeout_watch_failed batch_id=%s",
                self.batch_id,
                exc_info=True,
            )

    async def _mark_unusable(
        self, interaction: discord.Interaction | None, *, expired: bool, content: str
    ) -> None:
        self._terminal = True
        self._expired = expired
        self.disable_all_items()
        self.stop()
        current_task = asyncio.current_task()
        if (
            self._timeout_task is not None
            and self._timeout_task is not current_task
            and not self._timeout_task.done()
        ):
            self._timeout_task.cancel()
        message = getattr(interaction, "message", None) if interaction is not None else None
        message = message or self.message
        if message is None:
            return
        self.message = message
        try:
            await message.edit(content=content, view=self)
        except Exception:
            logger.debug("inventory_review_unusable_message_edit_failed", exc_info=True)

    def _terminal_message(self) -> str:
        if self._expired:
            return "This import review expired. Please upload the screenshot again."
        return "This import has already been completed."

    def _is_locally_unusable(self) -> bool:
        return self._terminal or self._expired

    async def _deny_if_not_actor(self, interaction: discord.Interaction) -> bool:
        actor = getattr(interaction, "user", None)
        if actor is not None and int(actor.id) != self.actor_discord_id:
            await _send_private(
                interaction, "Only the user who started this import can use these buttons."
            )
            return True
        if self._is_locally_unusable():
            await _send_private(interaction, self._terminal_message())
            return True
        try:
            state = await inventory_service.get_review_action_state(self.batch_id)
        except Exception:
            logger.exception("inventory_review_state_check_failed batch_id=%s", self.batch_id)
            await _send_private(
                interaction,
                f"Could not verify this import state. Please try again or contact an admin with batch ID {self.batch_id}.",
            )
            return True
        if state.active:
            return False
        await self._mark_unusable(
            interaction,
            expired=state.expired,
            content=state.message or self._terminal_message(),
        )
        await _send_private(interaction, state.message or self._terminal_message())
        return True

    async def _deny_if_modal_unusable(self, interaction: discord.Interaction) -> bool:
        if self._is_locally_unusable():
            await _send_private(interaction, self._terminal_message())
            return True
        try:
            state = await inventory_service.get_review_action_state(self.batch_id)
        except Exception:
            logger.exception("inventory_review_state_check_failed batch_id=%s", self.batch_id)
            await _send_private(
                interaction,
                f"Could not verify this import state. Please try again or contact an admin with batch ID {self.batch_id}.",
            )
            return True
        if state.active:
            return False
        terminal_msg = state.message or self._terminal_message()
        await self._mark_unusable(
            interaction,
            expired=state.expired,
            content=terminal_msg,
        )
        await _send_private(interaction, terminal_msg)
        return True

    async def _requires_second_approve(self, interaction: discord.Interaction) -> bool:
        if self._significant_change_confirmed:
            return False
        final_values = self.corrected_values or self.summary.values
        try:
            assessment = await inventory_service.assess_significant_change(
                governor_id=self.governor_id,
                import_type=self.summary.import_type,
                values=final_values,
                baseline_values=self.summary.values if self.corrected_values is not None else None,
            )
        except Exception:
            logger.exception("inventory_significant_change_check_failed batch_id=%s", self.batch_id)
            await _send_private(
                interaction,
                f"Could not assess whether this import is significantly different from the latest approved import. "
                f"Please try again or contact an admin with batch ID {self.batch_id}.",
            )
            return True
        if not assessment.requires_confirmation:
            return False
        self._significant_change_confirmed = True
        self._significant_change_warnings = assessment.warnings
        warning_text = "\n".join(f"- {item}" for item in assessment.warnings[:5])
        await _send_private(
            interaction,
            (
                "This import is significantly different from the latest approved import for this governor.\n"
                f"{warning_text}\n\nPress Approve Import again to confirm these values."
            ),
        )
        await self._update_review_message(
            interaction,
            content="Significant change detected. Press Approve Import again to confirm.",
        )
        return True

    async def _update_review_message(
        self, interaction: discord.Interaction, *, content: str | None = None
    ) -> None:
        message = getattr(interaction, "message", None) or self.message
        if message is None:
            return
        self.message = message
        embed = _analysis_embed(
            governor_id=self.governor_id,
            summary=self.summary,
            corrected=self.corrected_values is not None,
        )
        if self.corrected_values is not None:
            corrected_summary = InventoryAnalysisSummary(
                ok=self.summary.ok,
                import_type=self.summary.import_type,
                values=self.corrected_values,
                confidence_score=self.summary.confidence_score,
                warnings=self.summary.warnings,
                model=self.summary.model,
                prompt_version=self.summary.prompt_version,
                fallback_used=self.summary.fallback_used,
                error=self.summary.error,
                raw_json=self.summary.raw_json,
            )
            embed.set_field_at(
                len(embed.fields) - 1,
                name="Corrected Values",
                value=_format_values_for_display(corrected_summary)[:1024],
                inline=False,
            )
            if not self._terminal:
                embed.add_field(
                    name="Approval Required",
                    value="Corrections are saved for this pending import. Press Approve Import to save them.",
                    inline=False,
                )
        if self._significant_change_warnings and not self._terminal:
            embed.add_field(
                name="Significant Change Check",
                value=(
                    "\n".join(self._significant_change_warnings[:5])
                    + "\nPress Approve Import again to confirm."
                )[:1024],
                inline=False,
            )
        try:
            await message.edit(
                content=content or "Review the detected inventory values before approving.",
                embed=embed,
                view=self,
            )
        except Exception:
            try:
                await interaction.edit_original_response(
                    content=content or "Review the detected inventory values before approving.",
                    embed=embed,
                    view=self,
                )
            except Exception:
                logger.debug("inventory_review_message_update_failed", exc_info=True)

    @discord.ui.button(
        label="Approve Import",
        style=discord.ButtonStyle.success,
        custom_id="inventory_import_approve",
    )
    async def approve(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        if await self._deny_if_not_actor(interaction):
            return
        self.message = getattr(interaction, "message", None)
        await interaction.response.defer(ephemeral=True)
        try:
            final_values = self.corrected_values or self.summary.values
            if await self._requires_second_approve(interaction):
                return
            approval_started = inventory_audit.audit_timestamp_utc()
            normalized = await inventory_service.approve_import(
                import_batch_id=self.batch_id,
                governor_id=self.governor_id,
                summary=self.summary,
                final_values=final_values,
                corrected_values=self.corrected_values,
                is_admin=_is_admin(interaction.user),
            )
        except ValueError as exc:
            phase_status = "duplicate" if "already has an approved import" in str(exc) else "failed"
            await inventory_audit.record_inventory_audit_phase(
                await self._get_audit_batch_ref(),
                phase_name=inventory_audit.INVENTORY_AUDIT_APPROVAL_PHASE,
                phase_status=phase_status,
                error_type=type(exc).__name__,
                error_text=str(exc),
                details=inventory_audit.inventory_audit_details(
                    self._audit_context(),
                    import_type=self.summary.import_type,
                    error=str(exc),
                ),
            )
            await interaction.followup.send(str(exc), ephemeral=True)
            return
        except Exception as exc:
            logger.exception("inventory_import_approve_failed batch_id=%s", self.batch_id)
            await inventory_audit.record_inventory_audit_phase(
                await self._get_audit_batch_ref(),
                phase_name=inventory_audit.INVENTORY_AUDIT_APPROVAL_PHASE,
                phase_status="failed",
                error_type=type(exc).__name__,
                error_text=str(exc),
                details=inventory_audit.inventory_audit_details(
                    self._audit_context(),
                    import_type=self.summary.import_type,
                    error=str(exc),
                ),
            )
            await interaction.followup.send(
                f"Approval failed due to an internal error. Please try again or contact an admin with batch ID {self.batch_id}.",
                ephemeral=True,
            )
            return
        rows_written = inventory_audit.inventory_row_count(self.summary.import_type, normalized)
        rows_in_source = inventory_audit.image_count_from_summary(self.summary)
        await inventory_audit.record_inventory_audit_phase(
            await self._get_audit_batch_ref(),
            phase_name=inventory_audit.INVENTORY_AUDIT_APPROVAL_PHASE,
            phase_status="completed",
            started_at_utc=approval_started,
            rows_in=rows_in_source,
            rows_out=rows_written,
            duration_ms=inventory_audit.audit_duration_ms(approval_started),
            details=inventory_audit.inventory_audit_details(
                self._audit_context(),
                import_type=self.summary.import_type,
                rows_in_source=rows_in_source,
                rows_written=rows_written,
                domain_status="approved",
            ),
        )
        self._terminal = True
        self.disable_all_items()
        self.stop()
        if self.corrected_values:
            try:
                await _post_admin_debug(
                    bot=self.bot,
                    batch_id=self.batch_id,
                    governor_id=self.governor_id,
                    discord_user_id=self.actor_discord_id,
                    status="corrected_approved",
                    payload=self.payload,
                    summary=self.summary,
                    corrected_json=self.corrected_values,
                    final_json=normalized,
                )
                await inventory_audit.record_inventory_audit_phase(
                    await self._get_audit_batch_ref(),
                    phase_name=inventory_audit.INVENTORY_AUDIT_ADMIN_DEBUG_PHASE,
                    phase_status="completed",
                    details=inventory_audit.inventory_audit_details(
                        self._audit_context(),
                        import_type=self.summary.import_type,
                        admin_debug_status="corrected_approved",
                    ),
                )
            except Exception:
                logger.exception("inventory_approve_debug_post_failed batch_id=%s", self.batch_id)
                await inventory_audit.record_inventory_audit_phase(
                    await self._get_audit_batch_ref(),
                    phase_name=inventory_audit.INVENTORY_AUDIT_ADMIN_DEBUG_PHASE,
                    phase_status="failed",
                    details=inventory_audit.inventory_audit_details(
                        self._audit_context(),
                        import_type=self.summary.import_type,
                        admin_debug_status="corrected_approved",
                    ),
                )
        deleted = await _delete_original_upload(
            original_message=self.original_message,
            batch_id=self.batch_id,
        )
        await inventory_audit.record_inventory_audit_phase(
            await self._get_audit_batch_ref(),
            phase_name=inventory_audit.INVENTORY_AUDIT_UPLOAD_CLEANUP_PHASE,
            phase_status="completed" if deleted else "skipped",
            details=inventory_audit.inventory_audit_details(
                self._audit_context(),
                import_type=self.summary.import_type,
                cleanup_deleted=deleted,
            ),
        )
        await inventory_audit.record_inventory_audit_phase(
            await self._get_audit_batch_ref(),
            phase_name=inventory_audit.INVENTORY_AUDIT_TERMINAL_PHASE,
            phase_status="completed",
            rows_in=rows_in_source,
            rows_out=rows_written,
            details=inventory_audit.inventory_audit_details(
                self._audit_context(),
                import_type=self.summary.import_type,
                rows_in_source=rows_in_source,
                rows_written=rows_written,
                domain_status="approved",
            ),
        )
        await inventory_audit.complete_inventory_audit_batch(
            await self._get_audit_batch_ref(),
            status="completed",
            rows_in_source=rows_in_source,
            rows_staged=rows_in_source,
            rows_written=rows_written,
            rows_skipped=0,
            details=inventory_audit.inventory_audit_details(
                self._audit_context(),
                import_type=self.summary.import_type,
                rows_in_source=rows_in_source,
                rows_written=rows_written,
                domain_status="approved",
            ),
        )
        await interaction.followup.send("Inventory import approved.", ephemeral=True)
        await self._update_review_message(interaction, content="Inventory import approved.")

    @discord.ui.button(
        label="Correct Data",
        style=discord.ButtonStyle.primary,
        custom_id="inventory_import_correct",
    )
    async def correct(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        if await self._deny_if_not_actor(interaction):
            return
        self.message = getattr(interaction, "message", None)
        if self.summary.import_type == InventoryImportType.RESOURCES:
            await interaction.response.send_modal(ResourceCorrectionModal(self))
            return
        if self.summary.import_type == InventoryImportType.SPEEDUPS:
            await interaction.response.send_modal(SpeedupCorrectionModal(self))
            return
        if self.summary.import_type == InventoryImportType.MATERIALS:
            await interaction.response.send_message(
                "Choose the Materials section to correct:",
                view=MaterialCorrectionSectionView(parent=self),
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            "Corrections are not available for this import type.",
            ephemeral=True,
        )

    @discord.ui.button(
        label="Add Another Image",
        style=discord.ButtonStyle.secondary,
        custom_id="inventory_import_add_material_image",
    )
    async def add_material_image(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        if await self._deny_if_not_actor(interaction):
            return
        if self.summary.import_type != InventoryImportType.MATERIALS:
            await interaction.response.send_message(
                "Additional screenshots are only supported for Materials imports.",
                ephemeral=True,
            )
            return
        await interaction.response.defer(ephemeral=True)
        try:
            await inventory_service.set_batch_awaiting_more_material(self.batch_id)
        except Exception:
            logger.exception(
                "inventory_set_awaiting_more_material_failed batch_id=%s", self.batch_id
            )
            await interaction.followup.send(
                "Could not prepare this import for an additional screenshot. Please try again.",
                ephemeral=True,
            )
            return
        await inventory_audit.record_inventory_audit_phase(
            await self._get_audit_batch_ref(),
            phase_name=inventory_audit.INVENTORY_AUDIT_MATERIAL_MORE_PHASE,
            phase_status="completed",
            details=inventory_audit.inventory_audit_details(
                self._audit_context(),
                import_type=self.summary.import_type,
                domain_status="awaiting_more_material",
            ),
        )
        self._terminal = True
        self.disable_all_items()
        self.stop()
        await self._update_review_message(
            interaction,
            content=(
                "Additional Materials screenshot requested. "
                "Upload the next image; use the newest review message for approval."
            ),
        )
        await interaction.followup.send(
            "Upload the next Materials screenshot in this channel. I will merge it into this pending Materials import.",
            ephemeral=True,
        )

    @discord.ui.button(
        label="Cancel Import",
        style=discord.ButtonStyle.secondary,
        custom_id="inventory_import_cancel",
    )
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        if await self._deny_if_not_actor(interaction):
            return
        self.message = getattr(interaction, "message", None)
        await interaction.response.defer(ephemeral=True)
        try:
            await inventory_service.cancel_import(self.batch_id)
        except Exception:
            logger.exception("inventory_import_cancel_failed batch_id=%s", self.batch_id)
            await interaction.followup.send(
                f"Cancellation failed due to an internal error. Please try again or contact an admin with batch ID {self.batch_id}.",
                ephemeral=True,
            )
            return
        self._terminal = True
        self.disable_all_items()
        self.stop()
        await inventory_audit.record_inventory_audit_phase(
            await self._get_audit_batch_ref(),
            phase_name=inventory_audit.INVENTORY_AUDIT_TERMINAL_PHASE,
            phase_status="cancelled",
            rows_in=inventory_audit.image_count_from_summary(self.summary),
            rows_out=0,
            details=inventory_audit.inventory_audit_details(
                self._audit_context(),
                import_type=self.summary.import_type,
                domain_status="cancelled",
                terminal_reason="cancelled_by_user",
            ),
        )
        await inventory_audit.complete_inventory_audit_batch(
            await self._get_audit_batch_ref(),
            status="cancelled",
            rows_in_source=inventory_audit.image_count_from_summary(self.summary),
            rows_written=0,
            rows_skipped=inventory_audit.image_count_from_summary(self.summary),
            details=inventory_audit.inventory_audit_details(
                self._audit_context(),
                import_type=self.summary.import_type,
                domain_status="cancelled",
                terminal_reason="cancelled_by_user",
            ),
        )
        deleted = await _delete_original_upload(
            original_message=self.original_message,
            batch_id=self.batch_id,
        )
        await inventory_audit.record_inventory_audit_phase(
            await self._get_audit_batch_ref(),
            phase_name=inventory_audit.INVENTORY_AUDIT_UPLOAD_CLEANUP_PHASE,
            phase_status="completed" if deleted else "skipped",
            details=inventory_audit.inventory_audit_details(
                self._audit_context(),
                import_type=self.summary.import_type,
                cleanup_deleted=deleted,
            ),
        )
        try:
            await _post_admin_debug(
                bot=self.bot,
                batch_id=self.batch_id,
                governor_id=self.governor_id,
                discord_user_id=self.actor_discord_id,
                status="cancelled",
                payload=self.payload,
                summary=self.summary,
                error_json={"error": "Cancelled by user."},
            )
            await inventory_audit.record_inventory_audit_phase(
                await self._get_audit_batch_ref(),
                phase_name=inventory_audit.INVENTORY_AUDIT_ADMIN_DEBUG_PHASE,
                phase_status="completed",
                details=inventory_audit.inventory_audit_details(
                    self._audit_context(),
                    import_type=self.summary.import_type,
                    admin_debug_status="cancelled",
                ),
            )
        except Exception:
            logger.exception("inventory_cancel_debug_post_failed batch_id=%s", self.batch_id)
        await interaction.followup.send(
            "Import cancelled. You can upload a replacement screenshot if needed.\n\n"
            + SCREENSHOT_GUIDELINES,
            ephemeral=True,
        )
        await self._update_review_message(interaction, content="Inventory import cancelled.")

    async def on_timeout(self) -> None:
        if not self._terminal:
            try:
                await inventory_service.cancel_import(self.batch_id)
                await inventory_audit.record_inventory_audit_phase(
                    await self._get_audit_batch_ref(),
                    phase_name=inventory_audit.INVENTORY_AUDIT_TERMINAL_PHASE,
                    phase_status="cancelled",
                    rows_in=inventory_audit.image_count_from_summary(self.summary),
                    rows_out=0,
                    details=inventory_audit.inventory_audit_details(
                        self._audit_context(),
                        import_type=self.summary.import_type,
                        domain_status="cancelled",
                        terminal_reason="timeout",
                    ),
                )
                await inventory_audit.complete_inventory_audit_batch(
                    await self._get_audit_batch_ref(),
                    status="cancelled",
                    rows_in_source=inventory_audit.image_count_from_summary(self.summary),
                    rows_written=0,
                    rows_skipped=inventory_audit.image_count_from_summary(self.summary),
                    details=inventory_audit.inventory_audit_details(
                        self._audit_context(),
                        import_type=self.summary.import_type,
                        domain_status="cancelled",
                        terminal_reason="timeout",
                    ),
                )
            except Exception:
                logger.debug(
                    "inventory_confirmation_timeout_cancel_failed batch_id=%s",
                    self.batch_id,
                    exc_info=True,
                )
        await self._mark_unusable(
            None,
            expired=True,
            content="Inventory import review expired. Please upload the screenshot again.",
        )

    def _audit_context(self) -> inventory_audit.InventoryImportAuditContext:
        return inventory_audit.InventoryImportAuditContext(
            import_batch_id=self.batch_id,
            governor_id=self.governor_id,
            flow_type=self.flow_type,
            source_filename=self.payload.filename,
            source_message_id=self.payload.source_message_id,
            source_channel_id=self.payload.source_channel_id,
            actor_discord_id=self.actor_discord_id,
            entry_point=(
                "inventory_command_upload"
                if self.flow_type == InventoryFlowType.COMMAND.value
                else "inventory_upload_first"
            ),
        )

    async def _get_audit_batch_ref(self) -> Any | None:
        return self.audit_batch_ref


class ResourceCorrectionModal(discord.ui.Modal):
    def __init__(self, parent: InventoryConfirmationView) -> None:
        super().__init__(title="Correct Resource Totals")
        self.parent_view = parent
        resources = parent.summary.values.get("resources") or {}
        self.inputs: dict[str, discord.ui.InputText] = {}
        for key in ("food", "wood", "stone", "gold"):
            row = resources.get(key) or {}
            value = row.get("total_resources_value")
            field = discord.ui.InputText(
                label=f"{key.title()} Total Resources",
                value=_resource_modal_value(value),
                required=True,
            )
            self.inputs[key] = field
            self.add_item(field)

    async def callback(self, interaction: discord.Interaction) -> None:
        if await self.parent_view._deny_if_modal_unusable(interaction):
            return
        corrections = {key: str(field.value or "") for key, field in self.inputs.items()}
        try:
            corrected = apply_resource_total_corrections(
                self.parent_view.summary.values,
                corrections,
            )
        except ValueError as exc:
            await interaction.response.send_message(
                f"Correction rejected: `{exc}`",
                ephemeral=True,
            )
            return
        self.parent_view.corrected_values = corrected
        self.parent_view._significant_change_confirmed = False
        self.parent_view._significant_change_warnings = []
        await interaction.response.send_message(
            "Correction saved. Press Approve Import on the updated review to save it.",
            ephemeral=True,
        )
        await self.parent_view._update_review_message(interaction)


class SpeedupCorrectionModal(discord.ui.Modal):
    def __init__(self, parent: InventoryConfirmationView) -> None:
        super().__init__(title="Correct Speedup Days")
        self.parent_view = parent
        speedups = parent.summary.values.get("speedups") or {}
        self.inputs: dict[str, discord.ui.InputText] = {}
        for key in ("building", "research", "training", "healing", "universal"):
            row = speedups.get(key) or {}
            days = int(row.get("total_minutes") or 0) // 1440
            field = discord.ui.InputText(
                label=f"{key.title()} Speedup Days",
                value=f"{days}d",
                required=True,
            )
            self.inputs[key] = field
            self.add_item(field)

    async def callback(self, interaction: discord.Interaction) -> None:
        if await self.parent_view._deny_if_modal_unusable(interaction):
            return
        corrections = {key: str(field.value or "") for key, field in self.inputs.items()}
        try:
            corrected = apply_speedup_duration_corrections(
                self.parent_view.summary.values,
                corrections,
            )
        except ValueError as exc:
            await interaction.response.send_message(
                f"Correction rejected: `{exc}`",
                ephemeral=True,
            )
            return
        self.parent_view.corrected_values = corrected
        self.parent_view._significant_change_confirmed = False
        self.parent_view._significant_change_warnings = []
        await interaction.response.send_message(
            "Correction saved. Press Approve Import on the updated review to save it.",
            ephemeral=True,
        )
        await self.parent_view._update_review_message(interaction)


class MaterialCorrectionSectionView(discord.ui.View):
    def __init__(self, *, parent: InventoryConfirmationView) -> None:
        super().__init__(timeout=180)
        self.parent_view = parent
        self.add_item(MaterialCorrectionSectionSelect())


class MaterialCorrectionSectionSelect(discord.ui.Select):
    def __init__(self) -> None:
        options = [
            discord.SelectOption(label="Choice Chests", value="choice_chests"),
            discord.SelectOption(label="Animal Bone", value="animal_bone"),
            discord.SelectOption(label="Leather", value="leather"),
            discord.SelectOption(label="Ebony", value="ebony"),
            discord.SelectOption(label="Iron Ore", value="iron_ore"),
        ]
        super().__init__(placeholder="Select Materials section", options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, MaterialCorrectionSectionView):
            return
        if await view.parent_view._deny_if_modal_unusable(interaction):
            return
        await interaction.response.send_modal(
            MaterialCorrectionModal(view.parent_view, self.values[0])
        )


class MaterialCorrectionModal(discord.ui.Modal):
    def __init__(self, parent: InventoryConfirmationView, material_kind: str) -> None:
        self.parent_view = parent
        self.material_kind = material_kind
        labels = {
            "choice_chests": "Choice Chests",
            "animal_bone": "Animal Bone",
            "leather": "Leather",
            "ebony": "Ebony",
            "iron_ore": "Iron Ore",
        }
        super().__init__(title=f"Correct {labels.get(material_kind, material_kind)}")
        try:
            materials = normalize_material_values(parent.corrected_values or parent.summary.values)
        except ValueError:
            materials = {}
        self.inputs: dict[str, discord.ui.InputText] = {}
        row = materials.get(material_kind) or {}
        for rarity in MATERIAL_RARITIES:
            field = discord.ui.InputText(
                label=rarity.title(),
                value=str(int(row.get(rarity) or 0)),
                required=True,
            )
            self.inputs[rarity] = field
            self.add_item(field)

    async def callback(self, interaction: discord.Interaction) -> None:
        if await self.parent_view._deny_if_modal_unusable(interaction):
            return
        corrections = {key: str(field.value or "") for key, field in self.inputs.items()}
        try:
            corrected = material_service.apply_material_corrections(
                self.parent_view.corrected_values or self.parent_view.summary.values,
                self.material_kind,
                corrections,
            )
        except ValueError as exc:
            await interaction.response.send_message(
                f"Correction rejected: `{exc}`",
                ephemeral=True,
            )
            return
        self.parent_view.corrected_values = corrected
        self.parent_view._significant_change_confirmed = False
        self.parent_view._significant_change_warnings = []
        await interaction.response.send_message(
            "Correction saved. Press Approve Import on the updated review to save it.",
            ephemeral=True,
        )
        await self.parent_view._update_review_message(interaction)


class InventoryUploadGovernorSelectView(AccountPickerView):
    def __init__(
        self,
        *,
        ctx: Any,
        bot: Any,
        options: list[discord.SelectOption],
        actor_discord_id: int,
        payload: InventoryImagePayload,
        original_message: discord.Message,
    ) -> None:
        self.bot = bot
        self.actor_discord_id = int(actor_discord_id)
        self.payload = payload
        self.original_message = original_message

        async def _on_select(
            interaction: discord.Interaction, governor_id: str, ephemeral: bool
        ) -> None:
            if int(interaction.user.id) != self.actor_discord_id:
                await interaction.followup.send("This selector is not for you.", ephemeral=True)
                return
            await _process_payload_for_governor(
                bot=self.bot,
                interaction=interaction,
                governor_id=int(governor_id),
                actor_discord_id=self.actor_discord_id,
                payload=self.payload,
                original_message=self.original_message,
                batch_id=None,
                flow_from_pending_command=False,
            )

        super().__init__(
            ctx=ctx,
            options=options,
            on_select_governor=_on_select,
            heading="Select the governor this inventory image belongs to:",
            show_register_btn=False,
            ephemeral=True,
            timeout=300,
        )

    async def on_timeout(self) -> None:
        try:
            await super().on_timeout()
        finally:
            try:
                await self.original_message.delete()
            except Exception:
                logger.debug("inventory_upload_timeout_delete_failed", exc_info=True)


async def _delete_original_upload(
    *, original_message: discord.Message | None, batch_id: int | None
) -> bool:
    if original_message is None:
        return False
    try:
        await original_message.delete()
        if batch_id is not None:
            await inventory_service.mark_original_upload_deleted(batch_id)
        return True
    except Exception:
        logger.debug("inventory_original_upload_delete_failed", exc_info=True)
        return False


async def _process_payload_for_governor(
    *,
    bot: Any,
    interaction: discord.Interaction | None,
    governor_id: int,
    actor_discord_id: int,
    payload: InventoryImagePayload,
    original_message: discord.Message | None,
    batch_id: int | None,
    flow_from_pending_command: bool,
    flow_type: str | None = None,
    existing_detected_json: dict[str, Any] | None = None,
) -> None:
    if interaction is not None:
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

    audit_batch_ref: Any | None = None
    audit_context: inventory_audit.InventoryImportAuditContext | None = None
    try:
        resolved_flow_type = flow_type or (
            InventoryFlowType.COMMAND.value
            if flow_from_pending_command
            else InventoryFlowType.UPLOAD_FIRST.value
        )
        if batch_id is None:
            batch_id = await inventory_service.create_upload_first_batch(
                governor_id=governor_id,
                discord_user_id=actor_discord_id,
                payload=payload,
                is_admin=_is_admin(getattr(interaction, "user", None)) if interaction else False,
            )
            resolved_flow_type = InventoryFlowType.UPLOAD_FIRST.value
        audit_context = inventory_audit.InventoryImportAuditContext(
            import_batch_id=batch_id,
            governor_id=governor_id,
            flow_type=resolved_flow_type,
            source_filename=payload.filename,
            source_message_id=payload.source_message_id,
            source_channel_id=payload.source_channel_id,
            actor_discord_id=actor_discord_id,
            entry_point=(
                "inventory_additional_material_upload"
                if existing_detected_json is not None
                else (
                    "inventory_command_upload"
                    if resolved_flow_type == InventoryFlowType.COMMAND.value
                    else "inventory_upload_first"
                )
            ),
        )
        if existing_detected_json is not None:
            audit_batch_ref = await inventory_audit.fetch_inventory_audit_batch(
                import_batch_id=batch_id
            )
            if audit_batch_ref is None:
                audit_batch_ref = await inventory_audit.start_inventory_audit_batch(
                    context=audit_context,
                    image_bytes=payload.image_bytes,
                )
        else:
            audit_batch_ref = await inventory_audit.start_inventory_audit_batch(
                context=audit_context,
                image_bytes=payload.image_bytes,
            )
        await inventory_audit.record_inventory_audit_phase(
            audit_batch_ref,
            phase_name=inventory_audit.INVENTORY_AUDIT_IMAGE_READ_PHASE,
            phase_status="completed",
            rows_in=1,
            rows_out=1,
            details=inventory_audit.inventory_audit_details(
                audit_context,
                rows_in_source=1,
            ),
        )
        await inventory_audit.record_inventory_audit_phase(
            audit_batch_ref,
            phase_name=inventory_audit.INVENTORY_AUDIT_BATCH_HANDOFF_PHASE,
            phase_status="completed",
            details=inventory_audit.inventory_audit_details(audit_context),
        )
        analysis_started = inventory_audit.audit_timestamp_utc()
        if existing_detected_json is not None:
            summary = await inventory_service.analyse_additional_material_image(
                import_batch_id=batch_id,
                existing_detected_json=existing_detected_json,
                payload=payload,
            )
        else:
            summary = await inventory_service.analyse_inventory_image(
                import_batch_id=batch_id,
                payload=payload,
            )
        decision = inventory_service.decide_analysis_outcome(summary)
        analysis_phase = (
            inventory_audit.INVENTORY_AUDIT_MATERIAL_MERGE_PHASE
            if existing_detected_json is not None
            else inventory_audit.INVENTORY_AUDIT_VISION_PHASE
        )
        await inventory_audit.record_inventory_audit_phase(
            audit_batch_ref,
            phase_name=analysis_phase,
            phase_status="completed" if decision.action != "fail" else "failed",
            started_at_utc=analysis_started,
            rows_in=1,
            rows_out=1 if decision.action != "fail" else 0,
            duration_ms=inventory_audit.audit_duration_ms(analysis_started),
            error_type="InventoryAnalysisFailed" if decision.action == "fail" else None,
            error_text=decision.error if decision.action == "fail" else None,
            details=inventory_audit.inventory_audit_details(
                audit_context,
                import_type=summary.import_type,
                rows_in_source=inventory_audit.image_count_from_summary(summary),
                error=decision.error,
            ),
            set_batch_status="staged" if decision.action != "fail" else None,
        )
        if decision.action == "fail":
            if existing_detected_json is None:
                await inventory_service.fail_import(batch_id, error=decision.error)
                await inventory_audit.record_inventory_audit_phase(
                    audit_batch_ref,
                    phase_name=inventory_audit.INVENTORY_AUDIT_TERMINAL_PHASE,
                    phase_status="failed",
                    rows_in=1,
                    rows_out=0,
                    error_type="InventoryAnalysisFailed",
                    error_text=decision.error,
                    details=inventory_audit.inventory_audit_details(
                        audit_context,
                        import_type=summary.import_type,
                        domain_status="failed",
                        terminal_reason="analysis_failed",
                        error=decision.error,
                    ),
                )
                await inventory_audit.fail_inventory_audit_batch(
                    audit_batch_ref,
                    status="failed",
                    error_type="InventoryAnalysisFailed",
                    error_text=decision.error,
                    rows_in_source=1,
                    rows_written=0,
                    rows_skipped=1,
                    details=inventory_audit.inventory_audit_details(
                        audit_context,
                        import_type=summary.import_type,
                        domain_status="failed",
                        terminal_reason="analysis_failed",
                        error=decision.error,
                    ),
                )
            else:
                try:
                    await inventory_service.revert_additional_material_upload(batch_id)
                except Exception:
                    logger.exception(
                        "inventory_revert_additional_material_failed batch_id=%s", batch_id
                    )
            await _post_admin_debug(
                bot=bot,
                batch_id=batch_id,
                governor_id=governor_id,
                discord_user_id=actor_discord_id,
                status=decision.debug_status or "failed",
                payload=payload,
                summary=summary,
                error_json={"error": decision.error},
            )
            await inventory_audit.record_inventory_audit_phase(
                audit_batch_ref,
                phase_name=inventory_audit.INVENTORY_AUDIT_ADMIN_DEBUG_PHASE,
                phase_status="completed",
                details=inventory_audit.inventory_audit_details(
                    audit_context,
                    import_type=summary.import_type,
                    admin_debug_status=decision.debug_status or "failed",
                ),
            )
            message = (
                "I could not read this inventory screenshot clearly enough. No values were saved.\n\n"
                + SCREENSHOT_GUIDELINES
            )
            if existing_detected_json is not None:
                message = (
                    "I could not read this additional Materials screenshot clearly enough. "
                    "Your pending Materials import is still active.\n\n" + SCREENSHOT_GUIDELINES
                )
            if interaction is not None:
                sent = await _safe_followup_send(interaction, content=message, ephemeral=True)
                if sent is None and original_message is not None:
                    await original_message.channel.send(
                        f"<@{actor_discord_id}> {message}", delete_after=120
                    )
            elif original_message is not None:
                await original_message.channel.send(
                    f"<@{actor_discord_id}> {message}", delete_after=120
                )
            return

        embed = _analysis_embed(governor_id=governor_id, summary=summary)
        if decision.action == "reject":
            await inventory_service.reject_import(batch_id, error=decision.error)
            await inventory_audit.record_inventory_audit_phase(
                audit_batch_ref,
                phase_name=inventory_audit.INVENTORY_AUDIT_TERMINAL_PHASE,
                phase_status="skipped",
                rows_in=1,
                rows_out=0,
                error_type="InventoryRejected",
                error_text=decision.error,
                details=inventory_audit.inventory_audit_details(
                    audit_context,
                    import_type=summary.import_type,
                    domain_status="rejected",
                    terminal_reason="rejected",
                    error=decision.error,
                ),
            )
            await inventory_audit.complete_inventory_audit_batch(
                audit_batch_ref,
                status="skipped",
                rows_in_source=1,
                rows_written=0,
                rows_skipped=1,
                details=inventory_audit.inventory_audit_details(
                    audit_context,
                    import_type=summary.import_type,
                    domain_status="rejected",
                    terminal_reason="rejected",
                    error=decision.error,
                ),
            )
            await _post_admin_debug(
                bot=bot,
                batch_id=batch_id,
                governor_id=governor_id,
                discord_user_id=actor_discord_id,
                status=decision.debug_status or "rejected",
                payload=payload,
                summary=summary,
                error_json={"error": decision.error},
            )
            content = decision.error or "No values were saved."
            if interaction is not None:
                sent = await _safe_followup_send(
                    interaction,
                    content=content,
                    embed=embed,
                    ephemeral=True,
                )
                if sent is None and original_message is not None:
                    await original_message.channel.send(
                        f"<@{actor_discord_id}> {content}", embed=embed, delete_after=120
                    )
            elif original_message is not None:
                await original_message.channel.send(
                    f"<@{actor_discord_id}> {content}", embed=embed, delete_after=120
                )
            return

        view = InventoryConfirmationView(
            bot=bot,
            actor_discord_id=actor_discord_id,
            governor_id=governor_id,
            batch_id=batch_id,
            payload=payload,
            summary=summary,
            audit_batch_ref=audit_batch_ref,
            flow_type=resolved_flow_type,
        )
        content = "Review the detected inventory values before approving."
        if flow_from_pending_command:
            content = "Screenshot received. Review the detected inventory values before approving."
        view.original_message = original_message
        sent = await _send_review_message(
            interaction=interaction,
            original_message=original_message,
            actor_discord_id=actor_discord_id,
            content=content,
            embed=embed,
            view=view,
        )
        view.message = sent
        await inventory_audit.record_inventory_audit_phase(
            audit_batch_ref,
            phase_name=inventory_audit.INVENTORY_AUDIT_REVIEW_PHASE,
            phase_status="completed",
            rows_in=inventory_audit.image_count_from_summary(summary),
            rows_out=inventory_audit.image_count_from_summary(summary),
            details=inventory_audit.inventory_audit_details(
                audit_context,
                import_type=summary.import_type,
                rows_in_source=inventory_audit.image_count_from_summary(summary),
                domain_status="analysed",
            ),
            set_batch_status="staged",
        )
        view.start_timeout_watch()
    except Exception as exc:
        logger.exception("inventory_process_payload_failed governor_id=%s", governor_id)
        if audit_batch_ref is not None and audit_context is not None:
            await inventory_audit.record_inventory_audit_phase(
                audit_batch_ref,
                phase_name=inventory_audit.INVENTORY_AUDIT_TERMINAL_PHASE,
                phase_status="failed",
                rows_in=1,
                rows_out=0,
                error_type=type(exc).__name__,
                error_text=str(exc),
                details=inventory_audit.inventory_audit_details(
                    audit_context,
                    terminal_reason="internal_error",
                    error=str(exc),
                ),
            )
            await inventory_audit.fail_inventory_audit_batch(
                audit_batch_ref,
                status="failed",
                error_type=type(exc).__name__,
                error_text=str(exc),
                rows_in_source=1,
                rows_written=0,
                rows_skipped=1,
                details=inventory_audit.inventory_audit_details(
                    audit_context,
                    terminal_reason="internal_error",
                    error=str(exc),
                ),
            )
        if interaction is not None:
            sent = await _safe_followup_send(
                interaction,
                content=(
                    "Inventory import failed due to an internal error. "
                    "Please try again or contact an admin."
                ),
                ephemeral=True,
            )
            if sent is None and original_message is not None:
                await original_message.channel.send(
                    f"<@{actor_discord_id}> Inventory import failed. Please try again or contact an admin.",
                    delete_after=120,
                )
        elif original_message is not None:
            await original_message.channel.send(
                f"<@{actor_discord_id}> Inventory import failed. Please try again or contact an admin.",
                delete_after=120,
            )


async def start_import_command(ctx: discord.ApplicationContext, bot: Any) -> None:
    governors = await inventory_service.get_registered_governors_for_user(int(ctx.user.id))
    if not governors:
        await ctx.followup.send(
            "I do not see any governors registered to you. Use `/register_governor` first.",
            ephemeral=True,
        )
        return

    async def _create_session(governor_id: int) -> None:
        batch_id = await inventory_service.create_pending_command_session(
            governor_id=governor_id,
            discord_user_id=int(ctx.user.id),
            discord_user=ctx.user,
            is_admin=_is_admin(ctx.user),
        )
        await ctx.followup.send(
            (
                f"Inventory import started for GovernorID `{governor_id}`.\n"
                "Upload one resources, speedups, or materials screenshot in this channel within 10 minutes."
            ),
            ephemeral=True,
        )
        logger.info(
            "inventory_command_pending_session_created batch_id=%s governor_id=%s actor=%s",
            batch_id,
            governor_id,
            ctx.user.id,
        )

    if len(governors) == 1:
        await _create_session(governors[0].governor_id)
        return

    options = build_unique_gov_options(governors)

    async def _on_select(
        interaction: discord.Interaction, governor_id: str, ephemeral: bool
    ) -> None:
        if int(interaction.user.id) != int(ctx.user.id):
            await interaction.followup.send("This selector is not for you.", ephemeral=True)
            return
        await inventory_service.create_pending_command_session(
            governor_id=int(governor_id),
            discord_user_id=int(ctx.user.id),
            discord_user=ctx.user,
            is_admin=_is_admin(ctx.user),
        )
        await interaction.followup.send(
            (
                f"Inventory import started for GovernorID `{governor_id}`.\n"
                "Upload one resources, speedups, or materials screenshot in this channel within 10 minutes."
            ),
            ephemeral=True,
        )

    view = AccountPickerView(
        ctx=ctx,
        options=options,
        on_select_governor=_on_select,
        heading="Select which governor this import is for:",
        show_register_btn=False,
        ephemeral=True,
    )
    await ctx.followup.send(view.heading, view=view, ephemeral=True)


async def handle_inventory_upload_message(message: discord.Message, bot: Any) -> bool:
    attachments = list(message.attachments or [])
    target = next(
        (
            item
            for item in attachments
            if inventory_service.is_supported_image_attachment(
                getattr(item, "filename", None),
                getattr(item, "content_type", None),
            )
        ),
        None,
    )
    if target is None:
        return False

    try:
        image_bytes = await target.read()
    except Exception:
        logger.exception("inventory_upload_attachment_read_failed message_id=%s", message.id)
        await message.channel.send(
            f"<@{message.author.id}> I could not read that image attachment.",
            delete_after=120,
        )
        return True

    payload = InventoryImagePayload(
        image_bytes=image_bytes,
        filename=str(target.filename or "inventory_upload.png"),
        content_type=getattr(target, "content_type", None),
        source_message_id=int(message.id),
        source_channel_id=int(message.channel.id),
        image_attachment_url=str(getattr(target, "url", "") or ""),
    )

    pending = await inventory_service.get_pending_command_session(int(message.author.id))
    if pending:
        await _process_payload_for_governor(
            bot=bot,
            interaction=None,
            governor_id=int(pending["GovernorID"]),
            actor_discord_id=int(message.author.id),
            payload=payload,
            original_message=message,
            batch_id=int(pending["ImportBatchID"]),
            flow_from_pending_command=True,
            flow_type=str(pending.get("FlowType") or InventoryFlowType.COMMAND.value),
        )
        return True

    active_material = await inventory_service.get_active_material_session_for_user(
        int(message.author.id)
    )
    if active_material:
        detected_json = active_material.get("DetectedJson")
        screenshot_count = 1
        if isinstance(detected_json, dict):
            try:
                screenshot_count = int(detected_json.get("screenshot_count") or 1)
            except (TypeError, ValueError):
                screenshot_count = 1
        if screenshot_count >= 4:
            await message.channel.send(
                f"<@{message.author.id}> This pending Materials import already has 4 screenshots. Review, correct, approve, or cancel it before adding more.",
                delete_after=120,
            )
            return True
        await _process_payload_for_governor(
            bot=bot,
            interaction=None,
            governor_id=int(active_material["GovernorID"]),
            actor_discord_id=int(message.author.id),
            payload=payload,
            original_message=message,
            batch_id=int(active_material["ImportBatchID"]),
            flow_from_pending_command=False,
            flow_type=str(active_material.get("FlowType") or InventoryFlowType.UPLOAD_FIRST.value),
            existing_detected_json=detected_json if isinstance(detected_json, dict) else None,
        )
        return True

    governors = await inventory_service.get_registered_governors_for_user(int(message.author.id))
    if not governors:
        await message.channel.send(
            f"<@{message.author.id}> I found an inventory image, but you do not have a registered governor yet. Use `/register_governor` first.",
            delete_after=120,
        )
        return True

    if len(governors) == 1:
        await _process_payload_for_governor(
            bot=bot,
            interaction=None,
            governor_id=governors[0].governor_id,
            actor_discord_id=int(message.author.id),
            payload=payload,
            original_message=message,
            batch_id=None,
            flow_from_pending_command=False,
        )
        return True

    options = build_unique_gov_options(governors)
    ctx = type("_InventoryUploadCtx", (), {"user": message.author})()
    view = InventoryUploadGovernorSelectView(
        ctx=ctx,
        bot=bot,
        options=options,
        actor_discord_id=int(message.author.id),
        payload=payload,
        original_message=message,
    )
    prompt = await message.channel.send(
        f"<@{message.author.id}> Which governor is this inventory image for?",
        view=view,
        delete_after=300,
    )
    view.message = prompt
    return True
