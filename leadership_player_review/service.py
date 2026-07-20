"""Business rules and orchestration for private leadership player review."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
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
    LeadershipPlayerPayload,
    LinkedGovernor,
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
            return _directory_cache[1]
    rows = await asyncio.to_thread(dal.fetch_lookup_directory, history_days=720)
    async with _cache_lock:
        _directory_cache = (time.monotonic() + _DIRECTORY_TTL_SECONDS, rows)
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


def _metric_label(metric: ActivityMetric) -> str:
    return {
        "FORTS_TOTAL": "Forts",
        "HELPS": "Helps",
        "TECH_DONATIONS": "Tech Donations",
        "RSS_GATHERED": "RSS Gathered",
        "BUILDING_MINUTES": "Building Minutes",
        "POWER_CHANGE": "Power Change",
    }.get(metric.code, metric.code.replace("_", " ").title())


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
            return replace(cached[1], page=page)

    review_task = asyncio.to_thread(dal.fetch_review_contract, gid, period)
    kvk_task = asyncio.to_thread(dal.fetch_kvk_history, gid, candidate_limit=20)
    linked_task = asyncio.to_thread(_linked_governors, gid, None)
    review, kvk, linked = await asyncio.gather(review_task, kvk_task, linked_task)
    identity_ids = tuple(row.governor_id for row in linked) or (gid,)
    identity = await asyncio.to_thread(
        dal.fetch_identity_history,
        identity_ids,
        history_days=720,
    )
    header, presence, coverage, metrics, activity_index, history_depth = review
    aliases, episodes = identity
    candidates, kvk_rows = kvk
    finalized = _finalized_kvk_numbers(candidates)
    candidate_by_kvk = {candidate.kvk_no: candidate for candidate in candidates}
    completed_rows = tuple(
        sorted(
            (
                replace(row, kvk_name=candidate_by_kvk[row.kvk_no].kvk_name)
                for row in kvk_rows
                if row.kvk_no in finalized
            ),
            key=lambda row: row.kvk_no,
            reverse=True,
        )
    )
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
    )
    async with _cache_lock:
        if len(_payload_cache) >= 128:
            oldest = min(_payload_cache, key=lambda item: _payload_cache[item][0])
            _payload_cache.pop(oldest, None)
        _payload_cache[key] = (
            time.monotonic() + _PAYLOAD_TTL_SECONDS,
            replace(payload, page="overview"),
        )
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
