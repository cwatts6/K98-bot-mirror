from typing import Any

import pandas as pd

from gsheet_module import (
    _drop_cols_case_insensitive,
    _ensure_kvk_no_first,
    _prepare_kvk_export_df,
    _reorder_sheet_tabs,
)


def test_drop_cols_case_insensitive_empty_df_keeps_schema():
    df = pd.DataFrame(columns=["campid", "Name"])
    out = _drop_cols_case_insensitive(df, ["camp_id", "campid"])
    assert list(out.columns) == ["Name"]


def test_ensure_kvk_no_first_header_only():
    df = pd.DataFrame(columns=["Name"])
    out = _ensure_kvk_no_first(df, 14)
    assert next(iter(out.columns)) == "KVK_NO"


def test_prepare_kvk_export_df_case_insensitive():
    df = pd.DataFrame(columns=["CaMpId", "name"])
    out = _prepare_kvk_export_df(df, 14)
    assert list(out.columns) == ["KVK_NO", "name"]


class DummyBatchUpdateRequest:
    """
    Lightweight dummy request object for testing _reorder_sheet_tabs.
    Provides an execute() method so _safe_execute can call it.
    """

    def __init__(self, body: dict[str, Any]) -> None:
        self.body = body

    def execute(self, num_retries: int = 0) -> dict[str, Any]:
        return {"status": "ok", "body": self.body}


class DummySpreadsheets:
    """
    Dummy spreadsheets() facade that records the last batchUpdate body.
    """

    def __init__(self, parent: "DummyService") -> None:
        self._parent = parent

    def batchUpdate(self, spreadsheetId: str, body: dict[str, Any]) -> DummyBatchUpdateRequest:
        self._parent.last_spreadsheet_id = spreadsheetId
        self._parent.last_batch_body = body
        return DummyBatchUpdateRequest(body)


class DummyService:
    """
    Dummy Google Sheets service used to unit test _reorder_sheet_tabs.
    """

    def __init__(self) -> None:
        self.last_spreadsheet_id: str | None = None
        self.last_batch_body: dict[str, Any] | None = None

    def spreadsheets(self) -> DummySpreadsheets:
        return DummySpreadsheets(self)


def test_reorder_sheet_tabs_basic() -> None:
    service = DummyService()
    spreadsheet_id = "test-spreadsheet"
    title_to_id = {"SheetA": 101, "SheetB": 102, "SheetC": 103}
    desired_titles = ["SheetB", "SheetC", "SheetA"]

    _reorder_sheet_tabs(service, spreadsheet_id, title_to_id, desired_titles)

    assert service.last_spreadsheet_id == spreadsheet_id
    assert service.last_batch_body is not None

    requests = service.last_batch_body.get("requests", [])
    assert len(requests) == 3

    sheet_ids = [r["updateSheetProperties"]["properties"]["sheetId"] for r in requests]
    indices = [r["updateSheetProperties"]["properties"]["index"] for r in requests]
    fields_values = [r["updateSheetProperties"]["fields"] for r in requests]

    assert sheet_ids == [102, 103, 101]
    assert indices == [0, 1, 2]
    assert all(f == "index" for f in fields_values)
