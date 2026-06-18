from __future__ import annotations

from typing import Any

import discord

from kvk.models.kvk_rankings import RankingPayload
from utils import fmt_short

try:
    from constants import INFO_COLOR

    DEFAULT_COLOR = INFO_COLOR
except Exception:
    DEFAULT_COLOR = discord.Color.gold()


def _format_value(value: int | float) -> str:
    return fmt_short(value)


def _format_cell_value(label: str, value: Any) -> str:
    if value is None or value == "":
        return "-"
    if label in {"% K/T", "% Kill Target"}:
        try:
            return f"{float(value):.0f}%"
        except Exception:
            return "-"
    if isinstance(value, str):
        return value
    try:
        return fmt_short(value)
    except Exception:
        return str(value)


def _fit_cell(value: Any, width: int, *, right: bool = False) -> str:
    text = " ".join(str(value).replace("`", "'").split())
    if len(text) > width:
        text = text[: max(1, width - 1)].rstrip() + "."
    return text.rjust(width) if right else text.ljust(width)


def _support_columns(payload: RankingPayload) -> tuple[str, ...]:
    if payload.mode == "kvk":
        return ("Power", "Kills", "% K/T", "Deads", "DKP")
    if payload.mode == "prekvk":
        return ("Power", "Stage 1", "Stage 2", "Stage 3", "Overall")
    return ()


def _current_rankings_description(payload: RankingPayload) -> str:
    if not payload.rows:
        return payload.empty_message or "No matching players found."

    support_columns = _support_columns(payload)
    rank_w = 4
    name_w = 13 if len(support_columns) >= 5 else 18
    value_w = 9
    support_w = 8

    header = (
        f"{'Rank':<{rank_w}} " f"{'Name':<{name_w}} " f"{payload.metric_label[:value_w]:>{value_w}}"
    )
    for label in support_columns:
        header += f" {label[:support_w]:>{support_w}}"

    lines = [header, "-" * len(header)]
    for row in payload.rows:
        prefix = f"*{row.rank}" if row.rank <= 3 else f"{row.rank}."
        line = (
            f"{_fit_cell(prefix, rank_w)} "
            f"{_fit_cell(row.governor_name, name_w)} "
            f"{_fit_cell(_format_cell_value(payload.metric_label, row.value), value_w, right=True)}"
        )
        for label in support_columns:
            value = row.supporting_values.get(label)
            line += f" {_fit_cell(_format_cell_value(label, value), support_w, right=True)}"
        lines.append(line)
    return "```\n" + "\n".join(lines) + "\n```"


def _kvk_label(kvk_no: int | None, kvk_name: str | None) -> str:
    if kvk_no is None:
        return "KVK unknown"
    if kvk_name:
        return f"KVK {kvk_no} - {kvk_name}"
    return f"KVK {kvk_no}"


def build_current_rankings_embed(
    payload: RankingPayload,
    *,
    color: discord.Color | int = DEFAULT_COLOR,
) -> discord.Embed:
    mode_label = payload.mode_label or payload.mode.upper()
    kvk_suffix = f" - KVK {payload.kvk_no}" if payload.kvk_no is not None else ""
    embed = discord.Embed(
        title=f"{mode_label} Rankings{kvk_suffix} - Top {payload.limit} {payload.metric_label}",
        description=_current_rankings_description(payload),
        color=color if isinstance(color, int) else color,
    )
    footer_parts = [f"Sorted by: {payload.metric_label}"]
    if payload.total_rows is not None:
        shown = min(payload.limit, len(payload.rows))
        footer_parts.append(f"Showing: {shown} of {payload.total_rows}")
    else:
        footer_parts.append(f"Showing: Top {payload.limit}")
    if payload.freshness_label:
        footer_parts.append(f"Last refreshed: {payload.freshness_label}")
    if payload.source_note:
        footer_parts.append(payload.source_note)
    if payload.filters:
        footer_parts.append("Filters: " + ", ".join(payload.filters))
    if payload.source_state not in {"fresh", "empty"}:
        footer_parts.append(f"Source: {payload.source_state}")
    embed.set_footer(text=" | ".join(footer_parts))
    return embed


def build_hall_of_fame_embed(
    payload: RankingPayload,
    *,
    color: discord.Color | int = DEFAULT_COLOR,
) -> discord.Embed:
    if not payload.rows:
        description = "No qualifying records found for this metric yet."
    else:
        lines = []
        for row in payload.rows:
            lines.append(
                f"**#{row.rank}** **{row.governor_name}** - "
                f"{_format_value(row.value)}\n"
                f"`{_kvk_label(row.kvk_no, row.kvk_name)}`"
            )
        description = "\n".join(lines)

    embed = discord.Embed(
        title=f"KD98 Hall of Fame - Top {payload.limit} {payload.metric_label}",
        description=description,
        color=color if isinstance(color, int) else color,
    )
    footer_parts = [
        "Single-KVK performances only",
        "Same governor may appear more than once",
    ]
    if payload.source_note:
        footer_parts.append(payload.source_note)
    embed.set_footer(text=" | ".join(footer_parts))
    return embed
