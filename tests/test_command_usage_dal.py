# tests/test_command_usage_dal.py
"""
Unit tests for telemetry/dal/command_usage_dal.py.
No live database required — all SQL is mocked.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from constants import USAGE_TABLE
from telemetry.dal.command_usage_dal import (
    ctx_filter_sql,
    fetch_usage_detail,
    fetch_usage_summary,
    flush_events,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_event(**overrides) -> dict:
    evt = {
        "executed_at_utc": "2026-04-21T12:00:00+00:00",
        "command_name": "test_cmd",
        "version": "v1",
        "app_context": "slash",
        "user_id": 123456789,
        "user_display": "TestUser",
        "guild_id": 987654321,
        "channel_id": 111222333,
        "success": True,
        "error_code": None,
        "latency_ms": 42,
        "args_shape": None,
        "error_text": None,
    }
    evt.update(overrides)
    return evt


def _make_mock_conn(executemany_side_effect=None, execute_side_effect=None):
    """Return a mock connection whose cursor behaves as configured."""
    mock_cur = MagicMock()
    if executemany_side_effect is not None:
        mock_cur.executemany.side_effect = executemany_side_effect
    if execute_side_effect is not None:
        mock_cur.execute.side_effect = execute_side_effect

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    return mock_conn, mock_cur


# ---------------------------------------------------------------------------
# flush_events tests
# ---------------------------------------------------------------------------


def test_flush_events_happy_path():
    """Batch executemany succeeds — commit called once."""
    mock_conn, mock_cur = _make_mock_conn()
    with patch("telemetry.dal.command_usage_dal._get_conn", return_value=mock_conn):
        flush_events([_minimal_event()])

    mock_cur.executemany.assert_called_once()
    mock_conn.commit.assert_called_once()


def test_flush_events_batch_fails_per_row_salvage():
    """executemany raises, per-row execute succeeds — commit still called."""
    mock_conn_batch, _ = _make_mock_conn(executemany_side_effect=Exception("batch fail"))
    mock_conn_per_row, mock_cur_per_row = _make_mock_conn()

    call_count = [0]

    def _get_conn_side_effect():
        call_count[0] += 1
        if call_count[0] == 1:
            return mock_conn_batch
        return mock_conn_per_row

    with patch("telemetry.dal.command_usage_dal._get_conn", side_effect=_get_conn_side_effect):
        flush_events([_minimal_event()])

    mock_cur_per_row.execute.assert_called_once()
    mock_conn_per_row.commit.assert_called_once()


def test_flush_events_total_failure_logs_dropped_count(caplog):
    """Both paths raise — a WARNING with the dropped count is logged; 'retry later' must NOT appear."""
    mock_conn, _ = _make_mock_conn(
        executemany_side_effect=Exception("fail"),
        execute_side_effect=Exception("fail"),
    )

    events = [_minimal_event(command_name="ping"), _minimal_event(command_name="status")]

    with patch("telemetry.dal.command_usage_dal._get_conn", return_value=mock_conn):
        with caplog.at_level(logging.WARNING, logger="telemetry.dal.command_usage_dal"):
            flush_events(events)

    dropped_log = " ".join(caplog.messages)
    assert "2" in dropped_log, "Expected dropped count (2) in log message"
    assert "retry later" not in dropped_log.lower(), "Misleading 'retry later' text found"


def test_flush_events_uses_USAGE_TABLE_constant():
    """The INSERT SQL passed to executemany must reference the USAGE_TABLE constant."""
    captured_sql = []

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    def _capture_executemany(sql, rows):
        captured_sql.append(sql)

    mock_cur.executemany.side_effect = _capture_executemany

    with patch("telemetry.dal.command_usage_dal._get_conn", return_value=mock_conn):
        flush_events([_minimal_event()])

    assert len(captured_sql) == 1
    assert (
        USAGE_TABLE in captured_sql[0]
    ), f"Expected USAGE_TABLE={USAGE_TABLE!r} in SQL, got: {captured_sql[0]!r}"


def test_flush_events_nullable_user_fields():
    """user_id=None and user_display=None must not raise and must call executemany."""
    mock_conn, mock_cur = _make_mock_conn()
    with patch("telemetry.dal.command_usage_dal._get_conn", return_value=mock_conn):
        # Should not raise
        flush_events([_minimal_event(user_id=None, user_display=None)])

    mock_cur.executemany.assert_called_once()


# ---------------------------------------------------------------------------
# fetch_usage_summary tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_usage_summary_by_command():
    sample = [{"CommandName": "ping", "Uses": 5, "Successes": 5, "AvgLatencyMs": 30.0}]

    async def _mock(*a, **kw):
        return sample

    with patch("telemetry.dal.command_usage_dal.fetch_usage_rows", side_effect=_mock):
        result = await fetch_usage_summary(by="command", period="24h", context="all", limit=10)
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_fetch_usage_summary_by_user():
    sample = [{"UserId": 1, "UserDisplay": "Alice", "Uses": 3, "UniqueCommands": 2}]

    async def _mock(*a, **kw):
        return sample

    with patch("telemetry.dal.command_usage_dal.fetch_usage_rows", side_effect=_mock):
        result = await fetch_usage_summary(by="user", period="7d", context="all", limit=10)
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_fetch_usage_summary_by_reliability():
    sample = [
        {"CommandName": "ping", "Total": 10, "Successes": 8},
        {"CommandName": "status", "Total": 5, "Successes": 5},
    ]

    async def _mock(*a, **kw):
        return sample

    with patch("telemetry.dal.command_usage_dal.fetch_usage_rows", side_effect=_mock):
        result = await fetch_usage_summary(by="reliability", period="24h", context="all", limit=10)
    assert isinstance(result, list)
    assert all("Rate" in r for r in result)


# ---------------------------------------------------------------------------
# fetch_usage_detail tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_usage_detail_command_dimension():
    stats_row = [{"Total": 10, "Successes": 8, "Failures": 2, "P50": 30, "P95": 120}]
    err_rows: list = []

    call_index = [0]

    async def _mock_fetch_rows(sql, params):
        call_index[0] += 1
        if call_index[0] == 1:
            return stats_row
        return err_rows

    with patch("telemetry.dal.command_usage_dal.fetch_usage_rows", side_effect=_mock_fetch_rows):
        result = await fetch_usage_detail(
            dimension="command", value="/ping", period="7d", context="slash", limit=5
        )

    assert isinstance(result, list)
    assert len(result) == 1
    assert "Total" in result[0]
    assert "error_codes" in result[0]


# ---------------------------------------------------------------------------
# ctx_filter_sql tests
# ---------------------------------------------------------------------------


def test_ctx_filter_sql_all():
    assert ctx_filter_sql("all") == ("", tuple())


def test_ctx_filter_sql_slash():
    assert ctx_filter_sql("slash") == (" AND appcontext = ? ", ("slash",))
