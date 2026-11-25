"""Successor comparison forms must retain exact bodies, denials and source pins.

Only fixture source approval is substituted. No candidate/release hash is added
to the runtime's independently pinned allowlist by these tests or this change.
"""

from copy import deepcopy
import hashlib

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services import export_sql_direct_permissions as direct
from services.catalogue_observation_dal import canonical_module
from services.export_execution_dal import legacy_definition_hash, validate_legacy_permission_source
from services.export_runtime_composition import verify_legacy_installation_contract
from tests.test_export_sql_direct_permissions import contract as predecessor_contract


@pytest.fixture
def contract(monkeypatch):
    observed, approved = predecessor_contract.__wrapped__(monkeypatch)
    observed, approved = deepcopy(observed), deepcopy(approved)
    for name in ("dbo.KVKFinalReportHeader", "dbo.MaintenanceKvkWork", "dbo.MaintenanceWork"):
        approved["source"]["grants"].append(
            dict(
                database="ROK_TRACKER",
                principal="ExportLegacyEntryReader",
                securable_class="OBJECT",
                target=name,
                permission="ALTER",
                state="D",
            )
        )
        observed["grants"].append(
            dict(
                DatabaseName="ROK_TRACKER",
                PrincipalName="ExportLegacyEntryReader",
                SecurableClass="OBJECT",
                TargetName=name,
                PermissionName="ALTER",
                GrantState="D",
                MinorID=0,
            )
        )
    module = next(row for row in approved["source"]["modules"] if row["name"] == "dbo.child")
    row = next(row for row in observed["modules"] if row["ObjectName"] == "dbo.child")
    body = "CREATE PROCEDURE dbo.child AS\n SELECT 2;\n \t\n"
    module["definition_format"] = "module_header_lf_body_exact_v1"
    module["definition_sha256"] = hashlib.sha256(
        canonical_module(body).encode("utf-16-le")
    ).hexdigest()
    row["ModuleDefinition"] = body
    approved["metadata_hash"] = digest(observed).hex()
    monkeypatch.setattr(direct, "DIRECT_SOURCE_HASH", digest(approved["source"]).hex())
    return observed, approved


def test_complete_comparator_accepts_only_source_selected_exact_body_and_denials(contract):
    observed, approved = contract
    before = deepcopy((observed, approved))
    assert (
        verify_legacy_installation_contract(observed, approved, profile="application")
        == digest(observed).hex()
    )
    assert (observed, approved) == before
    # Token escalation rows intentionally describe grants; the separate exact
    # permission inventory must include all three denials.
    assert not any(row["GrantState"] == "D" for row in observed["token_grants"])
    assert sum(row["GrantState"] == "D" for row in observed["grants"]) == 3


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "grant",
        "grant_option",
        "wrong_object",
        "column",
        "duplicate",
        "denial_as_granted_token",
    ],
)
def test_denial_drift_fails_even_if_overall_fixture_hash_is_rebound(contract, damage):
    observed, approved = contract
    row = observed["grants"][-1]
    if damage == "missing":
        observed["grants"].pop()
    elif damage in {"grant", "grant_option"}:
        row["GrantState"] = "G" if damage == "grant" else "W"
    elif damage == "wrong_object":
        row["TargetName"] = "dbo.Other"
    elif damage == "column":
        row["MinorID"] = 1
    elif damage == "duplicate":
        observed["grants"].append(deepcopy(row))
    else:
        observed["token_grants"].append(
            dict(
                SecurableClass="OBJECT_OR_COLUMN",
                TargetName=row["TargetName"],
                PermissionName="ALTER",
                GrantState="G",
            )
        )
    approved["metadata_hash"] = digest(observed).hex()
    with pytest.raises(SourceConflict, match="exact reviewed grant plan"):
        verify_legacy_installation_contract(observed, approved, profile="application")


@pytest.mark.parametrize("damage", ["body", "trailing_space", "trailing_newline"])
def test_exact_body_format_does_not_trim_or_accept_other_body_bytes(contract, damage):
    observed, approved = contract
    row = next(row for row in observed["modules"] if row["ObjectName"] == "dbo.child")
    if damage == "body":
        row["ModuleDefinition"] = row["ModuleDefinition"].replace("SELECT 2", "SELECT 3")
    else:
        row["ModuleDefinition"] += " " if damage == "trailing_space" else "\n"
    approved["metadata_hash"] = digest(observed).hex()
    with pytest.raises(SourceConflict, match="source/context/owner"):
        verify_legacy_installation_contract(observed, approved, profile="application")


@pytest.mark.parametrize("header", ["ALTER   PROCEDURE", "CREATE OR ALTER\tPROCEDURE"])
def test_explicit_body_format_supports_header_and_crlf_transport_only(contract, header):
    observed, approved = contract
    row = next(row for row in observed["modules"] if row["ObjectName"] == "dbo.child")
    row["ModuleDefinition"] = (
        row["ModuleDefinition"].replace("CREATE PROCEDURE", header).replace("\n", "\r\n")
    )
    approved["metadata_hash"] = digest(observed).hex()
    verify_legacy_installation_contract(observed, approved, profile="application")


@pytest.mark.parametrize("format_value", [None, "future", 1, "module_header_lf_body_exact_v1"])
def test_unknown_format_or_extra_compatible_bodies_refuse(contract, monkeypatch, format_value):
    observed, approved = contract
    module = next(row for row in approved["source"]["modules"] if row["name"] == "dbo.child")
    module["definition_format"] = format_value
    if format_value == "module_header_lf_body_exact_v1":
        module["compatible_definition_sha256"] = []
    monkeypatch.setattr(direct, "DIRECT_SOURCE_HASH", digest(approved["source"]).hex())
    with pytest.raises(SourceConflict, match="body format"):
        verify_legacy_installation_contract(observed, approved, profile="application")


def test_candidate_forms_do_not_bypass_independent_source_approval(monkeypatch):
    _, approved = predecessor_contract.__wrapped__(monkeypatch)
    approved["source"]["modules"][0]["definition_format"] = "module_header_lf_body_exact_v1"
    with pytest.raises(SourceConflict, match="reviewed legacy SQL source"):
        validate_legacy_permission_source(approved["source"])


def test_historical_hash_default_and_unknown_format_are_explicit():
    body = "CREATE PROCEDURE dbo.Example AS SELECT 1;"
    expected = hashlib.sha256(body.encode("utf-16-le")).hexdigest()
    assert legacy_definition_hash(" \n" + body.replace("CREATE", "ALTER", 1) + "\t\r\n") == expected
    with pytest.raises(SourceConflict, match="Unsupported"):
        legacy_definition_hash(body, definition_format="future")
