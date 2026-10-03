from __future__ import annotations

from datetime import date

import pytest

from stats_alerts import offseason_dal as dal


class _RowsCursor:
    def __init__(self, rows):
        self.rows = rows
        self.executed = []

    def execute(self, sql, *params):
        self.executed.append((sql, params))

    def fetchall(self):
        return self.rows


class _SequenceCursor:
    def __init__(self, responses):
        self.responses = list(responses)
        self.active = None
        self.executed = []

    @property
    def description(self):
        return [(name,) for name in self.active[0]]

    def execute(self, sql, *params):
        self.executed.append((sql, params))
        self.active = self.responses.pop(0)

    def fetchone(self):
        return self.active[1]


def test_daily_activity_metric_is_allowlisted_and_parameterized() -> None:
    cursor = _RowsCursor([("Alpha", 10), ("Beta", None)])
    snapshot = date(2026, 7, 28)

    rows = dal.get_activity_top_daily(cursor, "BuildingDelta", 5, snapshot)

    assert rows == [("Alpha", 10), ("Beta", 0)]
    sql, params = cursor.executed[0]
    assert "SUM(BuildDonations)" in sql
    assert "TOP (5)" in sql
    assert params == (snapshot,)


@pytest.mark.parametrize(
    "call",
    [
        lambda cursor: dal.get_activity_top_daily(
            cursor, "Power); DROP TABLE dbo.KingdomScanData4;--", 5, date.today()
        ),
        lambda cursor: dal.get_daily_top(
            cursor, "dbo.vDaily_Helps; DROP TABLE dbo.KS;--", "HelpsDelta", date.today()
        ),
        lambda cursor: dal.get_weekly_top(cursor, "unknown"),
    ],
)
def test_dynamic_identifiers_fail_closed_before_execute(call) -> None:
    cursor = _RowsCursor([])

    with pytest.raises(ValueError):
        call(cursor)

    assert cursor.executed == []


def test_kingdom_summary_reads_schema_native_bigint_power() -> None:
    cursor = _SequenceCursor(
        [
            (("cur_order", "prev_order"), (10, 9)),
            (("PlayerCount",), (411,)),
            (("Power",), (1_000,)),
            (("Power",), (900,)),
        ]
    )

    summary = dal.get_kingdom_summary(cursor)

    assert summary == {
        "total_power_top300": 1_000,
        "total_players": 411,
        "power_delta_top300": 100,
    }
    aggregate_sql = "\n".join(sql for sql, _params in cursor.executed)
    assert "SUM(Power)" in aggregate_sql
    assert "CAST(Power AS BIGINT)" not in aggregate_sql


def test_weekly_loader_preserves_six_leaderboard_contracts() -> None:
    cursor = _RowsCursor([("Alpha", 12)])

    result = dal.load_all_weekly(cursor)

    assert list(result) == [
        "building",
        "tech",
        "helps",
        "rss_gathered",
        "rss_assisted",
        "forts",
    ]
    assert all(rows == [("Alpha", 12)] for rows in result.values())
    assert len(cursor.executed) == 6
