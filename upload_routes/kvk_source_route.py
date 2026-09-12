"""Distinct default-off private source route; recognized input never reaches fallback."""

import asyncio
from dataclasses import dataclass
import logging
import re

from kvk.services.new_source_admin_service import access_from_config, configured_service

logger = logging.getLogger(__name__)
MAX_BYTES = 20 * 1024 * 1024


@dataclass(frozen=True)
class KvkSourceRouteDeps:
    access: object
    service_factory: object = configured_service
    offload: object = asyncio.to_thread


async def handle_kvk_source_upload(message, deps):
    access = deps.access
    if not access.enabled or message.channel.id != access.channel_id:
        return False
    if not message.attachments:
        return False
    import discord

    from ui.views.kvk_source_import_view import KvkSourceImportView, current_actor

    try:
        actor = await current_actor(message, access)
        access.authorize(actor, upload=True)
        if len(message.attachments) != 1:
            raise ValueError("One workbook per confirmation.")
        attachment = message.attachments[0]
        if (
            not attachment.filename.lower().endswith(".xlsx")
            or not 0 < attachment.size <= MAX_BYTES
        ):
            raise ValueError("One bounded XLSX workbook is required.")
        content = await attachment.read()
        if not 0 < len(content) <= MAX_BYTES:
            raise ValueError("Attachment exceeds the supported size.")
        actor = await current_actor(message, access)
        access.authorize(actor, upload=True)
        caption = (getattr(message, "content", "") or "").strip()
        season = int(caption) if re.fullmatch(r"[1-9][0-9]{0,9}", caption) else None
        service = await deps.offload(deps.service_factory)
        row = await deps.offload(
            service.stage_upload,
            actor,
            filename=attachment.filename,
            content=content,
            message_id=message.id,
            attachment_id=attachment.id,
            season=season,
        )
        await message.channel.send(
            service.summary(row),
            view=KvkSourceImportView(service, row),
            allowed_mentions=discord.AllowedMentions.none(),
        )
    except Exception as exc:
        logger.info("KVK source upload rejected message=%s type=%s", message.id, type(exc).__name__)
        await message.channel.send(
            "Source upload was not completed. Use one XLSX file up to 20 MiB in the configured private channel with an authorized role. For filenames without a KVK number, enter the KVK number as the caption. Resume an existing receipt after an uncertain response.",
            allowed_mentions=discord.AllowedMentions.none(),
        )
    return True


async def handle_configured_kvk_source_upload(message):
    return await handle_kvk_source_upload(message, KvkSourceRouteDeps(access_from_config()))
