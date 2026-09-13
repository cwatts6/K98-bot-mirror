import types

import pandas as pd

from gsheet_module import _sort_kvk_export_sheet, sort_worksheet_multi


class DummyBatchUpdate:
    def __init__(self):
        self.calls = []

    def __call__(self, spreadsheetId, body):
        self.calls.append((spreadsheetId, body))
        return types.SimpleNamespace(execute=lambda num_retries=0: {"ok": True})


class DummyService:
    def __init__(self):
        self.batch = DummyBatchUpdate()

    def spreadsheets(self):
        return types.SimpleNamespace(batchUpdate=self.batch)


def test_sort_worksheet_multi_builds_sort_specs():
    service = DummyService()
    sort_worksheet_multi(
        service,
        spreadsheet_id="sheet123",
        sheet_id=42,
        total_rows=10,
        total_cols=5,
        sort_specs=[(3, "ASCENDING"), (1, "DESCENDING")],
        retries=1,
    )
    assert service.batch.calls
    _, body = service.batch.calls[0]
    req = body["requests"][0]["sortRange"]
    assert req["range"]["startRowIndex"] == 1
    assert req["range"]["endRowIndex"] == 10
    assert req["sortSpecs"] == [
        {"dimensionIndex": 3, "sortOrder": "ASCENDING"},
        {"dimensionIndex": 1, "sortOrder": "DESCENDING"},
    ]


def test_sort_kvk_export_sheet_default_sort():
    service = DummyService()
    df = pd.DataFrame({"DKP": [1, 2], "foo": [3, 4]})
    ws = types.SimpleNamespace(id=99)
    _sort_kvk_export_sheet(service, "sheetX", ws, df, "ANY", "ANY")
    _, body = service.batch.calls[0]
    sort_specs = body["requests"][0]["sortRange"]["sortSpecs"]
    assert sort_specs == [{"dimensionIndex": 0, "sortOrder": "DESCENDING"}]
