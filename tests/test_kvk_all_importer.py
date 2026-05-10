from __future__ import annotations

import datetime as dt
from io import BytesIO

import pandas as pd

from kvk.schemas.kvk_all_schema import EXPECTED_FULL_DATA_COLUMNS, SCHEMA_VERSION
import kvk_all_importer as importer


def _xlsx_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    return bio.getvalue()


def _full_data_df() -> pd.DataFrame:
    row: dict[str, object] = {column: 1 for column in EXPECTED_FULL_DATA_COLUMNS}
    row.update(
        {
            "name": "Test Governor",
            "first_updateUTC": "2026-05-08 01:00:00",
            "last_updateUTC": "2026-05-08 02:00:00",
        }
    )
    return pd.DataFrame([row], columns=list(EXPECTED_FULL_DATA_COLUMNS))


def test_wrapper_returns_schema_validation_error_without_db_connection() -> None:
    result = importer.ingest_kvk_all_excel(
        content=_xlsx_bytes({"Basic Data": pd.DataFrame([{"governor_id": 1}])}),
        source_filename="kvk.xlsx",
        uploader_id=123,
        scan_ts_utc=dt.datetime(2026, 5, 8, tzinfo=dt.UTC),
        server="unused",
        database="unused",
        username="unused",
        password="unused",
    )

    assert result["success"] is False
    assert result["schema_version"] == SCHEMA_VERSION
    assert result["validation_error"]["code"] == "missing_full_data_sheet"


def test_wrapper_preserves_success_return_shape(monkeypatch) -> None:
    expected = {
        "kvk_no": 13,
        "scan_id": 2,
        "row_count": 1,
        "negatives": 0,
        "staged_rows": 1,
        "ingest_ms": 12.0,
        "recompute_ms": 3.0,
        "proc_ms": 12.0,
        "sheet": "Full Data",
        "schema_version": SCHEMA_VERSION,
        "schema": {"schema_version": SCHEMA_VERSION},
        "success": True,
    }

    class MockConnection:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

    connection = MockConnection()
    monkeypatch.setattr(
        importer.kvk_all_import_dal, "connect_sql_server", lambda **_kwargs: connection
    )
    monkeypatch.setattr(
        importer.kvk_all_import_dal,
        "ingest_prepared_import",
        lambda **_kwargs: expected.copy(),
    )

    result = importer.ingest_kvk_all_excel(
        content=_xlsx_bytes({"Full Data": _full_data_df()}),
        source_filename="kvk.xlsx",
        uploader_id=123,
        scan_ts_utc=dt.datetime(2026, 5, 8, tzinfo=dt.UTC),
        server="unused",
        database="unused",
        username="unused",
        password="unused",
    )

    assert result["success"] is True
    assert result["kvk_no"] == 13
    assert result["proc_ms"] == 12.0
    assert result["duration_s"] >= 0
    assert connection.closed is True


def test_wrapper_returns_coercion_validation_context_without_db_connection() -> None:
    full_data = _full_data_df()
    full_data.loc[0, "governor_id"] = None

    result = importer.ingest_kvk_all_excel(
        content=_xlsx_bytes({"Full Data": full_data}),
        source_filename="kvk.xlsx",
        uploader_id=123,
        scan_ts_utc=dt.datetime(2026, 5, 8, tzinfo=dt.UTC),
        server="unused",
        database="unused",
        username="unused",
        password="unused",
    )

    assert result["success"] is False
    assert result["sheet"] == "Full Data"
    assert result["schema_version"] == SCHEMA_VERSION
    assert result["validation_error"]["code"] == "full_data_coercion_failed"
    assert result["validation_error"]["schema"]["schema_version"] == SCHEMA_VERSION
