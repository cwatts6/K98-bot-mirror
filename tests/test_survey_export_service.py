from __future__ import annotations

from datetime import UTC, datetime

from voting.survey_export_service import (
    build_survey_response_detail_csv_bytes,
    build_survey_totals_csv_bytes,
    survey_response_detail_csv_rows,
    survey_totals_csv_rows,
)
from voting.survey_models import (
    SurveyAnswerAuditRow,
    SurveyQuestion,
    SurveyQuestionOption,
    SurveySnapshot,
)


def _snapshot() -> SurveySnapshot:
    now = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
    return SurveySnapshot(
        survey_id=42,
        guild_id=1,
        channel_id=2,
        message_id=3,
        created_by_discord_user_id=4,
        title="=Planning",
        description="+Pick choices",
        status="Closed",
        allow_response_change=True,
        launch_mention_everyone=False,
        reminder_mention_everyone=False,
        close_mention_everyone=False,
        opens_at_utc=None,
        closes_at_utc=now,
        closed_at_utc=now,
        closed_by_discord_user_id=4,
        closed_reason="done",
        total_responses=2,
        created_at_utc=now,
        updated_at_utc=now,
        questions=(
            SurveyQuestion(
                question_id=10,
                survey_id=42,
                question_key="q1",
                prompt="First?",
                question_type="SingleChoice",
                sort_order=1,
                min_selections=1,
                max_selections=1,
                options=(
                    SurveyQuestionOption(101, 10, "opt1", "A", 1, response_count=2),
                    SurveyQuestionOption(102, 10, "opt2", "B", 2, response_count=0),
                ),
            ),
        ),
    )


def test_survey_totals_rows_include_question_and_option_totals():
    rows = survey_totals_csv_rows(_snapshot())

    assert rows[0]["SurveyID"] == 42
    assert rows[0]["QuestionKey"] == "q1"
    assert rows[0]["OptionLabel"] == "A"
    assert rows[0]["SelectionCount"] == 2
    assert rows[0]["SelectionPercentOfResponses"] == "100%"
    assert rows[0]["IsTopSelection"] == 1


def test_survey_csv_bytes_are_formula_safe():
    text = build_survey_totals_csv_bytes(_snapshot()).getvalue().decode("utf-8-sig")

    assert "'=Planning" in text
    assert "'+Pick choices" in text


def test_survey_response_detail_rows_include_spreadsheet_safe_discord_id():
    now = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
    rows = (
        SurveyAnswerAuditRow(
            survey_id=42,
            title="Planning",
            closed_at_utc=now,
            response_id=9,
            discord_user_id=123456789012345678,
            response_created_at_utc=now,
            response_updated_at_utc=now,
            question_id=10,
            question_key="q1",
            question_prompt="First?",
            question_type="SingleChoice",
            selected_option_ids=(101,),
            selected_option_keys=("opt1",),
            selected_option_labels=("A",),
            original_option_ids=(102,),
            original_option_keys=(),
            original_option_labels=(),
        ),
    )

    csv_rows = survey_response_detail_csv_rows(rows, discord_names_by_user_id={123456789012345678: "Tester"})

    assert csv_rows[0]["DiscordUserID"] == "'123456789012345678"
    assert csv_rows[0]["DiscordName"] == "Tester"
    assert csv_rows[0]["SelectedOptionLabels"] == "A"
    assert csv_rows[0]["ResponseChanged"] == 1

    text = build_survey_response_detail_csv_bytes(
        rows,
        discord_names_by_user_id={123456789012345678: "Tester"},
    ).getvalue().decode("utf-8-sig")
    assert "ResponseChanged" in text
