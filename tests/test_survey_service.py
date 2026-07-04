from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from voting import survey_service
from voting.service import VoteValidationError
from voting.survey_models import (
    SURVEY_QUESTION_TEXT,
    SurveyQuestion,
    SurveyQuestionOption,
    SurveySnapshot,
)


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


def test_build_question_request_derives_type_from_max_selections():
    single = survey_service.build_question_request(
        prompt="Question?",
        question_type=None,
        options=("A", "B"),
        min_selections=1,
        max_selections=1,
    )
    multi = survey_service.build_question_request(
        prompt="Question?",
        question_type=None,
        options=("A", "B", "C"),
        min_selections=1,
        max_selections=2,
    )

    assert single.question_type == "SingleChoice"
    assert multi.question_type == "MultiSelect"


def test_build_question_request_accepts_text_and_choice_details():
    text = survey_service.build_question_request(
        prompt="What should leadership know?",
        question_type="Text",
        options=(),
        min_selections=0,
        max_selections=0,
    )
    choice = survey_service.build_question_request(
        prompt="Which night?",
        question_type="SingleChoice",
        options=("Friday", "Saturday"),
        allow_details=True,
    )

    assert text.question_type == SURVEY_QUESTION_TEXT
    assert text.options == ()
    assert text.min_selections == 0
    assert text.max_selections == 0
    assert choice.allow_details is True

    with pytest.raises(VoteValidationError, match="do not use options"):
        survey_service.build_question_request(
            prompt="Why?",
            question_type="Text",
            options=("A",),
            min_selections=0,
            max_selections=0,
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
    with pytest.raises(VoteValidationError, match="not valid"):
        survey_service.validate_answers(snapshot, {10: (101,), 11: (201,), 999: (1,)})


def test_validate_response_payload_rejects_malformed_option_ids():
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
                options=(SurveyQuestionOption(101, 10, "opt1", "A", 1),),
            ),
            SurveyQuestion(
                question_id=11,
                survey_id=8,
                question_key="q2",
                prompt="Q2",
                question_type="SingleChoice",
                sort_order=2,
                min_selections=1,
                max_selections=1,
                options=(SurveyQuestionOption(201, 11, "opt1", "A", 1),),
            ),
        ),
    )

    with pytest.raises(VoteValidationError, match=r"question 1.*not valid"):
        survey_service.validate_response_payload(
            snapshot,
            answers_by_question_id={10: ("not-an-option",), 11: (201,)},
        )

    with pytest.raises(VoteValidationError, match=r"question 1.*not valid"):
        survey_service.validate_response_payload(
            snapshot,
            answers_by_question_id={10: (None,), 11: (201,)},
        )


def test_validate_response_payload_accepts_required_text_and_selected_details():
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
                allow_details=True,
            ),
            SurveyQuestion(
                question_id=11,
                survey_id=8,
                question_key="q2",
                prompt="Q2",
                question_type="Text",
                sort_order=2,
                min_selections=0,
                max_selections=0,
                options=(),
            ),
        ),
    )

    payload = survey_service.validate_response_payload(
        snapshot,
        answers_by_question_id={10: (101,)},
        text_answers_by_question_id={11: "  can lead rallies  "},
        detail_text_by_question_option={(10, 101): " preferred "},
    )

    assert payload.selected_option_ids == {10: (101,)}
    assert payload.text_answers == {11: "can lead rallies"}
    assert payload.detail_text_by_option == {(10, 101): "preferred"}

    with pytest.raises(VoteValidationError, match="question 2"):
        survey_service.validate_response_payload(
            snapshot,
            answers_by_question_id={10: (101,)},
            text_answers_by_question_id={11: " "},
        )

    with pytest.raises(VoteValidationError, match="text answers"):
        survey_service.validate_response_payload(
            snapshot,
            answers_by_question_id={10: (101,)},
            text_answers_by_question_id={"not-a-question": "ok"},
        )

    with pytest.raises(VoteValidationError, match="selected options"):
        survey_service.validate_response_payload(
            snapshot,
            answers_by_question_id={10: (101,)},
            text_answers_by_question_id={11: "ok"},
            detail_text_by_question_option={(10, 102): "not selected"},
        )


def test_validate_response_payload_allows_skipped_optional_choice_and_text():
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
                prompt="Optional choice",
                question_type="SingleChoice",
                sort_order=1,
                min_selections=1,
                max_selections=1,
                options=(
                    SurveyQuestionOption(101, 10, "opt1", "A", 1),
                    SurveyQuestionOption(102, 10, "opt2", "B", 2),
                ),
                allow_details=True,
                is_required=False,
            ),
            SurveyQuestion(
                question_id=11,
                survey_id=8,
                question_key="q2",
                prompt="Optional text",
                question_type="Text",
                sort_order=2,
                min_selections=0,
                max_selections=0,
                options=(),
                is_required=False,
            ),
        ),
    )

    skipped = survey_service.validate_response_payload(
        snapshot,
        answers_by_question_id={},
        text_answers_by_question_id={11: " "},
    )

    assert skipped.selected_option_ids == {}
    assert skipped.text_answers == {}
    assert skipped.detail_text_by_option == {}

    answered = survey_service.validate_response_payload(
        snapshot,
        answers_by_question_id={10: (101,)},
        text_answers_by_question_id={11: " maybe "},
        detail_text_by_question_option={(10, 101): " if needed "},
    )

    assert answered.selected_option_ids == {10: (101,)}
    assert answered.text_answers == {11: "maybe"}
    assert answered.detail_text_by_option == {(10, 101): "if needed"}

    with pytest.raises(VoteValidationError, match="selected options"):
        survey_service.validate_response_payload(
            snapshot,
            answers_by_question_id={},
            detail_text_by_question_option={(10, 101): "detail without selection"},
        )
