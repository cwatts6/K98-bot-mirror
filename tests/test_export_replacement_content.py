from copy import deepcopy
from types import SimpleNamespace

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_replacement_publication import legacy_content
from services.legacy_export_snapshot_service import OutputSection, output_digest


def legacy_records():
    def event(operation, arguments, response=None):
        return (
            SimpleNamespace(
                operation=operation,
                target="fresh-file",
                arguments=arguments,
                mutation=operation not in {"sheets.get", "sheets.values.get"},
            ),
            response or {},
        )

    return [
        event("sheets.get", {}, {"sheets": [{"properties": {"sheetId": 7, "title": "Report"}}]}),
        event("sheets.values.clear", {"range": "'Report'"}),
        event(
            "sheets.values.update",
            {
                "range": "'Report'!A1",
                "valueInputOption": "RAW",
                "body": {"values": [["ID", "Value"], [1, "retained"]]},
            },
        ),
        event(
            "sheets.values.get",
            {"range": "'Report'", "valueRenderOption": "UNFORMATTED_VALUE"},
            {"values": [["ID", "Value"], [1, "retained"]]},
        ),
    ]


def expected_hash():
    return output_digest((OutputSection("old-file:Report", ("ID", "Value"), ((1, "retained"),)),))


def test_private_content_reconstructs_original_capture_through_multiple_replacements():
    records = legacy_records()
    legacy_content(
        records, [{"old-file": "middle-file"}, {"middle-file": "fresh-file"}], expected_hash()
    )
    legacy_content(
        records,
        [{"old-file": "fresh-file"}, *[{f"unrelated-{i}": f"elsewhere-{i}"} for i in range(100)]],
        expected_hash(),
    )


@pytest.mark.parametrize(
    "damage",
    [
        "wrong_data",
        "wrong_readback",
        "missing_clear",
        "missing_write",
        "missing_readback",
        "overlap",
        "repeated_output",
        "formula_mode",
        "later_grid_resize",
        "extra_data_write",
    ],
)
def test_false_publication_cannot_resolve_original_content(damage):
    records = legacy_records()
    if damage == "wrong_data":
        records[2][0].arguments["body"]["values"][1][1] = "another report"
        records[3][1]["values"][1][1] = "another report"
    elif damage == "wrong_readback":
        records[3][1]["values"][1][1] = "changed"
    elif damage.startswith("missing_"):
        records.pop({"missing_clear": 1, "missing_write": 2, "missing_readback": 3}[damage])
    elif damage == "overlap":
        records.insert(3, deepcopy(records[2]))
    elif damage == "repeated_output":
        records.extend(deepcopy(records[1:]))
    elif damage == "formula_mode":
        records[2][0].arguments["valueInputOption"] = "USER_ENTERED"
    elif damage == "extra_data_write":
        records.append(
            (
                SimpleNamespace(
                    operation="sheets.batchUpdate",
                    target="fresh-file",
                    mutation=True,
                    arguments={"body": {"requests": [{"updateCells": {}}]}},
                ),
                {},
            )
        )
    else:
        records.append(
            (
                SimpleNamespace(
                    operation="sheets.batchUpdate",
                    target="fresh-file",
                    mutation=True,
                    arguments={
                        "body": {
                            "requests": [
                                {
                                    "updateSheetProperties": {
                                        "properties": {
                                            "sheetId": 7,
                                            "gridProperties": {"rowCount": 1, "columnCount": 1},
                                        },
                                        "fields": "gridProperties.rowCount,gridProperties.columnCount",
                                    }
                                }
                            ]
                        }
                    },
                ),
                {},
            )
        )
    with pytest.raises(SourceConflict):
        legacy_content(records, [{"old-file": "fresh-file"}], expected_hash())


def test_reader_publication_requires_complete_final_private_content(monkeypatch):
    from threading import Event
    from unittest.mock import Mock
    from uuid import uuid4

    from kvk.dal.new_source_import_dal import digest
    from kvk.services import new_source_reader_service
    from kvk.services.new_source_delivery_service import deliver_coordinated_export
    from kvk.services.new_source_workbook_transport import ReaderSheetsTransport
    from services.export_execution_protocol import ProviderRequest, validate_response
    from services.export_replacement_publication import source_content
    from tests.test_kvk_source_workbooks import setup_reader

    args, _, api = setup_reader()
    original = args["generation"]
    monkeypatch.setattr(
        new_source_reader_service, "load_reader_projection", Mock(return_value=original.projection)
    )
    records = []
    stream_id = str(uuid4())

    def execute(message):
        request = ProviderRequest.parse(message)
        arguments = deepcopy(request.arguments)
        if request.operation.startswith("drive."):
            _, resource, method = request.operation.split(".")
            arguments["fileId"] = request.target
            result = api.execute("/" + resource, method, arguments, 0)
        else:
            path = "/spreadsheets/values" if ".values." in request.operation else "/spreadsheets"
            arguments["spreadsheetId"] = request.target
            result = api.execute(path, request.operation.split(".")[-1], arguments, 0)
            if request.operation == "sheets.values.get":
                result["range"] = arguments["range"]
            else:
                result["spreadsheetId"] = request.target
            if request.operation == "sheets.batchUpdate":
                result["replies"] = [{} for _ in arguments["body"]["requests"]]
        validate_response(request, result)
        records.append((request, deepcopy(result)))
        return result

    registration = args["transport"].registration
    transport = ReaderSheetsTransport.from_authority(
        registration=registration,
        reuse_guard=lambda *_: False,
        protected_file_ids=(),
        execution=execute,
        stream_id=stream_id,
        authorize=lambda **_: None,
    )
    job = dict(
        ConsumerKind="new_source",
        IntentID="intent-a",
        InputHash=b"a" * 32,
        KVK_NO=16,
        DestinationSetHash=digest(tuple(sorted(("fake-index", "fake-1", "fake-2")))),
    )
    dal, retained = Mock(), {}

    def begin(_, manifest, parts):
        retained.update(manifest=deepcopy(manifest))
        return "attempt-a"

    dal.begin_attempt.side_effect = begin
    receipt = deliver_coordinated_export(
        job=job,
        claim=SimpleNamespace(fence=10),
        dal=dal,
        transport=transport,
        connect=None,
        budget=lambda: None,
        stop=Event(),
        reader_guild_id="123",
    )
    kwargs = dict(
        registration=registration,
        generation=retained["manifest"],
        files=receipt["files"],
        fence=10,
        stream_id=stream_id,
        expected=dict(generation_key=original.key, manifest_hash=digest(original.manifest()).hex()),
    )
    assert source_content(records, **kwargs) == receipt["remote_id"]
    with pytest.raises(SourceConflict, match="transcript"):
        source_content(records[:-1], **kwargs)
    changed = deepcopy(retained["manifest"])
    changed["content_key"] = "other-generation"
    with pytest.raises(SourceConflict, match="original content"):
        source_content(records, **dict(kwargs, generation=changed))
    # A mutation after the readback makes the old successful reads insufficient.
    mutation = next(record for record in records if record[0].mutation)
    with pytest.raises(SourceConflict, match="final private readback"):
        source_content([*records, mutation], **kwargs)
