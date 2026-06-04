from __future__ import annotations

from io import BytesIO
import logging

import discord

from kvk.models.kvk_stats_card import KvkStatsCardPayload, RenderedKvkStatsCard

logger = logging.getLogger(__name__)


def _compact(value: int | float | None) -> str:
    if value is None:
        return "N/A"
    val = float(value)
    abs_val = abs(val)
    for limit, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if abs_val >= limit:
            return f"{val / limit:.1f}".rstrip("0").rstrip(".") + suffix
    return f"{int(val):,}"


def _pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.1f}%"


def _line(label: str, value: str) -> str:
    return f"**{label}:** {value}"


def _nonzero_items(values: dict) -> list[tuple[str, int | float | str]]:
    return [(label, value) for label, value in values.items() if value not in (None, "", 0, 0.0)]


def build_more_stats_embed(payload: KvkStatsCardPayload) -> discord.Embed:
    embed = discord.Embed(
        title=f"More KVK Stats - {payload.governor_name}",
        description=f"{payload.display_kvk_label} | {payload.display_mode}",
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name="DKP",
        value=f"{_compact(payload.dkp)} / {_compact(payload.dkp_target)} - {_pct(payload.dkp_target_percent)}",
        inline=False,
    )
    if payload.pass_stats:
        passes = "\n".join(
            _line(label, _compact(value)) for label, value in payload.pass_stats.items()
        )
    else:
        passes = "No pass stats available."
    embed.add_field(name="Passes", value=passes, inline=False)
    embed.add_field(
        name="Pre-KVK",
        value="\n".join(
            [
                _line("Rank", str(payload.prekvk_rank) if payload.prekvk_rank else "N/A"),
                _line("Points", _compact(payload.prekvk_points)),
            ]
        ),
        inline=True,
    )
    embed.add_field(
        name="Honor",
        value="\n".join(
            [
                _line("Rank", str(payload.honor_rank) if payload.honor_rank else "N/A"),
                _line("Points", _compact(payload.honor_points)),
            ]
        ),
        inline=True,
    )
    embed.set_footer(text="Use Main Card to return to the visual card.")
    return embed


def build_history_embed(payload: KvkStatsCardPayload) -> discord.Embed:
    embed = discord.Embed(
        title=f"Historic KVK Data - {payload.governor_name}",
        description=f"{payload.display_kvk_label} | {payload.display_mode}",
        color=discord.Color.green(),
    )
    history_summary = _nonzero_items(payload.history_summary)
    personal_bests = _nonzero_items(payload.personal_bests)
    if history_summary:
        embed.add_field(
            name="Summary",
            value="\n".join(_line(label, _compact(value)) for label, value in history_summary),
            inline=False,
        )
    if personal_bests:
        embed.add_field(
            name="Personal Bests",
            value="\n".join(_line(label, _compact(value)) for label, value in personal_bests),
            inline=False,
        )
    if payload.last_kvk_summary:
        last_no = payload.last_kvk_summary.get("KVK_NO") or "Last"
        embed.add_field(
            name=f"Last KVK Summary - KVK {last_no}",
            value="\n".join(
                [
                    _line(
                        "Kills",
                        f"{_compact(payload.last_kvk_summary.get('Kills'))} / "
                        f"{_compact(payload.last_kvk_summary.get('Kill Target'))} - "
                        f"{_pct(payload.last_kvk_summary.get('Kill Percent'))}",
                    ),
                    _line(
                        "Deads",
                        f"{_compact(payload.last_kvk_summary.get('Deads'))} / "
                        f"{_compact(payload.last_kvk_summary.get('Dead Target'))} - "
                        f"{_pct(payload.last_kvk_summary.get('Dead Percent'))}",
                    ),
                    _line(
                        "DKP",
                        f"{_compact(payload.last_kvk_summary.get('DKP'))} / "
                        f"{_compact(payload.last_kvk_summary.get('DKP Target'))} - "
                        f"{_pct(payload.last_kvk_summary.get('DKP Percent'))}",
                    ),
                    _line("KP", _compact(payload.last_kvk_summary.get("KP"))),
                    _line("Acclaim", _compact(payload.last_kvk_summary.get("Acclaim"))),
                ]
            ),
            inline=False,
        )
    else:
        embed.add_field(name="Last KVK Summary", value="No history data available.", inline=False)

    if payload.matchmaking_snapshot:
        embed.add_field(
            name="Matchmaking Snapshot",
            value="\n".join(
                _line(label, _compact(value))
                for label, value in payload.matchmaking_snapshot.items()
                if value
            )
            or "No matchmaking snapshot available.",
            inline=False,
        )
    embed.set_footer(text="Use Main Card to return to the visual card.")
    return embed


class KvkStatsCardView(discord.ui.View):
    def __init__(
        self,
        *,
        payload: KvkStatsCardPayload,
        rendered: RenderedKvkStatsCard,
        timeout: float = 300.0,
    ) -> None:
        super().__init__(timeout=timeout)
        self.payload = payload
        self._image_bytes = rendered.image_bytes.getvalue()
        self._filename = rendered.filename
        self.message: discord.Message | None = None

    def _file(self) -> discord.File:
        return discord.File(BytesIO(self._image_bytes), filename=self._filename)

    async def _edit_host_message(self, interaction: discord.Interaction, **kwargs) -> None:
        try:
            if not interaction.response.is_done():
                await interaction.response.defer()
        except Exception:
            pass
        message = getattr(interaction, "message", None)
        if message is not None:
            self.message = message
            await message.edit(**kwargs)
            return
        await interaction.edit_original_response(**kwargs)

    async def _show_main(self, interaction: discord.Interaction) -> None:
        await self._edit_host_message(
            interaction,
            content=None,
            embeds=[],
            attachments=[],
            files=[self._file()],
            view=self,
        )

    async def _show_more_stats(self, interaction: discord.Interaction) -> None:
        await self._edit_host_message(
            interaction,
            content=None,
            embeds=[build_more_stats_embed(self.payload)],
            attachments=[],
            view=self,
        )

    async def _show_history(self, interaction: discord.Interaction) -> None:
        await self._edit_host_message(
            interaction,
            content=None,
            embeds=[build_history_embed(self.payload)],
            attachments=[],
            view=self,
        )

    @discord.ui.button(label="Main Card", style=discord.ButtonStyle.primary)
    async def main_card(self, _button: discord.ui.Button, interaction: discord.Interaction) -> None:
        await self._show_main(interaction)

    @discord.ui.button(label="More Stats", style=discord.ButtonStyle.secondary)
    async def more_stats(
        self, _button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        await self._show_more_stats(interaction)

    @discord.ui.button(label="History", style=discord.ButtonStyle.secondary)
    async def history(self, _button: discord.ui.Button, interaction: discord.Interaction) -> None:
        await self._show_history(interaction)

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            logger.debug("kvk_stats_card_view_timeout_edit_failed", exc_info=True)
