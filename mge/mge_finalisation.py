"""Discord adapter for immutable final payloads on original MGE messages.

Uses the existing presentation owner and owned-work drain. No sends, replacement
identities, business replay, generic scheduler or age-based receipt expiry.
"""

from datetime import UTC
import json
import logging

import discord

from core.board_lifecycle import BoardLifecycle, BoardWork
from core.owned_work import drain_thread
from mge.dal import mge_completion_dal, mge_finalisation_dal as dal
from mge.mge_board_ownership import presentation_owner
from mge.mge_board_preparation import BOARD_FIELDS, validate_event, validate_payload, validate_rows

logger = logging.getLogger(__name__)


async def _prepare(event, kind):
    from mge import mge_embed_manager as manager
    from mge.dal.mge_publish_dal import fetch_awards_with_signup_user

    validate_event(event, event["EventId"])
    stamp = event["UpdatedUtc"]
    stamp = stamp.replace(tzinfo=UTC) if stamp.tzinfo is None else stamp.astimezone(UTC)
    if kind == "signup":
        names = await drain_thread(
            manager.public_names, event["EventId"], simplified=manager.MGE_SIMPLIFIED_FLOW_ENABLED
        )
        embed = manager.build_mge_signup_embed(
            event, public_signup_names=names, lifecycle_state="finished"
        )
    elif kind == "leadership":
        payload = await drain_thread(
            manager.get_leadership_board_payload, event["EventId"], allow_placement=False
        )
        embed = manager.build_mge_leadership_embed(event_row=event, board_payload=payload)
        embed.description = "Final MGE roster. This historical board is frozen."
    else:
        rows = await drain_thread(fetch_awards_with_signup_user, event["EventId"], strict=True)
        validate_rows(rows, event["EventId"], awards=True)
        embed = manager.build_mge_awards_embed(
            event_row=event,
            awarded_rows=[r for r in rows if r["AwardStatus"] == "awarded"],
            waitlist_rows=[r for r in rows if r["AwardStatus"] == "waitlist"],
            publish_version=event["PublishVersion"],
            published_utc=stamp,
        )
    # Captured once before any IO. Restart reuses these exact bytes, including time.
    embed.timestamp = stamp
    payload = embed.to_dict()
    validate_payload(payload)
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _matches(message, payload):
    """Compare only authored embed keys (Discord adds image proxy metadata)."""

    def contains(actual, expected):
        if isinstance(expected, dict):
            return isinstance(actual, dict) and all(
                k in actual and contains(actual[k], v) for k, v in expected.items()
            )
        if isinstance(expected, list):
            return (
                isinstance(actual, list)
                and len(actual) == len(expected)
                and all(contains(a, b) for a, b in zip(actual, expected, strict=True))
            )
        return actual == expected

    return (
        len(message.embeds) == 1
        and not message.components
        and contains(message.embeds[0].to_dict(), payload)
    )


async def deliver_target(bot, event, target):
    """Called under the event presentation owner. Unknown edits are read back only."""
    work = BoardLifecycle(True, target["DeliveryState"]).work()
    if work == BoardWork.NONE:
        return target["DeliveryState"] == "confirmed"
    channel_field, message_field = BOARD_FIELDS[target["BoardKind"]]
    if (
        event["Status"] != "completed"
        or event["PublishVersion"] != target["PublishVersion"]
        or event[channel_field] != target["ChannelId"]
        or event[message_field] != target["MessageId"]
    ):
        await drain_thread(dal.transition, target, "held", reason="identity_conflict")
        return False
    try:
        payload_json = target["PayloadJson"]
        if not payload_json:
            if work == BoardWork.RECONCILE:
                await drain_thread(dal.transition, target, "held", reason="missing_payload")
                return False
            payload_json = await _prepare(event, target["BoardKind"])
            if not await drain_thread(dal.transition, target, "pending", payload=payload_json):
                return False
            target = next(
                t
                for t in await drain_thread(dal.targets, event["EventId"])
                if t["BoardKind"] == target["BoardKind"]
            )
        payload = json.loads(payload_json)
        channel = bot.get_channel(target["ChannelId"]) or await bot.fetch_channel(
            target["ChannelId"]
        )
        logger.info(
            "mge_final_board_fetch event_id=%s kind=%s", event["EventId"], target["BoardKind"]
        )
        message = await channel.fetch_message(target["MessageId"])
    except discord.NotFound:
        await drain_thread(dal.transition, target, "held", reason="confirmed_missing")
        return False
    except discord.Forbidden:
        await drain_thread(dal.transition, target, "held", reason="inaccessible")
        return False
    except Exception as exc:
        # A fetch/preparation failure never means that a message was deleted.
        if work != BoardWork.RECONCILE:
            await drain_thread(dal.transition, target, "failed", reason="prepare_or_fetch_failed")
        logger.warning(
            "mge_final_board_read_failed event_id=%s error_type=%s",
            event["EventId"],
            type(exc).__name__,
        )
        return False
    if work == BoardWork.RECONCILE:
        matched = _matches(message, payload)
        return (
            await drain_thread(
                dal.transition,
                target,
                "confirmed" if matched else "held",
                reason="readback_match" if matched else "unknown_edit_mismatch",
            )
            and matched
        )
    # Durable intent precedes IO; an uncertain intent commit never authorizes IO.
    if not await drain_thread(dal.transition, target, "unknown", reason="edit_entered"):
        return False
    target = next(
        t
        for t in await drain_thread(dal.targets, event["EventId"])
        if t["BoardKind"] == target["BoardKind"]
    )
    if target["DeliveryState"] != "unknown":
        return False
    try:
        logger.info(
            "mge_final_board_edit event_id=%s kind=%s", event["EventId"], target["BoardKind"]
        )
        await message.edit(
            embed=discord.Embed.from_dict(payload),
            view=None,
            allowed_mentions=discord.AllowedMentions.none(),
        )
    except discord.NotFound:
        await drain_thread(dal.transition, target, "held", reason="confirmed_missing")
        return False
    except Exception as exc:
        logger.warning(
            "mge_final_board_edit_unknown event_id=%s error_type=%s",
            event["EventId"],
            type(exc).__name__,
        )
        return False
    return await drain_thread(dal.transition, target, "confirmed", reason="edit_acknowledged")


async def finalise_event(bot, event_id, *, actor_id=None, complete=False):
    from mge.dal.mge_event_dal import fetch_event_for_embed
    from mge.mge_completion_service import complete_event
    from mge.mge_embed_manager import _refreshes

    async def owned():
        async with presentation_owner(bot, event_id):
            if complete:
                result = await drain_thread(
                    complete_event,
                    event_id,
                    actor_discord_id=actor_id,
                    source="admin_view" if actor_id is not None else "scheduler",
                )
                if not result.get("ok"):
                    return {"domain_completed": False, "states": {}}
            event = await drain_thread(fetch_event_for_embed, event_id, strict=True)
            if event["Status"] != "completed":
                return {"domain_completed": False, "states": {}}
            for target in await drain_thread(dal.targets, event_id):
                await deliver_target(bot, event, target)
            states = {
                t["BoardKind"]: t["DeliveryState"]
                for t in await drain_thread(dal.targets, event_id)
            }
            return {"domain_completed": True, "states": states}

    return await _refreshes.run_direct(owned)


async def sweep(bot, now):
    async def attempt(event_id, *, complete=False):
        try:
            await finalise_event(bot, event_id, complete=complete)
        except Exception as exc:
            logger.warning(
                "mge_finalisation_event_held event_id=%s error_type=%s",
                event_id,
                type(exc).__name__,
            )

    due = await drain_thread(mge_completion_dal.fetch_due_event_ids_for_completion, now)
    for event_id in due:
        await attempt(event_id, complete=True)
    cursor = 0
    while True:
        rows = await drain_thread(dal.pending_events, cursor)
        for row in rows:
            await attempt(row["EventId"])
        if len(rows) < 50:
            break
        cursor = rows[-1]["EventId"]
    logger.info(
        "mge_finalisation_counts due=%s events=%s targets=%s",
        len(due),
        await drain_thread(dal.event_counts),
        await drain_thread(dal.counts),
    )


async def retirement_preview(event_id):
    return [
        t
        for t in await drain_thread(dal.targets, event_id)
        if t["DeliveryState"] in {"pending", "failed", "held"}
    ]


async def retire_targets(bot, event_id, targets, actor_id):
    """Record the exact reviewed dispositions, retaining messages and domain data."""
    from mge.mge_embed_manager import _refreshes

    async def owned():
        async with presentation_owner(bot, event_id):
            outcomes = {}
            for target in targets:
                if target["EventId"] != event_id or target["DeliveryState"] not in {
                    "pending",
                    "failed",
                    "held",
                }:
                    raise ValueError("Invalid retirement preview")
                outcomes[target["BoardKind"]] = await drain_thread(
                    dal.transition,
                    target,
                    "retired",
                    reason="operator_keep_history",
                    actor_id=actor_id,
                )
            return outcomes

    return await _refreshes.run_direct(owned)
