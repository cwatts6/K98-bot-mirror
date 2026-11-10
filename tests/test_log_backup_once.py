"""Provider responses are simulated; no SQL Agent job or backup is executed."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from core import sql_connection_custody as custody
import log_backup


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setattr(custody, "_holds", {})
    for key in ("SQL_MONITOR_SERVER", "SQL_MONITOR_USERNAME", "SQL_MONITOR_PASSWORD"):
        monkeypatch.setenv(key, "test")
    monkeypatch.delenv("SQL_MONITOR_JOB_ID", raising=False)
    cursor = Mock()
    cursor.fetchone.return_value = (1,)
    cursor.nextset.return_value = False
    connection = Mock()
    connection.cursor.return_value = cursor
    monkeypatch.setattr(
        log_backup, "pyodbc", SimpleNamespace(connect=Mock(return_value=connection))
    )
    return cursor, connection


@pytest.mark.parametrize(
    "wrapper,jobid,method",
    [(1, None, "wrapper"), (None, "abc", "job_id"), (None, None, "job_name")],
)
def test_one_route_is_selected_before_dispatch(provider, monkeypatch, wrapper, jobid, method):
    cursor, _ = provider
    cursor.fetchone.return_value = (wrapper,)
    if jobid:
        monkeypatch.setenv("SQL_MONITOR_JOB_ID", jobid)
    result = log_backup.trigger_log_backup_sync()
    assert result["outcome"] == "requested" and result["backup_completed"] is None
    assert result["used_method"] == method
    assert cursor.execute.call_count == 2


@pytest.mark.parametrize("phase", ["execute", "nextset"])
def test_lost_dispatch_ack_never_falls_back(provider, phase):
    cursor, _ = provider
    getattr(cursor, phase).side_effect = [None, RuntimeError("private provider response")]
    result = log_backup.trigger_log_backup_sync()
    assert result["outcome"] == "unknown" and not result["ok"]
    assert cursor.execute.call_count == 2
    assert "private" not in str(result)


def test_route_failure_is_not_attempted(provider):
    cursor, _ = provider
    cursor.fetchone.side_effect = RuntimeError("route")
    assert log_backup.trigger_log_backup_sync()["outcome"] == "not_attempted"
    assert cursor.execute.call_count == 1


def test_pre_admission_equivalent_caller_never_blind_falls_back(provider):
    import log_health

    cursor, _ = provider
    cursor.execute.side_effect = [None, RuntimeError("ack lost")]
    assert not log_health._trigger_log_backup(cursor)
    assert cursor.execute.call_count == 2


def test_cleanup_loss_retains_acknowledged_outcome_and_handles(provider):
    cursor, connection = provider
    cursor.close.side_effect = RuntimeError("cleanup")
    result = log_backup.trigger_log_backup_sync()
    assert result["outcome"] == "requested" and result["cleanup"] == "unconfirmed"
    connection.close.assert_not_called()
    assert custody.custody_snapshot()["admission"] == "closed"
