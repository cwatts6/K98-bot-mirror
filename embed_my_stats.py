# embed_my_stats.py
import logging
import re

import discord
from discord import ui

from constants import CUSTOM_AVATAR_URL, DOWN_ARROW_EMOJI, STATS_VIEW_TIMEOUT, UP_ARROW_EMOJI
from embed_utils import fmt_short
from stats_service import _make_sparkline, get_stats_payload
from utils import normalize_governor_id

logger = logging.getLogger(__name__)

_VALID_TAG = re.compile(r"^<a?:\w+:\d+>$")

SLICE_LABELS = {
    "yesterday": "Yesterday",
    "wtd": "This Week",
    "last_week": "Last Week",
    "mtd": "This Month",
    "last_month": "Last Month",
    "last_3m": "Last 3M",
    "last_6m": "Last 6M",
}


def _find_row(
    rows: list[dict],
    window_key: str,
    governor_name_or_all: str,
    *,
    governor_id_for_choice: int | None = None,
) -> list[dict]:
    # If 'ALL', return the single ALL row. Else filter PER rows.
    candidates = [r for r in rows if r["WindowKey"] == window_key]
    if governor_name_or_all == "ALL":
        return [r for r in candidates if r["Grouping"] == "ALL"]
    # Prefer GovernorID match (robust) then fallback to name match
    if governor_id_for_choice is not None:
        try:
            wanted = normalize_governor_id(governor_id_for_choice)
            return [
                r
                for r in candidates
                if r.get("Grouping") == "PER"
                and normalize_governor_id(r.get("GovernorID")) == wanted
            ]
        except Exception:
            pass
    return [
        r
        for r in candidates
        if r.get("Grouping") == "PER" and r.get("GovernorName") == governor_name_or_all
    ]


def _num(x, default=0):
    try:
        return int(x if x is not None else default)
    except Exception:
        try:
            return int(float(x))
        except Exception:
            return default


def _delta_arrow(delta: int) -> str:
    """Format delta with arrow and short notation."""
    try:
        d = int(delta)
    except Exception:
        d = 0
    if d > 0:
        arrow = UP_ARROW_EMOJI if _VALID_TAG.match(UP_ARROW_EMOJI) else "⬆️"
        return f"{arrow} {fmt_short(d)}"
    if d < 0:
        arrow = DOWN_ARROW_EMOJI if _VALID_TAG.match(DOWN_ARROW_EMOJI) else "⬇️"
        return f"{arrow} {fmt_short(abs(d))}"
    return "0"


async def build_embeds(
    window_key: str, choice: str, data: dict, *, governor_id_for_choice: int | None = None
) -> tuple[list[discord.Embed], list[discord.File]]:
    """
    Build Discord embeds for stats display with charts.

    Args:
        window_key: Time slice (e.g., "wtd", "last_month")
        choice: Governor name or "ALL"
        data: Payload from get_stats_payload (rows, trends, trend_avgs, freshness)
        governor_id_for_choice: Optional GovernorID for matching (more robust than name)

    Returns:
        Tuple of (embeds list, files list)
    """
    try:
        rows = (data or {}).get("rows") or []
        subset = _find_row(rows, window_key, choice, governor_id_for_choice=governor_id_for_choice)
        files: list[discord.File] = []

        if not subset:
            empty = discord.Embed(title="Stats", description="No data.", color=0x5865F2)
            empty.set_thumbnail(url=CUSTOM_AVATAR_URL)
            return [empty], files

        r = subset[0]
        title = f"{SLICE_LABELS.get(window_key, window_key)} — {choice}"
        desc = (
            f"Alliance: {r.get('Alliance') or '-'}\n"
            "*Totals shown as **total (Δ change)**. Where time is > 1 day, **Avg/day** is shown.*"
        )
        stats_embed = discord.Embed(title=title, description=desc, color=0x2ECC71)

        # --- Pull trends + precomputed averages early (needed for field text and charts) ---
        trends = (data or {}).get("trends") or {}
        avgs = (data or {}).get("trend_avgs") or {}

        # --- Topline (Forts removed) ---
        power_end = _num(r.get("PowerEnd"))
        power_delta = _num(r.get("PowerDelta"))
        troop_end = _num(r.get("TroopPowerEnd"))
        troop_delta = _num(r.get("TroopPowerDelta"))
        stats_embed.add_field(
            name="Power",
            value=f"{fmt_short(power_end)}  ({_delta_arrow(power_delta)})",
            inline=True,
        )
        stats_embed.add_field(
            name="Troop Power",
            value=f"{fmt_short(troop_end)}  ({_delta_arrow(troop_delta)})",
            inline=True,
        )

        # --- Activity ---
        rss_end = _num(r.get("RSSGatheredEnd"))
        rss_delta = _num(r.get("RSSGatheredDelta"))
        rssA_end = _num(r.get("RSSAssistEnd"))
        rssA_delta = _num(r.get("RSSAssistDelta"))
        helps_end = _num(r.get("HelpsEnd"))
        helps_delta = _num(r.get("HelpsDelta"))

        # RSS: totals + optional Avg/day (multi-day slices only)
        rss_avg = avgs.get("RSS")
        rss_line = f"{fmt_short(rss_end)}  (Δ {fmt_short(max(rss_delta,0))})"
        if rss_avg is not None:
            rss_line += f"\nAvg/day: {fmt_short(rss_avg)}"
        stats_embed.add_field(name="RSS Gathered", value=rss_line, inline=True)

        stats_embed.add_field(
            name="RSS Assisted",
            value=f"{fmt_short(rssA_end)}  (Δ {fmt_short(max(rssA_delta,0))})",
            inline=True,
        )

        # Helps: use fmt_short for totals, keep Avg/day as full numbers (they're typically small)
        helps_avg = avgs.get("HELPS")
        helps_line = f"{fmt_short(helps_end)}  (Δ {fmt_short(max(helps_delta,0))})"
        if helps_avg is not None:
            # Avg/day is small (typically < 1000), keep as full number
            helps_line += f"\nAvg/day: {round(helps_avg):,}"
        stats_embed.add_field(name="Helps", value=helps_line, inline=True)

        # --- Alliance Activity (sum of per-day values in the window) + Avg/day where available ---
        bm_total = sum(int(v or 0) for _, v in (trends.get("AA_BUILD") or []))
        td_total = sum(int(v or 0) for _, v in (trends.get("AA_TECH") or []))

        # Build Minutes: use fmt_short for total, keep Avg/day as full number
        bm_line = f"{fmt_short(bm_total)}"
        bm_avg = avgs.get("AA_BUILD")
        if bm_avg is not None:
            # Avg/day is small, keep as full number
            bm_line += f"\nAvg/day: {round(bm_avg):,}"
        stats_embed.add_field(name="Build Minutes (Δ)", value=bm_line, inline=True)

        # Tech Donations: use fmt_short for total, keep Avg/day as full number
        td_line = f"{fmt_short(td_total)}"
        td_avg = avgs.get("AA_TECH")
        if td_avg is not None:
            # Avg/day is small, keep as full number
            td_line += f"\nAvg/day: {round(td_avg):,}"
        stats_embed.add_field(name="Tech Donations (Δ)", value=td_line, inline=True)

        # --- Forts ---
        rallies_total = _num(r.get("FortsTotal"))
        rallies_launch = _num(r.get("FortsLaunched"))
        rallies_join = _num(r.get("FortsJoined"))
        rally_avg = avgs.get("FORTS")

        forts_lines = [
            f"Total {rallies_total:,}",
            f"Launch {rallies_launch:,} • Join {rallies_join:,}",
        ]
        if rally_avg is not None:
            # Avg/day is small, keep as full number
            forts_lines.append(f"Avg/day: {round(rally_avg):,}")
        stats_embed.add_field(name="Forts", value="\n".join(forts_lines), inline=True)

        # --- Ark of Osiris (AOO) - compact inline layout ---
        aoo_joined = _num(r.get("AOOJoinedEnd"))
        aoo_won = _num(r.get("AOOWonEnd"))
        aoo_avg_kill = _num(r.get("AOOAvgKillEnd"))
        aoo_avg_dead = _num(r.get("AOOAvgDeadEnd"))
        aoo_avg_heal = _num(r.get("AOOAvgHealEnd"))

        # Only show AOO section if player has participated
        if aoo_joined > 0:
            # Add blank spacer to force next row (Discord embeds use 3-column layout)
            stats_embed.add_field(name="\u200b", value="\u200b", inline=True)

            # Ark Joined and Ark Won on same line (compact)
            stats_embed.add_field(
                name="Ark Played • Won",
                value=f"{aoo_joined:,} • {aoo_won:,}",
                inline=True,
            )

            # K/D/H with fmt_short for readability
            kdh_line = f"K: {fmt_short(aoo_avg_kill)} • D: {fmt_short(aoo_avg_dead)} • H: {fmt_short(aoo_avg_heal)}"
            stats_embed.add_field(name="Ark Avg K/D/H", value=kdh_line, inline=True)

        # --- Trendlines: pass averages so the dashed mean line renders ---
        rss_img = await _make_sparkline(trends.get("RSS") or [], "RSS Daily", avgs.get("RSS"))
        forts_img = await _make_sparkline(
            trends.get("FORTS") or [], "Forts Daily", avgs.get("FORTS")
        )

        chart_embeds: list[discord.Embed] = []
        if rss_img:
            f = discord.File(rss_img, filename="rss.png")
            files.append(f)
            e_rss = discord.Embed(color=0x2C3E50, title="RSS Daily")
            e_rss.set_image(url="attachment://rss.png")
            chart_embeds.append(e_rss)
        if forts_img:
            f = discord.File(forts_img, filename="forts.png")
            files.append(f)
            e_rally = discord.Embed(color=0x2C3E50, title="Forts Daily")
            e_rally.set_image(url="attachment://forts.png")
            chart_embeds.append(e_rally)

        # --- Footer freshness ---
        fr = (data or {}).get("freshness") or {}
        daily_dt = fr.get("daily")
        if daily_dt:
            stats_embed.set_footer(text=f"Data freshness: {daily_dt:%Y-%m-%d}")

        stats_embed.set_thumbnail(url=CUSTOM_AVATAR_URL)  # avatar only on stats card

        # Order: Stats → RSS → Rallies
        ordered = [stats_embed] + chart_embeds
        return ordered, files

    except Exception as exc:
        logger.exception(
            "Failed to build embeds: window_key=%s choice=%s governor_id=%s",
            window_key,
            choice,
            governor_id_for_choice,
        )
        # Return error embed instead of crashing
        error_embed = discord.Embed(
            title="⚠️ Stats Error",
            description=f"Failed to build stats embed: {type(exc).__name__}",
            color=0xFF0000,
        )
        error_embed.add_field(
            name="Suggestion",
            value="Please try again or contact support if this persists.",
            inline=False,
        )
        return [error_embed], []


class SliceButtons(ui.View):
    def __init__(
        self,
        requester_id: int,
        initial_slice: str,
        account_options: list[str],
        current_choice: str,
        governor_ids: list[int],
        name_to_id: dict[str, int],
        timeout: int = STATS_VIEW_TIMEOUT,  # ← Use constant
    ):
        super().__init__(timeout=timeout)
        self.requester_id = requester_id
        self.slice = initial_slice
        self.choice = current_choice
        self.account_options = account_options
        self.governor_ids = governor_ids
        self.name_to_id = name_to_id
        self.message: discord.Message | None = None
        self.followup = None
        self._expired: bool = (
            True  # default True until first send sets message; flipped to False by sender
        )

        self.add_item(AccountSelect(self))
        self._slice_buttons: dict[str, SliceButton] = {}
        for key in ["yesterday", "wtd", "last_week", "mtd", "last_month", "last_3m", "last_6m"]:
            btn = SliceButton(self, key)
            self._slice_buttons[key] = btn
            self.add_item(btn)
        self.update_styles()  # make currently-selected slice blue

    def mark_live(self):
        """Call this right after sending the first message to make the panel active."""
        self._expired = False

    def update_styles(self):
        for key, btn in self._slice_buttons.items():
            btn.style = (
                discord.ButtonStyle.primary if key == self.slice else discord.ButtonStyle.secondary
            )

    def _ids_for_choice(self) -> list[int]:
        if self.choice == "ALL":
            return self.governor_ids
        gid = self.name_to_id.get(self.choice)
        return [gid] if gid else self.governor_ids

    async def refresh_message(self, interaction: discord.Interaction):
        # Expired or wrong user protection
        if self._expired:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "This stats panel has expired. Run **/my_stats** again.",
                    ephemeral=True,
                )
            return
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message(
                "This panel isn't yours. Run `/my_stats` to get your own.", ephemeral=True
            )
            return

        # Performance monitoring: track total refresh time
        import time

        start = time.time()

        try:
            payload = await get_stats_payload(self.requester_id, self._ids_for_choice(), self.slice)
            gid_for_choice = None if self.choice == "ALL" else self.name_to_id.get(self.choice)
            embeds, files = await build_embeds(
                self.slice, self.choice, payload, governor_id_for_choice=gid_for_choice
            )
            self.update_styles()
        except Exception as exc:
            logger.exception(
                "Failed to refresh stats: user=%s slice=%s choice=%s",
                self.requester_id,
                self.slice,
                self.choice,
            )
            # Show user-friendly error instead of silent failure
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"⚠️ Failed to load stats: {type(exc).__name__}. Please try again.",
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    f"⚠️ Failed to load stats: {type(exc).__name__}. Please try again.",
                    ephemeral=True,
                )
            return

        # Emit performance telemetry
        elapsed = time.time() - start
        try:
            from file_utils import emit_telemetry_event

            emit_telemetry_event(
                {
                    "event": "my_stats_refresh",
                    "user_id": self.requester_id,
                    "slice": self.slice,
                    "choice": self.choice,
                    "num_governors": len(self._ids_for_choice()),
                    "elapsed_seconds": round(elapsed, 3),
                    "num_embeds": len(embeds),
                    "num_charts": len(files),
                    "has_trends": bool((payload or {}).get("trends")),
                }
            )
        except Exception:
            # Don't let telemetry failures break the command
            pass

        # --- PRIMARY PATH: edit the ephemeral follow-up by ID ---
        try:
            if self.followup and self.message:
                if files:
                    await self.followup.edit_message(
                        self.message.id, embeds=embeds, view=self, attachments=[], files=files
                    )
                else:
                    await self.followup.edit_message(
                        self.message.id, embeds=embeds, view=self, attachments=[]
                    )
                return
        except discord.errors.NotFound:
            # That follow-up message no longer exists
            try:
                await interaction.followup.send(
                    "This stats card has expired or was removed. Please run `/my_stats` again.",
                    ephemeral=True,
                )
            except Exception:
                pass
            self._expired = True
            return

        # --- SECONDARY PATHS (rare) ---

        # If we somehow don't have a followup/message handle, try original response
        try:
            await interaction.edit_original_response(
                embeds=embeds, view=self, attachments=[], files=files or []
            )
            return
        except discord.errors.NotFound:
            # Webhook token likely expired – last resort informative message
            try:
                await interaction.followup.send(
                    "This stats card has expired or was removed. Please run `/my_stats` again.",
                    ephemeral=True,
                )
                self._expired = True
                return
            except discord.errors.NotFound:
                # Even followup failed; post a short channel notice
                try:
                    chan = getattr(interaction, "channel", None) or (
                        self.message.channel if self.message else None
                    )
                    if chan:
                        await chan.send(
                            "This stats card has expired or was removed. Please run `/my_stats` again.",
                            delete_after=30,
                        )
                except Exception:
                    pass
                self._expired = True
                return

    async def on_timeout(self):
        # NOTE: Per your request, leaving your existing on_timeout logic unchanged.
        self._expired = True

        expired = discord.Embed(
            title="Stats panel expired",
            description="This stats view has timed out.\nRun **/my_stats** again to refresh.",
            color=0x95A5A6,
        )
        expired.set_footer(text="Tip: You can export via /my_stats_export")

        try:
            if not self.message:
                return

            # Prefer webhook path for ephemeral follow-ups
            if self.followup is not None:
                # Best effort: delete the old panel completely
                try:
                    await self.followup.delete_message(self.message.id)
                except Exception:
                    # If delete is refused (race, perms), hard-clear instead
                    try:
                        await self.followup.edit_message(
                            self.message.id, content=None, embeds=[], attachments=[], view=None
                        )
                    except Exception:
                        pass

                # Post a brand-new ephemeral "expired" message
                await self.followup.send(embeds=[expired], ephemeral=True)
                return

            # Fallback for non-webhook messages (rare in this command)
            try:
                await self.message.delete()
            except Exception:
                try:
                    await self.message.edit(content=None, embeds=[], attachments=[], view=None)
                except Exception:
                    pass
            await self.message.channel.send(embed=expired, delete_after=30)  # visible fallback
        except Exception:
            pass


class SliceButton(ui.Button):
    def __init__(self, parent: "SliceButtons", key: str):
        super().__init__(
            label=SLICE_LABELS.get(key, key),
            style=discord.ButtonStyle.secondary,  # styled dynamically
            custom_id=f"slice_{key}",
        )
        self.key = key
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        # 1) Instant ACK: disable controls so the client gets a successful response
        try:
            for child in self.parent.children:
                child.disabled = True
            await interaction.response.edit_message(view=self.parent)
        except Exception:
            # If this fails we still proceed, but the client may show a banner
            pass

        # 2) Do the real work
        self.parent.slice = self.key

        # Emit interaction telemetry
        try:
            from file_utils import emit_telemetry_event

            emit_telemetry_event(
                {
                    "event": "my_stats_slice_change",
                    "user_id": self.parent.requester_id,
                    "from_slice": self.parent.slice,  # old value
                    "to_slice": self.key,
                }
            )
        except Exception:
            pass

        self.parent.update_styles()
        # Re-enable controls for the final render
        for child in self.parent.children:
            child.disabled = False
        await self.parent.refresh_message(interaction)


class AccountSelect(ui.Select):
    def __init__(self, parent: "SliceButtons"):
        self.parent = parent
        # Mark the active option as default so it shows selected on first render
        opts = [
            discord.SelectOption(label="ALL", value="ALL", default=(parent.choice == "ALL")),
            *[
                # Discord hard limit: label ≤ 100 chars
                discord.SelectOption(
                    label=str(name)[:100], value=str(name), default=(name == parent.choice)
                )
                for name in parent.account_options
            ],
        ]
        super().__init__(placeholder="Choose account", min_values=1, max_values=1, options=opts)

    async def callback(self, interaction: discord.Interaction):
        # 1) Instant ACK
        try:
            for child in self.parent.children:
                child.disabled = True
            await interaction.response.edit_message(view=self.parent)
        except Exception:
            pass

        # 2) Update selection
        old_choice = self.parent.choice
        self.parent.choice = self.values[0]

        # Emit interaction telemetry
        try:
            from file_utils import emit_telemetry_event

            emit_telemetry_event(
                {
                    "event": "my_stats_account_change",
                    "user_id": self.parent.requester_id,
                    "from_account": old_choice,
                    "to_account": self.parent.choice,
                    "slice": self.parent.slice,
                }
            )
        except Exception:
            pass

        for opt in self.options:
            opt.default = opt.value == self.parent.choice

        for child in self.parent.children:
            child.disabled = False
        await self.parent.refresh_message(interaction)
