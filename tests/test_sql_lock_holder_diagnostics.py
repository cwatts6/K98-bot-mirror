"""Optional holder evidence cannot replace or retry an admission refusal."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from core.sql_connection_custody import custody_snapshot
from services import sql_lock_holder_diagnostics as module


def observed_row():
    now = datetime(2026, 11, 9)
    return ["observed", now, 73, now, str(uuid4()), now, 72, now, str(uuid4()), now, "SESSION", "X"]


def observe(rows=None, error=None, close_error=None):
    diagnostic = Mock()
    diagnostic.execute.return_value = diagnostic
    diagnostic.execute.side_effect = error
    diagnostic.fetchmany.return_value = rows if rows is not None else [observed_row()]
    diagnostic.close.side_effect = close_error
    connection = SimpleNamespace(timeout=15, cursor=Mock(return_value=diagnostic))
    original = RuntimeError("private original refusal")
    result = module.observe_holder(
        SimpleNamespace(connection=connection),
        resource=module.SNAPSHOT_RESOURCE,
        requester=73,
        original=original,
    )
    return result, connection, diagnostic, original


def test_observed_holder_is_distinct_born_connection_not_historical_cause():
    result, connection, diagnostic, _ = observe()
    assert result["status"] == "observed_after_refusal"
    assert result["holder"]["session_id"] == 72
    assert result["requester"]["session_id"] == 73
    assert result["holder"]["connection_id"] != result["requester"]["connection_id"]
    assert "private" not in str(result)
    assert connection.timeout == 15
    diagnostic.close.assert_called_once()
    diagnostic.execute.assert_called_once()
    diagnostic.fetchmany.assert_called_once_with(3)


@pytest.mark.parametrize(
    "rows,reason",
    [
        ([], "holder_disappeared_or_ambiguous"),
        ([observed_row(), observed_row()], "holder_disappeared_or_ambiguous"),
        ([("permission_unavailable",)], "permission_unavailable"),
    ],
)
def test_absent_permission_race_or_ambiguity_does_not_guess(rows, reason):
    result, connection, _, _ = observe(rows)
    assert result == dict(status="unavailable", reason=reason)
    assert connection.timeout == 15


@pytest.mark.parametrize(
    "index,value", [(2, 74), (6, 73), (7, None), (8, "secret"), (10, "unexpected")]
)
def test_partial_or_inconsistent_identity_is_unavailable(index, value):
    row = observed_row()
    row[index] = value
    result, _, _, _ = observe([row])
    assert result["status"] == "unavailable"
    assert "secret" not in str(result)


@pytest.mark.parametrize("error", [RuntimeError("secret"), KeyboardInterrupt()])
def test_diagnostic_failure_preserves_original_and_closes(error):
    result, connection, diagnostic, original = observe(error=error)
    assert result == dict(status="unavailable", reason="observation_failed")
    assert connection.timeout == 15
    diagnostic.close.assert_called_once()
    assert type(error).__name__ in original.__notes__[0]
    assert "secret" not in str(result)


def test_unknown_cleanup_retains_custody_and_never_reports_holder():
    result, connection, diagnostic, original = observe(close_error=OSError("private close"))
    assert result == dict(status="unavailable", reason="cleanup_unconfirmed")
    assert custody_snapshot()["unconfirmed"] == 1
    assert original.args == ("private original refusal",)
    from core import sql_connection_custody

    retained = next(iter(sql_connection_custody._holds.values())).retained_connection
    assert retained.connection is connection and retained.cursor is diagnostic


def test_timeout_restoration_failure_retains_cursor_and_first_refusal():
    class Connection:
        timeout = 15

        def __setattr__(self, name, value):
            if name == "timeout" and value == 15:
                raise OSError("private restore")
            object.__setattr__(self, name, value)

    diagnostic = Mock()
    connection = Connection()
    connection.cursor = Mock(return_value=diagnostic)
    original = RuntimeError("first")
    result = module.observe_holder(
        SimpleNamespace(connection=connection),
        resource=module.SNAPSHOT_RESOURCE,
        requester=73,
        original=original,
    )
    assert result == dict(status="unavailable", reason="cleanup_unconfirmed")
    assert custody_snapshot()["unconfirmed"] == 1
    diagnostic.execute.assert_not_called()
    diagnostic.close.assert_called_once()
    assert original.args == ("first",)


def test_truncated_coordination_resource_never_queries_or_guesses():
    cursor = Mock()
    result = module.observe_holder(
        cursor, resource="k98-export:" + "a" * 64, requester=73, original=RuntimeError()
    )
    assert result == dict(status="unavailable", reason="resource_name_truncated")
    assert cursor.mock_calls == []


def test_new_cursor_inherits_one_second_and_original_budget_is_restored_before_query():
    diagnostic = Mock()
    connection = SimpleNamespace(timeout=15)

    def new_cursor():
        assert connection.timeout == 1
        return diagnostic

    def execute(*args):
        assert connection.timeout == 15
        return diagnostic

    connection.cursor = new_cursor
    diagnostic.execute.side_effect = execute
    diagnostic.fetchmany.return_value = []
    module.observe_holder(
        SimpleNamespace(connection=connection),
        resource=module.SNAPSHOT_RESOURCE,
        requester=73,
        original=RuntimeError(),
    )
    assert connection.timeout == 15
