# honor_rankings_view.py
from __future__ import annotations

import logging
from typing import Any

import discord

from stats_alerts.honors import get_latest_honor_top
from utils import utcnow

logger = logging.getLogger(__name__)

DEFAULT_COLOR = discord.Color.gold()


def build_honor_rankings_embed(
    rows: list[dict[str, Any]] | None,
    limit: int = 10,
    *,
    color: discord.Color | int = DEFAULT_COLOR,
) -> discord.Embed:
    """
    Build the honor rankings embed from rows (list of dicts).
    """
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    lines: list[str] = []
    if not rows:
        desc = "No matching players found."
    else:
        for idx, r in enumerate(rows[:limit], start=1):
            prefix = medals.get(idx, f"{idx:>2}.")
            # Use robust name selection to avoid "None" showing up
            gid = r.get("GovernorID")
            raw_name = r.get("GovernorName")
            if raw_name and str(raw_name).strip():
                name = str(raw_name).strip()
            elif gid not in (None, ""):
                name = str(gid)
            else:
                name = "Unknown"
            try:
                pts = int(r.get("HonorPoints", 0) or 0)
            except Exception:
                pts = 0
            lines.append(f"{prefix} **{name}** — {pts:,}")
        desc = "\n".join(lines) if lines else "No matching players found."

    embed = discord.Embed(
        title="🏆 Top Honor — Current KVK",
        description=desc,
        color=color if isinstance(color, int) else color,
    )
    embed.add_field(name="Shown", value=f"Top {limit}", inline=True)
    # Small UX: show when this embed was generated
    try:
        embed.timestamp = utcnow()
    except Exception:
        pass
    return embed


class HonorRankingView(discord.ui.View):
    """
    View containing buttons to switch Top-N for honor rankings.
    Fetches fresh data on each button press.
    """

    def __init__(self, *, timeout: float = 120.0):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Top 10", style=discord.ButtonStyle.primary)
    async def top10(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self._refresh(interaction, 10, selected_button=button)

    @discord.ui.button(label="Top 25", style=discord.ButtonStyle.secondary)
    async def top25(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self._refresh(interaction, 25, selected_button=button)

    @discord.ui.button(label="Top 50", style=discord.ButtonStyle.secondary)
    async def top50(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self._refresh(interaction, 50, selected_button=button)

    @discord.ui.button(label="Top 100", style=discord.ButtonStyle.secondary)
    async def top100(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self._refresh(interaction, 100, selected_button=button)

    async def _refresh(
        self,
        interaction: discord.Interaction,
        limit: int,
        *,
        selected_button: discord.ui.Button | None = None,
    ):
        """
        Fetch Top-N and update the message embed/view.
        """
        try:
            rows = await get_latest_honor_top(limit)
        except Exception:
            logger.exception("[HONOR] get_latest_honor_top failed")
            # Use ephemeral so the channel isn't spammed on failure
            await interaction.response.send_message("Failed loading honor data.", ephemeral=True)
            return

        if not rows:
            await interaction.response.send_message(
                "No honor data found for the latest KVK.", ephemeral=True
            )
            return

        # Update button styles to show current selection
        if selected_button:
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    item.style = discord.ButtonStyle.secondary
            selected_button.style = discord.ButtonStyle.primary

        embed = build_honor_rankings_embed(rows, limit=limit)

        # Prefer to reuse the central responder helper if available (more robust)
        try:
            from target_utils import _respond  # type: ignore

            try:
                await _respond(interaction, embed=embed, view=self, ephemeral_flag=False)
                return
            except Exception:
                logger.debug(
                    "[HONOR] target_utils._respond available but raised; falling back",
                    exc_info=True,
                )
        except Exception:
            # helper not available; fall back to local strategy
            pass

        # Local fallback sequence: try component edit -> edit original response -> followup
        try:
            try:
                await interaction.response.edit_message(embed=embed, view=self)
                return
            except Exception as e:
                logger.debug("[HONOR] response.edit_message failed: %s", e)

            try:
                await interaction.edit_original_response(embed=embed, view=self)
                return
            except Exception as e:
                logger.debug("[HONOR] edit_original_response failed: %s", e)

            try:
                await interaction.followup.send(embed=embed, view=self)
                return
            except Exception:
                logger.exception("[HONOR] Followup send also failed")
        except Exception:
            logger.exception("[HONOR] Failed to update honor rankings message in fallback")
