from unittest.mock import Mock

import pytest

from services.stats_report_continuation_dal import (
    REPORT_QUERY_TIMEOUT_SECONDS,
    StatsReportContinuationDAL,
)


@pytest.mark.parametrize("failure", [None, "execute", "nextset", "cursor"])
def test_report_cursor_gets_bounded_budget_before_creation_and_restores_short_budget(failure):
    connection = Mock(timeout=15)
    cursor = Mock()
    cursor.nextset.side_effect = [True, False]

    def create():
        assert connection.timeout == REPORT_QUERY_TIMEOUT_SECONDS == 595
        if failure == "cursor":
            raise RuntimeError("create failed")
        return cursor

    connection.cursor.side_effect = create
    if failure in {"execute", "nextset"}:
        getattr(cursor, failure).side_effect = TimeoutError("driver failure")
    if failure:
        with pytest.raises((TimeoutError, RuntimeError)):
            StatsReportContinuationDAL._complete_reports(connection, "exact.csv", "prep")
    else:
        StatsReportContinuationDAL._complete_reports(connection, "exact.csv", "prep")
        assert cursor.nextset.call_count == 2
    assert connection.timeout == 15
    assert cursor.close.call_count == (failure != "cursor")
    connection.close.assert_not_called()
    if failure != "cursor":
        assert cursor.execute.call_args.args == (
            "EXEC dbo.usp_S11CompleteStatsReports @CompletedFileName=?,@ExportPreparationID=?",
            "exact.csv",
            "prep",
        )


@pytest.mark.parametrize("close_fails", [False, True])
def test_cleanup_failure_preserves_original_driver_error_and_codes(close_fails):
    import pyodbc

    from services.recovery_health import failure_detail

    original = pyodbc.OperationalError("HYT00", "private report failure (8153)")
    cursor = Mock()
    cursor.nextset.side_effect = original
    if close_fails:
        cursor.close.side_effect = RuntimeError("private close failure")

    class Connection:
        value = 15

        @property
        def timeout(self):
            return self.value

        @timeout.setter
        def timeout(self, value):
            if value == 15:
                raise RuntimeError("private restoration failure")
            self.value = value

        def cursor(self):
            assert self.value == 595
            return cursor

    with pytest.raises(pyodbc.OperationalError) as caught:
        StatsReportContinuationDAL._complete_reports(Connection(), "exact.csv", "prep")
    assert caught.value is original
    detail = failure_detail(caught.value)
    assert detail["sqlstates"] == ["HYT00"] and detail["sql_numbers"] == [8153]
    assert "private" not in str(detail)
    assert "timeout restoration also failed" in str(original.__notes__)
    assert "private" not in str(original.__notes__)
    cursor.close.assert_called_once()
