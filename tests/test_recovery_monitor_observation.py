from datetime import UTC, datetime, timedelta

import pytest

from services import recovery_health as health


@pytest.fixture(autouse=True)
def clean_monitor(monkeypatch):
    for name in (
        "_last_success",
        "_failure",
        "_failure_detail",
        "_notification_failure",
        "_cycle",
        "_last_completed_cycle",
        "_last_failed_cycle",
        "_cycle_started",
        "_progress_at",
        "_stage_started",
        "_notifications_started",
    ):
        monkeypatch.setattr(health, name, None)
    monkeypatch.setattr(health, "_checks", [])
    monkeypatch.setattr(health, "_failure_streak", 0)


def test_long_progress_is_live_but_does_not_certify_old_results(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(health.time, "monotonic", lambda: clock[0])
    health.record_success()
    health._last_success = datetime.now(UTC) - timedelta(seconds=131)
    health.begin_cycle()
    clock[0] = 100.7
    health.record_progress("registration_admission")
    row = health.observation()
    assert row["observer_state"] == "progressing"
    assert row["check_state"] == "stale" and not row["healthy"]
    assert "unavailable" not in row["status"]
    assert not health.outage_notification_due()
    health.record_success()
    assert health.observation()["last_completed_cycle"]["elapsed_seconds"] == 100.7


def test_failure_survives_next_cycle_and_recovery_without_remaining_active(caplog):
    health.begin_cycle()
    try:
        raise ValueError("secret SQL payload")
    except ValueError as exc:
        original = health.record_check("discovery:private_evidence", exc)
    health.record_failure(RuntimeError("aggregate"))
    health.begin_cycle()
    row = health.observation()
    assert row["checks"] == []
    assert row["last_failed_cycle"]["checks"] == [original]
    row["last_failed_cycle"]["checks"].clear()
    assert health.observation()["last_failed_cycle"]["checks"] == [original]
    health.record_success()
    row = health.observation()
    assert row["healthy"] and row["check_failure"] is None
    assert row["last_failed_cycle"]["recovered_utc"]
    assert row["last_failed_cycle"]["checks"] == [original]
    assert "secret SQL payload" not in caplog.text + str(row)
    assert "discovery:private_evidence" in caplog.text


def test_stall_and_total_cycle_limit_do_not_need_wall_clock_progress(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(health.time, "monotonic", lambda: clock[0])
    health.begin_cycle()
    clock[0] = health.STALL_SECONDS + 1
    assert health.observation()["observer_state"] == "stalled"
    health.record_progress("next")
    assert health.observation()["observer_state"] == "progressing"
    clock[0] = health.CYCLE_SECONDS + 1
    health.record_progress("still_working")
    assert health.observation()["observer_state"] == "stalled"
    assert not health.observation()["healthy"]


def test_transient_episode_degrades_immediately_but_notifies_after_repeat():
    for attempt in (1, 2):
        health.begin_cycle()
        health.record_check("discovery:private_evidence", TimeoutError())
        health.record_failure(RuntimeError())
        assert not health.observation()["healthy"]
        assert health.outage_notification_due() is (attempt == 2)
    health.record_success()
    assert not health.outage_notification_due()
    health.begin_cycle()
    health.record_check("discovery:private_evidence", PermissionError())
    health.record_failure(RuntimeError())
    assert health.outage_notification_due()


def test_waiting_and_truncation_are_retained_without_certifying_completion():
    health.begin_cycle()
    for _ in range(102):
        health.record_check("admission", TimeoutError(), waiting=True)
    row = health.observation()
    assert row["observer_state"] == "waiting"
    assert not row["healthy"]
    health.record_failure(RuntimeError())
    health.begin_cycle()
    prior = health.observation()["last_failed_cycle"]
    assert len(prior["checks"]) == 100
    assert prior["omitted_checks"] == 2


def test_current_failed_check_degrades_before_cycle_aggregation():
    health.record_success()
    health.begin_cycle()
    health.record_check("discovery:private_evidence", PermissionError())
    row = health.observation()
    assert row["observer_state"] == "progressing"
    assert row["check_state"] == "failed" and not row["healthy"]


def test_notification_time_is_separate_from_inspection(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(health.time, "monotonic", lambda: clock[0])
    health.begin_cycle()
    clock[0] = 100.7
    health.record_success()
    health.begin_notifications()
    clock[0] += 5
    health.record_notifications()
    row = health.observation()["last_completed_cycle"]
    assert row["elapsed_seconds"] == 100.7
    assert row["notification_seconds"] == 5


def test_distinct_transient_causes_do_not_count_as_repeated_identical_failure(caplog):
    for stage in ("first", "second"):
        health.begin_cycle()
        for _ in range(3):
            health.record_check(stage, TimeoutError())
        health.record_failure(RuntimeError())
        assert not health.outage_notification_due()
    assert caplog.text.count("recovery_check_failed diagnostic=") == 2
