from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import logging
from typing import Literal

import discord

from ark.dal.ark_dal import get_match
from ark.state.ark_state import ArkJsonState, ArkMessageRef, ArkMessageState
from core.discord_embed_limits import require_valid_embed_payload

logger = logging.getLogger(__name__)

RegistrationDeliveryOutcome = Literal[
    "created",
    "edited",
    "moved",
    "reposted",
    "recreated",
    "failed",
]
RegistrationDeliveryFailure = Literal[
    "missing_destination",
    "channel_unavailable",
    "edit_failed",
    "send_failed",
]


@dataclass(frozen=True)
class RegistrationDeliveryResult:
    """Observable registration delivery result without changing legacy caller semantics."""

    outcome: RegistrationDeliveryOutcome
    state_changed: bool
    failure_reason: RegistrationDeliveryFailure | None = None

    @property
    def succeeded(self) -> bool:
        return self.outcome != "failed"

    @property
    def legacy_moved_or_reposted(self) -> bool:
        return self.outcome in {"created", "moved", "reposted", "recreated"}

    def as_legacy_tuple(self) -> tuple[bool, bool]:
        return self.legacy_moved_or_reposted, self.state_changed


def _allowed_mentions(announce: bool) -> discord.AllowedMentions:
    return discord.AllowedMentions(everyone=True) if announce else discord.AllowedMentions.none()


async def _send_registration_message(
    *,
    announce: bool,
    channel,
    embed,
    match_id: int,
    view,
):
    try:
        return await channel.send(
            content="@everyone" if announce else None,
            embed=embed,
            view=view,
            allowed_mentions=_allowed_mentions(announce),
        )
    except Exception:
        logger.exception(
            "[ARK_REGISTRATION] delivery_result match_id=%s delivery_outcome=failed "
            "failure_reason=send_failed",
            match_id,
        )
        raise


def _validate_delivery_embed(embed, *, route: str) -> None:
    if embed is None:
        return
    # Non-payload sentinels have no embed contract to measure. Runtime Ark
    # builders always provide Embed/to_dict payloads and are validated here.
    if not isinstance(embed, Mapping) and not callable(getattr(embed, "to_dict", None)):
        return
    usage = require_valid_embed_payload(embed)
    logger.info(
        "ark_payload_delivery route=%s fields=%s chars=%s",
        route,
        usage.field_counts[0],
        usage.total_characters,
    )


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


async def upsert_registration_message_result(
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
) -> RegistrationDeliveryResult:
    """
    Ensure a registration message exists and is updated.

    Returns an explicit delivery outcome while preserving existing send/edit behavior.
    """
    _validate_delivery_embed(embed, route="registration_upsert")
    msg_state = state.messages.get(match_id)
    current_ref = msg_state.registration if msg_state and msg_state.registration else None
    if current_ref is None:
        current_ref = await _resolve_registration_ref_sql(match_id)

    target_id = int(target_channel_id or (current_ref.channel_id if current_ref else 0) or 0)

    if not target_id:
        logger.warning("[ARK] No target registration channel for match %s.", match_id)
        return RegistrationDeliveryResult(
            outcome="failed",
            state_changed=False,
            failure_reason="missing_destination",
        )

    target_channel = client.get_channel(target_id)
    if not target_channel:
        logger.warning("[ARK] Registration channel %s not found.", target_id)
        return RegistrationDeliveryResult(
            outcome="failed",
            state_changed=False,
            failure_reason="channel_unavailable",
        )

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

            new_msg = await _send_registration_message(
                announce=announce,
                channel=target_channel,
                embed=embed,
                match_id=match_id,
                view=view,
            )

            msg_state = state.messages.get(match_id) or ArkMessageState()
            msg_state.registration = ArkMessageRef(
                channel_id=int(new_msg.channel.id), message_id=int(new_msg.id)
            )
            state.messages[match_id] = msg_state
            return RegistrationDeliveryResult(
                outcome="moved" if channel_changed else "reposted",
                state_changed=True,
            )

        try:
            old_msg = await target_channel.fetch_message(int(current_ref.message_id))
            await old_msg.edit(
                content="@everyone" if announce else None,
                embed=embed,
                view=view,
                allowed_mentions=_allowed_mentions(announce),
            )
            return RegistrationDeliveryResult(outcome="edited", state_changed=False)
        except discord.NotFound:
            logger.warning("[ARK] Registration message missing; recreating.")
            new_msg = await _send_registration_message(
                announce=announce,
                channel=target_channel,
                embed=embed,
                match_id=match_id,
                view=view,
            )

            msg_state = state.messages.get(match_id) or ArkMessageState()
            msg_state.registration = ArkMessageRef(
                channel_id=int(new_msg.channel.id), message_id=int(new_msg.id)
            )
            state.messages[match_id] = msg_state
            return RegistrationDeliveryResult(outcome="recreated", state_changed=True)
        except Exception:
            logger.exception("[ARK] Failed to edit registration message.")
            return RegistrationDeliveryResult(
                outcome="failed",
                state_changed=False,
                failure_reason="edit_failed",
            )

    new_msg = await _send_registration_message(
        announce=announce,
        channel=target_channel,
        embed=embed,
        match_id=match_id,
        view=view,
    )

    msg_state = state.messages.get(match_id) or ArkMessageState()
    msg_state.registration = ArkMessageRef(
        channel_id=int(new_msg.channel.id), message_id=int(new_msg.id)
    )
    state.messages[match_id] = msg_state
    return RegistrationDeliveryResult(outcome="created", state_changed=True)


async def upsert_registration_message(
    *,
    announce: bool = False,
    client,
    state: ArkJsonState,
    match_id: int,
    embed,
    view,
    target_channel_id: int | None = None,
    delete_old: bool = True,
    force_repost: bool = False,
) -> tuple[bool, bool]:
    """Compatibility adapter for callers expecting the historical boolean tuple."""
    result = await upsert_registration_message_result(
        announce=announce,
        client=client,
        state=state,
        match_id=match_id,
        embed=embed,
        view=view,
        target_channel_id=target_channel_id,
        delete_old=delete_old,
        force_repost=force_repost,
    )
    return result.as_legacy_tuple()


async def disable_registration_message(
    *,
    client,
    state: ArkJsonState,
    match_id: int,
    embed=None,
) -> bool:
    _validate_delivery_embed(embed, route="registration_disable")
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
    _validate_delivery_embed(embed, route="confirmation_upsert")
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
    _validate_delivery_embed(embed, route="confirmation_disable")
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
