from __future__ import annotations

from collections.abc import Awaitable, Callable
import logging

import discord

from core.interaction_safety import send_ephemeral
from ui.views.vote_post_view import VotePostView
from voting.discord_presentation import build_vote_embed, build_vote_file, no_broad_mentions
from voting.models import VoteSnapshot
from voting.option_emojis import option_display_label
from voting.service import (
    CLOSE_DURATION_CHOICES,
    MAX_DESCRIPTION_LEN,
    MAX_TITLE_LEN,
    VoteValidationError,
    update_vote_option_emoji,
    update_vote,
)

logger = logging.getLogger(__name__)

RefreshCallback = Callable[[discord.Client, VoteSnapshot], Awaitable[None]]


async def refresh_public_vote_message(bot: discord.Client, snapshot: VoteSnapshot) -> None:
    if snapshot.message_id is None:
        return
    channel = bot.get_channel(snapshot.channel_id) or await bot.fetch_channel(snapshot.channel_id)
    message = await channel.fetch_message(snapshot.message_id)
    await message.edit(
        embed=build_vote_embed(snapshot),
        attachments=[],
        files=[build_vote_file(snapshot)],
        view=VotePostView(snapshot),
        allowed_mentions=no_broad_mentions(),
    )


def _duration_options() -> list[discord.SelectOption]:
    labels = {
        "30m": "30 minutes",
        "1h": "1 hour",
        "2h": "2 hours",
        "4h": "4 hours",
        "8h": "8 hours",
        "12h": "12 hours",
        "1d": "1 day",
        "2d": "2 days",
        "3d": "3 days",
        "7d": "7 days",
    }
    return [
        discord.SelectOption(label=labels.get(key, key), value=key)
        for key in CLOSE_DURATION_CHOICES
    ]


async def _apply_update(
    interaction: discord.Interaction,
    *,
    vote_post_id: int,
    actor_discord_user_id: int,
    refresh_callback: RefreshCallback,
    **changes,
) -> None:
    try:
        snapshot = await update_vote(
            vote_post_id=vote_post_id,
            actor_discord_user_id=actor_discord_user_id,
            **changes,
        )
    except VoteValidationError as exc:
        await send_ephemeral(interaction, f"Vote not updated: {exc}")
        return
    except Exception:
        logger.exception("vote_admin_update_apply_failed vote_post_id=%s", vote_post_id)
        await send_ephemeral(interaction, "Vote could not be updated. Please try again.")
        return

    try:
        await refresh_callback(interaction.client, snapshot)
    except Exception:
        logger.exception(
            "vote_admin_update_refresh_failed vote_post_id=%s message_id=%s",
            vote_post_id,
            snapshot.message_id,
        )
        await send_ephemeral(
            interaction,
            f"Vote #{vote_post_id} was updated, but the public message could not be refreshed.",
        )
        return

    await send_ephemeral(interaction, f"Vote #{vote_post_id} updated.")


class _VoteTextUpdateModal(discord.ui.Modal):
    def __init__(
        self,
        *,
        vote_post_id: int,
        actor_discord_user_id: int,
        field: str,
        label: str,
        current_value: str,
        max_length: int,
        refresh_callback: RefreshCallback,
    ) -> None:
        super().__init__(title=f"Update vote {label}", timeout=300)
        self.vote_post_id = int(vote_post_id)
        self.actor_discord_user_id = int(actor_discord_user_id)
        self.field = field
        self.refresh_callback = refresh_callback
        style = (
            discord.InputTextStyle.long if field == "description" else discord.InputTextStyle.short
        )
        self.value_input = discord.ui.InputText(
            label=label,
            value=current_value[:max_length],
            max_length=max_length,
            required=True,
            style=style,
        )
        self.add_item(self.value_input)

    async def callback(self, interaction: discord.Interaction) -> None:
        value = str(self.value_input.value or "")
        await _apply_update(
            interaction,
            vote_post_id=self.vote_post_id,
            actor_discord_user_id=self.actor_discord_user_id,
            refresh_callback=self.refresh_callback,
            **{self.field: value},
        )


class _VoteReminderModal(discord.ui.Modal):
    def __init__(
        self,
        *,
        vote_post_id: int,
        actor_discord_user_id: int,
        refresh_callback: RefreshCallback,
    ) -> None:
        super().__init__(title="Update vote reminders", timeout=300)
        self.vote_post_id = int(vote_post_id)
        self.actor_discord_user_id = int(actor_discord_user_id)
        self.refresh_callback = refresh_callback
        self.offsets = discord.ui.InputText(
            label="Reminder offsets in minutes",
            placeholder="Example: 60, 30, 10",
            max_length=80,
            required=False,
        )
        self.add_item(self.offsets)

    async def callback(self, interaction: discord.Interaction) -> None:
        await _apply_update(
            interaction,
            vote_post_id=self.vote_post_id,
            actor_discord_user_id=self.actor_discord_user_id,
            refresh_callback=self.refresh_callback,
            reminder_offsets=str(self.offsets.value or ""),
        )


class _VoteDurationSelect(discord.ui.Select):
    def __init__(self, parent_view: VoteAdminUpdateView) -> None:
        self.parent_view = parent_view
        super().__init__(
            placeholder="Choose a new close time",
            min_values=1,
            max_values=1,
            options=_duration_options(),
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await self.parent_view.guard(interaction):
            return
        await _apply_update(
            interaction,
            vote_post_id=self.parent_view.vote_post_id,
            actor_discord_user_id=self.parent_view.owner_user_id,
            refresh_callback=self.parent_view.refresh_callback,
            close_time_utc=self.values[0],
        )


class _VoteBoolSelect(discord.ui.Select):
    def __init__(self, parent_view: VoteAdminUpdateView, *, field: str, label: str) -> None:
        self.parent_view = parent_view
        self.field = field
        super().__init__(
            placeholder=label,
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="Yes", value="yes"),
                discord.SelectOption(label="No", value="no"),
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await self.parent_view.guard(interaction):
            return
        await _apply_update(
            interaction,
            vote_post_id=self.parent_view.vote_post_id,
            actor_discord_user_id=self.parent_view.owner_user_id,
            refresh_callback=self.parent_view.refresh_callback,
            **{self.field: self.values[0] == "yes"},
        )


class _VoteTargetSelect(discord.ui.Select):
    def __init__(self, parent_view: VoteAdminUpdateView) -> None:
        self.parent_view = parent_view
        super().__init__(
            placeholder="Choose what to update",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="Title", value="title"),
                discord.SelectOption(label="Description", value="description"),
                discord.SelectOption(label="Close time", value="close_time"),
                discord.SelectOption(label="Reminder offsets", value="reminders"),
                discord.SelectOption(label="Reminder @everyone", value="reminder_mention"),
                discord.SelectOption(label="Close @everyone", value="close_mention"),
                discord.SelectOption(label="Option icons", value="option_icons"),
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await self.parent_view.guard(interaction):
            return
        target = self.values[0]
        if target == "title":
            await interaction.response.send_modal(
                _VoteTextUpdateModal(
                    vote_post_id=self.parent_view.vote_post_id,
                    actor_discord_user_id=self.parent_view.owner_user_id,
                    field="title",
                    label="Title",
                    current_value=self.parent_view.snapshot.title,
                    max_length=MAX_TITLE_LEN,
                    refresh_callback=self.parent_view.refresh_callback,
                )
            )
            return
        if target == "description":
            await interaction.response.send_modal(
                _VoteTextUpdateModal(
                    vote_post_id=self.parent_view.vote_post_id,
                    actor_discord_user_id=self.parent_view.owner_user_id,
                    field="description",
                    label="Description",
                    current_value=self.parent_view.snapshot.description or "",
                    max_length=MAX_DESCRIPTION_LEN,
                    refresh_callback=self.parent_view.refresh_callback,
                )
            )
            return
        if target == "reminders":
            await interaction.response.send_modal(
                _VoteReminderModal(
                    vote_post_id=self.parent_view.vote_post_id,
                    actor_discord_user_id=self.parent_view.owner_user_id,
                    refresh_callback=self.parent_view.refresh_callback,
                )
            )
            return

        if target == "close_time":
            view = discord.ui.View(timeout=180)
            view.add_item(_VoteDurationSelect(self.parent_view))
            await interaction.response.edit_message(content="Choose the new close time:", view=view)
            return

        if target == "option_icons":
            view = _VoteOptionIconView(self.parent_view)
            await interaction.response.edit_message(content="Choose an option to polish:", view=view)
            return

        field = (
            "reminder_mention_everyone"
            if target == "reminder_mention"
            else "close_mention_everyone"
        )
        label = (
            "Mention @everyone on future reminders?"
            if target == "reminder_mention"
            else "Mention @everyone on close?"
        )
        view = discord.ui.View(timeout=180)
        view.add_item(_VoteBoolSelect(self.parent_view, field=field, label=label))
        await interaction.response.edit_message(content=label, view=view)


class _VoteOptionIconSelect(discord.ui.Select):
    def __init__(self, parent_view: "_VoteOptionIconView") -> None:
        self.parent_view = parent_view
        options = [
            discord.SelectOption(
                label=option.label[:100],
                value=str(option.option_id),
                description=option.emoji.text[:100] if option.emoji else None,
            )
            for option in parent_view.update_view.snapshot.options
        ]
        super().__init__(
            placeholder="Option to polish",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await self.parent_view.update_view.guard(interaction):
            return
        try:
            option_id = int(self.values[0])
        except (IndexError, TypeError, ValueError):
            await send_ephemeral(interaction, "Choose a valid option.")
            return
        option = next(
            (
                item
                for item in self.parent_view.update_view.snapshot.options
                if int(item.option_id) == option_id
            ),
            None,
        )
        if option is None:
            await send_ephemeral(interaction, "Choose a valid option.")
            return
        await interaction.response.send_modal(
            _VoteOptionIconModal(self.parent_view.update_view, option_id=option_id)
        )


class _VoteOptionIconView(discord.ui.View):
    def __init__(self, update_view: "VoteAdminUpdateView") -> None:
        super().__init__(timeout=180)
        self.update_view = update_view
        self.add_item(_VoteOptionIconSelect(self))


class _VoteOptionIconModal(discord.ui.Modal):
    def __init__(self, parent_view: "VoteAdminUpdateView", *, option_id: int) -> None:
        option = next(
            item for item in parent_view.snapshot.options if int(item.option_id) == int(option_id)
        )
        super().__init__(title="Vote option icon", timeout=300)
        self.parent_view = parent_view
        self.option_id = int(option_id)
        self.icon = discord.ui.InputText(
            label=f"Icon for {option.label[:34]}",
            required=False,
            max_length=120,
            placeholder="Unicode emoji or <:name:id>; blank clears",
            value=option.emoji.text if option.emoji is not None else "",
        )
        self.add_item(self.icon)

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await self.parent_view.guard(interaction):
            return
        try:
            snapshot = await update_vote_option_emoji(
                vote_post_id=self.parent_view.vote_post_id,
                option_id=self.option_id,
                emoji_value=str(self.icon.value or ""),
                actor_discord_user_id=self.parent_view.owner_user_id,
            )
        except VoteValidationError as exc:
            await send_ephemeral(interaction, f"Option icon not saved: {exc}")
            return
        except Exception:
            logger.exception(
                "vote_admin_option_icon_update_failed vote_post_id=%s option_id=%s",
                self.parent_view.vote_post_id,
                self.option_id,
            )
            await send_ephemeral(interaction, "Option icon could not be saved. Please try again.")
            return

        self.parent_view.snapshot = snapshot
        try:
            await self.parent_view.refresh_callback(interaction.client, snapshot)
        except Exception:
            logger.exception(
                "vote_admin_option_icon_refresh_failed vote_post_id=%s message_id=%s",
                self.parent_view.vote_post_id,
                snapshot.message_id,
            )
            await send_ephemeral(
                interaction,
                f"Vote #{self.parent_view.vote_post_id} was updated, "
                "but the public message could not be refreshed.",
            )
            return
        label = next(
            (
                option_display_label(item.label, item.emoji)
                for item in snapshot.options
                if int(item.option_id) == self.option_id
            ),
            "option",
        )
        await send_ephemeral(interaction, f"Option icon saved for {label}.")


class VoteAdminUpdateView(discord.ui.View):
    def __init__(
        self,
        snapshot: VoteSnapshot,
        *,
        owner_user_id: int,
        refresh_callback: RefreshCallback = refresh_public_vote_message,
    ) -> None:
        super().__init__(timeout=300)
        self.snapshot = snapshot
        self.vote_post_id = int(snapshot.vote_post_id)
        self.owner_user_id = int(owner_user_id)
        self.refresh_callback = refresh_callback
        self.add_item(_VoteTargetSelect(self))

    async def guard(self, interaction: discord.Interaction) -> bool:
        if int(getattr(interaction.user, "id", 0)) != self.owner_user_id:
            await send_ephemeral(interaction, "This update panel belongs to another admin.")
            return False
        return True
