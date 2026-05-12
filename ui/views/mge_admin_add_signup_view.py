from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import logging

import discord

from core.interaction_safety import send_ephemeral
from ui.views.ark_fuzzy_select_view import ArkFuzzySelectView

logger = logging.getLogger(__name__)


def _target_utils():
    from target_utils import (
        _name_cache,
        lookup_governor_id,
        refresh_name_cache_from_sql,
        sync_refresh_worker,
    )

    return _name_cache, lookup_governor_id, refresh_name_cache_from_sql, sync_refresh_worker


async def _ensure_name_cache_ready() -> None:
    """Ensure the governor name cache is populated for fuzzy lookup."""
    try:
        _name_cache, _, refresh_name_cache_from_sql, sync_refresh_worker = _target_utils()
        rows = (_name_cache or {}).get("rows") if isinstance(_name_cache, dict) else []
        if rows:
            return
        await refresh_name_cache_from_sql()
        _name_cache, _, _, sync_refresh_worker = _target_utils()
        rows = (_name_cache or {}).get("rows") if isinstance(_name_cache, dict) else []
        if rows:
            return
        await asyncio.to_thread(sync_refresh_worker)
    except Exception:
        logger.exception("mge_admin_add_ensure_name_cache_ready_failed")


def _fallback_substring_matches(query: str, limit: int = 25) -> list[dict[str, str]]:
    _name_cache, _, _, _ = _target_utils()
    q = (query or "").strip().lower()
    if not q:
        return []
    rows = (_name_cache or {}).get("rows") if isinstance(_name_cache, dict) else []
    matches: list[dict[str, str]] = []
    for row in rows:
        name = str(row.get("GovernorName") or "").strip()
        if not name:
            continue
        if q in name.lower():
            matches.append(
                {
                    "GovernorName": name,
                    "GovernorID": str(row.get("GovernorID") or ""),
                }
            )
            if len(matches) >= limit:
                break
    return matches


def _fallback_governor_id_matches(query: str, limit: int = 25) -> list[dict[str, str]]:
    _name_cache, _, _, _ = _target_utils()
    q = (query or "").strip()
    if not q:
        return []
    rows = (_name_cache or {}).get("rows") if isinstance(_name_cache, dict) else []
    matches: list[dict[str, str]] = []
    for row in rows:
        gid = str(row.get("GovernorID") or "").strip()
        name = str(row.get("GovernorName") or "").strip() or "Unknown"
        if not gid:
            continue
        if q in gid:
            matches.append({"GovernorName": name, "GovernorID": gid})
            if len(matches) >= limit:
                break
    return matches


def _build_fuzzy_embed(query: str, matches: list[dict[str, str]]) -> discord.Embed:
    max_lines = 15
    lines = [f"• **{m['GovernorName']}** — `{m['GovernorID']}`" for m in matches[:max_lines]]
    more = len(matches) - max_lines
    desc = f"OPTIONS MATCHING **{query.upper()}**\n\n" + "\n".join(lines)
    if more > 0:
        desc += f"\n…and **{more}** more."
    return discord.Embed(
        title="Governor Name Search Results",
        description=desc,
        color=discord.Color.blue(),
    )


class MgeAdminAddLookupModal(discord.ui.Modal):
    """Governor lookup modal for MGE admin-add signup flow."""

    def __init__(
        self,
        *,
        author_id: int,
        on_governor_selected: Callable[[discord.Interaction, int, str], Awaitable[None]],
    ) -> None:
        super().__init__(title="Admin Add Signup — Governor Lookup")
        self.author_id = int(author_id)
        self._on_governor_selected = on_governor_selected

        self.add_item(
            discord.ui.InputText(
                label="Governor name or ID",
                placeholder="Enter governor name or numeric GovernorID",
                style=discord.InputTextStyle.short,
                max_length=64,
            )
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Resolve the submitted governor query into a selected governor."""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ You can't use someone else's modal.", ephemeral=True
            )
            return

        raw = str(self.children[0].value or "").strip()
        if not raw:
            await interaction.response.send_message("❌ Name is required.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        await _ensure_name_cache_ready()

        if raw.isdigit():
            _name_cache, _, _, _ = _target_utils()
            exact = next(
                (
                    row
                    for row in (
                        (_name_cache or {}).get("rows") if isinstance(_name_cache, dict) else []
                    )
                    if str(row.get("GovernorID") or "").strip() == raw
                ),
                None,
            )
            if exact is not None:
                await self._on_governor_selected(
                    interaction,
                    int(raw),
                    str(exact.get("GovernorName") or "Unknown"),
                )
                return

            matches = _fallback_governor_id_matches(raw)
            if matches:
                await self._send_fuzzy_selector(interaction, raw, matches)
                return

            await send_ephemeral(
                interaction,
                "❌ GovernorID not found in name cache. Please verify the ID.",
            )
            return

        lookup_governor_id = _target_utils()[1]
        result = await lookup_governor_id(raw)
        status = str((result or {}).get("status") or "").strip().lower()
        if status == "not_found":
            await _ensure_name_cache_ready()
            lookup_governor_id = _target_utils()[1]
            result = await lookup_governor_id(raw)
            status = str((result or {}).get("status") or "").strip().lower()

        if status == "found":
            data = result.get("data") or {}
            governor_id = int(data.get("GovernorID"))
            governor_name = str(data.get("GovernorName") or "Unknown")
            await self._on_governor_selected(interaction, governor_id, governor_name)
            return

        matches = result.get("matches") or [] if isinstance(result, dict) else []
        if status == "fuzzy_matches" and matches:
            normalized = [
                {
                    "GovernorID": str(m.get("GovernorID") or ""),
                    "GovernorName": str(m.get("GovernorName") or "Unknown"),
                }
                for m in matches
                if str(m.get("GovernorID") or "").strip()
            ]
            await self._send_fuzzy_selector(interaction, raw, normalized)
            return

        fallback = _fallback_substring_matches(raw)
        if fallback:
            await self._send_fuzzy_selector(interaction, raw, fallback)
            return

        await send_ephemeral(interaction, (result or {}).get("message", "No matches found."))

    async def _send_fuzzy_selector(
        self,
        interaction: discord.Interaction,
        query: str,
        matches: list[dict[str, str]],
    ) -> None:
        """Send a fuzzy-match selector and continue when a governor is chosen."""

        async def _apply(inter: discord.Interaction, picked_id: str) -> None:
            picked_name = next(
                (
                    str(match.get("GovernorName") or "Unknown")
                    for match in matches
                    if str(match.get("GovernorID") or "") == str(picked_id)
                ),
                "Unknown",
            )
            await self._on_governor_selected(inter, int(picked_id), picked_name)

        embed = _build_fuzzy_embed(query, matches)
        view = ArkFuzzySelectView(matches, interaction.user.id, _apply)
        await view.send_followup(interaction, embed)
