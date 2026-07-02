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
from voting.survey_models import SurveyAnswerAuditRow, SurveySnapshot

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
    "QuestionSortOrder",
    "MinSelections",
    "MaxSelections",
    "OptionID",
    "OptionKey",
    "OptionLabel",
    "OptionSortOrder",
    "SelectionCount",
    "SelectionPercentOfResponses",
    "IsTopSelection",
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
    "SelectedOptionIDs",
    "SelectedOptionKeys",
    "SelectedOptionLabels",
    "OriginalOptionIDs",
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
    return f"survey_{snapshot.survey_id}_{_filename_part(snapshot.title)}_{_timestamp(snapshot)}.csv"


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
        for option in question.options:
            count = int(option.response_count or 0)
            rows.append(
                {
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
                    "QuestionSortOrder": question.sort_order,
                    "MinSelections": question.min_selections,
                    "MaxSelections": question.max_selections,
                    "OptionID": option.option_id,
                    "OptionKey": option.option_key,
                    "OptionLabel": option.label,
                    "OptionSortOrder": option.sort_order,
                    "SelectionCount": count,
                    "SelectionPercentOfResponses": _pct(count, total),
                    "IsTopSelection": 1 if top_count > 0 and count == top_count else 0,
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
        response_changed = set(row.original_option_ids) != set(row.selected_option_ids)
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
                "SelectedOptionIDs": _join_values(row.selected_option_ids),
                "SelectedOptionKeys": _join_values(row.selected_option_keys),
                "SelectedOptionLabels": _join_values(row.selected_option_labels),
                "OriginalOptionIDs": _join_values(row.original_option_ids),
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
    row_count = sum(len(question.options) for question in snapshot.questions)
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
    voter_ids = tuple(row.discord_user_id for row in rows)
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
