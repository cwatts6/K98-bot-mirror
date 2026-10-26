"""Daily overview orchestration using exact identities and separate step receipts.

The adapter owns Discord and the two legacy tracker projections. This service
never infers that a failed edit means permission to create another message.
"""

from services import event_delivery_service as delivery
from services.event_delivery_store import DeliveryHeld, delivery_key
from services.legacy_export_snapshot_service import drain_thread


class MessageAbsent(Exception):
    """Exact message fetch/delete returned Discord Unknown Message (10008)."""


async def _step(kind, channel_id, identity, invoke, *, message_id=None, generation=None):
    key = delivery_key(kind, channel_id, identity)
    if not await delivery.begin(
        key, kind=kind, target=channel_id, message_id=message_id, generation=generation
    ):
        receipt = await delivery.read(key)
        if receipt and receipt["state"] in {"acknowledged", "not_found"}:
            return receipt
        return None
    if delivery.is_closed():
        return None
    try:
        result = await invoke()
    except MessageAbsent:
        return await delivery.finish(key, "not_found", message_id=message_id, channel_id=channel_id)
    # Other failures/cancellation retain 'entered'; callers must not replay.
    return await delivery.finish(
        key, "acknowledged", message_id=result or message_id, channel_id=channel_id
    )


async def publish(adapter, channel_id, *, enabled, has_events, revision):
    async with delivery.operation_lock(("overview", channel_id)):
        if delivery.is_closed():
            return "closed"
        rows = await drain_thread(delivery.store.rows)
        selected = [
            r for r in rows if r["kind"].startswith("overview-") and r["target"] == str(channel_id)
        ]
        if any(r["state"] == "entered" for r in selected):
            return "unconfirmed_previous_operation"
        message_id = await adapter.identity()
        sends = [r for r in selected if r["kind"] == "overview-send"]
        generations = [row.get("generation") for row in sends]
        if any(type(value) is not int for value in generations) or sorted(generations) != list(
            range(len(sends))
        ):
            raise DeliveryHeld("Overview generation evidence is incomplete")
        latest = max(sends, key=lambda row: row["generation"]) if sends else None
        if latest and latest["state"] == "acknowledged":
            deleted = await delivery.read(
                delivery_key("overview-delete", channel_id, latest["message_id"])
            )
            if not deleted or deleted["state"] not in {"acknowledged", "not_found"}:
                if message_id and message_id != latest["message_id"]:
                    return "tracker_identity_conflict"
                message_id = latest["message_id"]

        if not enabled:
            if not message_id:
                return "not_in_kvk_no_message"
            try:
                await adapter.fetch(message_id)
                absent = False
            except MessageAbsent:
                absent = True
            deleted = await _step(
                "overview-delete",
                channel_id,
                message_id,
                adapter.absent if absent else lambda: adapter.delete(message_id),
                message_id=message_id,
            )
            if not deleted:
                return "removal_unconfirmed"
            await adapter.remove_projection(message_id)
            return "removed" if deleted["state"] == "acknowledged" else "confirmed_absent"
        if not has_events:
            return "no_upcoming_events"
        # Resolve read-only destinations and validate payload before recording
        # entry into a Discord mutation. A read failure is safe to observe again.
        await adapter.prepare()
        created = False
        if message_id:
            try:
                await adapter.fetch(message_id)
            except MessageAbsent:
                # Record absence and prune only this exact identity. Creation can
                # happen on a later normal invocation; never through edit failure.
                await _step(
                    "overview-delete",
                    channel_id,
                    message_id,
                    lambda: adapter.absent(),
                    message_id=message_id,
                )
                await adapter.remove_projection(message_id)
                return "confirmed_absent"
        else:
            sent = await _step(
                "overview-send", channel_id, len(sends), adapter.send, generation=len(sends)
            )
            if not sent:
                return "send_unconfirmed"
            message_id = sent["message_id"]
            created = True
        if not created:
            edited = await _step(
                "overview-edit",
                channel_id,
                [message_id, revision],
                lambda: adapter.edit(message_id),
                message_id=message_id,
            )
            if not edited or edited["state"] != "acknowledged":
                return "edit_unconfirmed"
        pinned = await _step(
            "overview-pin",
            channel_id,
            message_id,
            lambda: adapter.pin(message_id),
            message_id=message_id,
        )
        if not pinned or pinned["state"] != "acknowledged":
            return "pin_unconfirmed"
        await adapter.save_projection(message_id)
        return "created" if created else "updated"
