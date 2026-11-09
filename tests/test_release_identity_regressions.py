"""Permanent reproduction of the 2026-11-09 permission projection failure."""

from copy import deepcopy

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from scripts.project_application_permissions import project_new_object_permissions
from services.export_runtime_composition import verify_application_installation_contract
from tests.test_export_schema_fingerprint import portable_contract


def permission_fixture():
    # Native CI ordering puts a_lower before Z_upper. Python's tuple sort
    # puts Z_upper first. These are synthetic names, retaining the real cause.
    before = dict(
        schema_permissions=[dict(SchemaName="dbo", PermissionName="SELECT", Subentity="")],
        object_permissions=[
            dict(ObjectName="dbo.A", PermissionName="SELECT", Subentity=name)
            for name in ("", "a_lower", "Z_upper")
        ],
        column_permissions=[
            dict(ObjectName="dbo.A", ColumnName=name, PermissionName="SELECT", Allowed=1)
            for name in ("Z_upper", "a_lower")
        ],
    )
    additions = deepcopy(before)
    for section in ("object_permissions", "column_permissions"):
        for row in additions[section]:
            row["ObjectName"] = "dbo.B"
    return before, additions


def project(before, additions):
    return project_new_object_permissions(
        before, additions, before_sha256=digest(before).hex(), new_objects={"dbo.B"}
    )


def test_native_permission_order_survives_projection_and_real_startup_verification(monkeypatch):
    before, additions = permission_fixture()
    preserved = deepcopy((before, additions))
    result = project(before, additions)
    # Independent native expected rows, not generated with the projection sorter.
    expected = dict(
        schema_permissions=before["schema_permissions"],
        object_permissions=before["object_permissions"] + additions["object_permissions"],
        column_permissions=before["column_permissions"] + additions["column_permissions"],
    )
    assert result == expected
    assert (before, additions) == preserved
    observed, approved = portable_contract(monkeypatch)
    observed.update(expected)
    approved["permissions_hash"] = digest(result).hex()
    assert verify_application_installation_contract(observed, approved)

    # Reproduce the old compiler exactly. Equal rows are insufficient: a wrong
    # expectation must fail the unchanged runtime permission fingerprint check.
    wrong = deepcopy(result)
    wrong["object_permissions"].sort(
        key=lambda row: (row["ObjectName"], row["PermissionName"], row["Subentity"])
    )
    assert wrong != expected
    approved["permissions_hash"] = digest(wrong).hex()
    with pytest.raises(SourceConflict, match="permissions"):
        verify_application_installation_contract(observed, approved)


@pytest.mark.parametrize("section", ["object_permissions", "column_permissions"])
def test_new_group_merges_before_old_groups_without_sorting_inside_them(section):
    before, additions = permission_fixture()
    for key in ("object_permissions", "column_permissions"):
        for row in before[key]:
            row["ObjectName"] = "dbo.Z"
    result = project(before, additions)
    assert result[section] == additions[section] + before[section]
    result[section][0]["PermissionName"] = "CONTROL"
    assert additions[section][0]["PermissionName"] == "SELECT"


@pytest.mark.parametrize("damage", ["right", "column", "allowed", "missing", "extra"])
def test_real_permission_drift_is_not_hidden_by_projection(monkeypatch, damage):
    before, additions = permission_fixture()
    expected = project(before, additions)
    observed, approved = portable_contract(monkeypatch)
    observed.update(deepcopy(expected))
    approved["permissions_hash"] = digest(expected).hex()
    if damage == "right":
        observed["object_permissions"][0]["PermissionName"] = "CONTROL"
    elif damage == "column":
        observed["column_permissions"][0]["ColumnName"] = "other"
    elif damage == "allowed":
        observed["column_permissions"][0]["Allowed"] = 0
    elif damage == "missing":
        observed["object_permissions"].pop()
    else:
        observed["object_permissions"].append(dict(expected["object_permissions"][0]))
    with pytest.raises(SourceConflict, match="permissions"):
        verify_application_installation_contract(observed, approved)


@pytest.mark.parametrize("damage", ["hash", "schema", "overlap", "scope", "unknown", "duplicate"])
def test_projection_refuses_unqualified_evidence(damage):
    before, additions = permission_fixture()
    before_hash = digest(before).hex()
    if damage == "hash":
        before["object_permissions"][0]["PermissionName"] = "CONTROL"
    elif damage == "schema":
        additions["schema_permissions"] = []
    elif damage == "overlap":
        before["object_permissions"][0]["ObjectName"] = "dbo.B"
        before["object_permissions"].sort(key=lambda row: row["ObjectName"])
        before_hash = digest(before).hex()
    elif damage == "scope":
        additions["column_permissions"][0]["ObjectName"] = "dbo.Other"
    elif damage == "unknown":
        additions["column_permissions"][0]["Allowed"] = None
    else:
        additions["object_permissions"].append(dict(additions["object_permissions"][0]))
    with pytest.raises(ValueError):
        project_new_object_permissions(
            before, additions, before_sha256=before_hash, new_objects={"dbo.B"}
        )
