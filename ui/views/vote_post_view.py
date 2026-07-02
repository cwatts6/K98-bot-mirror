from __future__ import annotations

from datetime import UTC, datetime
import logging

import discord

from core.interaction_safety import send_ephemeral
from voting import service as vote_service
from voting.discord_presentation import build_vote_embed, build_vote_file, no_broad_mentions
from voting.models import VoteOption, VoteSnapshot
from voting.vote_modes import VOTE_MODE_MULTI_SELECT, normalize_vote_mode

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
        if normalize_vote_mode(snapshot.vote_mode) == VOTE_MODE_MULTI_SELECT:
            self.add_item(_MultiSelectOpenButton(self.vote_post_id, disabled=should_disable))
            return
        for index, option in enumerate(snapshot.options):
            self.add_item(
                _VoteOptionButton(
                    self.vote_post_id,
                    option,
                    disabled=should_disable,
                    row=index // 3,
                )
            )


class _VoteOptionButton(discord.ui.Button):
    def __init__(self, vote_post_id: int, option: VoteOption, *, disabled: bool, row: int) -> None:
        label = option.label[:80]
        super().__init__(
            label=label,
            style=_button_style(option.button_style),
            custom_id=f"vote:{int(vote_post_id)}:{int(option.option_id)}",
            disabled=disabled,
            row=row,
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

        try:
            result, snapshot = await vote_service.cast_vote(
                vote_post_id=self.vote_post_id,
                option_id=self.option_id,
                discord_user_id=int(interaction.user.id),
            )
        except Exception:
            logger.exception(
                "vote_cast_failed vote_post_id=%s option_id=%s actor_discord_id=%s",
                self.vote_post_id,
                self.option_id,
                getattr(getattr(interaction, "user", None), "id", None),
            )
            await send_ephemeral(interaction, "Vote could not be recorded. Please try again.")
            return
        if not result.accepted or snapshot is None:
            await send_ephemeral(interaction, result.message or "This vote could not be recorded.")
            return

        refreshed_view = VotePostView(snapshot)
        try:
            if interaction.message is not None:
                await interaction.message.edit(
                    embed=build_vote_embed(snapshot),
                    attachments=[],
                    files=[build_vote_file(snapshot)],
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


class _MultiSelectOpenButton(discord.ui.Button):
    def __init__(self, vote_post_id: int, *, disabled: bool) -> None:
        super().__init__(
            label="Choose options",
            style=discord.ButtonStyle.primary,
            custom_id=f"vote_multi:{int(vote_post_id)}",
            disabled=disabled,
        )
        self.vote_post_id = int(vote_post_id)

    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            logger.debug("vote_multi_select_defer_failed", exc_info=True)

        try:
            snapshot = await vote_service.get_vote_snapshot(self.vote_post_id)
        except Exception:
            logger.exception("vote_multi_select_snapshot_failed vote_post_id=%s", self.vote_post_id)
            await send_ephemeral(interaction, "Vote could not be loaded. Please try again.")
            return
        if snapshot is None:
            await send_ephemeral(interaction, "This vote no longer exists.")
            return
        if normalize_vote_mode(snapshot.vote_mode) != VOTE_MODE_MULTI_SELECT:
            await send_ephemeral(interaction, "Use the vote buttons for this vote.")
            return
        if snapshot.status != "Open" or snapshot.closes_at_utc <= datetime.now(UTC):
            await send_ephemeral(interaction, "This vote is already closed.")
            return

        await send_ephemeral(
            interaction,
            (
                f"Choose {snapshot.min_selections}-{snapshot.max_selections} options "
                f"for Vote #{snapshot.vote_post_id}."
            ),
            view=MultiSelectVotePanel(snapshot, owner_user_id=int(interaction.user.id)),
        )


class _MultiSelectOptionSelect(discord.ui.Select):
    def __init__(self, parent_view: "MultiSelectVotePanel") -> None:
        self.parent_view = parent_view
        options = [
            discord.SelectOption(label=option.label[:100], value=str(option.option_id))
            for option in parent_view.snapshot.options[:25]
        ]
        super().__init__(
            placeholder="Choose your options",
            min_values=max(1, int(parent_view.snapshot.min_selections)),
            max_values=max(1, min(int(parent_view.snapshot.max_selections), len(options))),
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if int(getattr(interaction.user, "id", 0)) != self.parent_view.owner_user_id:
            await send_ephemeral(interaction, "This selection panel belongs to another player.")
            return
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            logger.debug("vote_multi_select_panel_defer_failed", exc_info=True)

        try:
            selected_option_ids = tuple(int(value) for value in self.values)
        except (TypeError, ValueError):
            logger.warning(
                "vote_multi_select_invalid_payload vote_post_id=%s actor_discord_id=%s values=%s",
                self.parent_view.vote_post_id,
                getattr(getattr(interaction, "user", None), "id", None),
                list(self.values),
            )
            await send_ephemeral(interaction, "One or more selected options are not valid.")
            return
        try:
            result, snapshot = await vote_service.cast_multi_select_vote(
                vote_post_id=self.parent_view.vote_post_id,
                option_ids=selected_option_ids,
                discord_user_id=int(interaction.user.id),
            )
        except Exception:
            logger.exception(
                "vote_multi_select_cast_failed vote_post_id=%s actor_discord_id=%s",
                self.parent_view.vote_post_id,
                getattr(getattr(interaction, "user", None), "id", None),
            )
            await send_ephemeral(interaction, "Vote could not be recorded. Please try again.")
            return
        if not result.accepted or snapshot is None:
            await send_ephemeral(interaction, result.message or "This vote could not be recorded.")
            return

        try:
            channel = interaction.client.get_channel(
                snapshot.channel_id
            ) or await interaction.client.fetch_channel(snapshot.channel_id)
            message = (
                await channel.fetch_message(snapshot.message_id) if snapshot.message_id else None
            )
            if message is not None:
                await message.edit(
                    embed=build_vote_embed(snapshot),
                    attachments=[],
                    files=[build_vote_file(snapshot)],
                    view=VotePostView(snapshot),
                    allowed_mentions=no_broad_mentions(),
                )
        except Exception:
            logger.exception(
                "vote_multi_select_message_edit_failed vote_post_id=%s message_id=%s",
                self.parent_view.vote_post_id,
                snapshot.message_id,
            )
            await vote_service.record_message_edit_failed(
                vote_post_id=self.parent_view.vote_post_id,
                actor_discord_user_id=int(interaction.user.id),
                source="multi_select_vote",
            )

        await send_ephemeral(interaction, result.message or "Selections recorded.")


class MultiSelectVotePanel(discord.ui.View):
    def __init__(self, snapshot: VoteSnapshot, *, owner_user_id: int) -> None:
        super().__init__(timeout=300)
        self.snapshot = snapshot
        self.vote_post_id = int(snapshot.vote_post_id)
        self.owner_user_id = int(owner_user_id)
        self.add_item(_MultiSelectOptionSelect(self))


def disabled_vote_view(snapshot: VoteSnapshot) -> VotePostView:
    return VotePostView(snapshot, disabled=True)
