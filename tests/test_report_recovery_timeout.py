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
