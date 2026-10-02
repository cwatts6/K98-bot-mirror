"""Offline public-link manual enrollment contracts; no provider or SQL I/O."""

from copy import deepcopy

import pytest
import test_export_manual_enrollment as legacy

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_enrollment_service import ManagedOriginVerifier
from services.export_manual_enrollment import (
    ManualEnrollmentPlan,
    manual_readback,
    manual_requests,
)


def public_value():
    return legacy.manual_value() | dict(version=3, access_policy="public_viewer_link_v1")


def public_responses(plan, file):
    response = legacy.responses(plan, file)
    owner, editor = response[1]["permissions"]
    owner["permissionDetails"] = [
        dict(permissionType="file", role="owner", inherited=False),
        dict(permissionType="file", role="writer", inherited=True),
    ]
    editor["permissionDetails"] = [dict(permissionType="file", role="writer", inherited=False)]
    response[1]["permissions"].append(
        dict(
            id="anyoneWithLink",
            type="anyone",
            role="reader",
            allowFileDiscovery=False,
            permissionDetails=[dict(permissionType="file", role="reader", inherited=False)],
        )
    )
    return response


def test_public_policy_accepts_direct_grants_and_same_owner_inheritance():
    plan = ManualEnrollmentPlan(public_value())
    file = plan.value()["files"][0]
    manual_readback(plan, file, public_responses(plan, file))


@pytest.mark.parametrize(
    "damage",
    [
        "extra_editor",
        "extra_viewer",
        "public_writer",
        "public_commenter",
        "discoverable",
        "discovery_missing",
        "editor_inherited",
        "editor_details_null",
        "owner_direct_missing",
        "owner_wrong",
        "owner_inherited_owner",
        "detail_role",
        "detail_type",
        "detail_bool",
        "detail_extra",
        "detail_duplicate",
        "detail_not_object",
        "details_not_list",
        "principal_type",
        "permission_id_duplicate",
        "pending_owner",
        "deleted",
        "expiry",
        "domain",
        "published_view",
        "pagination",
        "nonblank",
        "hidden",
        "frozen",
        "extra_tab",
        "private",
        "wrong_owner_metadata",
    ],
)
def test_public_policy_rejects_unsafe_or_incomplete_readback(damage):
    plan = ManualEnrollmentPlan(public_value())
    file = plan.value()["files"][0]
    response = public_responses(plan, file)
    acl = response[1]
    owner, editor, public = acl["permissions"]
    detail = editor["permissionDetails"][0]
    if damage.startswith("extra_") and damage != "extra_tab":
        acl["permissions"].append(
            dict(
                id="extra",
                type="user",
                role="reader" if damage == "extra_viewer" else "writer",
                emailAddress="other@example.com",
            )
        )
    elif damage in {"public_writer", "public_commenter"}:
        public["role"] = damage.removeprefix("public_")
        public["permissionDetails"][0]["role"] = public["role"]
    elif damage == "discoverable":
        public["allowFileDiscovery"] = True
    elif damage == "discovery_missing":
        del public["allowFileDiscovery"]
    elif damage == "editor_inherited":
        detail["inherited"] = True
    elif damage == "editor_details_null":
        editor["permissionDetails"] = None
    elif damage == "owner_direct_missing":
        owner["permissionDetails"].pop(0)
    elif damage == "owner_wrong":
        owner["emailAddress"] = "wrong@example.com"
    elif damage == "owner_inherited_owner":
        owner["permissionDetails"][1]["role"] = "owner"
    elif damage == "detail_role":
        detail["role"] = "reader"
    elif damage == "detail_type":
        detail["permissionType"] = "member"
    elif damage == "detail_bool":
        detail["inherited"] = 0
    elif damage == "detail_extra":
        detail["inheritedFrom"] = "unreviewed-parent"
    elif damage == "detail_duplicate":
        editor["permissionDetails"].append(deepcopy(detail))
    elif damage == "detail_not_object":
        editor["permissionDetails"] = [None]
    elif damage == "details_not_list":
        editor["permissionDetails"] = {}
    elif damage == "principal_type":
        editor["type"] = "group"
    elif damage == "permission_id_duplicate":
        editor["id"] = owner["id"]
    elif damage == "pending_owner":
        editor["pendingOwner"] = True
    elif damage == "deleted":
        editor["deleted"] = True
    elif damage == "expiry":
        editor["expirationTime"] = "2099-01-01T00:00:00Z"
    elif damage == "domain":
        public["domain"] = "example.com"
    elif damage == "published_view":
        public["view"] = "published"
    elif damage == "pagination":
        acl["nextPageToken"] = "more"
    elif damage == "nonblank":
        response[3]["valueRanges"][0]["values"] = [["retain"]]
    elif damage == "hidden":
        response[2]["sheets"][0]["properties"]["hidden"] = True
    elif damage == "frozen":
        response[2]["sheets"][0]["properties"]["gridProperties"]["frozenRowCount"] = 1
    elif damage == "extra_tab":
        response[2]["sheets"].append({})
    elif damage == "private":
        acl["permissions"].pop()
    elif damage == "wrong_owner_metadata":
        response[0]["owners"][0]["emailAddress"] = "other@example.com"
    else:
        raise AssertionError(damage)
    with pytest.raises(SourceConflict):
        manual_readback(plan, file, response)


def test_version_two_receipts_and_requests_keep_private_semantics():
    plan = ManualEnrollmentPlan(legacy.manual_value())
    file = plan.value()["files"][0]
    manual_readback(plan, file, legacy.responses(plan, file))
    with pytest.raises(SourceConflict):
        manual_readback(plan, file, public_responses(plan, file))
    old_request = manual_requests(file, version=2)[1][1]
    assert old_request["pageSize"] == 1000
    assert "allowFileDiscovery" not in old_request["fields"]


@pytest.mark.parametrize(
    "version,policy",
    [
        (2, "public_viewer_link_v1"),
        (3, None),
        (3, "private"),
        (4, "public_viewer_link_v1"),
        (True, "public_viewer_link_v1"),
    ],
)
def test_version_and_policy_are_bound(version, policy):
    value = legacy.manual_value() | dict(version=version)
    if policy is not None:
        value["access_policy"] = policy
    with pytest.raises(SourceConflict):
        ManualEnrollmentPlan(value)


def test_version_three_authorizes_only_exact_bounded_read_requests():
    plan = ManualEnrollmentPlan(public_value())
    file = plan.value()["files"][0]
    requests = manual_requests(file, version=3)
    assert len(requests) == 4
    assert requests[1][1]["pageSize"] == 100
    assert "allowFileDiscovery" in requests[1][1]["fields"]
    # Exercising the actual plan authorizer prevents widening the provider field mask.
    for op, args in requests:
        request = type(
            "Request",
            (),
            dict(operation=op, arguments=args, target=file["file_id"], mutation=False),
        )()
        plan.authorize_request(request, phase="verify", ordinal=3)
    op, args = manual_requests(file, version=2)[1]
    wrong = type(
        "Request",
        (),
        dict(operation=op, arguments=args, target=file["file_id"], mutation=False),
    )()
    with pytest.raises(SourceConflict):
        plan.authorize_request(wrong, phase="verify", ordinal=3)


def public_runtime(monkeypatch):
    value = public_value()
    original_responses = legacy.responses
    sample_plan = ManualEnrollmentPlan(value)
    fixtures = {f["file_id"]: public_responses(sample_plan, f) for f in value["files"]}
    monkeypatch.setattr(legacy, "manual_value", lambda: deepcopy(value))
    monkeypatch.setattr(
        legacy,
        "responses",
        lambda plan, file: (
            deepcopy(fixtures[file["file_id"]])
            if plan.value()["version"] == 3
            else original_responses(plan, file)
        ),
    )
    return legacy.runtime()


def test_public_registration_reconciles_original_policy_without_new_requests(
    monkeypatch,
):
    runtime = public_runtime(monkeypatch)
    seal = runtime.runner.run(actor="admin", reason="public policy")
    assert seal["version"] == 3 and len(runtime.sent) == 12
    assert all(not request.mutation for request in runtime.sent)
    verifier = ManagedOriginVerifier(dal=runtime.dal, store=runtime.store)
    for _ in range(2):
        assert (
            verifier.verify(
                account="account-a",
                targets=sorted(f["file_id"] for f in runtime.plan.value()["files"]),
                owner_email="owner@example.com",
                editor_email="export@test-project.iam.gserviceaccount.com",
            )
            == seal
        )
    assert len(runtime.sent) == 12
    assert all(
        r.arguments["pageSize"] == 100
        for r in runtime.sent
        if r.operation == "drive.permissions.list"
    )


@pytest.mark.parametrize(
    "failure", ["drive.permissions.list", "sheets.get", "closure", "begin", "complete"]
)
def test_public_uncertainty_does_not_retry_or_release(monkeypatch, failure):
    runtime = public_runtime(monkeypatch)
    if failure in {"begin", "complete"}:
        runtime.dal.fail = ("manual_enrollment", failure)
    else:
        runtime.failure = failure
    from services.export_execution_authority import ExecutionUncertain

    with pytest.raises((ExecutionUncertain, RuntimeError)):
        runtime.runner.run(actor="admin", reason="public policy")
    sent = len(runtime.sent)
    with pytest.raises(SourceConflict):
        runtime.runner.run(actor="admin", reason="retry")
    assert len(runtime.sent) == sent


@pytest.mark.parametrize("omitted", [(0,), (1,), (2,), (0, 1, 2)])
def test_my_drive_acl_accepts_omitted_details_but_keeps_exact_principals(omitted):
    plan = ManualEnrollmentPlan(public_value())
    file = plan.value()["files"][0]
    response = public_responses(plan, file)
    for index in omitted:
        response[1]["permissions"][index].pop("permissionDetails")
    manual_readback(plan, file, response)
    response[1]["permissions"][1]["emailAddress"] = "other@example.com"
    with pytest.raises(SourceConflict):
        manual_readback(plan, file, response)
