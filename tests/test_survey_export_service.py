from __future__ import annotations

from datetime import UTC, datetime

import pytest

from voting import survey_export_service
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


def _text_snapshot() -> SurveySnapshot:
    now = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
    return SurveySnapshot(
        survey_id=43,
        guild_id=1,
        channel_id=2,
        message_id=3,
        created_by_discord_user_id=4,
        title="Planning",
        description=None,
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
                question_id=20,
                survey_id=43,
                question_key="q1",
                prompt="What should leadership know?",
                question_type="Text",
                sort_order=1,
                min_selections=0,
                max_selections=0,
                options=(),
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


def test_survey_totals_rows_include_text_question_metadata_without_raw_answers():
    rows = survey_totals_csv_rows(_text_snapshot())

    assert rows == [
        {
            "SurveyID": 43,
            "Title": "Planning",
            "Description": None,
            "Status": "Closed",
            "TotalResponses": 2,
            "ClosedAtUtc": "2026-07-02T12:00:00Z",
            "ClosedByDiscordUserID": 4,
            "ClosedReason": "done",
            "CreatedAtUtc": "2026-07-02T12:00:00Z",
            "ClosesAtUtc": "2026-07-02T12:00:00Z",
            "ChannelID": 2,
            "MessageID": 3,
            "MessageLink": "https://discord" + ".com/channels/1/2/3",
            "QuestionID": 20,
            "QuestionKey": "q1",
            "QuestionPrompt": "What should leadership know?",
            "QuestionType": "Text",
            "QuestionSortOrder": 1,
            "MinSelections": 0,
            "MaxSelections": 0,
            "OptionID": "",
            "OptionKey": "",
            "OptionLabel": "",
            "OptionSortOrder": "",
            "SelectionCount": 2,
            "SelectionPercentOfResponses": "100%",
            "IsTopSelection": 0,
        }
    ]


@pytest.mark.asyncio
async def test_survey_totals_export_counts_text_question_rows(monkeypatch):
    async def fake_get_survey_snapshot(_survey_id):
        return _text_snapshot()

    async def fake_insert_audit(**_kwargs):
        return None

    monkeypatch.setattr(
        survey_export_service.survey_dal,
        "get_survey_snapshot",
        fake_get_survey_snapshot,
    )
    monkeypatch.setattr(survey_export_service.survey_dal, "insert_audit", fake_insert_audit)

    export = await survey_export_service.build_survey_totals_export(
        survey_id=43,
        requested_by_discord_user_id=456,
    )

    assert export.row_count == 1


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

    csv_rows = survey_response_detail_csv_rows(
        rows, discord_names_by_user_id={123456789012345678: "Tester"}
    )

    assert csv_rows[0]["DiscordUserID"] == "'123456789012345678"
    assert csv_rows[0]["DiscordName"] == "Tester"
    assert csv_rows[0]["SelectedOptionLabels"] == "A"
    assert csv_rows[0]["ResponseChanged"] == 1

    text = (
        build_survey_response_detail_csv_bytes(
            rows,
            discord_names_by_user_id={123456789012345678: "Tester"},
        )
        .getvalue()
        .decode("utf-8-sig")
    )
    assert "ResponseChanged" in text


def test_survey_response_detail_text_and_details_are_formula_safe():
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
            question_type="Text",
            selected_option_ids=(),
            selected_option_keys=(),
            selected_option_labels=(),
            original_option_ids=(),
            original_option_keys=(),
            original_option_labels=(),
            text_answer="=call me",
            original_text_answer="+old",
            selected_option_detail_notes=("10:@detail",),
            original_selected_option_detail_notes=("10:-old detail",),
        ),
    )

    csv_rows = survey_response_detail_csv_rows(
        rows, discord_names_by_user_id={123456789012345678: "Tester"}
    )
    assert csv_rows[0]["TextAnswer"] == "=call me"
    assert csv_rows[0]["TextAnswerChanged"] == 1
    assert csv_rows[0]["DetailNotesChanged"] == 1

    text = (
        build_survey_response_detail_csv_bytes(
            rows,
            discord_names_by_user_id={123456789012345678: "Tester"},
        )
        .getvalue()
        .decode("utf-8-sig")
    )

    assert "'=call me" in text
    assert "'+old" in text
    assert "10:@detail" in text
    assert "10:-old detail" in text


def test_survey_response_detail_change_detection_preserves_duplicate_notes():
    now = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
    rows = (
        SurveyAnswerAuditRow(
            survey_id=42,
            title="Planning",
            closed_at_utc=now,
            response_id=9,
            discord_user_id=123,
            response_created_at_utc=now,
            response_updated_at_utc=now,
            question_id=10,
            question_key="q1",
            question_prompt="First?",
            question_type="MultiSelect",
            selected_option_ids=(101, 102),
            selected_option_keys=("a", "b"),
            selected_option_labels=("A", "B"),
            original_option_ids=(101, 102),
            original_option_keys=(),
            original_option_labels=(),
            selected_option_detail_notes=("101:same",),
            original_selected_option_detail_notes=("101:same", "102:same"),
        ),
    )

    csv_rows = survey_response_detail_csv_rows(rows, discord_names_by_user_id={123: "Tester"})

    assert csv_rows[0]["DetailNotesChanged"] == 1
    assert csv_rows[0]["ResponseChanged"] == 1


@pytest.mark.asyncio
async def test_survey_response_detail_export_deduplicates_name_resolution(monkeypatch):
    now = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
    rows = (
        SurveyAnswerAuditRow(
            survey_id=42,
            title="Planning",
            closed_at_utc=now,
            response_id=9,
            discord_user_id=123,
            response_created_at_utc=now,
            response_updated_at_utc=now,
            question_id=10,
            question_key="q1",
            question_prompt="First?",
            question_type="SingleChoice",
            selected_option_ids=(101,),
            selected_option_keys=("opt1",),
            selected_option_labels=("A",),
            original_option_ids=(101,),
            original_option_keys=(),
            original_option_labels=(),
        ),
        SurveyAnswerAuditRow(
            survey_id=42,
            title="Planning",
            closed_at_utc=now,
            response_id=9,
            discord_user_id=123,
            response_created_at_utc=now,
            response_updated_at_utc=now,
            question_id=11,
            question_key="q2",
            question_prompt="Second?",
            question_type="SingleChoice",
            selected_option_ids=(201,),
            selected_option_keys=("opt1",),
            selected_option_labels=("B",),
            original_option_ids=(201,),
            original_option_keys=(),
            original_option_labels=(),
        ),
    )
    captured: dict[str, object] = {}

    async def fake_get_survey_snapshot(_survey_id):
        return _snapshot()

    async def fake_list_answer_audit_rows(_survey_id):
        return rows

    async def fake_insert_audit(**_kwargs):
        return None

    async def fake_resolver(user_ids):
        captured["user_ids"] = user_ids
        return {123: "Tester"}

    monkeypatch.setattr(
        survey_export_service.survey_dal,
        "get_survey_snapshot",
        fake_get_survey_snapshot,
    )
    monkeypatch.setattr(
        survey_export_service.survey_dal,
        "list_answer_audit_rows",
        fake_list_answer_audit_rows,
    )
    monkeypatch.setattr(survey_export_service.survey_dal, "insert_audit", fake_insert_audit)

    export = await survey_export_service.build_survey_response_detail_export(
        survey_id=42,
        requested_by_discord_user_id=456,
        discord_name_resolver=fake_resolver,
    )

    assert captured["user_ids"] == (123,)
    assert export.row_count == 2
