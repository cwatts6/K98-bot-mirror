import asyncio
from datetime import UTC, datetime
import threading

import pytest

from event_calendar import audit_dal, service
from event_calendar.audit_dal import AuditResult
from event_calendar.mutation_owner import get_owner
from event_calendar.sheets_sync import SyncResult
from event_calendar.sql_lifecycle import SqlOutcome
from event_calendar.sync_audit import SyncAudit


def acknowledged(sync_id=42):
    return AuditResult(sync_id, SqlOutcome(effect="committed", cleanup="settled"))


async def wait_entered(event):
    for _ in range(2000):
        if event.is_set():
            return
        await asyncio.sleep(0.001)
    raise AssertionError("worker did not enter")


@pytest.mark.asyncio
async def test_blocked_start_never_gates_business_and_finish_binds_exact_id(monkeypatch):
    entered, release = threading.Event(), threading.Event()
    calls = []

    def start(*args):
        entered.set()
        assert release.wait(5)
        return acknowledged(731)

    def finish(sync_id, result, completed):
        calls.append((sync_id, result))
        return acknowledged(sync_id)

    monkeypatch.setattr(audit_dal, "start", start)
    monkeypatch.setattr(audit_dal, "finish", finish)
    monkeypatch.setattr(
        service,
        "sync_sheets_to_sql",
        lambda *a: SyncResult(True, "success", rows_upserted_oneoff=12),
    )
    try:
        output = await service.CalendarService().refresh(sheet_id="offline")
        await wait_entered(entered)
        assert output["ok"] and output["rows_upserted_oneoff"] == 12
        assert not calls
        assert get_owner().active is None
        assert get_owner().audit.offer("another", datetime.now(UTC)) is None
    finally:
        release.set()
        assert await get_owner().audit.drain()
    assert len(calls) == 1 and calls[0][0] == 731
    assert calls[0][1]["rows_upserted_oneoff"] == 12


@pytest.mark.asyncio
@pytest.mark.parametrize("effect", ["not_started", "rolled_back", "unknown"])
async def test_start_failure_never_rebinds_or_finishes(monkeypatch, effect):
    calls = []
    monkeypatch.setattr(
        audit_dal,
        "start",
        lambda *a: AuditResult(
            None,
            SqlOutcome(effect=effect, cleanup="settled", error={"error_type": "PermissionError"}),
        ),
    )
    monkeypatch.setattr(audit_dal, "finish", lambda *a: calls.append(a))
    audit = SyncAudit()
    ticket = audit.offer("test", datetime.now(UTC))
    audit.finish(ticket, {"status": "success"}, datetime.now(UTC))
    assert await audit.drain()
    assert audit.state == "failed" and not calls
    assert audit.first_error == {"error_type": "PermissionError"}


@pytest.mark.asyncio
async def test_audit_close_failure_retains_only_optional_slot(monkeypatch):
    connection = object()
    monkeypatch.setattr(
        audit_dal,
        "start",
        lambda *a: AuditResult(
            1,
            SqlOutcome(
                effect="committed",
                cleanup="unconfirmed",
                retained_connection=connection,
                cleanup_error={"error_type": "RuntimeError"},
            ),
        ),
    )
    monkeypatch.setattr(service, "sync_sheets_to_sql", lambda *a: SyncResult(True, "success"))
    svc = service.CalendarService()
    assert (await svc.refresh(sheet_id="offline"))["ok"]
    audit = get_owner().audit
    assert not await audit.drain()
    assert audit.retained.sql.retained_connection is connection
    assert (await svc.refresh(sheet_id="offline"))["ok"]
    assert audit.dropped == 1
    assert not (await svc.drain())["ok"]


@pytest.mark.asyncio
async def test_finish_failure_retains_first_error_and_no_retry(monkeypatch):
    calls = []
    monkeypatch.setattr(audit_dal, "start", lambda *a: acknowledged())

    def finish(*args):
        calls.append(args)
        return AuditResult(
            42,
            SqlOutcome(effect="unknown", cleanup="settled", error={"error_type": "TimeoutError"}),
        )

    monkeypatch.setattr(audit_dal, "finish", finish)
    audit = SyncAudit()
    ticket = audit.offer("test", datetime.now(UTC))
    audit.finish(ticket, {"status": "success", "rows_upserted_recurring": 17}, datetime.now(UTC))
    assert await audit.drain()
    assert len(calls) == 1 and calls[0][1]["rows_upserted_recurring"] == 17
    assert audit.snapshot()["first_error"] == {"error_type": "TimeoutError"}
    audit.close_admission()
    assert audit.offer("late", datetime.now(UTC)) is None
