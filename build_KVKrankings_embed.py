# build_KVKrankings_embed.py
from __future__ import annotations

from typing import Any

import discord

# Optional color/emoji fallbacks (use your constants if available)
try:
    from constants import INFO_COLOR

    DEFAULT_COLOR = INFO_COLOR
except Exception:
    DEFAULT_COLOR = discord.Color.gold()


def _to_int(v: Any, default: int = 0) -> int:
    try:
        if v is None or v == "":
            return default
        return int(float(v))
    except Exception:
        return default


def _to_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None or v == "":
            return default
        return float(v)
    except Exception:
        return default


def _fmt_int(n: int) -> str:
    return f"{n:,}"


def _fmt_float(n: float) -> str:
    s = f"{n:,.2f}"
    return s.rstrip("0").rstrip(".") if "." in s else s


def _value_getter(metric: str):
    """
    Returns (label, getter, formatter).
    """
    m = (metric or "kills").lower()
    if m == "deads":
        return (
            "Deads",
            lambda r: _to_int(r.get("Deads")),
            _fmt_int,
        )
    if m == "dkp":
        # support both DKP Score and DKP_SCORE
        return (
            "DKP",
            lambda r: _to_float(r.get("DKP Score") or r.get("DKP_SCORE")),
            _fmt_float,
        )

    # default: kills
    def _kills(r: dict[str, Any]) -> int:
        total = _to_int(r.get("T4&T5_Kills"))
        if total == 0:
            total = _to_int(r.get("T4_Kills")) + _to_int(r.get("T5_Kills"))
        return total

    return ("Kills (T4+T5)", _kills, _fmt_int)


def build_kvkrankings_embed(
    rows: list[dict[str, Any]],
    metric: str = "kills",
    limit: int = 10,
    *,
    color: discord.Color | int = DEFAULT_COLOR,
) -> discord.Embed:
    """
    Build the leaderboard embed given raw cache rows (list of dicts).
    Sort: metric desc, then Power asc.
    """
    label, getter, fmt_val = _value_getter(metric)

    sorted_rows = sorted(rows, key=lambda r: (-getter(r), _to_int(r.get("Power"))))[:limit]

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    lines: list[str] = []
    for idx, r in enumerate(sorted_rows, start=1):
        prefix = medals.get(idx, f"{idx:>2}.")
        name = (r.get("GovernorName") or str(r.get("GovernorID")) or "Unknown").strip()
        lines.append(f"{prefix} **{name}** — {fmt_val(getter(r))}")

    # last refreshed: prefer max LAST_REFRESH in set, else omit (Commands can add fallback)
    last_ref = None
    try:
        candidates = [
            str(r.get("LAST_REFRESH") or "") for r in sorted_rows if r.get("LAST_REFRESH")
        ]
        last_ref = max(candidates) if candidates else None
    except Exception:
        pass

    title_map = {"kills": "Top Kills", "deads": "Top Deads", "dkp": "Top DKP"}
    title = title_map.get((metric or "kills").lower(), "Top Kills")

    embed = discord.Embed(
        title=f"🏆 {title} — Current KVK",
        description="\n".join(lines) if lines else "No matching players found.",
        color=color if isinstance(color, int) else color,
    )
    embed.add_field(name="Metric", value=label, inline=True)
    embed.add_field(name="Shown", value=f"Top {limit}", inline=True)
    if last_ref:
        embed.set_footer(text=f"Last refreshed: {last_ref}")
    return embed
