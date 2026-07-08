from __future__ import annotations

import pytest

pytest.importorskip("pyodbc")

import forts_ingest


class _FakeCursor:
    description = (("IngestionID",),)

    def __init__(self):
        self.calls = []

    def execute(self, sql, params):
        self.calls.append((sql, params))

    def fetchone(self):
        return (123,)


def test_insert_log_returns_ingestion_id_from_output_clause():
    cur = _FakeCursor()

    ingestion_id = forts_ingest._insert_log(
        cur,
        "rally_daily",
        "Rally_data_26-05-2026.xlsx",
        "abc123",
        "2026-05-26",
        7,
        "success",
        None,
    )

    sql, params = cur.calls[0]
    assert "OUTPUT INSERTED.IngestionID" in sql
    assert params == (
        "rally_daily",
        "Rally_data_26-05-2026.xlsx",
        "abc123",
        "2026-05-26",
        7,
        "success",
        None,
    )
    assert ingestion_id == 123
