from __future__ import annotations

from datetime import date, datetime

import pytest

from stats.dal import personal_stats_dal as dal


class _Cursor:
    def __init__(self, result_sets):
        self._result_sets = result_sets
        self._index = 0
        self.timeout = None
        self.executed = None
        self.closed = False

    @property
    def description(self):
        return [(name,) for name in self._result_sets[self._index][0]]

    def execute(self, sql, params):
        self.executed = (sql, params)

    def fetchall(self):
        return self._result_sets[self._index][1]

    def nextset(self):
        self._index += 1
        return self._index < len(self._result_sets)

    def close(self):
        self.closed = True


class _Connection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.closed = False

    def cursor(self):
        return self._cursor

    def close(self):
        self.closed = True


def _sets(governor_id: int = 111):
    header_columns = (
        "StatsAnchorDate",
        "WindowStartDate",
        "WindowEndDate",
        "RequestedGovernorCount",
    )
    daily_columns = (
        "GovernorID",
        "AsOfDate",
        "HasStats",
        "PreviousStatsDate",
        "PowerDelta",
        "HasAllianceActivity",
        "HasForts",
        "FortsTotal",
    )
    return (
        (header_columns, [(date(2026, 7, 15), date(2026, 1, 17), date(2026, 7, 15), 1)]),
        (
            daily_columns,
            [
                (
                    governor_id,
                    datetime(2026, 7, 14, 12, 0),
                    1,
                    date(2026, 7, 13),
                    -50,
                    0,
                    1,
                    -2,
                )
            ],
        ),
    )


def test_set_based_contract_deduplicates_ids_binds_fixed_shape_and_closes(monkeypatch) -> None:
    cursor = _Cursor(_sets())
    connection = _Connection(cursor)
    monkeypatch.setattr(dal, "get_conn_with_retries", lambda: connection)

    dataset = dal.fetch_personal_stats_daily((111, 111), history_days=180)

    assert dataset.header.stats_anchor_date == date(2026, 7, 15)
    assert dataset.rows[0].power_delta == -50
    assert dataset.rows[0].forts_total == -2
    assert cursor.timeout == 9
    assert cursor.executed is not None
    sql, params = cursor.executed
    assert "dbo.IntList" in sql
    assert "usp_GetPersonalStatsDaily" in sql
    assert len(params) == 27
    assert params[0] == 111
    assert params[1:26] == (None,) * 25
    assert params[-1] == 180
    assert cursor.closed is True
    assert connection.closed is True


@pytest.mark.parametrize("governor_ids", ((), tuple(range(1, 28)), (0,), (-1,)))
def test_contract_rejects_out_of_bounds_governor_sets(governor_ids) -> None:
    with pytest.raises(ValueError):
        dal.fetch_personal_stats_daily(governor_ids)


def test_contract_rejects_foreign_rows_and_still_closes(monkeypatch) -> None:
    cursor = _Cursor(_sets(governor_id=999))
    connection = _Connection(cursor)
    monkeypatch.setattr(dal, "get_conn_with_retries", lambda: connection)

    with pytest.raises(ValueError, match="invalid source row identity"):
        dal.fetch_personal_stats_daily((111,))

    assert cursor.closed is True
    assert connection.closed is True
