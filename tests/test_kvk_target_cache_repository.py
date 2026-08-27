from __future__ import annotations

from datetime import UTC, datetime
import json
import multiprocessing
import os
from pathlib import Path
import sys
import threading
import time

import pytest

from kvk.models.kvk_target_cache import TargetCacheRefreshOutcome
from kvk.models.kvk_target_publication import (
    TargetPublicationMetadata,
    TargetPublicationSnapshot,
)
from kvk.models.kvk_target_row import TargetRow
from kvk.target_cache_repository import TargetCacheRepository
from process_utils import matches_process


def _context(*, kvk_no: int = 16, state: str = "DRAFT") -> dict[str, object]:
    return {
        "kvk_no": kvk_no,
        "state": state,
        "state_reason": "test_fighting_state",
    }


def _metadata(
    *,
    state: str = "OFFICIAL",
    version: int = 1,
    signature: str | None = None,
) -> TargetPublicationMetadata:
    official = state == "OFFICIAL"
    return TargetPublicationMetadata(
        publication_id=100 + version,
        kvk_no=16,
        publication_state=state,
        source_scan_order=1059 if official else 1040,
        source_scan_type="MATCHMAKING_SCAN" if official else "DRAFTSCAN",
        configured_draft_scan=1040,
        configured_matchmaking_scan=1059,
        published_at_utc=datetime(2026, 8, 27, 12, version, tzinfo=UTC),
        target_row_count=2,
        output_object_name="dbo.EXCEL_EXPORT_KVK_TARGETS_16",
        publication_version=version,
        publication_signature=signature or f"00000000-0000-0000-0000-{version:012d}",
    )


def _publication(
    *,
    state: str = "OFFICIAL",
    version: int = 1,
    signature: str | None = None,
) -> TargetPublicationSnapshot:
    return TargetPublicationSnapshot(
        _metadata(state=state, version=version, signature=signature),
        (
            TargetRow("123", "Alice", 1000, 100, 200, 10, 50, 1, 16),
            TargetRow("456", "Bob", 2000, 120, 240, 12, 60, 2, 16),
        ),
    )


def _repository(path, publication=None, **kwargs) -> TargetCacheRepository:
    selected = publication or _publication()
    return TargetCacheRepository(
        path,
        context_provider=lambda: _context(),
        metadata_fetcher=lambda _kvk_no: selected.metadata,
        publication_fetcher=lambda _kvk_no: selected,
        **kwargs,
    )


def _multiprocess_refresh_worker(
    cache_path: str,
    start_event,
    ready_event,
    block_rowset: bool,
    rowset_started,
    release_rowset,
    metadata_count,
    rowset_count,
    result_queue,
) -> None:
    publication = _publication()

    def fetch_metadata(_kvk_no):
        with metadata_count.get_lock():
            metadata_count.value += 1
        return publication.metadata

    def fetch_publication(_kvk_no):
        with rowset_count.get_lock():
            rowset_count.value += 1
        if block_rowset:
            rowset_started.set()
            release_rowset.wait(5)
        return publication

    repository = TargetCacheRepository(
        cache_path,
        context_provider=lambda: _context(),
        metadata_fetcher=fetch_metadata,
        publication_fetcher=fetch_publication,
    )
    ready_event.set()
    start_event.wait(5)
    pre_active = None
    if not block_rowset:
        coordination = repository._read_coordination()
        active = coordination.get("active_refresh")
        pre_active = bool(
            isinstance(active, dict) and repository._active_owner_is_current(active, time.time())
        )
    result_queue.put((repository.refresh().outcome.value, pre_active))


def test_two_processes_perform_one_metadata_and_rowset_fetch(tmp_path):
    context = multiprocessing.get_context("spawn")
    start_event = context.Event()
    first_ready = context.Event()
    second_ready = context.Event()
    rowset_started = context.Event()
    release_rowset = context.Event()
    metadata_count = context.Value("i", 0)
    rowset_count = context.Value("i", 0)
    result_queue = context.Queue()
    cache_path = str(tmp_path / "targets.json")
    first = context.Process(
        target=_multiprocess_refresh_worker,
        args=(
            cache_path,
            start_event,
            first_ready,
            True,
            rowset_started,
            release_rowset,
            metadata_count,
            rowset_count,
            result_queue,
        ),
    )
    second = context.Process(
        target=_multiprocess_refresh_worker,
        args=(
            cache_path,
            start_event,
            second_ready,
            False,
            rowset_started,
            release_rowset,
            metadata_count,
            rowset_count,
            result_queue,
        ),
    )
    processes = [first, second]
    first.start()
    assert first_ready.wait(5)
    start_event.set()
    assert rowset_started.wait(5)
    active = json.loads(Path(f"{cache_path}.coordination.json").read_text(encoding="utf-8"))[
        "active_refresh"
    ]
    assert matches_process(
        active["owner_pid"],
        exe_path=active["owner_executable"],
        created_before=datetime.fromisoformat(active["claimed_at_utc"]).timestamp(),
    )
    second.start()
    assert second_ready.wait(5)
    time.sleep(1.0)
    release_rowset.set()
    for process in processes:
        process.join(10)
        assert process.exitcode == 0

    worker_results = [result_queue.get(timeout=2) for _ in processes]
    outcomes = {result[0] for result in worker_results}
    assert any(result[1] is True for result in worker_results)
    assert metadata_count.value == 1
    assert rowset_count.value == 1
    assert outcomes == {"REFRESHED", "REUSED"}


def test_draft_poll_deadline_survives_repository_restart(tmp_path):
    now = [1000.0]
    draft = _publication(state="DRAFT")
    first = _repository(tmp_path / "targets.json", draft, wall_clock=lambda: now[0])
    assert first.refresh().outcome == TargetCacheRefreshOutcome.REFRESHED

    reads: list[int] = []
    second = TargetCacheRepository(
        tmp_path / "targets.json",
        context_provider=lambda: _context(),
        metadata_fetcher=lambda kvk_no: reads.append(kvk_no) or draft.metadata,
        publication_fetcher=lambda _kvk_no: draft,
        wall_clock=lambda: now[0],
    )

    assert second.read_snapshot().publication_state == "DRAFT"
    assert reads == []
    now[0] += 61
    assert second.read_snapshot().publication_state == "DRAFT"
    assert reads == [16]


def test_impossible_future_draft_poll_deadline_is_non_authoritative(tmp_path):
    now = [1000.0]
    draft = _publication(state="DRAFT")
    cache_path = tmp_path / "targets.json"
    first = _repository(cache_path, draft, wall_clock=lambda: now[0])
    assert first.refresh().outcome == TargetCacheRefreshOutcome.REFRESHED

    coordination = json.loads(Path(first.coordination_path).read_text(encoding="utf-8"))
    coordination["draft_poll"]["not_before_utc"] = datetime.fromtimestamp(
        now[0] + 600, UTC
    ).isoformat()
    Path(first.coordination_path).write_text(json.dumps(coordination), encoding="utf-8")

    reads: list[int] = []
    restarted = TargetCacheRepository(
        cache_path,
        context_provider=lambda: _context(),
        metadata_fetcher=lambda kvk_no: reads.append(kvk_no) or draft.metadata,
        publication_fetcher=lambda _kvk_no: draft,
        wall_clock=lambda: now[0],
    )

    assert restarted.read_snapshot().publication_state == "DRAFT"
    assert reads == [16]
    repaired = json.loads(Path(first.coordination_path).read_text(encoding="utf-8"))
    assert datetime.fromisoformat(repaired["draft_poll"]["not_before_utc"]).timestamp() == 1060


def test_explicit_maintenance_bypasses_draft_poll_without_refetching_rows(tmp_path):
    draft = _publication(state="DRAFT")
    metadata_reads: list[int] = []
    rowset_reads: list[int] = []
    repository = TargetCacheRepository(
        tmp_path / "targets.json",
        context_provider=lambda: _context(),
        metadata_fetcher=lambda kvk_no: metadata_reads.append(kvk_no) or draft.metadata,
        publication_fetcher=lambda kvk_no: rowset_reads.append(kvk_no) or draft,
    )

    assert repository.refresh().outcome == TargetCacheRefreshOutcome.REFRESHED
    assert repository.refresh().outcome == TargetCacheRefreshOutcome.REUSED

    assert metadata_reads == [16, 16]
    assert rowset_reads == [16]


def test_dead_owner_is_reclaimed_before_lease_expiry(tmp_path):
    repository = _repository(
        tmp_path / "targets.json",
        process_matcher=lambda *_args, **_kwargs: False,
    )
    Path(repository.coordination_path).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "active_refresh": {
                    "requested_kvk_no": 16,
                    "owner_token": "dead-owner",
                    "owner_pid": 999999,
                    "owner_executable": sys.executable,
                    "claimed_at_utc": datetime.now(UTC).isoformat(),
                    "lease_expires_at_utc": datetime.fromtimestamp(
                        time.time() + 30, UTC
                    ).isoformat(),
                },
            }
        ),
        encoding="utf-8",
    )

    result = repository.refresh()

    assert result.outcome == TargetCacheRefreshOutcome.REFRESHED
    assert result.snapshot.metadata is not None


def test_live_owner_wait_is_bounded_and_fails_closed_without_cache(tmp_path):
    repository = _repository(
        tmp_path / "targets.json",
        process_matcher=lambda *_args, **_kwargs: True,
        follower_wait_seconds=0.02,
        follower_poll_seconds=0.002,
    )
    Path(repository.coordination_path).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "active_refresh": {
                    "requested_kvk_no": 16,
                    "owner_token": "live-owner",
                    "owner_pid": os.getpid(),
                    "owner_executable": sys.executable,
                    "claimed_at_utc": datetime.now(UTC).isoformat(),
                    "lease_expires_at_utc": datetime.fromtimestamp(
                        time.time() + 30, UTC
                    ).isoformat(),
                },
            }
        ),
        encoding="utf-8",
    )

    started = time.monotonic()
    result = repository.refresh()

    assert time.monotonic() - started < 1
    assert result.outcome == TargetCacheRefreshOutcome.FAILED_CLOSED
    assert result.snapshot.publication_state == "UNKNOWN"
    assert result.reason == "coordination_wait_expired"


def test_follower_wait_uses_monotonic_clock_during_wall_clock_rollback(tmp_path):
    wall_now = [1020.0]
    wall_calls = [0]
    monotonic_now = [0.0]

    def rolling_back_wall_clock():
        wall_calls[0] += 1
        if wall_calls[0] > 50:
            raise AssertionError("wall-clock rollback must not extend the follower timeout")
        wall_now[0] -= 0.001
        return wall_now[0]

    def advance_monotonic(seconds):
        monotonic_now[0] += seconds

    repository = _repository(
        tmp_path / "targets.json",
        process_matcher=lambda *_args, **_kwargs: True,
        wall_clock=rolling_back_wall_clock,
        monotonic_clock=lambda: monotonic_now[0],
        sleeper=advance_monotonic,
        follower_wait_seconds=0.006,
        follower_poll_seconds=0.002,
    )
    Path(repository.coordination_path).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "active_refresh": {
                    "requested_kvk_no": 16,
                    "owner_token": "live-owner",
                    "owner_pid": os.getpid(),
                    "owner_executable": sys.executable,
                    "claimed_at_utc": datetime.fromtimestamp(1000, UTC).isoformat(),
                    "lease_expires_at_utc": datetime.fromtimestamp(1050, UTC).isoformat(),
                },
            }
        ),
        encoding="utf-8",
    )

    result = repository.refresh()

    assert result.outcome == TargetCacheRefreshOutcome.FAILED_CLOSED
    assert result.reason == "coordination_wait_expired"
    assert monotonic_now[0] >= 0.006
    assert wall_calls[0] < 50


def test_impossible_future_lease_is_non_authoritative(tmp_path):
    repository = _repository(
        tmp_path / "targets.json",
        process_matcher=lambda *_args, **_kwargs: True,
    )
    now = time.time()
    Path(repository.coordination_path).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "active_refresh": {
                    "requested_kvk_no": 16,
                    "owner_token": "unbounded-owner",
                    "owner_pid": os.getpid(),
                    "owner_executable": sys.executable,
                    "claimed_at_utc": datetime.fromtimestamp(now, UTC).isoformat(),
                    "lease_expires_at_utc": datetime.fromtimestamp(now + 600, UTC).isoformat(),
                },
            }
        ),
        encoding="utf-8",
    )

    result = repository.refresh()

    assert result.outcome == TargetCacheRefreshOutcome.REFRESHED
    assert result.snapshot.metadata is not None


def test_late_owner_cannot_overwrite_after_lease_reclaim(tmp_path):
    cache_path = tmp_path / "targets.json"
    started = threading.Event()
    release = threading.Event()
    older = _publication(version=1)

    def blocked_publication(_kvk_no):
        started.set()
        assert release.wait(5)
        return older

    repository_a = TargetCacheRepository(
        cache_path,
        context_provider=lambda: _context(),
        metadata_fetcher=lambda _kvk_no: older.metadata,
        publication_fetcher=blocked_publication,
        lease_seconds=0.05,
    )
    holder = {}
    thread = threading.Thread(target=lambda: holder.setdefault("result", repository_a.refresh()))
    thread.start()
    assert started.wait(2)
    time.sleep(0.08)

    newer = _repository(cache_path, _publication(version=2), lease_seconds=0.05)
    newer_result = newer.refresh()
    release.set()
    thread.join(5)

    assert newer_result.outcome == TargetCacheRefreshOutcome.REFRESHED
    assert holder["result"].outcome == TargetCacheRefreshOutcome.REJECTED_MISMATCH
    assert holder["result"].snapshot.metadata.publication_version == 2
    persisted = json.loads(cache_path.read_text(encoding="utf-8"))
    assert persisted["_meta"]["publication_version"] == 2


def test_lower_version_and_conflicting_signature_cannot_replace_cache(tmp_path):
    cache_path = tmp_path / "targets.json"
    current = _repository(cache_path, _publication(version=2))
    assert current.refresh().outcome == TargetCacheRefreshOutcome.REFRESHED

    older = _repository(cache_path, _publication(version=1))
    older_result = older.refresh()
    conflict = _repository(
        cache_path,
        _publication(version=2, signature="ffffffff-ffff-ffff-ffff-ffffffffffff"),
    )
    conflict_result = conflict.refresh()

    assert older_result.outcome == TargetCacheRefreshOutcome.REJECTED_MISMATCH
    assert conflict_result.outcome == TargetCacheRefreshOutcome.REJECTED_MISMATCH
    persisted = json.loads(cache_path.read_text(encoding="utf-8"))
    assert persisted["_meta"]["publication_version"] == 2
    assert persisted["_meta"]["publication_signature"] == _metadata(version=2).publication_signature


def test_official_cache_never_downgrades_to_newer_draft(tmp_path):
    cache_path = tmp_path / "targets.json"
    assert _repository(cache_path, _publication(version=2)).refresh().outcome == (
        TargetCacheRefreshOutcome.REFRESHED
    )

    draft = _repository(cache_path, _publication(state="DRAFT", version=3))
    result = draft.refresh()

    assert result.outcome == TargetCacheRefreshOutcome.REJECTED_MISMATCH
    assert result.snapshot.metadata.publication_version == 2
    assert result.snapshot.publication_state == "OFFICIAL"


def test_sql_failure_retains_matching_last_known_good(tmp_path):
    cache_path = tmp_path / "targets.json"
    repository = _repository(cache_path)
    repository.refresh()
    repository._metadata_fetcher = lambda _kvk_no: (_ for _ in ()).throw(
        RuntimeError("temporary SQL outage")
    )

    result = repository.refresh()

    assert result.outcome == TargetCacheRefreshOutcome.RETAINED_LAST_KNOWN_GOOD
    assert result.snapshot.publication_state == "OFFICIAL"
    assert len(result.snapshot.rows) == 2


def test_empty_rowset_fails_closed_without_cache(tmp_path):
    metadata = _metadata()
    repository = TargetCacheRepository(
        tmp_path / "targets.json",
        context_provider=lambda: _context(),
        metadata_fetcher=lambda _kvk_no: metadata,
        publication_fetcher=lambda _kvk_no: None,
    )

    result = repository.refresh()

    assert result.outcome == TargetCacheRefreshOutcome.FAILED_CLOSED
    assert result.snapshot.publication_state == "UNKNOWN"
    assert result.snapshot.rows == ()


def test_malformed_coordination_is_non_authoritative(tmp_path):
    repository = _repository(tmp_path / "targets.json")
    Path(repository.coordination_path).write_text("not-json", encoding="utf-8")

    result = repository.refresh()

    assert result.outcome == TargetCacheRefreshOutcome.REFRESHED
    coordination = json.loads(Path(repository.coordination_path).read_text(encoding="utf-8"))
    assert coordination["schema_version"] == 1
    assert "active_refresh" not in coordination


def test_snapshot_governor_index_is_immutable_and_constant_time(tmp_path):
    snapshot = _repository(tmp_path / "targets.json").refresh().snapshot

    assert snapshot.target_for("123") is snapshot.by_governor["123"]
    with pytest.raises(TypeError):
        snapshot.by_governor["789"] = snapshot.rows[0]  # type: ignore[index]
