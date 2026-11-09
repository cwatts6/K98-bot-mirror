import types

import pandas as pd

from gsheet_module import _sort_kvk_export_sheet, sort_worksheet_multi


def test_scan_plan_freezes_stable_sort_headers_and_empty_tab():
    from gsheet_module import plan_legacy_outputs

    frame = pd.DataFrame({"id": [2, 1, 3], "score": [10, 20, 10]})
    config = dict(
        consumer="scan_data",
        spreadsheets={"Daily": "file-a"},
        exports=[
            dict(sheet="Daily", tab="Data", sort=1, order="DESCENDING"),
            dict(sheet="Daily", tab="Empty"),
        ],
    )
    sections, plan = plan_legacy_outputs(
        config, frames=[frame, pd.DataFrame(columns=["ScanID", "UTC"])]
    )
    frame.loc[0, "score"] = 999
    assert sections[0].rows == ((1, 20), (2, 10), (3, 10))
    assert sections[1].columns == ("ScanID", "UTC") and sections[1].rows == ()
    assert plan["destinations"] == ["file-a"]


def test_legacy_comparison_captures_authoritative_full_not_sum_of_fights():
    import gsheet_module as gm
    from kvk.services.kvk_export_service import KVK_EXPORT_SECTION_SPECS

    frames = []
    names = {"kvk_no": "KVK_NO", "windowname": "WindowName"}
    for spec in KVK_EXPORT_SECTION_SPECS:
        columns = [names.get(c, c) for c in sorted(spec.required_columns)]
        if "Windowed" in spec.name or "Full" in spec.name:
            row = {c: 99 if "Full" in spec.name else 10 for c in columns}
            row.update(KVK_NO=7, WindowName="Full" if "Full" in spec.name else "Pass 4", campid=1)
            if "Player" in spec.name:
                row.update(governor_id=1, name="player", kingdom=98)
            elif "Kingdom" in spec.name:
                row.update(kingdom=98, camp_name="camp")
            else:
                row.update(camp_name="camp")
            frames.append(pd.DataFrame([row]))
        else:
            frames.append(pd.DataFrame(columns=columns))
    titles = [
        "KVK LIST",
        "KVK_PASS4_ALL_PLAYER_OUTPUT",
        "KVK_1ST_ALTAR_ALL_PLAYER_OUTPUT",
        "KVK_2ND_ALTAR_ALL_PLAYER_OUTPUT",
        "KVK_3RD_ALTAR_ALL_PLAYER_OUTPUT",
        "KVK_PASS7_ALL_PLAYER_OUTPUT",
        "KVK_PASS8_ALL_PLAYER_OUTPUT",
        "KVK_GREATZIG_ALL_PLAYER_OUTPUT",
        "KVK_PASS9_ALL_PLAYER_OUTPUT",
        "ALL_WINDOW_COMPARISON",
    ]
    scope = dict(
        consumer="all_kvk",
        kvk_no=7,
        primary_sheet="KVK LIST",
        spreadsheets={title: "file-" + str(i) for i, title in enumerate(titles)},
    )
    sections, plan = gm.plan_legacy_outputs(scope, frames=frames)
    output = next(o for o in plan["outputs"] if o["tab"] == "PLAYER_DKP")
    section = next(s for s in sections if s.name == output["section"])
    assert section.rows[0][section.columns.index("Overall dkp")] == 99
    assert section.rows[0][section.columns.index("Pass 4 dkp")] == 10


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
