from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import discord

from kvk.models.kvk_rankings import MyRankLookupResult, RankingPayload, RankingRow
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


def _clean_rank_text(value: Any) -> str:
    return " ".join(str(value).replace("`", "'").split())


@dataclass(frozen=True)
class _TableColumn:
    label: str
    key: str
    width: int


def _ranking_columns(payload: RankingPayload) -> tuple[_TableColumn, ...]:
    if payload.mode == "kvk":
        columns = {
            "power": _TableColumn("Power", "Power", 7),
            "kills": _TableColumn("Kills", "Kills", 7),
            "pct_kill_target": _TableColumn("% K/T", "% K/T", 5),
            "deads": _TableColumn("Dead", "Deads", 7),
            "dkp": _TableColumn("DKP", "DKP", 7),
        }
        order = (payload.metric, "power", "kills", "pct_kill_target", "deads", "dkp")
        return tuple(columns[metric] for metric in dict.fromkeys(order) if metric in columns)
    if payload.mode == "prekvk":
        columns = {
            "power": _TableColumn("Power", "Power", 7),
            "stage1": _TableColumn("Stage 1", "Stage 1", 7),
            "stage2": _TableColumn("Stage 2", "Stage 2", 7),
            "stage3": _TableColumn("Stage 3", "Stage 3", 7),
            "overall": _TableColumn("Overall", "Overall", 7),
        }
        order = (payload.metric, "power", "stage1", "stage2", "stage3", "overall")
        return tuple(columns[metric] for metric in dict.fromkeys(order) if metric in columns)
    return ()


def _compact_metric_label(payload: RankingPayload) -> str:
    labels = {
        "kills": "Kills",
        "pct_kill_target": "% K/T",
    }
    return labels.get(payload.metric, payload.metric_label)


def _current_rankings_description(payload: RankingPayload) -> str:
    if not payload.rows:
        return payload.empty_message or "No matching players found."

    columns = _ranking_columns(payload)
    rank_w = 4
    name_w = 11

    header = f"{'Rank':<{rank_w}} " f"{'Name':<{name_w}}"
    for column in columns:
        header += f" {column.label[: column.width]:>{column.width}}"

    lines = [header, "-" * len(header)]
    for row in payload.rows:
        prefix = f"*{row.rank}" if row.rank <= 3 else f"{row.rank}."
        line = f"{_fit_cell(prefix, rank_w)} " f"{_fit_cell(row.governor_name, name_w)}"
        for column in columns:
            value = (
                row.value
                if column.key == _compact_metric_label(payload)
                else row.supporting_values.get(column.key)
            )
            line += f" {_fit_cell(_format_cell_value(column.key, value), column.width, right=True)}"
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


def _my_rank_neighbor_line(row: RankingRow | None) -> str:
    if row is None:
        return "None"
    return f"#{row.rank} {_clean_rank_text(row.governor_name)} - {_format_value(row.value)}"


def build_my_rank_embed(
    result: MyRankLookupResult,
    *,
    color: discord.Color | int = DEFAULT_COLOR,
) -> discord.Embed:
    row = result.row
    title = f"My Rank - {result.mode_label} {result.metric_label}"
    if row is None:
        embed = discord.Embed(
            title=title,
            description=result.message,
            color=color if isinstance(color, int) else color,
        )
        embed.set_footer(text="Private result")
        return embed

    total_suffix = f" of {result.total_rows}" if result.total_rows is not None else ""
    embed = discord.Embed(
        title=title,
        description=(
            f"**{_clean_rank_text(row.governor_name)}** (`{row.governor_id}`) is "
            f"**#{row.rank}{total_suffix}**."
        ),
        color=color if isinstance(color, int) else color,
    )
    embed.add_field(name="Your value", value=_format_value(row.value), inline=True)
    if result.gap_to_next_value is not None:
        embed.add_field(
            name="Gap to next",
            value=_format_value(result.gap_to_next_value),
            inline=True,
        )
    embed.add_field(
        name="Next rank",
        value=(
            _my_rank_neighbor_line(result.row_above)
            if result.row_above is not None
            else "You are at the top."
        ),
        inline=False,
    )
    embed.add_field(
        name="Behind you",
        value=(
            _my_rank_neighbor_line(result.row_below)
            if result.row_below is not None
            else "No ranked row below you."
        ),
        inline=False,
    )

    footer_parts = ["Private result", f"Sorted by: {result.metric_label}"]
    payload = result.payload
    if payload is not None:
        if payload.freshness_label:
            footer_parts.append(f"Last refreshed: {payload.freshness_label}")
        if payload.source_note:
            footer_parts.append(payload.source_note)
        if payload.filters:
            footer_parts.append("Filters: " + ", ".join(payload.filters))
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
