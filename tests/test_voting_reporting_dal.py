from __future__ import annotations

from datetime import UTC, datetime

import pytest

from voting import reporting_dal
from voting.reporting_models import REPORT_CONTENT_SURVEY, REPORT_CONTENT_VOTE


@pytest.mark.asyncio
async def test_vote_dashboard_summaries_read_aggregate_vote_rows(monkeypatch):
    now = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
    captured: dict[str, object] = {}

    async def fake_run_query_async(sql, params=()):
        captured["sql"] = sql
        captured["params"] = params
        return [
            {
                "VotePostID": 42,
                "GuildID": 1,
                "ChannelID": 2,
                "MessageID": 3,
                "Title": "Availability",
                "Status": "Closed",
                "ResultVisibility": "HiddenUntilClose",
                "VoteMode": "MultiSelect",
                "CreatedAtUtc": now,
                "ClosesAtUtc": now,
                "ClosedAtUtc": now,
                "OptionCount": 3,
                "TotalParticipants": 5,
                "TotalSelections": 8,
            }
        ]

    monkeypatch.setattr(reporting_dal, "run_query_async", fake_run_query_async)

    rows = await reporting_dal.list_vote_dashboard_summaries(limit=99)

    assert captured["params"] == (99,)
    assert "dbo.VotePosts" in str(captured["sql"])
    assert "COUNT_BIG" in str(captured["sql"])
    assert "DiscordName" not in str(captured["sql"])
    assert rows[0].content_kind == REPORT_CONTENT_VOTE
    assert rows[0].content_id == 42
    assert rows[0].total_participants == 5
    assert rows[0].total_selections == 8
    assert rows[0].vote_mode == "MultiSelect"
    assert rows[0].message_link == "https://discord" + ".com/channels/1/2/3"


@pytest.mark.asyncio
async def test_survey_dashboard_summaries_read_aggregate_survey_rows(monkeypatch):
    now = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
    captured: dict[str, object] = {}

    async def fake_run_query_async(sql, params=()):
        captured["sql"] = sql
        captured["params"] = params
        return [
            {
                "SurveyID": 77,
                "GuildID": 1,
                "ChannelID": 2,
                "MessageID": 3,
                "Title": "Planning",
                "Status": "Closed",
                "ResultVisibility": "PublicLive",
                "CreatedAtUtc": now,
                "ClosesAtUtc": now,
                "ClosedAtUtc": now,
                "QuestionCount": 4,
                "RequiredQuestionCount": 3,
                "OptionalQuestionCount": 1,
                "ChoiceQuestionCount": 1,
                "TextQuestionCount": 1,
                "RatingQuestionCount": 1,
                "RankingQuestionCount": 1,
                "OptionCount": 8,
                "TotalParticipants": 6,
                "TotalSelections": 18,
            }
        ]

    monkeypatch.setattr(reporting_dal, "run_query_async", fake_run_query_async)

    rows = await reporting_dal.list_survey_dashboard_summaries(limit=10)

    assert captured["params"] == (10,)
    assert "dbo.SurveyPosts" in str(captured["sql"])
    assert "AnswerText" not in str(captured["sql"])
    assert "DetailText" not in str(captured["sql"])
    assert "DiscordUserID" not in str(captured["sql"])
    assert rows[0].content_kind == REPORT_CONTENT_SURVEY
    assert rows[0].content_id == 77
    assert rows[0].question_count == 4
    assert rows[0].answer_type_summary == "1 choice, 1 text, 1 rating, 1 ranking"


@pytest.mark.asyncio
async def test_vote_dashboard_option_aggregates_read_counts_without_identity(monkeypatch):
    captured: dict[str, object] = {}

    async def fake_run_query_async(sql, params=()):
        captured["sql"] = sql
        captured["params"] = params
        return [
            {
                "VotePostID": 42,
                "OptionID": 10,
                "OptionKey": "opt1",
                "OptionLabel": "A",
                "OptionSortOrder": 1,
                "SelectionCount": 3,
                "TotalParticipants": 5,
                "IsTopSelection": 1,
            }
        ]

    async def fake_run_one_async(sql, params=()):
        captured["column_probe"] = sql
        assert params == ()
        return {"EmojiKindColumn": None}

    monkeypatch.setattr(reporting_dal, "run_one_async", fake_run_one_async)
    monkeypatch.setattr(reporting_dal, "run_query_async", fake_run_query_async)

    rows = await reporting_dal.list_vote_dashboard_option_aggregates((42, 42))

    assert captured["params"] == (42, 42)
    assert "COL_LENGTH" in str(captured["column_probe"])
    assert "VotePostMultiSelectSelections" in str(captured["sql"])
    assert "CAST(NULL AS varchar(20)) AS EmojiKind" in str(captured["sql"])
    assert "DiscordName" not in str(captured["sql"])
    assert rows[0].content_kind == REPORT_CONTENT_VOTE
    assert rows[0].selection_count == 3
    assert rows[0].is_top_selection is True


@pytest.mark.asyncio
async def test_vote_dashboard_option_aggregates_skip_empty_id_list(monkeypatch):
    async def fake_run_query_async(_sql, _params=()):
        raise AssertionError("database should not be queried for an empty id list")

    monkeypatch.setattr(reporting_dal, "run_query_async", fake_run_query_async)

    assert await reporting_dal.list_vote_dashboard_option_aggregates(()) == ()
