from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
import io
import logging
import re
from typing import Any

from voting import dal
from voting.models import VoteSnapshot
from voting.outcomes import vote_outcome
from voting.service import VoteValidationError

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


def _filename_part(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_")
    text = _FILENAME_SAFE_RE.sub("_", text)
    text = text.strip("_")
    return text[:60] or "vote"


def vote_totals_csv_filename(snapshot: VoteSnapshot) -> str:
    closed_at = snapshot.closed_at_utc or datetime.now(UTC)
    timestamp = (
        closed_at.replace(tzinfo=UTC)
        if closed_at.tzinfo is None
        else closed_at.astimezone(UTC)
    ).strftime("%Y%m%d_%H%M%S")
    return f"vote_{snapshot.vote_post_id}_{_filename_part(snapshot.title)}_{timestamp}.csv"


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
    for option in snapshot.options:
        vote_count = int(option.vote_count or 0)
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
                "IsWinningOption": int(option.option_id) in outcome.winning_option_ids,
            }
        )
    return rows


def build_vote_totals_csv_bytes(snapshot: VoteSnapshot) -> io.BytesIO:
    rows = vote_totals_csv_rows(snapshot)
    text_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(text_buffer, fieldnames=EXPORT_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({header: _csv_cell(row.get(header)) for header in EXPORT_COLUMNS})
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
