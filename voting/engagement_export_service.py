from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
import io
import logging
import re
from typing import Any

from voting.reporting_models import EngagementReportingContract

logger = logging.getLogger(__name__)

CSV_UPLOAD_MAX_BYTES = 8 * 1024 * 1024

ENGAGEMENT_EXPORT_COLUMNS = (
    "GeneratedAtUtc",
    "Window",
    "WindowStartUtc",
    "WindowEndUtc",
    "RoleFilter",
    "RoleFilterValue",
    "EligibleUserCount",
    "VotePostCount",
    "SurveyPostCount",
    "DiscordUserID",
    "DiscordDisplayName",
    "RoleNames",
    "EligibleOpportunities",
    "VoteParticipationCount",
    "SurveyParticipationCount",
    "ParticipationCount",
    "MissedCount",
    "EngagementRate",
    "LastParticipationAtUtc",
)

_FILENAME_SAFE_RE = re.compile(r"[^a-z0-9_]+")
_FORMULA_PREFIXES = ("=", "+", "-", "@")


@dataclass(frozen=True)
class EngagementCsvExport:
    filename: str
    csv_bytes: io.BytesIO
    row_count: int
    contract: EngagementReportingContract

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


def _pct(rate: float) -> str:
    value = max(0.0, min(1.0, float(rate))) * 100
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


def _filename_part(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_")
    text = _FILENAME_SAFE_RE.sub("_", text)
    text = text.strip("_")
    return text[:60] or "engagement"


def _engagement_csv_filename(contract: EngagementReportingContract) -> str:
    generated = contract.generated_at_utc.astimezone(UTC).strftime("%Y%m%d_%H%M%S")
    window = _filename_part(contract.window_key)
    role = _filename_part(contract.role_filter_label)
    return f"vote_engagement_{window}_{role}_{generated}.csv"


def engagement_csv_rows(contract: EngagementReportingContract) -> list[dict[str, Any]]:
    sorted_users = sorted(
        contract.user_summaries,
        key=lambda row: (
            -float(row.engagement_rate),
            -int(row.participation_count),
            row.display_name.casefold(),
        ),
    )
    return [
        {
            "GeneratedAtUtc": _dt(contract.generated_at_utc),
            "Window": contract.window_label,
            "WindowStartUtc": _dt(contract.window_start_utc),
            "WindowEndUtc": _dt(contract.window_end_utc),
            "RoleFilter": contract.role_filter_label,
            "RoleFilterValue": contract.role_filter_value,
            "EligibleUserCount": contract.eligible_user_count,
            "VotePostCount": contract.vote_post_count,
            "SurveyPostCount": contract.survey_post_count,
            "DiscordUserID": _spreadsheet_text_id(row.discord_user_id),
            "DiscordDisplayName": row.display_name,
            "RoleNames": ";".join(row.role_names),
            "EligibleOpportunities": row.possible_count,
            "VoteParticipationCount": row.vote_participation_count,
            "SurveyParticipationCount": row.survey_participation_count,
            "ParticipationCount": row.participation_count,
            "MissedCount": max(0, int(row.possible_count) - int(row.participation_count)),
            "EngagementRate": _pct(row.engagement_rate),
            "LastParticipationAtUtc": _dt(row.last_participated_at_utc),
        }
        for row in sorted_users
    ]


def build_engagement_csv_bytes(contract: EngagementReportingContract) -> io.BytesIO:
    text_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        text_buffer,
        fieldnames=ENGAGEMENT_EXPORT_COLUMNS,
        lineterminator="\n",
    )
    writer.writeheader()
    for row in engagement_csv_rows(contract):
        writer.writerow({header: _csv_cell(row.get(header)) for header in ENGAGEMENT_EXPORT_COLUMNS})
    out = io.BytesIO(text_buffer.getvalue().encode("utf-8-sig"))
    out.seek(0)
    return out


def build_engagement_csv_export(
    contract: EngagementReportingContract,
    *,
    requested_by_discord_user_id: int,
) -> EngagementCsvExport:
    csv_bytes = build_engagement_csv_bytes(contract)
    export = EngagementCsvExport(
        filename=_engagement_csv_filename(contract),
        csv_bytes=csv_bytes,
        row_count=len(contract.user_summaries),
        contract=contract,
    )
    logger.info(
        "vote_engagement_export_ready actor_discord_id=%s rows=%s bytes=%s window=%s role_filter=%s",
        requested_by_discord_user_id,
        export.row_count,
        export.byte_count,
        contract.window_key,
        contract.role_filter_value,
    )
    return export

