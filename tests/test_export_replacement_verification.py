"""Fresh-file checks never infer ownership, blank cells or safe sharing."""

from copy import deepcopy
import json
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_execution_protocol import ProviderRequest
from services.export_replacement_verification import (
    METADATA,
    ReplacementVerificationPlan,
    discovered_grid,
    replacement_readback,
    replacement_requests,
)
from tests.test_export_enrollment_service import plan_value
from tests.test_export_manual_enrollment import responses


def value():
    original = plan_value()
    return original | dict(
        version=4,
        file_count=1,
        replacement_id=str(uuid4()),
        files=[
            dict(file_id="replacement-file", audience="private", editors=[original["editor_email"]])
        ],
    )


def test_maximum_file_count_has_bounded_plan_and_complete_read_only_scope():
    v = value()
    v["files"] = [
        dict(v["files"][0], file_id=f"replacement-{i:04}-" + "x" * 100) for i in range(1024)
    ]
    v["file_count"] = len(v["files"])
    plan = ReplacementVerificationPlan(v)
    assert len(plan.sql_json.encode("utf-16-le")) > 65536
    scope = dict(
        Purpose="enrollment",
        OwnerKind="preparation",
        AccountKey=v["account"],
        NestedToken=None,
        Epoch=None,
        RegistrationHash=plan.digest,
        SnapshotHash=plan.digest,
        ObjectID=v["plan_id"],
        OwnerID=v["plan_id"],
        Fence=1,
        ClaimVersion=1,
        ScopeJson=json.dumps(
            dict(
                resources=[
                    dict(key=key, version=1)
                    for key in sorted(
                        [
                            "account:" + v["account"],
                            *("destination:" + f["file_id"] for f in v["files"]),
                        ]
                    )
                ],
                enrollment=dict(phase="verify", ordinal=1024),
            )
        ),
    )
    assert 65536 < len(scope["ScopeJson"].encode("utf-16-le")) < 524288
    assert plan.authorize_scope(scope) == dict(phase="verify", ordinal=1024)
    v["files"].append(dict(v["files"][0], file_id="excess-file"))
    v["file_count"] += 1
    with pytest.raises(SourceConflict, match="bounded"):
        ReplacementVerificationPlan(v)


def readback():
    plan = ReplacementVerificationPlan(value())
    grid = dict(file_id="replacement-file", sheet_id=23, title="Sheet1", rows=1000, columns=26)
    return plan, grid, responses(plan, grid)


@pytest.mark.parametrize("audience", ["private", "anyone_reader", "anyone_writer"])
def test_exact_installed_legacy_access_and_automatic_grid_discovery(audience):
    plan, grid, reply = readback()
    v = plan.value()
    v["files"][0]["audience"] = audience
    if audience != "private":
        reply[1]["permissions"].append(
            dict(
                id="public",
                type="anyone",
                role="writer" if audience == "anyone_writer" else "reader",
                allowFileDiscovery=False,
            )
        )
    if audience == "anyone_writer":
        v["files"][0]["editors"].append("anyone")
        v["files"][0]["editors"].sort()
    plan = ReplacementVerificationPlan(v)
    assert discovered_grid(grid["file_id"], reply[2]) == grid
    replacement_readback(plan, v["files"][0], grid, reply)
    for operation, arguments in (METADATA, *replacement_requests(grid)):
        request = ProviderRequest.parse(
            dict(
                version=1,
                request_id=str(uuid4()),
                stream_id=str(uuid4()),
                operation=operation,
                target=grid["file_id"],
                arguments=arguments,
            ),
            enrollment=True,
        )
        plan.authorize_request(request, phase="verify", ordinal=1)


@pytest.mark.parametrize(
    "damage",
    [
        "owner",
        "extra_editor",
        "public",
        "pagination",
        "hidden",
        "cells",
        "formula",
        "huge",
        "wrong_file",
        "extra_tab",
        "metadata",
        "inherited",
    ],
)
def test_unsafe_or_incomplete_replacement_is_rejected(damage):
    plan, grid, reply = readback()
    if damage == "owner":
        reply[0]["owners"] = [dict(emailAddress="other@example.com")]
    elif damage == "extra_editor":
        reply[1]["permissions"].append(
            dict(id="other", type="user", role="writer", emailAddress="other@example.com")
        )
    elif damage == "public":
        reply[1]["permissions"].append(
            dict(id="public", type="anyone", role="reader", allowFileDiscovery=False)
        )
    elif damage == "pagination":
        reply[1]["nextPageToken"] = "more"
    elif damage == "hidden":
        reply[2]["sheets"][0]["properties"]["hidden"] = True
    elif damage == "cells":
        reply[2]["sheets"][0]["data"] = [dict(rowData=[dict(values=[dict(note="existing")])])]
    elif damage == "formula":
        reply[3]["valueRanges"][0]["values"] = [["=1+1"]]
    elif damage == "huge":
        reply[2]["sheets"][0]["properties"]["gridProperties"]["rowCount"] = 1000000
    elif damage == "wrong_file":
        reply[2]["spreadsheetId"] = "different"
    elif damage == "extra_tab":
        reply[2]["sheets"].append(deepcopy(reply[2]["sheets"][0]))
    elif damage == "metadata":
        reply[2]["developerMetadata"] = [dict(metadataKey="old")]
    elif damage == "inherited":
        reply[1]["permissions"][1]["permissionDetails"] = [
            dict(permissionType="file", role="writer", inherited=True)
        ]
    with pytest.raises(SourceConflict):
        replacement_readback(plan, plan.value()["files"][0], grid, reply)


@pytest.mark.parametrize("damage", ["mutation", "other_file", "arbitrary_read", "create_phase"])
def test_read_authority_cannot_escape_the_proposal(damage):
    plan, grid, _ = readback()
    operation, args = METADATA
    target, phase = grid["file_id"], "verify"
    if damage == "mutation":
        operation, args = "sheets.values.clear", dict(range="Sheet1!A1:A1", body={})
    elif damage == "other_file":
        target = "other-file"
    elif damage == "arbitrary_read":
        args = dict(includeGridData=True)
    else:
        phase = "create"
    request = ProviderRequest.parse(
        dict(
            version=1,
            request_id=str(uuid4()),
            stream_id=str(uuid4()),
            operation=operation,
            target=target,
            arguments=args,
        )
    )
    with pytest.raises(SourceConflict):
        plan.authorize_request(request, phase=phase, ordinal=1)
