from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
import logging

import discord

from core.interaction_safety import send_ephemeral
from voting import survey_service
from voting.survey_models import (
    SURVEY_QUESTION_MULTI_SELECT,
    SURVEY_QUESTION_TEXT,
    SurveyQuestionCreateRequest,
    SurveyResponsePayload,
    SurveySnapshot,
)
from voting.survey_presentation import (
    build_survey_embed,
    build_survey_file,
    no_broad_mentions,
)

logger = logging.getLogger(__name__)

SURVEY_INCOMPLETE_HELP = "You must answer all required questions to submit the survey."

SurveyPublishCallback = Callable[
    [discord.Interaction, tuple[SurveyQuestionCreateRequest, ...]], Awaitable[bool]
]
SurveyBuilderTimeoutCallback = Callable[["SurveyBuilderView"], Awaitable[None]]

_SURVEY_BUILDER_TIMEOUT_SECONDS = 14 * 60


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
        response_payload = SurveyResponsePayload({}, {}, {})
        try:
            response_payload = await survey_service.get_existing_response_payload(
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
            selected_option_ids=response_payload.selected_option_ids,
            text_answers=response_payload.text_answers,
            detail_text_by_option=response_payload.detail_text_by_option,
        )
        await send_ephemeral(interaction, panel.content(), view=panel)


class _SurveyQuestionSelect(discord.ui.Select):
    def __init__(self, parent_view: SurveyResponsePanel) -> None:
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
            min_values=0 if not question.is_required else max(1, int(question.min_selections)),
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
        question = self.parent_view.current_question
        existing_detail = self.parent_view.detail_text_for_question(question)
        self.parent_view.answers[question.question_id] = values
        self.parent_view.set_detail_text_for_question(question, existing_detail)
        await self.parent_view.refresh(interaction)


class _SurveyTextAnswerButton(discord.ui.Button):
    def __init__(self, parent_view: SurveyResponsePanel) -> None:
        super().__init__(
            label="Response (required)" if parent_view.current_question.is_required else "Response",
            style=discord.ButtonStyle.primary,
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction) -> None:
        if int(getattr(interaction.user, "id", 0)) != self.parent_view.owner_user_id:
            await send_ephemeral(interaction, "This survey panel belongs to another player.")
            return
        await interaction.response.send_modal(_SurveyTextAnswerModal(self.parent_view))


class _SurveyDetailOptionSelect(discord.ui.Select):
    def __init__(self, parent_view: SurveyResponsePanel) -> None:
        self.parent_view = parent_view
        question = parent_view.current_question
        anchor_option_id = parent_view.detail_anchor_option_id(question)
        has_detail = bool(parent_view.detail_text_for_question(question))
        if anchor_option_id is None:
            options = [discord.SelectOption(label="Select an option first", value="none")]
        else:
            options = [
                discord.SelectOption(
                    label=(
                        "Edit details about your response"
                        if has_detail
                        else "Add more details about your response"
                    ),
                    value=str(anchor_option_id),
                    description="Optional note for this question",
                    default=False,
                )
            ]
        super().__init__(
            placeholder="Add details",
            min_values=1,
            max_values=1,
            options=options,
            disabled=anchor_option_id is None,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if int(getattr(interaction.user, "id", 0)) != self.parent_view.owner_user_id:
            await send_ephemeral(interaction, "This survey panel belongs to another player.")
            return
        question = self.parent_view.current_question
        option_id = self.parent_view.detail_anchor_option_id(question)
        if option_id is None:
            await send_ephemeral(interaction, "Select an answer before adding details.")
            return
        await interaction.response.send_modal(_SurveyDetailModal(self.parent_view, option_id))


class _SurveyNavButton(discord.ui.Button):
    def __init__(self, parent_view: SurveyResponsePanel, *, direction: int) -> None:
        label = "Back" if direction < 0 else "Next"
        super().__init__(
            label=label,
            style=discord.ButtonStyle.secondary,
            disabled=(direction < 0 and parent_view.current_index == 0)
            or (
                direction > 0
                and parent_view.current_index >= len(parent_view.snapshot.questions) - 1
            ),
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
    def __init__(self, parent_view: SurveyResponsePanel) -> None:
        super().__init__(
            label="Submit",
            style=discord.ButtonStyle.success,
            disabled=not parent_view.is_complete(),
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction) -> None:
        if int(getattr(interaction.user, "id", 0)) != self.parent_view.owner_user_id:
            await send_ephemeral(interaction, "This survey panel belongs to another player.")
            return
        if not self.parent_view.is_complete():
            await send_ephemeral(interaction, SURVEY_INCOMPLETE_HELP)
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
                text_answers_by_question_id=self.parent_view.text_answers,
                detail_text_by_question_option=self.parent_view.normalized_detail_text_by_option(),
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
            await send_ephemeral(
                interaction, result.message or "Survey response could not be recorded."
            )
            return
        await _refresh_public_survey_message(interaction, snapshot)
        message = result.message or "Survey response recorded."
        self.parent_view.stop()
        try:
            if not interaction.response.is_done():
                await interaction.response.edit_message(content=message, view=None)
                return
        except Exception:
            logger.debug("survey_submit_ack_response_edit_failed", exc_info=True)
        try:
            await interaction.edit_original_response(content=message, view=None)
        except Exception:
            logger.debug("survey_submit_ack_edit_failed", exc_info=True)
            await send_ephemeral(interaction, message)


class SurveyResponsePanel(discord.ui.View):
    def __init__(
        self,
        snapshot: SurveySnapshot,
        *,
        owner_user_id: int,
        selected_option_ids: dict[int, tuple[int, ...]] | None = None,
        text_answers: dict[int, str] | None = None,
        detail_text_by_option: dict[tuple[int, int], str] | None = None,
        current_index: int = 0,
    ) -> None:
        super().__init__(timeout=600)
        self.snapshot = snapshot
        self.survey_id = int(snapshot.survey_id)
        self.owner_user_id = int(owner_user_id)
        self.current_index = int(current_index)
        self.answers: dict[int, tuple[int, ...]] = dict(selected_option_ids or {})
        self.text_answers: dict[int, str] = dict(text_answers or {})
        self.detail_text_by_option: dict[tuple[int, int], str] = dict(detail_text_by_option or {})
        self._rebuild()

    @property
    def current_question(self):
        return self.snapshot.questions[self.current_index]

    def is_complete(self) -> bool:
        try:
            survey_service.validate_response_payload(
                self.snapshot,
                answers_by_question_id=self.answers,
                text_answers_by_question_id=self.text_answers,
                detail_text_by_question_option=self.normalized_detail_text_by_option(),
            )
        except survey_service.VoteValidationError:
            return False
        return True

    def detail_anchor_option_id(self, question) -> int | None:
        selected_option_ids = set(self.answers.get(question.question_id, ()))
        for option in question.options:
            if option.option_id in selected_option_ids:
                return int(option.option_id)
        return None

    def detail_text_for_question(self, question) -> str:
        selected_option_ids = set(self.answers.get(question.question_id, ()))
        for option in question.options:
            if option.option_id not in selected_option_ids:
                continue
            text = self.detail_text_by_option.get((question.question_id, option.option_id), "")
            if text.strip():
                return text.strip()
        for (question_id, _option_id), text in sorted(self.detail_text_by_option.items()):
            if question_id == question.question_id and text.strip():
                return text.strip()
        return ""

    def set_detail_text_for_question(self, question, text: str) -> None:
        for key in tuple(self.detail_text_by_option):
            if key[0] == question.question_id:
                self.detail_text_by_option.pop(key, None)
        clean_text = str(text or "").strip()
        anchor_option_id = self.detail_anchor_option_id(question)
        if clean_text and anchor_option_id is not None:
            self.detail_text_by_option[(question.question_id, anchor_option_id)] = clean_text

    def normalized_detail_text_by_option(self) -> dict[tuple[int, int], str]:
        normalized: dict[tuple[int, int], str] = {}
        for question in self.snapshot.questions:
            if not question.allow_details:
                continue
            anchor_option_id = self.detail_anchor_option_id(question)
            detail_text = self.detail_text_for_question(question)
            if anchor_option_id is not None and detail_text:
                normalized[(question.question_id, anchor_option_id)] = detail_text
        return normalized

    def _rebuild(self) -> None:
        self.clear_items()
        if self.current_question.question_type == SURVEY_QUESTION_TEXT:
            self.add_item(_SurveyTextAnswerButton(self))
        else:
            self.add_item(_SurveyQuestionSelect(self))
            if self.current_question.allow_details:
                self.add_item(_SurveyDetailOptionSelect(self))
        self.add_item(_SurveyNavButton(self, direction=-1))
        self.add_item(_SurveyNavButton(self, direction=1))
        self.add_item(_SurveySubmitButton(self))

    def content(self) -> str:
        question = self.current_question
        incomplete_line = f"\n{SURVEY_INCOMPLETE_HELP}" if not self.is_complete() else ""
        if question.question_type == SURVEY_QUESTION_TEXT:
            saved = bool(self.text_answers.get(question.question_id, "").strip())
            requirement = "required" if question.is_required else "optional"
            state = (
                "complete" if saved else ("not yet complete" if question.is_required else "skipped")
            )
            return (
                f"Survey #{self.survey_id}: question {question.sort_order} of {len(self.snapshot.questions)}\n"
                f"{question.prompt}\n"
                f"{requirement.title()} text response: {state}"
                f"{incomplete_line}"
            )
        question_type = (
            "multi-select"
            if question.question_type == SURVEY_QUESTION_MULTI_SELECT
            else "single choice"
        )
        detail_count = 1 if self.detail_text_for_question(question) else 0
        detail_line = f"\nDetails: {detail_count} saved." if question.allow_details else ""
        requirement = "Required" if question.is_required else "Optional"
        answer_state = "answered" if self.answers.get(question.question_id) else "not yet complete"
        if not question.is_required and not self.answers.get(question.question_id):
            answer_state = "skipped"
        return (
            f"Survey #{self.survey_id}: question {question.sort_order} of {len(self.snapshot.questions)}\n"
            f"{question.prompt}\n"
            f"{requirement} {question_type}: choose {question.min_selections}-{question.max_selections} "
            f"({answer_state})."
            f"{detail_line}"
            f"{incomplete_line}"
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


class _SurveyTextAnswerModal(discord.ui.Modal):
    def __init__(self, parent_view: SurveyResponsePanel) -> None:
        super().__init__(title="Survey text answer")
        self.parent_view = parent_view
        question = parent_view.current_question
        self.answer = discord.ui.InputText(
            label=f"Response (max {survey_service.MAX_SURVEY_TEXT_ANSWER_LEN} characters)",
            style=discord.InputTextStyle.long,
            required=question.is_required,
            max_length=survey_service.MAX_SURVEY_TEXT_ANSWER_LEN,
            placeholder=(
                ("Required response. " if question.is_required else "Optional response. ")
                + f"Max {survey_service.MAX_SURVEY_TEXT_ANSWER_LEN} characters."
            ),
            value=parent_view.text_answers.get(question.question_id, ""),
        )
        self.add_item(self.answer)

    async def callback(self, interaction: discord.Interaction) -> None:
        if int(getattr(interaction.user, "id", 0)) != self.parent_view.owner_user_id:
            await send_ephemeral(interaction, "This survey panel belongs to another player.")
            return
        question = self.parent_view.current_question
        text = str(self.answer.value or "").strip()
        if not text:
            if question.is_required:
                await send_ephemeral(interaction, "Text answer is required.")
                return
            self.parent_view.text_answers.pop(question.question_id, None)
        else:
            self.parent_view.text_answers[question.question_id] = text
        await self.parent_view.refresh(interaction)


class _SurveyDetailModal(discord.ui.Modal):
    def __init__(self, parent_view: SurveyResponsePanel, option_id: int) -> None:
        super().__init__(title="Question details")
        self.parent_view = parent_view
        self.option_id = int(option_id)
        question = parent_view.current_question
        self.detail = discord.ui.InputText(
            label=f"Add more details (max {survey_service.MAX_SURVEY_DETAIL_LEN})",
            style=discord.InputTextStyle.long,
            required=False,
            max_length=survey_service.MAX_SURVEY_DETAIL_LEN,
            placeholder=(
                "Optional context for your response. "
                f"Max {survey_service.MAX_SURVEY_DETAIL_LEN} characters."
            ),
            value=parent_view.detail_text_for_question(question),
        )
        self.add_item(self.detail)

    async def callback(self, interaction: discord.Interaction) -> None:
        if int(getattr(interaction.user, "id", 0)) != self.parent_view.owner_user_id:
            await send_ephemeral(interaction, "This survey panel belongs to another player.")
            return
        question = self.parent_view.current_question
        text = str(self.detail.value or "").strip()
        self.parent_view.set_detail_text_for_question(question, text)
        await self.parent_view.refresh(interaction)


class SurveyBuilderView(discord.ui.View):
    def __init__(
        self,
        *,
        owner_user_id: int,
        publish_callback: SurveyPublishCallback,
        questions: tuple[SurveyQuestionCreateRequest, ...] = (),
        timeout_edit_callback: SurveyBuilderTimeoutCallback | None = None,
    ) -> None:
        super().__init__(timeout=_SURVEY_BUILDER_TIMEOUT_SECONDS)
        self.owner_user_id = int(owner_user_id)
        self.publish_callback = publish_callback
        self.timeout_edit_callback = timeout_edit_callback
        self.questions: list[SurveyQuestionCreateRequest] = list(questions)
        self.draft_prompt = ""
        self.draft_options: list[str] = []
        self.draft_min_selections = 1
        self.draft_max_selections = 1
        self.draft_is_text = False
        self.draft_allow_details = False
        self.draft_is_required = True
        self.publish_in_progress = False
        self.published = False
        self.expired = False
        self._rebuild()

    def _rebuild(self) -> None:
        self.clear_items()
        self.add_item(_BuilderPromptButton(self))
        self.add_item(_BuilderAddOptionButton(self))
        self.add_item(_BuilderRemoveOptionButton(self))
        self.add_item(_BuilderSaveQuestionButton(self))
        self.add_item(_BuilderClearDraftButton(self))
        self.add_item(_BuilderQuestionTypeSelect(self))
        self.add_item(_BuilderSelectionSelect(self, kind="min"))
        self.add_item(_BuilderSelectionSelect(self, kind="max"))
        self.add_item(_BuilderRequiredToggleButton(self))
        self.add_item(_BuilderDetailsToggleButton(self))
        self.add_item(_BuilderPublishButton(self))

    @property
    def builder_locked(self) -> bool:
        return self.publish_in_progress or self.published or self.expired

    @property
    def has_draft(self) -> bool:
        return bool(
            self.draft_prompt.strip()
            or self.draft_options
            or self.draft_is_text
            or self.draft_allow_details
            or not self.draft_is_required
        )

    @property
    def draft_question_type(self) -> str:
        if self.draft_is_text:
            return "Text"
        return "MultiSelect" if self.draft_max_selections > 1 else "SingleChoice"

    @property
    def draft_mode_label(self) -> str:
        if self.draft_is_text:
            return "text"
        return "multi-select" if self.draft_max_selections > 1 else "single choice"

    @property
    def draft_ready(self) -> bool:
        return (
            bool(self.draft_prompt.strip())
            and (
                self.draft_is_text
                or (
                    len(self.draft_options) >= survey_service.MIN_SURVEY_OPTIONS
                    and self.draft_min_selections >= 1
                    and self.draft_max_selections >= self.draft_min_selections
                    and self.draft_max_selections <= len(self.draft_options)
                )
            )
            and len(self.questions) < survey_service.MAX_SURVEY_QUESTIONS
        )

    def _sync_selection_bounds(self) -> None:
        option_count = len(self.draft_options)
        if option_count <= 0:
            self.draft_min_selections = 1
            self.draft_max_selections = 1
            return
        self.draft_max_selections = max(1, min(self.draft_max_selections, option_count))
        self.draft_min_selections = max(
            1,
            min(self.draft_min_selections, self.draft_max_selections),
        )

    def _clear_draft(self) -> None:
        self.draft_prompt = ""
        self.draft_options = []
        self.draft_min_selections = 1
        self.draft_max_selections = 1
        self.draft_is_text = False
        self.draft_allow_details = False
        self.draft_is_required = True

    async def refresh(self, interaction: discord.Interaction, *, prefix: str) -> None:
        self._rebuild()
        content = f"{prefix}\n\n{self.summary()}"
        try:
            if not interaction.response.is_done():
                await interaction.response.edit_message(content=content, view=self)
                return
        except Exception:
            logger.debug("survey_builder_response_edit_failed", exc_info=True)
        try:
            await interaction.edit_original_response(content=content, view=self)
        except Exception:
            logger.exception("survey_builder_refresh_failed")

    async def on_timeout(self) -> None:
        if self.published:
            return
        self.expired = True
        for child in self.children:
            if hasattr(child, "disabled"):
                child.disabled = True
        if self.timeout_edit_callback is None:
            return
        try:
            await self.timeout_edit_callback(self)
        except Exception:
            logger.debug("survey_builder_timeout_edit_failed", exc_info=True)

    def expired_content(self) -> str:
        return (
            "Survey builder expired. No survey was published.\n\n"
            "Run `/vote_admin survey_create` again if you still need it.\n\n"
            f"{self.summary()}"
        )

    def build_draft_question(self) -> SurveyQuestionCreateRequest:
        question = survey_service.build_question_request(
            prompt=self.draft_prompt,
            question_type=(SURVEY_QUESTION_TEXT if self.draft_is_text else None),
            options=() if self.draft_is_text else tuple(self.draft_options),
            min_selections=0 if self.draft_is_text else self.draft_min_selections,
            max_selections=0 if self.draft_is_text else self.draft_max_selections,
            allow_details=False if self.draft_is_text else self.draft_allow_details,
            is_required=self.draft_is_required,
        )
        self._clear_draft()
        return question

    def summary(self) -> str:
        lines = [f"Questions: {len(self.questions)}/{survey_service.MAX_SURVEY_QUESTIONS}"]
        if self.questions:
            lines.extend(
                f"{index}. {question.prompt[:70]} "
                f"({question.question_type}, {question.max_selections} max, {len(question.options)} options"
                f"{', details' if question.allow_details else ''}, "
                f"{'required' if question.is_required else 'optional'})"
                for index, question in enumerate(self.questions, start=1)
            )
        else:
            lines.append("Saved: none")
        prompt = self.draft_prompt.strip() or "not set"
        lines.extend(
            (
                "",
                f"Draft question: {prompt} "
                f"({len(self.draft_prompt.strip())}/{survey_service.MAX_SURVEY_QUESTION_PROMPT_LEN})",
                f"Draft type: {self.draft_mode_label}",
                f"Requirement: {'required' if self.draft_is_required else 'optional'}",
                f"Draft options: {len(self.draft_options)}/{survey_service.MAX_SURVEY_OPTIONS}",
            )
        )
        if self.draft_options:
            lines.extend(f"- {option}" for option in self.draft_options)
        if not self.draft_is_text:
            lines.append(
                f"Selections: {self.draft_min_selections}-{self.draft_max_selections} "
                f"({self.draft_mode_label})"
            )
            lines.append(f"Add details: {'enabled' if self.draft_allow_details else 'disabled'}")
        return "\n".join(lines)


def _builder_option_count(parent_view: SurveyBuilderView) -> int:
    return len(parent_view.draft_options)


def _builder_disabled(parent_view: SurveyBuilderView) -> bool:
    return (
        parent_view.builder_locked
        or len(parent_view.questions) >= survey_service.MAX_SURVEY_QUESTIONS
    )


class _BuilderPromptButton(discord.ui.Button):
    def __init__(self, parent_view: SurveyBuilderView) -> None:
        super().__init__(
            label="Draft question",
            style=discord.ButtonStyle.primary,
            disabled=_builder_disabled(parent_view),
            row=0,
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction) -> None:
        if int(getattr(interaction.user, "id", 0)) != self.parent_view.owner_user_id:
            await send_ephemeral(interaction, "This survey builder belongs to another admin.")
            return
        await interaction.response.send_modal(_SurveyQuestionPromptModal(self.parent_view))


class _BuilderAddOptionButton(discord.ui.Button):
    def __init__(self, parent_view: SurveyBuilderView) -> None:
        super().__init__(
            label=f"Option {_builder_option_count(parent_view)}/{survey_service.MAX_SURVEY_OPTIONS}",
            style=discord.ButtonStyle.primary,
            disabled=_builder_disabled(parent_view)
            or parent_view.draft_is_text
            or _builder_option_count(parent_view) >= survey_service.MAX_SURVEY_OPTIONS,
            row=0,
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction) -> None:
        if int(getattr(interaction.user, "id", 0)) != self.parent_view.owner_user_id:
            await send_ephemeral(interaction, "This survey builder belongs to another admin.")
            return
        await interaction.response.send_modal(_SurveyOptionModal(self.parent_view))


class _BuilderRemoveOptionButton(discord.ui.Button):
    def __init__(self, parent_view: SurveyBuilderView) -> None:
        super().__init__(
            label="Remove option",
            style=discord.ButtonStyle.secondary,
            disabled=_builder_disabled(parent_view)
            or parent_view.draft_is_text
            or not parent_view.draft_options,
            row=0,
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction) -> None:
        if int(getattr(interaction.user, "id", 0)) != self.parent_view.owner_user_id:
            await send_ephemeral(interaction, "This survey builder belongs to another admin.")
            return
        if self.parent_view.draft_options:
            self.parent_view.draft_options.pop()
            self.parent_view._sync_selection_bounds()
        await self.parent_view.refresh(interaction, prefix="Survey builder updated.")


class _BuilderSaveQuestionButton(discord.ui.Button):
    def __init__(self, parent_view: SurveyBuilderView) -> None:
        super().__init__(
            label="Save question",
            style=discord.ButtonStyle.success,
            disabled=parent_view.builder_locked or not parent_view.draft_ready,
            row=0,
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction) -> None:
        if int(getattr(interaction.user, "id", 0)) != self.parent_view.owner_user_id:
            await send_ephemeral(interaction, "This survey builder belongs to another admin.")
            return
        if self.parent_view.builder_locked:
            await send_ephemeral(interaction, "This survey has already been published.")
            return
        if len(self.parent_view.questions) >= survey_service.MAX_SURVEY_QUESTIONS:
            await send_ephemeral(
                interaction,
                f"Question not added: surveys support at most {survey_service.MAX_SURVEY_QUESTIONS} questions.",
            )
            return
        try:
            question = self.parent_view.build_draft_question()
        except (TypeError, ValueError, survey_service.VoteValidationError) as exc:
            await send_ephemeral(interaction, f"Question not added: {exc}")
            return
        self.parent_view.questions.append(question)
        await self.parent_view.refresh(interaction, prefix="Survey question saved.")


class _BuilderClearDraftButton(discord.ui.Button):
    def __init__(self, parent_view: SurveyBuilderView) -> None:
        super().__init__(
            label="Clear draft",
            style=discord.ButtonStyle.secondary,
            disabled=parent_view.builder_locked or not parent_view.has_draft,
            row=0,
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction) -> None:
        if int(getattr(interaction.user, "id", 0)) != self.parent_view.owner_user_id:
            await send_ephemeral(interaction, "This survey builder belongs to another admin.")
            return
        self.parent_view._clear_draft()
        await self.parent_view.refresh(interaction, prefix="Survey draft cleared.")


class _BuilderQuestionTypeSelect(discord.ui.Select):
    def __init__(self, parent_view: SurveyBuilderView) -> None:
        self.parent_view = parent_view
        options = [
            discord.SelectOption(
                label="Choice",
                value="choice",
                default=not parent_view.draft_is_text,
            ),
            discord.SelectOption(
                label="Text",
                value="text",
                default=parent_view.draft_is_text,
            ),
        ]
        super().__init__(
            placeholder="Question type",
            min_values=1,
            max_values=1,
            options=options,
            disabled=parent_view.builder_locked,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if int(getattr(interaction.user, "id", 0)) != self.parent_view.owner_user_id:
            await send_ephemeral(interaction, "This survey builder belongs to another admin.")
            return
        selected = self.values[0] if self.values else "choice"
        self.parent_view.draft_is_text = selected == "text"
        if self.parent_view.draft_is_text:
            self.parent_view.draft_options = []
            self.parent_view.draft_min_selections = 1
            self.parent_view.draft_max_selections = 1
            self.parent_view.draft_allow_details = False
        else:
            self.parent_view._sync_selection_bounds()
        await self.parent_view.refresh(interaction, prefix="Survey builder updated.")


class _BuilderSelectionSelect(discord.ui.Select):
    def __init__(self, parent_view: SurveyBuilderView, *, kind: str) -> None:
        self.parent_view = parent_view
        self.kind = kind
        option_count = max(1, len(parent_view.draft_options))
        current = (
            parent_view.draft_min_selections if kind == "min" else parent_view.draft_max_selections
        )
        label = "Minimum selections" if kind == "min" else "Maximum selections"
        option_label = "Minimum" if kind == "min" else "Maximum"
        options = [
            discord.SelectOption(
                label=f"{option_label}: {value}",
                value=str(value),
                default=value == current,
            )
            for value in range(1, option_count + 1)
        ]
        super().__init__(
            placeholder=label,
            min_values=1,
            max_values=1,
            options=options,
            disabled=parent_view.builder_locked
            or parent_view.draft_is_text
            or len(parent_view.draft_options) < 2,
            row=2 if kind == "min" else 3,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if int(getattr(interaction.user, "id", 0)) != self.parent_view.owner_user_id:
            await send_ephemeral(interaction, "This survey builder belongs to another admin.")
            return
        try:
            selected = int(self.values[0])
        except (IndexError, TypeError, ValueError):
            await send_ephemeral(interaction, "Selection count was not valid.")
            return
        if self.kind == "min":
            self.parent_view.draft_min_selections = selected
            if self.parent_view.draft_max_selections < selected:
                self.parent_view.draft_max_selections = selected
        else:
            self.parent_view.draft_max_selections = selected
            if self.parent_view.draft_min_selections > selected:
                self.parent_view.draft_min_selections = selected
        self.parent_view._sync_selection_bounds()
        await self.parent_view.refresh(interaction, prefix="Survey builder updated.")


class _BuilderDetailsToggleButton(discord.ui.Button):
    def __init__(self, parent_view: SurveyBuilderView) -> None:
        super().__init__(
            label="Details on" if parent_view.draft_allow_details else "Details off",
            style=(
                discord.ButtonStyle.success
                if parent_view.draft_allow_details
                else discord.ButtonStyle.secondary
            ),
            disabled=parent_view.builder_locked or parent_view.draft_is_text,
            row=4,
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction) -> None:
        if int(getattr(interaction.user, "id", 0)) != self.parent_view.owner_user_id:
            await send_ephemeral(interaction, "This survey builder belongs to another admin.")
            return
        if self.parent_view.draft_is_text:
            await send_ephemeral(interaction, "Text questions do not use choice details.")
            return
        self.parent_view.draft_allow_details = not self.parent_view.draft_allow_details
        await self.parent_view.refresh(interaction, prefix="Survey builder updated.")


class _BuilderRequiredToggleButton(discord.ui.Button):
    def __init__(self, parent_view: SurveyBuilderView) -> None:
        super().__init__(
            label="Required" if parent_view.draft_is_required else "Optional",
            style=(
                discord.ButtonStyle.success
                if parent_view.draft_is_required
                else discord.ButtonStyle.secondary
            ),
            disabled=parent_view.builder_locked,
            row=4,
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction) -> None:
        if int(getattr(interaction.user, "id", 0)) != self.parent_view.owner_user_id:
            await send_ephemeral(interaction, "This survey builder belongs to another admin.")
            return
        self.parent_view.draft_is_required = not self.parent_view.draft_is_required
        await self.parent_view.refresh(interaction, prefix="Survey builder updated.")


class _BuilderPublishButton(discord.ui.Button):
    def __init__(self, parent_view: SurveyBuilderView) -> None:
        super().__init__(
            label="Publish",
            style=discord.ButtonStyle.success,
            disabled=parent_view.builder_locked
            or parent_view.has_draft
            or len(parent_view.questions) < survey_service.MIN_SURVEY_QUESTIONS,
            row=4,
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction) -> None:
        if int(getattr(interaction.user, "id", 0)) != self.parent_view.owner_user_id:
            await send_ephemeral(interaction, "This survey builder belongs to another admin.")
            return
        if self.parent_view.publish_in_progress or self.parent_view.published:
            await send_ephemeral(interaction, "This survey has already been published.")
            return
        if self.parent_view.has_draft:
            await send_ephemeral(interaction, "Save or clear the draft question before publishing.")
            return
        self.parent_view.publish_in_progress = True
        self.parent_view._rebuild()
        try:
            await interaction.response.edit_message(
                content=f"Survey publishing...\n\n{self.parent_view.summary()}",
                view=self.parent_view,
            )
        except Exception:
            logger.debug("survey_builder_publish_disable_failed", exc_info=True)
        try:
            published = await self.parent_view.publish_callback(
                interaction,
                tuple(self.parent_view.questions),
            )
        except Exception:
            logger.exception("survey_builder_publish_failed")
            published = False
            await send_ephemeral(interaction, "Survey not created. Please try again.")
        self.parent_view.published = bool(published)
        self.parent_view.publish_in_progress = False
        self.parent_view._rebuild()
        if not published:
            try:
                await interaction.edit_original_response(
                    content=f"Survey builder reopened.\n\n{self.parent_view.summary()}",
                    view=self.parent_view,
                )
            except Exception:
                logger.debug("survey_builder_publish_reenable_failed", exc_info=True)


class _SurveyQuestionPromptModal(discord.ui.Modal):
    def __init__(self, parent_view: SurveyBuilderView) -> None:
        super().__init__(title="Survey question prompt")
        self.parent_view = parent_view
        self.prompt = discord.ui.InputText(
            label="Draft question",
            placeholder=(
                f"Max {survey_service.MAX_SURVEY_QUESTION_PROMPT_LEN} characters; "
                "Discord stops typing at the limit."
            ),
            max_length=survey_service.MAX_SURVEY_QUESTION_PROMPT_LEN,
            value=parent_view.draft_prompt,
        )
        self.add_item(self.prompt)

    async def callback(self, interaction: discord.Interaction) -> None:
        if int(getattr(interaction.user, "id", 0)) != self.parent_view.owner_user_id:
            await send_ephemeral(interaction, "This survey builder belongs to another admin.")
            return
        if self.parent_view.publish_in_progress or self.parent_view.published:
            await send_ephemeral(interaction, "This survey has already been published.")
            return
        if len(self.parent_view.questions) >= survey_service.MAX_SURVEY_QUESTIONS:
            await send_ephemeral(
                interaction,
                f"Question not added: surveys support at most {survey_service.MAX_SURVEY_QUESTIONS} questions.",
            )
            return
        self.parent_view.draft_prompt = str(self.prompt.value or "").strip()
        await self.parent_view.refresh(interaction, prefix="Survey builder updated.")


class _SurveyOptionModal(discord.ui.Modal):
    def __init__(self, parent_view: SurveyBuilderView) -> None:
        super().__init__(title="Survey question option")
        self.parent_view = parent_view
        self.option = discord.ui.InputText(
            label=f"Option {len(parent_view.draft_options) + 1}",
            placeholder=(
                f"Max {survey_service.MAX_OPTION_LABEL_LEN} characters; "
                "Discord stops typing at the limit."
            ),
            max_length=survey_service.MAX_OPTION_LABEL_LEN,
        )
        self.add_item(self.option)

    async def callback(self, interaction: discord.Interaction) -> None:
        if int(getattr(interaction.user, "id", 0)) != self.parent_view.owner_user_id:
            await send_ephemeral(interaction, "This survey builder belongs to another admin.")
            return
        if self.parent_view.publish_in_progress or self.parent_view.published:
            await send_ephemeral(interaction, "This survey has already been published.")
            return
        if len(self.parent_view.questions) >= survey_service.MAX_SURVEY_QUESTIONS:
            await send_ephemeral(
                interaction,
                f"Question not added: surveys support at most {survey_service.MAX_SURVEY_QUESTIONS} questions.",
            )
            return
        if len(self.parent_view.draft_options) >= survey_service.MAX_SURVEY_OPTIONS:
            await send_ephemeral(
                interaction,
                f"Option not added: each question supports at most {survey_service.MAX_SURVEY_OPTIONS} options.",
            )
            return
        label = str(self.option.value or "").strip()
        if not label:
            await send_ephemeral(interaction, "Option not added: option label is required.")
            return
        if label.casefold() in {option.casefold() for option in self.parent_view.draft_options}:
            await send_ephemeral(interaction, "Option not added: options must be unique.")
            return
        self.parent_view.draft_options.append(label)
        self.parent_view._sync_selection_bounds()
        await self.parent_view.refresh(interaction, prefix="Survey builder updated.")


async def _refresh_public_survey_message(
    interaction: discord.Interaction, snapshot: SurveySnapshot
) -> None:
    try:
        channel = interaction.client.get_channel(
            snapshot.channel_id
        ) or await interaction.client.fetch_channel(snapshot.channel_id)
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
