from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
import csv
from dataclasses import dataclass
from datetime import UTC, datetime
import io
import logging
import re
from typing import Any

from voting import survey_dal
from voting.service import VoteValidationError
from voting.survey_models import (
    SurveyAnswerAuditRow,
    SurveySnapshot,
    ranking_count_for_value,
    rating_count_for_value,
)

logger = logging.getLogger(__name__)

CSV_UPLOAD_MAX_BYTES = 8 * 1024 * 1024
_FORMULA_PREFIXES = ("=", "+", "-", "@")
_FILENAME_SAFE_RE = re.compile(r"[^a-z0-9_]+")

SURVEY_TOTALS_COLUMNS = (
    "SurveyID",
    "Title",
    "Description",
    "Status",
    "TotalResponses",
    "ClosedAtUtc",
    "ClosedByDiscordUserID",
    "ClosedReason",
    "CreatedAtUtc",
    "ClosesAtUtc",
    "ChannelID",
    "MessageID",
    "MessageLink",
    "QuestionID",
    "QuestionKey",
    "QuestionPrompt",
    "QuestionType",
    "IsRequired",
    "QuestionSortOrder",
    "MinSelections",
    "MaxSelections",
    "AnsweredResponses",
    "SkippedResponses",
    "OptionID",
    "OptionKey",
    "OptionLabel",
    "OptionSortOrder",
    "SelectionCount",
    "SelectionPercentOfResponses",
    "IsTopSelection",
    "AverageRating",
    "MinimumRating",
    "MaximumRating",
    "Rating1Count",
    "Rating2Count",
    "Rating3Count",
    "Rating4Count",
    "Rating5Count",
    "AverageRank",
    "FirstPlaceCount",
    "Rank1Count",
    "Rank2Count",
    "Rank3Count",
    "Rank4Count",
    "Rank5Count",
    "Rank6Count",
)

SURVEY_RESPONSE_DETAIL_COLUMNS = (
    "SurveyID",
    "Title",
    "ClosedAtUtc",
    "ResponseID",
    "DiscordUserID",
    "DiscordName",
    "QuestionID",
    "QuestionKey",
    "QuestionPrompt",
    "QuestionType",
    "IsRequired",
    "AnswerStatus",
    "SelectedOptionIDs",
    "SelectedOptionKeys",
    "SelectedOptionLabels",
    "OriginalOptionIDs",
    "TextAnswer",
    "OriginalTextAnswer",
    "TextAnswerChanged",
    "RatingValue",
    "OriginalRatingValue",
    "RatingChanged",
    "RankingOptionID",
    "RankingOptionKey",
    "RankingOptionLabel",
    "RankingRankValue",
    "OriginalRankingRankValue",
    "RankingChanged",
    "SelectedOptionDetailNotes",
    "OriginalSelectedOptionDetailNotes",
    "DetailNotesChanged",
    "ResponseCreatedAtUtc",
    "ResponseUpdatedAtUtc",
    "ResponseChanged",
)

DiscordNameResolver = Callable[[tuple[int, ...]], Awaitable[Mapping[int, str]]]


@dataclass(frozen=True)
class SurveyTotalsExport:
    filename: str
    csv_bytes: io.BytesIO
    row_count: int
    snapshot: SurveySnapshot

    @property
    def byte_count(self) -> int:
        return self.csv_bytes.getbuffer().nbytes

    def is_oversized(self, *, max_bytes: int = CSV_UPLOAD_MAX_BYTES) -> bool:
        return self.byte_count > max_bytes


@dataclass(frozen=True)
class SurveyResponseDetailExport:
    filename: str
    csv_bytes: io.BytesIO
    row_count: int
    snapshot: SurveySnapshot

    @property
    def byte_count(self) -> int:
        return self.csv_bytes.getbuffer().nbytes

    def is_oversized(self, *, max_bytes: int = CSV_UPLOAD_MAX_BYTES) -> bool:
        return self.byte_count > max_bytes


def _dt(value: datetime | None) -> str:
    if value is None:
        return ""
    normalized = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    return normalized.strftime("%Y-%m-%dT%H:%M:%SZ")


def _pct(count: int, total: int) -> str:
    if total <= 0:
        return "0%"
    value = (int(count) / int(total)) * 100
    return f"{value:.1f}".rstrip("0").rstrip(".") + "%"


def _csv_text_cell(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    text = " ".join(text.splitlines())
    stripped = text.lstrip()
    if stripped.startswith(_FORMULA_PREFIXES):
        return "'" + text
    return text


def _csv_cell(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (bool, int, float)):
        return value
    return _csv_text_cell(value)


def _spreadsheet_text_id(value: int) -> str:
    return f"'{int(value)}"


def _join_values(values: tuple[Any, ...]) -> str:
    return ";".join(str(value) for value in values)


def _answered_count(snapshot: SurveySnapshot, question) -> int:
    if question.answered_response_count is not None:
        return max(
            0, min(int(question.answered_response_count), int(snapshot.total_responses or 0))
        )
    if question.is_required:
        return int(snapshot.total_responses or 0)
    return 0


def _answer_status(row: SurveyAnswerAuditRow) -> str:
    has_answer = bool(
        row.selected_option_ids
        or (row.text_answer or "").strip()
        or row.rating_value is not None
        or row.ranking_rank_value is not None
    )
    if has_answer:
        return "Answered"
    return "MissingRequired" if row.is_required else "SkippedOptional"


def _filename_part(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_")
    text = _FILENAME_SAFE_RE.sub("_", text)
    text = text.strip("_")
    return text[:60] or "survey"


def _timestamp(snapshot: SurveySnapshot) -> str:
    closed_at = snapshot.closed_at_utc or datetime.now(UTC)
    return (
        closed_at.replace(tzinfo=UTC) if closed_at.tzinfo is None else closed_at.astimezone(UTC)
    ).strftime("%Y%m%d_%H%M%S")


def survey_totals_csv_filename(snapshot: SurveySnapshot) -> str:
    return (
        f"survey_{snapshot.survey_id}_{_filename_part(snapshot.title)}_{_timestamp(snapshot)}.csv"
    )


def survey_response_detail_csv_filename(snapshot: SurveySnapshot) -> str:
    return (
        f"survey_{snapshot.survey_id}_{_filename_part(snapshot.title)}_response_detail_"
        f"{_timestamp(snapshot)}.csv"
    )


def _message_link(snapshot: SurveySnapshot) -> str:
    if snapshot.message_id is None:
        return ""
    host = "https://discord" + ".com/channels"
    return f"{host}/{snapshot.guild_id}/{snapshot.channel_id}/{snapshot.message_id}"


def survey_totals_csv_rows(snapshot: SurveySnapshot) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    total = int(snapshot.total_responses or 0)
    for question in snapshot.questions:
        top_count = max((int(option.response_count or 0) for option in question.options), default=0)
        base_row = {
            "SurveyID": snapshot.survey_id,
            "Title": snapshot.title,
            "Description": snapshot.description,
            "Status": snapshot.status,
            "TotalResponses": total,
            "ClosedAtUtc": _dt(snapshot.closed_at_utc),
            "ClosedByDiscordUserID": snapshot.closed_by_discord_user_id,
            "ClosedReason": snapshot.closed_reason,
            "CreatedAtUtc": _dt(snapshot.created_at_utc),
            "ClosesAtUtc": _dt(snapshot.closes_at_utc),
            "ChannelID": snapshot.channel_id,
            "MessageID": snapshot.message_id,
            "MessageLink": _message_link(snapshot),
            "QuestionID": question.question_id,
            "QuestionKey": question.question_key,
            "QuestionPrompt": question.prompt,
            "QuestionType": question.question_type,
            "IsRequired": 1 if question.is_required else 0,
            "QuestionSortOrder": question.sort_order,
            "MinSelections": question.min_selections,
            "MaxSelections": question.max_selections,
            "AnsweredResponses": _answered_count(snapshot, question),
            "SkippedResponses": max(0, total - _answered_count(snapshot, question)),
            "AverageRating": (
                f"{question.rating_average:.2f}" if question.rating_average is not None else ""
            ),
            "MinimumRating": question.rating_min,
            "MaximumRating": question.rating_max,
            "Rating1Count": rating_count_for_value(question, 1),
            "Rating2Count": rating_count_for_value(question, 2),
            "Rating3Count": rating_count_for_value(question, 3),
            "Rating4Count": rating_count_for_value(question, 4),
            "Rating5Count": rating_count_for_value(question, 5),
            "AverageRank": "",
            "FirstPlaceCount": 0,
            "Rank1Count": 0,
            "Rank2Count": 0,
            "Rank3Count": 0,
            "Rank4Count": 0,
            "Rank5Count": 0,
            "Rank6Count": 0,
        }
        if not question.options:
            answered = _answered_count(snapshot, question)
            rows.append(
                {
                    **base_row,
                    "OptionID": "",
                    "OptionKey": "",
                    "OptionLabel": "",
                    "OptionSortOrder": "",
                    "SelectionCount": answered,
                    "SelectionPercentOfResponses": _pct(answered, total),
                    "IsTopSelection": 0,
                }
            )
            continue
        for option in question.options:
            count = int(option.response_count or 0)
            rows.append(
                {
                    **base_row,
                    "OptionID": option.option_id,
                    "OptionKey": option.option_key,
                    "OptionLabel": option.label,
                    "OptionSortOrder": option.sort_order,
                    "SelectionCount": count,
                    "SelectionPercentOfResponses": _pct(count, total),
                    "IsTopSelection": 1 if top_count > 0 and count == top_count else 0,
                    "AverageRank": (
                        f"{option.ranking_average:.2f}"
                        if option.ranking_average is not None
                        else ""
                    ),
                    "FirstPlaceCount": option.ranking_first_place_count,
                    "Rank1Count": ranking_count_for_value(option, 1),
                    "Rank2Count": ranking_count_for_value(option, 2),
                    "Rank3Count": ranking_count_for_value(option, 3),
                    "Rank4Count": ranking_count_for_value(option, 4),
                    "Rank5Count": ranking_count_for_value(option, 5),
                    "Rank6Count": ranking_count_for_value(option, 6),
                }
            )
    return rows


def _write_csv(rows: list[dict[str, Any]], fieldnames: tuple[str, ...]) -> io.BytesIO:
    text_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(text_buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({header: _csv_cell(row.get(header)) for header in fieldnames})
    out = io.BytesIO(text_buffer.getvalue().encode("utf-8-sig"))
    out.seek(0)
    return out


def build_survey_totals_csv_bytes(snapshot: SurveySnapshot) -> io.BytesIO:
    return _write_csv(survey_totals_csv_rows(snapshot), SURVEY_TOTALS_COLUMNS)


def survey_response_detail_csv_rows(
    rows: tuple[SurveyAnswerAuditRow, ...],
    *,
    discord_names_by_user_id: Mapping[int, str],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        text_changed = (row.original_text_answer or "") != (row.text_answer or "")
        rating_changed = row.original_rating_value != row.rating_value
        ranking_changed = row.original_ranking_rank_value != row.ranking_rank_value
        details_changed = sorted(row.original_selected_option_detail_notes) != sorted(
            row.selected_option_detail_notes
        )
        response_changed = (
            set(row.original_option_ids) != set(row.selected_option_ids)
            or text_changed
            or rating_changed
            or ranking_changed
            or details_changed
        )
        output.append(
            {
                "SurveyID": row.survey_id,
                "Title": row.title,
                "ClosedAtUtc": _dt(row.closed_at_utc),
                "ResponseID": row.response_id,
                "DiscordUserID": _spreadsheet_text_id(row.discord_user_id),
                "DiscordName": discord_names_by_user_id.get(row.discord_user_id) or "Unknown",
                "QuestionID": row.question_id,
                "QuestionKey": row.question_key,
                "QuestionPrompt": row.question_prompt,
                "QuestionType": row.question_type,
                "IsRequired": 1 if row.is_required else 0,
                "AnswerStatus": _answer_status(row),
                "SelectedOptionIDs": _join_values(row.selected_option_ids),
                "SelectedOptionKeys": _join_values(row.selected_option_keys),
                "SelectedOptionLabels": _join_values(row.selected_option_labels),
                "OriginalOptionIDs": _join_values(row.original_option_ids),
                "TextAnswer": row.text_answer or "",
                "OriginalTextAnswer": row.original_text_answer or "",
                "TextAnswerChanged": 1 if text_changed else 0,
                "RatingValue": row.rating_value if row.rating_value is not None else "",
                "OriginalRatingValue": (
                    row.original_rating_value if row.original_rating_value is not None else ""
                ),
                "RatingChanged": 1 if rating_changed else 0,
                "RankingOptionID": (
                    row.ranking_option_id if row.ranking_option_id is not None else ""
                ),
                "RankingOptionKey": row.ranking_option_key or "",
                "RankingOptionLabel": row.ranking_option_label or "",
                "RankingRankValue": (
                    row.ranking_rank_value if row.ranking_rank_value is not None else ""
                ),
                "OriginalRankingRankValue": (
                    row.original_ranking_rank_value
                    if row.original_ranking_rank_value is not None
                    else ""
                ),
                "RankingChanged": 1 if ranking_changed else 0,
                "SelectedOptionDetailNotes": _join_values(row.selected_option_detail_notes),
                "OriginalSelectedOptionDetailNotes": _join_values(
                    row.original_selected_option_detail_notes
                ),
                "DetailNotesChanged": 1 if details_changed else 0,
                "ResponseCreatedAtUtc": _dt(row.response_created_at_utc),
                "ResponseUpdatedAtUtc": _dt(row.response_updated_at_utc),
                "ResponseChanged": 1 if response_changed else 0,
            }
        )
    return output


def build_survey_response_detail_csv_bytes(
    rows: tuple[SurveyAnswerAuditRow, ...],
    *,
    discord_names_by_user_id: Mapping[int, str],
) -> io.BytesIO:
    return _write_csv(
        survey_response_detail_csv_rows(rows, discord_names_by_user_id=discord_names_by_user_id),
        SURVEY_RESPONSE_DETAIL_COLUMNS,
    )


async def build_survey_totals_export(
    *, survey_id: int, requested_by_discord_user_id: int
) -> SurveyTotalsExport:
    snapshot = await survey_dal.get_survey_snapshot(int(survey_id))
    if snapshot is None:
        raise VoteValidationError("Survey not found.")
    if snapshot.status != "Closed":
        raise VoteValidationError("Only closed surveys can be exported.")
    csv_bytes = build_survey_totals_csv_bytes(snapshot)
    row_count = sum(len(question.options) or 1 for question in snapshot.questions)
    export = SurveyTotalsExport(
        filename=survey_totals_csv_filename(snapshot),
        csv_bytes=csv_bytes,
        row_count=row_count,
        snapshot=snapshot,
    )
    logger.info(
        "survey_totals_export_ready survey_id=%s actor_discord_id=%s rows=%s bytes=%s",
        snapshot.survey_id,
        requested_by_discord_user_id,
        export.row_count,
        export.byte_count,
    )
    return export


async def build_survey_response_detail_export(
    *,
    survey_id: int,
    requested_by_discord_user_id: int,
    discord_name_resolver: DiscordNameResolver | None = None,
) -> SurveyResponseDetailExport:
    snapshot = await survey_dal.get_survey_snapshot(int(survey_id))
    if snapshot is None:
        raise VoteValidationError("Survey not found.")
    if snapshot.status != "Closed":
        raise VoteValidationError("Only closed surveys can be exported.")
    rows = await survey_dal.list_answer_audit_rows(int(survey_id))
    voter_ids = tuple(dict.fromkeys(row.discord_user_id for row in rows))
    discord_names: Mapping[int, str] = {}
    if discord_name_resolver is not None and voter_ids:
        discord_names = await discord_name_resolver(voter_ids)
    csv_bytes = build_survey_response_detail_csv_bytes(
        rows,
        discord_names_by_user_id=discord_names,
    )
    export = SurveyResponseDetailExport(
        filename=survey_response_detail_csv_filename(snapshot),
        csv_bytes=csv_bytes,
        row_count=len(rows),
        snapshot=snapshot,
    )
    await survey_dal.insert_audit(
        survey_id=snapshot.survey_id,
        actor_discord_user_id=int(requested_by_discord_user_id),
        action_type="ResponseDetailExported",
        details={
            "mode": "response_detail",
            "row_count": export.row_count,
            "byte_count": export.byte_count,
            "max_upload_bytes": CSV_UPLOAD_MAX_BYTES,
            "is_oversized": export.is_oversized(),
            "delivery_status": (
                "blocked_oversized" if export.is_oversized() else "ready_for_ephemeral_delivery"
            ),
            "columns": list(SURVEY_RESPONSE_DETAIL_COLUMNS),
        },
    )
    logger.info(
        "survey_response_detail_export_ready survey_id=%s actor_discord_id=%s rows=%s bytes=%s",
        snapshot.survey_id,
        requested_by_discord_user_id,
        export.row_count,
        export.byte_count,
    )
    return export
