"""Event views extracted from Commands.py with behavior parity.

These classes are used by /nextfight and /nextevent and are re-exported
from Commands.py for backward compatibility.
"""

from __future__ import annotations

import logging

import discord
from discord.errors import HTTPException, NotFound

from embed_utils import LocalTimeToggleView, format_event_embed, format_fight_embed
from utils import get_next_events, get_next_fights

logger = logging.getLogger(__name__)


class NextFightView(LocalTimeToggleView):
    def __init__(self, initial_limit: int = 1, prefix: str = "nextfight"):
        # Preload up to 3 for local-time toggle and button availability
        self.limit = max(1, int(initial_limit))
        self._all3 = get_next_fights(3) or []
        self.fights = self._all3[: self.limit]
        super().__init__(
            events=self.fights, prefix=prefix, timeout=None
        )  # sets self.events in parent
        self.message: discord.Message | None = None  # set by command after send
        self._apply_button_state()

    def _btns(self):
        one = next(
            (
                c
                for c in self.children
                if isinstance(c, discord.ui.Button)
                and (c.label or "").lower().startswith("next fight only")
            ),
            None,
        )
        three = next(
            (
                c
                for c in self.children
                if isinstance(c, discord.ui.Button)
                and "next" in (c.label or "").lower()
                and "fight" in (c.label or "").lower()
                and "only" not in (c.label or "").lower()
            ),
            None,
        )
        return one, three

    def _apply_button_state(self):
        """Update button disabled/style/label based on availability + selected limit."""
        one, three = self._btns()
        available = len(self._all3)

        if one:
            one.style = (
                discord.ButtonStyle.primary if self.limit == 1 else discord.ButtonStyle.secondary
            )

        if three:
            n = min(3, available)
            three.label = f"Next {n} Fight{'s' if n != 1 else ''}"
            three.disabled = n <= 1
            three.style = (
                discord.ButtonStyle.primary if self.limit > 1 else discord.ButtonStyle.secondary
            )

    async def _refresh(self, interaction: discord.Interaction):
        """Ack + update message and view; safe even if already responded."""
        self._apply_button_state()
        try:
            await interaction.response.edit_message(
                embed=format_fight_embed(self.fights), view=self
            )
            return
        except (discord.InteractionResponded, NotFound, HTTPException):
            try:
                if self.message:
                    await self.message.edit(embed=format_fight_embed(self.fights), view=self)
                    return
                try:
                    msg = await interaction.original_response()
                    await msg.edit(embed=format_fight_embed(self.fights), view=self)
                    return
                except Exception:
                    pass
            except Exception:
                logger.exception("[NextFightView] fallback edit failed")
        except Exception:
            logger.exception("[NextFightView] unexpected error while editing response")

    async def _recompute(self, desired_limit: int, interaction: discord.Interaction):
        """Recompute list given desired limit, keep LocalTimeToggleView in sync, and refresh."""
        if (desired_limit == 1 and self.limit == 1) or (desired_limit > 1 and self.limit > 1):
            await interaction.response.defer()  # silent ack; no edit
            return

        self._all3 = get_next_fights(3) or []
        available = len(self._all3)
        self.limit = 1 if desired_limit == 1 else min(3, max(2, available))

        self.fights = self._all3[: self.limit]
        self.events = self.fights

        if not self.fights:
            try:
                await interaction.response.edit_message(
                    content="Fighting finished just chill now!", embed=None, view=None
                )
            except discord.InteractionResponded:
                if self.message:
                    await self.message.edit(
                        content="Fighting finished just chill now!", embed=None, view=None
                    )
            return

        await self._refresh(interaction)

    @discord.ui.button(label="Next Fight Only", style=discord.ButtonStyle.primary)
    async def show_one(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self._recompute(desired_limit=1, interaction=interaction)

    @discord.ui.button(label="Next 3 Fights", style=discord.ButtonStyle.secondary)
    async def show_three(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self._recompute(desired_limit=3, interaction=interaction)


class NextEventView(LocalTimeToggleView):
    def __init__(
        self, initial_limit: int = 1, prefix: str = "nextevent", preloaded: list | None = None
    ):
        self.limit = max(1, int(initial_limit))
        self._all5 = (preloaded or get_next_events(limit=5)) or []
        self.events = self._all5[: self.limit]
        super().__init__(events=self.events, prefix=prefix, timeout=None)
        self.message: discord.Message | None = None
        self._apply_button_state()

    def _btns(self):
        one = next(
            (
                c
                for c in self.children
                if isinstance(c, discord.ui.Button)
                and (c.label or "").lower().startswith("next event only")
            ),
            None,
        )
        five = next(
            (
                c
                for c in self.children
                if isinstance(c, discord.ui.Button)
                and "next" in (c.label or "").lower()
                and "event" in (c.label or "").lower()
                and "only" not in (c.label or "").lower()
            ),
            None,
        )
        return one, five

    def _apply_button_state(self):
        one, five = self._btns()
        available = len(self._all5)

        if one:
            one.style = (
                discord.ButtonStyle.primary if self.limit == 1 else discord.ButtonStyle.secondary
            )

        if five:
            n = min(5, available)
            five.label = f"Next {n} Event{'s' if n != 1 else ''}"
            five.disabled = n <= 1
            five.style = (
                discord.ButtonStyle.primary if self.limit > 1 else discord.ButtonStyle.secondary
            )

    async def _refresh(self, interaction: discord.Interaction):
        """Ack + update the message; safe even if already responded."""
        self._apply_button_state()
        embed = format_event_embed(self.events)
        try:
            await interaction.response.edit_message(embed=embed, view=self)
            return
        except (discord.InteractionResponded, NotFound, HTTPException):
            try:
                if self.message:
                    await self.message.edit(embed=embed, view=self)
                    return
                try:
                    msg = await interaction.original_response()
                    await msg.edit(embed=embed, view=self)
                    return
                except Exception:
                    pass
            except Exception:
                logger.exception("[NextEventView] fallback edit failed")
        except Exception:
            logger.exception("[NextEventView] unexpected error while editing response")

    async def update_embed(self, interaction: discord.Interaction, *, desired_limit: int):
        """Recompute list given desired limit and refresh."""
        if (desired_limit == 1 and self.limit == 1) or (desired_limit > 1 and self.limit > 1):
            await interaction.response.defer()
            return

        self._all5 = get_next_events(limit=5) or self._all5
        available = len(self._all5)

        self.limit = 1 if desired_limit == 1 else min(5, max(2, available))
        self.events = self._all5[: self.limit]

        if not self.events:
            try:
                await interaction.response.edit_message(
                    content="No upcoming events found.", embed=None, view=None
                )
            except discord.InteractionResponded:
                if self.message:
                    await self.message.edit(
                        content="No upcoming events found.", embed=None, view=None
                    )
            return

        logger.info(f"[COMMAND] /nextevent – showing {len(self.events)} event(s)")
        await self._refresh(interaction)

    @discord.ui.button(label="Next Event Only", style=discord.ButtonStyle.primary)
    async def show_one(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.update_embed(interaction, desired_limit=1)

    @discord.ui.button(label="Next 5 Events", style=discord.ButtonStyle.secondary)
    async def show_five(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.update_embed(interaction, desired_limit=5)
