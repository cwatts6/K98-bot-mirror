from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
import json
import logging
from typing import Any

from file_utils import cursor_row_to_dict, fetch_one_dict, run_blocking_in_thread
from stats_alerts.db import exec_with_cursor, run_one_async, run_query_async
from voting.result_visibility import normalize_result_visibility
from voting.survey_models import (
    SURVEY_QUESTION_SINGLE_CHOICE,
    SurveyAnswerAuditRow,
    SurveyCloseResult,
    SurveyCreateRequest,
    SurveyLookupChoice,
    SurveyQuestion,
    SurveyQuestionOption,
    SurveyReminder,
    SurveyResponsePayload,
    SurveySnapshot,
    SurveySubmitResult,
)

logger = logging.getLogger(__name__)


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
    grouped: dict[int, list[SurveyQuestionOption]] = {}
    for row in rows:
        question_id = int(row["SurveyQuestionID"])
        grouped.setdefault(question_id, []).append(
            SurveyQuestionOption(
                option_id=int(row["SurveyOptionID"]),
                survey_question_id=question_id,
                option_key=str(row.get("OptionKey") or ""),
                label=str(row.get("Label") or ""),
                sort_order=int(row.get("SortOrder") or 0),
                response_count=int(row.get("ResponseCount") or 0),
            )
        )
    return {key: tuple(value) for key, value in grouped.items()}


def _rows_to_questions(
    question_rows: Sequence[dict[str, Any]],
    option_rows: Sequence[dict[str, Any]],
) -> tuple[SurveyQuestion, ...]:
    options_by_question_id = _rows_to_options(option_rows)
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


def _snapshot_from_rows(
    survey: dict[str, Any],
    question_rows: Sequence[dict[str, Any]],
    option_rows: Sequence[dict[str, Any]],
    reminder_rows: Sequence[dict[str, Any]],
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
        questions=_rows_to_questions(question_rows, option_rows),
        reminders=_rows_to_reminders(reminder_rows),
        result_visibility=normalize_result_visibility(survey.get("ResultVisibility")),
    )


async def create_survey(req: SurveyCreateRequest) -> int:
    def _callback(cur) -> int:
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
                    1,
                    int(question.min_selections),
                    int(question.max_selections),
                    1 if question.allow_details else 0,
                    now,
                ),
            )
            question_row = cur.fetchone()
            question_id = int(question_row[0]) if question_row else 0
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
    questions = await run_query_async(
        """
        SELECT SurveyQuestionID, SurveyID, QuestionKey, Prompt, QuestionType, SortOrder,
               IsRequired, MinSelections, MaxSelections, AllowDetails
        FROM dbo.SurveyQuestions
        WHERE SurveyID = ?
        ORDER BY SortOrder ASC, SurveyQuestionID ASC;
        """,
        (int(survey_id),),
    )
    options = await run_query_async(
        """
        SELECT o.SurveyOptionID, o.SurveyQuestionID, o.OptionKey, o.Label, o.SortOrder,
               COUNT(a.DiscordUserID) AS ResponseCount
        FROM dbo.SurveyQuestionOptions o
        JOIN dbo.SurveyQuestions q ON q.SurveyQuestionID = o.SurveyQuestionID
        LEFT JOIN dbo.SurveyAnswers a
          ON a.SurveyQuestionID = o.SurveyQuestionID
         AND a.SurveyOptionID = o.SurveyOptionID
        WHERE q.SurveyID = ?
        GROUP BY o.SurveyOptionID, o.SurveyQuestionID, o.OptionKey, o.Label, o.SortOrder
        ORDER BY o.SurveyQuestionID ASC, o.SortOrder ASC, o.SurveyOptionID ASC;
        """,
        (int(survey_id),),
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
    return _snapshot_from_rows(survey, questions, options, reminders)


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
    )


async def submit_survey_response(
    *,
    survey_id: int,
    discord_user_id: int,
    answers_by_question_id: Mapping[int, tuple[int, ...]],
    text_answers_by_question_id: Mapping[int, str] | None = None,
    detail_text_by_question_option: Mapping[tuple[int, int], str] | None = None,
    now_utc: datetime,
) -> SurveySubmitResult:
    def _callback(cur) -> SurveySubmitResult:
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

        previous_payload = _current_response_payload(cur, int(survey_id), int(discord_user_id))
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
                        "previous_choice_question_count": len(previous_payload.selected_option_ids),
                        "previous_text_answer_count": len(previous_payload.text_answers),
                        "previous_detail_note_count": len(previous_payload.detail_text_by_option),
                    },
                    ensure_ascii=False,
                ),
                now,
            ),
        )
        return SurveySubmitResult(status, int(survey_id), response_id=response_id, message=message)

    result = await run_blocking_in_thread(
        _submit_survey_response_sync, _callback, name="survey_submit"
    )
    if isinstance(result, SurveySubmitResult):
        return result
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


def _current_response_payload(cur, survey_id: int, discord_user_id: int) -> SurveyResponsePayload:
    return SurveyResponsePayload(
        selected_option_ids=_current_answer_ids(cur, survey_id, discord_user_id),
        text_answers=_current_text_answers(cur, survey_id, discord_user_id),
        detail_text_by_option=_current_detail_text(cur, survey_id, discord_user_id),
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


def _submit_survey_response_sync(callback) -> Any:
    return exec_with_cursor(callback)


async def list_answer_audit_rows(survey_id: int) -> tuple[SurveyAnswerAuditRow, ...]:
    rows = await run_query_async(
        """
        SELECT r.SurveyID, p.Title, p.ClosedAtUtc, r.ResponseID, r.DiscordUserID,
               r.OriginalAnswersJson, r.CreatedAtUtc AS ResponseCreatedAtUtc,
               r.UpdatedAtUtc AS ResponseUpdatedAtUtc,
               q.SurveyQuestionID, q.QuestionKey, q.Prompt, q.QuestionType,
               o.SurveyOptionID, o.OptionKey, o.Label,
               t.AnswerText, d.DetailText
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
        LEFT JOIN dbo.SurveyAnswerDetails d
          ON d.SurveyID = a.SurveyID
         AND d.ResponseID = a.ResponseID
         AND d.DiscordUserID = a.DiscordUserID
         AND d.SurveyQuestionID = a.SurveyQuestionID
         AND d.SurveyOptionID = a.SurveyOptionID
        WHERE r.SurveyID = ?
        ORDER BY r.DiscordUserID ASC, q.SortOrder ASC, o.SortOrder ASC;
        """,
        (int(survey_id),),
    )
    return _answer_audit_from_rows(rows)


def _answer_audit_from_rows(rows: Sequence[dict[str, Any]]) -> tuple[SurveyAnswerAuditRow, ...]:
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
            },
        )
        if row.get("SurveyOptionID") in (None, ""):
            continue
        option_id = int(row["SurveyOptionID"])
        current["selected_ids"].append(option_id)
        current["selected_keys"].append(str(row.get("OptionKey") or ""))
        current["selected_labels"].append(str(row.get("Label") or ""))
        if row.get("DetailText") not in (None, ""):
            current["detail_by_option"][option_id] = str(row.get("DetailText") or "")

    output: list[SurveyAnswerAuditRow] = []
    for (_response_id, question_id), item in grouped.items():
        row = item["base"]
        original_ids = _original_option_ids_for_question(
            row.get("OriginalAnswersJson"), question_id
        )
        original_details = _original_detail_by_option_for_question(
            row.get("OriginalAnswersJson"), question_id
        )
        current_details = item["detail_by_option"]
        include_empty_details = bool(current_details or original_details)
        created_at = _aware_utc(row.get("ResponseCreatedAtUtc"))
        updated_at = _aware_utc(row.get("ResponseUpdatedAtUtc"))
        if created_at is None or updated_at is None:
            raise ValueError("Survey response row is missing required UTC timestamps.")
        output.append(
            SurveyAnswerAuditRow(
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
        )
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
