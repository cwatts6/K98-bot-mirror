from __future__ import annotations

import logging

import discord

from ark.state.ark_state import ArkJsonState, ArkMessageRef, ArkMessageState

logger = logging.getLogger(__name__)


async def upsert_registration_message(
    *,
    client,
    state: ArkJsonState,
    match_id: int,
    embed,
    view,
    target_channel_id: int | None = None,
    delete_old: bool = True,
) -> tuple[bool, bool]:
    """
    Ensure a registration message exists and is updated.

    Returns:
        (moved, state_changed)
    """
    msg_state = state.messages.get(match_id)
    current_ref = msg_state.registration if msg_state else None
    target_id = int(target_channel_id or (current_ref.channel_id if current_ref else 0) or 0)

    if not target_id:
        logger.warning("[ARK] No target registration channel for match %s.", match_id)
        return False, False

    target_channel = client.get_channel(target_id)
    if not target_channel:
        logger.warning("[ARK] Registration channel %s not found.", target_id)
        return False, False

    if current_ref:
        if current_ref.channel_id != target_id:
            if delete_old:
                try:
                    old_channel = client.get_channel(current_ref.channel_id)
                    if old_channel:
                        old_msg = await old_channel.fetch_message(current_ref.message_id)
                        await old_msg.delete()
                except Exception:
                    logger.exception("[ARK] Failed to delete old registration message.")
            new_msg = await target_channel.send(embed=embed, view=view)
            msg_state.registration = ArkMessageRef(
                channel_id=new_msg.channel.id, message_id=new_msg.id
            )
            return True, True

        try:
            old_msg = await target_channel.fetch_message(current_ref.message_id)
            await old_msg.edit(embed=embed, view=view)
        except Exception:
            logger.exception("[ARK] Failed to edit registration message.")
        return False, False

    new_msg = await target_channel.send(embed=embed, view=view)
    state.messages[match_id] = ArkMessageState(
        registration=ArkMessageRef(channel_id=new_msg.channel.id, message_id=new_msg.id)
    )
    return True, True


async def disable_registration_message(
    *,
    client,
    state: ArkJsonState,
    match_id: int,
    embed=None,
) -> bool:
    msg_state = state.messages.get(match_id)
    if not msg_state or not msg_state.registration:
        logger.warning("[ARK] No registration message state for match %s.", match_id)
        return False
    try:
        channel = client.get_channel(msg_state.registration.channel_id)
        if not channel:
            return False
        msg = await channel.fetch_message(msg_state.registration.message_id)
        await msg.edit(embed=embed, view=None)
        return True
    except Exception:
        logger.exception("[ARK] Failed to disable registration message.")
        return False


async def upsert_confirmation_message(
    *,
    client,
    state: ArkJsonState,
    match_id: int,
    embed,
    view,
    target_channel_id: int | None = None,
    delete_old: bool = True,
) -> tuple[bool, bool]:
    """
    Ensure a confirmation message exists and is updated.

    Returns:
        (moved, state_changed)
    """
    msg_state = state.messages.get(match_id)
    current_ref = msg_state.confirmation if msg_state else None
    target_id = int(target_channel_id or (current_ref.channel_id if current_ref else 0) or 0)

    if not target_id:
        logger.warning("[ARK] No target confirmation channel for match %s.", match_id)
        return False, False

    target_channel = client.get_channel(target_id)
    if not target_channel:
        logger.warning("[ARK] Confirmation channel %s not found.", target_id)
        return False, False

    if current_ref:
        if current_ref.channel_id != target_id:
            if delete_old:
                try:
                    old_channel = client.get_channel(current_ref.channel_id)
                    if old_channel:
                        old_msg = await old_channel.fetch_message(current_ref.message_id)
                        await old_msg.delete()
                except Exception:
                    logger.exception("[ARK] Failed to delete old confirmation message.")
            new_msg = await target_channel.send(embed=embed, view=view)
            msg_state.confirmation = ArkMessageRef(
                channel_id=new_msg.channel.id, message_id=new_msg.id
            )
            return True, True

        try:
            old_msg = await target_channel.fetch_message(current_ref.message_id)
            await old_msg.edit(embed=embed, view=view)
        except (discord.NotFound, discord.HTTPException):
            logger.warning("[ARK] Confirmation message missing; recreating.")
            new_msg = await target_channel.send(embed=embed, view=view)
            msg_state.confirmation = ArkMessageRef(
                channel_id=new_msg.channel.id, message_id=new_msg.id
            )
            return True, True
        except Exception:
            logger.exception("[ARK] Failed to edit confirmation message.")
        return False, False

    new_msg = await target_channel.send(embed=embed, view=view)
    if msg_state:
        msg_state.confirmation = ArkMessageRef(channel_id=new_msg.channel.id, message_id=new_msg.id)
    else:
        state.messages[match_id] = ArkMessageState(
            confirmation=ArkMessageRef(channel_id=new_msg.channel.id, message_id=new_msg.id)
        )
    return True, True


async def disable_confirmation_message(
    *,
    client,
    state: ArkJsonState,
    match_id: int,
    embed=None,
) -> bool:
    msg_state = state.messages.get(match_id)
    if not msg_state or not msg_state.confirmation:
        logger.warning("[ARK] No confirmation message state for match %s.", match_id)
        return False
    try:
        channel = client.get_channel(msg_state.confirmation.channel_id)
        if not channel:
            return False
        msg = await channel.fetch_message(msg_state.confirmation.message_id)
        await msg.edit(embed=embed, view=None)
        return True
    except Exception:
        logger.exception("[ARK] Failed to disable confirmation message.")
        return False
