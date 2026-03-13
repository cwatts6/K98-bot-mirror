"""Leadership-only read scaffold for MGE review pool (Task I starter)."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import discord

from mge.mge_review_service import get_review_pool_with_summary

logger = logging.getLogger(__name__)


class MgeLeadershipBoardView(discord.ui.View):
    """Read-only leadership board scaffold (non-destructive)."""

    def __init__(self, *, event_id: int, timeout: float | None = 180) -> None:
        super().__init__(timeout=timeout)
        self.event_id = int(event_id)

    async def _defer_ephemeral(self, interaction: discord.Interaction) -> None:
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

    async def _send_followup(self, interaction: discord.Interaction, content: str) -> None:
        await interaction.followup.send(content, ephemeral=True)

    @discord.ui.button(
        label="Refresh Review Pool",
        style=discord.ButtonStyle.secondary,
        custom_id="mge_lead_refresh_pool",
    )
    async def refresh_pool(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        await self._defer_ephemeral(interaction)

        payload = await asyncio.to_thread(get_review_pool_with_summary, self.event_id)
        rows: list[dict[str, Any]] = payload.get("rows", [])
        summary: dict[str, Any] = payload.get("summary", {})

        msg = (
            f"📋 Leadership review pool refreshed for event `{self.event_id}`\n"
            f"- Applicants: **{summary.get('total_rows', len(rows))}**\n"
            f"- By priority: `{summary.get('by_priority', {})}`\n"
            f"- By commander: `{summary.get('by_commander', {})}`\n"
            f"- By role: `{summary.get('by_role', {})}`\n"
            f"- Warnings: `{summary.get('warnings', {})}`\n\n"
            "This is a read-only scaffold. Roster actions land in Task I."
        )
        await self._send_followup(interaction, msg)

    @discord.ui.button(
        label="Preview Top 10",
        style=discord.ButtonStyle.primary,
        custom_id="mge_lead_preview_top10",
    )
    async def preview_top_10(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        await self._defer_ephemeral(interaction)

        payload = await asyncio.to_thread(get_review_pool_with_summary, self.event_id)
        rows: list[dict[str, Any]] = payload.get("rows", [])
        top = rows[:10]

        if not top:
            await self._send_followup(interaction, "No active signups found for this event.")
            return

        lines: list[str] = []
        for idx, row in enumerate(top, start=1):
            gov = str(row.get("GovernorNameSnapshot") or row.get("GovernorId") or "Unknown")
            commander = str(row.get("RequestedCommanderName") or "Unknown")
            priority = str(row.get("RequestPriority") or "Unknown")
            same_awards = int(row.get("PriorAwardsRequestedCommanderCount") or 0)
            awards_2y = int(row.get("PriorAwardsOverallLast2YearsCount") or 0)
            lines.append(
                f"{idx}. {gov} | {commander} | {priority} | same-cmd={same_awards} | last2y={awards_2y}"
            )

        text = "Top 10 sorted applicants:\n" + "\n".join(lines)
        await self._send_followup(interaction, text)

    @discord.ui.button(
        label="Close",
        style=discord.ButtonStyle.danger,
        custom_id="mge_lead_close_view",
    )
    async def close_view(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        await self._defer_ephemeral(interaction)
        self.stop()
        await self._send_followup(interaction, "Closed leadership board view.")
