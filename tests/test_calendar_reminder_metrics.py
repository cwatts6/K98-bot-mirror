from __future__ import annotations

from event_calendar.reminder_metrics import get_reminder_status_service


class _Summary:
    ok = True
    status = "completed"
    candidates = 10
    attempted = 4
    sent = 3
    skipped_prefs = 2
    skipped_already_sent = 1
    skipped_unknown_type = 0
    failures = 1
    failed_forbidden = 1
    failed_not_found = 0
    failed_http_exception = 0
    failed_unknown = 0


def test_reminder_status_service_records_summary() -> None:
    svc = get_reminder_status_service()
    svc.record_summary(summary=_Summary(), dry_run=False)
    payload = svc.get_status()

    assert payload["status"] == "completed"
    assert payload["ok"] is True
    assert payload["dry_run"] is False
    assert payload["candidates"] == 10
    assert payload["attempted"] == 4
    assert payload["sent"] == 3
    assert payload["failures"] == 1
    assert payload["failed_forbidden"] == 1
    assert payload["last_dispatch_utc"] != "not_started"


def test_reminder_status_service_records_failure() -> None:
    svc = get_reminder_status_service()
    svc.record_failure(
        status="loop_iteration_failed", error_message="RuntimeError: boom", dry_run=True
    )
    payload = svc.get_status()

    assert payload["status"] == "loop_iteration_failed"
    assert payload["ok"] is False
    assert payload["dry_run"] is True
    assert "error_message" in payload
