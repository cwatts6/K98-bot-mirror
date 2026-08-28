from __future__ import annotations

import logging

import discord

from ark.dal.ark_dal import get_match
from ark.state.ark_state import ArkJsonState, ArkMessageRef, ArkMessageState

logger = logging.getLogger(__name__)


def _allowed_mentions(announce: bool) -> discord.AllowedMentions:
    return discord.AllowedMentions(everyone=True) if announce else discord.AllowedMentions.none()


async def _resolve_registration_ref_sql(match_id: int) -> ArkMessageRef | None:
    match = await get_match(int(match_id))
    if not match:
        return None
    cid = int(match.get("RegistrationChannelId") or 0)
    mid = int(match.get("RegistrationMessageId") or 0)
    if cid and mid:
        return ArkMessageRef(channel_id=cid, message_id=mid)
    return None


async def _resolve_confirmation_ref_sql(match_id: int) -> ArkMessageRef | None:
    match = await get_match(int(match_id))
    if not match:
        return None
    cid = int(match.get("ConfirmationChannelId") or 0)
    mid = int(match.get("ConfirmationMessageId") or 0)
    if cid and mid:
        return ArkMessageRef(channel_id=cid, message_id=mid)
    return None


async def upsert_registration_message(
    *,
    announce: bool = False,
    client,
    state: ArkJsonState,  # used for in-memory ref reuse and state updates
    match_id: int,
    embed,
    view,
    target_channel_id: int | None = None,
    delete_old: bool = True,
    force_repost: bool = False,
) -> tuple[bool, bool]:
    """
    Ensure a registration message exists and is updated.

    Returns:
        (moved_or_reposted, state_changed)
      - moved_or_reposted=True when a new message is sent/recreated/reposted
      - moved_or_reposted=False when edited in-place
      - state_changed=True if message ref changed
    """
    msg_state = state.messages.get(match_id)
    current_ref = msg_state.registration if msg_state and msg_state.registration else None
    if current_ref is None:
        current_ref = await _resolve_registration_ref_sql(match_id)

    target_id = int(target_channel_id or (current_ref.channel_id if current_ref else 0) or 0)

    if not target_id:
        logger.warning("[ARK] No target registration channel for match %s.", match_id)
        return False, False

    target_channel = client.get_channel(target_id)
    if not target_channel:
        logger.warning("[ARK] Registration channel %s not found.", target_id)
        return False, False

    if current_ref:
        current_channel_id = int(current_ref.channel_id or 0)
        current_message_id = int(current_ref.message_id or 0)
        channel_changed = current_channel_id != target_id
        repost_requested = bool(force_repost)

        if channel_changed or repost_requested:
            should_delete_old = bool(channel_changed or delete_old or repost_requested)

            if should_delete_old and current_message_id:
                try:
                    old_channel = client.get_channel(current_channel_id or target_id)
                    if old_channel:
                        old_msg = await old_channel.fetch_message(current_message_id)
                        await old_msg.delete()
                except Exception:
                    logger.exception("[ARK] Failed to delete old registration message.")

            new_msg = await target_channel.send(
                content="@everyone" if announce else None,
                embed=embed,
                view=view,
                allowed_mentions=_allowed_mentions(announce),
            )

            msg_state = state.messages.get(match_id) or ArkMessageState()
            msg_state.registration = ArkMessageRef(
                channel_id=int(new_msg.channel.id), message_id=int(new_msg.id)
            )
            state.messages[match_id] = msg_state
            return True, True

        try:
            old_msg = await target_channel.fetch_message(int(current_ref.message_id))
            await old_msg.edit(
                content="@everyone" if announce else None,
                embed=embed,
                view=view,
                allowed_mentions=_allowed_mentions(announce),
            )
            return False, False
        except discord.NotFound:
            logger.warning("[ARK] Registration message missing; recreating.")
            new_msg = await target_channel.send(
                content="@everyone" if announce else None,
                embed=embed,
                view=view,
                allowed_mentions=_allowed_mentions(announce),
            )

            msg_state = state.messages.get(match_id) or ArkMessageState()
            msg_state.registration = ArkMessageRef(
                channel_id=int(new_msg.channel.id), message_id=int(new_msg.id)
            )
            state.messages[match_id] = msg_state
            return True, True
        except Exception:
            logger.exception("[ARK] Failed to edit registration message.")
            return False, False

    new_msg = await target_channel.send(
        content="@everyone" if announce else None,
        embed=embed,
        view=view,
        allowed_mentions=_allowed_mentions(announce),
    )

    msg_state = state.messages.get(match_id) or ArkMessageState()
    msg_state.registration = ArkMessageRef(
        channel_id=int(new_msg.channel.id), message_id=int(new_msg.id)
    )
    state.messages[match_id] = msg_state
    return True, True


async def disable_registration_message(
    *,
    client,
    state: ArkJsonState,
    match_id: int,
    embed=None,
) -> bool:
    ref = await _resolve_registration_ref_sql(match_id)
    if not ref:
        logger.warning("[ARK] No SQL registration message ref for match %s.", match_id)
        return False

    try:
        channel = client.get_channel(int(ref.channel_id))
        if not channel:
            logger.warning(
                "[ARK] Registration channel not found match_id=%s channel_id=%s",
                match_id,
                ref.channel_id,
            )
            return False

        msg = await channel.fetch_message(int(ref.message_id))
        await msg.edit(embed=embed, view=None)
        return True
    except discord.NotFound:
        logger.warning(
            "[ARK] Registration message not found match_id=%s message_id=%s",
            match_id,
            ref.message_id,
        )
        return False
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
        (delivered, state_changed)
      - delivered=True if message was edited/sent/recreated
      - state_changed=True if message ref changed
    """
    msg_state = state.messages.get(match_id)
    current_ref = msg_state.confirmation if msg_state and msg_state.confirmation else None
    if current_ref is None:
        current_ref = await _resolve_confirmation_ref_sql(match_id)

    target_id = int(target_channel_id or (current_ref.channel_id if current_ref else 0) or 0)

    if not target_id:
        logger.warning("[ARK] No target confirmation channel for match %s.", match_id)
        return False, False

    target_channel = client.get_channel(target_id)
    if not target_channel:
        logger.warning("[ARK] Confirmation channel %s not found.", target_id)
        return False, False

    if current_ref:
        if int(current_ref.channel_id) != int(target_id):
            if delete_old:
                try:
                    old_channel = client.get_channel(int(current_ref.channel_id))
                    if old_channel:
                        old_msg = await old_channel.fetch_message(int(current_ref.message_id))
                        await old_msg.delete()
                except Exception:
                    logger.exception("[ARK] Failed to delete old confirmation message.")

            new_msg = await target_channel.send(embed=embed, view=view)

            msg_state = state.messages.get(match_id) or ArkMessageState()
            msg_state.confirmation = ArkMessageRef(
                channel_id=int(new_msg.channel.id), message_id=int(new_msg.id)
            )
            state.messages[match_id] = msg_state
            return True, True

        try:
            old_msg = await target_channel.fetch_message(int(current_ref.message_id))
            await old_msg.edit(embed=embed, view=view)
            return True, False
        except (discord.NotFound, discord.HTTPException):
            logger.warning("[ARK] Confirmation message missing; recreating.")
            new_msg = await target_channel.send(embed=embed, view=view)

            msg_state = state.messages.get(match_id) or ArkMessageState()
            msg_state.confirmation = ArkMessageRef(
                channel_id=int(new_msg.channel.id), message_id=int(new_msg.id)
            )
            state.messages[match_id] = msg_state
            return True, True
        except Exception:
            logger.exception("[ARK] Failed to edit confirmation message.")
            return False, False

    new_msg = await target_channel.send(embed=embed, view=view)

    msg_state = state.messages.get(match_id) or ArkMessageState()
    msg_state.confirmation = ArkMessageRef(
        channel_id=int(new_msg.channel.id), message_id=int(new_msg.id)
    )
    state.messages[match_id] = msg_state
    return True, True


async def disable_confirmation_message(
    *,
    client,
    state: ArkJsonState,
    match_id: int,
    embed=None,
) -> bool:
    ref = await _resolve_confirmation_ref_sql(match_id)
    if not ref:
        logger.warning("[ARK] No SQL confirmation message ref for match %s.", match_id)
        return False

    try:
        channel = client.get_channel(int(ref.channel_id))
        if not channel:
            logger.warning(
                "[ARK] Confirmation channel not found match_id=%s channel_id=%s",
                match_id,
                ref.channel_id,
            )
            return False

        msg = await channel.fetch_message(int(ref.message_id))
        await msg.edit(embed=embed, view=None)
        return True
    except discord.NotFound:
        logger.warning(
            "[ARK] Confirmation message not found match_id=%s message_id=%s",
            match_id,
            ref.message_id,
        )
        return False
    except Exception:
        logger.exception("[ARK] Failed to disable confirmation message.")
        return False
