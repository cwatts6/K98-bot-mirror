from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
import json
import logging
from typing import Any

from file_utils import cursor_row_to_dict, fetch_one_dict, run_blocking_in_thread
from stats_alerts.db import exec_with_cursor, run_one_async, run_query_async
from voting.result_visibility import normalize_result_visibility
from voting.service import VoteValidationError
from voting.survey_models import (
    MAX_RATING_VALUE,
    SURVEY_QUESTION_RANKING,
    SURVEY_QUESTION_RATING,
    SURVEY_QUESTION_SINGLE_CHOICE,
    SurveyAnswerAuditRow,
    SurveyCloseResult,
    SurveyCreateRequest,
    SurveyDraftSaveResult,
    SurveyLookupChoice,
    SurveyQuestion,
    SurveyQuestionOption,
    SurveyRankingCount,
    SurveyRatingCount,
    SurveyRatingLabel,
    SurveyReminder,
    SurveyReportingOptionRow,
    SurveyReportingQuestionRow,
    SurveyResponseDraft,
    SurveyResponsePayload,
    SurveySnapshot,
    SurveySubmitResult,
)

logger = logging.getLogger(__name__)

SURVEY_RATING_MIGRATION_ID = "20260704_002_add_survey_rating_questions"
SURVEY_RATING_MIGRATION_MESSAGE = (
    "Survey rating storage is unavailable. Deploy SQL migration "
    f"{SURVEY_RATING_MIGRATION_ID} before using rating survey questions."
)
SURVEY_RATING_SCALE_MIGRATION_ID = "20260707_001_add_survey_rating_scales"
SURVEY_RATING_SCALE_MIGRATION_MESSAGE = (
    "Survey rating scale metadata is unavailable. Deploy SQL migration "
    f"{SURVEY_RATING_SCALE_MIGRATION_ID} before using extended rating scales."
)
SURVEY_RANKING_MIGRATION_ID = "20260704_003_add_survey_ranking_questions"
SURVEY_RANKING_MIGRATION_MESSAGE = (
    "Survey ranking storage is unavailable. Deploy SQL migration "
    f"{SURVEY_RANKING_MIGRATION_ID} before using ranking survey questions."
)
SURVEY_REPORTING_MIGRATION_ID = "20260705_001_add_survey_reporting_views"
SURVEY_REPORTING_MIGRATION_MESSAGE = (
    "Survey reporting views are unavailable. Deploy SQL migration "
    f"{SURVEY_REPORTING_MIGRATION_ID} before using Survey Export v2."
)
SURVEY_DRAFT_MIGRATION_ID = "20260706_001_add_survey_response_drafts"
SURVEY_DRAFT_MIGRATION_MESSAGE = (
    "Survey draft storage is unavailable. Deploy SQL migration "
    f"{SURVEY_DRAFT_MIGRATION_ID} before using survey drafts."
)


def _naive_utc(value: datetime) -> datetime:
    aware = value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    return aware.replace(tzinfo=None)


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


def _bool(value: Any) -> bool:
    return bool(int(value or 0))


def _question_key(index: int) -> str:
    return f"q{index + 1}"


def _option_key(index: int) -> str:
    return f"opt{index + 1}"


def _reminder_due_at(closes_at_utc: datetime, offset_minutes: int) -> datetime:
    return closes_at_utc - timedelta(minutes=int(offset_minutes))


def _rows_to_options(rows: Sequence[dict[str, Any]]) -> dict[int, tuple[SurveyQuestionOption, ...]]:
    ranking_counts_by_option_id: dict[int, list[SurveyRankingCount]] = {}
    for row in rows:
        option_id_value = row.get("SurveyOptionID")
        rank_value = row.get("RankValue")
        if option_id_value in (None, "") or rank_value in (None, ""):
            continue
        ranking_counts_by_option_id.setdefault(int(option_id_value), []).append(
            SurveyRankingCount(
                rank_value=int(rank_value),
                response_count=int(row.get("RankResponseCount") or 0),
            )
        )
    grouped: dict[int, list[SurveyQuestionOption]] = {}
    seen_option_ids: set[int] = set()
    for row in rows:
        question_id = int(row["SurveyQuestionID"])
        option_id = int(row["SurveyOptionID"])
        if option_id in seen_option_ids:
            continue
        seen_option_ids.add(option_id)
        grouped.setdefault(question_id, []).append(
            SurveyQuestionOption(
                option_id=option_id,
                survey_question_id=question_id,
                option_key=str(row.get("OptionKey") or ""),
                label=str(row.get("Label") or ""),
                sort_order=int(row.get("SortOrder") or 0),
                response_count=int(row.get("ResponseCount") or 0),
                ranking_average=(
                    float(row["AverageRank"]) if row.get("AverageRank") not in (None, "") else None
                ),
                ranking_first_place_count=int(row.get("FirstPlaceCount") or 0),
                ranking_counts=tuple(ranking_counts_by_option_id.get(option_id, ())),
            )
        )
    return {key: tuple(value) for key, value in grouped.items()}


def _rows_to_rating_counts(
    rows: Sequence[dict[str, Any]],
) -> dict[int, tuple[SurveyRatingCount, ...]]:
    grouped: dict[int, list[SurveyRatingCount]] = {}
    for row in rows:
        question_id = int(row["SurveyQuestionID"])
        grouped.setdefault(question_id, []).append(
            SurveyRatingCount(
                rating_value=int(row.get("RatingValue") or 0),
                response_count=int(row.get("ResponseCount") or 0),
            )
        )
    return {key: tuple(value) for key, value in grouped.items()}


def _rows_to_rating_labels(
    rows: Sequence[dict[str, Any]],
) -> dict[int, tuple[SurveyRatingLabel, ...]]:
    grouped: dict[int, list[SurveyRatingLabel]] = {}
    for row in rows:
        question_id = int(row["SurveyQuestionID"])
        label = str(row.get("Label") or "").strip()
        if not label:
            continue
        grouped.setdefault(question_id, []).append(
            SurveyRatingLabel(
                rating_value=int(row.get("RatingValue") or 0),
                label=label,
            )
        )
    return {key: tuple(sorted(value, key=lambda item: item.rating_value)) for key, value in grouped.items()}


async def _survey_rating_answers_table_exists() -> bool:
    row = await run_one_async("""
        SELECT OBJECT_ID(N'dbo.SurveyRatingAnswers', N'U') AS ObjectId;
        """)
    return bool(row and row.get("ObjectId") not in (None, ""))


def _survey_rating_answers_table_exists_sync(cur) -> bool:
    cur.execute("""
        SELECT OBJECT_ID(N'dbo.SurveyRatingAnswers', N'U') AS ObjectId;
        """)
    row = fetch_one_dict(cur)
    return bool(row and row.get("ObjectId") not in (None, ""))


async def _survey_rating_scale_metadata_exists() -> bool:
    row = await run_one_async("""
        SELECT
            COL_LENGTH(N'dbo.SurveyQuestions', N'RatingMinValue') AS RatingMinValueColumn,
            OBJECT_ID(N'dbo.SurveyRatingChoiceLabels', N'U') AS LabelsObjectId;
        """)
    return bool(
        row
        and row.get("RatingMinValueColumn") not in (None, "")
        and row.get("LabelsObjectId") not in (None, "")
    )


def _survey_rating_scale_metadata_exists_sync(cur) -> bool:
    cur.execute("""
        SELECT
            COL_LENGTH(N'dbo.SurveyQuestions', N'RatingMinValue') AS RatingMinValueColumn,
            OBJECT_ID(N'dbo.SurveyRatingChoiceLabels', N'U') AS LabelsObjectId;
        """)
    row = fetch_one_dict(cur)
    return bool(
        row
        and row.get("RatingMinValueColumn") not in (None, "")
        and row.get("LabelsObjectId") not in (None, "")
    )


def _question_uses_extended_rating_scale(question) -> bool:
    if str(getattr(question, "question_type", "")) != SURVEY_QUESTION_RATING:
        return False
    return bool(
        int(getattr(question, "rating_min_value", 1) or 1) != 1
        or int(getattr(question, "rating_max_value", 5) or 5) != 5
        or str(getattr(question, "rating_low_label", "") or "").strip()
        or str(getattr(question, "rating_high_label", "") or "").strip()
        or tuple(getattr(question, "rating_labels", ()) or ())
    )


async def _survey_ranking_answers_table_exists() -> bool:
    row = await run_one_async("""
        SELECT OBJECT_ID(N'dbo.SurveyRankingAnswers', N'U') AS ObjectId;
        """)
    return bool(row and row.get("ObjectId") not in (None, ""))


def _survey_ranking_answers_table_exists_sync(cur) -> bool:
    cur.execute("""
        SELECT OBJECT_ID(N'dbo.SurveyRankingAnswers', N'U') AS ObjectId;
        """)
    row = fetch_one_dict(cur)
    return bool(row and row.get("ObjectId") not in (None, ""))


async def _survey_reporting_views_exist() -> bool:
    row = await run_one_async("""
        SELECT
            OBJECT_ID(N'dbo.v_SurveyReportingQuestionSummary', N'V') AS QuestionViewObjectId,
            OBJECT_ID(N'dbo.v_SurveyReportingOptionSummary', N'V') AS OptionViewObjectId;
        """)
    return bool(
        row
        and row.get("QuestionViewObjectId") not in (None, "")
        and row.get("OptionViewObjectId") not in (None, "")
    )


async def _survey_response_drafts_table_exists() -> bool:
    row = await run_one_async("""
        SELECT OBJECT_ID(N'dbo.SurveyResponseDrafts', N'U') AS ObjectId;
        """)
    return bool(row and row.get("ObjectId") not in (None, ""))


def _survey_response_drafts_table_exists_sync(cur) -> bool:
    cur.execute("""
        SELECT OBJECT_ID(N'dbo.SurveyResponseDrafts', N'U') AS ObjectId;
        """)
    row = fetch_one_dict(cur)
    return bool(row and row.get("ObjectId") not in (None, ""))


async def _require_survey_reporting_views() -> None:
    if await _survey_reporting_views_exist():
        return
    logger.warning("survey_reporting_views_missing migration=%s", SURVEY_REPORTING_MIGRATION_ID)
    raise VoteValidationError(SURVEY_REPORTING_MIGRATION_MESSAGE)


async def _require_survey_response_drafts_table() -> None:
    if await _survey_response_drafts_table_exists():
        return
    logger.warning("survey_response_drafts_missing migration=%s", SURVEY_DRAFT_MIGRATION_ID)
    raise VoteValidationError(SURVEY_DRAFT_MIGRATION_MESSAGE)


def _rows_to_questions(
    question_rows: Sequence[dict[str, Any]],
    option_rows: Sequence[dict[str, Any]],
    rating_rows: Sequence[dict[str, Any]] = (),
    rating_label_rows: Sequence[dict[str, Any]] = (),
) -> tuple[SurveyQuestion, ...]:
    options_by_question_id = _rows_to_options(option_rows)
    rating_counts_by_question_id = _rows_to_rating_counts(rating_rows)
    rating_labels_by_question_id = _rows_to_rating_labels(rating_label_rows)
    return tuple(
        SurveyQuestion(
            question_id=int(row["SurveyQuestionID"]),
            survey_id=int(row["SurveyID"]),
            question_key=str(row.get("QuestionKey") or ""),
            prompt=str(row.get("Prompt") or ""),
            question_type=str(row.get("QuestionType") or SURVEY_QUESTION_SINGLE_CHOICE),
            sort_order=int(row.get("SortOrder") or 0),
            min_selections=(
                int(row["MinSelections"]) if row.get("MinSelections") not in (None, "") else 1
            ),
            max_selections=(
                int(row["MaxSelections"]) if row.get("MaxSelections") not in (None, "") else 1
            ),
            options=options_by_question_id.get(int(row["SurveyQuestionID"]), ()),
            allow_details=_bool(row.get("AllowDetails")),
            is_required=_bool(row.get("IsRequired", 1)),
            answered_response_count=(
                int(row["AnsweredResponseCount"])
                if row.get("AnsweredResponseCount") not in (None, "")
                else None
            ),
            rating_counts=rating_counts_by_question_id.get(int(row["SurveyQuestionID"]), ()),
            rating_average=(
                float(row["AverageRating"]) if row.get("AverageRating") not in (None, "") else None
            ),
            rating_min=(
                int(row["MinimumRating"]) if row.get("MinimumRating") not in (None, "") else None
            ),
            rating_max=(
                int(row["MaximumRating"]) if row.get("MaximumRating") not in (None, "") else None
            ),
            rating_min_value=int(row.get("RatingMinValue") or 1),
            rating_max_value=int(row.get("RatingMaxValue") or 5),
            rating_low_label=(
                str(row.get("RatingLowLabel") or "").strip()
                if row.get("RatingLowLabel") not in (None, "")
                else None
            ),
            rating_high_label=(
                str(row.get("RatingHighLabel") or "").strip()
                if row.get("RatingHighLabel") not in (None, "")
                else None
            ),
            rating_labels=rating_labels_by_question_id.get(int(row["SurveyQuestionID"]), ()),
        )
        for row in question_rows
    )


def _rows_to_reminders(rows: Sequence[dict[str, Any]]) -> tuple[SurveyReminder, ...]:
    reminders: list[SurveyReminder] = []
    for row in rows:
        due_at = _aware_utc(row.get("DueAtUtc"))
        if due_at is None:
            continue
        reminders.append(
            SurveyReminder(
                reminder_id=int(row["ReminderID"]),
                survey_id=int(row["SurveyID"]),
                offset_minutes_before_close=int(row.get("OffsetMinutesBeforeClose") or 0),
                due_at_utc=due_at,
                sent_at_utc=_aware_utc(row.get("SentAtUtc")),
                message_id=(
                    int(row["MessageID"]) if row.get("MessageID") not in (None, "") else None
                ),
            )
        )
    return tuple(reminders)


def _reporting_question_from_row(row: Mapping[str, Any]) -> SurveyReportingQuestionRow:
    rating_label_summary = str(row.get("RatingLabels") or "").strip()
    rating_distribution = str(row.get("RatingDistribution") or "").strip()
    return SurveyReportingQuestionRow(
        survey_id=int(row["SurveyID"]),
        title=str(row.get("Title") or ""),
        status=str(row.get("Status") or ""),
        result_visibility=normalize_result_visibility(row.get("ResultVisibility")),
        question_id=int(row["SurveyQuestionID"]),
        question_key=str(row.get("QuestionKey") or ""),
        question_prompt=str(row.get("Prompt") or ""),
        question_type=str(row.get("QuestionType") or ""),
        question_sort_order=int(row.get("QuestionSortOrder") or 0),
        is_required=_bool(row.get("IsRequired", 1)),
        min_selections=int(row.get("MinSelections") or 0),
        max_selections=int(row.get("MaxSelections") or 0),
        allow_details=_bool(row.get("AllowDetails")),
        total_responses=int(row.get("TotalResponses") or 0),
        option_count=int(row.get("OptionCount") or 0),
        answered_responses=int(row.get("AnsweredResponses") or 0),
        skipped_responses=int(row.get("SkippedResponses") or 0),
        choice_selection_count=int(row.get("ChoiceSelectionCount") or 0),
        ranked_option_count=int(row.get("RankedOptionCount") or 0),
        ranking_first_place_count=int(row.get("RankingFirstPlaceCount") or 0),
        average_rating=(
            float(row["AverageRating"]) if row.get("AverageRating") not in (None, "") else None
        ),
        minimum_rating=(
            int(row["MinimumRating"]) if row.get("MinimumRating") not in (None, "") else None
        ),
        maximum_rating=(
            int(row["MaximumRating"]) if row.get("MaximumRating") not in (None, "") else None
        ),
        rating1_count=int(row.get("Rating1Count") or 0),
        rating2_count=int(row.get("Rating2Count") or 0),
        rating3_count=int(row.get("Rating3Count") or 0),
        rating4_count=int(row.get("Rating4Count") or 0),
        rating5_count=int(row.get("Rating5Count") or 0),
        rating_scale_min=int(row.get("RatingMinValue") or 1),
        rating_scale_max=int(row.get("RatingMaxValue") or 5),
        rating_low_label=(
            str(row.get("RatingLowLabel") or "").strip()
            if row.get("RatingLowLabel") not in (None, "")
            else None
        ),
        rating_high_label=(
            str(row.get("RatingHighLabel") or "").strip()
            if row.get("RatingHighLabel") not in (None, "")
            else None
        ),
        rating_labels=rating_label_summary,
        rating_distribution=rating_distribution,
        rating6_count=int(row.get("Rating6Count") or 0),
        rating7_count=int(row.get("Rating7Count") or 0),
        rating8_count=int(row.get("Rating8Count") or 0),
        rating9_count=int(row.get("Rating9Count") or 0),
        rating10_count=int(row.get("Rating10Count") or 0),
    )


def _reporting_option_from_row(row: Mapping[str, Any]) -> SurveyReportingOptionRow:
    return SurveyReportingOptionRow(
        survey_id=int(row["SurveyID"]),
        title=str(row.get("Title") or ""),
        status=str(row.get("Status") or ""),
        result_visibility=normalize_result_visibility(row.get("ResultVisibility")),
        question_id=int(row["SurveyQuestionID"]),
        question_key=str(row.get("QuestionKey") or ""),
        question_prompt=str(row.get("Prompt") or ""),
        question_type=str(row.get("QuestionType") or ""),
        question_sort_order=int(row.get("QuestionSortOrder") or 0),
        is_required=_bool(row.get("IsRequired", 1)),
        option_id=int(row["SurveyOptionID"]),
        option_key=str(row.get("OptionKey") or ""),
        option_label=str(row.get("OptionLabel") or ""),
        option_sort_order=int(row.get("OptionSortOrder") or 0),
        total_responses=int(row.get("TotalResponses") or 0),
        selection_count=int(row.get("SelectionCount") or 0),
        is_top_selection=_bool(row.get("IsTopSelection")),
        ranked_count=int(row.get("RankedCount") or 0),
        average_rank=(
            float(row["AverageRank"]) if row.get("AverageRank") not in (None, "") else None
        ),
        rank1_count=int(row.get("Rank1Count") or 0),
        rank2_count=int(row.get("Rank2Count") or 0),
        rank3_count=int(row.get("Rank3Count") or 0),
        rank4_count=int(row.get("Rank4Count") or 0),
        rank5_count=int(row.get("Rank5Count") or 0),
        rank6_count=int(row.get("Rank6Count") or 0),
    )


def _snapshot_from_rows(
    survey: dict[str, Any],
    question_rows: Sequence[dict[str, Any]],
    option_rows: Sequence[dict[str, Any]],
    rating_rows: Sequence[dict[str, Any]],
    reminder_rows: Sequence[dict[str, Any]],
    rating_label_rows: Sequence[dict[str, Any]] = (),
) -> SurveySnapshot:
    closes_at = _aware_utc(survey.get("ClosesAtUtc"))
    created_at = _aware_utc(survey.get("CreatedAtUtc"))
    updated_at = _aware_utc(survey.get("UpdatedAtUtc"))
    if closes_at is None or created_at is None or updated_at is None:
        raise ValueError("Survey row is missing required UTC timestamps.")
    return SurveySnapshot(
        survey_id=int(survey["SurveyID"]),
        guild_id=int(survey["GuildID"]),
        channel_id=int(survey["ChannelID"]),
        message_id=int(survey["MessageID"]) if survey.get("MessageID") not in (None, "") else None,
        created_by_discord_user_id=int(survey["CreatedByDiscordUserID"]),
        title=str(survey.get("Title") or ""),
        description=survey.get("Description"),
        status=str(survey.get("Status") or ""),
        allow_response_change=_bool(survey.get("AllowResponseChange")),
        launch_mention_everyone=_bool(survey.get("LaunchMentionEveryone")),
        reminder_mention_everyone=_bool(survey.get("ReminderMentionEveryone")),
        close_mention_everyone=_bool(survey.get("CloseMentionEveryone")),
        opens_at_utc=_aware_utc(survey.get("OpensAtUtc")),
        closes_at_utc=closes_at,
        closed_at_utc=_aware_utc(survey.get("ClosedAtUtc")),
        closed_by_discord_user_id=(
            int(survey["ClosedByDiscordUserID"])
            if survey.get("ClosedByDiscordUserID") not in (None, "")
            else None
        ),
        closed_reason=survey.get("ClosedReason"),
        total_responses=int(survey.get("TotalResponses") or 0),
        created_at_utc=created_at,
        updated_at_utc=updated_at,
        questions=_rows_to_questions(question_rows, option_rows, rating_rows, rating_label_rows),
        reminders=_rows_to_reminders(reminder_rows),
        result_visibility=normalize_result_visibility(survey.get("ResultVisibility")),
    )


async def create_survey(req: SurveyCreateRequest) -> int:
    def _callback(cur) -> int | VoteValidationError:
        if any(question.question_type == SURVEY_QUESTION_RANKING for question in req.questions):
            if not _survey_ranking_answers_table_exists_sync(cur):
                logger.warning(
                    "survey_ranking_answers_missing_create migration=%s",
                    SURVEY_RANKING_MIGRATION_ID,
                )
                return VoteValidationError(SURVEY_RANKING_MIGRATION_MESSAGE)
        rating_scale_available = _survey_rating_scale_metadata_exists_sync(cur)
        if not rating_scale_available and any(
            _question_uses_extended_rating_scale(question) for question in req.questions
        ):
            logger.warning(
                "survey_rating_scale_metadata_missing_create migration=%s",
                SURVEY_RATING_SCALE_MIGRATION_ID,
            )
            return VoteValidationError(SURVEY_RATING_SCALE_MIGRATION_MESSAGE)
        now = _naive_utc(datetime.now(UTC))
        cur.execute(
            """
            INSERT INTO dbo.SurveyPosts
                (
                    GuildID, ChannelID, CreatedByDiscordUserID, Title, Description, Status,
                    AllowResponseChange, LaunchMentionEveryone, ReminderMentionEveryone,
                    CloseMentionEveryone, OpensAtUtc, ClosesAtUtc, ResultVisibility,
                    CreatedAtUtc, UpdatedAtUtc
                )
            OUTPUT INSERTED.SurveyID
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                int(req.guild_id),
                int(req.channel_id),
                int(req.created_by_discord_user_id),
                req.title,
                req.description,
                "Open",
                1 if req.allow_response_change else 0,
                1 if req.launch_mention_everyone else 0,
                1 if req.reminder_mention_everyone else 0,
                1 if req.close_mention_everyone else 0,
                _naive_utc(req.opens_at_utc) if req.opens_at_utc else None,
                _naive_utc(req.closes_at_utc),
                normalize_result_visibility(req.result_visibility),
                now,
                now,
            ),
        )
        row = cur.fetchone()
        survey_id = int(row[0]) if row else 0
        for question_index, question in enumerate(req.questions):
            if rating_scale_available:
                cur.execute(
                    """
                    INSERT INTO dbo.SurveyQuestions
                        (
                            SurveyID, QuestionKey, Prompt, QuestionType, SortOrder,
                            IsRequired, MinSelections, MaxSelections, AllowDetails,
                            RatingMinValue, RatingMaxValue, RatingLowLabel, RatingHighLabel,
                            CreatedAtUtc
                        )
                    OUTPUT INSERTED.SurveyQuestionID
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        survey_id,
                        _question_key(question_index),
                        question.prompt,
                        question.question_type,
                        question_index + 1,
                        1 if question.is_required else 0,
                        int(question.min_selections),
                        int(question.max_selections),
                        1 if question.allow_details else 0,
                        int(question.rating_min_value),
                        int(question.rating_max_value),
                        question.rating_low_label,
                        question.rating_high_label,
                        now,
                    ),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO dbo.SurveyQuestions
                        (
                            SurveyID, QuestionKey, Prompt, QuestionType, SortOrder,
                            IsRequired, MinSelections, MaxSelections, AllowDetails, CreatedAtUtc
                        )
                    OUTPUT INSERTED.SurveyQuestionID
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        survey_id,
                        _question_key(question_index),
                        question.prompt,
                        question.question_type,
                        question_index + 1,
                        1 if question.is_required else 0,
                        int(question.min_selections),
                        int(question.max_selections),
                        1 if question.allow_details else 0,
                        now,
                    ),
                )
            question_row = cur.fetchone()
            question_id = int(question_row[0]) if question_row else 0
            if rating_scale_available and question.question_type == SURVEY_QUESTION_RATING:
                for item in question.rating_labels:
                    cur.execute(
                        """
                        INSERT INTO dbo.SurveyRatingChoiceLabels
                            (
                                SurveyID, SurveyQuestionID, RatingValue, Label, CreatedAtUtc,
                                UpdatedAtUtc
                            )
                        VALUES (?, ?, ?, ?, ?, ?);
                        """,
                        (
                            survey_id,
                            question_id,
                            int(item.rating_value),
                            item.label,
                            now,
                            now,
                        ),
                    )
            for option_index, label in enumerate(question.options):
                cur.execute(
                    """
                    INSERT INTO dbo.SurveyQuestionOptions
                        (SurveyQuestionID, OptionKey, Label, SortOrder, CreatedAtUtc)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (question_id, _option_key(option_index), label, option_index + 1, now),
                )
        for offset in req.reminder_offsets_minutes:
            cur.execute(
                """
                INSERT INTO dbo.SurveyReminders
                    (SurveyID, OffsetMinutesBeforeClose, DueAtUtc, CreatedAtUtc)
                VALUES (?, ?, ?, ?);
                """,
                (
                    survey_id,
                    int(offset),
                    _naive_utc(_reminder_due_at(req.closes_at_utc, int(offset))),
                    now,
                ),
            )
        cur.execute(
            """
            INSERT INTO dbo.SurveyAudit
                (SurveyID, ActorDiscordUserID, ActionType, DetailsJson, CreatedAtUtc)
            VALUES (?, ?, 'Created', ?, ?);
            """,
            (
                survey_id,
                int(req.created_by_discord_user_id),
                json.dumps(
                    {
                        "question_count": len(req.questions),
                        "result_visibility": normalize_result_visibility(req.result_visibility),
                    },
                    ensure_ascii=False,
                ),
                now,
            ),
        )
        return survey_id

    survey_id = await run_blocking_in_thread(_create_survey_sync, _callback, name="survey_create")
    if isinstance(survey_id, VoteValidationError):
        raise survey_id
    return int(survey_id or 0)


def _create_survey_sync(callback) -> Any:
    return exec_with_cursor(callback)


async def update_survey_message(survey_id: int, *, channel_id: int, message_id: int) -> bool:
    row = await run_one_async(
        """
        UPDATE dbo.SurveyPosts
        SET ChannelID = ?,
            MessageID = ?,
            UpdatedAtUtc = SYSUTCDATETIME()
        OUTPUT INSERTED.SurveyID
        WHERE SurveyID = ?;
        """,
        (int(channel_id), int(message_id), int(survey_id)),
    )
    return bool(row)


async def get_survey_snapshot(survey_id: int) -> SurveySnapshot | None:
    survey = await run_one_async(
        """
        SELECT p.*,
               (
                   SELECT COUNT_BIG(1)
                   FROM dbo.SurveyResponses r
                   WHERE r.SurveyID = p.SurveyID
               ) AS TotalResponses
        FROM dbo.SurveyPosts p
        WHERE p.SurveyID = ?;
        """,
        (int(survey_id),),
    )
    if not survey:
        return None
    rating_answers_available = await _survey_rating_answers_table_exists()
    rating_scale_available = await _survey_rating_scale_metadata_exists()
    ranking_answers_available = await _survey_ranking_answers_table_exists()
    if not rating_answers_available:
        logger.warning(
            "survey_rating_answers_missing_snapshot survey_id=%s migration=%s",
            survey_id,
            SURVEY_RATING_MIGRATION_ID,
        )
    if not ranking_answers_available:
        logger.warning(
            "survey_ranking_answers_missing_snapshot survey_id=%s migration=%s",
            survey_id,
            SURVEY_RANKING_MIGRATION_ID,
        )
    rating_cte = (
        """,
            RatingAnswered AS (
                SELECT SurveyID, SurveyQuestionID,
                       COUNT_BIG(1) AS AnsweredResponseCount,
                       AVG(CAST(RatingValue AS float)) AS AverageRating,
                       MIN(RatingValue) AS MinimumRating,
                       MAX(RatingValue) AS MaximumRating
                FROM dbo.SurveyRatingAnswers
                WHERE SurveyID = ?
                GROUP BY SurveyID, SurveyQuestionID
            )"""
        if rating_answers_available
        else ""
    )
    ranking_cte = (
        """,
            RankingAnswered AS (
                SELECT SurveyID, SurveyQuestionID,
                       COUNT_BIG(DISTINCT ResponseID) AS AnsweredResponseCount
                FROM dbo.SurveyRankingAnswers
                WHERE SurveyID = ?
                GROUP BY SurveyID, SurveyQuestionID
            )"""
        if ranking_answers_available
        else ""
    )
    rating_join = (
        """
            LEFT JOIN RatingAnswered rating_counts
              ON rating_counts.SurveyID = q.SurveyID
             AND rating_counts.SurveyQuestionID = q.SurveyQuestionID"""
        if rating_answers_available
        else ""
    )
    ranking_join = (
        """
            LEFT JOIN RankingAnswered ranking_counts
              ON ranking_counts.SurveyID = q.SurveyID
             AND ranking_counts.SurveyQuestionID = q.SurveyQuestionID"""
        if ranking_answers_available
        else ""
    )
    rating_answered_expr = (
        "rating_counts.AnsweredResponseCount" if rating_answers_available else "0"
    )
    ranking_answered_expr = (
        "ranking_counts.AnsweredResponseCount" if ranking_answers_available else "0"
    )
    rating_average_expr = (
        "rating_counts.AverageRating" if rating_answers_available else "CAST(NULL AS float)"
    )
    rating_min_expr = (
        "rating_counts.MinimumRating" if rating_answers_available else "CAST(NULL AS tinyint)"
    )
    rating_max_expr = (
        "rating_counts.MaximumRating" if rating_answers_available else "CAST(NULL AS tinyint)"
    )
    rating_min_value_expr = "q.RatingMinValue" if rating_scale_available else "1"
    rating_max_value_expr = "q.RatingMaxValue" if rating_scale_available else "5"
    rating_low_label_expr = (
        "q.RatingLowLabel"
        if rating_scale_available
        else "CAST(NULL AS nvarchar(40))"
    )
    rating_high_label_expr = (
        "q.RatingHighLabel"
        if rating_scale_available
        else "CAST(NULL AS nvarchar(40))"
    )
    question_sql = f"""
            WITH ChoiceAnswered AS (
                SELECT SurveyID, SurveyQuestionID, COUNT_BIG(1) AS AnsweredResponseCount
                FROM (
                    SELECT DISTINCT SurveyID, SurveyQuestionID, DiscordUserID
                    FROM dbo.SurveyAnswers
                    WHERE SurveyID = ?
                ) answered
                GROUP BY SurveyID, SurveyQuestionID
            ),
            TextAnswered AS (
                SELECT SurveyID, SurveyQuestionID, COUNT_BIG(1) AS AnsweredResponseCount
                FROM dbo.SurveyTextAnswers
                WHERE SurveyID = ?
                GROUP BY SurveyID, SurveyQuestionID
            )
            {rating_cte}
            {ranking_cte}
            SELECT q.SurveyQuestionID, q.SurveyID, q.QuestionKey, q.Prompt, q.QuestionType, q.SortOrder,
                   q.IsRequired, q.MinSelections, q.MaxSelections, q.AllowDetails,
                   COALESCE(
                       CASE
                           WHEN q.QuestionType = 'Text' THEN text_counts.AnsweredResponseCount
                           WHEN q.QuestionType = 'Rating' THEN {rating_answered_expr}
                           WHEN q.QuestionType = 'Ranking' THEN {ranking_answered_expr}
                           ELSE choice_counts.AnsweredResponseCount
                       END,
                       0
                   ) AS AnsweredResponseCount,
                   {rating_average_expr} AS AverageRating,
                   {rating_min_expr} AS MinimumRating,
                   {rating_max_expr} AS MaximumRating,
                   {rating_min_value_expr} AS RatingMinValue,
                   {rating_max_value_expr} AS RatingMaxValue,
                   {rating_low_label_expr} AS RatingLowLabel,
                   {rating_high_label_expr} AS RatingHighLabel
            FROM dbo.SurveyQuestions q
            LEFT JOIN ChoiceAnswered choice_counts
              ON choice_counts.SurveyID = q.SurveyID
             AND choice_counts.SurveyQuestionID = q.SurveyQuestionID
            LEFT JOIN TextAnswered text_counts
              ON text_counts.SurveyID = q.SurveyID
             AND text_counts.SurveyQuestionID = q.SurveyQuestionID
            {rating_join}
            {ranking_join}
            WHERE q.SurveyID = ?
            ORDER BY q.SortOrder ASC, q.SurveyQuestionID ASC;
            """
    question_params = [int(survey_id), int(survey_id)]
    if rating_answers_available:
        question_params.append(int(survey_id))
    if ranking_answers_available:
        question_params.append(int(survey_id))
    question_params.append(int(survey_id))
    questions = await run_query_async(question_sql, tuple(question_params))
    option_ranking_cte = (
        """
        WITH RankingOptionStats AS (
            SELECT SurveyQuestionID, SurveyOptionID,
                   SUM(CASE WHEN RankValue = 1 THEN 1 ELSE 0 END) AS FirstPlaceCount,
                   AVG(CAST(RankValue AS float)) AS AverageRank
            FROM dbo.SurveyRankingAnswers
            WHERE SurveyID = ?
            GROUP BY SurveyQuestionID, SurveyOptionID
        ),
        RankingDistribution AS (
            SELECT SurveyQuestionID, SurveyOptionID, RankValue,
                   COUNT_BIG(1) AS RankResponseCount
            FROM dbo.SurveyRankingAnswers
            WHERE SurveyID = ?
            GROUP BY SurveyQuestionID, SurveyOptionID, RankValue
        )
        """
        if ranking_answers_available
        else ""
    )
    option_ranking_select = (
        """,
               COALESCE(ranking_stats.FirstPlaceCount, 0) AS FirstPlaceCount,
               ranking_stats.AverageRank,
               ranking_dist.RankValue,
               ranking_dist.RankResponseCount"""
        if ranking_answers_available
        else """,
               0 AS FirstPlaceCount,
               CAST(NULL AS float) AS AverageRank,
               CAST(NULL AS tinyint) AS RankValue,
               CAST(NULL AS bigint) AS RankResponseCount"""
    )
    option_ranking_join = (
        """
        LEFT JOIN RankingOptionStats ranking_stats
          ON ranking_stats.SurveyQuestionID = o.SurveyQuestionID
         AND ranking_stats.SurveyOptionID = o.SurveyOptionID
        LEFT JOIN RankingDistribution ranking_dist
          ON ranking_dist.SurveyQuestionID = o.SurveyQuestionID
         AND ranking_dist.SurveyOptionID = o.SurveyOptionID"""
        if ranking_answers_available
        else ""
    )
    options = await run_query_async(
        f"""
        {option_ranking_cte}
        SELECT o.SurveyOptionID, o.SurveyQuestionID, o.OptionKey, o.Label, o.SortOrder,
               COUNT(a.DiscordUserID) AS ResponseCount
               {option_ranking_select}
        FROM dbo.SurveyQuestionOptions o
        JOIN dbo.SurveyQuestions q ON q.SurveyQuestionID = o.SurveyQuestionID
        LEFT JOIN dbo.SurveyAnswers a
          ON a.SurveyQuestionID = o.SurveyQuestionID
         AND a.SurveyOptionID = o.SurveyOptionID
        {option_ranking_join}
        WHERE q.SurveyID = ?
        GROUP BY o.SurveyOptionID, o.SurveyQuestionID, o.OptionKey, o.Label, o.SortOrder
                 {', ranking_stats.FirstPlaceCount, ranking_stats.AverageRank, ranking_dist.RankValue, ranking_dist.RankResponseCount' if ranking_answers_available else ''}
        ORDER BY o.SurveyQuestionID ASC, o.SortOrder ASC, o.SurveyOptionID ASC;
        """,
        (
            (int(survey_id), int(survey_id), int(survey_id))
            if ranking_answers_available
            else (int(survey_id),)
        ),
    )
    ratings = (
        await run_query_async(
            """
            SELECT SurveyQuestionID, RatingValue, COUNT_BIG(1) AS ResponseCount
            FROM dbo.SurveyRatingAnswers
            WHERE SurveyID = ?
            GROUP BY SurveyQuestionID, RatingValue
            ORDER BY SurveyQuestionID ASC, RatingValue ASC;
            """,
            (int(survey_id),),
        )
        if rating_answers_available
        else []
    )
    rating_labels = (
        await run_query_async(
            """
            SELECT SurveyQuestionID, RatingValue, Label
            FROM dbo.SurveyRatingChoiceLabels
            WHERE SurveyID = ?
            ORDER BY SurveyQuestionID ASC, RatingValue ASC;
            """,
            (int(survey_id),),
        )
        if rating_scale_available
        else []
    )
    reminders = await run_query_async(
        """
        SELECT ReminderID, SurveyID, OffsetMinutesBeforeClose, DueAtUtc, SentAtUtc, MessageID
        FROM dbo.SurveyReminders
        WHERE SurveyID = ?
        ORDER BY DueAtUtc ASC, ReminderID ASC;
        """,
        (int(survey_id),),
    )
    return _snapshot_from_rows(survey, questions, options, ratings, reminders, rating_labels)


async def list_open_surveys() -> list[SurveySnapshot]:
    rows = await run_query_async("""
        SELECT p.*,
               (SELECT COUNT_BIG(1) FROM dbo.SurveyResponses r WHERE r.SurveyID = p.SurveyID) AS TotalResponses
        FROM dbo.SurveyPosts p
        WHERE p.Status = 'Open'
          AND p.MessageID IS NOT NULL
        ORDER BY p.ClosesAtUtc ASC, p.SurveyID ASC;
        """)
    snapshots: list[SurveySnapshot] = []
    for row in rows:
        snapshot = await get_survey_snapshot(int(row["SurveyID"]))
        if snapshot is not None:
            snapshots.append(snapshot)
    return snapshots


async def search_surveys(query: str | None = None, *, limit: int = 25) -> list[SurveyLookupChoice]:
    text = f"%{(query or '').strip()}%"
    rows = await run_query_async(
        """
        SELECT TOP (?) SurveyID, Title, Status, ChannelID, ClosesAtUtc, ClosedAtUtc
        FROM dbo.SurveyPosts
        WHERE Status = 'Open'
          AND (? = '%%' OR Title LIKE ? OR CONVERT(varchar(30), SurveyID) LIKE ?)
        ORDER BY ClosesAtUtc ASC, SurveyID ASC;
        """,
        (int(limit), text, text, text),
    )
    return [_lookup_from_row(row) for row in rows]


async def search_closed_surveys(
    query: str | None = None, *, limit: int = 25
) -> list[SurveyLookupChoice]:
    text = f"%{(query or '').strip()}%"
    rows = await run_query_async(
        """
        SELECT TOP (?) SurveyID, Title, Status, ChannelID, ClosesAtUtc, ClosedAtUtc
        FROM dbo.SurveyPosts
        WHERE Status = 'Closed'
          AND (? = '%%' OR Title LIKE ? OR CONVERT(varchar(30), SurveyID) LIKE ?)
        ORDER BY ClosedAtUtc DESC, SurveyID DESC;
        """,
        (int(limit), text, text, text),
    )
    return [_lookup_from_row(row) for row in rows]


def _lookup_from_row(row: dict[str, Any]) -> SurveyLookupChoice:
    closes_at = _aware_utc(row.get("ClosesAtUtc"))
    if closes_at is None:
        raise ValueError("Survey lookup row is missing ClosesAtUtc.")
    return SurveyLookupChoice(
        survey_id=int(row["SurveyID"]),
        title=str(row.get("Title") or ""),
        status=str(row.get("Status") or ""),
        channel_id=int(row.get("ChannelID") or 0),
        closes_at_utc=closes_at,
        closed_at_utc=_aware_utc(row.get("ClosedAtUtc")),
    )


async def get_existing_answer_option_ids(
    *, survey_id: int, discord_user_id: int
) -> dict[int, tuple[int, ...]]:
    rows = await run_query_async(
        """
        SELECT a.SurveyQuestionID, a.SurveyOptionID
        FROM dbo.SurveyAnswers a
        WHERE a.SurveyID = ?
          AND a.DiscordUserID = ?
        ORDER BY a.SurveyQuestionID ASC, a.SurveyOptionID ASC;
        """,
        (int(survey_id), int(discord_user_id)),
    )
    grouped: dict[int, list[int]] = {}
    for row in rows:
        grouped.setdefault(int(row["SurveyQuestionID"]), []).append(int(row["SurveyOptionID"]))
    return {key: tuple(value) for key, value in grouped.items()}


async def get_existing_response_payload(
    *, survey_id: int, discord_user_id: int
) -> SurveyResponsePayload:
    option_ids = await get_existing_answer_option_ids(
        survey_id=survey_id, discord_user_id=discord_user_id
    )
    text_rows = await run_query_async(
        """
        SELECT SurveyQuestionID, AnswerText
        FROM dbo.SurveyTextAnswers
        WHERE SurveyID = ?
          AND DiscordUserID = ?
        ORDER BY SurveyQuestionID ASC;
        """,
        (int(survey_id), int(discord_user_id)),
    )
    detail_rows = await run_query_async(
        """
        SELECT SurveyQuestionID, SurveyOptionID, DetailText
        FROM dbo.SurveyAnswerDetails
        WHERE SurveyID = ?
          AND DiscordUserID = ?
        ORDER BY SurveyQuestionID ASC, SurveyOptionID ASC;
        """,
        (int(survey_id), int(discord_user_id)),
    )
    if await _survey_rating_answers_table_exists():
        rating_rows = await run_query_async(
            """
            SELECT SurveyQuestionID, RatingValue
            FROM dbo.SurveyRatingAnswers
            WHERE SurveyID = ?
              AND DiscordUserID = ?
            ORDER BY SurveyQuestionID ASC;
            """,
            (int(survey_id), int(discord_user_id)),
        )
    else:
        logger.warning(
            "survey_rating_answers_missing_prefill survey_id=%s discord_user_id=%s migration=%s",
            survey_id,
            discord_user_id,
            SURVEY_RATING_MIGRATION_ID,
        )
        rating_rows = []
    if await _survey_ranking_answers_table_exists():
        ranking_rows = await run_query_async(
            """
            SELECT SurveyQuestionID, SurveyOptionID, RankValue
            FROM dbo.SurveyRankingAnswers
            WHERE SurveyID = ?
              AND DiscordUserID = ?
            ORDER BY SurveyQuestionID ASC, RankValue ASC;
            """,
            (int(survey_id), int(discord_user_id)),
        )
    else:
        logger.warning(
            "survey_ranking_answers_missing_prefill survey_id=%s discord_user_id=%s migration=%s",
            survey_id,
            discord_user_id,
            SURVEY_RANKING_MIGRATION_ID,
        )
        ranking_rows = []
    ranking_answers: dict[int, list[tuple[int, int]]] = {}
    for row in ranking_rows:
        ranking_answers.setdefault(int(row["SurveyQuestionID"]), []).append(
            (int(row["RankValue"]), int(row["SurveyOptionID"]))
        )
    return SurveyResponsePayload(
        selected_option_ids=option_ids,
        text_answers={
            int(row["SurveyQuestionID"]): str(row.get("AnswerText") or "") for row in text_rows
        },
        detail_text_by_option={
            (int(row["SurveyQuestionID"]), int(row["SurveyOptionID"])): str(
                row.get("DetailText") or ""
            )
            for row in detail_rows
        },
        rating_answers={
            int(row["SurveyQuestionID"]): int(row["RatingValue"]) for row in rating_rows
        },
        ranking_answers={
            question_id: tuple(option_id for _rank, option_id in sorted(items))
            for question_id, items in ranking_answers.items()
        },
    )


async def has_submitted_response(*, survey_id: int, discord_user_id: int) -> bool:
    row = await run_one_async(
        """
        SELECT TOP (1) ResponseID
        FROM dbo.SurveyResponses
        WHERE SurveyID = ?
          AND DiscordUserID = ?;
        """,
        (int(survey_id), int(discord_user_id)),
    )
    return bool(row)


async def get_survey_response_draft(
    *, survey_id: int, discord_user_id: int
) -> SurveyResponseDraft | None:
    if not await _survey_response_drafts_table_exists():
        logger.warning(
            "survey_response_drafts_missing_load survey_id=%s discord_user_id=%s migration=%s",
            survey_id,
            discord_user_id,
            SURVEY_DRAFT_MIGRATION_ID,
        )
        return None
    row = await run_one_async(
        """
        SELECT TOP (1)
               SurveyID, DiscordUserID, DraftPayloadJson, Revision, Status,
               CreatedAtUtc, UpdatedAtUtc, ExpiresAtUtc
        FROM dbo.SurveyResponseDrafts
        WHERE SurveyID = ?
          AND DiscordUserID = ?
          AND Status = 'Active'
          AND (ExpiresAtUtc IS NULL OR ExpiresAtUtc > SYSUTCDATETIME());
        """,
        (int(survey_id), int(discord_user_id)),
    )
    if not row:
        return None
    created_at = _aware_utc(row.get("CreatedAtUtc"))
    updated_at = _aware_utc(row.get("UpdatedAtUtc"))
    if created_at is None or updated_at is None:
        logger.warning(
            "survey_response_draft_missing_timestamps survey_id=%s discord_user_id=%s",
            survey_id,
            discord_user_id,
        )
        return None
    return SurveyResponseDraft(
        survey_id=int(row["SurveyID"]),
        discord_user_id=int(row["DiscordUserID"]),
        payload=_payload_from_json_value(row.get("DraftPayloadJson")),
        revision=int(row.get("Revision") or 0),
        status=str(row.get("Status") or ""),
        created_at_utc=created_at,
        updated_at_utc=updated_at,
        expires_at_utc=_aware_utc(row.get("ExpiresAtUtc")),
    )


async def save_survey_response_draft(
    *,
    survey_id: int,
    discord_user_id: int,
    payload: SurveyResponsePayload,
    expected_revision: int | None,
    now_utc: datetime,
) -> SurveyDraftSaveResult:
    def _callback(cur) -> SurveyDraftSaveResult:
        if not _survey_response_drafts_table_exists_sync(cur):
            logger.warning(
                "survey_response_drafts_missing_save survey_id=%s discord_user_id=%s migration=%s",
                survey_id,
                discord_user_id,
                SURVEY_DRAFT_MIGRATION_ID,
            )
            return SurveyDraftSaveResult(
                "unavailable", int(survey_id), message=SURVEY_DRAFT_MIGRATION_MESSAGE
            )
        now = _naive_utc(now_utc)
        cur.execute(
            """
            SELECT SurveyID, Status, AllowResponseChange, ClosesAtUtc
            FROM dbo.SurveyPosts WITH (UPDLOCK, HOLDLOCK)
            WHERE SurveyID = ?;
            """,
            (int(survey_id),),
        )
        survey = fetch_one_dict(cur)
        if not survey:
            return SurveyDraftSaveResult(
                "missing", int(survey_id), message="This survey no longer exists."
            )
        closes_at = _aware_utc(survey.get("ClosesAtUtc"))
        if str(survey.get("Status")) != "Open" or (closes_at is not None and now_utc >= closes_at):
            return SurveyDraftSaveResult(
                "closed", int(survey_id), message="This survey is already closed."
            )
        cur.execute(
            """
            SELECT TOP (1) ResponseID
            FROM dbo.SurveyResponses WITH (UPDLOCK, HOLDLOCK)
            WHERE SurveyID = ? AND DiscordUserID = ?;
            """,
            (int(survey_id), int(discord_user_id)),
        )
        if cur.fetchone() is not None and not _bool(survey.get("AllowResponseChange")):
            return SurveyDraftSaveResult(
                "change_blocked",
                int(survey_id),
                message="You have already responded and changes are not enabled for this survey.",
            )
        cur.execute(
            """
            DELETE FROM dbo.SurveyResponseDrafts
            WHERE SurveyID = ?
              AND DiscordUserID = ?
              AND Status = 'Active'
              AND ExpiresAtUtc IS NOT NULL
              AND ExpiresAtUtc <= SYSUTCDATETIME();
            """,
            (int(survey_id), int(discord_user_id)),
        )
        cur.execute(
            """
            SELECT Revision
            FROM dbo.SurveyResponseDrafts WITH (UPDLOCK, HOLDLOCK)
            WHERE SurveyID = ?
              AND DiscordUserID = ?
              AND Status = 'Active';
            """,
            (int(survey_id), int(discord_user_id)),
        )
        row = cur.fetchone()
        current_revision = int(row[0]) if row else None
        if expected_revision is not None and int(expected_revision) == 0:
            if current_revision is not None:
                return SurveyDraftSaveResult(
                    "stale",
                    int(survey_id),
                    revision=current_revision,
                    message=(
                        "A newer draft exists. Please continue editing in your newer "
                        "survey panel."
                    ),
                )
        elif expected_revision is not None and current_revision != int(expected_revision):
            return SurveyDraftSaveResult(
                "stale",
                int(survey_id),
                revision=current_revision,
                message=(
                    "A newer draft exists. Please continue editing in your newer survey panel."
                ),
            )
        payload_json = json.dumps(_payload_to_json_dict(payload), ensure_ascii=False)
        if current_revision is None:
            new_revision = 1
            cur.execute(
                """
                INSERT INTO dbo.SurveyResponseDrafts
                    (
                        SurveyID, DiscordUserID, DraftPayloadJson, Revision, Status,
                        CreatedAtUtc, UpdatedAtUtc, ExpiresAtUtc
                    )
                VALUES (?, ?, ?, ?, 'Active', ?, ?, NULL);
                """,
                (
                    int(survey_id),
                    int(discord_user_id),
                    payload_json,
                    new_revision,
                    now,
                    now,
                ),
            )
        else:
            new_revision = current_revision + 1
            cur.execute(
                """
                UPDATE dbo.SurveyResponseDrafts
                SET DraftPayloadJson = ?,
                    Revision = ?,
                    Status = 'Active',
                    UpdatedAtUtc = ?,
                    ExpiresAtUtc = NULL
                WHERE SurveyID = ?
                  AND DiscordUserID = ?
                  AND Status = 'Active';
                """,
                (
                    payload_json,
                    new_revision,
                    now,
                    int(survey_id),
                    int(discord_user_id),
                ),
            )
        return SurveyDraftSaveResult(
            "saved", int(survey_id), revision=new_revision, message="Survey draft saved."
        )

    result = await run_blocking_in_thread(
        _submit_survey_response_sync, _callback, name="survey_draft_save"
    )
    if isinstance(result, SurveyDraftSaveResult):
        return result
    return SurveyDraftSaveResult(
        "error", int(survey_id), message="Survey draft could not be saved."
    )


async def discard_survey_response_draft(
    *, survey_id: int, discord_user_id: int, expected_revision: int | None
) -> SurveyDraftSaveResult:
    def _callback(cur) -> SurveyDraftSaveResult:
        if not _survey_response_drafts_table_exists_sync(cur):
            return SurveyDraftSaveResult(
                "unavailable", int(survey_id), message=SURVEY_DRAFT_MIGRATION_MESSAGE
            )
        cur.execute(
            """
            DELETE FROM dbo.SurveyResponseDrafts
            WHERE SurveyID = ?
              AND DiscordUserID = ?
              AND Status = 'Active'
              AND ExpiresAtUtc IS NOT NULL
              AND ExpiresAtUtc <= SYSUTCDATETIME();
            """,
            (int(survey_id), int(discord_user_id)),
        )
        cur.execute(
            """
            SELECT Revision
            FROM dbo.SurveyResponseDrafts WITH (UPDLOCK, HOLDLOCK)
            WHERE SurveyID = ?
              AND DiscordUserID = ?
              AND Status = 'Active';
            """,
            (int(survey_id), int(discord_user_id)),
        )
        row = cur.fetchone()
        current_revision = int(row[0]) if row else None
        if current_revision is None and expected_revision in (None, 0):
            return SurveyDraftSaveResult(
                "discarded", int(survey_id), message="Survey draft discarded."
            )
        if expected_revision is not None and current_revision != int(expected_revision):
            return SurveyDraftSaveResult(
                "stale",
                int(survey_id),
                revision=current_revision,
                message=(
                    "A newer draft exists. Please continue editing in your newer survey panel."
                ),
            )
        cur.execute(
            """
            DELETE FROM dbo.SurveyResponseDrafts
            WHERE SurveyID = ?
              AND DiscordUserID = ?;
            """,
            (int(survey_id), int(discord_user_id)),
        )
        return SurveyDraftSaveResult("discarded", int(survey_id), message="Survey draft discarded.")

    result = await run_blocking_in_thread(
        _submit_survey_response_sync, _callback, name="survey_draft_discard"
    )
    if isinstance(result, SurveyDraftSaveResult):
        return result
    return SurveyDraftSaveResult(
        "error", int(survey_id), message="Survey draft could not be discarded."
    )


async def submit_survey_response(
    *,
    survey_id: int,
    discord_user_id: int,
    answers_by_question_id: Mapping[int, tuple[int, ...]],
    text_answers_by_question_id: Mapping[int, str] | None = None,
    detail_text_by_question_option: Mapping[tuple[int, int], str] | None = None,
    rating_answers_by_question_id: Mapping[int, int] | None = None,
    ranking_answers_by_question_id: Mapping[int, tuple[int, ...]] | None = None,
    now_utc: datetime,
) -> SurveySubmitResult:
    def _callback(cur) -> SurveySubmitResult | VoteValidationError:
        now = _naive_utc(now_utc)
        cur.execute(
            """
            SELECT SurveyID, Status, AllowResponseChange, ClosesAtUtc
            FROM dbo.SurveyPosts WITH (UPDLOCK, HOLDLOCK)
            WHERE SurveyID = ?;
            """,
            (int(survey_id),),
        )
        survey = fetch_one_dict(cur)
        if not survey:
            return SurveySubmitResult(
                "missing", int(survey_id), message="This survey no longer exists."
            )
        closes_at = _aware_utc(survey.get("ClosesAtUtc"))
        if str(survey.get("Status")) != "Open" or (closes_at is not None and now_utc >= closes_at):
            return SurveySubmitResult(
                "closed", int(survey_id), message="This survey is already closed."
            )

        cur.execute(
            """
            SELECT ResponseID
            FROM dbo.SurveyResponses WITH (UPDLOCK, HOLDLOCK)
            WHERE SurveyID = ? AND DiscordUserID = ?;
            """,
            (int(survey_id), int(discord_user_id)),
        )
        response_row = cur.fetchone()
        existing_response_id = int(response_row[0]) if response_row else None
        if existing_response_id is not None and not _bool(survey.get("AllowResponseChange")):
            return SurveySubmitResult(
                "change_blocked",
                int(survey_id),
                response_id=existing_response_id,
                message="You have already responded and changes are not enabled for this survey.",
            )

        rating_answers_available = _survey_rating_answers_table_exists_sync(cur)
        ranking_answers_available = _survey_ranking_answers_table_exists_sync(cur)
        if not rating_answers_available:
            logger.warning(
                "survey_rating_answers_missing_submit survey_id=%s discord_user_id=%s migration=%s",
                survey_id,
                discord_user_id,
                SURVEY_RATING_MIGRATION_ID,
            )
            if rating_answers_by_question_id:
                return VoteValidationError(SURVEY_RATING_MIGRATION_MESSAGE)
        if not ranking_answers_available:
            logger.warning(
                "survey_ranking_answers_missing_submit survey_id=%s discord_user_id=%s migration=%s",
                survey_id,
                discord_user_id,
                SURVEY_RANKING_MIGRATION_ID,
            )
            if ranking_answers_by_question_id:
                return VoteValidationError(SURVEY_RANKING_MIGRATION_MESSAGE)

        previous_payload = _current_response_payload(
            cur,
            int(survey_id),
            int(discord_user_id),
            rating_answers_available=rating_answers_available,
            ranking_answers_available=ranking_answers_available,
        )
        incoming_payload = SurveyResponsePayload(
            selected_option_ids={
                int(key): tuple(int(item) for item in value)
                for key, value in answers_by_question_id.items()
            },
            text_answers={
                int(key): str(value) for key, value in (text_answers_by_question_id or {}).items()
            },
            detail_text_by_option={
                (int(key[0]), int(key[1])): str(value)
                for key, value in (detail_text_by_question_option or {}).items()
            },
            rating_answers={
                int(key): int(value) for key, value in (rating_answers_by_question_id or {}).items()
            },
            ranking_answers={
                int(key): tuple(int(option_id) for option_id in value)
                for key, value in (ranking_answers_by_question_id or {}).items()
            },
        )
        if existing_response_id is not None and previous_payload == incoming_payload:
            return SurveySubmitResult(
                "unchanged",
                int(survey_id),
                response_id=existing_response_id,
                message="Your survey response was already recorded.",
            )

        if existing_response_id is None:
            cur.execute(
                """
                INSERT INTO dbo.SurveyResponses
                    (SurveyID, DiscordUserID, OriginalAnswersJson, CreatedAtUtc, UpdatedAtUtc)
                OUTPUT INSERTED.ResponseID
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    int(survey_id),
                    int(discord_user_id),
                    json.dumps(_payload_to_json_dict(incoming_payload), ensure_ascii=False),
                    now,
                    now,
                ),
            )
            inserted = cur.fetchone()
            response_id = int(inserted[0]) if inserted else 0
            action = "ResponseRecorded"
            status = "recorded"
            message = "Survey response recorded."
        else:
            response_id = existing_response_id
            cur.execute(
                """
                UPDATE dbo.SurveyResponses
                SET UpdatedAtUtc = ?
                WHERE SurveyID = ? AND DiscordUserID = ?;
                """,
                (now, int(survey_id), int(discord_user_id)),
            )
            action = "ResponseChanged"
            status = "changed"
            message = "Survey response updated."

        cur.execute(
            """
            DELETE FROM dbo.SurveyAnswerDetails
            WHERE SurveyID = ? AND DiscordUserID = ?;
            """,
            (int(survey_id), int(discord_user_id)),
        )
        cur.execute(
            """
            DELETE FROM dbo.SurveyTextAnswers
            WHERE SurveyID = ? AND DiscordUserID = ?;
            """,
            (int(survey_id), int(discord_user_id)),
        )
        if rating_answers_available:
            cur.execute(
                """
                DELETE FROM dbo.SurveyRatingAnswers
                WHERE SurveyID = ? AND DiscordUserID = ?;
                """,
                (int(survey_id), int(discord_user_id)),
            )
        if ranking_answers_available:
            cur.execute(
                """
                DELETE FROM dbo.SurveyRankingAnswers
                WHERE SurveyID = ? AND DiscordUserID = ?;
                """,
                (int(survey_id), int(discord_user_id)),
            )
        cur.execute(
            """
            DELETE FROM dbo.SurveyAnswers
            WHERE SurveyID = ? AND DiscordUserID = ?;
            """,
            (int(survey_id), int(discord_user_id)),
        )
        for question_id, option_ids in incoming_payload.selected_option_ids.items():
            for option_id in option_ids:
                cur.execute(
                    """
                    INSERT INTO dbo.SurveyAnswers
                        (
                            SurveyID, ResponseID, DiscordUserID, SurveyQuestionID,
                            SurveyOptionID, CreatedAtUtc
                        )
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (
                        int(survey_id),
                        response_id,
                        int(discord_user_id),
                        int(question_id),
                        int(option_id),
                        now,
                    ),
                )
        for question_id, text in incoming_payload.text_answers.items():
            cur.execute(
                """
                INSERT INTO dbo.SurveyTextAnswers
                    (
                        SurveyID, ResponseID, DiscordUserID, SurveyQuestionID,
                        AnswerText, CreatedAtUtc, UpdatedAtUtc
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    int(survey_id),
                    response_id,
                    int(discord_user_id),
                    int(question_id),
                    text,
                    now,
                    now,
                ),
            )
        for (question_id, option_id), text in incoming_payload.detail_text_by_option.items():
            cur.execute(
                """
                INSERT INTO dbo.SurveyAnswerDetails
                    (
                        SurveyID, ResponseID, DiscordUserID, SurveyQuestionID,
                        SurveyOptionID, DetailText, CreatedAtUtc, UpdatedAtUtc
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    int(survey_id),
                    response_id,
                    int(discord_user_id),
                    int(question_id),
                    int(option_id),
                    text,
                    now,
                    now,
                ),
            )
        if rating_answers_available:
            for question_id, rating_value in incoming_payload.rating_answers.items():
                cur.execute(
                    """
                    INSERT INTO dbo.SurveyRatingAnswers
                        (
                            SurveyID, ResponseID, DiscordUserID, SurveyQuestionID,
                            QuestionType, RatingValue, CreatedAtUtc, UpdatedAtUtc
                        )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        int(survey_id),
                        response_id,
                        int(discord_user_id),
                        int(question_id),
                        SURVEY_QUESTION_RATING,
                        int(rating_value),
                        now,
                        now,
                    ),
                )
        if ranking_answers_available:
            for question_id, ranked_option_ids in incoming_payload.ranking_answers.items():
                for rank_index, option_id in enumerate(ranked_option_ids, start=1):
                    cur.execute(
                        """
                        INSERT INTO dbo.SurveyRankingAnswers
                            (
                                SurveyID, ResponseID, DiscordUserID, SurveyQuestionID,
                                SurveyOptionID, QuestionType, RankValue, CreatedAtUtc, UpdatedAtUtc
                            )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            int(survey_id),
                            response_id,
                            int(discord_user_id),
                            int(question_id),
                            int(option_id),
                            SURVEY_QUESTION_RANKING,
                            int(rank_index),
                            now,
                            now,
                        ),
                    )

        cur.execute(
            """
            INSERT INTO dbo.SurveyAudit
                (SurveyID, ActorDiscordUserID, ActionType, DetailsJson, CreatedAtUtc)
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                int(survey_id),
                int(discord_user_id),
                action,
                json.dumps(
                    {
                        "choice_question_count": len(incoming_payload.selected_option_ids),
                        "text_answer_count": len(incoming_payload.text_answers),
                        "detail_note_count": len(incoming_payload.detail_text_by_option),
                        "rating_answer_count": len(incoming_payload.rating_answers),
                        "ranking_question_count": len(incoming_payload.ranking_answers),
                        "ranking_answer_count": sum(
                            len(value) for value in incoming_payload.ranking_answers.values()
                        ),
                        "previous_choice_question_count": len(previous_payload.selected_option_ids),
                        "previous_text_answer_count": len(previous_payload.text_answers),
                        "previous_detail_note_count": len(previous_payload.detail_text_by_option),
                        "previous_rating_answer_count": len(previous_payload.rating_answers),
                        "previous_ranking_question_count": len(previous_payload.ranking_answers),
                        "previous_ranking_answer_count": sum(
                            len(value) for value in previous_payload.ranking_answers.values()
                        ),
                    },
                    ensure_ascii=False,
                ),
                now,
            ),
        )
        if _survey_response_drafts_table_exists_sync(cur):
            cur.execute(
                """
                DELETE FROM dbo.SurveyResponseDrafts
                WHERE SurveyID = ? AND DiscordUserID = ?;
                """,
                (int(survey_id), int(discord_user_id)),
            )
        return SurveySubmitResult(status, int(survey_id), response_id=response_id, message=message)

    result = await run_blocking_in_thread(
        _submit_survey_response_sync, _callback, name="survey_submit"
    )
    if isinstance(result, SurveySubmitResult):
        return result
    if isinstance(result, VoteValidationError):
        raise result
    return SurveySubmitResult(
        "error", int(survey_id), message="Survey response could not be recorded."
    )


def _payload_to_json_dict(payload: SurveyResponsePayload) -> dict[str, Any]:
    return {
        "choices": {
            str(question_id): list(option_ids)
            for question_id, option_ids in payload.selected_option_ids.items()
        },
        "text": {str(question_id): text for question_id, text in payload.text_answers.items()},
        "ratings": {
            str(question_id): int(rating_value)
            for question_id, rating_value in payload.rating_answers.items()
        },
        "rankings": {
            str(question_id): [int(option_id) for option_id in option_ids]
            for question_id, option_ids in payload.ranking_answers.items()
        },
        "details": {
            str(question_id): {
                str(option_id): text
                for (detail_question_id, option_id), text in payload.detail_text_by_option.items()
                if detail_question_id == question_id
            }
            for question_id in sorted(
                {question_id for question_id, _option_id in payload.detail_text_by_option}
            )
        },
    }


def _payload_from_json_value(value: Any) -> SurveyResponsePayload:
    try:
        parsed = json.loads(str(value or "{}"))
    except (TypeError, json.JSONDecodeError):
        parsed = {}
    if not isinstance(parsed, dict):
        parsed = {}
    choices = parsed.get("choices") if isinstance(parsed.get("choices"), dict) else {}
    text_answers = parsed.get("text") if isinstance(parsed.get("text"), dict) else {}
    ratings = parsed.get("ratings") if isinstance(parsed.get("ratings"), dict) else {}
    rankings = parsed.get("rankings") if isinstance(parsed.get("rankings"), dict) else {}
    details = parsed.get("details") if isinstance(parsed.get("details"), dict) else {}

    selected_output: dict[int, tuple[int, ...]] = {}
    for raw_question_id, raw_option_ids in choices.items():
        if not isinstance(raw_option_ids, list):
            continue
        try:
            question_id = int(raw_question_id)
            option_ids = tuple(int(option_id) for option_id in raw_option_ids)
        except (TypeError, ValueError):
            continue
        selected_output[question_id] = option_ids

    text_output: dict[int, str] = {}
    for raw_question_id, raw_text in text_answers.items():
        try:
            question_id = int(raw_question_id)
        except (TypeError, ValueError):
            continue
        text = str(raw_text or "").strip()
        if text:
            text_output[question_id] = text

    rating_output: dict[int, int] = {}
    for raw_question_id, raw_rating in ratings.items():
        try:
            question_id = int(raw_question_id)
            rating_output[question_id] = int(raw_rating)
        except (TypeError, ValueError):
            continue

    ranking_output: dict[int, tuple[int, ...]] = {}
    for raw_question_id, raw_option_ids in rankings.items():
        if not isinstance(raw_option_ids, list):
            continue
        try:
            question_id = int(raw_question_id)
            ranking_output[question_id] = tuple(int(option_id) for option_id in raw_option_ids)
        except (TypeError, ValueError):
            continue

    detail_output: dict[tuple[int, int], str] = {}
    for raw_question_id, raw_by_option in details.items():
        if not isinstance(raw_by_option, dict):
            continue
        try:
            question_id = int(raw_question_id)
        except (TypeError, ValueError):
            continue
        for raw_option_id, raw_text in raw_by_option.items():
            try:
                option_id = int(raw_option_id)
            except (TypeError, ValueError):
                continue
            text = str(raw_text or "").strip()
            if text:
                detail_output[(question_id, option_id)] = text

    return SurveyResponsePayload(
        selected_option_ids=selected_output,
        text_answers=text_output,
        detail_text_by_option=detail_output,
        rating_answers=rating_output,
        ranking_answers=ranking_output,
    )


def _current_response_payload(
    cur,
    survey_id: int,
    discord_user_id: int,
    *,
    rating_answers_available: bool = True,
    ranking_answers_available: bool = True,
) -> SurveyResponsePayload:
    return SurveyResponsePayload(
        selected_option_ids=_current_answer_ids(cur, survey_id, discord_user_id),
        text_answers=_current_text_answers(cur, survey_id, discord_user_id),
        detail_text_by_option=_current_detail_text(cur, survey_id, discord_user_id),
        rating_answers=(
            _current_rating_answers(cur, survey_id, discord_user_id)
            if rating_answers_available
            else {}
        ),
        ranking_answers=(
            _current_ranking_answers(cur, survey_id, discord_user_id)
            if ranking_answers_available
            else {}
        ),
    )


def _current_answer_ids(cur, survey_id: int, discord_user_id: int) -> dict[int, tuple[int, ...]]:
    cur.execute(
        """
        SELECT SurveyQuestionID, SurveyOptionID
        FROM dbo.SurveyAnswers WITH (UPDLOCK, HOLDLOCK)
        WHERE SurveyID = ? AND DiscordUserID = ?
        ORDER BY SurveyQuestionID ASC, SurveyOptionID ASC;
        """,
        (survey_id, discord_user_id),
    )
    grouped: dict[int, list[int]] = {}
    for row in cur.fetchall():
        grouped.setdefault(int(row[0]), []).append(int(row[1]))
    return {key: tuple(value) for key, value in grouped.items()}


def _current_text_answers(cur, survey_id: int, discord_user_id: int) -> dict[int, str]:
    cur.execute(
        """
        SELECT SurveyQuestionID, AnswerText
        FROM dbo.SurveyTextAnswers WITH (UPDLOCK, HOLDLOCK)
        WHERE SurveyID = ? AND DiscordUserID = ?
        ORDER BY SurveyQuestionID ASC;
        """,
        (survey_id, discord_user_id),
    )
    return {int(row[0]): str(row[1] or "") for row in cur.fetchall()}


def _current_detail_text(cur, survey_id: int, discord_user_id: int) -> dict[tuple[int, int], str]:
    cur.execute(
        """
        SELECT SurveyQuestionID, SurveyOptionID, DetailText
        FROM dbo.SurveyAnswerDetails WITH (UPDLOCK, HOLDLOCK)
        WHERE SurveyID = ? AND DiscordUserID = ?
        ORDER BY SurveyQuestionID ASC, SurveyOptionID ASC;
        """,
        (survey_id, discord_user_id),
    )
    return {(int(row[0]), int(row[1])): str(row[2] or "") for row in cur.fetchall()}


def _current_rating_answers(cur, survey_id: int, discord_user_id: int) -> dict[int, int]:
    cur.execute(
        """
        SELECT SurveyQuestionID, RatingValue
        FROM dbo.SurveyRatingAnswers WITH (UPDLOCK, HOLDLOCK)
        WHERE SurveyID = ? AND DiscordUserID = ?
        ORDER BY SurveyQuestionID ASC;
        """,
        (survey_id, discord_user_id),
    )
    return {int(row[0]): int(row[1]) for row in cur.fetchall()}


def _current_ranking_answers(
    cur, survey_id: int, discord_user_id: int
) -> dict[int, tuple[int, ...]]:
    cur.execute(
        """
        SELECT SurveyQuestionID, SurveyOptionID, RankValue
        FROM dbo.SurveyRankingAnswers WITH (UPDLOCK, HOLDLOCK)
        WHERE SurveyID = ? AND DiscordUserID = ?
        ORDER BY SurveyQuestionID ASC, RankValue ASC;
        """,
        (survey_id, discord_user_id),
    )
    grouped: dict[int, list[tuple[int, int]]] = {}
    for row in cur.fetchall():
        grouped.setdefault(int(row[0]), []).append((int(row[2]), int(row[1])))
    return {
        question_id: tuple(option_id for _rank, option_id in sorted(items))
        for question_id, items in grouped.items()
    }


def _submit_survey_response_sync(callback) -> Any:
    return exec_with_cursor(callback)


async def list_answer_audit_rows(survey_id: int) -> tuple[SurveyAnswerAuditRow, ...]:
    rating_answers_available = await _survey_rating_answers_table_exists()
    rating_scale_available = await _survey_rating_scale_metadata_exists()
    ranking_answers_available = await _survey_ranking_answers_table_exists()
    if not rating_answers_available:
        logger.warning(
            "survey_rating_answers_missing_audit survey_id=%s migration=%s",
            survey_id,
            SURVEY_RATING_MIGRATION_ID,
        )
    if not ranking_answers_available:
        logger.warning(
            "survey_ranking_answers_missing_audit survey_id=%s migration=%s",
            survey_id,
            SURVEY_RANKING_MIGRATION_ID,
        )
    rating_select = (
        "rating.RatingValue" if rating_answers_available else "CAST(NULL AS tinyint) AS RatingValue"
    )
    rating_join = (
        """
            LEFT JOIN dbo.SurveyRatingAnswers rating
              ON rating.SurveyID = r.SurveyID
             AND rating.DiscordUserID = r.DiscordUserID
             AND rating.SurveyQuestionID = q.SurveyQuestionID"""
        if rating_answers_available
        else ""
    )
    ranking_select = (
        """,
                   ranking.SurveyOptionID AS RankingOptionID,
                   ranking_option.OptionKey AS RankingOptionKey,
                   ranking_option.Label AS RankingOptionLabel,
                   ranking.RankValue AS RankingRankValue"""
        if ranking_answers_available
        else """,
                   CAST(NULL AS bigint) AS RankingOptionID,
                   CAST(NULL AS varchar(32)) AS RankingOptionKey,
                   CAST(NULL AS nvarchar(80)) AS RankingOptionLabel,
                   CAST(NULL AS tinyint) AS RankingRankValue"""
    )
    ranking_join = (
        """
            LEFT JOIN dbo.SurveyRankingAnswers ranking
              ON ranking.SurveyID = r.SurveyID
             AND ranking.DiscordUserID = r.DiscordUserID
             AND ranking.SurveyQuestionID = q.SurveyQuestionID
            LEFT JOIN dbo.SurveyQuestionOptions ranking_option
              ON ranking_option.SurveyOptionID = ranking.SurveyOptionID"""
        if ranking_answers_available
        else ""
    )
    rows = await run_query_async(
        f"""
        SELECT r.SurveyID, p.Title, p.ClosedAtUtc, r.ResponseID, r.DiscordUserID,
               r.OriginalAnswersJson, r.CreatedAtUtc AS ResponseCreatedAtUtc,
               r.UpdatedAtUtc AS ResponseUpdatedAtUtc,
               q.SurveyQuestionID, q.QuestionKey, q.Prompt, q.QuestionType, q.IsRequired,
               o.SurveyOptionID, o.OptionKey, o.Label,
               t.AnswerText, d.DetailText, {rating_select}
               {ranking_select}
        FROM dbo.SurveyResponses r
        JOIN dbo.SurveyPosts p ON p.SurveyID = r.SurveyID
        JOIN dbo.SurveyQuestions q ON q.SurveyID = r.SurveyID
        LEFT JOIN dbo.SurveyAnswers a
          ON a.SurveyID = r.SurveyID
         AND a.DiscordUserID = r.DiscordUserID
         AND a.SurveyQuestionID = q.SurveyQuestionID
        LEFT JOIN dbo.SurveyQuestionOptions o ON o.SurveyOptionID = a.SurveyOptionID
        LEFT JOIN dbo.SurveyTextAnswers t
          ON t.SurveyID = r.SurveyID
         AND t.DiscordUserID = r.DiscordUserID
         AND t.SurveyQuestionID = q.SurveyQuestionID
        {rating_join}
        {ranking_join}
        LEFT JOIN dbo.SurveyAnswerDetails d
          ON d.SurveyID = a.SurveyID
         AND d.ResponseID = a.ResponseID
         AND d.DiscordUserID = a.DiscordUserID
         AND d.SurveyQuestionID = a.SurveyQuestionID
         AND d.SurveyOptionID = a.SurveyOptionID
        WHERE r.SurveyID = ?
        ORDER BY r.DiscordUserID ASC, q.SortOrder ASC, RankingRankValue ASC, o.SortOrder ASC;
        """,
        (int(survey_id),),
    )
    rating_labels = (
        await run_query_async(
            """
            SELECT SurveyQuestionID, RatingValue, Label
            FROM dbo.SurveyRatingChoiceLabels
            WHERE SurveyID = ?
            ORDER BY SurveyQuestionID ASC, RatingValue ASC;
            """,
            (int(survey_id),),
        )
        if rating_scale_available
        else []
    )
    return _answer_audit_from_rows(rows, rating_labels)


async def list_reporting_question_rows(
    survey_id: int,
) -> tuple[SurveyReportingQuestionRow, ...]:
    return await list_reporting_question_rows_for_surveys((survey_id,))


async def list_reporting_question_rows_for_surveys(
    survey_ids: Sequence[int],
) -> tuple[SurveyReportingQuestionRow, ...]:
    normalized_ids = tuple(dict.fromkeys(int(survey_id) for survey_id in survey_ids))
    if not normalized_ids:
        return ()
    await _require_survey_reporting_views()
    rating_scale_available = await _survey_rating_scale_metadata_exists()
    placeholders = ", ".join("?" for _ in normalized_ids)
    order_cases = " ".join(
        f"WHEN ? THEN {index}" for index, _survey_id in enumerate(normalized_ids)
    )
    rating_scale_columns = (
        """
               RatingMinValue, RatingMaxValue, RatingLowLabel, RatingHighLabel,
               RatingLabels, RatingDistribution, Rating6Count, Rating7Count,
               Rating8Count, Rating9Count, Rating10Count"""
        if rating_scale_available
        else """
               1 AS RatingMinValue, 5 AS RatingMaxValue,
               CAST(NULL AS nvarchar(40)) AS RatingLowLabel,
               CAST(NULL AS nvarchar(40)) AS RatingHighLabel,
               CAST('' AS nvarchar(max)) AS RatingLabels,
               CAST('' AS nvarchar(max)) AS RatingDistribution,
               0 AS Rating6Count, 0 AS Rating7Count, 0 AS Rating8Count,
               0 AS Rating9Count, 0 AS Rating10Count"""
    )
    rows = await run_query_async(
        f"""
        SELECT SurveyID, Title, Status, ResultVisibility,
               SurveyQuestionID, QuestionKey, Prompt, QuestionType, QuestionSortOrder,
               IsRequired, MinSelections, MaxSelections, AllowDetails, TotalResponses,
               OptionCount, AnsweredResponses, SkippedResponses, ChoiceSelectionCount,
               RankedOptionCount, RankingFirstPlaceCount, AverageRating, MinimumRating,
               MaximumRating, Rating1Count, Rating2Count, Rating3Count, Rating4Count,
               Rating5Count,
               {rating_scale_columns}
        FROM dbo.v_SurveyReportingQuestionSummary
        WHERE SurveyID IN ({placeholders})
        ORDER BY CASE SurveyID {order_cases} ELSE {len(normalized_ids)} END ASC,
                 QuestionSortOrder ASC, SurveyQuestionID ASC;
        """,
        normalized_ids + normalized_ids,
    )
    return tuple(_reporting_question_from_row(row) for row in rows)


async def list_reporting_option_rows(
    survey_id: int,
) -> tuple[SurveyReportingOptionRow, ...]:
    return await list_reporting_option_rows_for_surveys((survey_id,))


async def list_reporting_option_rows_for_surveys(
    survey_ids: Sequence[int],
) -> tuple[SurveyReportingOptionRow, ...]:
    normalized_ids = tuple(dict.fromkeys(int(survey_id) for survey_id in survey_ids))
    if not normalized_ids:
        return ()
    await _require_survey_reporting_views()
    placeholders = ", ".join("?" for _ in normalized_ids)
    order_cases = " ".join(
        f"WHEN ? THEN {index}" for index, _survey_id in enumerate(normalized_ids)
    )
    rows = await run_query_async(
        f"""
        SELECT SurveyID, Title, Status, ResultVisibility, SurveyQuestionID, QuestionKey,
               Prompt, QuestionType, QuestionSortOrder, IsRequired,
               SurveyOptionID, OptionKey, OptionLabel, OptionSortOrder,
               TotalResponses, SelectionCount, IsTopSelection,
               RankedCount, AverageRank, Rank1Count, Rank2Count,
               Rank3Count, Rank4Count, Rank5Count, Rank6Count
        FROM dbo.v_SurveyReportingOptionSummary
        WHERE SurveyID IN ({placeholders})
        ORDER BY CASE SurveyID {order_cases} ELSE {len(normalized_ids)} END ASC,
                 QuestionSortOrder ASC, OptionSortOrder ASC, SurveyOptionID ASC;
        """,
        normalized_ids + normalized_ids,
    )
    return tuple(_reporting_option_from_row(row) for row in rows)


def _answer_rating_label(
    labels_by_question_id: Mapping[int, tuple[SurveyRatingLabel, ...]],
    question_id: int,
    rating_value: int | None,
) -> str | None:
    if rating_value is None:
        return None
    for item in labels_by_question_id.get(question_id, ()):
        if int(item.rating_value) == int(rating_value):
            return item.label
    return None


def _answer_audit_from_rows(
    rows: Sequence[dict[str, Any]],
    rating_label_rows: Sequence[dict[str, Any]] = (),
) -> tuple[SurveyAnswerAuditRow, ...]:
    labels_by_question_id = _rows_to_rating_labels(rating_label_rows)
    grouped: dict[tuple[int, int], dict[str, Any]] = {}
    for row in rows:
        key = (int(row["ResponseID"]), int(row["SurveyQuestionID"]))
        current = grouped.setdefault(
            key,
            {
                "base": row,
                "selected_ids": [],
                "selected_keys": [],
                "selected_labels": [],
                "detail_by_option": {},
                "ranking_items": [],
            },
        )
        if row.get("SurveyOptionID") in (None, ""):
            pass
        else:
            option_id = int(row["SurveyOptionID"])
            current["selected_ids"].append(option_id)
            current["selected_keys"].append(str(row.get("OptionKey") or ""))
            current["selected_labels"].append(str(row.get("Label") or ""))
            if row.get("DetailText") not in (None, ""):
                current["detail_by_option"][option_id] = str(row.get("DetailText") or "")
        if row.get("RankingOptionID") not in (None, ""):
            current["ranking_items"].append(
                {
                    "option_id": int(row["RankingOptionID"]),
                    "option_key": str(row.get("RankingOptionKey") or ""),
                    "option_label": str(row.get("RankingOptionLabel") or ""),
                    "rank_value": int(row["RankingRankValue"]),
                }
            )

    output: list[SurveyAnswerAuditRow] = []
    for (_response_id, question_id), item in grouped.items():
        row = item["base"]
        original_ids = _original_option_ids_for_question(
            row.get("OriginalAnswersJson"), question_id
        )
        original_details = _original_detail_by_option_for_question(
            row.get("OriginalAnswersJson"), question_id
        )
        original_ranking = _original_ranking_for_question(
            row.get("OriginalAnswersJson"), question_id
        )
        current_details = item["detail_by_option"]
        include_empty_details = bool(current_details or original_details)
        created_at = _aware_utc(row.get("ResponseCreatedAtUtc"))
        updated_at = _aware_utc(row.get("ResponseUpdatedAtUtc"))
        if created_at is None or updated_at is None:
            raise ValueError("Survey response row is missing required UTC timestamps.")
        rating_value = (
            int(row["RatingValue"]) if row.get("RatingValue") not in (None, "") else None
        )
        original_rating_value = _original_rating_for_question(
            row.get("OriginalAnswersJson"), question_id
        )
        base_kwargs = dict(
            survey_id=int(row["SurveyID"]),
            title=str(row.get("Title") or ""),
            closed_at_utc=_aware_utc(row.get("ClosedAtUtc")),
            response_id=int(row["ResponseID"]),
            discord_user_id=int(row["DiscordUserID"]),
            response_created_at_utc=created_at,
            response_updated_at_utc=updated_at,
            question_id=question_id,
            question_key=str(row.get("QuestionKey") or ""),
            question_prompt=str(row.get("Prompt") or ""),
            question_type=str(row.get("QuestionType") or ""),
            is_required=_bool(row.get("IsRequired", 1)),
            selected_option_ids=tuple(item["selected_ids"]),
            selected_option_keys=tuple(item["selected_keys"]),
            selected_option_labels=tuple(item["selected_labels"]),
            original_option_ids=original_ids,
            original_option_keys=(),
            original_option_labels=(),
            text_answer=(
                str(row.get("AnswerText")) if row.get("AnswerText") not in (None, "") else None
            ),
            original_text_answer=_original_text_for_question(
                row.get("OriginalAnswersJson"), question_id
            ),
            rating_value=rating_value,
            original_rating_value=original_rating_value,
            rating_label=_answer_rating_label(
                labels_by_question_id,
                question_id,
                rating_value,
            ),
            original_rating_label=_answer_rating_label(
                labels_by_question_id,
                question_id,
                original_rating_value,
            ),
            selected_option_detail_notes=_format_detail_notes(
                item["selected_ids"],
                current_details,
                include_empty=include_empty_details,
            ),
            original_selected_option_detail_notes=_format_detail_notes(
                original_ids,
                original_details,
                include_empty=include_empty_details,
            ),
        )
        if str(row.get("QuestionType") or "") == SURVEY_QUESTION_RANKING:
            original_rank_by_option = {
                option_id: rank_index
                for rank_index, option_id in enumerate(original_ranking, start=1)
            }
            current_option_ids: set[int] = set()
            for ranking_item in sorted(item["ranking_items"], key=lambda item: item["rank_value"]):
                option_id = int(ranking_item["option_id"])
                current_option_ids.add(option_id)
                output.append(
                    SurveyAnswerAuditRow(
                        **base_kwargs,
                        ranking_option_id=option_id,
                        ranking_option_key=str(ranking_item["option_key"]),
                        ranking_option_label=str(ranking_item["option_label"]),
                        ranking_rank_value=int(ranking_item["rank_value"]),
                        original_ranking_rank_value=original_rank_by_option.get(option_id),
                    )
                )
            for option_id, original_rank_value in sorted(
                original_rank_by_option.items(), key=lambda item: item[1]
            ):
                if option_id in current_option_ids:
                    continue
                output.append(
                    SurveyAnswerAuditRow(
                        **base_kwargs,
                        ranking_option_id=option_id,
                        ranking_option_key="",
                        ranking_option_label="",
                        ranking_rank_value=None,
                        original_ranking_rank_value=original_rank_value,
                    )
                )
            if current_option_ids or original_rank_by_option:
                continue
        output.append(SurveyAnswerAuditRow(**base_kwargs))
    return tuple(output)


def _original_option_ids_for_question(value: Any, question_id: int) -> tuple[int, ...]:
    parsed = _parse_original_answers_json(value)
    if isinstance(parsed, dict) and "choices" in parsed:
        raw_ids = parsed.get("choices", {}).get(str(question_id))
    elif isinstance(parsed, dict):
        raw_ids = parsed.get(str(question_id))
    else:
        raw_ids = None
    if not isinstance(raw_ids, list):
        return ()
    output: list[int] = []
    for item in raw_ids:
        try:
            output.append(int(item))
        except (TypeError, ValueError):
            continue
    return tuple(output)


def _original_text_for_question(value: Any, question_id: int) -> str | None:
    parsed = _parse_original_answers_json(value)
    if not isinstance(parsed, dict):
        return None
    raw = parsed.get("text", {}).get(str(question_id))
    text = str(raw or "").strip()
    return text or None


def _original_rating_for_question(value: Any, question_id: int) -> int | None:
    parsed = _parse_original_answers_json(value)
    if not isinstance(parsed, dict):
        return None
    raw = parsed.get("ratings", {}).get(str(question_id))
    try:
        rating = int(raw)
    except (TypeError, ValueError):
        return None
    if rating < 1 or rating > MAX_RATING_VALUE:
        return None
    return rating


def _original_ranking_for_question(value: Any, question_id: int) -> tuple[int, ...]:
    parsed = _parse_original_answers_json(value)
    if not isinstance(parsed, dict):
        return ()
    raw = parsed.get("rankings", {}).get(str(question_id))
    if not isinstance(raw, list):
        return ()
    output: list[int] = []
    for item in raw:
        try:
            output.append(int(item))
        except (TypeError, ValueError):
            continue
    return tuple(output)


def _original_detail_by_option_for_question(value: Any, question_id: int) -> dict[int, str]:
    parsed = _parse_original_answers_json(value)
    if not isinstance(parsed, dict):
        return {}
    raw = parsed.get("details", {}).get(str(question_id))
    if not isinstance(raw, dict):
        return {}
    output: dict[int, str] = {}
    for option_id, text in raw.items():
        clean_text = str(text or "").strip()
        if not clean_text:
            continue
        try:
            output[int(option_id)] = clean_text
        except (TypeError, ValueError):
            continue
    return output


def _format_detail_notes(
    option_ids: Sequence[int],
    detail_by_option: Mapping[int, str],
    *,
    include_empty: bool,
) -> tuple[str, ...]:
    if not include_empty:
        return ()
    output: list[str] = []
    for option_id in option_ids:
        note = str(detail_by_option.get(int(option_id), "") or "").strip()
        output.append(f"{int(option_id)}:{note}")
    return tuple(output)


def _parse_original_answers_json(value: Any) -> Any:
    if value in (None, ""):
        return None
    try:
        return json.loads(str(value))
    except (TypeError, ValueError):
        return None


async def claim_due_reminders(now_utc: datetime, *, limit: int = 10) -> list[dict[str, Any]]:
    def _callback(cur) -> list[dict[str, Any]]:
        now = _naive_utc(now_utc)
        cur.execute(
            """
            ;WITH due AS (
                SELECT TOP (?) r.ReminderID
                FROM dbo.SurveyReminders r WITH (UPDLOCK, READPAST)
                JOIN dbo.SurveyPosts p ON p.SurveyID = r.SurveyID
                WHERE p.Status = 'Open'
                  AND p.ClosesAtUtc > ?
                  AND r.SentAtUtc IS NULL
                  AND r.DueAtUtc <= ?
                  AND (r.ClaimedAtUtc IS NULL OR r.ClaimedAtUtc < DATEADD(minute, -30, ?))
                ORDER BY r.DueAtUtc ASC, r.ReminderID ASC
            )
            UPDATE r
            SET ClaimedAtUtc = ?
            OUTPUT INSERTED.ReminderID, INSERTED.SurveyID
            FROM dbo.SurveyReminders r
            JOIN due ON due.ReminderID = r.ReminderID;
            """,
            (int(limit), now, now, now, now),
        )
        return [cursor_row_to_dict(cur, row) for row in cur.fetchall()]

    rows = await run_blocking_in_thread(
        _claim_due_reminders_sync, _callback, name="survey_claim_reminders"
    )
    return list(rows or [])


def _claim_due_reminders_sync(callback) -> Any:
    return exec_with_cursor(callback)


async def mark_reminder_sent(reminder_id: int, *, message_id: int, now_utc: datetime) -> bool:
    row = await run_one_async(
        """
        UPDATE dbo.SurveyReminders
        SET SentAtUtc = ?,
            MessageID = ?
        OUTPUT INSERTED.ReminderID
        WHERE ReminderID = ? AND SentAtUtc IS NULL;
        """,
        (_naive_utc(now_utc), int(message_id), int(reminder_id)),
    )
    return bool(row)


async def list_due_closes(now_utc: datetime, *, limit: int = 10) -> list[int]:
    rows = await run_query_async(
        """
        SELECT TOP (?) SurveyID
        FROM dbo.SurveyPosts
        WHERE Status = 'Open'
          AND ClosesAtUtc <= ?
        ORDER BY ClosesAtUtc ASC, SurveyID ASC;
        """,
        (int(limit), _naive_utc(now_utc)),
    )
    return [int(row["SurveyID"]) for row in rows]


async def close_survey(
    *,
    survey_id: int,
    actor_discord_user_id: int | None,
    reason: str,
    now_utc: datetime,
) -> SurveyCloseResult:
    row = await run_one_async(
        """
        UPDATE dbo.SurveyPosts
        SET Status = 'Closed',
            ClosedAtUtc = ?,
            ClosedByDiscordUserID = ?,
            ClosedReason = ?,
            UpdatedAtUtc = ?
        OUTPUT INSERTED.SurveyID
        WHERE SurveyID = ?
          AND Status = 'Open';
        """,
        (
            _naive_utc(now_utc),
            int(actor_discord_user_id) if actor_discord_user_id is not None else None,
            reason,
            _naive_utc(now_utc),
            int(survey_id),
        ),
    )
    if row:
        await insert_audit(
            survey_id=survey_id,
            actor_discord_user_id=actor_discord_user_id,
            action_type="ClosedEarly" if actor_discord_user_id else "ClosedAutomatically",
            details={"reason": reason},
            now_utc=now_utc,
        )
        return SurveyCloseResult("closed", int(survey_id), "Survey closed.")
    snapshot = await get_survey_snapshot(int(survey_id))
    if snapshot and snapshot.status == "Closed":
        return SurveyCloseResult("already_closed", int(survey_id), "Survey is already closed.")
    return SurveyCloseResult("missing", int(survey_id), "Survey was not found.")


async def cancel_survey_launch_failure(
    *,
    survey_id: int,
    actor_discord_user_id: int | None,
    reason: str,
    now_utc: datetime,
) -> bool:
    row = await run_one_async(
        """
        UPDATE dbo.SurveyPosts
        SET Status = 'Cancelled',
            ClosedAtUtc = ?,
            ClosedByDiscordUserID = ?,
            ClosedReason = ?,
            UpdatedAtUtc = ?
        OUTPUT INSERTED.SurveyID
        WHERE SurveyID = ?
          AND Status = 'Open'
          AND MessageID IS NULL;
        """,
        (
            _naive_utc(now_utc),
            int(actor_discord_user_id) if actor_discord_user_id is not None else None,
            reason,
            _naive_utc(now_utc),
            int(survey_id),
        ),
    )
    if row:
        await insert_audit(
            survey_id=survey_id,
            actor_discord_user_id=actor_discord_user_id,
            action_type="LaunchFailed",
            details={"reason": reason},
            now_utc=now_utc,
        )
    return bool(row)


async def insert_audit(
    *,
    survey_id: int,
    actor_discord_user_id: int | None,
    action_type: str,
    details: dict[str, Any] | None = None,
    now_utc: datetime | None = None,
) -> None:
    await run_one_async(
        """
        INSERT INTO dbo.SurveyAudit
            (SurveyID, ActorDiscordUserID, ActionType, DetailsJson, CreatedAtUtc)
        OUTPUT INSERTED.AuditID
        VALUES (?, ?, ?, ?, ?);
        """,
        (
            int(survey_id),
            int(actor_discord_user_id) if actor_discord_user_id is not None else None,
            action_type,
            json.dumps(details, ensure_ascii=False) if details else None,
            _naive_utc(now_utc or datetime.now(UTC)),
        ),
    )
