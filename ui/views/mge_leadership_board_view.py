"""Leadership board + Task-I roster builder launcher."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import discord

from core.interaction_safety import send_ephemeral
from mge.mge_review_service import get_review_pool_with_summary
from ui.views.mge_publish_view import MgePublishView
from ui.views.mge_roster_builder_view import MgeRosterBuilderView

logger = logging.getLogger(__name__)


class MgeLeadershipBoardView(discord.ui.View):
    """Leadership board view with summary refresh + roster builder launch."""

    def __init__(self, *, event_id: int, timeout: float | None = 180) -> None:
        super().__init__(timeout=timeout)
        self.event_id = int(event_id)

    @discord.ui.button(
        label="Refresh Review Pool",
        style=discord.ButtonStyle.secondary,
        custom_id="mge_lead_refresh_pool",
    )
    async def refresh_pool(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        payload = await asyncio.to_thread(get_review_pool_with_summary, self.event_id)
        rows: list[dict[str, Any]] = payload.get("rows", [])
        summary: dict[str, Any] = payload.get("summary", {})

        msg = (
            f"📋 Leadership review pool refreshed for event `{self.event_id}`\n"
            f"- Applicants: **{summary.get('total_rows', len(rows))}**\n"
            f"- By priority: `{summary.get('by_priority', {})}`\n"
            f"- By commander: `{summary.get('by_commander', {})}`\n"
            f"- By role: `{summary.get('by_role', {})}`"
        )
        await send_ephemeral(interaction, msg)

    @discord.ui.button(
        label="Preview Top 10",
        style=discord.ButtonStyle.primary,
        custom_id="mge_lead_preview_top10",
    )
    async def preview_top_10(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        payload = await asyncio.to_thread(get_review_pool_with_summary, self.event_id)
        rows: list[dict[str, Any]] = payload.get("rows", [])
        top = rows[:10]

        if not top:
            await send_ephemeral(interaction, "No active signups found for this event.")
            return

        header = (
            "Top 10 sorted applicants:\n"
            "Gov | Commander | Priority | KVK last→latest | "
            "T4/T5 last→latest | %Target last→latest | same-cmd | last2y"
        )

        lines: list[str] = []
        for idx, row in enumerate(top, start=1):
            gov = str(
                row.get("GovernorNameDisplay")
                or row.get("GovernorNameSnapshot")
                or row.get("GovernorId")
                or "Unknown"
            )
            commander = str(
                row.get("CommanderNameDisplay") or row.get("RequestedCommanderName") or "Unknown"
            )
            priority = str(row.get("PriorityDisplay") or row.get("RequestPriority") or "Unknown")
            latest_kvk = row.get("LatestKVKRank")
            last_kvk = row.get("LastKVKRank")
            latest_kills = row.get("LatestT4T5Kills")
            last_kills = row.get("LastT4T5Kills")
            latest_pct = row.get("LatestPercentOfKillTarget")
            last_pct = row.get("LastPercentOfKillTarget")
            same_awards = int(row.get("PriorAwardsRequestedCommanderCount") or 0)
            awards_2y = int(row.get("PriorAwardsOverallLast2YearsCount") or 0)

            lines.append(
                f"{idx}. {gov} | {commander} | {priority} | "
                f"{last_kvk if last_kvk is not None else '—'}→{latest_kvk if latest_kvk is not None else '—'} | "
                f"{last_kills if last_kills is not None else '—'}→{latest_kills if latest_kills is not None else '—'} | "
                f"{last_pct if last_pct is not None else '—'}→{latest_pct if latest_pct is not None else '—'} | "
                f"{same_awards} | {awards_2y}"
            )

        text = header + "\n" + "\n".join(lines)
        await send_ephemeral(interaction, text)

    @discord.ui.button(
        label="Open Roster Builder",
        style=discord.ButtonStyle.success,
        custom_id="mge_lead_open_roster_builder",
    )
    async def open_roster_builder(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        view = MgeRosterBuilderView(
            event_id=self.event_id,
            actor_discord_id=int(interaction.user.id),
        )
        await send_ephemeral(
            interaction,
            f"🧭 Roster builder opened for event `{self.event_id}`.",
            view=view,
        )

    @discord.ui.button(
        label="Open Publish Panel",
        style=discord.ButtonStyle.success,
        custom_id="mge_lead_open_publish_panel",
    )
    async def open_publish_panel(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        view = MgePublishView(event_id=self.event_id)
        await send_ephemeral(
            interaction,
            f"📣 Publish panel opened for event `{self.event_id}`.",
            view=view,
        )

    @discord.ui.button(
        label="Close",
        style=discord.ButtonStyle.danger,
        custom_id="mge_lead_close_view",
    )
    async def close_view(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        del button
        self.stop()
        await send_ephemeral(interaction, "Closed leadership board view.")
