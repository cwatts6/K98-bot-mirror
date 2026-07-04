from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import discord
import pytest

from ui.views.survey_post_view import (
    SURVEY_INCOMPLETE_HELP,
    SurveyBuilderView,
    SurveyPostView,
    SurveyResponsePanel,
    _SurveyDetailModal,
    _SurveyDetailOptionSelect,
    _SurveyOptionModal,
    _SurveyQuestionPromptModal,
    _SurveyTextAnswerModal,
)
from voting import survey_service
from voting.survey_models import (
    SURVEY_QUESTION_RATING,
    SurveyQuestion,
    SurveyQuestionCreateRequest,
    SurveyQuestionOption,
    SurveyResponsePayload,
    SurveySnapshot,
)


def _snapshot() -> SurveySnapshot:
    now = datetime.now(UTC)
    return SurveySnapshot(
        survey_id=7,
        guild_id=1,
        channel_id=2,
        message_id=3,
        created_by_discord_user_id=4,
        title="Survey",
        description=None,
        status="Open",
        allow_response_change=True,
        launch_mention_everyone=False,
        reminder_mention_everyone=False,
        close_mention_everyone=False,
        opens_at_utc=None,
        closes_at_utc=now + timedelta(hours=1),
        closed_at_utc=None,
        closed_by_discord_user_id=None,
        closed_reason=None,
        total_responses=0,
        created_at_utc=now,
        updated_at_utc=now,
        questions=(
            SurveyQuestion(
                question_id=10,
                survey_id=7,
                question_key="q1",
                prompt="First?",
                question_type="SingleChoice",
                sort_order=1,
                min_selections=1,
                max_selections=1,
                options=(
                    SurveyQuestionOption(101, 10, "opt1", "A", 1),
                    SurveyQuestionOption(102, 10, "opt2", "B", 2),
                ),
            ),
            SurveyQuestion(
                question_id=11,
                survey_id=7,
                question_key="q2",
                prompt="Second?",
                question_type="MultiSelect",
                sort_order=2,
                min_selections=1,
                max_selections=2,
                options=(
                    SurveyQuestionOption(201, 11, "opt1", "C", 1),
                    SurveyQuestionOption(202, 11, "opt2", "D", 2),
                ),
            ),
        ),
    )


class _Response:
    def __init__(self) -> None:
        self.done = False

    def is_done(self) -> bool:
        return self.done

    async def defer(self, *, ephemeral: bool) -> None:
        self.done = True
        self.ephemeral = ephemeral

    async def edit_message(self, **kwargs) -> None:
        self.done = True
        self.edited = kwargs


def _button(view: SurveyBuilderView, label: str):
    return next(child for child in view.children if getattr(child, "label", None) == label)


def _select(view: SurveyBuilderView, placeholder: str):
    return next(
        child for child in view.children if getattr(child, "placeholder", None) == placeholder
    )


@pytest.mark.asyncio
async def test_survey_post_view_uses_single_persistent_opener():
    view = SurveyPostView(_snapshot())

    assert len(view.children) == 1
    button = view.children[0]
    assert button.label == "Answer survey"
    assert button.custom_id == "survey:7"


@pytest.mark.asyncio
async def test_survey_opener_sends_private_panel_with_existing_answers(monkeypatch):
    snapshot = _snapshot()
    view = SurveyPostView(snapshot)
    button = view.children[0]
    captured: dict[str, object] = {}

    async def fake_get_survey_snapshot(_survey_id):
        return snapshot

    async def fake_get_existing_response_payload(**kwargs):
        assert kwargs == {"survey_id": 7, "discord_user_id": 123}
        return SurveyResponsePayload(
            selected_option_ids={10: (102,), 11: (201, 202)},
            text_answers={},
            detail_text_by_option={},
        )

    async def fake_send_ephemeral(_interaction, content, **kwargs):
        captured["content"] = content
        captured.update(kwargs)

    monkeypatch.setattr(
        "ui.views.survey_post_view.survey_service.get_survey_snapshot",
        fake_get_survey_snapshot,
    )
    monkeypatch.setattr(
        "ui.views.survey_post_view.survey_service.get_existing_response_payload",
        fake_get_existing_response_payload,
    )
    monkeypatch.setattr("ui.views.survey_post_view.send_ephemeral", fake_send_ephemeral)

    interaction = SimpleNamespace(
        response=_Response(),
        user=SimpleNamespace(id=123),
        message=SimpleNamespace(id=456),
    )

    await button.callback(interaction)

    assert "question 1 of 2" in str(captured["content"])
    assert "First?" in str(captured["content"])
    assert "Required single choice" in str(captured["content"])
    assert isinstance(captured["view"], SurveyResponsePanel)
    select = captured["view"].children[0]
    defaults = {option.value for option in select.options if option.default}
    assert defaults == {"102"}


@pytest.mark.asyncio
async def test_survey_submit_defers_before_persisting(monkeypatch):
    snapshot = _snapshot()
    panel = SurveyResponsePanel(
        snapshot,
        owner_user_id=123,
        selected_option_ids={10: (101,), 11: (201,)},
    )
    submit = panel.children[-1]
    captured: dict[str, object] = {}

    async def fake_submit_survey_response(**_kwargs):
        captured["deferred_before_submit"] = interaction.response.done
        return SimpleNamespace(accepted=True, message="Survey response recorded."), snapshot

    async def fake_refresh_public_survey_message(_interaction, _snapshot):
        captured["refresh"] = True

    async def fake_send_ephemeral(_interaction, content, **kwargs):
        captured["content"] = content
        captured.update(kwargs)

    async def fake_edit_original_response(**kwargs):
        captured["edited_original"] = kwargs

    monkeypatch.setattr(
        "ui.views.survey_post_view.survey_service.submit_survey_response",
        fake_submit_survey_response,
    )
    monkeypatch.setattr(
        "ui.views.survey_post_view._refresh_public_survey_message",
        fake_refresh_public_survey_message,
    )
    monkeypatch.setattr("ui.views.survey_post_view.send_ephemeral", fake_send_ephemeral)

    interaction = SimpleNamespace(
        response=_Response(),
        user=SimpleNamespace(id=123),
        message=SimpleNamespace(id=456),
        edit_original_response=fake_edit_original_response,
    )

    await submit.callback(interaction)

    assert captured["deferred_before_submit"] is True
    assert captured["refresh"] is True
    assert captured["edited_original"] == {
        "content": "Survey response recorded.",
        "view": None,
    }


@pytest.mark.asyncio
async def test_survey_submit_requires_all_questions_before_enabled(monkeypatch):
    snapshot = _snapshot()
    panel = SurveyResponsePanel(
        snapshot,
        owner_user_id=123,
        selected_option_ids={10: (101,)},
    )
    submit = panel.children[-1]
    captured: dict[str, object] = {}

    async def fake_submit_survey_response(**_kwargs):
        captured["submit_called"] = True
        return SimpleNamespace(accepted=True, message="Survey response recorded."), snapshot

    async def fake_send_ephemeral(_interaction, content, **kwargs):
        captured["content"] = content
        captured.update(kwargs)

    monkeypatch.setattr(
        "ui.views.survey_post_view.survey_service.submit_survey_response",
        fake_submit_survey_response,
    )
    monkeypatch.setattr("ui.views.survey_post_view.send_ephemeral", fake_send_ephemeral)

    assert submit.disabled is True
    assert SURVEY_INCOMPLETE_HELP in panel.content()

    await submit.callback(SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123)))

    assert captured["content"] == SURVEY_INCOMPLETE_HELP
    assert "submit_called" not in captured

    panel.answers[11] = (201,)
    panel._rebuild()

    assert not panel.children[-1].disabled
    assert SURVEY_INCOMPLETE_HELP not in panel.content()


@pytest.mark.asyncio
async def test_survey_submit_allows_skipped_optional_question():
    now = datetime.now(UTC)
    snapshot = SurveySnapshot(
        survey_id=7,
        guild_id=1,
        channel_id=2,
        message_id=3,
        created_by_discord_user_id=4,
        title="Survey",
        description=None,
        status="Open",
        allow_response_change=True,
        launch_mention_everyone=False,
        reminder_mention_everyone=False,
        close_mention_everyone=False,
        opens_at_utc=None,
        closes_at_utc=now + timedelta(hours=1),
        closed_at_utc=None,
        closed_by_discord_user_id=None,
        closed_reason=None,
        total_responses=0,
        created_at_utc=now,
        updated_at_utc=now,
        questions=(
            SurveyQuestion(
                question_id=10,
                survey_id=7,
                question_key="q1",
                prompt="Required?",
                question_type="SingleChoice",
                sort_order=1,
                min_selections=1,
                max_selections=1,
                options=(
                    SurveyQuestionOption(101, 10, "opt1", "A", 1),
                    SurveyQuestionOption(102, 10, "opt2", "B", 2),
                ),
            ),
            SurveyQuestion(
                question_id=11,
                survey_id=7,
                question_key="q2",
                prompt="Optional note?",
                question_type="Text",
                sort_order=2,
                min_selections=0,
                max_selections=0,
                options=(),
                is_required=False,
            ),
        ),
    )
    panel = SurveyResponsePanel(
        snapshot,
        owner_user_id=123,
        selected_option_ids={10: (101,)},
        current_index=1,
    )

    assert panel.is_complete() is True
    assert not panel.children[-1].disabled
    assert "Optional text response: skipped" in panel.content()
    assert SURVEY_INCOMPLETE_HELP not in panel.content()


@pytest.mark.asyncio
async def test_survey_response_panel_supports_rating_entry_and_prefill():
    now = datetime.now(UTC)
    snapshot = SurveySnapshot(
        survey_id=7,
        guild_id=1,
        channel_id=2,
        message_id=3,
        created_by_discord_user_id=4,
        title="Survey",
        description=None,
        status="Open",
        allow_response_change=True,
        launch_mention_everyone=False,
        reminder_mention_everyone=False,
        close_mention_everyone=False,
        opens_at_utc=None,
        closes_at_utc=now + timedelta(hours=1),
        closed_at_utc=None,
        closed_by_discord_user_id=None,
        closed_reason=None,
        total_responses=0,
        created_at_utc=now,
        updated_at_utc=now,
        questions=(
            SurveyQuestion(
                question_id=10,
                survey_id=7,
                question_key="q1",
                prompt="Rate readiness",
                question_type="Rating",
                sort_order=1,
                min_selections=0,
                max_selections=0,
                options=(),
            ),
        ),
    )
    panel = SurveyResponsePanel(snapshot, owner_user_id=123)

    assert panel.children[-1].disabled is True
    assert "Required rating: choose 1-5 (not yet complete)." in panel.content()

    rating_five = next(child for child in panel.children if getattr(child, "label", None) == "5")
    await rating_five.callback(SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123)))

    assert panel.rating_answers == {10: 5}
    assert not panel.children[-1].disabled
    assert "Required rating: choose 1-5 (rated 5/5)." in panel.content()
    selected_button = next(
        child for child in panel.children if getattr(child, "label", None) == "5"
    )
    assert selected_button.style == discord.ButtonStyle.success


@pytest.mark.asyncio
async def test_survey_response_panel_allows_skipped_optional_rating():
    now = datetime.now(UTC)
    snapshot = SurveySnapshot(
        survey_id=7,
        guild_id=1,
        channel_id=2,
        message_id=3,
        created_by_discord_user_id=4,
        title="Survey",
        description=None,
        status="Open",
        allow_response_change=True,
        launch_mention_everyone=False,
        reminder_mention_everyone=False,
        close_mention_everyone=False,
        opens_at_utc=None,
        closes_at_utc=now + timedelta(hours=1),
        closed_at_utc=None,
        closed_by_discord_user_id=None,
        closed_reason=None,
        total_responses=0,
        created_at_utc=now,
        updated_at_utc=now,
        questions=(
            SurveyQuestion(
                question_id=10,
                survey_id=7,
                question_key="q1",
                prompt="Optional rating",
                question_type="Rating",
                sort_order=1,
                min_selections=0,
                max_selections=0,
                options=(),
                is_required=False,
            ),
        ),
    )
    panel = SurveyResponsePanel(
        snapshot,
        owner_user_id=123,
        rating_answers={10: 4},
    )

    assert not panel.children[-1].disabled
    assert "Optional rating: choose 1-5 (rated 4/5)." in panel.content()

    skip = next(child for child in panel.children if getattr(child, "label", None) == "Skip rating")
    await skip.callback(SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123)))

    assert panel.rating_answers == {}
    assert not panel.children[-1].disabled
    assert "Optional rating: choose 1-5 (skipped)." in panel.content()


@pytest.mark.asyncio
async def test_survey_text_and_detail_modals_update_private_panel_state():
    now = datetime.now(UTC)
    snapshot = SurveySnapshot(
        survey_id=7,
        guild_id=1,
        channel_id=2,
        message_id=3,
        created_by_discord_user_id=4,
        title="Survey",
        description=None,
        status="Open",
        allow_response_change=True,
        launch_mention_everyone=False,
        reminder_mention_everyone=False,
        close_mention_everyone=False,
        opens_at_utc=None,
        closes_at_utc=now + timedelta(hours=1),
        closed_at_utc=None,
        closed_by_discord_user_id=None,
        closed_reason=None,
        total_responses=0,
        created_at_utc=now,
        updated_at_utc=now,
        questions=(
            SurveyQuestion(
                question_id=10,
                survey_id=7,
                question_key="q1",
                prompt="Choice?",
                question_type="SingleChoice",
                sort_order=1,
                min_selections=1,
                max_selections=1,
                options=(
                    SurveyQuestionOption(101, 10, "opt1", "A", 1),
                    SurveyQuestionOption(102, 10, "opt2", "B", 2),
                ),
                allow_details=True,
            ),
            SurveyQuestion(
                question_id=11,
                survey_id=7,
                question_key="q2",
                prompt="Explain?",
                question_type="Text",
                sort_order=2,
                min_selections=0,
                max_selections=0,
                options=(),
            ),
        ),
    )
    panel = SurveyResponsePanel(snapshot, owner_user_id=123, selected_option_ids={10: (101,)})
    assert panel.children[-1].disabled is True
    assert SURVEY_INCOMPLETE_HELP in panel.content()

    detail_select = next(
        child for child in panel.children if isinstance(child, _SurveyDetailOptionSelect)
    )

    assert detail_select.options[0].label == "Add more details about your response"
    assert detail_select.options[0].description == "Optional note for this question"

    detail_modal = _SurveyDetailModal(panel, 101)
    assert detail_modal.detail.label == (
        f"Add more details (max {survey_service.MAX_SURVEY_DETAIL_LEN})"
    )
    assert detail_modal.detail.placeholder == (
        "Optional context for your response. "
        f"Max {survey_service.MAX_SURVEY_DETAIL_LEN} characters."
    )
    detail_modal.detail.value = " Preferred because reset is easier "
    await detail_modal.callback(SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123)))

    panel.current_index = 1
    panel._rebuild()

    assert panel.children[0].label == "Response (required)"
    assert panel.children[-1].disabled is True
    assert "Required text response: not yet complete" in panel.content()
    assert SURVEY_INCOMPLETE_HELP in panel.content()

    text_modal = _SurveyTextAnswerModal(panel)
    assert text_modal.answer.label == (
        f"Response (max {survey_service.MAX_SURVEY_TEXT_ANSWER_LEN} characters)"
    )
    assert text_modal.answer.placeholder == (
        "Required response. " f"Max {survey_service.MAX_SURVEY_TEXT_ANSWER_LEN} characters."
    )
    text_modal.answer.value = " I can lead "
    await text_modal.callback(SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123)))

    assert panel.detail_text_by_option == {(10, 101): "Preferred because reset is easier"}
    assert panel.text_answers == {11: "I can lead"}
    assert "Required text response: complete" in panel.content()
    assert SURVEY_INCOMPLETE_HELP not in panel.content()
    assert not panel.children[-1].disabled


@pytest.mark.asyncio
async def test_survey_multi_select_details_are_question_level():
    now = datetime.now(UTC)
    snapshot = SurveySnapshot(
        survey_id=7,
        guild_id=1,
        channel_id=2,
        message_id=3,
        created_by_discord_user_id=4,
        title="Survey",
        description=None,
        status="Open",
        allow_response_change=True,
        launch_mention_everyone=False,
        reminder_mention_everyone=False,
        close_mention_everyone=False,
        opens_at_utc=None,
        closes_at_utc=now + timedelta(hours=1),
        closed_at_utc=None,
        closed_by_discord_user_id=None,
        closed_reason=None,
        total_responses=0,
        created_at_utc=now,
        updated_at_utc=now,
        questions=(
            SurveyQuestion(
                question_id=10,
                survey_id=7,
                question_key="q1",
                prompt="Choices?",
                question_type="MultiSelect",
                sort_order=1,
                min_selections=1,
                max_selections=2,
                options=(
                    SurveyQuestionOption(101, 10, "opt1", "A", 1),
                    SurveyQuestionOption(102, 10, "opt2", "B", 2),
                    SurveyQuestionOption(103, 10, "opt3", "C", 3),
                ),
                allow_details=True,
            ),
        ),
    )
    panel = SurveyResponsePanel(
        snapshot,
        owner_user_id=123,
        selected_option_ids={10: (101, 103)},
        detail_text_by_option={(10, 101): "first detail", (10, 103): "second detail"},
    )
    detail_select = next(
        child for child in panel.children if isinstance(child, _SurveyDetailOptionSelect)
    )

    assert len(detail_select.options) == 1
    assert detail_select.options[0].label == "Edit details about your response"
    assert detail_select.options[0].description == "Optional note for this question"
    assert detail_select.options[0].value == "101"
    assert panel.detail_text_for_question(snapshot.questions[0]) == "first detail"
    assert panel.normalized_detail_text_by_option() == {(10, 101): "first detail"}
    assert "Details: 1 saved." in panel.content()

    detail_modal = _SurveyDetailModal(panel, 101)
    assert detail_modal.title == "Question details"
    assert detail_modal.detail.value == "first detail"
    detail_modal.detail.value = " Combined context "
    await detail_modal.callback(SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123)))

    assert panel.detail_text_by_option == {(10, 101): "Combined context"}
    assert panel.normalized_detail_text_by_option() == {(10, 101): "Combined context"}

    panel.answers[10] = (103,)
    panel.set_detail_text_for_question(snapshot.questions[0], "Combined context")

    assert panel.detail_text_by_option == {(10, 103): "Combined context"}
    assert panel.normalized_detail_text_by_option() == {(10, 103): "Combined context"}


@pytest.mark.asyncio
async def test_survey_builder_disables_publish_after_success(monkeypatch):
    question_one = SurveyQuestionCreateRequest(
        prompt="First?",
        question_type="SingleChoice",
        options=("A", "B"),
    )
    question_two = SurveyQuestionCreateRequest(
        prompt="Second?",
        question_type="MultiSelect",
        options=("A", "B", "C"),
        min_selections=1,
        max_selections=2,
    )
    captured: dict[str, object] = {"publish_calls": 0}

    async def fake_publish(_interaction, questions):
        captured["publish_calls"] = int(captured["publish_calls"]) + 1
        captured["questions"] = questions
        captured["disabled_during_publish"] = tuple(child.disabled for child in view.children)
        return True

    async def fake_send_ephemeral(_interaction, content, **_kwargs):
        captured["ephemeral"] = content

    monkeypatch.setattr("ui.views.survey_post_view.send_ephemeral", fake_send_ephemeral)

    view = SurveyBuilderView(
        owner_user_id=123,
        publish_callback=fake_publish,
        questions=(question_one, question_two),
    )
    interaction = SimpleNamespace(
        response=_Response(),
        user=SimpleNamespace(id=123),
    )

    await _button(view, "Publish").callback(interaction)

    assert captured["publish_calls"] == 1
    assert captured["questions"] == (question_one, question_two)
    assert all(captured["disabled_during_publish"])
    assert view.published is True
    assert all(child.disabled for child in view.children)

    await _button(view, "Publish").callback(
        SimpleNamespace(
            response=_Response(),
            user=SimpleNamespace(id=123),
        )
    )

    assert captured["publish_calls"] == 1
    assert captured["ephemeral"] == "This survey has already been published."


@pytest.mark.asyncio
async def test_survey_builder_timeout_disables_controls_and_edits_builder_message():
    captured: dict[str, object] = {}

    async def fake_publish(_interaction, _questions):
        captured["published"] = True
        return True

    async def fake_timeout_edit(expired_view):
        captured["content"] = expired_view.expired_content()
        captured["view"] = expired_view

    view = SurveyBuilderView(
        owner_user_id=123,
        publish_callback=fake_publish,
        timeout_edit_callback=fake_timeout_edit,
    )
    view.draft_prompt = "Which night works?"
    view.draft_options = ["Friday", "Saturday"]
    view._sync_selection_bounds()
    view._rebuild()

    await view.on_timeout()

    assert captured.get("published") is not True
    assert captured["view"] is view
    assert view.expired is True
    assert all(child.disabled for child in view.children)
    assert str(captured["content"]).startswith("Survey builder expired. No survey was published.")
    assert "Run `/vote_admin survey_create` again" in str(captured["content"])
    assert "Draft question: Which night works?" in str(captured["content"])


@pytest.mark.asyncio
async def test_survey_guided_builder_saves_multi_select_from_max_selection(monkeypatch):
    captured: dict[str, object] = {}

    async def fake_publish(_interaction, _questions):
        return True

    async def fake_send_ephemeral(_interaction, content, **_kwargs):
        captured["ephemeral"] = content

    monkeypatch.setattr("ui.views.survey_post_view.send_ephemeral", fake_send_ephemeral)

    view = SurveyBuilderView(owner_user_id=123, publish_callback=fake_publish)
    prompt_modal = _SurveyQuestionPromptModal(view)
    assert prompt_modal.prompt.label == "Draft question"
    assert (
        f"Max {survey_service.MAX_SURVEY_QUESTION_PROMPT_LEN} characters"
        in prompt_modal.prompt.placeholder
    )
    prompt_modal.prompt.value = "Which nights work?"
    prompt_interaction = SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123))

    await prompt_modal.callback(prompt_interaction)

    assert (
        "Draft question: Which nights work? (18/180)"
        in prompt_interaction.response.edited["content"]
    )
    assert _button(view, "Draft question").label == "Draft question"

    first_option = _SurveyOptionModal(view)
    assert (
        f"Max {survey_service.MAX_OPTION_LABEL_LEN} characters" in first_option.option.placeholder
    )
    first_option.option.value = "Friday"
    await first_option.callback(SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123)))
    second_option = _SurveyOptionModal(view)
    second_option.option.value = "Saturday"
    await second_option.callback(
        SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123))
    )
    third_option = _SurveyOptionModal(view)
    third_option.option.value = "Sunday"
    await third_option.callback(SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123)))

    view.draft_max_selections = 2
    view._sync_selection_bounds()
    view._rebuild()

    minimum_select = _select(view, "Minimum selections")
    maximum_select = _select(view, "Maximum selections")
    assert [option.label for option in minimum_select.options] == [
        "Minimum: 1",
        "Minimum: 2",
        "Minimum: 3",
    ]
    assert [option.label for option in maximum_select.options] == [
        "Maximum: 1",
        "Maximum: 2",
        "Maximum: 3",
    ]

    await _button(view, "Save question").callback(
        SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123))
    )

    assert len(view.questions) == 1
    assert view.questions[0].question_type == "MultiSelect"
    assert view.questions[0].max_selections == 2
    assert view.questions[0].options == ("Friday", "Saturday", "Sunday")
    assert "Survey question saved." not in captured.get("ephemeral", "")


@pytest.mark.asyncio
async def test_survey_guided_builder_saves_text_question_and_details_toggle(monkeypatch):
    captured: dict[str, object] = {}

    async def fake_publish(_interaction, _questions):
        return True

    async def fake_send_ephemeral(_interaction, content, **_kwargs):
        captured["ephemeral"] = content

    monkeypatch.setattr("ui.views.survey_post_view.send_ephemeral", fake_send_ephemeral)

    view = SurveyBuilderView(owner_user_id=123, publish_callback=fake_publish)
    view.draft_is_text = True
    view._rebuild()
    prompt_modal = _SurveyQuestionPromptModal(view)
    prompt_modal.prompt.value = "What should we know?"
    await prompt_modal.callback(SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123)))

    await _button(view, "Save question").callback(
        SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123))
    )

    assert view.questions[0].question_type == "Text"
    assert view.questions[0].options == ()

    prompt_modal = _SurveyQuestionPromptModal(view)
    prompt_modal.prompt.value = "Which night?"
    await prompt_modal.callback(SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123)))
    first_option = _SurveyOptionModal(view)
    first_option.option.value = "Friday"
    await first_option.callback(SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123)))
    second_option = _SurveyOptionModal(view)
    second_option.option.value = "Saturday"
    await second_option.callback(
        SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123))
    )
    await _button(view, "Details off").callback(
        SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123))
    )
    await _button(view, "Save question").callback(
        SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123))
    )

    assert view.questions[1].question_type == "SingleChoice"
    assert view.questions[1].allow_details is True


@pytest.mark.asyncio
async def test_survey_guided_builder_saves_optional_question(monkeypatch):
    async def fake_publish(_interaction, _questions):
        return True

    async def fake_send_ephemeral(_interaction, _content, **_kwargs):
        return None

    monkeypatch.setattr("ui.views.survey_post_view.send_ephemeral", fake_send_ephemeral)

    view = SurveyBuilderView(owner_user_id=123, publish_callback=fake_publish)
    await _button(view, "Required").callback(
        SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123))
    )

    assert view.draft_is_required is False
    assert _button(view, "Optional").label == "Optional"

    prompt_modal = _SurveyQuestionPromptModal(view)
    prompt_modal.prompt.value = "Optional notes?"
    await prompt_modal.callback(SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123)))
    first_option = _SurveyOptionModal(view)
    first_option.option.value = "A"
    await first_option.callback(SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123)))
    second_option = _SurveyOptionModal(view)
    second_option.option.value = "B"
    await second_option.callback(
        SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123))
    )
    await _button(view, "Save question").callback(
        SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123))
    )

    assert view.questions[0].is_required is False
    assert "optional" in view.summary()


@pytest.mark.asyncio
async def test_survey_guided_builder_saves_rating_question(monkeypatch):
    async def fake_publish(_interaction, _questions):
        return True

    async def fake_send_ephemeral(_interaction, _content, **_kwargs):
        return None

    monkeypatch.setattr("ui.views.survey_post_view.send_ephemeral", fake_send_ephemeral)

    view = SurveyBuilderView(owner_user_id=123, publish_callback=fake_publish)
    view.draft_is_rating = True
    view._rebuild()

    prompt_modal = _SurveyQuestionPromptModal(view)
    prompt_modal.prompt.value = "Rate readiness"
    await prompt_modal.callback(SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123)))
    await _button(view, "Save question").callback(
        SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123))
    )

    assert view.questions[0].question_type == SURVEY_QUESTION_RATING
    assert view.questions[0].options == ()
    assert view.questions[0].min_selections == 0
    assert view.questions[0].max_selections == 0
    assert "Rating 1-5" in view.summary()


@pytest.mark.asyncio
async def test_survey_question_prompt_modal_rejects_after_publish_started(monkeypatch):
    captured: dict[str, object] = {}

    async def fake_publish(_interaction, _questions):
        return True

    async def fake_send_ephemeral(_interaction, content, **_kwargs):
        captured["content"] = content

    monkeypatch.setattr("ui.views.survey_post_view.send_ephemeral", fake_send_ephemeral)

    view = SurveyBuilderView(owner_user_id=123, publish_callback=fake_publish)
    view.publish_in_progress = True
    modal = _SurveyQuestionPromptModal(view)

    await modal.callback(SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123)))

    assert view.questions == []
    assert captured["content"] == "This survey has already been published."


@pytest.mark.asyncio
async def test_survey_question_prompt_modal_enforces_max_questions_server_side(monkeypatch):
    question = SurveyQuestionCreateRequest(
        prompt="First?",
        question_type="SingleChoice",
        options=("A", "B"),
    )
    captured: dict[str, object] = {}

    async def fake_publish(_interaction, _questions):
        return True

    async def fake_send_ephemeral(_interaction, content, **_kwargs):
        captured["content"] = content

    monkeypatch.setattr("ui.views.survey_post_view.send_ephemeral", fake_send_ephemeral)

    view = SurveyBuilderView(
        owner_user_id=123,
        publish_callback=fake_publish,
        questions=(question,) * 5,
    )
    modal = _SurveyQuestionPromptModal(view)

    await modal.callback(SimpleNamespace(response=_Response(), user=SimpleNamespace(id=123)))

    assert len(view.questions) == 5
    assert captured["content"] == "Question not added: surveys support at most 5 questions."
