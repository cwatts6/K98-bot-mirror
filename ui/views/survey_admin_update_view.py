from __future__ import annotations

from collections.abc import Awaitable, Callable
import logging

import discord

from core.interaction_safety import send_ephemeral
from ui.views.survey_post_view import SurveyPostView
from voting.option_emojis import EMOJI_KIND_CUSTOM_DISCORD, OptionEmoji, option_display_label
from voting.service import (
    CLOSE_DURATION_CHOICES,
    MAX_DESCRIPTION_LEN,
    MAX_TITLE_LEN,
    RESULT_VISIBILITY_CHOICES,
    VoteValidationError,
)
from voting.survey_models import SurveyQuestion, SurveySnapshot
from voting.survey_presentation import build_survey_embed, build_survey_file, no_broad_mentions
from voting.survey_service import (
    record_message_edit_failed,
    update_survey,
    update_survey_option_emoji,
)

logger = logging.getLogger(__name__)

SurveyRefreshCallback = Callable[[discord.Client, SurveySnapshot], Awaitable[None]]


def _discord_emoji(emoji: OptionEmoji | None) -> discord.PartialEmoji | str | None:
    if emoji is None:
        return None
    if emoji.kind == EMOJI_KIND_CUSTOM_DISCORD:
        try:
            return discord.PartialEmoji.from_str(emoji.text)
        except (TypeError, ValueError):
            return None
    return emoji.text


async def refresh_public_survey_message(bot: discord.Client, snapshot: SurveySnapshot) -> None:
    if snapshot.message_id is None:
        return
    try:
        channel = bot.get_channel(snapshot.channel_id) or await bot.fetch_channel(
            snapshot.channel_id
        )
        message = await channel.fetch_message(snapshot.message_id)
        await message.edit(
            embed=build_survey_embed(snapshot),
            attachments=[],
            files=[build_survey_file(snapshot)],
            view=SurveyPostView(snapshot),
            allowed_mentions=no_broad_mentions(),
        )
    except Exception:
        logger.exception(
            "survey_admin_update_refresh_failed survey_id=%s message_id=%s",
            snapshot.survey_id,
            snapshot.message_id,
        )
        await record_message_edit_failed(
            survey_id=snapshot.survey_id,
            actor_discord_user_id=None,
            source="survey_update",
        )
        raise


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
    survey_id: int,
    actor_discord_user_id: int,
    refresh_callback: SurveyRefreshCallback,
    **changes,
) -> None:
    try:
        snapshot = await update_survey(
            survey_id=survey_id,
            actor_discord_user_id=actor_discord_user_id,
            **changes,
        )
    except VoteValidationError as exc:
        await send_ephemeral(interaction, f"Survey not updated: {exc}")
        return
    except Exception:
        logger.exception("survey_admin_update_apply_failed survey_id=%s", survey_id)
        await send_ephemeral(interaction, "Survey could not be updated. Please try again.")
        return

    try:
        await refresh_callback(interaction.client, snapshot)
    except Exception:
        await send_ephemeral(
            interaction,
            f"Survey #{survey_id} was updated, but the public message could not be refreshed.",
        )
        return

    await send_ephemeral(interaction, f"Survey #{survey_id} updated.")


class _SurveyTextUpdateModal(discord.ui.Modal):
    def __init__(
        self,
        *,
        survey_id: int,
        actor_discord_user_id: int,
        field: str,
        label: str,
        current_value: str,
        max_length: int,
        refresh_callback: SurveyRefreshCallback,
    ) -> None:
        super().__init__(title=f"Update survey {label}", timeout=300)
        self.survey_id = int(survey_id)
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
        await _apply_update(
            interaction,
            survey_id=self.survey_id,
            actor_discord_user_id=self.actor_discord_user_id,
            refresh_callback=self.refresh_callback,
            **{self.field: str(self.value_input.value or "")},
        )


class _SurveyReminderModal(discord.ui.Modal):
    def __init__(
        self,
        *,
        survey_id: int,
        actor_discord_user_id: int,
        refresh_callback: SurveyRefreshCallback,
    ) -> None:
        super().__init__(title="Update survey reminders", timeout=300)
        self.survey_id = int(survey_id)
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
            survey_id=self.survey_id,
            actor_discord_user_id=self.actor_discord_user_id,
            refresh_callback=self.refresh_callback,
            reminder_offsets=str(self.offsets.value or ""),
        )


class _SurveyDurationSelect(discord.ui.Select):
    def __init__(self, parent_view: SurveyAdminUpdateView) -> None:
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
            survey_id=self.parent_view.survey_id,
            actor_discord_user_id=self.parent_view.owner_user_id,
            refresh_callback=self.parent_view.refresh_callback,
            close_time_utc=self.values[0],
        )


class _SurveyBoolSelect(discord.ui.Select):
    def __init__(self, parent_view: SurveyAdminUpdateView, *, field: str, label: str) -> None:
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
        if self.field == "allow_response_change" and self.parent_view.snapshot.total_responses > 0:
            await send_ephemeral(
                interaction, "Response changes cannot be edited after responses exist."
            )
            return
        await _apply_update(
            interaction,
            survey_id=self.parent_view.survey_id,
            actor_discord_user_id=self.parent_view.owner_user_id,
            refresh_callback=self.parent_view.refresh_callback,
            **{self.field: self.values[0] == "yes"},
        )


class _SurveyResultVisibilitySelect(discord.ui.Select):
    def __init__(self, parent_view: SurveyAdminUpdateView) -> None:
        self.parent_view = parent_view
        options = [
            discord.SelectOption(
                label=label,
                value=value,
                default=value == parent_view.snapshot.result_visibility,
            )
            for value, label in RESULT_VISIBILITY_CHOICES.items()
        ]
        super().__init__(
            placeholder="Result visibility",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await self.parent_view.guard(interaction):
            return
        if self.parent_view.snapshot.total_responses > 0:
            await send_ephemeral(
                interaction, "Result visibility cannot be edited after responses exist."
            )
            return
        await _apply_update(
            interaction,
            survey_id=self.parent_view.survey_id,
            actor_discord_user_id=self.parent_view.owner_user_id,
            refresh_callback=self.parent_view.refresh_callback,
            result_visibility=self.values[0],
        )


class _SurveyTargetSelect(discord.ui.Select):
    def __init__(self, parent_view: SurveyAdminUpdateView) -> None:
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
                discord.SelectOption(label="Response changes", value="response_changes"),
                discord.SelectOption(label="Result visibility", value="result_visibility"),
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await self.parent_view.guard(interaction):
            return
        target = self.values[0]
        if target == "title":
            await interaction.response.send_modal(
                _SurveyTextUpdateModal(
                    survey_id=self.parent_view.survey_id,
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
                _SurveyTextUpdateModal(
                    survey_id=self.parent_view.survey_id,
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
                _SurveyReminderModal(
                    survey_id=self.parent_view.survey_id,
                    actor_discord_user_id=self.parent_view.owner_user_id,
                    refresh_callback=self.parent_view.refresh_callback,
                )
            )
            return
        if target == "close_time":
            view = discord.ui.View(timeout=180)
            view.add_item(_SurveyDurationSelect(self.parent_view))
            await interaction.response.edit_message(content="Choose the new close time:", view=view)
            return
        if target == "option_icons":
            if self.parent_view.snapshot.total_responses > 0:
                await send_ephemeral(
                    interaction, "Option icons cannot be edited after responses exist."
                )
                return
            view = _SurveyQuestionIconView(self.parent_view)
            if not view.children:
                await send_ephemeral(interaction, "This survey has no option-based questions.")
                return
            await interaction.response.edit_message(content="Choose a question:", view=view)
            return
        if target == "response_changes":
            view = discord.ui.View(timeout=180)
            view.add_item(
                _SurveyBoolSelect(
                    self.parent_view,
                    field="allow_response_change",
                    label="Allow response changes?",
                )
            )
            await interaction.response.edit_message(content="Allow response changes?", view=view)
            return
        if target == "result_visibility":
            view = discord.ui.View(timeout=180)
            view.add_item(_SurveyResultVisibilitySelect(self.parent_view))
            await interaction.response.edit_message(content="Choose result visibility:", view=view)
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
        view.add_item(_SurveyBoolSelect(self.parent_view, field=field, label=label))
        await interaction.response.edit_message(content=label, view=view)


class _SurveyQuestionIconSelect(discord.ui.Select):
    def __init__(self, parent_view: _SurveyQuestionIconView) -> None:
        self.parent_view = parent_view
        options = [
            discord.SelectOption(
                label=f"Q{question.sort_order}: {question.prompt}"[:100],
                value=str(question.question_id),
                description=f"{len(question.options)} options",
            )
            for question in parent_view.questions
        ]
        super().__init__(
            placeholder="Question to polish",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await self.parent_view.update_view.guard(interaction):
            return
        try:
            question_id = int(self.values[0])
        except (IndexError, TypeError, ValueError):
            await send_ephemeral(interaction, "Choose a valid question.")
            return
        question = next(
            (item for item in self.parent_view.questions if int(item.question_id) == question_id),
            None,
        )
        if question is None:
            await send_ephemeral(interaction, "Choose a valid question.")
            return
        view = _SurveyOptionIconView(self.parent_view.update_view, question=question)
        await interaction.response.edit_message(content="Choose an option to polish:", view=view)


class _SurveyQuestionIconView(discord.ui.View):
    def __init__(self, update_view: SurveyAdminUpdateView) -> None:
        super().__init__(timeout=180)
        self.update_view = update_view
        self.questions = tuple(
            question for question in update_view.snapshot.questions if question.options
        )
        if self.questions:
            self.add_item(_SurveyQuestionIconSelect(self))


class _SurveyOptionIconSelect(discord.ui.Select):
    def __init__(self, parent_view: _SurveyOptionIconView) -> None:
        self.parent_view = parent_view
        options = [
            discord.SelectOption(
                label=option.label[:100],
                value=str(option.option_id),
                description=option.emoji.text[:100] if option.emoji else None,
                emoji=_discord_emoji(option.emoji),
            )
            for option in parent_view.question.options
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
                for item in self.parent_view.question.options
                if int(item.option_id) == option_id
            ),
            None,
        )
        if option is None:
            await send_ephemeral(interaction, "Choose a valid option.")
            return
        await interaction.response.send_modal(
            _SurveyOptionIconModal(self.parent_view.update_view, option_id=option_id)
        )


class _SurveyOptionIconView(discord.ui.View):
    def __init__(self, update_view: SurveyAdminUpdateView, *, question: SurveyQuestion) -> None:
        super().__init__(timeout=180)
        self.update_view = update_view
        self.question = question
        self.add_item(_SurveyOptionIconSelect(self))


class _SurveyOptionIconModal(discord.ui.Modal):
    def __init__(self, parent_view: SurveyAdminUpdateView, *, option_id: int) -> None:
        option = next(
            option
            for question in parent_view.snapshot.questions
            for option in question.options
            if int(option.option_id) == int(option_id)
        )
        super().__init__(title="Survey option icon", timeout=300)
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
            snapshot = await update_survey_option_emoji(
                survey_id=self.parent_view.survey_id,
                option_id=self.option_id,
                emoji_value=str(self.icon.value or ""),
                actor_discord_user_id=self.parent_view.owner_user_id,
            )
        except VoteValidationError as exc:
            await send_ephemeral(interaction, f"Option icon not saved: {exc}")
            return
        except Exception:
            logger.exception(
                "survey_admin_option_icon_update_failed survey_id=%s option_id=%s",
                self.parent_view.survey_id,
                self.option_id,
            )
            await send_ephemeral(interaction, "Option icon could not be saved. Please try again.")
            return

        self.parent_view.snapshot = snapshot
        try:
            await self.parent_view.refresh_callback(interaction.client, snapshot)
        except Exception:
            await send_ephemeral(
                interaction,
                f"Survey #{self.parent_view.survey_id} was updated, "
                "but the public message could not be refreshed.",
            )
            return
        label = next(
            (
                option_display_label(option.label, option.emoji)
                for question in snapshot.questions
                for option in question.options
                if int(option.option_id) == self.option_id
            ),
            "option",
        )
        await send_ephemeral(interaction, f"Option icon saved for {label}.")


class SurveyAdminUpdateView(discord.ui.View):
    def __init__(
        self,
        snapshot: SurveySnapshot,
        *,
        owner_user_id: int,
        refresh_callback: SurveyRefreshCallback = refresh_public_survey_message,
    ) -> None:
        super().__init__(timeout=300)
        self.snapshot = snapshot
        self.survey_id = int(snapshot.survey_id)
        self.owner_user_id = int(owner_user_id)
        self.refresh_callback = refresh_callback
        self.add_item(_SurveyTargetSelect(self))

    async def guard(self, interaction: discord.Interaction) -> bool:
        if int(getattr(interaction.user, "id", 0)) != self.owner_user_id:
            await send_ephemeral(interaction, "This survey update panel belongs to another admin.")
            return False
        if self.snapshot.status != "Open":
            await send_ephemeral(interaction, "This survey is already closed.")
            return False
        return True


__all__ = [
    "SurveyAdminUpdateView",
    "refresh_public_survey_message",
]
