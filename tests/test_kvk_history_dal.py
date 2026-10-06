from __future__ import annotations

import pytest

from kvk.dal import kvk_history_dal


class _Cursor:
    def __init__(self, result_sets):
        self._result_sets = result_sets
        self._index = 0
        self.executed = None

    @property
    def description(self):
        columns, _rows = self._result_sets[self._index]
        return None if columns is None else [(column,) for column in columns]

    def execute(self, sql, params):
        self.executed = (sql, params)

    def fetchall(self):
        if self.description is None:
            raise AssertionError("fetchall called for a non-row-bearing result set")
        return self._result_sets[self._index][1]

    def nextset(self):
        self._index += 1
        return self._index < len(self._result_sets)


class _Connection:
    def __init__(self, cursor):
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def cursor(self):
        return self._cursor


def test_summary_metric_ranks_skip_non_row_result_and_map_contract(monkeypatch):
    cursor = _Cursor(
        [
            (None, []),
            (
                ["Metric", "Gov_ID", "KVK_NO", "MetricValue", "Overall_Rank"],
                [("Most Kills", 2441482, 15, 123456, 2)],
            ),
        ]
    )
    monkeypatch.setattr(
        kvk_history_dal,
        "get_conn_with_retries",
        lambda: _Connection(cursor),
    )

    rows = kvk_history_dal.fetch_history_summary_metric_ranks(
        2441482,
        [15, 13, 15, 0, -1],
    )

    assert rows == [
        {
            "Metric": "Most Kills",
            "Gov_ID": 2441482,
            "KVK_NO": 15,
            "MetricValue": 123456,
            "Overall_Rank": 2,
        }
    ]
    sql, params = cursor.executed
    assert "SET NOCOUNT ON;" in sql
    assert "EXEC dbo.usp_GetKvkHistorySummaryMetricRanks" in sql
    assert params[:2] == [13, 15]
    assert params[2:20] == [None] * 18
    assert params[20] == 2441482


def test_summary_metric_ranks_raise_when_contract_omits_result_set(monkeypatch):
    cursor = _Cursor([(None, [])])
    monkeypatch.setattr(
        kvk_history_dal,
        "get_conn_with_retries",
        lambda: _Connection(cursor),
    )

    with pytest.raises(ValueError, match="omitted a result set"):
        kvk_history_dal.fetch_history_summary_metric_ranks(2441482, [15])


def test_summary_metric_ranks_do_not_open_connection_without_finalized_kvks(monkeypatch):
    monkeypatch.setattr(
        kvk_history_dal,
        "get_conn_with_retries",
        lambda: pytest.fail("connection should not be opened"),
    )

    assert kvk_history_dal.fetch_history_summary_metric_ranks(2441482, []) == []
