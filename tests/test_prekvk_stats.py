from stats_alerts import prekvk_stats


def test_load_prekvk_top3_structured(monkeypatch):
    """Ensure load_prekvk_top3 returns expected dict shape and values using mocked DB results."""
    # Prepare fake results for sequence: overall, p1, p2, p3
    overall = [{"Name": "Alice", "Points": 150}, {"Name": "Bob", "Points": 120}]
    p1 = [{"Name": "Charlie", "Points": 40}]
    p2 = [{"Name": "Delta", "Points": 30}]
    p3 = [{"Name": "Echo", "Points": 20}]

    seq = [overall, p1, p2, p3]

    def fake_fetch_all(cur):
        return seq.pop(0)

    monkeypatch.setattr(prekvk_stats, "_fetch_all_as_dicts", lambda cur: fake_fetch_all(cur))

    # Also monkeypatch get_conn_with_retries to avoid real DB
    class DummyCursor:
        def execute(self, *args, **kwargs):
            pass

        def fetchall(self):
            return []

    class DummyConn:
        def cursor(self):
            return DummyCursor()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(prekvk_stats, "get_conn_with_retries", lambda: DummyConn())

    out = prekvk_stats.load_prekvk_top3(14, limit=3)
    assert set(out.keys()) == {"overall", "p1", "p2", "p3"}
    assert out["overall"][0]["Name"] == "Alice"
    assert out["overall"][0]["Points"] == 150
    assert out["p1"][0]["Name"] == "Charlie"
    assert out["p1"][0]["Points"] == 40


def test_load_prekvk_top3_limit_one(monkeypatch):
    """Ensure limit parameter is honoured (phase/overall)."""
    overall = [{"Name": "A", "Points": 10}, {"Name": "B", "Points": 5}]
    p_rows = [{"Name": "X", "Points": 7}]

    seq = [overall, p_rows, p_rows, p_rows]

    monkeypatch.setattr(prekvk_stats, "_fetch_all_as_dicts", lambda cur: seq.pop(0))

    class DummyCursor:
        def execute(self, *args, **kwargs):
            pass

        def fetchall(self):
            return []

    class DummyConn:
        def cursor(self):
            return DummyCursor()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(prekvk_stats, "get_conn_with_retries", lambda: DummyConn())

    out = prekvk_stats.load_prekvk_top3(15, limit=1)
    assert len(out["overall"]) <= 1
    assert len(out["p1"]) <= 1
    assert out["overall"][0]["Name"] == "A"


def test_load_prekvk_top3_queries_direct_stage_columns(monkeypatch):
    overall = [{"Name": "A", "Points": 60}]
    p1 = [{"Name": "A", "Points": 10}]
    p2 = [{"Name": "B", "Points": 20}]
    p3 = [{"Name": "C", "Points": 30}]
    seq = [overall, p1, p2, p3]
    executed = []

    monkeypatch.setattr(prekvk_stats, "_fetch_all_as_dicts", lambda cur: seq.pop(0))

    class DummyCursor:
        def execute(self, sql, *args, **kwargs):
            executed.append(str(sql))

        def fetchall(self):
            return []

    class DummyConn:
        def cursor(self):
            return DummyCursor()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(prekvk_stats, "get_conn_with_retries", lambda: DummyConn())

    out = prekvk_stats.load_prekvk_top3(15, limit=3)

    assert out == {"overall": overall, "p1": p1, "p2": p2, "p3": p3}
    assert "COALESCE(sc.TotalPoints, sc.Points)" in executed[0]
    assert "Stage1Points" in executed[1]
    assert "Stage2Points" in executed[2]
    assert "Stage3Points" in executed[3]
    assert all("PreKvk_Phases" not in sql for sql in executed)


def test_load_prekvk_top3_old_rows_without_stage_values_return_empty_phases(monkeypatch):
    overall = [{"Name": "Legacy", "Points": 50}]
    seq = [overall, [], [], []]
    monkeypatch.setattr(prekvk_stats, "_fetch_all_as_dicts", lambda cur: seq.pop(0))

    class DummyCursor:
        def execute(self, *args, **kwargs):
            pass

        def fetchall(self):
            return []

    class DummyConn:
        def cursor(self):
            return DummyCursor()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(prekvk_stats, "get_conn_with_retries", lambda: DummyConn())

    out = prekvk_stats.load_prekvk_top3(15, limit=3)

    assert out["overall"] == overall
    assert out["p1"] == []
    assert out["p2"] == []
    assert out["p3"] == []
