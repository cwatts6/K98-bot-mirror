from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from voting import survey_service
from voting.service import VoteValidationError
from voting.survey_models import SurveyQuestion, SurveyQuestionOption, SurveySnapshot


def _question(index: int, *, multi: bool = False):
    return survey_service.build_question_request(
        prompt=f"Question {index}?",
        question_type="MultiSelect" if multi else "SingleChoice",
        options=("A", "B", "C"),
        min_selections=1,
        max_selections=2 if multi else 1,
    )


def test_build_survey_create_request_accepts_choice_questions():
    now = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)

    req = survey_service.build_create_request(
        guild_id=1,
        channel_id=2,
        created_by_discord_user_id=3,
        title="Planning survey",
        description="Pick what works",
        questions=(_question(1), _question(2, multi=True)),
        close_time_utc=(now + timedelta(hours=2)).isoformat(),
        reminder_offsets="60,30",
        allow_response_change=True,
        launch_mention_everyone=False,
        reminder_mention_everyone=False,
        close_mention_everyone=False,
        now_utc=now,
    )

    assert req.title == "Planning survey"
    assert len(req.questions) == 2
    assert req.reminder_offsets_minutes == (60, 30)
    assert req.questions[1].question_type == "MultiSelect"


def test_build_survey_create_request_filters_past_due_default_reminder():
    now = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)

    req = survey_service.build_create_request(
        guild_id=1,
        channel_id=2,
        created_by_discord_user_id=3,
        title="Planning survey",
        description=None,
        questions=(_question(1), _question(2)),
        close_time_utc="30m",
        reminder_offsets="60",
        allow_response_change=True,
        launch_mention_everyone=False,
        reminder_mention_everyone=False,
        close_mention_everyone=False,
        now_utc=now,
    )

    assert req.reminder_offsets_minutes == ()


def test_build_survey_create_request_rejects_too_few_questions():
    now = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)

    with pytest.raises(VoteValidationError, match="at least 2 questions"):
        survey_service.build_create_request(
            guild_id=1,
            channel_id=2,
            created_by_discord_user_id=3,
            title="Planning survey",
            description=None,
            questions=(_question(1),),
            close_time_utc=(now + timedelta(hours=2)).isoformat(),
            reminder_offsets="60",
            allow_response_change=True,
            launch_mention_everyone=False,
            reminder_mention_everyone=False,
            close_mention_everyone=False,
            now_utc=now,
        )


def test_build_question_request_rejects_unknown_type_and_bad_cardinality():
    with pytest.raises(VoteValidationError, match="question type"):
        survey_service.build_question_request(
            prompt="Question?",
            question_type="FreeText",
            options=("A", "B"),
        )

    with pytest.raises(VoteValidationError, match="at least two selections"):
        survey_service.build_question_request(
            prompt="Question?",
            question_type="MultiSelect",
            options=("A", "B"),
            min_selections=1,
            max_selections=1,
        )


def test_validate_answers_requires_every_question_and_valid_options():
    now = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
    snapshot = SurveySnapshot(
        survey_id=8,
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
                survey_id=8,
                question_key="q1",
                prompt="Q1",
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
                survey_id=8,
                question_key="q2",
                prompt="Q2",
                question_type="MultiSelect",
                sort_order=2,
                min_selections=1,
                max_selections=2,
                options=(
                    SurveyQuestionOption(201, 11, "opt1", "A", 1),
                    SurveyQuestionOption(202, 11, "opt2", "B", 2),
                ),
            ),
        ),
    )

    assert survey_service.validate_answers(snapshot, {10: (101,), 11: (201, 202)}) == {
        10: (101,),
        11: (201, 202),
    }
    with pytest.raises(VoteValidationError, match="question 2"):
        survey_service.validate_answers(snapshot, {10: (101,)})
    with pytest.raises(VoteValidationError, match="not valid"):
        survey_service.validate_answers(snapshot, {10: (999,), 11: (201,)})
