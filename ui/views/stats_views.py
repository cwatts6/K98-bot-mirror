# ui/views/stats_views.py
"""Stats-domain UI views.

Module created for ongoing Commands.py UI extraction.
"""

from __future__ import annotations

import asyncio
import logging

import discord

from build_KVKrankings_embed import build_kvkrankings_embed, filter_rows_for_leaderboard

logger = logging.getLogger(__name__)


class KVKRankingView(discord.ui.View):
    """
    Interactive view for KVK rankings with multi-column display.

    Features:
    - 5 sort metrics: Power, Kills, % Kill Target, Deads, DKP
    - 4 limit options: Top 10, 25, 50, 100
    - Automatic pagination for Top 100 (2 pages, 50 per page)
    - Excel-style sort indicator (▼) on active column

    Attributes:
        cache: Full stat cache dict
        metric: Active sort metric
        limit: Number of players to show
        page: Current page number (1-based)
        message: Discord message reference for editing
    """

    def __init__(
        self, cache: dict, metric: str = "power", limit: int = 10, *, timeout: float = 120.0
    ):
        super().__init__(timeout=timeout)
        self.cache = cache
        self.metric = (metric or "power").lower()
        self.limit = limit
        self.page = 1
        self.message: discord.Message | None = None

        # rows: list of player dicts (exclude metadata)
        self.rows = [r for k, r in cache.items() if k != "_meta"]
        self.meta = cache.get("_meta", {})

        # Build UI components
        self._add_metric_dropdown()
        self._add_limit_buttons()
        self._add_pagination_buttons()

    def _add_metric_dropdown(self):
        """Add metric selection dropdown with all 5 options."""
        self.metric_select = discord.ui.Select(
            placeholder="Sort by…",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Power", value="power", default=(self.metric == "power"), emoji="⚡"
                ),
                discord.SelectOption(
                    label="Kills (T4+T5)",
                    value="kills",
                    default=(self.metric == "kills"),
                    emoji="⚔️",
                ),
                discord.SelectOption(
                    label="% of Kill Target",
                    value="pct_kill_target",
                    default=(self.metric == "pct_kill_target"),
                    emoji="🎯",
                ),
                discord.SelectOption(
                    label="Deads", value="deads", default=(self.metric == "deads"), emoji="💀"
                ),
                discord.SelectOption(
                    label="DKP", value="dkp", default=(self.metric == "dkp"), emoji="🏅"
                ),
            ],
            row=0,
        )
        self.metric_select.callback = self.on_metric_change
        self.add_item(self.metric_select)

    def _add_limit_buttons(self):
        """Add limit buttons (Top 10/25/50/100) to row 1."""
        for n in (10, 25, 50, 100):
            btn = discord.ui.Button(
                label=f"Top {n}",
                style=(
                    discord.ButtonStyle.primary
                    if n == self.limit
                    else discord.ButtonStyle.secondary
                ),
                custom_id=f"kvk_top_{n}",
                row=1,
            )
            btn.callback = self._make_limit_handler(n)
            self.add_item(btn)

    def _add_pagination_buttons(self):
        """
        Ensure prev/next pagination buttons exist when there are multiple pages.

        Behavior:
        - If total_pages <= 1: remove any existing pagination buttons.
        - If total_pages > 1: make sure both buttons are present (recreate them
          fresh if necessary) and then update their state.
        """
        total_pages = self._compute_total_pages()

        # If only a single page, remove any pagination UI and exit.
        if total_pages <= 1:
            self._remove_pagination_buttons()
            return

        # At this point we need pagination controls. Recreate them to avoid
        # stale/corrupted component objects or attribute/view mismatches.
        # Remove any existing ones first to ensure a clean state.
        if hasattr(self, "prev_btn"):
            try:
                self.remove_item(self.prev_btn)
            except Exception as exc:
                logger.debug("Failed to remove existing prev_btn: %r", exc)
            try:
                delattr(self, "prev_btn")
            except Exception as exc:
                logger.debug("Failed to delete prev_btn attr: %r", exc)

        if hasattr(self, "next_btn"):
            try:
                self.remove_item(self.next_btn)
            except Exception as exc:
                logger.debug("Failed to remove existing next_btn: %r", exc)
            try:
                delattr(self, "next_btn")
            except Exception as exc:
                logger.debug("Failed to delete next_btn attr: %r", exc)

        # Create fresh button objects and attach them to the view.
        import discord

        # Put pagination on its own row (row=2) beneath the limit buttons (row=1)
        self.prev_btn = discord.ui.Button(label="Prev", style=discord.ButtonStyle.secondary, row=2)
        self.next_btn = discord.ui.Button(label="Next", style=discord.ButtonStyle.secondary, row=2)

        async def _prev_handler(interaction: discord.Interaction):
            await self._on_prev_page(interaction)

        async def _next_handler(interaction: discord.Interaction):
            await self._on_next_page(interaction)

        self.prev_btn.callback = _prev_handler
        self.next_btn.callback = _next_handler

        # Add to the view (order is deterministic)
        self.add_item(self.prev_btn)
        self.add_item(self.next_btn)

        # Ensure page is within the valid range and update button disabled states.
        self.page = max(1, min(self.page, total_pages))
        self._update_pagination_buttons()

    def _remove_pagination_buttons(self):
        """Remove pagination buttons and cleanup attributes if present."""
        if hasattr(self, "prev_btn"):
            try:
                self.remove_item(self.prev_btn)
            except Exception as exc:
                logger.debug("Failed to remove existing prev_btn: %r", exc)
            try:
                delattr(self, "prev_btn")
            except Exception as exc:
                logger.debug("Failed to delete prev_btn attr: %r", exc)

        if hasattr(self, "next_btn"):
            try:
                self.remove_item(self.next_btn)
            except Exception as exc:
                logger.debug("Failed to remove existing next_btn: %r", exc)
            try:
                delattr(self, "next_btn")
            except Exception as exc:
                logger.debug("Failed to delete next_btn attr: %r", exc)

    def _update_pagination_buttons(self):
        """Update pagination button states (disabled/enabled) based on current page."""
        # If buttons are missing, try to add them if pagination is needed.
        total_pages = self._compute_total_pages()
        if total_pages <= 1:
            # Nothing to update; ensure they are removed
            self._remove_pagination_buttons()
            return

        # If attributes are missing but pagination is required, create them.
        if not hasattr(self, "prev_btn") or not hasattr(self, "next_btn"):
            self._add_pagination_buttons()
            # _add_pagination_buttons will call _update_pagination_buttons again.
            return

        # Clamp page into range first
        self.page = max(1, min(self.page, total_pages))

        # Update disabled state
        self.prev_btn.disabled = self.page == 1
        self.next_btn.disabled = self.page >= total_pages

    def _compute_total_pages(self) -> int:
        """
        Compute total pages based on the actual number of rows available and the selected limit.

        Mirrors build_kvkrankings_embed which slices rows to `limit` then pages at 50 per page.
        Ensures at least 1 page is returned.

        IMPORTANT: This applies the same filtering as the embed builder so the UI and
        page controls remain consistent with what the embed shows.
        """
        PAGE_SIZE = 50
        # Apply same filtering as the embed builder to determine how many rows
        raw_rows = getattr(self, "rows", []) or []
        # filter_rows_for_leaderboard should be imported at module top:
        # from build_KVKrankings_embed import build_kvkrankings_embed, filter_rows_for_leaderboard
        filtered = filter_rows_for_leaderboard(raw_rows)

        rows_len = len(filtered)
        total_available = min(self.limit, rows_len)
        if total_available <= 0:
            return 1
        return max(1, (total_available + PAGE_SIZE - 1) // PAGE_SIZE)

    # ---- New helpers to robustly handle interaction.response.is_done() which
    #      may be a bool in runtime or a coroutine in unit tests (AsyncMock) ----
    async def _is_response_done(self, interaction: discord.Interaction) -> bool:
        """
        Return True if the interaction response is already done.

        Handles both cases where interaction.response.is_done() returns a bool
        (runtime) or a coroutine (unit tests using AsyncMock).
        """
        try:
            res = interaction.response.is_done()
            # If res is a coroutine (as in tests), await it.
            if asyncio.iscoroutine(res):
                return bool(await res)
            return bool(res)
        except Exception as exc:
            logger.debug("Failed to check response.is_done(): %r", exc)
            # Be conservative: treat as not done so subsequent code will defer/send
            return False

    async def _ensure_deferred(self, interaction: discord.Interaction) -> None:
        """
        Ensure the interaction is deferred (acknowledged) if not already.

        Uses _is_response_done to handle both coroutine and boolean returns.
        """
        try:
            done = await self._is_response_done(interaction)
            if not done:
                await interaction.response.defer()
        except Exception as exc:
            logger.debug("Failed to defer interaction in _ensure_deferred: %r", exc)
            # Continue — we will attempt other acknowledgement strategies later.

    # ---- Pagination navigation handlers ----
    async def _on_prev_page(self, interaction: discord.Interaction):
        """
        Handler for Previous page button.

        When already at page 1, update the view state and push the update to Discord
        (so stale enabled/disabled button state is corrected for clients).
        """
        # If already at first page, ensure the UI state is corrected and push update
        if self.page <= 1:
            self._update_pagination_buttons()
            try:
                # _redraw will rebuild the embed and edit the message (or call interaction.response)
                await self._redraw(interaction)
            except asyncio.CancelledError:
                # expected cancellation - no stack trace; perform minimal cleanup, then propagate
                logger.debug(
                    "KVKRankingView._on_prev_page cancelled while redrawing (page=%s limit=%s)",
                    self.page,
                    self.limit,
                )
                await self._ensure_deferred(interaction)
                raise
            except Exception:
                logger.exception(
                    "KVKRankingView._on_prev_page failed to redraw UI (page=%s limit=%s metric=%s)",
                    self.page,
                    self.limit,
                    getattr(self, "metric", None),
                )
                # Ensure the interaction is acknowledged to avoid 10062
                await self._ensure_deferred(interaction)
            return

        # Normal previous-page flow
        self.page = max(1, self.page - 1)
        self._update_pagination_buttons()
        try:
            await self._redraw(interaction)
        except Exception:
            logger.exception(
                "KVKRankingView._on_prev_page failed while redrawing after decrement (page=%s limit=%s metric=%s)",
                self.page,
                self.limit,
                getattr(self, "metric", None),
            )
            await self._ensure_deferred(interaction)

    async def _on_next_page(self, interaction: discord.Interaction):
        """
        Handler for Next page button.

        When already at the last page, update the view state and push the update to Discord
        so clients receive the corrected disabled/enable component state.
        """
        total_pages = self._compute_total_pages()

        # Already at last page: ensure UI state is consistent and respond
        if self.page >= total_pages:
            self._update_pagination_buttons()
            try:
                await self._redraw(interaction)
            except asyncio.CancelledError:
                logger.debug(
                    "KVKRankingView._on_next_page cancelled while redrawing (page=%s limit=%s)",
                    self.page,
                    self.limit,
                )
                await self._ensure_deferred(interaction)
                raise
            except Exception:
                logger.exception(
                    "KVKRankingView._on_next_page failed to redraw UI (page=%s limit=%s)",
                    self.page,
                    self.limit,
                )
                await self._ensure_deferred(interaction)
            return

        # Normal next-page flow
        # Increment and defensively clamp in one step
        self.page = max(1, min(self.page + 1, total_pages))

        self._update_pagination_buttons()
        try:
            await self._redraw(interaction)
        except Exception:
            logger.exception(
                "KVKRankingView._on_next_page failed while redrawing after increment (page=%s limit=%s metric=%s)",
                self.page,
                self.limit,
                getattr(self, "metric", None),
            )
            await self._ensure_deferred(interaction)

    async def _safe_edit(self, interaction: discord.Interaction, *, embed: discord.Embed):
        """
        Safely edit the message for a component interaction.

        Tries multiple fallback strategies to ensure the view updates and the
        interaction is acknowledged so Discord doesn't show "This interaction failed".
        """
        # Try to ensure we have acknowledged/deferred the interaction quickly.
        await self._ensure_deferred(interaction)

        # Strategy 1: Edit via interaction.edit_original_response
        try:
            await interaction.edit_original_response(embed=embed, view=self)
            return
        except Exception as exc:
            logger.debug("Failed to edit_original_response in _safe_edit: %r", exc)

        # Strategy 2: Edit via followup.edit_message (some bots use followups)
        try:
            if interaction.message:
                # Be defensive: followup may not exist on the interaction object in
                # some runtime contexts until after defer(); check/get attr first.
                followup = getattr(interaction, "followup", None)
                if followup:
                    await followup.edit_message(interaction.message.id, embed=embed, view=self)
                return
        except Exception as exc:
            logger.debug("Failed to edit via followup in _safe_edit: %r", exc)

        # Strategy 3: Edit cached message reference
        if self.message:
            try:
                await self.message.edit(embed=embed, view=self)
                return
            except Exception as exc:
                logger.debug("Failed to edit cached message in _safe_edit: %r", exc)

        # Final fallback: try to send a followup message to acknowledge the interaction
        # and present the embed, to avoid "This interaction failed".
        try:
            followup = getattr(interaction, "followup", None)
            if followup:
                await followup.send(embed=embed, view=self)
            return
        except Exception as exc:
            logger.debug("Failed to send followup in _safe_edit: %r", exc)

    async def _redraw(self, interaction: discord.Interaction):
        """Rebuild and update embed with current settings."""
        # Update dropdown selected state
        for opt in self.metric_select.options:
            opt.default = opt.value == self.metric

        # Update button styles
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.label and item.label.startswith("Top "):
                item.style = (
                    discord.ButtonStyle.primary
                    if item.label == f"Top {self.limit}"
                    else discord.ButtonStyle.secondary
                )

        # Handle pagination button visibility
        if self.limit <= 50:
            # Remove pagination buttons if they exist
            self._remove_pagination_buttons()
            self.page = 1  # Reset to page 1
        else:
            # Add or update pagination buttons
            if not hasattr(self, "prev_btn"):
                self._add_pagination_buttons()
            else:
                self._update_pagination_buttons()

        # Build embed with current page
        embed = build_kvkrankings_embed(self.rows, self.metric, self.limit, page=self.page)

        # Fallback footer if builder didn't set one
        if not embed.footer or not embed.footer.text:
            last_ref = self.meta.get("generated_at") or "unknown"
            embed.set_footer(text=f"Last refreshed: {last_ref}")

        await self._safe_edit(interaction, embed=embed)

    async def on_metric_change(self, interaction: discord.Interaction):
        """Handle metric dropdown change."""
        self.metric = self.metric_select.values[0]
        self.page = 1  # Reset to page 1 when changing metric
        await self._redraw(interaction)

    def _make_limit_handler(self, n: int):
        """Create button handler for limit change."""

        async def _handler(interaction: discord.Interaction):
            self.limit = n
            self.page = 1  # Reset to page 1 when changing limit
            await self._redraw(interaction)

        return _handler

    async def on_timeout(self):
        """Disable all UI elements on timeout."""
        for child in self.children:
            child.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception as exc:
            logger.debug("Failed to update message on timeout: %r", exc)


__all__ = ["KVKRankingView"]
