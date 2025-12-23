# targets_embed.py
from __future__ import annotations

import re
from typing import Any

import discord

# Helpers (with safe fallbacks)
try:
    # embed_utils.py provides fmt_short which is the canonical short-number formatter in repo
    from embed_utils import brand_color, fmt_short as format_number_short
except Exception:

    def brand_color() -> int:
        return 0x2B6CB0

    def format_number_short(v) -> str:
        try:
            x = float(v)
        except Exception:
            return str(v) if v is not None else "—"
        ax = abs(x)
        if ax >= 1_000_000_000:
            return f"{x/1_000_000_000:.2f}B"
        if ax >= 1_000_000:
            return f"{x/1_000_000:.2f}M"
        if ax >= 1_000:
            return f"{x/1_000:.2f}K"
        try:
            return f"{int(x):,}"
        except Exception:
            return str(v)


# Robust constants import (avoid all-or-nothing failures)
try:
    import constants as _C
except Exception:
    _C = object()

CUSTOM_AVATAR_URL = getattr(_C, "CUSTOM_AVATAR_URL", None)

# Normalize KVK banner map to lowercase keys
_KBM = getattr(_C, "KVK_BANNER_MAP", {}) or {}
KVK_BANNER_MAP = {str(k).lower(): v for k, v in _KBM.items()}
SHOW_KVK_BANNER = bool(getattr(_C, "SHOW_KVK_BANNER", False))

# State assets can be a custom emoji tag "<:name:id>" OR a URL (ignored for header text)
DRAFT_TARGET_EMOJI = getattr(_C, "DRAFT_TARGET_EMOJI", None)
ACTIVE_TARGET_EMOJI = getattr(_C, "ACTIVE_TARGET_EMOJI", None)
HISTORIC_TARGET_EMOJI = getattr(_C, "HISTORIC_TARGET_EMOJI", None)

_EMOJI_TAG = re.compile(r"^<a?:\w+:\d+>$", re.IGNORECASE)


def _state_assets_for_header(state: str | None) -> tuple[str, str | None]:
    """
    Returns (emoji_text_for_header, author_icon_url_if_any).
    - If constant is a Discord custom emoji tag (<:name:id>), use inline in header text.
    - If it's a URL, return it as author icon (header shows no inline emoji).
    - Otherwise, fallback to neat Unicode emoji inline.
    """
    s = (state or "").upper()
    raw = {
        "DRAFT": DRAFT_TARGET_EMOJI,
        "ACTIVE": ACTIVE_TARGET_EMOJI,
        "ENDED": HISTORIC_TARGET_EMOJI,
    }.get(s)

    if isinstance(raw, str):
        val = raw.strip()
        if _EMOJI_TAG.match(val):  # e.g. "<:draft_target:123...>"
            return (val + " ", None)  # inline emoji
        if val.lower().startswith(("http://", "https://", "attachment://")):
            return ("", val)  # small author icon

    # Unicode fallbacks (inline)
    return {
        "DRAFT": ("🧪 ", None),
        "ACTIVE": ("✅ ", None),
        "ENDED": ("📜 ", None),
    }.get(s, ("✅ ", None))


def _state_color(state: str | None) -> int:
    s = (state or "").upper()
    return {"DRAFT": 0x2563EB, "ACTIVE": 0x16A34A, "ENDED": 0x334155}.get(s, brand_color())


def _state_label(state: str | None) -> str:
    return {"DRAFT": "Draft", "ACTIVE": "Active", "ENDED": "Ended"}.get(
        (state or "").upper(), "Active"
    )


def _maybe_banner(kvk_name: str | None) -> str | None:
    if not SHOW_KVK_BANNER or not kvk_name:
        return None
    return KVK_BANNER_MAP.get(str(kvk_name).lower())


def build_kvk_targets_embed(
    gov_name: str,
    governor_id: int | str,
    targets: dict[str, Any],
    kvk_name: str | None,
) -> discord.Embed:
    """
    Build a KVK targets embed.

    Inputs:
      - gov_name: display name of the governor
      - governor_id: numeric or string ID (will be coerced to str)
      - targets: mapping with target values. Keys in incoming data may be "DKP_Target",
                 "DKP Target", "Kill_Target", "Kill Target", etc. This function normalises
                 keys (lowercase, spaces -> underscores) to be tolerant of either form.
      - kvk_name: optional KVK label used to select a banner.

    Returns a discord.Embed ready to send.
    """
    # Defensive normalisation of incoming target keys (case-insensitive; spaces -> underscores)
    norm = {str(k).strip().lower().replace(" ", "_"): v for k, v in (targets or {}).items()}

    state = str(
        norm.get("targetstate") or norm.get("target_state") or norm.get("target") or "ACTIVE"
    ).upper()
    kvk_no = norm.get("kvk_no") or norm.get("kvk")

    # support multiple key naming variants
    dkp = norm.get("dkp_target") or norm.get("dkp_target_value") or norm.get("dkp")
    kills = norm.get("kill_target") or norm.get("kill_target_value") or norm.get("kills")
    deads = (
        norm.get("deads_target") or norm.get("dead_target") or norm.get("deads") or norm.get("dead")
    )
    min_k = norm.get("min_kill_target") or norm.get("min_kills")
    power = norm.get("power")

    # Title = big name/id
    governor_id_str = str(governor_id)
    title = f"{gov_name} • {governor_id_str}"
    kvk_label = kvk_name or (f"KVK {kvk_no}" if kvk_no else "KVK")
    color = _state_color(state)
    label = _state_label(state)

    em = discord.Embed(title=title, color=color)

    # High-contrast header in DESCRIPTION
    emoji_text, author_icon = _state_assets_for_header(state)
    header = f"{emoji_text}**{label.upper()}** • **{str(kvk_label).upper()}**"
    em.description = header

    # Optional small author icon if provided as URL
    if author_icon:
        em.set_author(name=" ", icon_url=author_icon)

    # Top-right avatar thumbnail
    if CUSTOM_AVATAR_URL:
        em.set_thumbnail(url=CUSTOM_AVATAR_URL)

    # Primary targets
    em.add_field(name="🎯 DKP Target", value=f"**{format_number_short(dkp)}**", inline=True)

    kill_val = f"**{format_number_short(kills)}**"
    if min_k is not None:
        kill_val += f"\n_Min: {format_number_short(min_k)}_"
    em.add_field(name="⚔️ Kill Target", value=kill_val, inline=True)

    em.add_field(name="💀 Deads Target", value=f"**{format_number_short(deads)}**", inline=True)

    # Meta row (only if content) — zero-width name avoids a visible label
    meta_bits = []
    if power is not None:
        meta_bits.append(f"Matchmaking Power: **{format_number_short(power)}**")
    if kvk_no:
        meta_bits.append(f"KVK: **{kvk_no}**")
    if meta_bits:
        em.add_field(name="\u200b", value=" • ".join(meta_bits), inline=False)

    # Optional banner at bottom
    banner_url = _maybe_banner(kvk_name)
    if banner_url:
        em.set_image(url=banner_url)

    # Footer per state
    foot = {
        "DRAFT": "Draft targets (may change before KVK starts)",
        "ACTIVE": "Official KVK targets",
        "ENDED": "Historical targets",
    }.get(state, "Targets")
    em.set_footer(text=f"GovernorID: {governor_id_str} • {foot}")

    # Set a consistent timezone-aware timestamp (use discord.utils.utcnow or repo utc helper)
    try:
        # prefer repo style (utils.utcnow) if available
        from utils import utcnow as _utcnow

        em.timestamp = _utcnow()
    except Exception:
        # fallback to discord's helper
        em.timestamp = discord.utils.utcnow()

    return em
