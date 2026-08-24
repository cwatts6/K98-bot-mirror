from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from ui.views.survey_admin_update_view import (
    SurveyAdminUpdateView,
    _SurveyOptionIconModal,
    _SurveyResultVisibilitySelect,
)
from voting.option_emojis import normalize_option_emoji
from voting.service import VoteValidationError
from voting.survey_models import SurveyQuestion, SurveyQuestionOption, SurveySnapshot


def _snapshot(*, total_responses: int = 0, status: str = "Open") -> SurveySnapshot:
    now = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
    return SurveySnapshot(
        survey_id=7,
        guild_id=1,
        channel_id=2,
        message_id=3,
        created_by_discord_user_id=4,
        title="Survey",
        description=None,
        status=status,
        allow_response_change=True,
        launch_mention_everyone=False,
        reminder_mention_everyone=False,
        close_mention_everyone=False,
        opens_at_utc=None,
        closes_at_utc=now + timedelta(hours=1),
        closed_at_utc=None,
        closed_by_discord_user_id=None,
        closed_reason=None,
        total_responses=total_responses,
        created_at_utc=now,
        updated_at_utc=now,
        questions=(
            SurveyQuestion(
                question_id=10,
                survey_id=7,
                question_key="q1",
                prompt="Pick one",
                question_type="SingleChoice",
                sort_order=1,
                min_selections=1,
                max_selections=1,
                options=(
                    SurveyQuestionOption(101, 10, "opt1", "A", 1),
                    SurveyQuestionOption(102, 10, "opt2", "B", 2),
                ),
            ),
        ),
    )


@pytest.mark.asyncio
async def test_survey_update_view_guard_rejects_other_admin(monkeypatch):
    sent: list[str] = []

    async def fake_send_ephemeral(_interaction, content, **_kwargs):
        sent.append(content)

    monkeypatch.setattr("ui.views.survey_admin_update_view.send_ephemeral", fake_send_ephemeral)
    view = SurveyAdminUpdateView(_snapshot(), owner_user_id=123)

    assert await view.guard(SimpleNamespace(user=SimpleNamespace(id=456))) is False
    assert sent == ["This survey update panel belongs to another admin."]


@pytest.mark.asyncio
async def test_survey_option_icon_modal_updates_and_refreshes(monkeypatch):
    captured: dict[str, object] = {}
    snapshot = _snapshot()
    updated = SurveySnapshot(
        **{
            **snapshot.__dict__,
            "questions": (
                SurveyQuestion(
                    **{
                        **snapshot.questions[0].__dict__,
                        "options": (
                            SurveyQuestionOption(
                                101,
                                10,
                                "opt1",
                                "A",
                                1,
                                emoji=normalize_option_emoji("\u2705"),
                            ),
                            snapshot.questions[0].options[1],
                        ),
                    }
                ),
            ),
        }
    )

    async def fake_update_survey_option_emoji(**kwargs):
        captured["update"] = kwargs
        return updated

    async def fake_refresh(_client, refreshed_snapshot):
        captured["refreshed"] = refreshed_snapshot

    async def fake_send_ephemeral(_interaction, content, **_kwargs):
        captured["ephemeral"] = content

    monkeypatch.setattr(
        "ui.views.survey_admin_update_view.update_survey_option_emoji",
        fake_update_survey_option_emoji,
    )
    monkeypatch.setattr("ui.views.survey_admin_update_view.send_ephemeral", fake_send_ephemeral)

    view = SurveyAdminUpdateView(snapshot, owner_user_id=123, refresh_callback=fake_refresh)
    modal = _SurveyOptionIconModal(view, option_id=101)
    modal.icon.value = "\u2705"

    await modal.callback(SimpleNamespace(user=SimpleNamespace(id=123), client=object()))

    assert captured["update"] == {
        "survey_id": 7,
        "option_id": 101,
        "emoji_value": "\u2705",
        "actor_discord_user_id": 123,
    }
    assert captured["refreshed"] is updated
    assert captured["ephemeral"] == "Option icon saved for \u2705 A."


@pytest.mark.asyncio
async def test_survey_option_icon_modal_handles_stale_missing_option(monkeypatch):
    sent: list[str] = []

    async def fake_update_survey_option_emoji(**_kwargs):
        raise VoteValidationError("Survey option was not found.")

    async def fake_send_ephemeral(_interaction, content, **_kwargs):
        sent.append(content)

    monkeypatch.setattr(
        "ui.views.survey_admin_update_view.update_survey_option_emoji",
        fake_update_survey_option_emoji,
    )
    monkeypatch.setattr("ui.views.survey_admin_update_view.send_ephemeral", fake_send_ephemeral)

    view = SurveyAdminUpdateView(_snapshot(), owner_user_id=123)
    modal = _SurveyOptionIconModal(view, option_id=999)
    modal.icon.value = ""

    await modal.callback(SimpleNamespace(user=SimpleNamespace(id=123), client=object()))

    assert sent == ["Option icon not saved: Survey option was not found."]


@pytest.mark.asyncio
async def test_result_visibility_select_blocks_when_responses_exist(monkeypatch):
    sent: list[str] = []

    async def fake_send_ephemeral(_interaction, content, **_kwargs):
        sent.append(content)

    monkeypatch.setattr("ui.views.survey_admin_update_view.send_ephemeral", fake_send_ephemeral)
    view = SurveyAdminUpdateView(_snapshot(total_responses=1), owner_user_id=123)
    select = _SurveyResultVisibilitySelect(view)
    select._selected_values = ["HiddenUntilClose"]
    select._interaction = SimpleNamespace(data={})

    await select.callback(SimpleNamespace(user=SimpleNamespace(id=123)))

    assert sent == ["Result visibility cannot be edited after responses exist."]
