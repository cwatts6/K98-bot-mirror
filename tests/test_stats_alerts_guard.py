from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pytest

import file_utils
from stats_alerts import guard


@pytest.fixture
def log(monkeypatch, tmp_path):
    path = tmp_path / "log.csv"
    monkeypatch.setattr(guard, "LOG_PATH", str(path))
    monkeypatch.setattr(guard, "utcnow", lambda: datetime(2026, 9, 8, 12, tzinfo=UTC))
    return path


@pytest.mark.parametrize(
    "content",
    [
        "2026-09-08,11:00:00\n",
        "date,time_utc,kind\n2026-09-08,11:00:00,offseason_daily\n",
        "2026-09-08,11:00:00,offseason_daily\n\nbad\n",
    ],
)
def test_legacy_rows_and_claims_preserve_contract(log, content):
    log.write_text(content, encoding="utf-8")
    assert guard.sent_today("offseason_daily")
    assert guard.sent_today_any(["offseason_daily", "offseason_weekly"])
    assert not guard.claim_send("offseason_daily")
    assert guard.claim_send("kvk", max_per_day=3)
    assert guard.claim_send("kvk", max_per_day=3)
    assert guard.claim_send("kvk", max_per_day=3)
    assert not guard.claim_send("kvk", max_per_day=3)
    assert log.read_text().splitlines()[0] == "date,time_utc,kind"


def test_migration_and_distinct_claims_do_not_lose_rows(log):
    log.write_text("2026-09-07,11:00:00\n", encoding="utf-8")

    def run(index):
        if index % 2:
            guard.ensure_log_exists()
        else:
            assert guard.claim_send(f"kind-{index}")

    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(run, range(12)))
    rows = list(guard.iter_log_rows())
    assert len(rows) == 7
    assert rows[0]["kind"] == "offseason_daily"


def test_failed_write_releases_lock_and_preserves_csv(log, monkeypatch):
    guard.ensure_log_exists()
    before = log.read_bytes()

    def fail(*args, **kwargs):
        raise OSError("disk")

    with monkeypatch.context() as patch:
        patch.setattr(guard, "atomic_write_csv", fail)
        assert not guard.claim_send("prekvk_daily")
    assert log.read_bytes() == before
    assert guard.claim_send("prekvk_daily")


@pytest.mark.parametrize("operation", ["create", "migrate", "append"])
def test_csv_sharing_retry_keeps_lock_and_serializes_rows_once(log, monkeypatch, operation):
    if operation == "migrate":
        log.write_text("2026-09-07,11:00:00\n", encoding="utf-8")
    elif operation == "append":
        guard.ensure_log_exists()
    original_replace = file_utils.os.replace
    original_fsync = file_utils.os.fsync
    attempts, writes = [], []
    monkeypatch.setattr(guard, "LOCK_TIMEOUT_SECONDS", 0)

    def replace(source, target):
        assert Path(target) == log
        # A contender must remain excluded for the entire retry sequence.
        with pytest.raises(TimeoutError):
            with guard.coordination_lock():
                pytest.fail("retry released the coordination lock")
        attempts.append(Path(source).read_bytes())
        if len(attempts) < 3:
            error = PermissionError("sharing violation")
            error.winerror = 32
            raise error
        return original_replace(source, target)

    def fsync(fd):
        writes.append(fd)
        return original_fsync(fd)

    monkeypatch.setattr(file_utils.os, "replace", replace)
    monkeypatch.setattr(file_utils.os, "fsync", fsync)
    monkeypatch.setattr(file_utils.time, "sleep", lambda _: None)
    if operation == "append":
        assert guard.claim_send("prekvk_daily")
    else:
        guard.ensure_log_exists()
    assert len(attempts) == 3
    assert attempts[0] == attempts[1] == attempts[2]
    assert len(writes) == 1
    assert not log.with_suffix(".csv.tmp").exists()
    rows = list(guard.iter_log_rows())
    assert len(rows) == (0 if operation == "create" else 1)


@pytest.mark.parametrize("winerror,expected_attempts", [(32, 5), (5, 1)])
def test_csv_replacement_failure_preserves_success_log(
    log, monkeypatch, winerror, expected_attempts
):
    guard.ensure_log_exists()
    before = log.read_bytes()
    attempts = []

    def fail(*args):
        attempts.append(args)
        error = PermissionError("access failure")
        error.winerror = winerror
        raise error

    with monkeypatch.context() as patch:
        patch.setattr(file_utils.os, "replace", fail)
        patch.setattr(file_utils.time, "sleep", lambda _: None)
        assert not guard.claim_send("prekvk_daily")
    assert len(attempts) == expected_attempts
    assert log.read_bytes() == before
    assert guard.claim_send("prekvk_daily")  # lock released after final error
    assert len(list(guard.iter_log_rows())) == 1


def test_other_csv_callers_keep_single_attempt_default(log, monkeypatch):
    attempts = []

    def fail(*args):
        attempts.append(args)
        error = PermissionError("sharing violation")
        error.winerror = 32
        raise error

    monkeypatch.setattr(file_utils.os, "replace", fail)
    with pytest.raises(PermissionError):
        file_utils.atomic_write_csv(log, guard.HEADER, [])
    assert len(attempts) == 1
