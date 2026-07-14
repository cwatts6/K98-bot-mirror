from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from player_self_service import accounts_dal


class _Cursor:
    def __init__(self) -> None:
        self.executions = []
        self.description = [
            (name,)
            for name in (
                "RequestedGovernorID",
                "GovernorName",
                "Civilisation",
                "CityHall",
                "VipLevelCode",
                "VipLevelLabel",
                "Power",
                "TroopPower",
                "KillPoints",
                "T4Kills",
                "T5Kills",
                "Deads",
                "HealedTroops",
                "HighestAcclaim",
                "Helps",
                "RSSGathered",
                "RSSAssistance",
                "Conduct",
                "LocationX",
                "LocationY",
                "ScanDate",
                "LatestScanDate",
            )
        ]
        self._params = ()

    def execute(self, sql, params):
        self.executions.append((sql, tuple(params)))
        self._params = tuple(params)

    def fetchall(self):
        now = datetime(2026, 7, 14, 8, 0)
        return [
            (
                governor_id,
                f"Gov {governor_id}",
                "Rome",
                25,
                "VIP_18",
                "VIP 18",
                1_000,
                400,
                200,
                30,
                40,
                50,
                60,
                70,
                80,
                90,
                100,
                Decimal("98.50"),
                123,
                456,
                now,
                now,
            )
            for governor_id in self._params
        ]


class _Connection:
    def __init__(self) -> None:
        self.cursor_instance = _Cursor()
        self.closed = False

    def cursor(self):
        return self.cursor_instance

    def close(self):
        self.closed = True


def test_accounts_dal_uses_one_set_based_latest_scan_query(monkeypatch) -> None:
    connection = _Connection()
    monkeypatch.setattr(accounts_dal, "get_conn_with_retries", lambda: connection)

    rows = accounts_dal.fetch_latest_accounts_scan_rows([222, 111, 222])

    assert [row.governor_id for row in rows] == [222, 111]
    assert rows[0].t4_t5_kills == 70
    assert rows[0].conduct == Decimal("98.50")
    assert rows[0].vip_level_code == "VIP_18"
    assert rows[0].vip_level_label == "VIP 18"
    assert connection.closed is True
    assert len(connection.cursor_instance.executions) == 1
    sql, params = connection.cursor_instance.executions[0]
    assert params == (222, 111)
    assert "MAX(s.ScanDate)" in sql
    assert "PARTITION BY TRY_CONVERT(BIGINT, s.GovernorID)" in sql
    assert "dbo.KingdomScanData4" in sql
    assert "dbo.Civilization_Mapping" in sql
    assert "dbo.PlayerLocation" in sql
    assert "dbo.GovernorInventoryProfile" in sql
    assert "VipLevelLabel" in sql
    assert "RSSAssistance" in sql


def test_accounts_dal_chunks_without_n_plus_one(monkeypatch) -> None:
    connection = _Connection()
    monkeypatch.setattr(accounts_dal, "get_conn_with_retries", lambda: connection)

    rows = accounts_dal.fetch_latest_accounts_scan_rows(range(1, 702))

    assert len(rows) == 701
    assert [len(params) for _sql, params in connection.cursor_instance.executions] == [500, 201]
