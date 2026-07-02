from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from ui.views.survey_post_view import SurveyBuilderView, SurveyPostView, SurveyResponsePanel
from voting.survey_models import (
    SurveyQuestion,
    SurveyQuestionCreateRequest,
    SurveyQuestionOption,
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

    async def fake_get_existing_answer_option_ids(**kwargs):
        assert kwargs == {"survey_id": 7, "discord_user_id": 123}
        return {10: (102,), 11: (201, 202)}

    async def fake_send_ephemeral(_interaction, content, **kwargs):
        captured["content"] = content
        captured.update(kwargs)

    monkeypatch.setattr(
        "ui.views.survey_post_view.survey_service.get_survey_snapshot",
        fake_get_survey_snapshot,
    )
    monkeypatch.setattr(
        "ui.views.survey_post_view.survey_service.get_existing_answer_option_ids",
        fake_get_existing_answer_option_ids,
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
    )

    await submit.callback(interaction)

    assert captured["deferred_before_submit"] is True
    assert captured["refresh"] is True
    assert captured["content"] == "Survey response recorded."


@pytest.mark.asyncio
async def test_survey_builder_disables_publish_after_success(monkeypatch):
    question = SurveyQuestionCreateRequest(
        prompt="First?",
        question_type="SingleChoice",
        options=("A", "B"),
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
        questions=(question,),
    )
    interaction = SimpleNamespace(
        response=_Response(),
        user=SimpleNamespace(id=123),
    )

    await view.children[1].callback(interaction)

    assert captured["publish_calls"] == 1
    assert captured["questions"] == (question,)
    assert captured["disabled_during_publish"] == (True, True)
    assert view.published is True
    assert tuple(child.disabled for child in view.children) == (True, True)

    await view.children[1].callback(
        SimpleNamespace(
            response=_Response(),
            user=SimpleNamespace(id=123),
        )
    )

    assert captured["publish_calls"] == 1
    assert captured["ephemeral"] == "This survey has already been published."
