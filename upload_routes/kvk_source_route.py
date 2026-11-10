"""Distinct default-off private source route; recognized input never reaches fallback."""

import asyncio
from dataclasses import dataclass
import logging

from kvk.services.new_source_admin_service import access_from_config, configured_service
from kvk.services.source_admin_review_service import configured_review_service

logger = logging.getLogger(__name__)
MAX_BYTES = 20 * 1024 * 1024


def configured_recovery_intake():
    from kvk.services.new_source_recovery_service import RecoveryIntakeAdapter

    return RecoveryIntakeAdapter(configured_service())


@dataclass(frozen=True)
class KvkSourceRouteDeps:
    access: object
    service_factory: object = configured_recovery_intake
    offload: object = asyncio.to_thread
    review_factory: object = configured_review_service


async def handle_kvk_source_upload(message, deps):
    access = deps.access
    if not access.enabled or message.channel.id != access.channel_id:
        return False
    if not message.attachments:
        return False
    import discord

    from ui.views.kvk_source_import_view import SourceUploadStartView, current_actor

    try:
        actor = await current_actor(message, access)
        access.authorize(actor, upload=True)
        if not 1 <= len(message.attachments) <= 2 or len(
            {a.id for a in message.attachments}
        ) != len(message.attachments):
            raise ValueError("Upload one or two distinct workbooks.")
        if any(
            not a.filename.lower().endswith(".xlsx") or not 0 < a.size <= MAX_BYTES
            for a in message.attachments
        ):
            raise ValueError("Each attachment must be an XLSX workbook up to 20 MiB.")
        review = await deps.offload(deps.review_factory)
        season = await deps.offload(review.default_season, actor)
        await message.channel.send(
            f"Review season {season or '(select season)'} before intake. Both upload orders are supported. "
            "Missing baseline configuration will block acceptance. Source setup uses /kvk_admin source choose_source.",
            view=SourceUploadStartView(
                access, actor, message.attachments, message.id, deps.service_factory, season
            ),
            allowed_mentions=discord.AllowedMentions.none(),
        )
    except Exception as exc:
        logger.info("KVK source upload rejected message=%s type=%s", message.id, type(exc).__name__)
        await message.channel.send(
            "Source upload review was not started. Use one or two distinct XLSX files up to 20 MiB each in the configured private channel with an authorized role. Check source setup; resume retained receipts after an uncertain response.",
            allowed_mentions=discord.AllowedMentions.none(),
        )
    return True


async def handle_configured_kvk_source_upload(message):
    return await handle_kvk_source_upload(message, KvkSourceRouteDeps(access_from_config()))
