from __future__ import annotations

from datetime import UTC, datetime

from player_self_service import governor_dashboard_dal as dal


class _Cursor:
    def __init__(self) -> None:
        self.executed_sql = ""
        self.executed_params = ()
        self.description = [
            ("GovernorID",),
            ("GovernorName",),
            ("Alliance",),
            ("Power",),
            ("KillPoints",),
            ("Dead",),
            ("Helps",),
            ("Healed",),
            ("HighestAcclaim",),
            ("AOOJoined",),
            ("AOOWon",),
            ("AutarchTimes",),
            ("KvKPlayed",),
            ("Conduct",),
            ("Civilization",),
            ("LocationX",),
            ("LocationY",),
            ("UpdatedAtUtc",),
            ("ScanOrder",),
        ]
        self._row = (
            2_441_482,
            "Chrislos",
            "k98A",
            123_901_077,
            8_515_574_404,
            26_223_242,
            189_295,
            357_163_093,
            91,
            12,
            8,
            4,
            7,
            100,
            "Britain",
            123,
            456,
            datetime(2026, 7, 10, 9, 17, tzinfo=UTC),
            1002,
        )

    def execute(self, sql, params) -> None:
        self.executed_sql = sql
        self.executed_params = params

    def fetchone(self):
        return self._row


class _Connection:
    def __init__(self) -> None:
        self.cursor_instance = _Cursor()
        self.closed = False

    def cursor(self) -> _Cursor:
        return self.cursor_instance

    def close(self) -> None:
        self.closed = True


def test_dashboard_dal_uses_latest_scan_fields_and_civilisation_mapping(monkeypatch) -> None:
    connection = _Connection()
    monkeypatch.setattr(dal, "get_conn_with_retries", lambda: connection)

    result = dal.fetch_governor_dashboard_data(2_441_482)

    sql = connection.cursor_instance.executed_sql
    assert "s.HighestAcclaim" in sql
    assert "s.AOOJoined" in sql
    assert "s.AOOWon" in sql
    assert "s.AutarchTimes" in sql
    assert "s.KvKPlayed" in sql
    assert "s.GovernorID = CONVERT(FLOAT, ?)" in sql
    assert "ORDER BY s.SCANORDER DESC, s.AsOfDate DESC, s.ScanDate DESC" in sql
    assert "TRY_CONVERT(BIGINT, s.GovernorID)" not in sql
    assert "dbo.Civilization_Mapping" in sql
    assert "cm.Civilization_Name" in sql
    assert "dbo.PlayerLocation" in sql
    assert "pl.GovernorID = r.GovernorID" in sql
    assert "ALL_STATS_FOR_DASHBOARD" not in sql
    assert connection.cursor_instance.executed_params == (2_441_482, 2_441_482)
    assert connection.closed is True
    assert result.highest_acclaim == 91
    assert result.ark_joined == 12
    assert result.ark_won == 8
    assert result.times_named_autarch == 4
    assert result.kvk_played == 7
    assert result.civilization == "Britain"
    assert result.location_x == 123
    assert result.location_y == 456
