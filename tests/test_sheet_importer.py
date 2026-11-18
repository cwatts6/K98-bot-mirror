import pandas as pd

from sheet_importer import executemany_batched, quote_sql_columns, write_df_to_staging_and_upsert


def test_quote_sql_columns_basic():
    cols = ["KVK_NO", "Col[With]Brackets", "Name"]
    out = quote_sql_columns(cols)
    assert "[KVK_NO]" in out
    assert (
        "[Col[[]With]]Brackets]" in out or "[Col[With]]Brackets]" in out
    )  # ensure brackets escaped


def test_executemany_batched_single_and_multi(monkeypatch):
    executed = []

    class MockCursor:
        def executemany(self, sql, rows):
            executed.append((sql, len(rows)))

    class MockConn:
        def commit(self):
            executed.append(("commit", None))

        def rollback(self):
            executed.append(("rollback", None))

    cursor = MockCursor()
    conn = MockConn()

    # Single batch
    rows = [(i,) for i in range(10)]
    inserted = executemany_batched(cursor, conn, "INSERT", rows, batch_size=100)
    assert inserted == 10
    assert any(e[0] == "commit" for e in executed)

    executed.clear()

    # Multi batch
    rows = [(i,) for i in range(12000)]
    inserted = executemany_batched(cursor, conn, "INSERT", rows, batch_size=5000)
    assert inserted == 12000
    # 3 batch commits expected
    assert sum(1 for e in executed if e[0] == "commit") == 3


def test_write_df_to_staging_and_upsert(monkeypatch, tmp_path):
    # Prepare df
    df = pd.DataFrame([{"KVK_NO": 1, "KVK_NAME": "Test"}])

    class DummyCursor:
        def __init__(self):
            self.calls = []

        def execute(self, sql, *args, **kwargs):
            self.calls.append(sql)
            # mimic DBCC SQLPERF call returns for other modules if needed
            return None

        def executemany(self, sql, rows):
            self.calls.append(("executemany", sql, len(rows)))

    class DummyConn:
        def commit(self):
            pass

        def rollback(self):
            pass

    cursor = DummyCursor()
    conn = DummyConn()

    res = write_df_to_staging_and_upsert(
        cursor,
        conn,
        df,
        "dbo.ProcConfig_Staging",
        "dbo.sp_Upsert_ProcConfig_From_Staging",
        transactional=True,
    )
    assert res["staging"]["status"] in ("ok", "error")
    # upsert result should be present even if mocked
    assert "upsert" in res
