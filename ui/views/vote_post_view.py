from __future__ import annotations

from datetime import UTC, datetime
import logging

import discord

from core.interaction_safety import send_ephemeral
from voting import service as vote_service
from voting.discord_presentation import build_vote_embed, build_vote_file, no_broad_mentions
from voting.models import VoteOption, VoteSnapshot

logger = logging.getLogger(__name__)


def _button_style(value: str | None) -> discord.ButtonStyle:
    mapping = {
        "primary": discord.ButtonStyle.primary,
        "secondary": discord.ButtonStyle.secondary,
        "success": discord.ButtonStyle.success,
        "danger": discord.ButtonStyle.danger,
    }
    return mapping.get((value or "").casefold(), discord.ButtonStyle.primary)


class VotePostView(discord.ui.View):
    def __init__(self, snapshot: VoteSnapshot, *, disabled: bool | None = None) -> None:
        super().__init__(timeout=None)
        self.vote_post_id = int(snapshot.vote_post_id)
        closed = snapshot.status != "Open" or snapshot.closes_at_utc <= datetime.now(UTC)
        should_disable = closed if disabled is None else bool(disabled)
        for option in snapshot.options:
            self.add_item(_VoteOptionButton(self.vote_post_id, option, disabled=should_disable))


class _VoteOptionButton(discord.ui.Button):
    def __init__(self, vote_post_id: int, option: VoteOption, *, disabled: bool) -> None:
        label = option.label[:80]
        super().__init__(
            label=label,
            style=_button_style(option.button_style),
            custom_id=f"vote:{int(vote_post_id)}:{int(option.option_id)}",
            disabled=disabled,
        )
        self.vote_post_id = int(vote_post_id)
        self.option_id = int(option.option_id)
        self.option_label = option.label

    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            logger.debug("vote_button_defer_failed", exc_info=True)

        result, snapshot = await vote_service.cast_vote(
            vote_post_id=self.vote_post_id,
            option_id=self.option_id,
            discord_user_id=int(interaction.user.id),
        )
        if not result.accepted or snapshot is None:
            await send_ephemeral(interaction, result.message or "This vote could not be recorded.")
            return

        refreshed_view = VotePostView(snapshot)
        try:
            if interaction.message is not None:
                await interaction.message.edit(
                    embed=build_vote_embed(snapshot),
                    attachments=[build_vote_file(snapshot)],
                    view=refreshed_view,
                    allowed_mentions=no_broad_mentions(),
                )
        except Exception:
            logger.exception(
                "vote_message_edit_failed vote_post_id=%s message_id=%s",
                self.vote_post_id,
                getattr(getattr(interaction, "message", None), "id", None),
            )
            await vote_service.record_message_edit_failed(
                vote_post_id=self.vote_post_id,
                actor_discord_user_id=int(interaction.user.id),
                source="button_vote",
            )

        await send_ephemeral(interaction, result.message or f"Vote recorded: {self.option_label}")


def disabled_vote_view(snapshot: VoteSnapshot) -> VotePostView:
    return VotePostView(snapshot, disabled=True)
