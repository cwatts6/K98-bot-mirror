"""Stored-procedure-only data access for leadership player review."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
import time
from typing import Any, cast
from uuid import UUID

from file_utils import get_conn_with_retries
from leadership_player_review.last_active import validate_last_active
from leadership_player_review.models import (
    ActivityIndex,
    ActivityMetric,
    AliasRecord,
    AllianceEpisode,
    HistoryDepth,
    KvkCandidate,
    KvkIndex,
    KvkPerformance,
    LastActive,
    LastActiveState,
    LookupCandidate,
    ReviewHeader,
    ScanPresence,
    SourceCoverage,
)

_QUERY_TIMEOUT_SECONDS = 12
_MAX_GOVERNORS = 26


def _int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(Decimal(str(value).strip()))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _decimal(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, TypeError, ValueError):
        return None


def _text(value: Any) -> str | None:
    cleaned = " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())
    return cleaned or None


def _date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    return value if isinstance(value, date) else None


def _utc(value: Any) -> datetime | None:
    if not isinstance(value, datetime):
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _rows(cursor: Any) -> list[dict[str, Any]]:
    fetched = cursor.fetchall()
    if not fetched:
        return []
    names = [str(column[0]) for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in fetched]


def _next_rows(cursor: Any, *, advance: bool = False) -> list[dict[str, Any]]:
    if advance and not cursor.nextset():
        raise ValueError("leadership SQL contract omitted a result set")
    while cursor.description is None:
        if not cursor.nextset():
            raise ValueError("leadership SQL contract omitted a result set")
    return _rows(cursor)


def _cursor(conn: Any) -> Any:
    cursor = conn.cursor()
    if hasattr(cursor, "timeout"):
        cursor.timeout = _QUERY_TIMEOUT_SECONDS
    return cursor


def _result_sets(cursor: Any, count: int) -> tuple[list[dict[str, Any]], ...]:
    return tuple(_next_rows(cursor, advance=index > 0) for index in range(count))


def _approximate_result_bytes(result_sets: Iterable[Iterable[dict[str, Any]]]) -> int:
    return sum(
        len(str(key).encode("utf-8")) + len(str(value).encode("utf-8"))
        for rows in result_sets
        for row in rows
        for key, value in row.items()
    )


def _record_diagnostics(
    diagnostics: dict[str, Any] | None,
    *,
    started: float,
    connected: float,
    fetched: float,
    mapped: float,
    result_sets: tuple[list[dict[str, Any]], ...],
) -> None:
    if diagnostics is None:
        return
    diagnostics.update(
        connection_ms=(connected - started) * 1000.0,
        sql_fetch_ms=(fetched - connected) * 1000.0,
        mapping_ms=(mapped - fetched) * 1000.0,
        total_ms=(mapped - started) * 1000.0,
        result_rows=sum(len(rows) for rows in result_sets),
        approximate_result_bytes=_approximate_result_bytes(result_sets),
        result_set_rows=tuple(len(rows) for rows in result_sets),
    )


def fetch_lookup_directory(
    *, history_days: int = 720, diagnostics: dict[str, Any] | None = None
) -> tuple[LookupCandidate, ...]:
    if not 1 <= int(history_days) <= 720:
        raise ValueError("lookup history must be between 1 and 720 days")
    started = time.perf_counter()
    with get_conn_with_retries() as conn:
        connected = time.perf_counter()
        cur = _cursor(conn)
        cur.execute(
            "EXEC dbo.usp_GetLeadershipPlayerLookupDirectory @HistoryDays = ?;",
            (int(history_days),),
        )
        result_sets = _result_sets(cur, 1)
        fetched = time.perf_counter()
        output = []
        for row in result_sets[0]:
            gid = _int(row.get("GovernorID"))
            name = _text(row.get("GovernorName"))
            key = _text(row.get("GovernorNameKey"))
            if not gid or not name or not key:
                continue
            output.append(
                LookupCandidate(
                    governor_id=gid,
                    governor_name=name,
                    normalized_name=key,
                    current_name=_text(row.get("CurrentGovernorName")),
                    current_alliance=_text(row.get("CurrentAlliance")),
                    last_scan_at_utc=_utc(row.get("LastGovernorScanAtUtc")),
                    present_latest=bool(row.get("PresentInLatestCompleteScan")),
                    is_current_name=bool(row.get("IsCurrentName")),
                    first_seen=_utc(row.get("FirstSeen")),
                    last_seen=_utc(row.get("LastSeen")),
                    seen_scan_count=_int(row.get("SeenScanCount")) or 0,
                )
            )
        result = tuple(output)
        mapped = time.perf_counter()
        _record_diagnostics(
            diagnostics,
            started=started,
            connected=connected,
            fetched=fetched,
            mapped=mapped,
            result_sets=result_sets,
        )
        return result


def fetch_review_contract(
    governor_id: int,
    period_days: int,
    *,
    now_utc: datetime | None = None,
    diagnostics: dict[str, Any] | None = None,
) -> tuple[
    ReviewHeader,
    tuple[ScanPresence, ...],
    tuple[SourceCoverage, ...],
    tuple[ActivityMetric, ...],
    ActivityIndex,
    tuple[HistoryDepth, ...],
]:
    started = time.perf_counter()
    with get_conn_with_retries() as conn:
        connected = time.perf_counter()
        cur = _cursor(conn)
        cur.execute(
            "EXEC dbo.usp_GetLeadershipPlayerReview @GovernorID = ?, @PeriodDays = ?, @NowUtc = ?;",
            (int(governor_id), int(period_days), now_utc),
        )
        result_sets = _result_sets(cur, 6)
        fetched = time.perf_counter()
        header_rows, presence_rows, coverage_rows, metric_rows, index_rows, history_rows = (
            result_sets
        )
        if len(header_rows) != 1:
            raise ValueError("leadership review header result must contain exactly one row")
        row = header_rows[0]
        effective = _utc(row.get("EffectiveNowUtc"))
        if effective is None:
            raise ValueError("leadership review header omitted EffectiveNowUtc")
        header = ReviewHeader(
            governor_id=_int(row.get("GovernorID")) or int(governor_id),
            governor_name=_text(row.get("GovernorName")),
            current_alliance=_text(row.get("CurrentAlliance")),
            current_power=_int(row.get("CurrentPower")),
            current_power_rank=_int(row.get("PowerRank")),
            city_hall=_int(row.get("CityHall")),
            effective_now_utc=effective,
            anchor_date=_date(row.get("AnchorDate")),
            current_start_date=_date(row.get("CurrentStartDate")),
            current_end_date=_date(row.get("CurrentEndDate")),
            previous_start_date=_date(row.get("PreviousStartDate")),
            previous_end_date=_date(row.get("PreviousEndDate")),
            period_days=_int(row.get("PeriodDays")) or int(period_days),
            latest_complete_scan_order=_int(row.get("LatestCompleteScanOrder")),
            latest_complete_scan_at_utc=_utc(row.get("LatestCompleteScanAtUtc")),
            latest_governor_scan_order=_int(row.get("LatestGovernorScanOrder")),
            latest_governor_scan_at_utc=_utc(row.get("LatestGovernorScanAtUtc")),
            present_latest=bool(row.get("PresentInLatestCompleteScan")),
            first_observed_date=_date(row.get("FirstObservedDate")),
            first_observed_offset_days=_int(row.get("FirstObservedOffsetDays")),
            location_x=_int(row.get("LocationX")),
            location_y=_int(row.get("LocationY")),
            location_updated_at_utc=_utc(row.get("LocationUpdatedAtUtc")),
            shield_ends_at_utc=_utc(row.get("ShieldEndsAtUtc")),
        )

        presence = tuple(
            ScanPresence(
                window=_text(item.get("WindowCode")) or "UNKNOWN",
                complete_scans=_int(item.get("CompleteScanCount")) or 0,
                present_scans=_int(item.get("PresentScanCount")) or 0,
                scanned_days=_int(item.get("ScannedDayCount")) or 0,
                present_scanned_days=_int(item.get("PresentScannedDayCount")) or 0,
            )
            for item in presence_rows
        )
        coverage = tuple(
            SourceCoverage(
                window=_text(item.get("WindowCode")) or "UNKNOWN",
                source_code=_text(item.get("SourceCode")) or "UNKNOWN",
                required=bool(item.get("RequiredSource")),
                expected_units=_int(item.get("ExpectedUnits")) or 0,
                valid_units=_int(item.get("ValidUnits")) or 0,
                missing_units=_int(item.get("MissingUnits")) or 0,
                reset_count=_int(item.get("ResetCount")) or 0,
                state=_text(item.get("CoverageState")) or "NO_DATA",
            )
            for item in coverage_rows
        )
        metrics = tuple(
            ActivityMetric(
                order=_int(item.get("MetricOrder")) or 0,
                code=_text(item.get("MetricCode")) or "UNKNOWN",
                current_total=_decimal(item.get("CurrentTotal")),
                current_valid_days=_int(item.get("CurrentValidReportingDays")) or 0,
                current_average=_decimal(item.get("CurrentAveragePerValidDay")),
                previous_total=_decimal(item.get("PreviousTotal")),
                previous_valid_days=_int(item.get("PreviousValidReportingDays")) or 0,
                previous_average=_decimal(item.get("PreviousAveragePerValidDay")),
                comparison_mode=_text(item.get("ComparisonMode")) or "UNAVAILABLE",
                comparison_percent=_decimal(item.get("ComparisonPercent")),
                expected_units=_int(item.get("CurrentExpectedUnits")) or 0,
                missing_units=_int(item.get("CurrentMissingUnits")) or 0,
                reset_count=_int(item.get("CurrentResetCount")) or 0,
                available=bool(item.get("CurrentIsAvailable")),
                kingdom_rank=_int(item.get("KingdomRank")),
                cohort_count=_int(item.get("RankCohortCount")),
                percentile=_decimal(item.get("PercentileScore")),
                top_percent=_decimal(item.get("TopPercent")),
            )
            for item in metric_rows
        )
        index_row = index_rows[0] if index_rows else {}
        activity_index = ActivityIndex(
            value=_decimal(index_row.get("ActivityIndex")),
            rank=_int(index_row.get("ActivityRank")),
            cohort_count=_int(index_row.get("ActivityRankCohortCount")),
            components=tuple(
                (label, _decimal(index_row.get(column)))
                for label, column in (
                    ("Forts", "FortsScore"),
                    ("Helps", "HelpsScore"),
                    ("Tech", "TechScore"),
                    ("RSS", "RSSScore"),
                    ("Building", "BuildingScore"),
                    ("Power", "PowerScore"),
                )
            ),
            availability=_text(index_row.get("Availability")) or "MISSING_COMPONENT",
        )
        history = tuple(
            HistoryDepth(
                source_code=_text(item.get("SourceCode")) or "UNKNOWN",
                history_kind=_text(item.get("HistoryKind")) or "UNKNOWN",
                earliest=_date(item.get("EarliestObservedDate")),
                latest=_date(item.get("LatestObservedDate")),
                observation_count=_int(item.get("ObservationCount")) or 0,
                gap_count=_int(item.get("GapCount")),
                longest_gap_days=_int(item.get("LongestGapDays")),
                evidence_basis=_text(item.get("EvidenceBasis")) or "UNKNOWN",
            )
            for item in history_rows
        )
        result = header, presence, coverage, metrics, activity_index, history
        mapped = time.perf_counter()
        _record_diagnostics(
            diagnostics,
            started=started,
            connected=connected,
            fetched=fetched,
            mapped=mapped,
            result_sets=result_sets,
        )
        return result


def _governor_id_values_sql(ids: tuple[int, ...]) -> tuple[str, tuple[Any, ...]]:
    padded: tuple[Any, ...] = (*ids, *(None for _ in range(_MAX_GOVERNORS - len(ids))))
    return ", ".join("(?)" for _ in range(_MAX_GOVERNORS)), padded


def fetch_identity_history(
    governor_ids: Iterable[int],
    *,
    history_days: int = 720,
    diagnostics: dict[str, Any] | None = None,
) -> tuple[tuple[AliasRecord, ...], tuple[AllianceEpisode, ...]]:
    ids = tuple(dict.fromkeys(int(value) for value in governor_ids if int(value) > 0))
    if not 1 <= len(ids) <= _MAX_GOVERNORS:
        raise ValueError("identity history requires between 1 and 26 Governor IDs")
    if not 1 <= int(history_days) <= 720:
        raise ValueError("identity history must be between 1 and 720 days")
    values_sql, params = _governor_id_values_sql(ids)
    sql = f"""
        SET NOCOUNT ON;
        DECLARE @GovernorIDs dbo.IntList;
        INSERT INTO @GovernorIDs(ID)
        SELECT DISTINCT GovernorID FROM (VALUES {values_sql}) AS v(GovernorID)
        WHERE GovernorID IS NOT NULL;
        EXEC dbo.usp_GetLeadershipPlayerIdentityHistory
             @GovernorIDs = @GovernorIDs, @HistoryDays = ?;
    """
    started = time.perf_counter()
    with get_conn_with_retries() as conn:
        connected = time.perf_counter()
        cur = _cursor(conn)
        cur.execute(sql, (*params, int(history_days)))
        result_sets = _result_sets(cur, 2)
        fetched = time.perf_counter()
        aliases = tuple(
            AliasRecord(
                governor_id=_int(row.get("GovernorID")) or 0,
                governor_name=_text(row.get("GovernorName")) or "Unknown",
                first_seen=_utc(row.get("FirstSeen")),
                last_seen=_utc(row.get("LastSeen")),
                seen_scan_count=_int(row.get("SeenScanCount")) or 0,
            )
            for row in result_sets[0]
        )
        episodes = tuple(
            AllianceEpisode(
                governor_id=_int(row.get("GovernorID")) or 0,
                sequence=_int(row.get("EpisodeSequence")) or 0,
                alliance=_text(row.get("Alliance")) or "Unallied",
                first_observed=_date(row.get("FirstObservedDate")),
                last_observed=_date(row.get("LastObservedDate")),
                observed_scans=_int(row.get("ObservedScanCount")) or 0,
                current=bool(row.get("IsCurrentEpisode")),
            )
            for row in result_sets[1]
        )
        result = aliases, episodes
        mapped = time.perf_counter()
        _record_diagnostics(
            diagnostics,
            started=started,
            connected=connected,
            fetched=fetched,
            mapped=mapped,
            result_sets=result_sets,
        )
        return result


def fetch_kvk_history(
    governor_id: int,
    *,
    candidate_limit: int = 12,
    diagnostics: dict[str, Any] | None = None,
) -> tuple[tuple[KvkCandidate, ...], tuple[KvkPerformance, ...], KvkIndex]:
    if not 3 <= int(candidate_limit) <= 20:
        raise ValueError("KVK candidate limit must be between 3 and 20")
    started = time.perf_counter()
    with get_conn_with_retries() as conn:
        connected = time.perf_counter()
        cur = _cursor(conn)
        cur.execute(
            "EXEC dbo.usp_GetLeadershipPlayerKvkHistory @GovernorID = ?, @CandidateLimit = ?;",
            (int(governor_id), int(candidate_limit)),
        )
        result_sets = _result_sets(cur, 3)
        fetched = time.perf_counter()
        candidates = tuple(
            KvkCandidate(
                kvk_no=_int(row.get("KVK_NO")) or 0,
                kvk_name=_text(row.get("KVK_NAME")),
                registration_date=_date(row.get("KVK_REGISTRATION_DATE")),
                start_date=_date(row.get("KVK_START_DATE")),
                end_date=_date(row.get("KVK_END_DATE")),
                matchmaking_scan=_int(row.get("MATCHMAKING_SCAN")),
                kvk_end_scan=_int(row.get("KVK_END_SCAN")),
                matchmaking_start_date=_date(row.get("MATCHMAKING_START_DATE")),
                fighting_start_date=_date(row.get("FIGHTING_START_DATE")),
                pass4_start_scan=_int(row.get("PASS4_START_SCAN")),
                final_data_at_utc=_utc(row.get("FinalDataAtUtc")),
                final_scan_order=_int(row.get("FinalScanOrder")),
                final_output_state=_text(row.get("FinalOutputState")),
                finalization_basis=_text(row.get("FinalizationBasis")),
            )
            for row in result_sets[0]
        )
        rows = tuple(
            KvkPerformance(
                kvk_no=_int(row.get("KVK_NO")) or 0,
                kvk_name=None,
                governor_id=_int(row.get("GovernorID")) or int(governor_id),
                governor_name=_text(row.get("GovernorName")),
                kvk_rank=_int(row.get("KVKRank")),
                t4_t5_kills=_int(row.get("T4T5Kills")),
                kill_target=_int(row.get("KillTarget")),
                kill_target_percent=_decimal(row.get("KillTargetPercent")),
                kill_points=_int(row.get("KillPoints")),
                deads=_int(row.get("Deads")),
                dead_target=_int(row.get("DeadTarget")),
                dead_target_percent=_decimal(row.get("DeadTargetPercent")),
                healed=_int(row.get("Healed")),
                kp_loss=_int(row.get("KPLoss")),
                tanking_score=_decimal(row.get("TankingScore")),
                acclaim=_int(row.get("Acclaim")),
                acclaim_rank=_int(row.get("AcclaimRank")),
                dkp=_int(row.get("DKP")),
                dkp_target=_int(row.get("DKPTarget")),
                dkp_target_percent=_decimal(row.get("DKPTargetPercent")),
                prekvk_points=_int(row.get("PreKvkPoints")),
                prekvk_rank=_int(row.get("PreKvkRank")),
                honor_points=_int(row.get("HonorPoints")),
                honor_rank=_int(row.get("HonorRank")),
                exempt=bool(row.get("IsExempt")),
                engaged=bool(row.get("IsEngaged")),
                healed_rank=_int(row.get("HealedRank")),
                tanking_rank=_int(row.get("TankingRank")),
                engaged_cohort_count=_int(row.get("EngagedCohortCount")),
                tanking_cohort_count=_int(row.get("TankingCohortCount")),
                final_data_at_utc=_utc(row.get("FinalDataAtUtc")),
                final_output_state=_text(row.get("FinalOutputState")),
                finalization_basis=_text(row.get("FinalizationBasis")),
                personal_completed_kvk_best_acclaim=_int(
                    row.get("PersonalCompletedKvkBestAcclaim")
                ),
                kill_points_rank=_int(row.get("KillPointsRank")),
                deads_rank=_int(row.get("DeadsRank")),
                healed_data_available=(
                    bool(row.get("HealedDataAvailable"))
                    if row.get("HealedDataAvailable") is not None
                    else None
                ),
            )
            for row in result_sets[1]
        )
        index_rows = result_sets[2]
        if len(index_rows) != 1:
            raise ValueError("leadership KVK Index result must contain exactly one row")
        index_row = index_rows[0]
        returned_governor_id = _int(index_row.get("GovernorID"))
        if returned_governor_id != int(governor_id):
            raise ValueError("leadership KVK Index returned a mismatched Governor ID")
        availability = _text(index_row.get("Availability"))
        if availability not in {"AVAILABLE", "PARTIAL", "NOT_RECORDED"}:
            raise ValueError("leadership KVK Index returned an invalid availability state")
        scored_kvks = _int(index_row.get("ScoredKvkCount")) or 0
        candidate_kvks = _int(index_row.get("CandidateKvkCount")) or 0
        cohort_count = _int(index_row.get("KvkIndexCohortCount")) or 0
        rank = _int(index_row.get("KvkIndexRank"))
        value = _decimal(index_row.get("KvkIndexValue"))
        if not 0 <= scored_kvks <= candidate_kvks <= 3:
            raise ValueError("leadership KVK Index returned invalid score counts")
        if cohort_count < 0 or (rank is not None and not 1 <= rank <= cohort_count):
            raise ValueError("leadership KVK Index returned invalid kingdom rank values")
        if availability == "NOT_RECORDED" and (value is not None or rank is not None):
            raise ValueError("leadership KVK Index returned a value for NOT_RECORDED")
        if availability != "NOT_RECORDED" and (value is None or rank is None):
            raise ValueError("leadership KVK Index omitted an available value or rank")
        kvk_index = KvkIndex(
            value=value,
            scored_kvks=scored_kvks,
            candidate_kvks=candidate_kvks,
            per_kvk_scores=(),
            availability=availability,
            rank=rank,
            cohort_count=cohort_count,
        )
        result = candidates, rows, kvk_index
        mapped = time.perf_counter()
        _record_diagnostics(
            diagnostics,
            started=started,
            connected=connected,
            fetched=fetched,
            mapped=mapped,
            result_sets=result_sets,
        )
        return result


def fetch_last_active(
    governor_id: int,
    *,
    history_days: int = 720,
    now_utc: datetime | None = None,
    diagnostics: dict[str, Any] | None = None,
) -> LastActive:
    if int(governor_id) <= 0:
        raise ValueError("Governor ID must be positive")
    if not 1 <= int(history_days) <= 720:
        raise ValueError("Last Active history must be between 1 and 720 days")
    started = time.perf_counter()
    with get_conn_with_retries() as conn:
        connected = time.perf_counter()
        cur = _cursor(conn)
        cur.execute(
            """
            EXEC dbo.usp_GetLeadershipPlayerLastActive
                 @GovernorID = ?, @HistoryDays = ?, @NowUtc = ?;
            """,
            (int(governor_id), int(history_days), now_utc),
        )
        result_sets = _result_sets(cur, 1)
        fetched = time.perf_counter()
        rows = result_sets[0]
        if len(rows) != 1:
            raise ValueError("leadership Last Active result must contain exactly one row")
        row = rows[0]
        returned_governor_id = _int(row.get("GovernorID"))
        if returned_governor_id != int(governor_id):
            raise ValueError("leadership Last Active returned a mismatched Governor ID")
        effective = _date(row.get("EffectiveUtcDate"))
        history_start = _date(row.get("HistoryStartDate"))
        history_end = _date(row.get("HistoryEndDate"))
        state = _text(row.get("ActivityState"))
        if effective is None or history_start is None or history_end is None:
            raise ValueError("leadership Last Active omitted its bounded UTC dates")
        if state not in {"ACTIVE", "INACTIVE", "NOT_RECORDED"}:
            raise ValueError("leadership Last Active returned an invalid activity state")
        result = validate_last_active(
            LastActive(
                governor_id=returned_governor_id,
                effective_utc_date=effective,
                history_start_date=history_start,
                history_end_date=history_end,
                last_active_date=_date(row.get("LastActiveDate")),
                activity_state=cast(LastActiveState, state),
                qualifying_source_code=_text(row.get("QualifyingSourceCode")),
                qualifying_scan_order=_int(row.get("QualifyingScanOrder")),
                compared_complete_scans=_int(row.get("ComparedCompleteScanCount")) or 0,
                history_days=_int(row.get("HistoryDays")) or int(history_days),
            )
        )
        mapped = time.perf_counter()
        _record_diagnostics(
            diagnostics,
            started=started,
            connected=connected,
            fetched=fetched,
            mapped=mapped,
            result_sets=result_sets,
        )
        return result


def record_audit(
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
    with get_conn_with_retries() as conn:
        cur = _cursor(conn)
        cur.execute(
            """
            EXEC dbo.usp_RecordLeadershipPlayerReviewAudit
                 @ActorDiscordID = ?, @TargetGovernorID = ?, @GuildID = ?, @ChannelID = ?,
                 @AuthorizationBasis = ?, @AuthorizationRoleID = ?, @Action = ?, @Outcome = ?,
                 @ErrorCode = ?, @RequestCorrelationID = ?;
            """,
            (
                int(actor_id),
                int(target_governor_id) if target_governor_id else None,
                int(guild_id),
                int(channel_id),
                authorization_basis,
                int(authorization_role_id) if authorization_role_id else None,
                action,
                outcome,
                error_code,
                str(correlation_id),
            ),
        )
        conn.commit()
