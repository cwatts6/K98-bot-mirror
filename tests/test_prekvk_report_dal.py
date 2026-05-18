from prekvk.dal import report_dal


def test_fetch_latest_report_rows_uses_direct_stage_columns_and_power(monkeypatch):
    captured = {}

    class Cursor:
        def __init__(self):
            self.description = [
                ("GovernorID",),
                ("GovernorName",),
                ("Power",),
                ("Stage1Points",),
                ("Stage2Points",),
                ("Stage3Points",),
                ("OverallPoints",),
                ("ScanID",),
                ("ScanTimestampUTC",),
                ("SourceFileName",),
            ]

        def execute(self, sql, params):
            captured["sql"] = sql
            captured["params"] = params

        def fetchall(self):
            return [(1, "Alpha", 100, 10, 20, 30, 60, 7, "now", "file.xlsx")]

    class Conn:
        def cursor(self):
            return Cursor()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(report_dal, "get_conn_with_retries", lambda: Conn())

    rows = report_dal.fetch_latest_prekvk_report_rows(15)

    assert rows[0]["GovernorName"] == "Alpha"
    assert "Stage1Points" in captured["sql"]
    assert "Stage2Points" in captured["sql"]
    assert "Stage3Points" in captured["sql"]
    assert "ALL_STATS_FOR_DASHBAORD" in captured["sql"]
    assert "PreKvk_Phases" not in captured["sql"]
    assert captured["params"] == (15, 15, 15)
