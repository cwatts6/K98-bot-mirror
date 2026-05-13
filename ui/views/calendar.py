from __future__ import annotations

from collections import OrderedDict
from datetime import UTC, datetime
import logging
import math
from typing import Any

import discord

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

_EMBED_MAX_FIELDS = 25
_FIELD_VALUE_MAX = 1024
_EMBED_TOTAL_SOFT_MAX = 5800  # conservative under discord hard cap


def discord_ts(iso_utc: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        epoch = int(dt.timestamp())
        return f"<t:{epoch}:f> • <t:{epoch}:R>"
    except Exception:
        return iso_utc


def fmt_abs_utc(iso_utc: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        dt = dt.astimezone(UTC)
        return dt.strftime("%d %B %Y %H:%M")
    except Exception:
        return iso_utc


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

    if link_url:
        parts.append(f"[link]({link_url})")
    if channel_id and channel_id.isdigit():
        parts.append(f"<#{channel_id}>")

    return " • ".join(parts)


def title_with_variant(e: dict) -> str:
    title = str(e.get("title") or "(untitled)").strip()
    variant = str(e.get("variant") or "").strip()
    return f"{title} [{variant}]" if variant else title


def event_line(e: dict) -> str:
    emoji = str(e.get("emoji") or "").strip()
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

    return f"• {emoji_prefix}**{title_text}**\nstarts: {start_abs} • {start_rel} → ends: {end_abs}{meta_line}"


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


def build_pinned_calendar_embed(*, events: list[dict[str, Any]], footer: str) -> discord.Embed:
    embed = discord.Embed(title="📌 30-Day Calendar", color=discord.Color.blurple())
    grouped = group_events_by_date(events)

    total_chars = len(embed.title or "")
    fields_used = 0

    for day, day_events in grouped.items():
        if fields_used >= _EMBED_MAX_FIELDS:
            break
        lines = [event_line(e) for e in day_events]
        value = "\n\n".join(lines)

        if len(value) > _FIELD_VALUE_MAX:
            out: list[str] = []
            running = 0
            for ln in lines:
                need = len(ln) + 2
                if running + need > (_FIELD_VALUE_MAX - 4):
                    break
                out.append(ln)
                running += need
            value = "\n\n".join(out) + "\n…"

        projected = total_chars + len(day) + len(value)
        if projected > _EMBED_TOTAL_SOFT_MAX:
            if fields_used == 0:
                value = value[: (_FIELD_VALUE_MAX - 1)] + "…"
            else:
                break

        embed.add_field(name=day, value=value or "—", inline=False)
        total_chars += len(day) + len(value)
        fields_used += 1

    embed.set_footer(text=footer)
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

    embed.description = f"**{title_display}**\nstarts: {start_abs} • {start_rel} → ends: {end_abs}"

    meta = line_meta_links(event)
    if meta:
        embed.add_field(name="Details", value=meta, inline=False)

    embed.set_footer(text=footer)
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
        super().__init__(events=converted, prefix=prefix, timeout=timeout)


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

        embed = discord.Embed(
            title=self._title,
            description="\n\n".join(event_line(e) for e in page_items),
            color=self._color,
        )
        if p == 1 and self._summary_field_name and self._summary_field_value:
            embed.add_field(
                name=self._summary_field_name,
                value=self._summary_field_value,
                inline=False,
            )

        total_items = len(self._all_items)
        if total_items > 0:
            start_idx = ((p - 1) * _PAGE_SIZE) + 1
            end_idx = min(p * _PAGE_SIZE, total_items)
            range_text = f"{start_idx}–{end_idx} of {total_items}"
        else:
            range_text = "0 of 0"

        embed.set_footer(text=f"{range_text} • page {p}/{total} • {self._cache_footer}")
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
