"""Service layer for KVK admin command workflows."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
import logging
import time
from typing import Any

from kvk.dal import kvk_admin_dal

logger = logging.getLogger(__name__)
DISCORD_EMBED_FIELD_VALUE_LIMIT = 1024


@dataclass(frozen=True)
class KvkExportTestSection:
    name: str
    lines: list[str]


@dataclass(frozen=True)
class KvkExportTestResult:
    kvk_no: int
    sheet_name: str
    duration_seconds: float
    meta: dict[str, Any]
    sections: list[KvkExportTestSection]


@dataclass(frozen=True)
class KvkExportAllResult:
    kvk_no: int
    sheet_name: str
    ok: bool


@dataclass(frozen=True)
class KvkCacheBuildOutcome:
    label: str
    count: int | None
    duration_seconds: float
    error: str | None = None
    non_fatal: bool = False


@dataclass(frozen=True)
class KvkCacheRefreshResult:
    main: KvkCacheBuildOutcome
    last_kvk: KvkCacheBuildOutcome


@dataclass(frozen=True)
class KvkEmbedTestContext:
    timestamp_label: str
    is_kvk: bool


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


def normalize_sheet_name(sheet_name: str | None, default_sheet_name: str) -> str:
    return (sheet_name or default_sheet_name).strip() or default_sheet_name


def run_export_test(
    *,
    kvk_no: int | None,
    sheet_name: str,
    server: str,
    database: str,
    username: str,
    password: str,
    credentials_file: str,
    create_primary: bool,
    export_pass4: bool,
    export_altar: bool,
    export_pass7: bool,
    runner: Callable[..., dict[str, Any] | Any],
) -> KvkExportTestResult:
    resolved_kvk = resolve_kvk_no(kvk_no) if not kvk_no else int(kvk_no)
    started = time.perf_counter()
    raw_meta = runner(
        server,
        database,
        username,
        password,
        resolved_kvk,
        sheet_name,
        credentials_file,
        create_primary,
        export_pass4,
        export_altar,
        export_pass7,
    )
    meta = raw_meta if isinstance(raw_meta, dict) else {}
    return KvkExportTestResult(
        kvk_no=resolved_kvk,
        sheet_name=sheet_name,
        duration_seconds=time.perf_counter() - started,
        meta=meta,
        sections=_build_export_test_sections(meta),
    )


def run_export_all(
    *,
    kvk_no: int | None,
    sheet_name: str,
    server: str,
    database: str,
    username: str,
    password: str,
    credentials_file: str,
    alert_channel: Any,
    event_loop: Any,
    runner: Callable[..., bool],
) -> KvkExportAllResult:
    resolved_kvk = resolve_kvk_no(kvk_no) if not kvk_no else int(kvk_no)
    ok = bool(
        runner(
            server,
            database,
            username,
            password,
            resolved_kvk,
            sheet_name,
            credentials_file,
            alert_channel,
            event_loop,
        )
    )
    return KvkExportAllResult(kvk_no=resolved_kvk, sheet_name=sheet_name, ok=ok)


async def refresh_stats_caches(
    *,
    build_player_stats_cache: Callable[[], Awaitable[Any]],
    build_lastkvk_player_stats_cache: Callable[[], Awaitable[Any]],
) -> KvkCacheRefreshResult:
    main = await _run_cache_builder("Player stats cache", build_player_stats_cache)
    last_kvk = await _run_cache_builder(
        "Last-KVK cache",
        build_lastkvk_player_stats_cache,
        non_fatal=True,
    )
    return KvkCacheRefreshResult(main=main, last_kvk=last_kvk)


def format_cache_refresh_message(result: KvkCacheRefreshResult) -> str:
    return " \n".join(
        [
            _format_cache_outcome(result.main),
            _format_cache_outcome(result.last_kvk),
        ]
    )


def load_embed_test_context(
    *,
    is_currently_kvk_checker: Callable[..., bool],
    server: str,
    database: str,
    username: str,
    password: str,
) -> KvkEmbedTestContext:
    return KvkEmbedTestContext(
        timestamp_label=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        is_kvk=bool(is_currently_kvk_checker(server, database, username, password)),
    )


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


async def _run_cache_builder(
    label: str,
    builder: Callable[[], Awaitable[Any]],
    *,
    non_fatal: bool = False,
) -> KvkCacheBuildOutcome:
    started = time.perf_counter()
    try:
        result = await builder()
    except Exception as exc:
        logger.exception("[KVK ADMIN] %s refresh failed", label)
        return KvkCacheBuildOutcome(
            label=label,
            count=None,
            duration_seconds=time.perf_counter() - started,
            error=f"{type(exc).__name__}: {exc}",
            non_fatal=non_fatal,
        )

    return KvkCacheBuildOutcome(
        label=label,
        count=_extract_count(result),
        duration_seconds=time.perf_counter() - started,
        non_fatal=non_fatal,
    )


def _extract_count(result: Any) -> int | None:
    if isinstance(result, int):
        return result
    if isinstance(result, dict):
        count = (result.get("_meta") or {}).get("count") or result.get("count")
        return int(count) if count is not None else None
    return None


def _format_cache_outcome(outcome: KvkCacheBuildOutcome) -> str:
    if outcome.error:
        if outcome.non_fatal:
            return (
                f"Warning: {outcome.label} build failed (non-fatal): `{outcome.error}` - "
                "the main cache is available."
            )
        return f"Failed: {outcome.label} build failed: `{outcome.error}`"

    if outcome.count is not None:
        return (
            f"Success: {outcome.label} refreshed "
            f"({outcome.count} records) in {outcome.duration_seconds:.1f}s"
        )
    return f"Success: {outcome.label} refreshed in {outcome.duration_seconds:.1f}s"


def _build_export_test_sections(meta: dict[str, Any]) -> list[KvkExportTestSection]:
    sections: list[KvkExportTestSection] = []
    primary = meta.get("primary") if isinstance(meta, dict) else None
    if primary:
        lines = _export_meta_lines(primary)
        sections.append(KvkExportTestSection("Primary result", lines or ["No primary metadata"]))

    additional = meta.get("additional") if isinstance(meta, dict) else {}
    if isinstance(additional, dict):
        for ss_name, ss_meta in additional.items():
            if isinstance(ss_meta, dict):
                sections.append(KvkExportTestSection(str(ss_name), _export_meta_lines(ss_meta)))
    return sections


def _export_meta_lines(ss_meta: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    if "created" in ss_meta or "reason" in ss_meta:
        if ss_meta.get("created"):
            lines.append("Created")
        elif ss_meta.get("reason") == "no_data":
            lines.append("Skipped")
        else:
            lines.append("Failed")
    written = ss_meta.get("written_tabs", []) or []
    skipped = ss_meta.get("skipped_tabs", []) or []
    if written:
        lines.append(f"Written: {len(written)}")
    if skipped:
        lines.append(f"Skipped: {len(skipped)}")
    url = ss_meta.get("spreadsheet_url")
    if url:
        lines.append(f"[Open]({url})")
    return lines


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
