"""Offline bounded reader batching and legacy sequence compatibility."""

from copy import deepcopy
import re
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from kvk.services.new_source_delivery_service import deliver_export
from tests.test_kvk_source_workbooks import setup_reader


def published():
    args, _, api = setup_reader()
    assert deliver_export(**args).delivery_state == "confirmed"
    api.calls.clear()
    return args, api


@pytest.mark.parametrize("batched,expected_reads", [(False, 40), (True, 3)])
def test_complete_reader_comparison_reduces_requests_without_writes(batched, expected_reads):
    from services.export_execution_protocol import from_http
    from services.export_provider_adapter import recorded_clients

    args, api = published()
    before = deepcopy((api.cells, api.grids, api.files_data))
    transport = args["transport"]
    transport.batch_observation_reads = batched
    assert (
        transport.verify(args["destination"], args["generation"].key)
        == args["generation"].manifest()
    )
    requests = [
        a for p, m, a in api.calls if p == "/spreadsheets" and m == "get" and a.get("ranges")
    ]
    assert len(requests) == expected_reads
    assert all(1 <= len(a["ranges"]) <= 16 for a in requests)
    assert all(method == "get" for _, method, _ in api.calls)
    assert (api.cells, api.grids, api.files_data) == before
    sheets, _ = recorded_clients()
    for arguments in requests:
        request = sheets.spreadsheets().get(**arguments)
        from_http(
            method=request.method,
            uri=request.uri,
            body=request.body,
            stream_id=str(uuid4()),
            request_id=str(uuid4()),
        )


@pytest.mark.parametrize(
    "damage",
    ["missing", "duplicate", "foreign", "sheet_id", "offset", "width", "filter", "formula"],
)
def test_batch_damage_never_becomes_verified(damage):
    args, api = published()
    transport = args["transport"]
    transport.batch_observation_reads = True
    execute = api.execute

    def damaged(path, method, arguments, retries):
        result = execute(path, method, arguments, retries)
        if len(arguments.get("ranges", [])) > 1:
            sheet = result["sheets"][0]
            if damage == "missing":
                result["sheets"].pop()
            elif damage == "duplicate":
                result["sheets"][-1] = deepcopy(sheet)
            elif damage == "foreign":
                sheet["properties"]["title"] = "Foreign"
            elif damage == "sheet_id":
                sheet["properties"]["sheetId"] += 1
            elif damage == "offset":
                sheet["data"][0]["startRow"] += 1
            elif damage == "width":
                sheet["data"][0]["columnMetadata"][0]["pixelSize"] += 1
            elif damage == "filter":
                sheet["basicFilter"]["range"]["endRowIndex"] += 1
            else:
                sheet["data"][0]["rowData"][0]["values"][0]["userEnteredValue"] = {
                    "formulaValue": "=1"
                }
        return result

    api.execute = damaged
    with pytest.raises(SourceConflict):
        transport.verify(args["destination"], args["generation"].key)
    assert args["generation"].key not in transport._verified


def test_batches_accept_sheet_order_and_multiple_chunks_but_preserve_exact_cells():
    args, api = published()
    transport = args["transport"]
    transport.batch_observation_reads = True
    transport.batch_rows = 3
    execute = api.execute

    def reversed_sheets(path, method, arguments, retries):
        result = execute(path, method, arguments, retries)
        if len(arguments.get("ranges", [])) > 1:
            result["sheets"].reverse()
        return result

    api.execute = reversed_sheets
    assert (
        transport.verify(args["destination"], args["generation"].key)
        == args["generation"].manifest()
    )


def test_batch_cell_limit_is_preserved_for_large_rectangles():
    args, api = published()
    transport = args["transport"]
    transport.batch_rows = 1000
    requests = []

    def execute(path, method, arguments, retries):
        requests.append(arguments)
        titles = [r.split("'!")[0][1:] for r in arguments["ranges"]]
        return {"sheets": [{"properties": {"title": title}} for title in titles]}

    # Use the same fake SDK request boundary; no provider call is made.
    api.execute = execute
    responses = list(
        transport._batched_cell_responses("fake-1", [(f"Sheet{i}", 700, 100) for i in range(3)])
    )
    assert len(responses) == 6
    for request in requests:
        cells = 0
        for rectangle in request["ranges"]:
            match = re.search(r"!A(\d+):[A-Z]+(\d+)$", rectangle)
            cells += (int(match[2]) - int(match[1]) + 1) * 100
        assert cells <= 50_000


def test_failed_batch_does_not_fall_back_or_retry():
    args, api = published()
    transport = args["transport"]
    transport.batch_observation_reads = True
    execute = api.execute
    attempts = []

    def unavailable(path, method, arguments, retries):
        if arguments.get("ranges"):
            attempts.append(arguments)
            raise OSError("provider unavailable")
        return execute(path, method, arguments, retries)

    api.execute = unavailable
    with pytest.raises(OSError, match="provider unavailable"):
        transport.verify(args["destination"], args["generation"].key)
    assert len(attempts) == 1
    assert args["generation"].key not in transport._verified
