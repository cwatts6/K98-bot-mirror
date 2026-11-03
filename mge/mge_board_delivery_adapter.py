"""Discord adapter: board creation uses the existing durable evidence contract."""

import discord

from services import event_delivery_service as delivery
from services.event_delivery_store import DeliveryHeld, delivery_key


async def send_board_once(*, kind, event_id, channel, binding=None, **kwargs):
    key = delivery_key("mge_board", kind, int(event_id), int(channel.id))
    async with delivery.operation_lock(key):
        receipt = await delivery.read(key)
        if receipt:
            if (
                receipt.get("state") != "acknowledged"
                or not receipt.get("message_id")
                or int(receipt.get("channel_id", 0)) != int(channel.id)
                or binding is None
                or (receipt.get("event_data") or {}).get("board_binding") != binding
            ):
                raise DeliveryHeld("Board send outcome requires exact reconciliation")
            message = await channel.fetch_message(int(receipt["message_id"]))
            # An acknowledged send with a failed SQL ID save is recoverable by exact identity.
            # Never repeat notifications while bringing that known message up to date.
            await message.edit(**{**kwargs, "allowed_mentions": discord.AllowedMentions.none()})
            return message
        if not await delivery.begin(
            key,
            kind=f"mge_{kind}_board",
            target=channel.id,
            event=str(event_id),
            event_data={"board_binding": binding} if binding is not None else None,
        ):
            raise DeliveryHeld("Board creation admission is unavailable")
        message = await channel.send(**kwargs)
        await delivery.finish(key, "acknowledged", message_id=message.id, channel_id=channel.id)
        return message
