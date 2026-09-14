from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from stats_alerts.db import run_one_async, run_query_async
from voting.option_emojis import option_emoji_from_row
from voting.reporting_models import (
    REPORT_CONTENT_SURVEY,
    REPORT_CONTENT_VOTE,
    DashboardReportingOptionAggregate,
    DashboardReportingSummary,
    EngagementItemSummary,
    EngagementParticipant,
)
from voting.result_visibility import normalize_result_visibility
from voting.vote_modes import normalize_vote_mode


def _aware_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    if isinstance(value, str):
        text = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
        return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
    return None


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def _bool(value: Any) -> bool:
    return bool(int(value or 0))


def _message_link(*, guild_id: Any, channel_id: Any, message_id: Any) -> str:
    if message_id in (None, ""):
        return ""
    host = "https://discord" + ".com/channels"
    return f"{host}/{int(guild_id)}/{int(channel_id)}/{int(message_id)}"


def _summary_from_vote_row(row: Mapping[str, Any]) -> DashboardReportingSummary:
    created_at = _aware_utc(row.get("CreatedAtUtc"))
    closes_at = _aware_utc(row.get("ClosesAtUtc"))
    if created_at is None or closes_at is None:
        raise ValueError("Vote reporting row is missing required UTC timestamps.")
    return DashboardReportingSummary(
        content_kind=REPORT_CONTENT_VOTE,
        content_id=int(row["VotePostID"]),
        title=str(row.get("Title") or ""),
        status=str(row.get("Status") or ""),
        result_visibility=normalize_result_visibility(row.get("ResultVisibility")),
        created_at_utc=created_at,
        closes_at_utc=closes_at,
        closed_at_utc=_aware_utc(row.get("ClosedAtUtc")),
        total_participants=int(row.get("TotalParticipants") or 0),
        total_selections=int(row.get("TotalSelections") or 0),
        option_count=int(row.get("OptionCount") or 0),
        question_count=1,
        required_question_count=1,
        optional_question_count=0,
        vote_mode=normalize_vote_mode(row.get("VoteMode")),
        message_link=_message_link(
            guild_id=row.get("GuildID"),
            channel_id=row.get("ChannelID"),
            message_id=row.get("MessageID"),
        ),
    )


def _summary_from_survey_row(row: Mapping[str, Any]) -> DashboardReportingSummary:
    created_at = _aware_utc(row.get("CreatedAtUtc"))
    closes_at = _aware_utc(row.get("ClosesAtUtc"))
    if created_at is None or closes_at is None:
        raise ValueError("Survey reporting row is missing required UTC timestamps.")
    answer_counts = {
        "choice": int(row.get("ChoiceQuestionCount") or 0),
        "text": int(row.get("TextQuestionCount") or 0),
        "rating": int(row.get("RatingQuestionCount") or 0),
        "ranking": int(row.get("RankingQuestionCount") or 0),
    }
    answer_type_summary = ", ".join(
        f"{count} {label}" for label, count in answer_counts.items() if count > 0
    )
    return DashboardReportingSummary(
        content_kind=REPORT_CONTENT_SURVEY,
        content_id=int(row["SurveyID"]),
        title=str(row.get("Title") or ""),
        status=str(row.get("Status") or ""),
        result_visibility=normalize_result_visibility(row.get("ResultVisibility")),
        created_at_utc=created_at,
        closes_at_utc=closes_at,
        closed_at_utc=_aware_utc(row.get("ClosedAtUtc")),
        total_participants=int(row.get("TotalParticipants") or 0),
        total_selections=int(row.get("TotalSelections") or 0),
        option_count=int(row.get("OptionCount") or 0),
        question_count=int(row.get("QuestionCount") or 0),
        required_question_count=int(row.get("RequiredQuestionCount") or 0),
        optional_question_count=int(row.get("OptionalQuestionCount") or 0),
        answer_type_summary=answer_type_summary,
        message_link=_message_link(
            guild_id=row.get("GuildID"),
            channel_id=row.get("ChannelID"),
            message_id=row.get("MessageID"),
        ),
    )


def _option_from_vote_row(row: Mapping[str, Any]) -> DashboardReportingOptionAggregate:
    return DashboardReportingOptionAggregate(
        content_kind=REPORT_CONTENT_VOTE,
        content_id=int(row["VotePostID"]),
        option_id=int(row["OptionID"]),
        option_key=str(row.get("OptionKey") or ""),
        option_label=str(row.get("OptionLabel") or ""),
        option_sort_order=int(row.get("OptionSortOrder") or 0),
        total_participants=int(row.get("TotalParticipants") or 0),
        selection_count=int(row.get("SelectionCount") or 0),
        is_top_selection=_bool(row.get("IsTopSelection")),
        option_emoji=option_emoji_from_row(row),
    )


def _engagement_item_from_row(row: Mapping[str, Any]) -> EngagementItemSummary:
    created_at = _aware_utc(row.get("CreatedAtUtc"))
    if created_at is None:
        raise ValueError("Engagement item row is missing CreatedAtUtc.")
    return EngagementItemSummary(
        content_kind=str(row.get("ContentKind") or ""),
        content_id=int(row["ContentID"]),
        created_at_utc=created_at,
        status=str(row.get("Status") or ""),
        title=str(row.get("Title") or ""),
    )


def _engagement_participant_from_row(row: Mapping[str, Any]) -> EngagementParticipant:
    participated_at = _aware_utc(row.get("ParticipatedAtUtc"))
    if participated_at is None:
        raise ValueError("Engagement participant row is missing ParticipatedAtUtc.")
    return EngagementParticipant(
        content_kind=str(row.get("ContentKind") or ""),
        content_id=int(row["ContentID"]),
        discord_user_id=int(row["DiscordUserID"]),
        participated_at_utc=participated_at,
    )


async def _vote_option_emoji_columns_exist() -> bool:
    row = await run_one_async("""
        SELECT COL_LENGTH(N'dbo.VotePostOptions', N'EmojiKind') AS EmojiKindColumn;
        """)
    return bool(row and row.get("EmojiKindColumn") not in (None, ""))


async def list_vote_dashboard_summaries(
    *, limit: int = 25
) -> tuple[DashboardReportingSummary, ...]:
    rows = await run_query_async(
        """
        SELECT TOP (?) p.VotePostID, p.GuildID, p.ChannelID, p.MessageID, p.Title, p.Status,
               p.ResultVisibility, p.VoteMode, p.CreatedAtUtc, p.ClosesAtUtc, p.ClosedAtUtc,
               (
                   SELECT COUNT_BIG(1)
                   FROM dbo.VotePostOptions o
                   WHERE o.VotePostID = p.VotePostID
               ) AS OptionCount,
               CASE
                   WHEN COALESCE(p.VoteMode, 'OneChoice') = 'MultiSelect'
                       THEN (
                           SELECT COUNT_BIG(1)
                           FROM dbo.VotePostMultiSelectVotes mv
                           WHERE mv.VotePostID = p.VotePostID
                       )
                   ELSE (
                       SELECT COUNT_BIG(1)
                       FROM dbo.VotePostVotes v
                       WHERE v.VotePostID = p.VotePostID
                   )
               END AS TotalParticipants,
               CASE
                   WHEN COALESCE(p.VoteMode, 'OneChoice') = 'MultiSelect'
                       THEN (
                           SELECT COUNT_BIG(1)
                           FROM dbo.VotePostMultiSelectSelections ms
                           WHERE ms.VotePostID = p.VotePostID
                       )
                   ELSE (
                       SELECT COUNT_BIG(1)
                       FROM dbo.VotePostVotes v
                       WHERE v.VotePostID = p.VotePostID
                   )
               END AS TotalSelections
        FROM dbo.VotePosts p
        WHERE p.MessageID IS NOT NULL
        ORDER BY p.ClosesAtUtc DESC, p.VotePostID DESC;
        """,
        (max(1, int(limit)),),
    )
    return tuple(_summary_from_vote_row(row) for row in rows)


async def list_survey_dashboard_summaries(
    *, limit: int = 25
) -> tuple[DashboardReportingSummary, ...]:
    rows = await run_query_async(
        """
        SELECT TOP (?) p.SurveyID, p.GuildID, p.ChannelID, p.MessageID, p.Title, p.Status,
               p.ResultVisibility, p.CreatedAtUtc, p.ClosesAtUtc, p.ClosedAtUtc,
               (
                   SELECT COUNT_BIG(1)
                   FROM dbo.SurveyQuestions q
                   WHERE q.SurveyID = p.SurveyID
               ) AS QuestionCount,
               (
                   SELECT COUNT_BIG(1)
                   FROM dbo.SurveyQuestions q
                   WHERE q.SurveyID = p.SurveyID
                     AND q.IsRequired = 1
               ) AS RequiredQuestionCount,
               (
                   SELECT COUNT_BIG(1)
                   FROM dbo.SurveyQuestions q
                   WHERE q.SurveyID = p.SurveyID
                     AND q.IsRequired = 0
               ) AS OptionalQuestionCount,
               (
                   SELECT COUNT_BIG(1)
                   FROM dbo.SurveyQuestions q
                   WHERE q.SurveyID = p.SurveyID
                     AND q.QuestionType IN ('SingleChoice', 'MultiSelect')
               ) AS ChoiceQuestionCount,
               (
                   SELECT COUNT_BIG(1)
                   FROM dbo.SurveyQuestions q
                   WHERE q.SurveyID = p.SurveyID
                     AND q.QuestionType = 'Text'
               ) AS TextQuestionCount,
               (
                   SELECT COUNT_BIG(1)
                   FROM dbo.SurveyQuestions q
                   WHERE q.SurveyID = p.SurveyID
                     AND q.QuestionType = 'Rating'
               ) AS RatingQuestionCount,
               (
                   SELECT COUNT_BIG(1)
                   FROM dbo.SurveyQuestions q
                   WHERE q.SurveyID = p.SurveyID
                     AND q.QuestionType = 'Ranking'
               ) AS RankingQuestionCount,
               (
                   SELECT COUNT_BIG(1)
                   FROM dbo.SurveyQuestionOptions o
                   JOIN dbo.SurveyQuestions q
                     ON q.SurveyQuestionID = o.SurveyQuestionID
                   WHERE q.SurveyID = p.SurveyID
               ) AS OptionCount,
               (
                   SELECT COUNT_BIG(1)
                   FROM dbo.SurveyResponses r
                   WHERE r.SurveyID = p.SurveyID
               ) AS TotalParticipants,
               (
                   SELECT COUNT_BIG(1)
                   FROM dbo.SurveyAnswers a
                   WHERE a.SurveyID = p.SurveyID
               ) + (
                   SELECT COUNT_BIG(1)
                   FROM dbo.SurveyTextAnswers t
                   WHERE t.SurveyID = p.SurveyID
               ) + (
                   SELECT COUNT_BIG(1)
                   FROM dbo.SurveyRatingAnswers rating
                   WHERE rating.SurveyID = p.SurveyID
               ) + (
                   SELECT COUNT_BIG(1)
                   FROM dbo.SurveyRankingAnswers ranking
                   WHERE ranking.SurveyID = p.SurveyID
               ) AS TotalSelections
        FROM dbo.SurveyPosts p
        WHERE p.MessageID IS NOT NULL
        ORDER BY p.ClosesAtUtc DESC, p.SurveyID DESC;
        """,
        (max(1, int(limit)),),
    )
    return tuple(_summary_from_survey_row(row) for row in rows)


async def list_vote_dashboard_option_aggregates(
    vote_post_ids: Sequence[int],
) -> tuple[DashboardReportingOptionAggregate, ...]:
    normalized_ids = tuple(dict.fromkeys(int(vote_post_id) for vote_post_id in vote_post_ids))
    if not normalized_ids:
        return ()
    placeholders = ", ".join("?" for _ in normalized_ids)
    emoji_columns_exist = await _vote_option_emoji_columns_exist()
    emoji_select = (
        "o.EmojiKind, o.EmojiText, o.EmojiName, o.EmojiID, o.EmojiAnimated"
        if emoji_columns_exist
        else (
            "CAST(NULL AS varchar(20)) AS EmojiKind, "
            "CAST(NULL AS nvarchar(120)) AS EmojiText, "
            "CAST(NULL AS nvarchar(64)) AS EmojiName, "
            "CAST(NULL AS varchar(32)) AS EmojiID, "
            "CAST(NULL AS bit) AS EmojiAnimated"
        )
    )
    emoji_group_by = (
        ", o.EmojiKind, o.EmojiText, o.EmojiName, o.EmojiID, o.EmojiAnimated"
        if emoji_columns_exist
        else ""
    )
    rows = await run_query_async(
        f"""
        WITH ParticipantCounts AS (
            SELECT p.VotePostID,
                   CASE
                       WHEN COALESCE(p.VoteMode, 'OneChoice') = 'MultiSelect'
                           THEN (
                               SELECT COUNT_BIG(1)
                               FROM dbo.VotePostMultiSelectVotes mv
                               WHERE mv.VotePostID = p.VotePostID
                           )
                       ELSE (
                           SELECT COUNT_BIG(1)
                           FROM dbo.VotePostVotes v
                           WHERE v.VotePostID = p.VotePostID
                       )
                   END AS TotalParticipants
            FROM dbo.VotePosts p
            WHERE p.VotePostID IN ({placeholders})
        ),
        OptionCounts AS (
            SELECT p.VotePostID, o.OptionID, o.OptionKey, o.Label AS OptionLabel,
                   o.SortOrder AS OptionSortOrder,
                   {emoji_select},
                   CASE
                       WHEN COALESCE(p.VoteMode, 'OneChoice') = 'MultiSelect'
                           THEN COUNT(ms.DiscordUserID)
                       ELSE COUNT(v.DiscordUserID)
                   END AS SelectionCount
            FROM dbo.VotePosts p
            JOIN dbo.VotePostOptions o
              ON o.VotePostID = p.VotePostID
            LEFT JOIN dbo.VotePostVotes v
              ON v.VotePostID = p.VotePostID
             AND v.OptionID = o.OptionID
             AND COALESCE(p.VoteMode, 'OneChoice') <> 'MultiSelect'
            LEFT JOIN dbo.VotePostMultiSelectVotes mv
              ON mv.VotePostID = p.VotePostID
             AND COALESCE(p.VoteMode, 'OneChoice') = 'MultiSelect'
            LEFT JOIN dbo.VotePostMultiSelectSelections ms
              ON ms.VotePostID = p.VotePostID
             AND ms.DiscordUserID = mv.DiscordUserID
             AND ms.OptionID = o.OptionID
             AND COALESCE(p.VoteMode, 'OneChoice') = 'MultiSelect'
            WHERE p.VotePostID IN ({placeholders})
            GROUP BY p.VotePostID, p.VoteMode, o.OptionID, o.OptionKey, o.Label, o.SortOrder{emoji_group_by}
        ),
        Tops AS (
            SELECT VotePostID, MAX(SelectionCount) AS TopSelectionCount
            FROM OptionCounts
            GROUP BY VotePostID
        )
        SELECT oc.VotePostID, oc.OptionID, oc.OptionKey, oc.OptionLabel,
               oc.EmojiKind, oc.EmojiText, oc.EmojiName, oc.EmojiID, oc.EmojiAnimated,
               oc.OptionSortOrder, oc.SelectionCount, pc.TotalParticipants,
               CASE
                   WHEN oc.SelectionCount > 0 AND oc.SelectionCount = t.TopSelectionCount THEN 1
                   ELSE 0
               END AS IsTopSelection
        FROM OptionCounts oc
        JOIN Tops t
          ON t.VotePostID = oc.VotePostID
        JOIN ParticipantCounts pc
          ON pc.VotePostID = oc.VotePostID
        ORDER BY oc.VotePostID DESC, oc.OptionSortOrder ASC, oc.OptionID ASC;
        """,
        normalized_ids + normalized_ids,
    )
    return tuple(_option_from_vote_row(row) for row in rows)


async def list_vote_engagement_items(
    *, start_at_utc: datetime, end_at_utc: datetime
) -> tuple[EngagementItemSummary, ...]:
    start_at = _naive_utc(start_at_utc)
    end_at = _naive_utc(end_at_utc)
    rows = await run_query_async(
        """
        SELECT 'vote' AS ContentKind,
               p.VotePostID AS ContentID,
               p.Title,
               p.CreatedAtUtc,
               p.Status
        FROM dbo.VotePosts p
        WHERE p.MessageID IS NOT NULL
          AND p.Status = 'Closed'
          AND p.CreatedAtUtc >= ?
          AND p.CreatedAtUtc < ?
        ORDER BY p.CreatedAtUtc DESC, p.VotePostID DESC;
        """,
        (start_at, end_at),
    )
    return tuple(_engagement_item_from_row(row) for row in rows)


async def list_survey_engagement_items(
    *, start_at_utc: datetime, end_at_utc: datetime
) -> tuple[EngagementItemSummary, ...]:
    start_at = _naive_utc(start_at_utc)
    end_at = _naive_utc(end_at_utc)
    rows = await run_query_async(
        """
        SELECT 'survey' AS ContentKind,
               p.SurveyID AS ContentID,
               p.Title,
               p.CreatedAtUtc,
               p.Status
        FROM dbo.SurveyPosts p
        WHERE p.MessageID IS NOT NULL
          AND p.Status = 'Closed'
          AND p.CreatedAtUtc >= ?
          AND p.CreatedAtUtc < ?
        ORDER BY p.CreatedAtUtc DESC, p.SurveyID DESC;
        """,
        (start_at, end_at),
    )
    return tuple(_engagement_item_from_row(row) for row in rows)


async def list_vote_engagement_participants(
    *, start_at_utc: datetime, end_at_utc: datetime
) -> tuple[EngagementParticipant, ...]:
    start_at = _naive_utc(start_at_utc)
    end_at = _naive_utc(end_at_utc)
    rows = await run_query_async(
        """
        SELECT 'vote' AS ContentKind,
               p.VotePostID AS ContentID,
               v.DiscordUserID,
               v.UpdatedAtUtc AS ParticipatedAtUtc
        FROM dbo.VotePosts p
        JOIN dbo.VotePostVotes v
          ON v.VotePostID = p.VotePostID
        WHERE p.MessageID IS NOT NULL
          AND p.Status = 'Closed'
          AND COALESCE(p.VoteMode, 'OneChoice') <> 'MultiSelect'
          AND p.CreatedAtUtc >= ?
          AND p.CreatedAtUtc < ?
        UNION ALL
        SELECT 'vote' AS ContentKind,
               p.VotePostID AS ContentID,
               mv.DiscordUserID,
               mv.UpdatedAtUtc AS ParticipatedAtUtc
        FROM dbo.VotePosts p
        JOIN dbo.VotePostMultiSelectVotes mv
          ON mv.VotePostID = p.VotePostID
        WHERE p.MessageID IS NOT NULL
          AND p.Status = 'Closed'
          AND COALESCE(p.VoteMode, 'OneChoice') = 'MultiSelect'
          AND p.CreatedAtUtc >= ?
          AND p.CreatedAtUtc < ?
        ORDER BY ContentID DESC, DiscordUserID ASC;
        """,
        (start_at, end_at, start_at, end_at),
    )
    return tuple(_engagement_participant_from_row(row) for row in rows)


async def list_survey_engagement_participants(
    *, start_at_utc: datetime, end_at_utc: datetime
) -> tuple[EngagementParticipant, ...]:
    start_at = _naive_utc(start_at_utc)
    end_at = _naive_utc(end_at_utc)
    rows = await run_query_async(
        """
        SELECT 'survey' AS ContentKind,
               p.SurveyID AS ContentID,
               r.DiscordUserID,
               r.UpdatedAtUtc AS ParticipatedAtUtc
        FROM dbo.SurveyPosts p
        JOIN dbo.SurveyResponses r
          ON r.SurveyID = p.SurveyID
        WHERE p.MessageID IS NOT NULL
          AND p.Status = 'Closed'
          AND p.CreatedAtUtc >= ?
          AND p.CreatedAtUtc < ?
        ORDER BY p.SurveyID DESC, r.DiscordUserID ASC;
        """,
        (start_at, end_at),
    )
    return tuple(_engagement_participant_from_row(row) for row in rows)
