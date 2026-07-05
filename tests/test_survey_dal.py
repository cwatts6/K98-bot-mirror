from __future__ import annotations

from datetime import UTC, datetime
import json

import pytest

from voting import survey_dal
from voting.service import VoteValidationError
from voting.survey_models import SurveyCreateRequest, SurveyQuestionCreateRequest


@pytest.mark.asyncio
async def test_get_survey_snapshot_skips_rating_queries_when_rating_table_missing(monkeypatch):
    now = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
    executed_queries: list[str] = []

    async def fake_run_one_async(sql, params=None):
        if "OBJECT_ID" in sql:
            return {"ObjectId": None}
        return {
            "SurveyID": 42,
            "GuildID": 1,
            "ChannelID": 2,
            "MessageID": 3,
            "CreatedByDiscordUserID": 4,
            "Title": "Planning",
            "Description": None,
            "Status": "Open",
            "AllowResponseChange": 1,
            "LaunchMentionEveryone": 0,
            "ReminderMentionEveryone": 0,
            "CloseMentionEveryone": 0,
            "OpensAtUtc": None,
            "ClosesAtUtc": now,
            "ClosedAtUtc": None,
            "ClosedByDiscordUserID": None,
            "ClosedReason": None,
            "TotalResponses": 0,
            "CreatedAtUtc": now,
            "UpdatedAtUtc": now,
            "ResultVisibility": "PublicLive",
        }

    async def fake_run_query_async(sql, params=None):
        executed_queries.append(sql)
        assert "SurveyRatingAnswers" not in sql
        if "FROM dbo.SurveyQuestions q" in sql:
            return [
                {
                    "SurveyQuestionID": 10,
                    "SurveyID": 42,
                    "QuestionKey": "q1",
                    "Prompt": "Pick one",
                    "QuestionType": "SingleChoice",
                    "SortOrder": 1,
                    "IsRequired": 1,
                    "MinSelections": 1,
                    "MaxSelections": 1,
                    "AllowDetails": 0,
                    "AnsweredResponseCount": 0,
                    "AverageRating": None,
                    "MinimumRating": None,
                    "MaximumRating": None,
                }
            ]
        return []

    monkeypatch.setattr(survey_dal, "run_one_async", fake_run_one_async)
    monkeypatch.setattr(survey_dal, "run_query_async", fake_run_query_async)

    snapshot = await survey_dal.get_survey_snapshot(42)

    assert snapshot is not None
    assert snapshot.questions[0].rating_counts == ()
    assert executed_queries


@pytest.mark.asyncio
async def test_submit_survey_response_missing_rating_table_has_clear_error(monkeypatch):
    now = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)

    class FakeCursor:
        last_sql = ""

        def execute(self, sql, params=()):
            self.last_sql = sql

        def fetchone(self):
            return None

    def fake_fetch_one_dict(cur):
        if "OBJECT_ID" in cur.last_sql:
            return {"ObjectId": None}
        return {
            "SurveyID": 42,
            "Status": "Open",
            "AllowResponseChange": 1,
            "ClosesAtUtc": datetime(2026, 7, 4, 13, 0, tzinfo=UTC),
        }

    async def fake_run_blocking_in_thread(func, callback, *, name=None):
        return func(callback)

    monkeypatch.setattr(survey_dal, "fetch_one_dict", fake_fetch_one_dict)

    def fake_exec_with_cursor(callback):
        try:
            return callback(FakeCursor())
        except Exception:
            return None

    monkeypatch.setattr(survey_dal, "exec_with_cursor", fake_exec_with_cursor)
    monkeypatch.setattr(survey_dal, "run_blocking_in_thread", fake_run_blocking_in_thread)

    with pytest.raises(VoteValidationError, match=survey_dal.SURVEY_RATING_MIGRATION_ID):
        await survey_dal.submit_survey_response(
            survey_id=42,
            discord_user_id=123,
            answers_by_question_id={},
            rating_answers_by_question_id={10: 5},
            now_utc=now,
        )


@pytest.mark.asyncio
async def test_submit_survey_response_missing_ranking_table_has_clear_error(monkeypatch):
    now = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)

    class FakeCursor:
        last_sql = ""

        def execute(self, sql, params=()):
            self.last_sql = sql

        def fetchone(self):
            return None

    def fake_fetch_one_dict(cur):
        if "OBJECT_ID" in cur.last_sql:
            return {"ObjectId": None}
        return {
            "SurveyID": 42,
            "Status": "Open",
            "AllowResponseChange": 1,
            "ClosesAtUtc": datetime(2026, 7, 4, 13, 0, tzinfo=UTC),
        }

    async def fake_run_blocking_in_thread(func, callback, *, name=None):
        return func(callback)

    monkeypatch.setattr(survey_dal, "fetch_one_dict", fake_fetch_one_dict)

    def fake_exec_with_cursor(callback):
        try:
            return callback(FakeCursor())
        except Exception:
            return None

    monkeypatch.setattr(survey_dal, "exec_with_cursor", fake_exec_with_cursor)
    monkeypatch.setattr(survey_dal, "run_blocking_in_thread", fake_run_blocking_in_thread)

    with pytest.raises(VoteValidationError, match=survey_dal.SURVEY_RANKING_MIGRATION_ID):
        await survey_dal.submit_survey_response(
            survey_id=42,
            discord_user_id=123,
            answers_by_question_id={},
            ranking_answers_by_question_id={10: (101, 102)},
            now_utc=now,
        )


@pytest.mark.asyncio
async def test_create_survey_missing_ranking_table_has_clear_error(monkeypatch):
    now = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)

    class FakeCursor:
        last_sql = ""

        def execute(self, sql, params=()):
            self.last_sql = sql

    def fake_fetch_one_dict(cur):
        assert "OBJECT_ID" in cur.last_sql
        return {"ObjectId": None}

    async def fake_run_blocking_in_thread(func, callback, *, name=None):
        return func(callback)

    monkeypatch.setattr(survey_dal, "fetch_one_dict", fake_fetch_one_dict)

    def fake_exec_with_cursor(callback):
        try:
            return callback(FakeCursor())
        except Exception:
            return None

    monkeypatch.setattr(survey_dal, "exec_with_cursor", fake_exec_with_cursor)
    monkeypatch.setattr(survey_dal, "run_blocking_in_thread", fake_run_blocking_in_thread)

    req = SurveyCreateRequest(
        guild_id=1,
        channel_id=2,
        created_by_discord_user_id=3,
        title="Planning",
        description=None,
        questions=(
            SurveyQuestionCreateRequest(
                prompt="Rank priorities",
                question_type="Ranking",
                options=("A", "B"),
                min_selections=2,
                max_selections=2,
            ),
            SurveyQuestionCreateRequest(
                prompt="Pick one",
                question_type="SingleChoice",
                options=("Yes", "No"),
            ),
        ),
        closes_at_utc=now,
        reminder_offsets_minutes=(),
    )

    with pytest.raises(VoteValidationError, match=survey_dal.SURVEY_RANKING_MIGRATION_ID):
        await survey_dal.create_survey(req)


def test_answer_audit_rows_include_text_and_option_aligned_detail_payloads():
    now = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
    rows = [
        {
            "SurveyID": 42,
            "Title": "Planning",
            "ClosedAtUtc": now,
            "ResponseID": 9,
            "DiscordUserID": 123,
            "OriginalAnswersJson": json.dumps(
                {
                    "choices": {"10": [101, 102]},
                    "text": {"11": "old text"},
                    "details": {"10": {"101": "old detail"}},
                }
            ),
            "ResponseCreatedAtUtc": now,
            "ResponseUpdatedAtUtc": now,
            "SurveyQuestionID": 10,
            "QuestionKey": "q1",
            "Prompt": "Choice?",
            "QuestionType": "SingleChoice",
            "IsRequired": 0,
            "SurveyOptionID": 101,
            "OptionKey": "opt1",
            "Label": "A",
            "AnswerText": None,
            "DetailText": "new detail",
        },
        {
            "SurveyID": 42,
            "Title": "Planning",
            "ClosedAtUtc": now,
            "ResponseID": 9,
            "DiscordUserID": 123,
            "OriginalAnswersJson": json.dumps(
                {
                    "choices": {"10": [101, 102]},
                    "text": {"11": "old text"},
                    "details": {"10": {"101": "old detail"}},
                }
            ),
            "ResponseCreatedAtUtc": now,
            "ResponseUpdatedAtUtc": now,
            "SurveyQuestionID": 10,
            "QuestionKey": "q1",
            "Prompt": "Choice?",
            "QuestionType": "MultiSelect",
            "IsRequired": 0,
            "SurveyOptionID": 102,
            "OptionKey": "opt2",
            "Label": "B",
            "AnswerText": None,
            "DetailText": None,
        },
        {
            "SurveyID": 42,
            "Title": "Planning",
            "ClosedAtUtc": now,
            "ResponseID": 9,
            "DiscordUserID": 123,
            "OriginalAnswersJson": json.dumps(
                {
                    "choices": {"10": [101]},
                    "text": {"11": "old text"},
                    "details": {"10": {"101": "old detail"}},
                }
            ),
            "ResponseCreatedAtUtc": now,
            "ResponseUpdatedAtUtc": now,
            "SurveyQuestionID": 11,
            "QuestionKey": "q2",
            "Prompt": "Explain?",
            "QuestionType": "Text",
            "IsRequired": 1,
            "SurveyOptionID": None,
            "OptionKey": None,
            "Label": None,
            "AnswerText": "new text",
            "DetailText": None,
        },
    ]

    audit_rows = survey_dal._answer_audit_from_rows(rows)

    assert audit_rows[0].selected_option_ids == (101, 102)
    assert audit_rows[0].is_required is False
    assert audit_rows[0].selected_option_detail_notes == ("101:new detail", "102:")
    assert audit_rows[0].original_selected_option_detail_notes == ("101:old detail", "102:")
    assert audit_rows[1].text_answer == "new text"
    assert audit_rows[1].is_required is True
    assert audit_rows[1].original_text_answer == "old text"


@pytest.mark.asyncio
async def test_reporting_question_rows_require_reporting_views(monkeypatch):
    async def fake_run_one_async(_sql, _params=None):
        return {"QuestionViewObjectId": None, "OptionViewObjectId": None}

    monkeypatch.setattr(survey_dal, "run_one_async", fake_run_one_async)

    with pytest.raises(VoteValidationError, match=survey_dal.SURVEY_REPORTING_MIGRATION_ID):
        await survey_dal.list_reporting_question_rows(42)


@pytest.mark.asyncio
async def test_reporting_rows_read_sql_reporting_views(monkeypatch):
    captured: list[str] = []

    async def fake_run_one_async(_sql, _params=None):
        return {"QuestionViewObjectId": 1, "OptionViewObjectId": 2}

    async def fake_run_query_async(sql, params=None):
        captured.append(sql)
        assert params == (42,)
        if "v_SurveyReportingQuestionSummary" in sql:
            return [
                {
                    "SurveyID": 42,
                    "Title": "Planning",
                    "Status": "Closed",
                    "ResultVisibility": "HiddenUntilClose",
                    "SurveyQuestionID": 10,
                    "QuestionKey": "q1",
                    "Prompt": "Rate?",
                    "QuestionType": "Rating",
                    "QuestionSortOrder": 1,
                    "IsRequired": 0,
                    "MinSelections": 0,
                    "MaxSelections": 0,
                    "AllowDetails": 0,
                    "TotalResponses": 3,
                    "OptionCount": 0,
                    "AnsweredResponses": 2,
                    "SkippedResponses": 1,
                    "ChoiceSelectionCount": 0,
                    "RankedOptionCount": 0,
                    "RankingFirstPlaceCount": 0,
                    "AverageRating": 4.5,
                    "MinimumRating": 4,
                    "MaximumRating": 5,
                    "Rating1Count": 0,
                    "Rating2Count": 0,
                    "Rating3Count": 0,
                    "Rating4Count": 1,
                    "Rating5Count": 1,
                }
            ]
        return [
            {
                "SurveyID": 42,
                "Title": "Planning",
                "Status": "Closed",
                "ResultVisibility": "HiddenUntilClose",
                "SurveyQuestionID": 11,
                "QuestionKey": "q2",
                "Prompt": "Rank?",
                "QuestionType": "Ranking",
                "QuestionSortOrder": 2,
                "IsRequired": 1,
                "SurveyOptionID": 101,
                "OptionKey": "opt1",
                "OptionLabel": "A",
                "OptionSortOrder": 1,
                "TotalResponses": 3,
                "SelectionCount": 0,
                "IsTopSelection": 0,
                "RankedCount": 2,
                "AverageRank": 1.5,
                "Rank1Count": 1,
                "Rank2Count": 1,
                "Rank3Count": 0,
                "Rank4Count": 0,
                "Rank5Count": 0,
                "Rank6Count": 0,
            }
        ]

    monkeypatch.setattr(survey_dal, "run_one_async", fake_run_one_async)
    monkeypatch.setattr(survey_dal, "run_query_async", fake_run_query_async)

    question_rows = await survey_dal.list_reporting_question_rows(42)
    option_rows = await survey_dal.list_reporting_option_rows(42)

    assert question_rows[0].question_type == "Rating"
    assert question_rows[0].is_required is False
    assert question_rows[0].average_rating == 4.5
    assert option_rows[0].question_type == "Ranking"
    assert option_rows[0].average_rank == 1.5
    assert option_rows[0].rank1_count == 1
    assert any("dbo.v_SurveyReportingQuestionSummary" in sql for sql in captured)
    assert any("dbo.v_SurveyReportingOptionSummary" in sql for sql in captured)


def test_answer_audit_rows_include_rating_values_and_original_metadata():
    now = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
    rows = [
        {
            "SurveyID": 42,
            "Title": "Planning",
            "ClosedAtUtc": now,
            "ResponseID": 9,
            "DiscordUserID": 123,
            "OriginalAnswersJson": json.dumps({"ratings": {"10": 2}}),
            "ResponseCreatedAtUtc": now,
            "ResponseUpdatedAtUtc": now,
            "SurveyQuestionID": 10,
            "QuestionKey": "q1",
            "Prompt": "Rate readiness",
            "QuestionType": "Rating",
            "IsRequired": 1,
            "SurveyOptionID": None,
            "OptionKey": None,
            "Label": None,
            "AnswerText": None,
            "DetailText": None,
            "RatingValue": 5,
        }
    ]

    audit_rows = survey_dal._answer_audit_from_rows(rows)

    assert audit_rows[0].question_type == "Rating"
    assert audit_rows[0].rating_value == 5
    assert audit_rows[0].original_rating_value == 2
    assert audit_rows[0].selected_option_ids == ()


def test_answer_audit_rows_expand_ranking_values_and_original_metadata():
    now = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
    base = {
        "SurveyID": 42,
        "Title": "Planning",
        "ClosedAtUtc": now,
        "ResponseID": 9,
        "DiscordUserID": 123,
        "OriginalAnswersJson": json.dumps({"rankings": {"10": [102, 101]}}),
        "ResponseCreatedAtUtc": now,
        "ResponseUpdatedAtUtc": now,
        "SurveyQuestionID": 10,
        "QuestionKey": "q1",
        "Prompt": "Rank priorities",
        "QuestionType": "Ranking",
        "IsRequired": 1,
        "SurveyOptionID": None,
        "OptionKey": None,
        "Label": None,
        "AnswerText": None,
        "DetailText": None,
        "RatingValue": None,
    }
    rows = [
        {
            **base,
            "RankingOptionID": 101,
            "RankingOptionKey": "opt1",
            "RankingOptionLabel": "A",
            "RankingRankValue": 1,
        },
        {
            **base,
            "RankingOptionID": 102,
            "RankingOptionKey": "opt2",
            "RankingOptionLabel": "B",
            "RankingRankValue": 2,
        },
    ]

    audit_rows = survey_dal._answer_audit_from_rows(rows)

    assert len(audit_rows) == 2
    assert audit_rows[0].question_type == "Ranking"
    assert audit_rows[0].ranking_option_id == 101
    assert audit_rows[0].ranking_rank_value == 1
    assert audit_rows[0].original_ranking_rank_value == 2
    assert audit_rows[1].ranking_option_id == 102
    assert audit_rows[1].ranking_rank_value == 2
    assert audit_rows[1].original_ranking_rank_value == 1


def test_answer_audit_rows_preserve_original_ranking_when_current_is_cleared():
    now = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
    rows = [
        {
            "SurveyID": 42,
            "Title": "Planning",
            "ClosedAtUtc": now,
            "ResponseID": 9,
            "DiscordUserID": 123,
            "OriginalAnswersJson": json.dumps({"rankings": {"10": [102, 101]}}),
            "ResponseCreatedAtUtc": now,
            "ResponseUpdatedAtUtc": now,
            "SurveyQuestionID": 10,
            "QuestionKey": "q1",
            "Prompt": "Rank priorities",
            "QuestionType": "Ranking",
            "IsRequired": 0,
            "SurveyOptionID": None,
            "OptionKey": None,
            "Label": None,
            "AnswerText": None,
            "DetailText": None,
            "RatingValue": None,
            "RankingOptionID": None,
            "RankingOptionKey": None,
            "RankingOptionLabel": None,
            "RankingRankValue": None,
        }
    ]

    audit_rows = survey_dal._answer_audit_from_rows(rows)

    assert len(audit_rows) == 2
    assert audit_rows[0].question_type == "Ranking"
    assert audit_rows[0].ranking_option_id == 102
    assert audit_rows[0].ranking_rank_value is None
    assert audit_rows[0].original_ranking_rank_value == 1
    assert audit_rows[1].ranking_option_id == 101
    assert audit_rows[1].ranking_rank_value is None
    assert audit_rows[1].original_ranking_rank_value == 2
