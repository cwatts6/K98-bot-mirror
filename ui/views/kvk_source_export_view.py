"""Disposable export previews; fresh member/config authority on every callback."""

import asyncio

import discord

from core.interaction_safety import safe_defer
from kvk.services.new_source_admin_service import CONFIRM_SECONDS
from ui.views.kvk_source_import_view import current_actor, report_failure, send_receipt


class KvkSourceExportView(discord.ui.View):
    def __init__(self, service, preview):
        super().__init__(timeout=CONFIRM_SECONDS)
        self.service, self.preview = service, preview

    @discord.ui.button(label="Confirm reviewed action", style=discord.ButtonStyle.danger)
    async def confirm_button(self, button, interaction):
        try:
            actor = await current_actor(interaction, self.service.access_factory())
            self.service.authorize(actor, self.preview.action)
            if not await safe_defer(interaction, ephemeral=True):
                return
            row = await asyncio.to_thread(self.service.confirm, actor, self.preview.token)
            await send_receipt(interaction, self.service, row)
            button.disabled = True
            self.stop()
        except Exception as exc:
            await report_failure(interaction, exc)


class SourceExportReasonModal(discord.ui.Modal):
    def __init__(self, service, action, *, kvk_no, index_file_id, job_id, new_kvk):
        super().__init__(title="Review export operation", timeout=CONFIRM_SECONDS)
        self.service, self.action = service, action
        self.kvk_no, self.index_file_id, self.job_id, self.new_kvk = (
            kvk_no,
            index_file_id,
            job_id,
            new_kvk,
        )
        self.reason = discord.ui.InputText(
            label="Audit reason", style=discord.InputTextStyle.long, max_length=1024, required=True
        )
        self.add_item(self.reason)

    async def callback(self, interaction):
        try:
            actor = await current_actor(interaction, self.service.access_factory())
            self.service.authorize(actor, self.action)
            if not await safe_defer(interaction, ephemeral=True):
                return
            if self.action == "rollover_preview":
                row = await asyncio.to_thread(
                    self.service.preview_rollover,
                    actor,
                    self.kvk_no,
                    self.new_kvk,
                    reason=self.reason.value,
                    index_file_id=self.index_file_id,
                )
            else:
                row = await asyncio.to_thread(
                    self.service.preview_rebuild, actor, self.job_id, reason=self.reason.value
                )
            await send_receipt(
                interaction, self.service, row, KvkSourceExportView(self.service, row)
            )
        except Exception as exc:
            await report_failure(interaction, exc)


async def dispatch_export(
    ctx, service, actor, action, *, kvk_no, index_file_id, job_id, new_kvk, review
):
    service.authorize(actor, action)
    interaction = getattr(ctx, "interaction", ctx)
    if action in {"export_rebuild", "rollover_preview"}:
        await interaction.response.send_modal(
            SourceExportReasonModal(
                service,
                action,
                kvk_no=kvk_no,
                index_file_id=index_file_id,
                job_id=job_id,
                new_kvk=new_kvk,
            )
        )
        return
    if not await safe_defer(ctx, ephemeral=True):
        return
    if action == "export":
        row = await asyncio.to_thread(service.export, actor, kvk_no, index_file_id)
    elif action == "export_status":
        row = await asyncio.to_thread(service.status, actor, kvk_no, index_file_id)
    elif action == "export_reconcile":
        row = await asyncio.to_thread(service.reconcile, actor, job_id)
    elif action == "rollover_confirm":
        row = await asyncio.to_thread(service.confirm, actor, review)
    else:
        raise ValueError("Unknown grouped export action.")
    await send_receipt(interaction, service, row)
