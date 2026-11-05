# daily_KVK_overview_embed.py

from datetime import timedelta
import json
import logging

logger = logging.getLogger(__name__)

import discord

from constants import DAILY_KVK_OVERVIEW_TRACKER
from core.discord_embed_limits import (
    MAX_FIELD_VALUE_CHARACTERS,
    require_valid_embed_payload,
    truncate_text,
    validate_embed_payload,
)
from embed_utils import LocalTimeToggleView, format_event_time
from event_cache import get_all_upcoming_events
from event_utils import serialize_event
from file_utils import atomic_json_write

# Use the safer, centralized retrying save helper (delegates to file_utils.run_with_retries)
from rehydrate_views import _tracker_store
from services import event_delivery_service as delivery
from services.event_delivery_store import DeliveryHeld, delivery_key
from services.legacy_export_snapshot_service import drain_thread
from services.overview_delivery_service import MessageAbsent, publish
from stats_alerts.kvk_meta import is_currently_kvk
from utils import utcnow  # tz-aware UTC


class _OverviewAdapter:
    def __init__(self, bot, channel_id, upcoming):
        self.bot, self.channel_id, self.upcoming = bot, channel_id, upcoming
        self.channel = None
        self.messages = {}
        self.prepared_payload = None

    async def identity(self):
        daily_id = await drain_thread(load_existing_daily_KVK_overview_id)
        tracked = (await _tracker_store().snapshot()).get("daily_kvk_overview")
        if tracked:
            receipt = tracked.get("_restoration_edit")
            if receipt is not None and (
                not isinstance(receipt, dict) or receipt.get("state") != "acknowledged"
            ):
                raise DeliveryHeld("Overview restoration edit unresolved")
            if tracked.get("channel_id") != self.channel_id:
                raise DeliveryHeld("Overview channel identity conflict")
            tracked_id = tracked["message_id"]
            if daily_id and daily_id != tracked_id:
                raise DeliveryHeld("Overview tracker identity conflict")
            return daily_id or tracked_id
        return daily_id

    async def _channel(self):
        if self.channel is None:
            self.channel = await self.bot.fetch_channel(self.channel_id)
        return self.channel

    async def fetch(self, message_id):
        if message_id not in self.messages:
            channel = await self._channel()
            try:
                self.messages[message_id] = await channel.fetch_message(message_id)
            except discord.NotFound as exc:
                if exc.code == 10008:
                    raise MessageAbsent() from exc
                raise
        return self.messages[message_id]

    def payload(self):
        return dict(
            embed=build_daily_KVK_overview_embed(self.upcoming),
            view=LocalTimeToggleView(
                events=self.upcoming,
                prefix="daily_kvk_overview",
                timeout=None,
                complete_event_packing=True,
            ),
        )

    async def send(self):
        message = await self.channel.send(**self.prepared_payload)
        self.messages[message.id] = message
        return message.id

    async def edit(self, message_id):
        message = await self.fetch(message_id)
        await message.edit(**self.prepared_payload)
        return message.id

    async def prepare(self):
        await self._channel()
        self.prepared_payload = self.payload()

    async def pin(self, message_id):
        message = await self.fetch(message_id)
        await message.pin()
        return message.id

    async def absent(self):
        raise MessageAbsent()

    async def delete(self, message_id):
        message = await self.fetch(message_id)
        try:
            # Deletion also removes a pin. No independent unpin operation whose
            # failure could hide the disposition of the deletion.
            await message.delete()
        except discord.NotFound as exc:
            if exc.code == 10008:
                raise MessageAbsent() from exc
            raise
        return message.id

    async def save_projection(self, message_id):
        # Durable edit acknowledgement does not restore process-local callback
        # handlers. Rebind current events even when the remote edit is reused.
        self.bot.add_view(self.prepared_payload["view"], message_id=message_id)
        store = _tracker_store()
        async with store.locked():
            data = await store.snapshot()
            old = data.get("daily_kvk_overview")
            if old and old.get("message_id") != message_id:
                raise DeliveryHeld("Overview tracker changed during delivery")
            if old and old.get("_restoration_edit", {}).get("state") not in {None, "acknowledged"}:
                raise DeliveryHeld("Overview restoration edit unresolved")
            data["daily_kvk_overview"] = {
                "message_id": message_id,
                "channel_id": self.channel_id,
                "created_at": utcnow().isoformat(),
                "events": [serialize_event(e) for e in self.upcoming],
                "prefix": "daily_kvk_overview",
            }
            await store.write(data)
        await drain_thread(save_daily_KVK_overview_id, message_id)

    async def remove_projection(self, message_id):
        store = _tracker_store()
        async with store.locked():
            data = await store.snapshot()
            old = data.get("daily_kvk_overview")
            if old:
                if old.get("message_id") != message_id or old.get("channel_id") != self.channel_id:
                    raise DeliveryHeld("Overview tracker changed during removal")
                data.pop("daily_kvk_overview")
                await store.write(data)
        current = await drain_thread(load_existing_daily_KVK_overview_id)
        if current and current != message_id:
            raise DeliveryHeld("Daily overview identity changed during removal")
        if current:
            await drain_thread(atomic_json_write, DAILY_KVK_OVERVIEW_TRACKER, {})


async def _publish_overview(bot, event_channel_id, *, enabled):
    now = utcnow()
    upcoming = [e for e in get_all_upcoming_events() if e["start_time"] <= now + timedelta(days=4)]
    revision = delivery_key(now.date().isoformat(), [serialize_event(e) for e in upcoming])
    try:
        return await publish(
            _OverviewAdapter(bot, event_channel_id, upcoming),
            event_channel_id,
            enabled=enabled,
            has_events=bool(upcoming),
            revision=revision,
        )
    except Exception as exc:
        logger.warning(
            "[DAILY_KVK_OVERVIEW] disposition=unconfirmed error_type=%s", type(exc).__name__
        )
        return "unconfirmed"


async def post_or_update_daily_KVK_overview(bot, event_channel_id):
    task = delivery.own(
        _publish_overview(bot, event_channel_id, enabled=is_currently_kvk()),
        name="daily-kvk-overview",
    )
    return await task if task else "closed"


async def remove_daily_KVK_overview_embed(bot, event_channel_id):
    task = delivery.own(
        _publish_overview(bot, event_channel_id, enabled=False), name="daily-kvk-overview-removal"
    )
    return await task if task else "closed"


# ---- Embed Generator ----
def build_daily_KVK_overview_embed(events):
    type_map = {
        "ruins": "ruins",
        "next ruins": "ruins",
        "altar": "altars",
        "altars": "altars",
        "next altar fight": "altars",
        "chronicle": "chronicle",
        "major": "major",
    }
    grouped = {"ruins": [], "altars": [], "chronicle": [], "major": []}
    for event in events:
        raw_type = (event.get("type") or "").lower()
        normalized_type = type_map.get(raw_type)
        if normalized_type in grouped:
            grouped[normalized_type].append(event)
        else:
            logger.warning("[DAILY_KVK_OVERVIEW] Skipping unknown event type")

    now = utcnow()
    window_end = now + timedelta(days=4)
    total_in_window = len(events)
    window_str = f"**{now.strftime('%a %d %b')} → {window_end.strftime('%a %d %b')} (UTC)**"
    desc = (
        f"{window_str}\n"
        f"{total_in_window} upcoming event{'s' if total_in_window != 1 else ''} in the next 4 days.\n\n"
        f"Use the toggle below to view times in your local timezone."
    )

    embed = discord.Embed(
        title="📊 KVK Event Overview – Next 4 Days",
        description=desc,
        color=discord.Color.teal(),
        timestamp=utcnow(),
    )
    embed.set_footer(
        text="K98 Bot – Daily Schedule • Times shown in UTC — tap ‘Show in my local time’ to convert.",
        icon_url=None,
    )

    for entries in grouped.values():
        entries.sort(key=lambda item: item["start_time"])
    shown = {key: min(6, len(entries)) for key, entries in grouped.items()}

    def event_block(event):
        start_text = format_event_time(event["start_time"])
        date_header = event["start_time"].strftime("%a %d %b")
        raw_title = " ".join(
            str(event.get("title") or event.get("name") or "(Unnamed Event)").split()
        )
        fixed_length = len(f"**{date_header}**\n• ****\n{start_text}")
        title = truncate_text(raw_title, MAX_FIELD_VALUE_CHARACTERS - fixed_length)
        return f"**{date_header}**\n• **{title}**\n{start_text}"

    def event_was_compacted(event):
        start_text = format_event_time(event["start_time"])
        date_header = event["start_time"].strftime("%a %d %b")
        raw_title = " ".join(
            str(event.get("title") or event.get("name") or "(Unnamed Event)").split()
        )
        fixed_length = len(f"**{date_header}**\n• ****\n{start_text}")
        return len(raw_title) > MAX_FIELD_VALUE_CHARACTERS - fixed_length

    def build_fields():
        fields = []
        for event_type, entries in grouped.items():
            if not entries:
                continue
            base_name = f"{event_type.capitalize()} • {len(entries)}"
            type_fields = []
            for event in entries[: shown[event_type]]:
                block = event_block(event)
                if (
                    type_fields
                    and len(f"{type_fields[-1][1]}\n\n{block}") <= MAX_FIELD_VALUE_CHARACTERS
                ):
                    name, value = type_fields[-1]
                    type_fields[-1] = (name, f"{value}\n\n{block}")
                else:
                    suffix = " (continued)" if type_fields else ""
                    type_fields.append((f"{base_name}{suffix}", block))

            omitted = len(entries) - shown[event_type]
            if omitted:
                marker = f"… {omitted} more {event_type} events in the next 4 days — use Local Time"
                if (
                    type_fields
                    and len(f"{type_fields[-1][1]}\n{marker}") <= MAX_FIELD_VALUE_CHARACTERS
                ):
                    name, value = type_fields[-1]
                    type_fields[-1] = (name, f"{value}\n{marker}")
                else:
                    type_fields.append((f"{base_name} (continued)", marker))
            fields.extend(type_fields)
        return fields

    fields = build_fields()
    while validate_embed_payload(
        {
            **embed.to_dict(),
            "fields": [{"name": name, "value": value, "inline": False} for name, value in fields],
        }
    ):
        removable = next((key for key in reversed(tuple(grouped)) if shown[key] > 0), None)
        if removable is None:
            break
        shown[removable] -= 1
        fields = build_fields()

    for name, value in fields:
        embed.add_field(name=name, value=value, inline=False)

    usage = require_valid_embed_payload(embed)
    compacted = sum(
        event_was_compacted(event)
        for key, entries in grouped.items()
        for event in entries[: shown[key]]
    )
    omitted = sum(len(entries) - shown[key] for key, entries in grouped.items())
    logger.info(
        "[EMBED_PAYLOAD] renderer=daily_kvk fields=%d chars=%d max_field_value=%d compacted_events=%d omitted_events=%d",
        usage.field_counts[0],
        usage.total_characters,
        max((len(field.value or "") for field in embed.fields), default=0),
        compacted,
        omitted,
    )
    return embed


# ---- Tracker for pin/update ----
def load_existing_daily_KVK_overview_id():
    try:
        with open(DAILY_KVK_OVERVIEW_TRACKER, encoding="utf-8") as stream:
            data = json.load(stream)
    except FileNotFoundError:
        return None
    if not isinstance(data, dict):
        raise DeliveryHeld("Invalid daily overview tracker")
    message_id = data.get("message_id")
    if message_id is not None and (type(message_id) is not int or message_id <= 0):
        raise DeliveryHeld("Invalid daily overview message identity")
    return message_id


def save_daily_KVK_overview_id(msg_id):
    atomic_json_write(DAILY_KVK_OVERVIEW_TRACKER, {"message_id": int(msg_id)})
