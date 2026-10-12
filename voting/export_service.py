from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
import csv
from dataclasses import dataclass
from datetime import UTC, datetime
import io
import logging
import re
from typing import Any

from voting import dal
from voting.models import VoteSnapshot, VoteVoterAuditRow
from voting.outcomes import vote_outcome
from voting.service import VoteValidationError
from voting.vote_modes import VOTE_MODE_MULTI_SELECT, VOTE_MODE_ONE_CHOICE, normalize_vote_mode

logger = logging.getLogger(__name__)

CSV_UPLOAD_MAX_BYTES = 8 * 1024 * 1024

_FORMULA_PREFIXES = ("=", "+", "-", "@")
_FILENAME_SAFE_RE = re.compile(r"[^a-z0-9_]+")

EXPORT_COLUMNS = (
    "VotePostID",
    "Title",
    "Description",
    "Status",
    "TotalVotes",
    "OutcomeKind",
    "OutcomeSummary",
    "ClosedAtUtc",
    "ClosedByDiscordUserID",
    "ClosedReason",
    "CreatedAtUtc",
    "ClosesAtUtc",
    "ChannelID",
    "MessageID",
    "MessageLink",
    "ReminderOffsetsMinutes",
    "ReminderSentCount",
    "ReminderPendingCount",
    "ReminderMessageIDs",
    "OptionID",
    "OptionKey",
    "OptionLabel",
    "SortOrder",
    "VoteCount",
    "VotePercent",
    "IsWinningOption",
)

MULTI_SELECT_EXPORT_COLUMNS = (
    "VotePostID",
    "Title",
    "Description",
    "Status",
    "VoteMode",
    "MinSelections",
    "MaxSelections",
    "TotalVoters",
    "TotalSelections",
    "OutcomeKind",
    "OutcomeSummary",
    "ClosedAtUtc",
    "ClosedByDiscordUserID",
    "ClosedReason",
    "CreatedAtUtc",
    "ClosesAtUtc",
    "ChannelID",
    "MessageID",
    "MessageLink",
    "ReminderOffsetsMinutes",
    "ReminderSentCount",
    "ReminderPendingCount",
    "ReminderMessageIDs",
    "OptionID",
    "OptionKey",
    "OptionLabel",
    "SortOrder",
    "SelectionCount",
    "SelectionPercentOfVoters",
    "IsTopSelection",
)

VOTER_AUDIT_EXPORT_COLUMNS = (
    "VotePostID",
    "Title",
    "ClosedAtUtc",
    "DiscordUserID",
    "DiscordName",
    "OptionID",
    "OptionKey",
    "OptionLabel",
    "OriginalOptionID",
    "OriginalOptionKey",
    "OriginalOptionLabel",
    "VoteCreatedAtUtc",
    "VoteUpdatedAtUtc",
    "VoteChanged",
)

MULTI_SELECT_VOTER_AUDIT_EXPORT_COLUMNS = (
    "VotePostID",
    "Title",
    "ClosedAtUtc",
    "DiscordUserID",
    "DiscordName",
    "SelectedOptionIDs",
    "SelectedOptionKeys",
    "SelectedOptionLabels",
    "OriginalOptionIDs",
    "OriginalOptionKeys",
    "OriginalOptionLabels",
    "VoteCreatedAtUtc",
    "VoteUpdatedAtUtc",
    "VoteChanged",
)

DiscordNameResolver = Callable[[tuple[int, ...]], Awaitable[Mapping[int, str]]]


@dataclass(frozen=True)
class VoteTotalsExport:
    filename: str
    csv_bytes: io.BytesIO
    row_count: int
    snapshot: VoteSnapshot
    outcome_kind: str
    outcome_summary: str

    @property
    def byte_count(self) -> int:
        return self.csv_bytes.getbuffer().nbytes

    def is_oversized(self, *, max_bytes: int = CSV_UPLOAD_MAX_BYTES) -> bool:
        return self.byte_count > max_bytes


@dataclass(frozen=True)
class VoteVoterAuditExport:
    filename: str
    csv_bytes: io.BytesIO
    row_count: int
    snapshot: VoteSnapshot

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


def _join_values(values: tuple[Any, ...]) -> str:
    return ";".join(str(value) for value in values)


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


def _filename_part(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_")
    text = _FILENAME_SAFE_RE.sub("_", text)
    text = text.strip("_")
    return text[:60] or "vote"


def vote_totals_csv_filename(snapshot: VoteSnapshot) -> str:
    closed_at = snapshot.closed_at_utc or datetime.now(UTC)
    timestamp = (
        closed_at.replace(tzinfo=UTC) if closed_at.tzinfo is None else closed_at.astimezone(UTC)
    ).strftime("%Y%m%d_%H%M%S")
    return f"vote_{snapshot.vote_post_id}_{_filename_part(snapshot.title)}_{timestamp}.csv"


def vote_voter_audit_csv_filename(snapshot: VoteSnapshot) -> str:
    closed_at = snapshot.closed_at_utc or datetime.now(UTC)
    timestamp = (
        closed_at.replace(tzinfo=UTC) if closed_at.tzinfo is None else closed_at.astimezone(UTC)
    ).strftime("%Y%m%d_%H%M%S")
    return (
        f"vote_{snapshot.vote_post_id}_{_filename_part(snapshot.title)}_voter_audit_{timestamp}.csv"
    )


def _message_link(snapshot: VoteSnapshot) -> str:
    if snapshot.message_id is None:
        return ""
    host = "https://discord" + ".com/channels"
    return f"{host}/{snapshot.guild_id}/{snapshot.channel_id}/{snapshot.message_id}"


def vote_totals_csv_rows(snapshot: VoteSnapshot) -> list[dict[str, Any]]:
    outcome = vote_outcome(snapshot)
    sent_reminders = [r for r in snapshot.reminders if r.sent_at_utc is not None]
    pending_reminders = [r for r in snapshot.reminders if r.sent_at_utc is None]
    reminder_offsets = ";".join(str(r.offset_minutes_before_close) for r in snapshot.reminders)
    reminder_message_ids = ";".join(
        str(r.message_id) for r in sent_reminders if r.message_id is not None
    )
    total_votes = int(snapshot.total_votes or 0)

    rows: list[dict[str, Any]] = []
    is_multi_select = normalize_vote_mode(snapshot.vote_mode) == VOTE_MODE_MULTI_SELECT
    for option in snapshot.options:
        vote_count = int(option.vote_count or 0)
        if is_multi_select:
            rows.append(
                {
                    "VotePostID": snapshot.vote_post_id,
                    "Title": snapshot.title,
                    "Description": snapshot.description,
                    "Status": snapshot.status,
                    "VoteMode": VOTE_MODE_MULTI_SELECT,
                    "MinSelections": snapshot.min_selections,
                    "MaxSelections": snapshot.max_selections,
                    "TotalVoters": total_votes,
                    "TotalSelections": int(snapshot.total_selections or 0),
                    "OutcomeKind": outcome.kind,
                    "OutcomeSummary": outcome.summary,
                    "ClosedAtUtc": _dt(snapshot.closed_at_utc),
                    "ClosedByDiscordUserID": snapshot.closed_by_discord_user_id,
                    "ClosedReason": snapshot.closed_reason,
                    "CreatedAtUtc": _dt(snapshot.created_at_utc),
                    "ClosesAtUtc": _dt(snapshot.closes_at_utc),
                    "ChannelID": snapshot.channel_id,
                    "MessageID": snapshot.message_id,
                    "MessageLink": _message_link(snapshot),
                    "ReminderOffsetsMinutes": reminder_offsets,
                    "ReminderSentCount": len(sent_reminders),
                    "ReminderPendingCount": len(pending_reminders),
                    "ReminderMessageIDs": reminder_message_ids,
                    "OptionID": option.option_id,
                    "OptionKey": option.option_key,
                    "OptionLabel": option.label,
                    "SortOrder": option.sort_order,
                    "SelectionCount": vote_count,
                    "SelectionPercentOfVoters": _pct(vote_count, total_votes),
                    "IsTopSelection": (
                        1 if int(option.option_id) in outcome.winning_option_ids else 0
                    ),
                }
            )
            continue
        rows.append(
            {
                "VotePostID": snapshot.vote_post_id,
                "Title": snapshot.title,
                "Description": snapshot.description,
                "Status": snapshot.status,
                "TotalVotes": total_votes,
                "OutcomeKind": outcome.kind,
                "OutcomeSummary": outcome.summary,
                "ClosedAtUtc": _dt(snapshot.closed_at_utc),
                "ClosedByDiscordUserID": snapshot.closed_by_discord_user_id,
                "ClosedReason": snapshot.closed_reason,
                "CreatedAtUtc": _dt(snapshot.created_at_utc),
                "ClosesAtUtc": _dt(snapshot.closes_at_utc),
                "ChannelID": snapshot.channel_id,
                "MessageID": snapshot.message_id,
                "MessageLink": _message_link(snapshot),
                "ReminderOffsetsMinutes": reminder_offsets,
                "ReminderSentCount": len(sent_reminders),
                "ReminderPendingCount": len(pending_reminders),
                "ReminderMessageIDs": reminder_message_ids,
                "OptionID": option.option_id,
                "OptionKey": option.option_key,
                "OptionLabel": option.label,
                "SortOrder": option.sort_order,
                "VoteCount": vote_count,
                "VotePercent": _pct(vote_count, total_votes),
                "IsWinningOption": 1 if int(option.option_id) in outcome.winning_option_ids else 0,
            }
        )
    return rows


def build_vote_totals_csv_bytes(snapshot: VoteSnapshot) -> io.BytesIO:
    rows = vote_totals_csv_rows(snapshot)
    fieldnames = (
        MULTI_SELECT_EXPORT_COLUMNS
        if normalize_vote_mode(snapshot.vote_mode) == VOTE_MODE_MULTI_SELECT
        else EXPORT_COLUMNS
    )
    text_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(text_buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({header: _csv_cell(row.get(header)) for header in fieldnames})
    out = io.BytesIO(text_buffer.getvalue().encode("utf-8-sig"))
    out.seek(0)
    return out


def vote_voter_audit_csv_rows(
    rows: tuple[VoteVoterAuditRow, ...],
    *,
    discord_names_by_user_id: Mapping[int, str],
    vote_mode: str = VOTE_MODE_ONE_CHOICE,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    is_multi_select = normalize_vote_mode(vote_mode) == VOTE_MODE_MULTI_SELECT
    for row in rows:
        if is_multi_select:
            vote_changed = set(row.original_option_ids) != set(row.selected_option_ids)
            output.append(
                {
                    "VotePostID": row.vote_post_id,
                    "Title": row.title,
                    "ClosedAtUtc": _dt(row.closed_at_utc),
                    "DiscordUserID": _spreadsheet_text_id(row.discord_user_id),
                    "DiscordName": discord_names_by_user_id.get(row.discord_user_id) or "Unknown",
                    "SelectedOptionIDs": _join_values(row.selected_option_ids),
                    "SelectedOptionKeys": _join_values(row.selected_option_keys),
                    "SelectedOptionLabels": _join_values(row.selected_option_labels),
                    "OriginalOptionIDs": _join_values(row.original_option_ids),
                    "OriginalOptionKeys": _join_values(row.original_option_keys),
                    "OriginalOptionLabels": _join_values(row.original_option_labels),
                    "VoteCreatedAtUtc": _dt(row.vote_created_at_utc),
                    "VoteUpdatedAtUtc": _dt(row.vote_updated_at_utc),
                    "VoteChanged": 1 if vote_changed else 0,
                }
            )
            continue
        original_option_id = row.original_option_id
        vote_changed = original_option_id is not None and int(original_option_id) != int(
            row.option_id
        )
        output.append(
            {
                "VotePostID": row.vote_post_id,
                "Title": row.title,
                "ClosedAtUtc": _dt(row.closed_at_utc),
                "DiscordUserID": _spreadsheet_text_id(row.discord_user_id),
                "DiscordName": discord_names_by_user_id.get(row.discord_user_id) or "Unknown",
                "OptionID": row.option_id,
                "OptionKey": row.option_key,
                "OptionLabel": row.option_label,
                "OriginalOptionID": original_option_id,
                "OriginalOptionKey": row.original_option_key,
                "OriginalOptionLabel": row.original_option_label,
                "VoteCreatedAtUtc": _dt(row.vote_created_at_utc),
                "VoteUpdatedAtUtc": _dt(row.vote_updated_at_utc),
                "VoteChanged": 1 if vote_changed else 0,
            }
        )
    return output


def build_vote_voter_audit_csv_bytes(
    rows: tuple[VoteVoterAuditRow, ...],
    *,
    discord_names_by_user_id: Mapping[int, str],
    vote_mode: str = VOTE_MODE_ONE_CHOICE,
) -> io.BytesIO:
    csv_rows = vote_voter_audit_csv_rows(
        rows,
        discord_names_by_user_id=discord_names_by_user_id,
        vote_mode=vote_mode,
    )
    fieldnames = (
        MULTI_SELECT_VOTER_AUDIT_EXPORT_COLUMNS
        if normalize_vote_mode(vote_mode) == VOTE_MODE_MULTI_SELECT
        else VOTER_AUDIT_EXPORT_COLUMNS
    )
    text_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        text_buffer,
        fieldnames=fieldnames,
        lineterminator="\n",
    )
    writer.writeheader()
    for row in csv_rows:
        writer.writerow({header: _csv_cell(row.get(header)) for header in fieldnames})
    out = io.BytesIO(text_buffer.getvalue().encode("utf-8-sig"))
    out.seek(0)
    return out


async def build_vote_totals_export(
    *, vote_post_id: int, requested_by_discord_user_id: int
) -> VoteTotalsExport:
    snapshot = await dal.get_vote_snapshot(int(vote_post_id))
    if snapshot is None:
        raise VoteValidationError("Vote not found.")
    if snapshot.status != "Closed":
        raise VoteValidationError("Only closed votes can be exported.")

    outcome = vote_outcome(snapshot)
    csv_bytes = build_vote_totals_csv_bytes(snapshot)
    export = VoteTotalsExport(
        filename=vote_totals_csv_filename(snapshot),
        csv_bytes=csv_bytes,
        row_count=len(snapshot.options),
        snapshot=snapshot,
        outcome_kind=outcome.kind,
        outcome_summary=outcome.summary,
    )
    logger.info(
        "vote_totals_export_ready vote_post_id=%s actor_discord_id=%s rows=%s bytes=%s",
        snapshot.vote_post_id,
        requested_by_discord_user_id,
        export.row_count,
        export.byte_count,
    )
    return export


async def build_vote_voter_audit_export(
    *,
    vote_post_id: int,
    requested_by_discord_user_id: int,
    discord_name_resolver: DiscordNameResolver | None = None,
) -> VoteVoterAuditExport:
    snapshot = await dal.get_vote_snapshot(int(vote_post_id))
    if snapshot is None:
        raise VoteValidationError("Vote not found.")
    if snapshot.status != "Closed":
        raise VoteValidationError("Only closed votes can be exported.")

    rows = await dal.list_vote_voter_audit_rows(int(vote_post_id))
    voter_ids = tuple(row.discord_user_id for row in rows)
    discord_names: Mapping[int, str] = {}
    if discord_name_resolver is not None and voter_ids:
        discord_names = await discord_name_resolver(voter_ids)

    csv_bytes = build_vote_voter_audit_csv_bytes(
        rows,
        discord_names_by_user_id=discord_names,
        vote_mode=snapshot.vote_mode,
    )
    export = VoteVoterAuditExport(
        filename=vote_voter_audit_csv_filename(snapshot),
        csv_bytes=csv_bytes,
        row_count=len(rows),
        snapshot=snapshot,
    )
    await dal.insert_audit(
        vote_post_id=snapshot.vote_post_id,
        actor_discord_user_id=int(requested_by_discord_user_id),
        action_type="VoterAuditExported",
        details={
            "mode": "voter_audit",
            "row_count": export.row_count,
            "byte_count": export.byte_count,
            "max_upload_bytes": CSV_UPLOAD_MAX_BYTES,
            "is_oversized": export.is_oversized(),
            "delivery_status": (
                "blocked_oversized" if export.is_oversized() else "ready_for_ephemeral_delivery"
            ),
            "columns": list(
                MULTI_SELECT_VOTER_AUDIT_EXPORT_COLUMNS
                if normalize_vote_mode(snapshot.vote_mode) == VOTE_MODE_MULTI_SELECT
                else VOTER_AUDIT_EXPORT_COLUMNS
            ),
        },
    )
    logger.info(
        "vote_voter_audit_export_ready vote_post_id=%s actor_discord_id=%s rows=%s bytes=%s",
        snapshot.vote_post_id,
        requested_by_discord_user_id,
        export.row_count,
        export.byte_count,
    )
    return export
