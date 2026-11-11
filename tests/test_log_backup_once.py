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
    cursor.fetchmany.return_value = [(1, 0, 1)]
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
    cursor.fetchmany.return_value = [(wrapper, 1, 1 if wrapper else None)]
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
    cursor.fetchmany.side_effect = RuntimeError("route")
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


@pytest.mark.parametrize("visibility", [0, None])
@pytest.mark.parametrize("job_id", [None, "configured-job"])
def test_hidden_or_unknown_wrapper_never_selects_fallback(provider, visibility, job_id):
    cursor, _ = provider
    cursor.fetchmany.return_value = [(None, visibility, None)]
    result = log_backup.request_once(cursor, job_id=job_id)
    assert result["outcome"] == "not_attempted"
    assert "used_method" not in result
    assert cursor.execute.call_count == 1


@pytest.mark.parametrize("execute_right", [0, None])
def test_visible_but_inaccessible_wrapper_is_not_dispatched(provider, execute_right):
    cursor, _ = provider
    cursor.fetchmany.return_value = [(1, 1, execute_right)]
    assert log_backup.request_once(cursor)["outcome"] == "not_attempted"
    assert cursor.execute.call_count == 1


@pytest.mark.parametrize("rows", [[], [(1,)], [(1, 1, 1), (2, 1, 1)]])
def test_unacknowledged_or_ambiguous_route_never_dispatches(provider, rows):
    cursor, _ = provider
    cursor.fetchmany.return_value = rows
    assert log_backup.request_once(cursor)["outcome"] == "not_attempted"
    assert cursor.execute.call_count == 1


def test_pre_admission_inspection_uses_msdb_context_without_changing_caller_database(provider):
    cursor, _ = provider
    log_backup.request_once(cursor)
    assert cursor.execute.call_args_list[0].args == (log_backup.BACKUP_ROUTE_QUERY,)
    assert log_backup.BACKUP_ROUTE_QUERY.startswith("EXEC msdb.sys.sp_executesql N'")
    assert "USE " not in log_backup.BACKUP_ROUTE_QUERY
