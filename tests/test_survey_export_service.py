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
    SurveyRankingCount,
    SurveyRatingCount,
    SurveyRatingLabel,
    SurveyReportingOptionRow,
    SurveyReportingQuestionRow,
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
            "IsRequired": 1,
            "QuestionSortOrder": 1,
            "MinSelections": 0,
            "MaxSelections": 0,
            "AnsweredResponses": 2,
            "SkippedResponses": 0,
            "OptionID": "",
            "OptionKey": "",
            "OptionLabel": "",
            "OptionSortOrder": "",
            "SelectionCount": 2,
            "SelectionPercentOfResponses": "100%",
            "IsTopSelection": 0,
            "AverageRating": "",
            "RatingScaleMin": "",
            "RatingScaleMax": "",
            "RatingLowLabel": "",
            "RatingHighLabel": "",
            "RatingLabels": "",
            "RatingDistribution": "",
            "MinimumRating": None,
            "MaximumRating": None,
            "Rating1Count": 0,
            "Rating2Count": 0,
            "Rating3Count": 0,
            "Rating4Count": 0,
            "Rating5Count": 0,
            "Rating6Count": 0,
            "Rating7Count": 0,
            "Rating8Count": 0,
            "Rating9Count": 0,
            "Rating10Count": 0,
            "AverageRank": "",
            "FirstPlaceCount": 0,
            "Rank1Count": 0,
            "Rank2Count": 0,
            "Rank3Count": 0,
            "Rank4Count": 0,
            "Rank5Count": 0,
            "Rank6Count": 0,
        }
    ]


def test_survey_totals_rows_include_optional_answered_and_skipped_counts():
    now = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
    snapshot = SurveySnapshot(
        survey_id=44,
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
        total_responses=3,
        created_at_utc=now,
        updated_at_utc=now,
        questions=(
            SurveyQuestion(
                question_id=20,
                survey_id=44,
                question_key="q1",
                prompt="Optional note?",
                question_type="Text",
                sort_order=1,
                min_selections=0,
                max_selections=0,
                options=(),
                is_required=False,
                answered_response_count=1,
            ),
        ),
    )

    rows = survey_totals_csv_rows(snapshot)

    assert rows[0]["IsRequired"] == 0
    assert rows[0]["AnsweredResponses"] == 1
    assert rows[0]["SkippedResponses"] == 2
    assert rows[0]["SelectionCount"] == 1
    assert rows[0]["SelectionPercentOfResponses"] == "33.3%"


def test_survey_totals_rows_include_rating_aggregates():
    now = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
    snapshot = SurveySnapshot(
        survey_id=45,
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
        total_responses=3,
        created_at_utc=now,
        updated_at_utc=now,
        questions=(
            SurveyQuestion(
                question_id=20,
                survey_id=45,
                question_key="q1",
                prompt="Rate readiness",
                question_type="Rating",
                sort_order=1,
                min_selections=0,
                max_selections=0,
                options=(),
                is_required=False,
                answered_response_count=2,
                rating_counts=(
                    SurveyRatingCount(3, 1),
                    SurveyRatingCount(10, 1),
                ),
                rating_average=6.5,
                rating_min=3,
                rating_max=10,
                rating_min_value=1,
                rating_max_value=10,
                rating_low_label="Poor",
                rating_high_label="Excellent",
                rating_labels=(
                    SurveyRatingLabel(1, "Poor"),
                    SurveyRatingLabel(10, "Excellent"),
                ),
            ),
        ),
    )

    rows = survey_totals_csv_rows(snapshot)

    assert rows[0]["QuestionType"] == "Rating"
    assert rows[0]["AnsweredResponses"] == 2
    assert rows[0]["SkippedResponses"] == 1
    assert rows[0]["AverageRating"] == "6.50"
    assert rows[0]["RatingScaleMin"] == 1
    assert rows[0]["RatingScaleMax"] == 10
    assert rows[0]["RatingLowLabel"] == "Poor"
    assert rows[0]["RatingHighLabel"] == "Excellent"
    assert rows[0]["RatingLabels"] == "1=Poor; 10=Excellent"
    assert rows[0]["RatingDistribution"] == "Poor:0 2:0 3:1 4:0 5:0 6:0 7:0 8:0 9:0 Excellent:1"
    assert rows[0]["MinimumRating"] == 3
    assert rows[0]["MaximumRating"] == 10
    assert rows[0]["Rating3Count"] == 1
    assert rows[0]["Rating10Count"] == 1


def test_survey_totals_rows_omit_rating_labels_for_non_rating_questions():
    now = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
    snapshot = SurveySnapshot(
        survey_id=47,
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
        total_responses=1,
        created_at_utc=now,
        updated_at_utc=now,
        questions=(
            SurveyQuestion(
                question_id=30,
                survey_id=47,
                question_key="q1",
                prompt="Pick one",
                question_type="SingleChoice",
                sort_order=1,
                min_selections=1,
                max_selections=1,
                options=(SurveyQuestionOption(301, 30, "opt1", "Yes", 1, response_count=1),),
                rating_low_label="Should not export",
                rating_high_label="Should not export",
            ),
        ),
    )

    rows = survey_totals_csv_rows(snapshot)

    assert rows[0]["RatingLowLabel"] == ""
    assert rows[0]["RatingHighLabel"] == ""


def test_survey_totals_rows_include_ranking_aggregates():
    now = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
    snapshot = SurveySnapshot(
        survey_id=46,
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
        total_responses=3,
        created_at_utc=now,
        updated_at_utc=now,
        questions=(
            SurveyQuestion(
                question_id=20,
                survey_id=46,
                question_key="q1",
                prompt="Rank priorities",
                question_type="Ranking",
                sort_order=1,
                min_selections=3,
                max_selections=3,
                answered_response_count=2,
                options=(
                    SurveyQuestionOption(
                        101,
                        20,
                        "opt1",
                        "A",
                        1,
                        ranking_average=1.5,
                        ranking_first_place_count=1,
                        ranking_counts=(
                            SurveyRankingCount(1, 1),
                            SurveyRankingCount(2, 1),
                        ),
                    ),
                    SurveyQuestionOption(
                        102,
                        20,
                        "opt2",
                        "B",
                        2,
                        ranking_average=2.5,
                        ranking_first_place_count=0,
                        ranking_counts=(
                            SurveyRankingCount(2, 1),
                            SurveyRankingCount(3, 1),
                        ),
                    ),
                ),
            ),
        ),
    )

    rows = survey_totals_csv_rows(snapshot)

    assert rows[0]["QuestionType"] == "Ranking"
    assert rows[0]["AnsweredResponses"] == 2
    assert rows[0]["SkippedResponses"] == 1
    assert rows[0]["AverageRank"] == "1.50"
    assert rows[0]["FirstPlaceCount"] == 1
    assert rows[0]["Rank1Count"] == 1
    assert rows[0]["Rank2Count"] == 1


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


def test_survey_response_detail_rows_mark_skipped_optional_answers():
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
            question_prompt="Optional note?",
            question_type="Text",
            selected_option_ids=(),
            selected_option_keys=(),
            selected_option_labels=(),
            original_option_ids=(),
            original_option_keys=(),
            original_option_labels=(),
            is_required=False,
        ),
    )

    csv_rows = survey_response_detail_csv_rows(
        rows, discord_names_by_user_id={123456789012345678: "Tester"}
    )

    assert csv_rows[0]["IsRequired"] == 0
    assert csv_rows[0]["AnswerStatus"] == "SkippedOptional"
    assert csv_rows[0]["TextAnswer"] == ""


def test_survey_response_detail_rows_include_rating_values_and_changes():
    now = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
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
            question_prompt="Rate readiness",
            question_type="Rating",
            selected_option_ids=(),
            selected_option_keys=(),
            selected_option_labels=(),
            original_option_ids=(),
            original_option_keys=(),
            original_option_labels=(),
            rating_value=5,
            original_rating_value=3,
        ),
    )

    csv_rows = survey_response_detail_csv_rows(
        rows, discord_names_by_user_id={123456789012345678: "Tester"}
    )

    assert csv_rows[0]["AnswerStatus"] == "Answered"
    assert csv_rows[0]["RatingValue"] == 5
    assert csv_rows[0]["OriginalRatingValue"] == 3
    assert csv_rows[0]["RatingChanged"] == 1
    assert csv_rows[0]["ResponseChanged"] == 1


def test_survey_response_detail_rows_include_ranking_values_and_changes():
    now = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
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
            question_prompt="Rank priorities",
            question_type="Ranking",
            selected_option_ids=(),
            selected_option_keys=(),
            selected_option_labels=(),
            original_option_ids=(),
            original_option_keys=(),
            original_option_labels=(),
            ranking_option_id=101,
            ranking_option_key="opt1",
            ranking_option_label="@A",
            ranking_rank_value=1,
            original_ranking_rank_value=3,
        ),
    )

    csv_rows = survey_response_detail_csv_rows(
        rows, discord_names_by_user_id={123456789012345678: "Tester"}
    )

    assert csv_rows[0]["AnswerStatus"] == "Answered"
    assert csv_rows[0]["RankingOptionID"] == 101
    assert csv_rows[0]["RankingOptionKey"] == "opt1"
    assert csv_rows[0]["RankingOptionLabel"] == "@A"
    assert csv_rows[0]["RankingRankValue"] == 1
    assert csv_rows[0]["OriginalRankingRankValue"] == 3
    assert csv_rows[0]["RankingChanged"] == 1
    assert csv_rows[0]["ResponseChanged"] == 1

    text = (
        build_survey_response_detail_csv_bytes(
            rows,
            discord_names_by_user_id={123456789012345678: "Tester"},
        )
        .getvalue()
        .decode("utf-8-sig")
    )
    assert "'@A" in text


def test_survey_response_detail_rows_mark_cleared_optional_ranking_as_changed():
    now = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
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
            question_prompt="Rank priorities",
            question_type="Ranking",
            selected_option_ids=(),
            selected_option_keys=(),
            selected_option_labels=(),
            original_option_ids=(),
            original_option_keys=(),
            original_option_labels=(),
            is_required=False,
            ranking_option_id=101,
            ranking_option_key="",
            ranking_option_label="",
            ranking_rank_value=None,
            original_ranking_rank_value=1,
        ),
    )

    csv_rows = survey_response_detail_csv_rows(
        rows, discord_names_by_user_id={123456789012345678: "Tester"}
    )

    assert csv_rows[0]["AnswerStatus"] == "SkippedOptional"
    assert csv_rows[0]["RankingOptionID"] == 101
    assert csv_rows[0]["RankingRankValue"] == ""
    assert csv_rows[0]["OriginalRankingRankValue"] == 1
    assert csv_rows[0]["RankingChanged"] == 1
    assert csv_rows[0]["ResponseChanged"] == 1


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


@pytest.mark.asyncio
async def test_survey_report_bundle_export_builds_private_multi_csv_bundle(monkeypatch):
    now = datetime(2026, 7, 5, 12, 0, tzinfo=UTC)
    response_rows = (
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
            text_answer="=private answer",
        ),
    )
    question_rows = (
        SurveyReportingQuestionRow(
            survey_id=42,
            title="Planning",
            status="Closed",
            result_visibility="HiddenUntilClose",
            question_id=10,
            question_key="q1",
            question_prompt="First?",
            question_type="Text",
            question_sort_order=1,
            is_required=True,
            min_selections=0,
            max_selections=0,
            allow_details=False,
            total_responses=1,
            option_count=0,
            answered_responses=1,
            skipped_responses=0,
            choice_selection_count=0,
            ranked_option_count=0,
            ranking_first_place_count=0,
            average_rating=None,
            minimum_rating=None,
            maximum_rating=None,
            rating1_count=0,
            rating2_count=0,
            rating3_count=0,
            rating4_count=0,
            rating5_count=0,
        ),
    )
    option_rows = (
        SurveyReportingOptionRow(
            survey_id=42,
            title="Planning",
            status="Closed",
            result_visibility="HiddenUntilClose",
            question_id=11,
            question_key="q2",
            question_prompt="Rank?",
            question_type="Ranking",
            question_sort_order=2,
            is_required=False,
            option_id=101,
            option_key="opt1",
            option_label="@A",
            option_sort_order=1,
            total_responses=1,
            selection_count=0,
            is_top_selection=False,
            ranked_count=1,
            average_rank=1.0,
            rank1_count=1,
            rank2_count=0,
            rank3_count=0,
            rank4_count=0,
            rank5_count=0,
            rank6_count=0,
        ),
    )
    captured: dict[str, object] = {}

    async def fake_get_survey_snapshot(_survey_id):
        return _snapshot()

    async def fake_question_rows(_survey_id):
        return question_rows

    async def fake_option_rows(_survey_id):
        return option_rows

    async def fake_response_rows(_survey_id):
        return response_rows

    async def fake_insert_audit(**kwargs):
        captured.update(kwargs)

    async def fake_resolver(user_ids):
        captured["user_ids"] = user_ids
        return {123456789012345678: "=Planner"}

    monkeypatch.setattr(
        survey_export_service.survey_dal,
        "get_survey_snapshot",
        fake_get_survey_snapshot,
    )
    monkeypatch.setattr(
        survey_export_service.survey_dal,
        "list_reporting_question_rows",
        fake_question_rows,
    )
    monkeypatch.setattr(
        survey_export_service.survey_dal,
        "list_reporting_option_rows",
        fake_option_rows,
    )
    monkeypatch.setattr(
        survey_export_service.survey_dal,
        "list_answer_audit_rows",
        fake_response_rows,
    )
    monkeypatch.setattr(survey_export_service.survey_dal, "insert_audit", fake_insert_audit)

    export = await survey_export_service.build_survey_report_bundle_export(
        survey_id=42,
        requested_by_discord_user_id=456,
        discord_name_resolver=fake_resolver,
    )

    assert len(export.files) == 4
    assert export.row_count == 4
    assert export.is_oversized() is False
    assert captured["user_ids"] == (123456789012345678,)
    assert captured["action_type"] == "ReportBundleExported"
    assert captured["details"]["mode"] == "report_bundle"
    assert captured["details"]["file_count"] == 4
    assert "raw/detail answers" in captured["details"]["privacy_profile"]

    summary_csv = export.files[0].csv_bytes.getvalue().decode("utf-8-sig")
    response_detail_csv = export.files[3].csv_bytes.getvalue().decode("utf-8-sig")
    assert "QuestionReportRows" in summary_csv
    assert "'123456789012345678" in response_detail_csv
    assert "'=Planner" in response_detail_csv
    assert "'=private answer" in response_detail_csv
