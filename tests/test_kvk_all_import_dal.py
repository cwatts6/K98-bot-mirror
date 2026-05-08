from __future__ import annotations

import datetime as dt
from typing import Any, cast

import pandas as pd

from kvk.dal import kvk_all_import_dal as dal
from kvk.schemas.kvk_all_schema import (
    EXPECTED_FULL_DATA_COLUMNS,
    SCHEMA_VERSION,
    validate_full_data_columns,
)
from kvk.services.kvk_all_import_service import KvkAllPreparedImport


def _prepared_frame() -> KvkAllPreparedImport:
    schema = validate_full_data_columns(
        EXPECTED_FULL_DATA_COLUMNS, sheet_name="Full Data"
    ).to_dict()
    row: dict[str, Any] = {column: 1 for column in dal.STAGE_COL_ORDER}
    row.update(
        {
            "governor_id": 123,
            "name": "Test Governor",
            "kingdom": 98,
            "schema_version": SCHEMA_VERSION,
            "source_sheet_name": "Full Data",
            "source_column_hash": schema["column_hash"],
            "source_column_count": schema["column_count"],
            "source_row_count": 1,
        }
    )
    return KvkAllPreparedImport(
        dataframe=pd.DataFrame([row]),
        sheet_name="Full Data",
        schema_metadata=schema,
    )


class MockCursor:
    def __init__(self) -> None:
        self.fast_executemany = False
        self.executed: list[tuple[str, object]] = []
        self.executemany_calls: list[tuple[str, list[tuple[object, ...]]]] = []
        self._fetchall: list[tuple[object, ...]] = []
        self._fetchone: tuple[object, ...] | None = (1,)
        self.description = [("COUNT",)]

    def execute(self, sql: str, params=None):
        self.executed.append((sql, params))
        if sql == dal.STAGE_SCHEMA_COLUMNS_SQL:
            self._fetchall = [(column,) for column in dal.STAGE_INSERT_COLUMNS]
        elif sql == dal.CALL_INGEST_SQL:
            self._fetchall = [(13, 2, 1)]
        elif sql == dal.NEGATIVE_COUNT_SQL:
            self.description = [("COUNT",)]
            self._fetchall = []
            self._fetchone = (3,)
        return self

    def executemany(self, sql: str, rows):
        self.executemany_calls.append((sql, list(rows)))

    def fetchall(self):
        return self._fetchall

    def fetchone(self):
        return self._fetchone


class MockConnection:
    def __init__(self) -> None:
        self.cursors: list[MockCursor] = []
        self.commit_calls = 0

    def cursor(self) -> MockCursor:
        cursor = MockCursor()
        self.cursors.append(cursor)
        return cursor

    def commit(self) -> None:
        self.commit_calls += 1


def test_rows_for_stage_uses_declared_column_order() -> None:
    prepared = _prepared_frame()

    row = dal.rows_for_stage("token-1", prepared.dataframe)[0]
    values = dict(zip(["IngestToken", *dal.STAGE_COL_ORDER], row, strict=True))

    assert values["IngestToken"] == "token-1"
    assert values["governor_id"] == 123
    assert values["schema_version"] == SCHEMA_VERSION
    assert len(row) == len(dal.STAGE_INSERT_COLUMNS)


def test_ingest_prepared_import_call_shape(monkeypatch) -> None:
    connection = MockConnection()
    monkeypatch.setattr(dal, "scan_ts_within_kvk_details", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(dal.uuid, "uuid4", lambda: "token-1")

    result = dal.ingest_prepared_import(
        con=connection,
        prepared=_prepared_frame(),
        content=b"abc",
        source_filename="kvk.xlsx",
        uploader_id=999,
        scan_ts_utc=dt.datetime(2026, 5, 8, 1, 0, tzinfo=dt.UTC),
    )

    stage_cursor = connection.cursors[0]
    ingest_cursor = connection.cursors[1]
    recompute_cursor = connection.cursors[2]
    negative_cursor = connection.cursors[3]

    assert stage_cursor.executemany_calls[0][0] == dal.STAGE_INSERT_SQL
    assert ingest_cursor.executed[0][0] == dal.CALL_INGEST_SQL
    params = cast(tuple[Any, ...], ingest_cursor.executed[0][1])
    assert params[0] == "token-1"
    assert params[2] == "kvk.xlsx"
    assert params[4] == 999
    assert params[5] == SCHEMA_VERSION
    assert params[6] == "Full Data"
    assert params[8] == len(EXPECTED_FULL_DATA_COLUMNS)
    assert params[9] == 1
    assert recompute_cursor.executed[0] == (dal.RECOMPUTE_SQL, 13)
    assert negative_cursor.executed[0] == (dal.NEGATIVE_COUNT_SQL, (13, 2))
    assert result["kvk_no"] == 13
    assert result["scan_id"] == 2
    assert result["negatives"] == 3
    assert result["success"] is True
    assert connection.commit_calls == 3


def test_ingest_prepared_import_cleans_stage_rows_when_precheck_fails(monkeypatch) -> None:
    connection = MockConnection()
    monkeypatch.setattr(dal, "scan_ts_within_kvk_details", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(dal.uuid, "uuid4", lambda: "token-2")

    result = dal.ingest_prepared_import(
        con=connection,
        prepared=_prepared_frame(),
        content=b"abc",
        source_filename="kvk.xlsx",
        uploader_id=999,
        scan_ts_utc=dt.datetime(2026, 5, 8, 1, 0, tzinfo=dt.UTC),
    )

    stage_cursor = connection.cursors[0]
    assert stage_cursor.executemany_calls[0][0] == dal.STAGE_INSERT_SQL
    assert (dal.DELETE_STAGED_TOKEN_SQL, "token-2") in stage_cursor.executed
    assert result["success"] is False
    assert connection.commit_calls == 2
