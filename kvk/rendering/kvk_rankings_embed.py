from __future__ import annotations

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


def _kvk_label(kvk_no: int | None, kvk_name: str | None) -> str:
    if kvk_no is None:
        return "KVK unknown"
    if kvk_name:
        return f"KVK {kvk_no} - {kvk_name}"
    return f"KVK {kvk_no}"


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

