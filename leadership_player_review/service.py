"""Business rules and orchestration for private leadership player review."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
import logging
import time
import unicodedata
from uuid import UUID

from rapidfuzz import fuzz

import kvk_state
from leadership_player_review import dal
from leadership_player_review.models import (
    ActivityMetric,
    FreshnessState,
    KvkIndex,
    KvkPerformance,
    LastActive,
    LeadershipPlayerPayload,
    LinkedGovernor,
    LoadDiagnostics,
    LookupCandidate,
    LookupResult,
    ReviewPage,
)
from registry import registry_service

logger = logging.getLogger(__name__)

SUPPORTED_PERIODS = (30, 90, 180, 360)
DEFAULT_PERIOD = 90
_DIRECTORY_TTL_SECONDS = 300.0
_PAYLOAD_TTL_SECONDS = 60.0
_FUZZY_CUTOFF = 70.0
_SMALL_COHORT = 5
_MAX_LOOKUP_LENGTH = 100
_MAX_GOVERNOR_ID = 9_223_372_036_854_775_807

_directory_cache: tuple[float, tuple[LookupCandidate, ...]] | None = None
_payload_cache: dict[tuple[int, int], tuple[float, LeadershipPlayerPayload]] = {}
_last_active_cache: dict[tuple[int, date], tuple[float, LastActive]] = {}
_cache_lock = asyncio.Lock()


def normalize_name(value: str | None) -> str:
    """Unicode normalize, trim/collapse whitespace, then full Python casefold."""
    normalized = unicodedata.normalize("NFKC", str(value or ""))
    return " ".join(normalized.split()).casefold()


async def _lookup_directory(*, refresh: bool = False) -> tuple[LookupCandidate, ...]:
    global _directory_cache
    now = time.monotonic()
    async with _cache_lock:
        if not refresh and _directory_cache and _directory_cache[0] > now:
            logger.debug("leadership_player_lookup_performance cache=HIT total_ms=%.3f", 0.0)
            return _directory_cache[1]
    started = time.perf_counter()
    diagnostics: dict[str, object] = {}
    rows = await asyncio.to_thread(
        dal.fetch_lookup_directory,
        history_days=720,
        diagnostics=diagnostics,
    )
    async with _cache_lock:
        _directory_cache = (time.monotonic() + _DIRECTORY_TTL_SECONDS, rows)
    logger.debug(
        "leadership_player_lookup_performance cache=%s total_ms=%.3f "
        "connection_ms=%s sql_fetch_ms=%s mapping_ms=%s rows=%s approximate_bytes=%s",
        "REFRESH" if refresh else "MISS",
        (time.perf_counter() - started) * 1000.0,
        diagnostics.get("connection_ms"),
        diagnostics.get("sql_fetch_ms"),
        diagnostics.get("mapping_ms"),
        diagnostics.get("result_rows"),
        diagnostics.get("approximate_result_bytes"),
    )
    return rows


def _dedupe_candidates(rows: list[LookupCandidate]) -> tuple[LookupCandidate, ...]:
    by_governor: dict[int, LookupCandidate] = {}
    for row in rows:
        existing = by_governor.get(row.governor_id)
        if existing is None or (
            row.score,
            row.is_current_name,
            row.last_seen or datetime.min.replace(tzinfo=UTC),
        ) > (
            existing.score,
            existing.is_current_name,
            existing.last_seen or datetime.min.replace(tzinfo=UTC),
        ):
            by_governor[row.governor_id] = row
    return tuple(
        sorted(
            by_governor.values(),
            key=lambda item: (
                -item.score,
                not item.is_current_name,
                item.governor_name.casefold(),
                item.governor_id,
            ),
        )
    )


async def resolve_name(name: str, *, refresh: bool = False) -> LookupResult:
    query = normalize_name(name)
    if not query:
        return LookupResult(status="invalid", error="A governor name is required.")
    if len(query) > _MAX_LOOKUP_LENGTH:
        return LookupResult(
            status="invalid", error="Governor name lookup is limited to 100 characters."
        )
    directory = await _lookup_directory(refresh=refresh)
    exact = _dedupe_candidates(
        [row for row in directory if normalize_name(row.governor_name) == query]
    )
    if exact:
        return LookupResult(status="found" if len(exact) == 1 else "matches", candidates=exact)

    scored: list[LookupCandidate] = []
    for row in directory:
        candidate_name = normalize_name(row.governor_name)
        score = float(max(fuzz.ratio(query, candidate_name), fuzz.WRatio(query, candidate_name)))
        if score >= _FUZZY_CUTOFF:
            scored.append(replace(row, score=score))
    candidates = _dedupe_candidates(scored)
    if not candidates:
        return LookupResult(status="not_found", error="No matching governor was found.")
    return LookupResult(
        status="found" if len(candidates) == 1 else "matches",
        candidates=candidates[:25],
    )


def validate_command_inputs(governor_id: int | None, name: str | None) -> str | None:
    has_id = governor_id is not None
    has_name = bool(normalize_name(name))
    if has_id == has_name:
        return "Provide exactly one of governor_id or name."
    if has_id and not 0 < int(governor_id or 0) <= _MAX_GOVERNOR_ID:
        return "Governor ID must be a positive exact 64-bit ID."
    if has_name and len(normalize_name(name)) > _MAX_LOOKUP_LENGTH:
        return "Governor name lookup is limited to 100 characters."
    return None


def _freshness(payload_header, coverage, presence) -> FreshnessState:
    current_presence = next((item for item in presence if item.window == "CURRENT"), None)
    if current_presence is None or current_presence.present_scans == 0:
        return "NO DATA"
    scan_at = payload_header.latest_governor_scan_at_utc
    stale = (
        not payload_header.present_latest
        or scan_at is None
        or payload_header.effective_now_utc - scan_at > timedelta(hours=48)
    )
    if stale:
        return "STALE"
    required = [item for item in coverage if item.window == "CURRENT" and item.required]
    if any(item.state not in {"COMPLETE", "NOT_REQUIRED"} for item in required):
        return "PARTIAL"
    return "CURRENT"


def _linked_governors(governor_id: int, governor_name: str | None) -> tuple[LinkedGovernor, ...]:
    owner = registry_service.get_discord_user_for_governor(governor_id)
    if not owner:
        return ()
    accounts = registry_service.get_user_accounts(int(owner["DiscordUserID"]))
    output: dict[int, LinkedGovernor] = {}
    for row in accounts.values():
        try:
            gid = int(str(row.get("GovernorID") or "").strip())
        except (TypeError, ValueError):
            continue
        if gid <= 0:
            continue
        output[gid] = LinkedGovernor(
            governor_id=gid,
            governor_name=str(
                row.get("GovernorName") or (governor_name if gid == governor_id else gid)
            ),
            current=gid == governor_id,
        )
    return tuple(
        sorted(
            output.values(),
            key=lambda item: (not item.current, item.governor_name.casefold(), item.governor_id),
        )
    )


async def is_current_linked_target(source_governor_id: int, target_governor_id: int) -> bool:
    """Re-resolve the registry relationship before linked-governor navigation."""
    rows = await asyncio.to_thread(_linked_governors, int(source_governor_id), None)
    return int(target_governor_id) in {row.governor_id for row in rows}


def _finalized_kvk_numbers(candidates) -> set[int]:
    details = kvk_state.get_latest_kvk_details()
    max_scan_order = details.get("max_scan_order") if details else None
    finalized: set[int] = set()
    for candidate in candidates:
        if candidate.final_output_state != "OUTPUT_COMPLETE" or candidate.final_data_at_utc is None:
            continue
        state, _reason = kvk_state.resolve_kvk_scan_state(
            pass4_start_scan=candidate.pass4_start_scan,
            kvk_end_scan=candidate.kvk_end_scan,
            max_scan_order=max_scan_order,
        )
        if state == "ENDED":
            finalized.add(candidate.kvk_no)
    return finalized


def _normalise_kvk_performance(row: KvkPerformance) -> KvkPerformance:
    """Apply leadership availability guards without inventing historical combat evidence."""
    if row.healed_data_available is False:
        return replace(
            row,
            healed=None,
            kp_loss=None,
            healed_rank=None,
            tanking_score=None,
            tanking_rank=None,
            tanking_cohort_count=None,
        )
    if row.healed is None or row.healed <= 0:
        return replace(row, tanking_score=None, tanking_rank=None)
    return row


def _kvk_index(rows: tuple[KvkPerformance, ...]) -> KvkIndex:
    """Return the uncapped mean KVK score for the latest three finalized rows."""
    candidates = rows[:3]
    per_kvk: list[tuple[int, Decimal | None]] = []
    scores: list[Decimal] = []
    for row in candidates:
        score: Decimal | None = None
        raw_values = (row.t4_t5_kills, row.deads, row.healed)
        percentages = (row.kill_target_percent, row.dead_target_percent)
        source_available = row.healed_data_available is True
        complete = all(value is not None and value >= 0 for value in raw_values)
        targets_available = all(value is not None for value in percentages)
        if source_available and not row.exempt and complete and targets_available:
            if any(value == 0 for value in raw_values):
                score = Decimal(0)
            elif row.tanking_score is not None:
                score = (
                    row.kill_target_percent * Decimal("0.60")
                    + row.dead_target_percent * Decimal("0.20")
                    + row.tanking_score * Decimal("0.20")
                )
        per_kvk.append((row.kvk_no, score))
        if score is not None:
            scores.append(score)

    value = sum(scores, Decimal(0)) / Decimal(len(scores)) if scores else None
    availability = (
        "AVAILABLE"
        if scores and len(scores) == len(candidates)
        else "PARTIAL" if scores else "NOT_RECORDED"
    )
    return KvkIndex(value, len(scores), len(candidates), tuple(per_kvk), availability)


def _metric_label(metric: ActivityMetric) -> str:
    return {
        "FORTS_TOTAL": "Forts",
        "HELPS": "Helps",
        "TECH_DONATIONS": "Tech Donations",
        "RSS_GATHERED": "RSS Gathered",
        "BUILDING_MINUTES": "Building Minutes",
        "POWER_CHANGE": "Power Change",
    }.get(metric.code, metric.code.replace("_", " ").title())


async def _load_last_active(
    governor_id: int,
    *,
    effective_now_utc: datetime,
    refresh: bool,
    diagnostics: dict[str, object],
) -> LastActive:
    cache_key = (int(governor_id), effective_now_utc.date())
    started = time.perf_counter()
    cache_now = time.monotonic()
    async with _cache_lock:
        cached = _last_active_cache.get(cache_key)
        if not refresh and cached and cached[0] > cache_now:
            diagnostics.update(cache_status="HIT", total_ms=(time.perf_counter() - started) * 1000)
            return cached[1]
    sql_diagnostics: dict[str, object] = {}
    result = await asyncio.to_thread(
        dal.fetch_last_active,
        governor_id,
        history_days=720,
        now_utc=effective_now_utc,
        diagnostics=sql_diagnostics,
    )
    diagnostics.update(sql_diagnostics)
    diagnostics["cache_status"] = "REFRESH" if refresh else "MISS"
    async with _cache_lock:
        if len(_last_active_cache) >= 128:
            oldest = min(_last_active_cache, key=lambda item: _last_active_cache[item][0])
            _last_active_cache.pop(oldest, None)
        _last_active_cache[cache_key] = (
            time.monotonic() + _PAYLOAD_TTL_SECONDS,
            result,
        )
    return result


def _load_diagnostics(
    *,
    cache_status: str,
    total_ms: float,
    stages: dict[str, float],
    dal_diagnostics: dict[str, dict[str, object]],
) -> LoadDiagnostics:
    stage_rows: list[tuple[str, float]] = [
        (name, round(value, 3)) for name, value in stages.items()
    ]
    result_rows: list[tuple[str, int]] = []
    result_bytes: list[tuple[str, int]] = []
    for name, values in dal_diagnostics.items():
        for metric in ("connection_ms", "sql_fetch_ms", "mapping_ms", "total_ms"):
            value = values.get(metric)
            if isinstance(value, (int, float)):
                stage_rows.append((f"{name}_{metric}", round(float(value), 3)))
        rows = values.get("result_rows")
        size = values.get("approximate_result_bytes")
        if isinstance(rows, int):
            result_rows.append((name, rows))
        if isinstance(size, int):
            result_bytes.append((name, size))
    return LoadDiagnostics(
        cache_status=cache_status,
        total_ms=round(total_ms, 3),
        stage_ms=tuple(stage_rows),
        result_rows=tuple(result_rows),
        approximate_result_bytes=tuple(result_bytes),
    )


def _log_performance(diagnostics: LoadDiagnostics, *, period: int, page: ReviewPage) -> None:
    logger.debug(
        "leadership_player_performance cache=%s period=%s page=%s total_ms=%.3f "
        "stages=%s rows=%s approximate_bytes=%s",
        diagnostics.cache_status,
        period,
        page,
        diagnostics.total_ms,
        diagnostics.stage_ms,
        diagnostics.result_rows,
        diagnostics.approximate_result_bytes,
    )


def _prompts(*, freshness: FreshnessState, header, metrics, activity_index) -> tuple[str, ...]:
    is_new = (
        header.first_observed_date is not None
        and header.current_start_date is not None
        and header.first_observed_date >= header.current_start_date
    )
    comparable = all(metric.comparison_mode != "UNAVAILABLE" for metric in metrics)
    cohort = activity_index.cohort_count or 0
    if freshness != "CURRENT" or is_new or not comparable or cohort < _SMALL_COHORT:
        return ()
    ranked = [metric for metric in metrics if metric.percentile is not None and metric.kingdom_rank]
    if not ranked:
        return ()
    best = max(ranked, key=lambda item: item.percentile or 0)
    worst = min(ranked, key=lambda item: item.percentile or 0)
    strength = (
        f"Strength: {_metric_label(best)} ranks #{best.kingdom_rank} of {best.cohort_count}; "
        f"top {best.top_percent:.0f}% with {best.current_valid_days} valid reporting days."
    )
    attention = (
        f"Review: what changed in {_metric_label(worst)}? It ranks #{worst.kingdom_rank} of "
        f"{worst.cohort_count} with {worst.missing_units} missing source units."
    )
    return (strength, attention) if best.order != worst.order else (strength,)


async def load_payload(
    governor_id: int,
    period_days: int = DEFAULT_PERIOD,
    *,
    page: ReviewPage = "overview",
    refresh: bool = False,
) -> LeadershipPlayerPayload:
    load_started = time.perf_counter()
    gid = int(governor_id)
    period = int(period_days)
    if gid <= 0:
        raise ValueError("Governor ID must be positive")
    if period not in SUPPORTED_PERIODS:
        raise ValueError("Unsupported leadership review period")
    key = (gid, period)
    now = time.monotonic()
    async with _cache_lock:
        cached = _payload_cache.get(key)
        if not refresh and cached and cached[0] > now:
            diagnostics = LoadDiagnostics(
                cache_status="HIT",
                total_ms=round((time.perf_counter() - load_started) * 1000.0, 3),
            )
            _log_performance(diagnostics, period=period, page=page)
            return replace(cached[1], page=page, diagnostics=diagnostics)

    effective_now_utc = datetime.now(UTC)
    review_diagnostics: dict[str, object] = {}
    kvk_diagnostics: dict[str, object] = {}
    last_active_diagnostics: dict[str, object] = {}
    stages: dict[str, float] = {}

    async def load_linked() -> tuple[LinkedGovernor, ...]:
        started = time.perf_counter()
        result = await asyncio.to_thread(_linked_governors, gid, None)
        stages["linked_lookup_ms"] = (time.perf_counter() - started) * 1000.0
        return result

    review_task = asyncio.to_thread(
        dal.fetch_review_contract,
        gid,
        period,
        now_utc=effective_now_utc,
        diagnostics=review_diagnostics,
    )
    kvk_task = asyncio.to_thread(
        dal.fetch_kvk_history,
        gid,
        candidate_limit=20,
        diagnostics=kvk_diagnostics,
    )
    last_active_task = _load_last_active(
        gid,
        effective_now_utc=effective_now_utc,
        refresh=refresh,
        diagnostics=last_active_diagnostics,
    )
    review, kvk, linked, last_active = await asyncio.gather(
        review_task, kvk_task, load_linked(), last_active_task
    )
    identity_ids = (gid,)
    identity_diagnostics: dict[str, object] = {}
    identity = await asyncio.to_thread(
        dal.fetch_identity_history,
        identity_ids,
        history_days=720,
        diagnostics=identity_diagnostics,
    )
    kvk_started = time.perf_counter()
    header, presence, coverage, metrics, activity_index, history_depth = review
    aliases, episodes = identity
    candidates, kvk_rows = kvk
    finalized = _finalized_kvk_numbers(candidates)
    candidate_by_kvk = {candidate.kvk_no: candidate for candidate in candidates}
    completed_rows = tuple(
        sorted(
            (
                _normalise_kvk_performance(
                    replace(row, kvk_name=candidate_by_kvk[row.kvk_no].kvk_name)
                )
                for row in kvk_rows
                if row.kvk_no in finalized
            ),
            key=lambda row: row.kvk_no,
            reverse=True,
        )
    )
    stages["kvk_resolution_ms"] = (time.perf_counter() - kvk_started) * 1000.0
    payload_started = time.perf_counter()
    warnings: list[str] = []
    if any(metric.reset_count for metric in metrics):
        warnings.append("Negative monotonic-counter resets were excluded from activity totals.")
    if header.first_observed_offset_days is not None:
        warnings.append(f"NEW TO PERIOD · first observed day +{header.first_observed_offset_days}")
    freshness = _freshness(header, coverage, presence)
    payload = LeadershipPlayerPayload(
        header=header,
        freshness=freshness,
        period_days=period,
        page=page,
        presence=presence,
        coverage=coverage,
        metrics=metrics,
        activity_index=activity_index,
        history_depth=history_depth,
        aliases=aliases,
        alliance_episodes=episodes,
        linked_governors=linked,
        kvk_rows=completed_rows,
        prompts=_prompts(
            freshness=freshness,
            header=header,
            metrics=metrics,
            activity_index=activity_index,
        ),
        warnings=tuple(warnings),
        generated_at_utc=datetime.now(UTC),
        last_active=last_active,
        kvk_index=_kvk_index(completed_rows),
    )
    stages["payload_construction_ms"] = (time.perf_counter() - payload_started) * 1000.0
    diagnostics = _load_diagnostics(
        cache_status="REFRESH" if refresh else "MISS",
        total_ms=(time.perf_counter() - load_started) * 1000.0,
        stages=stages,
        dal_diagnostics={
            "review": review_diagnostics,
            "kvk": kvk_diagnostics,
            "last_active": last_active_diagnostics,
            "identity": identity_diagnostics,
        },
    )
    payload = replace(payload, diagnostics=diagnostics)
    async with _cache_lock:
        if len(_payload_cache) >= 128:
            oldest = min(_payload_cache, key=lambda item: _payload_cache[item][0])
            _payload_cache.pop(oldest, None)
        _payload_cache[key] = (
            time.monotonic() + _PAYLOAD_TTL_SECONDS,
            replace(payload, page="overview", diagnostics=None),
        )
    _log_performance(diagnostics, period=period, page=page)
    return payload


async def write_audit(
    *,
    actor_id: int,
    target_governor_id: int | None,
    guild_id: int,
    channel_id: int,
    authorization_basis: str,
    authorization_role_id: int | None,
    action: str,
    outcome: str,
    error_code: str | None,
    correlation_id: UUID,
) -> None:
    try:
        await asyncio.to_thread(
            dal.record_audit,
            actor_id=actor_id,
            target_governor_id=target_governor_id,
            guild_id=guild_id,
            channel_id=channel_id,
            authorization_basis=authorization_basis,
            authorization_role_id=authorization_role_id,
            action=action,
            outcome=outcome,
            error_code=error_code,
            correlation_id=correlation_id,
        )
    except Exception:
        logger.exception(
            "leadership_player_review_audit_failed actor_id=%s target_id=%s action=%s outcome=%s",
            actor_id,
            target_governor_id,
            action,
            outcome,
        )
