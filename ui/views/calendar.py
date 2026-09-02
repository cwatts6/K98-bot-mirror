from __future__ import annotations

from collections import OrderedDict
from datetime import UTC, datetime
import logging
import math
from typing import Any

import discord

from core.discord_embed_limits import (
    MAX_DESCRIPTION_CHARACTERS,
    MAX_FIELD_NAME_CHARACTERS,
    MAX_FIELD_VALUE_CHARACTERS,
    MAX_FOOTER_CHARACTERS,
    MAX_TITLE_CHARACTERS,
    MAX_TOTAL_CHARACTERS,
    require_valid_embed_payload,
    truncate_text,
    validate_embed_payload,
)
from embed_utils import LocalTimeToggleView
from event_calendar.datetime_utils import parse_iso_utc_nullable
from event_calendar.runtime_cache import (
    filter_events,
    list_event_types,
    list_importance_values,
    load_runtime_cache,
    next_event as pick_next_event,
)

logger = logging.getLogger(__name__)

_PAGE_SIZE = 8
_ALLOWED_DAYS = {1, 3, 7, 30, 90, 180, 365}

_SOURCE_LINK_MAX = 500


def discord_ts(iso_utc: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        epoch = int(dt.timestamp())
        return f"<t:{epoch}:f> • <t:{epoch}:R>"
    except Exception:
        return truncate_text(iso_utc, 64)


def fmt_abs_utc(iso_utc: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        dt = dt.astimezone(UTC)
        return dt.strftime("%d %B %Y %H:%M")
    except Exception:
        return truncate_text(iso_utc, 64)


def cache_footer(cache_state: dict) -> str:
    """
    Task 8 fix:
    Do not rely on missing pipeline_run_id in cache payload.
    """
    age = cache_state.get("cache_age_minutes")
    payload = cache_state.get("payload") or {}
    generated_utc = payload.get("generated_utc") or "n/a"
    horizon_days = payload.get("horizon_days")
    source = payload.get("source") or "n/a"
    return (
        f"cache_age_min={age if age is not None else 'n/a'}"
        f" • generated_utc={generated_utc}"
        f" • horizon_days={horizon_days if horizon_days is not None else 'n/a'}"
        f" • source={source}"
    )


def line_meta_links(e: dict) -> str:
    parts: list[str] = []
    link_url = str(e.get("link_url") or "").strip()
    channel_id = str(e.get("channel_id") or "").strip()

    if link_url and len(link_url) <= _SOURCE_LINK_MAX:
        parts.append(f"[link]({link_url})")
    elif link_url:
        parts.append("link omitted: source URL exceeds the supported length")
    if channel_id and channel_id.isdigit():
        parts.append(f"<#{channel_id}>")

    return " • ".join(parts)


def title_with_variant(e: dict) -> str:
    title = str(e.get("title") or "(untitled)").strip()
    variant = str(e.get("variant") or "").strip()
    return f"{title} [{variant}]" if variant else title


def event_line(e: dict, *, max_length: int = MAX_FIELD_VALUE_CHARACTERS) -> str:
    emoji = truncate_text(str(e.get("emoji") or "").strip(), 16)
    title_text = title_with_variant(e)

    start_iso = str(e.get("start_utc") or "")
    end_iso = str(e.get("end_utc") or "")
    start_abs = fmt_abs_utc(start_iso)
    end_abs = fmt_abs_utc(end_iso)

    ts = discord_ts(start_iso)
    start_rel = ts.split(" • ")[1] if " • " in ts else ts

    meta = line_meta_links(e)
    meta_line = f"\n{meta}" if meta else ""
    emoji_prefix = f"{emoji} " if emoji else ""

    fixed = f"• {emoji_prefix}****\nstarts: {start_abs} • {start_rel} → ends: {end_abs}{meta_line}"
    compact_title = truncate_text(title_text, max(1, max_length - len(fixed)))
    return f"• {emoji_prefix}**{compact_title}**\nstarts: {start_abs} • {start_rel} → ends: {end_abs}{meta_line}"


def _payload_with_fields(embed: discord.Embed, fields: list[tuple[str, str]]) -> dict[str, Any]:
    return {
        **embed.to_dict(),
        "fields": [{"name": name, "value": value, "inline": False} for name, value in fields],
    }


def paginate(items: list[dict], page: int) -> tuple[list[dict], int, int]:
    total = max(1, math.ceil(len(items) / _PAGE_SIZE))
    p = min(max(1, page), total)
    start = (p - 1) * _PAGE_SIZE
    return items[start : start + _PAGE_SIZE], p, total


def autocomplete_pick(options: list[str], value: str, *, limit: int = 25) -> list[str]:
    q = (value or "").strip().lower()
    if not q:
        return options[:limit]
    starts = [o for o in options if o.startswith(q)]
    contains = [o for o in options if q in o and o not in starts]
    return (starts + contains)[:limit]


def group_events_by_date(events: list[dict[str, Any]]) -> OrderedDict[str, list[dict[str, Any]]]:
    grouped: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
    for e in events:
        iso = str(e.get("start_utc") or "")
        label = fmt_abs_utc(iso).split(" ")[0:3]
        day_key = " ".join(label) if label else "Unknown date"
        grouped.setdefault(day_key, []).append(e)
    return grouped


def _calendar_omission_field(omitted: int) -> tuple[str, str]:
    return (
        "… More calendar events",
        f"{omitted} additional calendar events omitted to fit Discord limits — use /calendar.",
    )


def build_pinned_calendar_embed(
    *, events: list[dict[str, Any]], footer: str, description: str | None = None
) -> discord.Embed:
    candidates = [
        (day, event)
        for day, day_events in group_events_by_date(events).items()
        for event in day_events
    ]
    title = "📌 30-Day Calendar"
    marker_name, marker_value = _calendar_omission_field(len(candidates))
    reserved_marker_characters = len(marker_name) + len(marker_value) if candidates else 0
    description_limit = min(
        MAX_DESCRIPTION_CHARACTERS,
        max(0, MAX_TOTAL_CHARACTERS - len(title) - reserved_marker_characters),
    )
    bounded_description = truncate_text(description, description_limit) if description else None
    embed = discord.Embed(
        title=title,
        description=bounded_description,
        color=discord.Color.blurple(),
    )
    base_characters = len(embed.title or "") + len(embed.description or "")
    footer_limit = min(
        MAX_FOOTER_CHARACTERS,
        max(0, MAX_TOTAL_CHARACTERS - base_characters - reserved_marker_characters),
    )
    embed.set_footer(text=truncate_text(footer, footer_limit))

    def build_fields(accepted: list[tuple[str, dict[str, Any]]], omitted: int):
        fields: list[tuple[str, str]] = []
        for day, event in accepted:
            line = event_line(event)
            base_name = truncate_text(day, MAX_FIELD_NAME_CHARACTERS)
            if fields and fields[-1][0] in {base_name, f"{base_name} (continued)"}:
                combined = f"{fields[-1][1]}\n\n{line}"
                if len(combined) <= MAX_FIELD_VALUE_CHARACTERS:
                    fields[-1] = (fields[-1][0], combined)
                    continue
            continued = any(name.startswith(base_name) for name, _ in fields)
            name = f"{base_name} (continued)" if continued else base_name
            fields.append((truncate_text(name, MAX_FIELD_NAME_CHARACTERS), line))
        if omitted:
            fields.append(_calendar_omission_field(omitted))
        return fields

    accepted: list[tuple[str, dict[str, Any]]] = []
    for index, candidate in enumerate(candidates):
        projected = [*accepted, candidate]
        fields = build_fields(projected, len(candidates) - index - 1)
        if validate_embed_payload(_payload_with_fields(embed, fields)):
            break
        accepted = projected

    omitted = len(candidates) - len(accepted)
    fields = build_fields(accepted, omitted)
    while accepted and validate_embed_payload(_payload_with_fields(embed, fields)):
        accepted.pop()
        omitted = len(candidates) - len(accepted)
        fields = build_fields(accepted, omitted)
    for name, value in fields:
        embed.add_field(name=name, value=value or "—", inline=False)

    usage = require_valid_embed_payload(embed)
    logger.info(
        "[EMBED_PAYLOAD] renderer=calendar_pinned fields=%d chars=%d max_field_value=%d compacted_events=%d omitted_events=%d",
        usage.field_counts[0],
        usage.total_characters,
        max((len(field.value or "") for field in embed.fields), default=0),
        int(
            any(
                len(event_line(event, max_length=100_000)) > MAX_FIELD_VALUE_CHARACTERS
                for _, event in accepted
            )
        ),
        omitted,
    )
    return embed


def build_next_event_embed(*, event: dict[str, Any], footer: str) -> discord.Embed:
    embed = discord.Embed(title="⏭️ Next Calendar Event", color=discord.Color.green())

    emoji = str(event.get("emoji") or "").strip()
    title_text = title_with_variant(event)
    title_display = f"{emoji} {title_text}".strip()

    start_iso = str(event.get("start_utc") or "")
    end_iso = str(event.get("end_utc") or "")
    start_abs = fmt_abs_utc(start_iso)
    end_abs = fmt_abs_utc(end_iso)

    ts = discord_ts(start_iso)
    start_rel = ts.split(" • ")[1] if " • " in ts else ts

    fixed = f"****\nstarts: {start_abs} • {start_rel} → ends: {end_abs}"
    title_display = truncate_text(title_display, MAX_DESCRIPTION_CHARACTERS - len(fixed))
    embed.description = f"**{title_display}**\nstarts: {start_abs} • {start_rel} → ends: {end_abs}"

    meta = line_meta_links(event)
    if meta:
        embed.add_field(name="Details", value=meta, inline=False)

    payload_without_footer = require_valid_embed_payload(embed)
    footer_limit = min(
        MAX_FOOTER_CHARACTERS,
        MAX_TOTAL_CHARACTERS - payload_without_footer.total_characters,
    )
    embed.set_footer(text=truncate_text(footer, footer_limit))
    usage = require_valid_embed_payload(embed)
    logger.info(
        "[EMBED_PAYLOAD] renderer=calendar_next fields=%d chars=%d max_field_value=%d compacted_events=%d omitted_events=0",
        usage.field_counts[0],
        usage.total_characters,
        max((len(field.value or "") for field in embed.fields), default=0),
        int(title_display != f"{emoji} {title_text}".strip()),
    )
    return embed


class CalendarLocalTimeToggleView(LocalTimeToggleView):
    def __init__(self, events: list[dict[str, Any]], prefix: str, timeout: float | None):
        converted = []
        for e in events:
            start_iso = str(e.get("start_utc") or "")
            dt = parse_iso_utc_nullable(start_iso)
            if dt is None:
                continue
            converted.append(
                {
                    "name": title_with_variant(e),
                    "title": title_with_variant(e),
                    "type": str(e.get("type") or ""),
                    "start_time": dt,
                }
            )
        super().__init__(
            events=converted,
            prefix=prefix,
            timeout=timeout,
            complete_event_packing=True,
        )


class CalendarPaginationView(CalendarLocalTimeToggleView):
    def __init__(
        self,
        *,
        title: str,
        items: list[dict],
        cache_footer_text: str,
        owner_user_id: int | None = None,
        summary_field_name: str | None = None,
        summary_field_value: str | None = None,
        color: discord.Color = discord.Color.blurple(),
        timeout: float = 180.0,
        local_time_events: list[dict[str, Any]] | None = None,
        local_time_prefix: str = "calendar_command",
    ):
        super().__init__(
            events=local_time_events if local_time_events is not None else items,
            prefix=local_time_prefix,
            timeout=timeout,
        )
        self._title = title
        self._all_items = items
        self._cache_footer = cache_footer_text
        self._owner_user_id = owner_user_id
        self._summary_field_name = summary_field_name
        self._summary_field_value = summary_field_value
        self._color = color
        self._page = 1
        self.message: discord.Message | None = None

        _, _, total = paginate(self._all_items, self._page)
        self._total_pages = total
        self._sync_button_state()

    def _sync_button_state(self) -> None:
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if child.custom_id == "calendar_prev":
                    child.disabled = self._page <= 1
                elif child.custom_id == "calendar_next":
                    child.disabled = self._page >= self._total_pages

    def _build_current_embed(self) -> discord.Embed:
        page_items, p, total = paginate(self._all_items, self._page)
        self._total_pages = total
        self._sync_button_state()

        total_items = len(self._all_items)
        if total_items > 0:
            start_idx = ((p - 1) * _PAGE_SIZE) + 1
            end_idx = min(p * _PAGE_SIZE, total_items)
            range_text = f"{start_idx}–{end_idx} of {total_items}"
        else:
            range_text = "0 of 0"

        footer = truncate_text(
            f"{range_text} • page {p}/{total} • {self._cache_footer}",
            MAX_FOOTER_CHARACTERS,
        )
        embed = discord.Embed(
            title=truncate_text(self._title, MAX_TITLE_CHARACTERS),
            color=self._color,
        )
        if p == 1 and self._summary_field_name and self._summary_field_value:
            embed.add_field(
                name=truncate_text(self._summary_field_name, MAX_FIELD_NAME_CHARACTERS),
                value=truncate_text(self._summary_field_value, MAX_FIELD_VALUE_CHARACTERS),
                inline=False,
            )
        embed.set_footer(text=footer)

        accepted: list[str] = []
        for index, item in enumerate(page_items):
            line = event_line(item)
            remaining = len(page_items) - index - 1
            parts = [*accepted, line]
            if remaining:
                parts.append(
                    f"… {remaining} more events on this page omitted to fit Discord limits"
                )
            embed.description = "\n\n".join(parts)
            if validate_embed_payload(embed):
                break
            accepted.append(line)

        omitted = len(page_items) - len(accepted)
        parts = list(accepted)
        if omitted:
            parts.append(f"… {omitted} more events on this page omitted to fit Discord limits")
        embed.description = "\n\n".join(parts)
        while accepted and validate_embed_payload(embed):
            accepted.pop()
            omitted = len(page_items) - len(accepted)
            embed.description = "\n\n".join(
                [
                    *accepted,
                    f"… {omitted} more events on this page omitted to fit Discord limits",
                ]
            )

        usage = require_valid_embed_payload(embed)
        logger.info(
            "[EMBED_PAYLOAD] renderer=calendar_page fields=%d chars=%d max_field_value=%d compacted_events=%d omitted_events=%d",
            usage.field_counts[0],
            usage.total_characters,
            max((len(field.value or "") for field in embed.fields), default=0),
            sum(
                len(event_line(item, max_length=100_000)) > MAX_FIELD_VALUE_CHARACTERS
                for item in page_items[: len(accepted)]
            ),
            omitted,
        )
        return embed

    async def _guard_owner(self, interaction: discord.Interaction) -> bool:
        if self._owner_user_id is None:
            return True
        if not interaction.user or interaction.user.id != self._owner_user_id:
            await interaction.response.send_message(
                "Only the command invoker can use these pagination buttons.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(
        label="◀ Prev", style=discord.ButtonStyle.secondary, custom_id="calendar_prev"
    )
    async def prev_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not await self._guard_owner(interaction):
            return
        if self._page > 1:
            self._page -= 1

        page_items, _, _ = paginate(self._all_items, self._page)

        local_events = []
        for e in page_items:
            parsed = parse_iso_utc_nullable(str(e.get("start_utc") or ""))
            if parsed is None:
                continue
            local_events.append(
                {
                    "name": title_with_variant(e),
                    "title": title_with_variant(e),
                    "type": str(e.get("type") or ""),
                    "start_time": parsed,
                }
            )

        self.events = local_events
        await interaction.response.edit_message(embed=self._build_current_embed(), view=self)

    @discord.ui.button(
        label="Next ▶", style=discord.ButtonStyle.secondary, custom_id="calendar_next"
    )
    async def next_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not await self._guard_owner(interaction):
            return
        if self._page < self._total_pages:
            self._page += 1

        page_items, _, _ = paginate(self._all_items, self._page)

        local_events = []
        for e in page_items:
            parsed = parse_iso_utc_nullable(str(e.get("start_utc") or ""))
            if parsed is None:
                continue
            local_events.append(
                {
                    "name": title_with_variant(e),
                    "title": title_with_variant(e),
                    "type": str(e.get("type") or ""),
                    "start_time": parsed,
                }
            )

        self.events = local_events
        await interaction.response.edit_message(embed=self._build_current_embed(), view=self)

    async def on_timeout(self) -> None:
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            logger.debug("[CalendarPaginationView] timeout edit failed", exc_info=True)


async def calendar_type_autocomplete(ctx: discord.AutocompleteContext) -> list[str]:
    cache_state = load_runtime_cache()
    types = ["all"]
    if cache_state.get("ok"):
        types.extend(list_event_types(cache_state))
    return autocomplete_pick(types, str(getattr(ctx, "value", "") or ""))


async def calendar_importance_autocomplete(ctx: discord.AutocompleteContext) -> list[str]:
    cache_state = load_runtime_cache()
    values = ["all"]
    if cache_state.get("ok"):
        values.extend(list_importance_values(cache_state))
    return autocomplete_pick(values, str(getattr(ctx, "value", "") or ""))


def query_calendar(
    *,
    days: int,
    event_type: str,
    importance: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    cache_state = load_runtime_cache()
    if not cache_state.get("ok"):
        return cache_state, []

    known_types = ["all", *list_event_types(cache_state)]
    known_importance = ["all", *list_importance_values(cache_state)]

    type_norm = (event_type or "all").strip().lower()
    imp_norm = (importance or "all").strip().lower()
    if type_norm not in known_types:
        type_norm = "all"
    if imp_norm not in known_importance:
        imp_norm = "all"

    filtered = filter_events(
        cache_state.get("events", []),
        now=datetime.now(UTC),
        days=days,
        event_type=type_norm,
        importance=imp_norm,
    )
    return cache_state, filtered


def allowed_days() -> set[int]:
    return set(_ALLOWED_DAYS)


def get_next_event(cache_state: dict[str, Any], *, event_type: str) -> dict[str, Any] | None:
    t = (event_type or "all").strip().lower()
    known = ["all", *list_event_types(cache_state)]
    if t not in known:
        t = "all"
    return pick_next_event(cache_state.get("events", []), now=datetime.now(UTC), event_type=t)
