import json
from uuid import uuid4

import pytest

from services.export_execution_protocol import (
    ProtocolError,
    ProviderRequest,
    ProviderThrottled,
    decode,
    encode,
    validate_response,
)


@pytest.mark.parametrize(
    "header,expected",
    [
        (None, "1.0"),
        ("provider prose", "1.0"),
        ("x" * 129, "1.0"),
        ("inf", "1.0"),
        ("NaN", "1.0"),
        ("-10", "1.0"),
        ("9000", "3600.0"),
        ("12.5", "12.5"),
        ("Wed, 21 Oct 2015 07:28:00 GMT", "Wed, 21 Oct 2015 07:28:00 GMT"),
    ],
)
def test_throttle_feedback_is_bounded_and_preserves_absolute_dates(header, expected):
    request_id = str(uuid4())
    failure = ProviderThrottled.from_header(429, header)
    wire = decode(encode(failure.message(request_id)))
    parsed = ProviderThrottled.parse(wire, request_id=request_id)
    assert parsed.status == 429
    assert parsed.retry_after == expected
    assert len(encode(wire)) < 160
    assert str(parsed) == "Provider throttling requires reconciliation."


@pytest.mark.parametrize(
    "change",
    [
        {"status": 400},
        {"status": True},
        {"status": 429.0},
        {"request_id": str(uuid4())},
        {"error": "unproven_outcome"},
        {"retry_after": "arbitrary provider text"},
        {"retry_after": "9000.0"},
        {"retry_after": 12},
        {"retry_after": "NaN"},
        {"retry_after": "x" * 1000},
        {"result": {}},
    ],
)
def test_child_throttle_envelope_rejects_wrong_identity_or_unbounded_fields(change):
    request_id = str(uuid4())
    wire = ProviderThrottled.from_header(503, "12").message(request_id)
    with pytest.raises(ProtocolError):
        ProviderThrottled.parse(wire | change, request_id=request_id)


def message(operation="sheets.values.update", arguments=None):
    return dict(
        version=1,
        request_id=str(uuid4()),
        stream_id=str(uuid4()),
        operation=operation,
        target="registered_file",
        arguments=(
            arguments
            if arguments is not None
            else {
                "range": "Sheet1!A1",
                "valueInputOption": "RAW",
                "body": {"values": [["=not_a_formula", 2]]},
            }
        ),
    )


def test_catalogue_hash_vector_matches_the_authored_sql_binary_contract():
    from services.export_execution_protocol import CATALOGUE_SEED, catalogue_step

    assert (
        CATALOGUE_SEED.hex() == "f47f228dc11112ca1ee887f92cc4e90fe3c3885a9d7b412961550da8da83f270"
    )
    assert (
        catalogue_step(
            CATALOGUE_SEED, "11111111-2222-3333-4444-555555555555", 7, b"\x22" * 32
        ).hex()
        == "80a986bfbbcc45879d65c7bf60ed3d2e74019cd160da725f66b1e295d77fe73c"
    )


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "old_list",
        "duplicate",
        "version",
        "targets",
        "negative",
        "boolean",
        "hash",
        "probe",
        "huge",
    ],
)
def test_proof_membership_is_exact_and_bounds_representation_without_dropping_history(damage):
    from services.export_execution_protocol import CATALOGUE_SEED, proof_membership

    value = dict(
        version=2,
        targets=["file-a", "file-b"],
        history=dict(count=50000, sha256=CATALOGUE_SEED.hex()),
        probe=dict(stream_id="11111111-2222-3333-4444-555555555555", version=7),
    )
    if damage == "old_list":
        value = [value["probe"]]
    elif damage == "version":
        value["version"] = True
    elif damage == "targets":
        value["targets"] = ["file-b", "file-a"]
    elif damage == "negative":
        value["history"]["count"] = -1
    elif damage == "boolean":
        value["history"]["count"] = True
    elif damage == "hash":
        value["history"]["sha256"] = "G" * 64
    elif damage == "probe":
        value["probe"]["version"] = 0
    elif damage == "huge":
        value["targets"] = ["x" * 65536]
    raw = json.dumps(value)
    if damage == "duplicate":
        raw = raw.replace('"version": 2', '"version": 2, "version": 2', 1)
    if damage:
        with pytest.raises(ProtocolError):
            proof_membership(raw)
    else:
        assert proof_membership(raw) == value
        assert len(raw) < 1024  # Counter/root, not an ever-growing ID receipt.


def test_request_roundtrip_freezes_caller_mutable_arguments():
    value = message()
    request = ProviderRequest.parse(decode(encode(value)))
    value["arguments"]["body"]["values"][0][0] = "changed"
    assert request.arguments["body"]["values"][0][0] == "=not_a_formula"
    assert request.mutation


@pytest.mark.parametrize(
    "change",
    [
        {"version": True},
        {"version": 2},
        {"operation": "drive.files.copy"},
        {"target": "https://attacker.invalid"},
        {"target": "../file"},
        {"request_id": "not-uuid"},
        {"arguments": {"url": "https://attacker.invalid"}},
        {
            "arguments": {
                "range": "A1",
                "valueInputOption": "USER_ENTERED",
                "body": {"values": [[1]]},
            }
        },
        {"arguments": {"range": "A1", "valueInputOption": "RAW", "body": {"values": [[{}]]}}},
    ],
)
def test_protocol_rejects_widened_scope(change):
    with pytest.raises(ProtocolError):
        ProviderRequest.parse(message() | change)


@pytest.mark.parametrize("raw", [b'{"version":1,"version":2}', b'{"x":NaN}', b"[]", b"\xff", b"{"])
def test_decoder_rejects_duplicate_nonfinite_and_nonobjects(raw):
    with pytest.raises(ProtocolError):
        decode(raw)


@pytest.mark.parametrize(
    "response",
    [
        {},
        {"spreadsheetId": "other"},
        {
            "spreadsheetId": "registered_file",
            "updatedRange": "A1",
            "updatedRows": True,
            "updatedColumns": 1,
            "updatedCells": 1,
        },
    ],
)
def test_update_requires_exact_identity_and_complete_terminal_body(response):
    with pytest.raises(ProtocolError):
        validate_response(ProviderRequest.parse(message()), response)


def test_values_get_does_not_invent_spreadsheet_id_field():
    request = ProviderRequest.parse(message("sheets.values.get", {"range": "Sheet1!A1"}))
    validate_response(request, {"range": "Sheet1!A1", "values": [[1]]})


def test_batch_reply_membership_and_raw_body_are_required():
    request = ProviderRequest.parse(
        message("sheets.batchUpdate", {"body": {"requests": [{"deleteSheet": {"sheetId": 4}}]}})
    )
    with pytest.raises(ProtocolError):
        validate_response(request, {"spreadsheetId": "registered_file", "replies": []})
    validate_response(request, {"spreadsheetId": "registered_file", "replies": [{}]})


@pytest.mark.parametrize(
    "body",
    [
        {"type": "anyone", "role": "writer"},
        {"type": "user", "role": "reader", "emailAddress": "other@example.invalid"},
    ],
)
def test_permission_operation_cannot_grant_a_different_audience(body):
    with pytest.raises(ProtocolError):
        ProviderRequest.parse(message("drive.permissions.create", {"body": body}))


def test_clear_generation_properties_preserves_existing_transport_contract():
    request = ProviderRequest.parse(
        message(
            "drive.files.update",
            {
                "body": {"appProperties": {"k98Generation": None}, "description": ""},
                "fields": "id",
            },
        )
    )
    validate_response(request, {"id": "registered_file"})


def test_response_bytes_are_bounded_and_finite():
    with pytest.raises(ProtocolError):
        encode({"value": float("inf")})
    with pytest.raises(ProtocolError):
        decode(json.dumps({"x": "x" * (16 * 1024 * 1024)}).encode())


@pytest.mark.parametrize(
    "uri",
    [
        "http://sheets.googleapis.com/v4/spreadsheets/file-a",
        "https://attacker.invalid/v4/spreadsheets/file-a",
        "https://sheets.googleapis.com/v4/spreadsheets",
        "https://sheets.googleapis.com/v4/spreadsheets/file-a?fields=id&fields=title",
        "https://sheets.googleapis.com/v4/spreadsheets/file-a#ignored",
        "https://sheets.googleapis.com/v4/spreadsheets/file-a?access_token=secret",
    ],
)
def test_sdk_translation_refuses_unknown_or_ambiguous_endpoint(uri):
    from services.export_execution_protocol import from_http

    with pytest.raises(ProtocolError):
        from_http(method="GET", uri=uri, body=None, stream_id=str(uuid4()), request_id=str(uuid4()))


def test_sdk_translation_preserves_quoted_range_and_literal_raw_cells():
    from services.export_execution_protocol import from_http

    request = from_http(
        method="PUT",
        uri="https://sheets.googleapis.com/v4/spreadsheets/file-a/values/%27A%20B%27%21A1?valueInputOption=RAW&alt=json",
        body='{"values":[["=RAW"]]}',
        stream_id=str(uuid4()),
        request_id=str(uuid4()),
    )
    assert request.arguments == {
        "range": "'A B'!A1",
        "valueInputOption": "RAW",
        "body": {"values": [["=RAW"]]},
    }


def test_batch_read_sdk_translation_preserves_repeated_range_order():
    from services.export_execution_protocol import from_http

    request = from_http(
        method="GET",
        uri="https://sheets.googleapis.com/v4/spreadsheets/registered_file/values:batchGet?ranges=%27A%27!A1:B2&ranges=%27B%27!A1:A1&valueRenderOption=FORMULA&alt=json",
        body=None,
        stream_id=str(uuid4()),
        request_id=str(uuid4()),
    )
    assert request.arguments == {
        "ranges": ["'A'!A1:B2", "'B'!A1:A1"],
        "valueRenderOption": "FORMULA",
    }
    assert not request.mutation
    validate_response(
        request,
        {
            "spreadsheetId": request.target,
            "valueRanges": [
                {"range": "A!A1:B2", "values": [["x", "y"]]},
                {"range": "B!A1:A1"},
            ],
        },
    )


@pytest.mark.parametrize(
    "ranges",
    [
        [],
        ["A!A1:B2"] * 17,
        ["A!A1:B2", "'A'!A1:B2"],
        ["A!A1:Z2000"],
        ["A!A1"],
        ["A!B2:A1"],
        ["A!A0:B2"],
        ["A!A1:ZZZZ2"],
        [False],
    ],
)
def test_batch_read_refuses_ambiguous_or_excessive_rectangles(ranges):
    with pytest.raises(ProtocolError):
        ProviderRequest.parse(message("sheets.values.batchGet", {"ranges": ranges}))


@pytest.mark.parametrize(
    "blocks",
    [
        [],
        [{"range": "other!A1:B2"}],
        [{"range": "A!A1:B2", "values": [[1, 2, 3]]}],
        [{"range": "A!A1:B2", "values": [[1], [2], [3]]}],
        [{"range": "A!A1:B2", "values": [{"bad": "row"}]}],
        [{"range": "A!A1:B2", "majorDimension": "COLUMNS"}],
    ],
)
def test_batch_read_success_requires_complete_exact_range_and_values(blocks):
    request = ProviderRequest.parse(message("sheets.values.batchGet", {"ranges": ["'A'!A1:B2"]}))
    with pytest.raises(ProtocolError):
        validate_response(request, {"spreadsheetId": request.target, "valueRanges": blocks})


def test_batch_read_cannot_merge_query_and_parameter_range_lists():
    from services.export_execution_protocol import from_http

    with pytest.raises(ProtocolError, match="Duplicate"):
        from_http(
            method="GET",
            uri="https://sheets.googleapis.com/v4/spreadsheets/registered_file/values:batchGet?ranges=A!A1:A2",
            body=None,
            params={"ranges": ["B!A1:A2"]},
            stream_id=str(uuid4()),
            request_id=str(uuid4()),
        )


def test_retirement_deletes_exact_metadata_and_accepts_empty_property_clear():
    request = ProviderRequest.parse(
        message(
            "sheets.batchUpdate",
            {
                "body": {
                    "requests": [
                        {"deleteNamedRange": {"namedRangeId": "named-1"}},
                        {
                            "deleteDeveloperMetadata": {
                                "dataFilter": {"developerMetadataLookup": {"metadataId": 7}}
                            }
                        },
                    ]
                }
            },
        )
    )
    validate_response(
        request,
        {
            "spreadsheetId": request.target,
            "replies": [
                {},
                {"deleteDeveloperMetadata": {"deletedDeveloperMetadata": [{"metadataId": 7}]}},
            ],
        },
    )
    with pytest.raises(ProtocolError, match="Metadata deletion"):
        validate_response(
            request,
            {
                "spreadsheetId": request.target,
                "replies": [
                    {},
                    {"deleteDeveloperMetadata": {"deletedDeveloperMetadata": [{"metadataId": 8}]}},
                ],
            },
        )
    ProviderRequest.parse(
        message(
            "drive.files.update", {"body": {"appProperties": {}, "description": ""}, "fields": "id"}
        )
    )


@pytest.mark.parametrize(
    "instruction",
    [
        {"dataFilter": {"developerMetadataLookup": {}}},
        {"dataFilter": {"developerMetadataLookup": {"metadataKey": "all"}}},
        {"dataFilter": {"developerMetadataLookup": {"metadataId": True}}},
        {"dataFilter": {"developerMetadataLookup": {"metadataId": 7, "metadataKey": "all"}}},
        {"dataFilter": {"a1Range": "Sheet1"}},
    ],
)
def test_retirement_cannot_broaden_metadata_deletion_filter(instruction):
    with pytest.raises(ProtocolError):
        ProviderRequest.parse(
            message(
                "sheets.batchUpdate",
                {"body": {"requests": [{"deleteDeveloperMetadata": instruction}]}},
            )
        )
