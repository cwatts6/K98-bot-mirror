from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

import pytest

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

    def fail(*args):
        raise OSError("disk")

    with monkeypatch.context() as patch:
        patch.setattr(guard, "atomic_write_csv", fail)
        assert not guard.claim_send("prekvk_daily")
    assert log.read_bytes() == before
    assert guard.claim_send("prekvk_daily")
