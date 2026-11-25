from __future__ import annotations

import csv
from datetime import UTC, datetime
import io
import re
from typing import Any

from kvk.models.kvk_rankings import RankingPayload, RankingRow

_FORMULA_PREFIXES = ("=", "+", "-", "@")
_FILENAME_SAFE_RE = re.compile(r"[^a-z0-9_]+")

_COMMON_HEADERS = (
    "Rank",
    "GovernorID",
    "GovernorName",
)

_MODE_SUPPORT_HEADERS: dict[str, tuple[str, ...]] = {
    "kvk": (
        "Power",
        "Kills",
        "PercentKillTarget",
        "Deads",
        "DKP",
        "Acclaim",
        "TankingScore",
        "KillPoints",
        "KPLoss",
        "Healed",
    ),
    "honor": (
        "Honor",
        "KVK",
    ),
    "prekvk": (
        "Power",
        "Stage1",
        "Stage2",
        "Stage3",
        "Overall",
    ),
}

_SUPPORT_VALUE_KEYS: dict[str, str] = {
    "PercentKillTarget": "% K/T",
    "TankingScore": "Tanking Score",
    "KillPoints": "Kill Points",
    "KPLoss": "KP Loss",
    "Stage1": "Stage 1",
    "Stage2": "Stage 2",
    "Stage3": "Stage 3",
}


def _generated_at(payload: RankingPayload) -> datetime:
    generated = payload.generated_at_utc
    if generated.tzinfo is None:
        return generated.replace(tzinfo=UTC)
    return generated.astimezone(UTC)


def _timestamp_label(payload: RankingPayload) -> str:
    return _generated_at(payload).strftime("%Y-%m-%dT%H:%M:%SZ")


def _filename_part(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_")
    text = _FILENAME_SAFE_RE.sub("_", text)
    text = text.strip("_")
    return text or "rankings"


def current_rankings_csv_filename(payload: RankingPayload) -> str:
    timestamp = _generated_at(payload).strftime("%Y%m%d_%H%M%S")
    mode = _filename_part(payload.mode)
    metric = _filename_part(payload.metric)
    return f"kvk_rankings_full_list_{mode}_{metric}_{timestamp}.csv"


def _csv_text_cell(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
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


def _support_value(row: RankingRow, header: str) -> Any:
    key = _SUPPORT_VALUE_KEYS.get(header, header)
    return row.supporting_values.get(key)


def current_rankings_csv_headers(payload: RankingPayload) -> tuple[str, ...]:
    return _COMMON_HEADERS + _MODE_SUPPORT_HEADERS.get(payload.mode, ())


def current_rankings_csv_rows(payload: RankingPayload) -> list[dict[str, Any]]:
    headers = current_rankings_csv_headers(payload)
    return [
        _current_rankings_csv_row(
            row,
            headers=headers,
        )
        for row in payload.rows
    ]


def _current_rankings_csv_row(
    row: RankingRow,
    *,
    headers: tuple[str, ...],
) -> dict[str, Any]:
    csv_row: dict[str, Any] = {
        "Rank": row.rank,
        "GovernorID": row.governor_id,
        "GovernorName": row.governor_name,
    }
    for header in headers:
        if header in csv_row:
            continue
        csv_row[header] = _support_value(row, header)
    return csv_row


def build_current_rankings_csv_bytes(payload: RankingPayload) -> io.BytesIO:
    headers = current_rankings_csv_headers(payload)
    text_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(text_buffer, fieldnames=headers, lineterminator="\n")
    writer.writeheader()
    for row in payload.rows:
        csv_row = _current_rankings_csv_row(
            row,
            headers=headers,
        )
        writer.writerow({header: _csv_cell(csv_row.get(header)) for header in headers})
    out = io.BytesIO(text_buffer.getvalue().encode("utf-8-sig"))
    out.seek(0)
    return out
