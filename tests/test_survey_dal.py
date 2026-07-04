from __future__ import annotations

from datetime import UTC, datetime
import json

import pytest

from voting import survey_dal
from voting.service import VoteValidationError


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
    monkeypatch.setattr(survey_dal, "exec_with_cursor", lambda callback: callback(FakeCursor()))
    monkeypatch.setattr(survey_dal, "run_blocking_in_thread", fake_run_blocking_in_thread)

    with pytest.raises(VoteValidationError, match=survey_dal.SURVEY_RATING_MIGRATION_ID):
        await survey_dal.submit_survey_response(
            survey_id=42,
            discord_user_id=123,
            answers_by_question_id={},
            rating_answers_by_question_id={10: 5},
            now_utc=now,
        )


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
