from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
import logging

import discord

from core.interaction_safety import send_ephemeral
from voting import survey_service
from voting.survey_models import (
    SURVEY_QUESTION_MULTI_SELECT,
    SurveyQuestionCreateRequest,
    SurveySnapshot,
)
from voting.survey_presentation import (
    build_survey_embed,
    build_survey_file,
    no_broad_mentions,
)

logger = logging.getLogger(__name__)

SurveyPublishCallback = Callable[
    [discord.Interaction, tuple[SurveyQuestionCreateRequest, ...]], Awaitable[None]
]


class SurveyPostView(discord.ui.View):
    def __init__(self, snapshot: SurveySnapshot, *, disabled: bool | None = None) -> None:
        super().__init__(timeout=None)
        self.survey_id = int(snapshot.survey_id)
        closed = snapshot.status != "Open" or snapshot.closes_at_utc <= datetime.now(UTC)
        should_disable = closed if disabled is None else bool(disabled)
        self.add_item(_SurveyOpenButton(self.survey_id, disabled=should_disable))


class _SurveyOpenButton(discord.ui.Button):
    def __init__(self, survey_id: int, *, disabled: bool) -> None:
        super().__init__(
            label="Answer survey",
            style=discord.ButtonStyle.primary,
            custom_id=f"survey:{int(survey_id)}",
            disabled=disabled,
        )
        self.survey_id = int(survey_id)

    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            logger.debug("survey_open_defer_failed", exc_info=True)
        try:
            snapshot = await survey_service.get_survey_snapshot(self.survey_id)
        except Exception:
            logger.exception("survey_snapshot_failed survey_id=%s", self.survey_id)
            await send_ephemeral(interaction, "Survey could not be loaded. Please try again.")
            return
        if snapshot is None:
            await send_ephemeral(interaction, "This survey no longer exists.")
            return
        if snapshot.status != "Open" or snapshot.closes_at_utc <= datetime.now(UTC):
            await send_ephemeral(interaction, "This survey is already closed.")
            return
        selected_option_ids: dict[int, tuple[int, ...]] = {}
        try:
            selected_option_ids = await survey_service.get_existing_answer_option_ids(
                survey_id=self.survey_id,
                discord_user_id=int(interaction.user.id),
            )
        except Exception:
            logger.exception(
                "survey_existing_answers_failed survey_id=%s actor_discord_id=%s",
                self.survey_id,
                getattr(getattr(interaction, "user", None), "id", None),
            )
        panel = SurveyResponsePanel(
            snapshot,
            owner_user_id=int(interaction.user.id),
            selected_option_ids=selected_option_ids,
        )
        await send_ephemeral(interaction, panel.content(), view=panel)


class _SurveyQuestionSelect(discord.ui.Select):
    def __init__(self, parent_view: "SurveyResponsePanel") -> None:
        self.parent_view = parent_view
        question = parent_view.current_question
        selected_option_ids = set(parent_view.answers.get(question.question_id, ()))
        options = [
            discord.SelectOption(
                label=option.label[:100],
                value=str(option.option_id),
                default=int(option.option_id) in selected_option_ids,
            )
            for option in question.options[:25]
        ]
        super().__init__(
            placeholder=f"Question {question.sort_order}",
            min_values=max(1, int(question.min_selections)),
            max_values=max(1, min(int(question.max_selections), len(options))),
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if int(getattr(interaction.user, "id", 0)) != self.parent_view.owner_user_id:
            await send_ephemeral(interaction, "This survey panel belongs to another player.")
            return
        try:
            values = tuple(int(value) for value in self.values)
        except (TypeError, ValueError):
            await send_ephemeral(interaction, "One or more selected options are not valid.")
            return
        self.parent_view.answers[self.parent_view.current_question.question_id] = values
        await self.parent_view.refresh(interaction)


class _SurveyNavButton(discord.ui.Button):
    def __init__(self, parent_view: "SurveyResponsePanel", *, direction: int) -> None:
        label = "Back" if direction < 0 else "Next"
        super().__init__(
            label=label,
            style=discord.ButtonStyle.secondary,
            disabled=direction < 0 and parent_view.current_index == 0
            or direction > 0 and parent_view.current_index >= len(parent_view.snapshot.questions) - 1,
        )
        self.parent_view = parent_view
        self.direction = int(direction)

    async def callback(self, interaction: discord.Interaction) -> None:
        if int(getattr(interaction.user, "id", 0)) != self.parent_view.owner_user_id:
            await send_ephemeral(interaction, "This survey panel belongs to another player.")
            return
        self.parent_view.current_index = max(
            0,
            min(
                len(self.parent_view.snapshot.questions) - 1,
                self.parent_view.current_index + self.direction,
            ),
        )
        await self.parent_view.refresh(interaction)


class _SurveySubmitButton(discord.ui.Button):
    def __init__(self, parent_view: "SurveyResponsePanel") -> None:
        super().__init__(label="Submit", style=discord.ButtonStyle.success)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction) -> None:
        if int(getattr(interaction.user, "id", 0)) != self.parent_view.owner_user_id:
            await send_ephemeral(interaction, "This survey panel belongs to another player.")
            return
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            logger.debug("survey_submit_defer_failed", exc_info=True)
        try:
            result, snapshot = await survey_service.submit_survey_response(
                survey_id=self.parent_view.survey_id,
                discord_user_id=int(interaction.user.id),
                answers_by_question_id=self.parent_view.answers,
            )
        except survey_service.VoteValidationError as exc:
            await send_ephemeral(interaction, str(exc))
            return
        except Exception:
            logger.exception(
                "survey_submit_failed survey_id=%s actor_discord_id=%s",
                self.parent_view.survey_id,
                getattr(getattr(interaction, "user", None), "id", None),
            )
            await send_ephemeral(interaction, "Survey response could not be recorded.")
            return
        if not result.accepted or snapshot is None:
            await send_ephemeral(interaction, result.message or "Survey response could not be recorded.")
            return
        await _refresh_public_survey_message(interaction, snapshot)
        await send_ephemeral(interaction, result.message or "Survey response recorded.")


class SurveyResponsePanel(discord.ui.View):
    def __init__(
        self,
        snapshot: SurveySnapshot,
        *,
        owner_user_id: int,
        selected_option_ids: dict[int, tuple[int, ...]] | None = None,
        current_index: int = 0,
    ) -> None:
        super().__init__(timeout=600)
        self.snapshot = snapshot
        self.survey_id = int(snapshot.survey_id)
        self.owner_user_id = int(owner_user_id)
        self.current_index = int(current_index)
        self.answers: dict[int, tuple[int, ...]] = dict(selected_option_ids or {})
        self._rebuild()

    @property
    def current_question(self):
        return self.snapshot.questions[self.current_index]

    def _rebuild(self) -> None:
        self.clear_items()
        self.add_item(_SurveyQuestionSelect(self))
        self.add_item(_SurveyNavButton(self, direction=-1))
        self.add_item(_SurveyNavButton(self, direction=1))
        self.add_item(_SurveySubmitButton(self))

    def content(self) -> str:
        question = self.current_question
        question_type = "multi-select" if question.question_type == SURVEY_QUESTION_MULTI_SELECT else "single choice"
        return (
            f"Survey #{self.survey_id}: question {question.sort_order} of {len(self.snapshot.questions)}\n"
            f"{question.prompt}\n"
            f"Required {question_type}: choose {question.min_selections}-{question.max_selections}."
        )

    async def refresh(self, interaction: discord.Interaction) -> None:
        self._rebuild()
        try:
            if not interaction.response.is_done():
                await interaction.response.edit_message(content=self.content(), view=self)
                return
        except Exception:
            logger.debug("survey_panel_edit_response_failed", exc_info=True)
        try:
            await interaction.edit_original_response(content=self.content(), view=self)
        except Exception:
            logger.exception("survey_panel_refresh_failed survey_id=%s", self.survey_id)


class SurveyBuilderView(discord.ui.View):
    def __init__(
        self,
        *,
        owner_user_id: int,
        publish_callback: SurveyPublishCallback,
        questions: tuple[SurveyQuestionCreateRequest, ...] = (),
    ) -> None:
        super().__init__(timeout=900)
        self.owner_user_id = int(owner_user_id)
        self.publish_callback = publish_callback
        self.questions: list[SurveyQuestionCreateRequest] = list(questions)
        self._rebuild()

    def _rebuild(self) -> None:
        self.clear_items()
        self.add_item(_BuilderAddQuestionButton(self))
        self.add_item(_BuilderPublishButton(self))

    def summary(self) -> str:
        if not self.questions:
            return "No questions added yet."
        lines = [
            f"{index}. {question.prompt[:70]} ({question.question_type}, {len(question.options)} options)"
            for index, question in enumerate(self.questions, start=1)
        ]
        return "\n".join(lines)


class _BuilderAddQuestionButton(discord.ui.Button):
    def __init__(self, parent_view: SurveyBuilderView) -> None:
        super().__init__(
            label="Add question",
            style=discord.ButtonStyle.primary,
            disabled=len(parent_view.questions) >= survey_service.MAX_SURVEY_QUESTIONS,
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction) -> None:
        if int(getattr(interaction.user, "id", 0)) != self.parent_view.owner_user_id:
            await send_ephemeral(interaction, "This survey builder belongs to another admin.")
            return
        await interaction.response.send_modal(_SurveyQuestionModal(self.parent_view))


class _BuilderPublishButton(discord.ui.Button):
    def __init__(self, parent_view: SurveyBuilderView) -> None:
        super().__init__(
            label="Publish",
            style=discord.ButtonStyle.success,
            disabled=len(parent_view.questions) < survey_service.MIN_SURVEY_QUESTIONS,
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction) -> None:
        if int(getattr(interaction.user, "id", 0)) != self.parent_view.owner_user_id:
            await send_ephemeral(interaction, "This survey builder belongs to another admin.")
            return
        await self.parent_view.publish_callback(interaction, tuple(self.parent_view.questions))


class _SurveyQuestionModal(discord.ui.Modal):
    def __init__(self, parent_view: SurveyBuilderView) -> None:
        super().__init__(title="Add survey question")
        self.parent_view = parent_view
        self.prompt = discord.ui.InputText(
            label="Question",
            max_length=survey_service.MAX_SURVEY_QUESTION_PROMPT_LEN,
        )
        self.question_type = discord.ui.InputText(
            label="Type: SingleChoice or MultiSelect",
            required=False,
            max_length=20,
            value="SingleChoice",
        )
        self.options = discord.ui.InputText(
            label="Options, one per line",
            style=discord.InputTextStyle.long,
            max_length=500,
        )
        self.min_selections = discord.ui.InputText(
            label="Minimum selections",
            required=False,
            max_length=2,
            value="1",
        )
        self.max_selections = discord.ui.InputText(
            label="Maximum selections",
            required=False,
            max_length=2,
            value="1",
        )
        for field in (
            self.prompt,
            self.question_type,
            self.options,
            self.min_selections,
            self.max_selections,
        ):
            self.add_item(field)

    async def callback(self, interaction: discord.Interaction) -> None:
        if int(getattr(interaction.user, "id", 0)) != self.parent_view.owner_user_id:
            await send_ephemeral(interaction, "This survey builder belongs to another admin.")
            return
        try:
            options = tuple(
                line.strip() for line in str(self.options.value or "").splitlines() if line.strip()
            )
            question = survey_service.build_question_request(
                prompt=str(self.prompt.value or ""),
                question_type=str(self.question_type.value or ""),
                options=options,
                min_selections=int(str(self.min_selections.value or "1")),
                max_selections=int(str(self.max_selections.value or "1")),
            )
        except (TypeError, ValueError, survey_service.VoteValidationError) as exc:
            await send_ephemeral(interaction, f"Question not added: {exc}")
            return
        self.parent_view.questions.append(question)
        self.parent_view._rebuild()
        await interaction.response.edit_message(
            content=f"Survey builder updated.\n\n{self.parent_view.summary()}",
            view=self.parent_view,
        )


async def _refresh_public_survey_message(interaction: discord.Interaction, snapshot: SurveySnapshot) -> None:
    try:
        channel = interaction.client.get_channel(snapshot.channel_id) or await interaction.client.fetch_channel(
            snapshot.channel_id
        )
        message = await channel.fetch_message(snapshot.message_id) if snapshot.message_id else None
        if message is not None:
            await message.edit(
                embed=build_survey_embed(snapshot),
                attachments=[],
                files=[build_survey_file(snapshot)],
                view=SurveyPostView(snapshot),
                allowed_mentions=no_broad_mentions(),
            )
    except Exception:
        logger.exception(
            "survey_message_edit_failed survey_id=%s message_id=%s",
            snapshot.survey_id,
            snapshot.message_id,
        )
        await survey_service.record_message_edit_failed(
            survey_id=snapshot.survey_id,
            actor_discord_user_id=int(interaction.user.id),
            source="survey_response",
        )


def disabled_survey_view(snapshot: SurveySnapshot) -> SurveyPostView:
    return SurveyPostView(snapshot, disabled=True)
