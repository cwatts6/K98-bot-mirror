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

    monkeypatch.setattr("file_utils.get_conn_with_retries", lambda: DummyConn())

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

    monkeypatch.setattr("file_utils.get_conn_with_retries", lambda: DummyConn())

    out = prekvk_stats.load_prekvk_top3(15, limit=1)
    assert len(out["overall"]) <= 1
    assert len(out["p1"]) <= 1
    assert out["overall"][0]["Name"] == "A"
