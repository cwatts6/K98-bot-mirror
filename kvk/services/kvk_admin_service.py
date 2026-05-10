"""Service layer for KVK admin command workflows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import time
from typing import Any

from kvk.dal import kvk_admin_dal

DISCORD_EMBED_FIELD_VALUE_LIMIT = 1024


@dataclass(frozen=True)
class KvkRecomputeResult:
    kvk_no: int
    duration_seconds: float


@dataclass(frozen=True)
class KvkRecentScansResult:
    kvk_no: int
    limit: int
    rows: list[dict[str, Any]]


@dataclass(frozen=True)
class KvkWindowPreviewResult:
    kvk_no: int
    rows: list[dict[str, Any]]
    bad_ranges: list[dict[str, Any]]
    generated_at_utc: datetime


def resolve_kvk_no(kvk_no: int | None = None) -> int:
    return kvk_admin_dal.resolve_kvk_no(kvk_no)


def recompute_kvk_windows(kvk_no: int | None = None) -> KvkRecomputeResult:
    started = time.perf_counter()
    resolved_kvk = kvk_admin_dal.recompute_windows(kvk_no)
    return KvkRecomputeResult(
        kvk_no=resolved_kvk,
        duration_seconds=time.perf_counter() - started,
    )


def list_recent_scans(kvk_no: int | None = None, limit: int = 20) -> KvkRecentScansResult:
    bounded_limit = max(1, min(int(limit), 100))
    resolved_kvk, rows = kvk_admin_dal.fetch_recent_scans(kvk_no, bounded_limit)
    return KvkRecentScansResult(kvk_no=resolved_kvk, limit=bounded_limit, rows=rows)


def load_window_preview(kvk_no: int | None = None) -> KvkWindowPreviewResult:
    resolved_kvk, rows = kvk_admin_dal.fetch_window_preview(kvk_no)
    bad_ranges = [
        row
        for row in rows
        if row.get("StartScanID") is not None
        and row.get("EndScanID") is not None
        and row["EndScanID"] < row["StartScanID"]
    ]
    return KvkWindowPreviewResult(
        kvk_no=resolved_kvk,
        rows=rows,
        bad_ranges=bad_ranges,
        generated_at_utc=datetime.now(UTC),
    )


def format_recent_scans_message(result: KvkRecentScansResult) -> str:
    lines = [
        "```",
        f"{'ScanID':>6}  {'Scan UTC':19}  {'Rows':>6}  {'Imported UTC':19}  Source",
    ]
    for row in result.rows:
        lines.append(
            f"{row.get('ScanID', ''):>6}  "
            f"{str(row.get('ScanTimestampUTC'))[:19]:19}  "
            f"{row.get('Row_Count', ''):>6}  "
            f"{str(row.get('ImportedAtUTC'))[:19]:19}  "
            f"{str(row.get('SourceFileName'))[:50]}"
        )
    lines.append("```")
    return f"**KVK {result.kvk_no} — Recent Scans (Top {result.limit})**\n" + "\n".join(lines)


def format_window_preview_table(result: KvkWindowPreviewResult) -> str:
    header = f"{'Window':20} {'Start':>8} {'End':>8} {'#Scans':>7} {'Rows':>7}"
    lines = [header, "-" * len(header)]
    for row in result.rows:
        name = (row.get("WindowName") or "")[:20]
        start = str(row.get("StartScanID")) if row.get("StartScanID") is not None else "—"
        end = str(row.get("EndScanID")) if row.get("EndScanID") is not None else "open"
        scans = str(row.get("NumScans")) if row.get("NumScans") is not None else "—"
        row_count = str(row.get("RowCount") or 0)
        lines.append(f"{name:20} {start:>8} {end:>8} {scans:>7} {row_count:>7}")

    lines.append("")
    lines.append("Timestamps (UTC):")
    lines.append(f"{'Window':20} {'StartTS':>16} {'EndTS':>16}")
    lines.append("-" * 56)
    for row in result.rows:
        name = (row.get("WindowName") or "")[:20]
        start = _format_timestamp(row.get("StartTS"))
        end = _format_timestamp(row.get("EndTS"))
        lines.append(f"{name:20} {start:>16} {end:>16}")

    return _bounded_code_block(lines, max_chars=DISCORD_EMBED_FIELD_VALUE_LIMIT)


def _format_timestamp(value: Any) -> str:
    try:
        if not value:
            return "—"
        return value.strftime("%d %b %H:%M")
    except Exception:
        return "—"


def _bounded_code_block(lines: list[str], *, max_chars: int) -> str:
    prefix = "```\n"
    suffix = "\n```"
    truncation_line = "... truncated ..."
    overhead = len(prefix) + len(suffix)
    if max_chars < overhead:
        raise ValueError(f"max_chars must be at least {overhead} to fit the code block fences")
    body_limit = max_chars - overhead

    body = "\n".join(lines)
    if len(body) <= body_limit:
        return prefix + body + suffix

    selected: list[str] = []
    for index, line in enumerate(lines):
        has_more = index < len(lines) - 1
        candidate_lines = [*selected, line]
        if has_more:
            candidate_lines.append(truncation_line)
        if len("\n".join(candidate_lines)) > body_limit:
            break
        selected.append(line)

    if not selected:
        selected = [truncation_line[:body_limit]]
    elif len(selected) < len(lines):
        selected.append(truncation_line)

    return prefix + "\n".join(selected) + suffix
