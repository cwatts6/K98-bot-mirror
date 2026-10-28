"""Discord response sequencing for evidence-qualified MGE actions."""

import asyncio
import logging

from core.interaction_safety import send_ephemeral_result as send_ephemeral
from core.operation_outcome import MutationOutcome
from mge.mge_action_result import ActionDisposition, ActionEvidence
from mge.mge_refresh_work import registration_scope

logger = logging.getLogger(__name__)


def action_evidence(result):
    evidence = getattr(result, "action", None)
    if evidence is not None:
        return evidence
    # Signup's transaction result is an explicit settlement contract, not a Boolean.
    outcomes = {
        MutationOutcome.COMMITTED: ActionDisposition.COMPLETED,
        MutationOutcome.NOT_ENTERED: ActionDisposition.NOT_ENTERED,
        MutationOutcome.ROLLED_BACK: ActionDisposition.ROLLED_BACK,
        MutationOutcome.UNKNOWN: ActionDisposition.UNKNOWN,
    }
    return ActionEvidence(outcomes.get(getattr(result, "outcome", None), ActionDisposition.UNKNOWN))


async def reply_with_refresh(
    interaction,
    result,
    *,
    event_id,
    register_refresh=None,
    refresh_public=True,
    refresh_leadership=True,
    refresh_awards=False,
):
    evidence = action_evidence(result)
    gate = asyncio.Event()
    registered = False
    handle = None
    try:
        if evidence.refresh_eligible:
            try:
                with registration_scope(gate, evidence.read_only_refresh):
                    if register_refresh is not None:
                        handle = register_refresh(int(event_id))
                    elif refresh_public or refresh_leadership or refresh_awards:
                        from mge.mge_embed_manager import request_board_refresh

                        handle = request_board_refresh(
                            bot=interaction.client,
                            event_id=event_id,
                            refresh_public=refresh_public,
                            refresh_leadership=refresh_leadership,
                            refresh_awards=refresh_awards,
                        )
                registered = bool(getattr(handle, "registered", False))
            except Exception as exc:
                logger.warning(
                    "mge_action_refresh_registration_failed event_id=%s error_type=%s",
                    event_id,
                    type(exc).__name__,
                )
        text = evidence.message(result.message)
        if evidence.disposition == ActionDisposition.COMPLETED:
            if (
                register_refresh is not None
                or refresh_public
                or refresh_leadership
                or refresh_awards
            ):
                text += (
                    " Board refresh is pending."
                    if registered
                    else " The board refresh could not be fully scheduled; leadership can refresh the board."
                )
            text = "✅ " + text
        elif evidence.disposition in {ActionDisposition.NOT_ENTERED, ActionDisposition.ROLLED_BACK}:
            text = "❌ " + text
        delivered = await send_ephemeral(interaction, text)
        logger.info(
            "mge_action_reply event_id=%s disposition=%s refresh_registered=%s reply_confirmed=%s",
            event_id,
            evidence.disposition,
            registered,
            delivered is True,
        )
        return evidence
    finally:
        # A response transport failure or cancellation cannot strand the saved action's refresh.
        gate.set()


def refresh_message(result, name="Board"):
    status = getattr(result, "status", "delivered" if result is True else "failed")
    if status == "delivered":
        return f"✅ {name} refreshed."
    if status == "pending":
        return f"{name} refresh is still running."
    return f"{name} could not be refreshed. Its saved identity has been retained."
