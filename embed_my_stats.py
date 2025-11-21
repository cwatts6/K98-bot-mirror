# embed_my_stats.py
import re

import discord
from discord import ui

from constants import CUSTOM_AVATAR_URL
from stats_service import _make_sparkline, get_stats_payload
from utils import normalize_governor_id

try:
    # Optional: define these in constants.py if you have custom server emojis
    from constants import DOWN_ARROW_EMOJI, UP_ARROW_EMOJI
except Exception:
    UP_ARROW_EMOJI = "⬆️"
    DOWN_ARROW_EMOJI = "⬇️"

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


def _short(n: float | int) -> str:
    try:
        n = float(n)
    except Exception:
        return str(n)
    ab = abs(n)
    if ab >= 1_000_000_000:
        return f"{n/1_000_000_000:.1f}B"
    if ab >= 1_000_000:
        return f"{n/1_000_000:.0f}M" if ab >= 10_000_000 else f"{n/1_000_000:.1f}M"
    if ab >= 1_000:
        return f"{n/1_000:.0f}K" if ab >= 10_000 else f"{n/1_000:.1f}K"
    # small numbers: keep as plain int with commas
    return f"{int(n):,}"


def _delta_arrow(delta: int) -> str:
    try:
        d = int(delta)
    except Exception:
        d = 0
    if d > 0:
        arrow = UP_ARROW_EMOJI if _VALID_TAG.match(UP_ARROW_EMOJI) else "⬆️"
        return f"{arrow} {_short(d)}"  # ← short
    if d < 0:
        arrow = DOWN_ARROW_EMOJI if _VALID_TAG.match(DOWN_ARROW_EMOJI) else "⬇️"
        return f"{arrow} {_short(abs(d))}"  # ← short
    return "0"


def build_embeds(
    window_key: str, choice: str, data: dict, *, governor_id_for_choice: int | None = None
) -> tuple[list[discord.Embed], list[discord.File]]:
    rows = (data or {}).get("rows") or []
    subset = _find_row(rows, window_key, choice, governor_id_for_choice=governor_id_for_choice)
    files: list[discord.File] = []

    if not subset:
        empty = discord.Embed(title="Stats", description="No data.", color=0x5865F2)
        empty.set_thumbnail(url=CUSTOM_AVATAR_URL)  # avatar only on stats card
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
        name="Power", value=f"{_short(power_end)}  ({_delta_arrow(power_delta)})", inline=True
    )
    stats_embed.add_field(
        name="Troop Power", value=f"{_short(troop_end)}  ({_delta_arrow(troop_delta)})", inline=True
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
    rss_line = f"{_short(rss_end)}  (Δ {_short(max(rss_delta,0))})"
    if rss_avg is not None:
        rss_line += f"\nAvg/day: {_short(rss_avg)}"
    stats_embed.add_field(name="RSS Gathered", value=rss_line, inline=True)

    stats_embed.add_field(
        name="RSS Assisted",
        value=f"{_short(rssA_end)}  (Δ {_short(max(rssA_delta,0))})",
        inline=True,
    )

    # Helps: totals + optional Avg/day (multi-day windows only); keep full numbers
    helps_avg = avgs.get("HELPS")
    helps_line = f"{helps_end:,}  (Δ {max(helps_delta,0):,})"
    if helps_avg is not None:
        helps_line += f"\nAvg/day: {round(helps_avg):,}"
    stats_embed.add_field(name="Helps", value=helps_line, inline=True)

    # --- Alliance Activity (sum of per-day values in the window) + Avg/day where available ---
    bm_total = sum(int(v or 0) for _, v in (trends.get("AA_BUILD") or []))
    td_total = sum(int(v or 0) for _, v in (trends.get("AA_TECH") or []))

    bm_line = f"{bm_total:,}"
    bm_avg = avgs.get("AA_BUILD")
    if bm_avg is not None:
        bm_line += f"\nAvg/day: {round(bm_avg):,}"
    stats_embed.add_field(name="Build Minutes (Δ)", value=bm_line, inline=True)

    td_line = f"{td_total:,}"
    td_avg = avgs.get("AA_TECH")
    if td_avg is not None:
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
        forts_lines.append(f"Avg/day: {round(rally_avg):,}")
    stats_embed.add_field(name="Forts", value="\n".join(forts_lines), inline=True)

    # --- Trendlines: pass averages so the dashed mean line renders ---
    rss_img = _make_sparkline(trends.get("RSS") or [], "RSS Daily", avgs.get("RSS"))
    forts_img = _make_sparkline(trends.get("FORTS") or [], "Forts Daily", avgs.get("FORTS"))

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


class SliceButtons(ui.View):
    def __init__(
        self,
        requester_id: int,
        initial_slice: str,
        account_options: list[str],
        current_choice: str,
        governor_ids: list[int],
        name_to_id: dict[str, int],
        timeout: int = 70,
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
                "This panel isn’t yours. Run `/my_stats` to get your own.", ephemeral=True
            )
            return

        payload = await get_stats_payload(self.requester_id, self._ids_for_choice(), self.slice)
        gid_for_choice = None if self.choice == "ALL" else self.name_to_id.get(self.choice)
        embeds, files = build_embeds(
            self.slice, self.choice, payload, governor_id_for_choice=gid_for_choice
        )
        self.update_styles()

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

        # If we somehow don’t have a followup/message handle, try original response
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

                # Post a brand-new ephemeral “expired” message
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

        # 2) Update selection + final render
        self.parent.choice = self.values[0]
        for opt in self.options:
            opt.default = opt.value == self.parent.choice

        for child in self.parent.children:
            child.disabled = False
        await self.parent.refresh_message(interaction)
