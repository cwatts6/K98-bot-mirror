"""Actual statement budget and first-failure custody across player report callers."""

from inspect import unwrap
from unittest.mock import MagicMock, Mock

import pytest

from core.sql_connection_custody import SqlCleanupUnknown, custody_snapshot
from core.sql_operation_policy import player_statement_seconds
from kvk.dal.new_source_import_dal import UncertainCommit
import player_stats_cache as cache
from services.player_report_sql import player_connection, player_report_cursor


@pytest.mark.parametrize(
    "requested,inherited,expected", [(300, 15, 15), (300, 0, 15), (5, 15, 5), (300, 3, 3)]
)
def test_budget_never_raises_existing_limit(requested, inherited, expected):
    assert player_statement_seconds(requested, inherited) == expected


@pytest.mark.parametrize(
    "requested,inherited", [(0, 15), (-1, 15), (True, 15), (15, -1), (15, None)]
)
def test_invalid_budget_is_not_an_unbounded_statement(requested, inherited):
    with pytest.raises(ValueError):
        player_statement_seconds(requested, inherited)


@pytest.fixture
def connection(monkeypatch):
    cn = MagicMock(autocommit=False, timeout=15)
    cur = cn.cursor.return_value
    cur.execute.return_value = cur
    cur.nextset.return_value = False
    monkeypatch.setattr(cache, "current_owner", lambda: None)
    monkeypatch.setattr(cache, "record_writer_completion", Mock())
    monkeypatch.setattr(cache.time, "sleep", Mock())
    import services.legacy_export_snapshot_service as legacy

    for name in ("verify_producer_cursor", "begin_writer_transaction", "record_writer_stage"):
        monkeypatch.setattr(legacy, name, Mock())
    return cn


def test_cursor_copies_limit_before_creation_restores_connection_and_uses_row_budget(connection):
    cn = connection
    cur = cn.cursor.return_value

    def cursor():
        assert cn.timeout == 15
        return cur

    cn.cursor.side_effect = cursor
    unwrap(cache._execute_sp_with_retries)(cn, retries=1)
    assert cur.execute.call_args_list[0].args == ("SET LOCK_TIMEOUT 1000;",)
    assert cur.execute.call_args_list[1].args == (cache._SQL_EXEC_SP,)
    cn.commit.assert_called_once()
    cur.close.assert_called_once()
    assert cn.timeout == 15


def test_lower_limit_is_not_leaked_to_other_cursors(connection):
    cn = connection
    cur = cn.cursor.return_value

    def create():
        assert cn.timeout == 2
        return cur

    cn.cursor.side_effect = create
    with player_report_cursor(cn, requested=2) as (_, seconds):
        assert seconds == 2 and cn.timeout == 15
    cur.close.assert_called_once()


@pytest.mark.parametrize(
    "phase", ["commit", "post_commit_close", "rollback", "interrupt", "driver_cancel"]
)
def test_uncertain_or_cancelled_report_never_retries(connection, phase):
    cn = connection
    cur = cn.cursor.return_value
    original = OSError("private failure")
    expected = UncertainCommit if phase == "commit" else SqlCleanupUnknown
    if phase == "commit":
        cn.commit.side_effect = original
    elif phase == "post_commit_close":
        cur.close.side_effect = original
    elif phase == "rollback":
        cur.execute.side_effect = original
        cn.rollback.side_effect = OSError("private rollback")
    elif phase == "driver_cancel":
        original = cache.pyodbc.Error("HY008", "cancelled")
        cur.execute.side_effect = original
        expected = cache.pyodbc.Error
    else:
        original = KeyboardInterrupt()
        cur.execute.side_effect = original
        expected = KeyboardInterrupt
    with pytest.raises(expected) as caught:
        unwrap(cache._execute_sp_with_retries)(cn, retries=3)
    assert cn.cursor.call_count == 1
    cur.close.assert_called_once()
    cache.time.sleep.assert_not_called()
    if phase in {"rollback", "post_commit_close"}:
        assert custody_snapshot()["unconfirmed"]
    if phase == "commit":
        assert caught.value.__cause__ is original
    if phase == "interrupt":
        assert caught.value is original


def test_acknowledged_precommit_rollback_can_use_existing_retry(connection):
    cn = connection
    cur = cn.cursor.return_value
    cur.execute.side_effect = [None, OSError("body"), None, None]
    unwrap(cache._execute_sp_with_retries)(cn, retries=2)
    assert cn.cursor.call_count == 2 and cur.close.call_count == 2
    cn.rollback.assert_called_once()
    cn.commit.assert_called_once()


def test_owned_connection_rolls_back_and_closes_without_implicit_context_commit(
    connection, monkeypatch
):
    monkeypatch.setattr("file_utils.get_conn_with_retries", lambda **_: connection)
    with player_connection(operation="player_stats_cache") as cn:
        assert cn is connection
    connection.rollback.assert_called_once()
    connection.close.assert_called_once()
    connection.commit.assert_not_called()
    connection.__exit__.assert_not_called()


def test_connection_close_failure_retains_first_body_failure(connection, monkeypatch):
    monkeypatch.setattr("file_utils.get_conn_with_retries", lambda **_: connection)
    connection.close.side_effect = OSError("close")
    first = ValueError("body")
    with pytest.raises(SqlCleanupUnknown) as caught:
        with player_connection(operation="guided_player_report"):
            raise first
    assert caught.value.__cause__ is first
    assert custody_snapshot()["unconfirmed"] == 1


def test_unknown_report_commit_cannot_fall_back_to_old_sql_cache(connection, monkeypatch):
    monkeypatch.setattr("file_utils.get_conn_with_retries", lambda **_: connection)
    monkeypatch.setattr(
        cache, "_execute_sp_with_retries", Mock(side_effect=UncertainCommit("unknown"))
    )
    with pytest.raises(UncertainCommit):
        cache._build_cache_sync(refresh=True)
    connection.cursor.assert_not_called()
    connection.rollback.assert_called_once()
    connection.close.assert_called_once()


def test_guided_caller_closes_its_owned_connection(connection, monkeypatch):
    from services.player_report_continuation import PlayerReportContinuation

    monkeypatch.setattr("file_utils.get_conn_with_retries", lambda **_: connection)
    report = Mock()
    monkeypatch.setattr(cache, "_execute_sp_with_retries", report)
    PlayerReportContinuation._run()
    report.assert_called_once_with(connection, retries=1)
    connection.close.assert_called_once()
    connection.commit.assert_not_called()
