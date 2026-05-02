from __future__ import annotations

import io
import json
import logging
from typing import Any

import discord

from account_picker import AccountPickerView, build_unique_gov_options
from bot_config import INVENTORY_ADMIN_DEBUG_CHANNEL_ID
from decoraters import _is_admin
from inventory import inventory_service
from inventory.models import (
    InventoryAnalysisSummary,
    InventoryImagePayload,
    InventoryImportType,
    RegisteredGovernor,
)
from inventory.parsing import (
    apply_resource_total_corrections,
    apply_speedup_duration_corrections,
    format_resource_value,
    format_speedup_duration,
)

logger = logging.getLogger(__name__)

SCREENSHOT_GUIDELINES = (
    "Upload a full screenshot.\n"
    "Do not crop the image.\n"
    "Make sure all rows and values are visible.\n"
    "Use English game language if possible.\n"
    "Do not upload edited or compressed screenshots."
)


def _governors_to_accounts(governors: list[RegisteredGovernor]) -> dict[str, dict[str, Any]]:
    return {
        item.account_type: {
            "GovernorID": item.governor_id,
            "GovernorName": item.governor_name,
        }
        for item in governors
    }


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
    return "No Phase 1A values detected."


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
    if interaction.response.is_done():
        await interaction.followup.send(content, ephemeral=True, **kwargs)
    else:
        await interaction.response.send_message(content, ephemeral=True, **kwargs)


async def _send_followup_capture_message(interaction: discord.Interaction, **kwargs: Any) -> Any:
    try:
        return await interaction.followup.send(wait=True, **kwargs)
    except TypeError:
        return await interaction.followup.send(**kwargs)


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
    ) -> None:
        super().__init__(timeout=900)
        self.bot = bot
        self.actor_discord_id = int(actor_discord_id)
        self.governor_id = int(governor_id)
        self.batch_id = int(batch_id)
        self.payload = payload
        self.summary = summary
        self.corrected_values: dict[str, Any] | None = None
        self._terminal = False
        self.message: discord.Message | None = None

        if summary.import_type in {InventoryImportType.MATERIALS, InventoryImportType.UNKNOWN}:
            for child in self.children:
                if getattr(child, "custom_id", "") == "inventory_import_approve":
                    child.disabled = True

    async def _deny_if_not_actor(self, interaction: discord.Interaction) -> bool:
        if self._terminal:
            await _send_private(interaction, "This import has already been completed.")
            return True
        if int(interaction.user.id) == self.actor_discord_id:
            return False
        await _send_private(
            interaction, "Only the user who started this import can use these buttons."
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
            normalized = await inventory_service.approve_import(
                import_batch_id=self.batch_id,
                governor_id=self.governor_id,
                summary=self.summary,
                final_values=final_values,
                corrected_values=self.corrected_values,
                is_admin=_is_admin(interaction.user),
            )
        except ValueError as exc:
            await interaction.followup.send(str(exc), ephemeral=True)
            return
        except Exception:
            logger.exception("inventory_import_approve_failed batch_id=%s", self.batch_id)
            await interaction.followup.send(
                f"Approval failed due to an internal error. Please try again or contact an admin with batch ID {self.batch_id}.",
                ephemeral=True,
            )
            return
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
            except Exception:
                logger.exception("inventory_approve_debug_post_failed batch_id=%s", self.batch_id)
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
        await interaction.response.send_message(
            "Corrections are only available for Resources and Speedups in Phase 1.",
            ephemeral=True,
        )

    @discord.ui.button(
        label="Reject Import",
        style=discord.ButtonStyle.danger,
        custom_id="inventory_import_reject",
    )
    async def reject(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        if await self._deny_if_not_actor(interaction):
            return
        self.message = getattr(interaction, "message", None)
        await interaction.response.defer(ephemeral=True)
        try:
            await inventory_service.reject_import(self.batch_id, error="Rejected by user.")
        except Exception:
            logger.exception("inventory_import_reject_failed batch_id=%s", self.batch_id)
            await interaction.followup.send(
                f"Rejection failed due to an internal error. Please try again or contact an admin with batch ID {self.batch_id}.",
                ephemeral=True,
            )
            return
        self._terminal = True
        self.disable_all_items()
        self.stop()
        try:
            await _post_admin_debug(
                bot=self.bot,
                batch_id=self.batch_id,
                governor_id=self.governor_id,
                discord_user_id=self.actor_discord_id,
                status="rejected",
                payload=self.payload,
                summary=self.summary,
                error_json={"error": "Rejected by user."},
            )
        except Exception:
            logger.exception("inventory_reject_debug_post_failed batch_id=%s", self.batch_id)
        await interaction.followup.send(
            "Import rejected. You can upload one replacement screenshot if needed.\n\n"
            + SCREENSHOT_GUIDELINES,
            ephemeral=True,
        )
        await self._update_review_message(interaction, content="Inventory import rejected.")

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
        await interaction.followup.send("Import cancelled.", ephemeral=True)
        await self._update_review_message(interaction, content="Inventory import cancelled.")

    async def on_timeout(self) -> None:
        if not self._terminal:
            try:
                await inventory_service.cancel_import(self.batch_id)
            except Exception:
                logger.debug(
                    "inventory_confirmation_timeout_cancel_failed batch_id=%s",
                    self.batch_id,
                    exc_info=True,
                )
        self.disable_all_items()
        message = getattr(self, "message", None)
        if message is not None:
            try:
                await message.edit(view=self)
            except Exception:
                logger.debug("inventory_timeout_message_edit_failed", exc_info=True)


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
                value=str(int(value)) if value is not None else "",
                required=True,
            )
            self.inputs[key] = field
            self.add_item(field)

    async def callback(self, interaction: discord.Interaction) -> None:
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
            value = row.get("total_minutes")
            field = discord.ui.InputText(
                label=f"{key.title()} Speedup Days",
                value=format_speedup_duration(value) if value is not None else "",
                required=True,
            )
            self.inputs[key] = field
            self.add_item(field)

    async def callback(self, interaction: discord.Interaction) -> None:
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
) -> None:
    if original_message is None:
        return
    try:
        await original_message.delete()
        if batch_id is not None:
            await inventory_service.mark_original_upload_deleted(batch_id)
    except Exception:
        logger.debug("inventory_original_upload_delete_failed", exc_info=True)


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
) -> None:
    if interaction is not None:
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

    try:
        if batch_id is None:
            batch_id = await inventory_service.create_upload_first_batch(
                governor_id=governor_id,
                discord_user_id=actor_discord_id,
                payload=payload,
                is_admin=_is_admin(getattr(interaction, "user", None)) if interaction else False,
            )
        await _delete_original_upload(original_message=original_message, batch_id=batch_id)
        summary = await inventory_service.analyse_inventory_image(
            import_batch_id=batch_id,
            payload=payload,
        )
        if (
            not summary.ok
            or summary.confidence_score < 0.70
            or summary.import_type == InventoryImportType.UNKNOWN
        ):
            await inventory_service.fail_import(batch_id, error=summary.error or "Analysis failed.")
            await _post_admin_debug(
                bot=bot,
                batch_id=batch_id,
                governor_id=governor_id,
                discord_user_id=actor_discord_id,
                status="failed",
                payload=payload,
                summary=summary,
                error_json={"error": summary.error or "Analysis failed."},
            )
            message = (
                "I could not read this inventory screenshot clearly enough. No values were saved.\n\n"
                + SCREENSHOT_GUIDELINES
            )
            if interaction is not None:
                await interaction.followup.send(message, ephemeral=True)
            elif original_message is not None:
                await original_message.channel.send(
                    f"<@{actor_discord_id}> {message}", delete_after=120
                )
            return

        embed = _analysis_embed(governor_id=governor_id, summary=summary)
        if summary.import_type == InventoryImportType.MATERIALS:
            await inventory_service.reject_import(batch_id, error="Materials disabled in Phase 1.")
            await _post_admin_debug(
                bot=bot,
                batch_id=batch_id,
                governor_id=governor_id,
                discord_user_id=actor_discord_id,
                status="materials_disabled",
                payload=payload,
                summary=summary,
                error_json={"error": "Materials disabled in Phase 1."},
            )
            content = "Materials import is not available yet. No values were saved."
            if interaction is not None:
                await interaction.followup.send(content, embed=embed, ephemeral=True)
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
        )
        content = "Review the detected inventory values before approving."
        if flow_from_pending_command:
            content = "Screenshot received. Review the detected inventory values before approving."
        if interaction is not None:
            sent = await _send_followup_capture_message(
                interaction,
                content=content,
                embed=embed,
                view=view,
                ephemeral=True,
            )
            view.message = sent
        elif original_message is not None:
            sent = await original_message.channel.send(
                f"<@{actor_discord_id}> {content}",
                embed=embed,
                view=view,
                delete_after=900,
            )
            view.message = sent
    except Exception:
        logger.exception("inventory_process_payload_failed governor_id=%s", governor_id)
        if interaction is not None:
            await interaction.followup.send(
                "Inventory import failed due to an internal error. Please try again or contact an admin.",
                ephemeral=True,
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
                "Upload one resources or speedups screenshot in this channel within 10 minutes."
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

    options = build_unique_gov_options(_governors_to_accounts(governors))

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
                "Upload one resources or speedups screenshot in this channel within 10 minutes."
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

    options = build_unique_gov_options(_governors_to_accounts(governors))
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
