"""Receipt truthfulness and physical cleanup for the explicit maintenance owner."""

import asyncio
from copy import deepcopy
import threading
from types import SimpleNamespace
from uuid import uuid4

import pytest

from core import sql_connection_custody as custody
from services import maintenance_dal as dal, maintenance_service as service


def receipt(state="complete"):
    return {
        "request_id": str(uuid4()),
        "maintenance": [
            dict(
                zip(
                    dal.FIELDS,
                    (
                        "post_import",
                        1,
                        int(state == "complete"),
                        1,
                        str(uuid4()),
                        state,
                        None,
                        None,
                    ),
                    strict=True,
                )
            )
        ],
    }


@pytest.fixture
def connection(monkeypatch):
    # No uncertainty created by an isolated fake may leak into other tests.
    monkeypatch.setattr(custody, "_holds", {})
    events = []
    result = receipt()

    class Cursor:
        description = tuple((field,) for field in dal.FIELDS)

        def execute(self, statement, request=None):
            events.append((statement, request) if request else statement)
            assert owner.timeout == 17

        def fetchone(self):
            return (0, "NoLock", "NoLock", "NoLock", "NoLock", "NoLock")

        def fetchmany(self, size):
            assert size == 7
            return [tuple(row[field] for field in dal.FIELDS) for row in result["maintenance"]]

        def nextset(self):
            events.append("response_consumed")
            return False

        def close(self):
            events.append("cursor_closed")

    class Connection:
        autocommit = False
        timeout = None

        def cursor(self):
            assert self.timeout == 17
            return cursor

        def close(self):
            events.append("closed")

    cursor, owner = Cursor(), Connection()
    return SimpleNamespace(owner=owner, cursor=cursor, events=events, result=result)


def test_exact_receipt_consumed_before_cleanup(connection):
    c = connection
    request = str(uuid4())
    result = dal.run_maintenance(lambda: c.owner, timeout_seconds=17, request_id=request)
    assert result == dict(c.result, request_id=request)
    assert c.events == [
        dal.SESSION_STATE,
        ("EXEC dbo.usp_update_stats @RequestID=?", request),
        "response_consumed",
        dal.RELEASE_SESSION,
        "response_consumed",
        "cursor_closed",
        "closed",
    ]


@pytest.mark.parametrize("state", ["pending", "running", "unknown", "failed"])
def test_outstanding_maintenance_never_becomes_completed_business_evidence(state):
    value = service.result(receipt(state))
    assert value[0] is False
    evidence, verified = service.evidence(value)
    assert not verified
    assert evidence["outcome"] == "maintenance_outstanding"


@pytest.mark.parametrize("phase", ["cursor", "connection"])
def test_cleanup_failure_retains_connection_and_blocks_admission(connection, monkeypatch, phase):
    c = connection
    target = c.cursor if phase == "cursor" else c.owner

    def fail():
        raise OSError("close acknowledgement lost")

    monkeypatch.setattr(target, "close", fail)
    with pytest.raises(OSError):
        dal.run_maintenance(lambda: c.owner, timeout_seconds=17)
    assert custody.custody_snapshot() == {"admission": "closed", "unconfirmed": 1}
    assert "closed" not in c.events
    assert custody.connection_retained(c.owner)
    with pytest.raises(custody.SqlCleanupUnknown):
        dal.run_maintenance(lambda: pytest.fail("must not connect"))


def test_late_sql_failure_survives_failed_cleanup(connection, monkeypatch):
    c = connection
    first = RuntimeError("late result failure")
    raised = False

    def late():
        nonlocal raised
        if not raised:
            raised = True
            raise first
        return False

    def close():
        raise OSError("cleanup failed")

    monkeypatch.setattr(c.cursor, "nextset", late)
    monkeypatch.setattr(c.owner, "close", close)
    with pytest.raises(RuntimeError) as error:
        dal.run_maintenance(lambda: c.owner, timeout_seconds=17)
    assert error.value is first
    assert "SQL close failed: OSError" in first.__notes__


def test_foreign_session_owner_is_retained_without_releasing_it(connection, monkeypatch):
    c = connection
    monkeypatch.setattr(
        c.cursor, "fetchone", lambda: (0, "Exclusive", "NoLock", "NoLock", "NoLock", "NoLock")
    )
    with pytest.raises(custody.SqlCleanupUnknown, match="pre-existing"):
        dal.run_maintenance(lambda: c.owner, timeout_seconds=17)
    assert c.events == [dal.SESSION_STATE]
    assert custody.custody_snapshot()["admission"] == "closed"


def test_unknown_session_release_never_returns_connection_to_pool(connection, monkeypatch):
    c = connection
    original = c.cursor.execute

    def execute(statement, request=None):
        if statement == dal.RELEASE_SESSION:
            raise OSError("release acknowledgement lost")
        return original(statement, request)

    monkeypatch.setattr(c.cursor, "execute", execute)
    with pytest.raises(OSError, match="acknowledgement lost"):
        dal.run_maintenance(lambda: c.owner, timeout_seconds=17)
    assert "cursor_closed" not in c.events
    assert "closed" not in c.events
    assert custody.custody_snapshot()["admission"] == "closed"


@pytest.mark.parametrize("damage", ["missing", "duplicate", "invalid_state", "false_complete"])
def test_unverified_or_invalid_receipts_refused(connection, damage):
    rows = connection.result["maintenance"]
    if damage == "missing":
        rows.clear()
    elif damage == "duplicate":
        rows.append(deepcopy(rows[0]))
    elif damage == "invalid_state":
        rows[0]["State"] = "success"
    else:
        rows[0]["CompletedGeneration"] = 0
    with pytest.raises(ValueError):
        dal.run_maintenance(lambda: connection.owner, timeout_seconds=17)
    assert connection.events[-1] == "closed"


@pytest.mark.asyncio
async def test_plain_maintenance_cancellation_drains_the_physical_worker(monkeypatch):
    import file_utils

    entered, release, ended = threading.Event(), threading.Event(), threading.Event()

    def worker(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        ended.set()
        return receipt()

    monkeypatch.setattr(file_utils, "run_post_import_stats_update", worker)
    task = asyncio.create_task(
        file_utils.run_maintenance_with_isolation("post_stats", prefer_process=False)
    )
    try:
        assert await asyncio.to_thread(entered.wait, 5)
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
        assert not ended.is_set()
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert ended.is_set()
