"""DM-based follow-up flow for optional MGE signup attachments."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import logging
from typing import Any

import discord

from mge.dal import mge_signup_dal

logger = logging.getLogger(__name__)

_ATTACHMENT_KIND_GEAR = "gear"
_ATTACHMENT_KIND_ARMAMENT = "armament"
_ALLOWED_IMAGE_PREFIX = "image/"


@dataclass(slots=True)
class AttachmentSaveResult:
    success: bool
    message: str


@dataclass(slots=True)
class DmAttachmentSession:
    signup_id: int
    event_id: int
    actor_discord_id: int
    view: discord.ui.View


# Active DM sessions keyed by actor Discord user id.
_DM_SESSIONS: dict[int, DmAttachmentSession] = {}


def _now_utc(now_utc: datetime | None = None) -> datetime:
    if now_utc is None:
        return datetime.now(UTC)
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=UTC)
    return now_utc.astimezone(UTC)


def build_dm_intro_text(event_name: str) -> str:
    """Build DM intro text for optional attachment follow-up."""
    return (
        f"Thanks for your MGE signup update for **{event_name}**.\n\n"
        "You can optionally upload:\n"
        "1) Gear screenshot\n"
        "2) Armament screenshot\n\n"
        "Use the buttons below to choose what you are uploading."
    )


def register_dm_session(
    *,
    actor_discord_id: int,
    signup_id: int,
    event_id: int,
    view: discord.ui.View,
) -> None:
    _DM_SESSIONS[int(actor_discord_id)] = DmAttachmentSession(
        signup_id=int(signup_id),
        event_id=int(event_id),
        actor_discord_id=int(actor_discord_id),
        view=view,
    )


def clear_dm_session(actor_discord_id: int) -> None:
    _DM_SESSIONS.pop(int(actor_discord_id), None)


async def route_dm_message(message: discord.Message) -> bool:
    """
    Route DM message attachments to active MGE DM session.
    Returns True if handled.
    """
    if message.author.bot:
        return False
    if message.guild is not None:
        return False

    # Do not intercept normal DM chat/commands
    if not message.attachments:
        return False

    session = _DM_SESSIONS.get(int(message.author.id))
    if not session:
        return False

    handler = getattr(session.view, "handle_dm_message", None)
    if handler is None:
        return False

    try:
        response_text = await handler(message)
        await message.channel.send(response_text)
        return True
    except Exception:
        logger.exception(
            "mge_dm_followup_route_failed actor_discord_id=%s signup_id=%s event_id=%s",
            message.author.id,
            session.signup_id,
            session.event_id,
        )
        await message.channel.send("❌ Failed to process attachment. Please try again.")
        return True


async def open_dm_followup(
    *,
    user: discord.abc.User,
    event_id: int,
    signup_id: int,
    event_name: str,
) -> tuple[bool, str]:
    """
    Open a DM follow-up session with attachment buttons.
    Returns (success, message) where message is user-facing.
    """
    try:
        dm = user.dm_channel or await user.create_dm()
        from ui.views.mge_dm_attachment_view import MgeDmAttachmentView

        view = MgeDmAttachmentView(
            signup_id=signup_id,
            event_id=event_id,
            actor_discord_id=int(user.id),
        )
        await dm.send(content=build_dm_intro_text(event_name), view=view)
        register_dm_session(
            actor_discord_id=int(user.id),
            signup_id=signup_id,
            event_id=event_id,
            view=view,
        )
        logger.info(
            "mge_dm_followup_opened event_id=%s signup_id=%s actor_discord_id=%s",
            event_id,
            signup_id,
            user.id,
        )
        return True, "I sent you a DM for optional gear/armament attachments."
    except Exception:
        logger.exception(
            "mge_dm_followup_open_failed event_id=%s signup_id=%s actor_discord_id=%s",
            event_id,
            signup_id,
            user.id,
        )
        return (
            False,
            "I couldn't DM you. Please enable DMs from server members and try again later.",
        )


def _pick_first_image_attachment(
    attachments: list[discord.Attachment],
) -> discord.Attachment | None:
    for item in attachments:
        ctype = (item.content_type or "").lower()
        if ctype.startswith(_ALLOWED_IMAGE_PREFIX):
            return item
        filename = (item.filename or "").lower()
        if filename.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
            return item
    return None


def _attachment_audit_details(
    *,
    kind: str,
    attachment: discord.Attachment,
) -> dict[str, Any]:
    return {
        "action": f"attachment_update_{kind}",
        "kind": kind,
        "discord_url": str(attachment.url),
        "filename": str(attachment.filename),
        "content_type": attachment.content_type,
        "size": int(attachment.size) if attachment.size is not None else None,
    }


def save_attachment_for_signup(
    *,
    signup_id: int,
    event_id: int,
    governor_id: int,
    actor_discord_id: int,
    kind: str,
    attachment: discord.Attachment,
    now_utc: datetime | None = None,
) -> AttachmentSaveResult:
    """
    Persist one attachment (latest-upload-wins) for signup.
    Kind must be 'gear' or 'armament'.
    """
    now = _now_utc(now_utc)
    url = str(attachment.url)
    filename = str(attachment.filename or "")

    if kind == _ATTACHMENT_KIND_GEAR:
        ok = mge_signup_dal.update_signup_gear_attachment(
            signup_id=signup_id,
            gear_attachment_url=url,
            gear_attachment_filename=filename,
            now_utc=now,
        )
    elif kind == _ATTACHMENT_KIND_ARMAMENT:
        ok = mge_signup_dal.update_signup_armament_attachment(
            signup_id=signup_id,
            armament_attachment_url=url,
            armament_attachment_filename=filename,
            now_utc=now,
        )
    else:
        return AttachmentSaveResult(False, "Unsupported attachment kind.")

    if not ok:
        return AttachmentSaveResult(False, "Failed to save attachment. Please try again.")

    details = _attachment_audit_details(kind=kind, attachment=attachment)
    mge_signup_dal.insert_signup_audit(
        signup_id=signup_id,
        event_id=event_id,
        governor_id=governor_id,
        action_type="edit",
        actor_discord_id=actor_discord_id,
        details=details,
        now_utc=now,
    )
    return AttachmentSaveResult(True, f"{kind.title()} attachment saved.")


def validate_and_get_image(attachments: list[discord.Attachment]) -> discord.Attachment | None:
    """Return first valid image attachment from a message attachment list."""
    return _pick_first_image_attachment(attachments)
