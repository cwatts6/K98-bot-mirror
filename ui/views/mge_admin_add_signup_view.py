from __future__ import annotations

from collections.abc import Awaitable, Callable
import logging

import discord

from core.interaction_safety import send_ephemeral
from services.governor_lookup_service import resolve_governor_query
from ui.views.ark_fuzzy_select_view import ArkFuzzySelectView

logger = logging.getLogger(__name__)


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
        result = await resolve_governor_query(raw)

        if result.status == "found":
            governor_id = int(result.governor_id or 0)
            governor_name = str(result.governor_name or "Unknown")
            await self._on_governor_selected(interaction, governor_id, governor_name)
            return

        if result.status == "matches" and result.matches:
            matches = [
                {
                    "GovernorID": str(m.get("GovernorID") or ""),
                    "GovernorName": str(m.get("GovernorName") or "Unknown"),
                }
                for m in result.matches
                if str(m.get("GovernorID") or "").strip()
            ]
            await self._send_fuzzy_selector(interaction, raw, matches)
            return

        await send_ephemeral(interaction, result.message)

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
