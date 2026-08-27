from __future__ import annotations

import discord

from kvk.models.kvk_targets_card import KvkTargetsCardPayload
from kvk.services.kvk_target_publication_service import target_publication_display
from kvk.theme import normalize_kvk_mode

try:
    import constants as _constants
except Exception:
    _constants = object()

_banner_map = getattr(_constants, "KVK_BANNER_MAP", {}) or {}
KVK_BANNER_MAP = {normalize_kvk_mode(key): value for key, value in _banner_map.items()}
SHOW_KVK_BANNER = bool(getattr(_constants, "SHOW_KVK_BANNER", False))


def _maybe_banner(kvk_name: str | None) -> str | None:
    if not SHOW_KVK_BANNER or not kvk_name:
        return None
    return KVK_BANNER_MAP.get(normalize_kvk_mode(kvk_name))


def _compact(value: int | float | None) -> str:
    if value is None:
        return "N/A"
    numeric = float(value)
    absolute = abs(numeric)
    for limit, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if absolute >= limit:
            return f"{numeric / limit:.1f}".rstrip("0").rstrip(".") + suffix
    return f"{int(numeric):,}"


def _percent(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.1f}".rstrip("0").rstrip(".") + "%"


def build_targets_fallback_embed(payload: KvkTargetsCardPayload) -> discord.Embed:
    """Build the canonical embed fallback from the shared typed presentation payload."""
    publication = target_publication_display(
        payload.publication_state,
        source_scan_order=payload.target_source_scan,
    )
    publication_colors = {
        "DRAFT": 0x2563EB,
        "OFFICIAL": 0x16A34A,
        "HISTORIC": 0x334155,
        "UNKNOWN": 0xD97706,
    }
    embed = discord.Embed(
        title=f"KVK Targets - {payload.governor_name}",
        description=(
            f"**{publication.label} targets** | "
            f"{payload.display_kvk_label} | {payload.display_mode}"
        ),
        color=discord.Color(publication_colors[publication.state]),
    )
    embed.add_field(name="Target Publication", value=publication.source_text, inline=False)
    warning_text = publication.warning_text or (payload.warnings[0] if payload.warnings else None)
    if warning_text:
        embed.add_field(name="Publication Warning", value=warning_text, inline=False)
    embed.add_field(name="Status", value=payload.status_detail, inline=False)
    for metric in payload.metrics:
        if not metric.has_target:
            lines = [_compact(metric.current)]
            if metric.note:
                lines.append(metric.note)
            embed.add_field(name=metric.label, value="\n".join(lines), inline=False)
            continue
        if metric.remaining is None:
            remaining = "progress unavailable"
        elif metric.remaining <= 0:
            remaining = "complete"
        else:
            remaining = f"{_compact(metric.remaining)} remaining"
        embed.add_field(
            name=metric.label,
            value=(
                f"{_compact(metric.current)} / {_compact(metric.target)} - "
                f"{_percent(metric.percent)}\n{remaining}"
            ),
            inline=False,
        )
    embed.add_field(name="Next Action", value=payload.next_action, inline=False)
    footer = f"GovernorID: {payload.governor_id}"
    if payload.target_published_at:
        footer += f" | Published {payload.target_published_at}"
    if payload.last_refreshed:
        footer += f" | Cache {payload.last_refreshed}"
    embed.set_footer(text=footer)
    banner_url = _maybe_banner(payload.kvk_name)
    if banner_url:
        embed.set_image(url=banner_url)
    return embed


def build_kvk_targets_embed(payload: KvkTargetsCardPayload) -> discord.Embed:
    """Compatibility name for callers migrating to the canonical fallback payload."""
    return build_targets_fallback_embed(payload)
