from __future__ import annotations

import asyncio
from copy import deepcopy
from io import BytesIO
import logging

import discord

from core.interaction_safety import send_ephemeral
from kvk.models.kvk_stats_card import (
    KvkStatsCardPayload,
    RenderedKvkStatsCard,
    card_context_label,
)
from kvk.rendering.kvk_stats_card_renderer import render_kvk_more_stats_card
from kvk.services.kvk_stats_card_service import require_card_current

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


def _overall_rank_text(payload: KvkStatsCardPayload) -> str:
    if payload.source_context is not None:
        source = payload.source_context
        return (
            f"#{source['rank']} / {source['population']} (usable frozen B0 cohort)"
            if source.get("available")
            else "Unavailable"
        )
    if not payload.overall_kvk_rank:
        return "TBC"
    value = f"#{payload.overall_kvk_rank}"
    context: list[str] = []
    if payload.overall_kvk_total_governors:
        context.append(f"Total {_compact(payload.overall_kvk_total_governors).lower()}")
    if payload.overall_kvk_top_percent is not None:
        context.append(f"Top {_pct(payload.overall_kvk_top_percent)}")
    if context:
        value = f"{value}\n{' / '.join(context)}"
    return value


def build_more_stats_embed(payload: KvkStatsCardPayload) -> discord.Embed:
    embed = discord.Embed(
        title=f"More KVK Stats - {payload.governor_name}",
        description=f"{payload.display_kvk_label} | {payload.display_mode}",
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name="Independent KVK statistics",
        value=(
            f"Kills: {_compact(payload.kills_gain)} / {_compact(payload.kill_target)}\n"
            f"Deads: {_compact(payload.deads)} / {_compact(payload.dead_target)}\n"
            f"KP: {_compact(payload.kp_gain)} | KVK rank: {payload.kvk_rank or 'N/A'}"
        ),
        inline=False,
    )
    embed.add_field(
        name="Combat and matchmaking",
        value=(
            f"MM power: {_compact(payload.matchmaking_power)} | Kingdom rank: {payload.kingdom_rank or 'N/A'}\n"
            f"Healed: {_compact(payload.healed)} | KP loss: {_compact(payload.kp_loss)}\n"
            f"Tanking: {_pct(payload.tanking_score_percent)} | Acclaim: {_compact(payload.acclaim)}\n"
            f"Power change: {_compact(payload.power_loss)}"
        ),
        inline=False,
    )
    if card_context_label(payload):
        embed.add_field(name="Source context", value=card_context_label(payload), inline=False)
    embed.add_field(
        name="KVK Overall Rank",
        value=_overall_rank_text(payload),
        inline=False,
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


async def require_card_destination(context, *, user=None):
    """Recheck the current actor's access immediately before context-bearing output."""
    channel = getattr(context, "channel", None)
    guild = getattr(channel, "guild", None) or getattr(context, "guild", None)
    if guild is None:
        return
    permissions_for = getattr(channel, "permissions_for", None)
    if not callable(permissions_for):
        raise PermissionError("Card destination is unavailable.")
    user = user or context.user
    member = await guild.fetch_member(user.id)
    permissions = permissions_for(member)
    if not permissions.view_channel or not permissions.send_messages:
        raise PermissionError("Card destination permission changed.")


class KvkStatsCardView(discord.ui.View):
    def __init__(
        self,
        *,
        payload: KvkStatsCardPayload,
        rendered: RenderedKvkStatsCard,
        timeout: float = 300.0,
        owner_id: int | None = None,
    ) -> None:
        super().__init__(timeout=timeout)
        self.owner_id = owner_id
        self.guild_id = None
        self.channel_id = None
        self._expired = False
        self.payload = deepcopy(payload)
        self._bound_payload = deepcopy(payload)
        self._image_bytes = rendered.image_bytes.getvalue()
        self._filename = rendered.filename
        self._more_stats_bytes: bytes | None = None
        self._more_stats_filename: str | None = None
        self.message: discord.Message | None = None

    async def _authorize(self, interaction):
        if self.payload != self._bound_payload:
            raise PermissionError("Card inputs changed; request a new card.")
        if self._expired or self.is_finished() or interaction.user.id != self.owner_id:
            raise PermissionError("This card is expired or belongs to another user.")
        if self.message is None or getattr(interaction.message, "id", None) != self.message.id:
            raise PermissionError("Card message changed.")
        if interaction.channel_id != self.channel_id or interaction.guild_id != self.guild_id:
            raise PermissionError("Card destination changed.")
        await require_card_destination(interaction)
        await require_card_current(self.payload)

    async def interaction_check(self, interaction):
        try:
            await self._authorize(interaction)
            return True
        except Exception:
            await send_ephemeral(
                interaction, "This card is stale or unavailable. Request a new card."
            )
            return False

    def _file(self) -> discord.File:
        return discord.File(BytesIO(self._image_bytes), filename=self._filename)

    def _cached_file(self, *, kind: str) -> discord.File | None:
        if kind == "more":
            if self._more_stats_bytes is None or self._more_stats_filename is None:
                return None
            return discord.File(BytesIO(self._more_stats_bytes), filename=self._more_stats_filename)
        return None

    async def _defer_interaction(self, interaction: discord.Interaction) -> None:
        try:
            if not interaction.response.is_done():
                await interaction.response.defer()
        except Exception:
            pass

    async def _edit_host_message(self, interaction: discord.Interaction, **kwargs) -> None:
        await self._defer_interaction(interaction)
        if not await self.interaction_check(interaction):
            return
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
        await self._defer_interaction(interaction)
        if not await self.interaction_check(interaction):
            return
        try:
            if self._more_stats_bytes is None or self._more_stats_filename is None:
                rendered = await asyncio.to_thread(render_kvk_more_stats_card, self.payload)
                if rendered is not None:
                    self._more_stats_bytes = rendered.image_bytes.getvalue()
                    self._more_stats_filename = rendered.filename
            file = self._cached_file(kind="more")
            if file is not None:
                await self._edit_host_message(
                    interaction,
                    content=None,
                    embeds=[],
                    attachments=[],
                    files=[file],
                    view=self,
                )
                return
        except Exception:
            logger.exception(
                "kvk_more_stats_card_render_or_send_failed governor_id=%s",
                self.payload.governor_id,
            )
        await self._edit_host_message(
            interaction,
            content=None,
            embeds=[build_more_stats_embed(self.payload)],
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

    async def on_timeout(self) -> None:
        self._expired = True
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            logger.debug("kvk_stats_card_view_timeout_edit_failed", exc_info=True)
