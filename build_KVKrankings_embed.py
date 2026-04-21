# build_KVKrankings_embed.py
from __future__ import annotations

import string
from typing import Any
import unicodedata

import discord

# Import project standard formatter
from utils import fmt_short

# Optional color/emoji fallbacks (use your constants if available)
try:
    from constants import INFO_COLOR

    DEFAULT_COLOR = INFO_COLOR
except Exception:
    DEFAULT_COLOR = discord.Color.gold()

_ALLOWED_NAME_CHARS = set(string.ascii_letters + string.digits + " ._-")


def _sanitize_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = "".join(ch if ch in _ALLOWED_NAME_CHARS else " " for ch in ascii_only)
    cleaned = " ".join(cleaned.split())
    return cleaned or "?"


def _to_int(v: Any, default: int = 0) -> int:
    """
    Safely convert value to int.

    Handles None, empty strings, numeric strings, and float-like strings.
    Returns default if conversion fails.
    """
    try:
        if v is None or v == "":
            return default
        return int(float(v))
    except Exception:
        return default


def _to_float(v: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float.

    Handles None, empty strings, and numeric strings.
    Returns default if conversion fails.
    """
    try:
        if v is None or v == "":
            return default
        return float(v)
    except Exception:
        return default


# === Safe field getters ===


def _safe_get_power(r: dict) -> int:
    """
    Get power from cache.

    Stat cache uses 'Starting Power' field.
    Falls back to 'Power' for compatibility.
    Returns 0 if both missing.
    """
    return _to_int(r.get("Starting Power") or r.get("Power") or 0)


def _safe_get_kills(r: dict) -> int:
    """
    Get T4+T5 kills.

    Prefers 'T4&T5_Kills' field.
    Falls back to sum of 'T4_Kills' + 'T5_Kills'.
    Returns 0 if all missing.
    """
    total = _to_int(r.get("T4&T5_Kills"))
    if total == 0:
        total = _to_int(r.get("T4_Kills")) + _to_int(r.get("T5_Kills"))
    return total


def _safe_get_deads(r: dict) -> int:
    """
    Get deads delta.

    Uses 'Deads_Delta' field.
    Falls back to 'Deads' for compatibility.
    Returns 0 if both missing.
    """
    return _to_int(r.get("Deads_Delta") or r.get("Deads") or 0)


def _safe_get_dkp(r: dict) -> float:
    """
    Get DKP score.

    Supports both 'DKP_SCORE' and 'DKP Score' field variants.
    Returns 0.0 if both missing.
    """
    return _to_float(r.get("DKP_SCORE") or r.get("DKP Score") or 0.0)


def _safe_get_pct_kill_target(r: dict) -> float:
    """
    Get % of kill target (already calculated in cache).

    Uses '% of Kill Target' field.
    Returns 0.0 if missing.
    """
    return _to_float(r.get("% of Kill Target") or 0.0)


def _get_sort_indicator(column: str, active_metric: str) -> str:
    """
    Return Excel-style sort indicator for column header.

    Returns:
        "▼" if this column is actively sorted, "" otherwise
    """
    return "▼" if column == active_metric else ""


def _value_getter(metric: str):
    """
    Returns (label, getter, formatter) tuple for a given metric.

    Supported metrics:
    - "power": Starting Power
    - "kills": T4&T5_Kills
    - "pct_kill_target": % of Kill Target
    - "deads": Deads_Delta
    - "dkp": DKP_SCORE

    Defaults to "power" for PR2+ (changed from "kills" in PR1).

    Returns:
        tuple: (label: str, getter: callable, formatter: callable)
    """
    m = (metric or "power").lower()

    if m == "power":
        return ("Power", _safe_get_power, fmt_short)

    if m == "kills":
        return ("Kills (T4+T5)", _safe_get_kills, fmt_short)

    if m == "pct_kill_target":
        # Special formatter for percentage
        return ("% Kill Target", _safe_get_pct_kill_target, lambda x: f"{x:.0f}%")

    if m == "deads":
        return ("Deads", _safe_get_deads, fmt_short)

    if m == "dkp":
        return ("DKP", _safe_get_dkp, fmt_short)

    # Default: power
    return ("Power", _safe_get_power, fmt_short)


def _display_width(s: str) -> int:
    """
    Compute rendered display width for a monospaced context.

    In this module, names are sanitized to ASCII before calling this
    function, so the effective behavior is to return an approximate
    column width for ASCII text. The implementation is Unicode-aware
    for potential future use but callers should not rely on precise
    handling of East Asian wide characters here.
    """
    width = 0
    for ch in s:
        if unicodedata.combining(ch):
            continue
        width += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return width


def _fit_name(name: str, width: int) -> str:
    """
    Sanitize and fit name to a fixed display width.

    Uses _display_width to account for wide characters. If truncated, append a single
    ellipsis character (unicode HORIZONTAL ELLIPSIS) to indicate truncation.
    """
    safe = _sanitize_name(name)
    if _display_width(safe) > width:
        # Truncate while preserving display width
        truncated = ""
        cur_w = 0
        for ch in safe:
            ch_w = 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
            if cur_w + ch_w >= width:  # leave room for ellipsis
                break
            truncated += ch
            cur_w += ch_w
        return truncated + "…"
    # Pad to width using simple spaces - monospaced code block will align
    # Use naive length pad (monospace characters assumed)
    pad_len = max(0, width - _display_width(safe))
    return safe + (" " * pad_len)


def filter_rows_for_leaderboard(
    rows: list[dict[str, Any]],
    *,
    required_status: str = "INCLUDED",
    min_power: int = 40_000_000,
) -> list[dict[str, Any]]:
    """
    Apply the same filtering used by the embed builder.

    Only rows with STATUS matching required_status (case-insensitive) and
    with Starting Power (or Power) >= min_power will be included.

    This helper exists so callers (e.g., KVKRankingView in Commands.py) can
    compute pages and UI state using the exact same dataset as the embed.
    """
    if not rows:
        return []
    req = (required_status or "").upper()
    return [
        r
        for r in rows
        if (not req or str(r.get("STATUS", "")).upper() == req) and _safe_get_power(r) >= min_power
    ]


def build_kvkrankings_embed(
    rows: list[dict[str, Any]],
    metric: str = "power",
    limit: int = 10,
    *,
    page: int = 1,
    color: discord.Color | int = DEFAULT_COLOR,
    apply_filter: bool = True,
    required_status: str = "INCLUDED",
    min_power: int = 40_000_000,
) -> discord.Embed:
    """
    Build multi-column KVK leaderboard embed with compact fixed-width columns.

    This keeps each line short enough to avoid wrapping in Discord embeds.

    Parameters:
    - rows: list of player stat dicts
    - metric: metric key to sort by ("power", "kills", "pct_kill_target", "deads", "dkp")
    - limit: max number of players to consider (slicing occurs before pagination)
    - page: 1-based page number for paged responses (50 rows per page)
    - color: embed color
    - apply_filter: whether to apply the default STATUS/min_power filter (True by default)
    - required_status: status string that must match row['STATUS'] (case-insensitive)
    - min_power: minimum power threshold to include a player
    """
    # Determine sort key
    label, getter, _ = _value_getter(metric)

    # Filtering (configurable)
    candidate_rows = rows or []
    if apply_filter:
        candidate_rows = filter_rows_for_leaderboard(
            candidate_rows, required_status=required_status, min_power=min_power
        )

    # Sort: primary by metric (desc), tiebreaker by power (desc)
    sorted_rows = sorted(candidate_rows, key=lambda r: (-getter(r), -_safe_get_power(r)))[:limit]

    # Pagination (50 per page)
    PAGE_SIZE = 50
    total_pages = max(1, (len(sorted_rows) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * PAGE_SIZE
    end_idx = min(start_idx + PAGE_SIZE, len(sorted_rows))
    page_rows = sorted_rows[start_idx:end_idx]

    # ---- Compact column widths (tuned to avoid wrap) ----
    RANK_W = 4
    NAME_W = 11
    POWER_W = 7
    KILLS_W = 7
    PCT_W = 5  # increased to avoid misleading truncation
    DEADS_W = 7
    DKP_W = 7

    def _fit_cell(val: str, width: int) -> str:
        s = str(val)
        # Special handling for percentage values to avoid misleading truncation.
        # For values like "1000%" with a small column width, we cap the display
        # to a maximum (e.g., "999%+") instead of truncating from the left.
        if s.endswith("%") and len(s) > width:
            # Extract numeric portion
            num_part = s[:-1]
            # If numeric, cap display like "999%+"
            if num_part.replace(".", "").isdigit() and width >= 3:
                digit_count = max(1, width - 2)  # leave space for "%+"
                capped_digits = "9" * digit_count
                return f"{capped_digits}%+"
        return s[-width:] if len(s) > width else s

    # Short headers + sort indicator
    power_hdr = "Power" + _get_sort_indicator("power", metric)
    kills_hdr = "Kills" + _get_sort_indicator("kills", metric)
    pct_hdr = "% K/T" + _get_sort_indicator("pct_kill_target", metric)
    deads_hdr = "Dead" + _get_sort_indicator("deads", metric)
    dkp_hdr = "DKP" + _get_sort_indicator("dkp", metric)

    header_line = (
        f"{'Rank':<{RANK_W}} "
        f"{'Name':<{NAME_W}} "
        f"{power_hdr:>{POWER_W}} "
        f"{kills_hdr:>{KILLS_W}} "
        f"{pct_hdr:>{PCT_W}} "
        f"{deads_hdr:>{DEADS_W}} "
        f"{dkp_hdr:>{DKP_W}}"
    )

    # Build player lines
    # medals removed intentionally — use compact ASCII rank indicator for alignment
    lines = [header_line, "─" * len(header_line)]

    for idx, r in enumerate(page_rows, start=start_idx + 1):
        # Rank: fixed-width ASCII for alignment
        if idx <= 3:
            rank_str = f"*{idx}"  # highlight top 3 without emoji
        else:
            rank_str = f"{idx}."

        name = r.get("GovernorName") or str(r.get("GovernorID")) or "???"
        name = _fit_name(name, NAME_W)

        power = _fit_cell(fmt_short(_safe_get_power(r)), POWER_W)
        kills = _fit_cell(fmt_short(_safe_get_kills(r)), KILLS_W)
        pct_target = _fit_cell(f"{_safe_get_pct_kill_target(r):.0f}%", PCT_W)
        deads = _fit_cell(fmt_short(_safe_get_deads(r)), DEADS_W)
        dkp = _fit_cell(fmt_short(_safe_get_dkp(r)), DKP_W)

        line = (
            f"{rank_str:<{RANK_W}} "
            f"{name:<{NAME_W}} "
            f"{power:>{POWER_W}} "
            f"{kills:>{KILLS_W}} "
            f"{pct_target:>{PCT_W}} "
            f"{deads:>{DEADS_W}} "
            f"{dkp:>{DKP_W}}"
        )
        lines.append(line)

    description = "```\n" + "\n".join(lines) + "\n```"

    title_map = {
        "power": "Top Power",
        "kills": "Top Kills",
        "pct_kill_target": "Top % Kill Target",
        "deads": "Top Deads",
        "dkp": "Top DKP",
    }
    title = title_map.get(metric, "Leaderboard")

    page_info = f" • Page {page}/{total_pages}" if total_pages > 1 else ""

    embed = discord.Embed(
        title=f"🏆 {title} — Current KVK{page_info}",
        description=description,
        color=color if isinstance(color, int) else color,
    )

    footer_parts = [f"Sorted by: {label} (Descending)"]
    if limit > 50 and total_pages > 1:
        footer_parts.append(f"Showing: {start_idx + 1}-{end_idx} of {limit}")
    else:
        footer_parts.append(f"Showing: Top {limit}")

    last_ref = _get_last_refresh(sorted_rows)
    if last_ref:
        footer_parts.append(f"Last refreshed: {last_ref}")

    embed.set_footer(text=" • ".join(footer_parts))
    return embed


def _get_last_refresh(rows: list[dict]) -> str | None:
    """
    Extract most recent LAST_REFRESH from rows.

    Args:
        rows: List of player stat dicts

    Returns:
        Max LAST_REFRESH value as string, or None if not available
    """
    try:
        candidates = [str(r.get("LAST_REFRESH") or "") for r in rows if r.get("LAST_REFRESH")]
        return max(candidates) if candidates else None
    except Exception:
        return None
