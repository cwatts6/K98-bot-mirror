"""Direct privilege boundaries and explicit model selection; no SQL workflows."""

import copy
import json
from pathlib import Path
import re
import sqlite3

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from scripts.prepare_s11_sql_account import render
from services import export_sql_direct_permissions as direct
from services.export_execution_dal import (
    LEGACY_DATABASE_CAPABILITIES,
    LEGACY_SERVER_CAPABILITIES,
    installation_migrations,
    installation_permissions,
    legacy_definition_hash,
    legacy_permission_queries,
    validate_legacy_permission_source,
)
from services.export_runtime_composition import (
    validate_legacy_installation_contract,
    verify_legacy_installation_contract,
)


@pytest.fixture
def contract(monkeypatch):
    definitions = {
        "dbo.UPDATE_ALL2": "CREATE PROCEDURE dbo.UPDATE_ALL2 AS SELECT 1;",
        "dbo.child": "CREATE PROCEDURE dbo.child AS SELECT 2;",
        "KVK.ingest": "CREATE PROCEDURE KVK.ingest AS SELECT 3;",
    }
    grants = [
        dict(
            database="ROK_TRACKER",
            principal="ExportLegacyEntryReader",
            securable_class=kind,
            target=target,
            permission=permission,
        )
        for kind, target, permission in (
            ("OBJECT", "dbo.UPDATE_ALL2", "EXECUTE"),
            ("OBJECT", "KVK.ingest", "EXECUTE"),
            ("OBJECT", "dbo.child", "ALTER"),
            ("SCHEMA", "dbo", "ALTER"),
            ("DATABASE", "ROK_TRACKER", "CREATE TABLE"),
        )
    ] + [
        dict(
            database="master",
            principal="$application",
            securable_class="SERVER",
            target="",
            permission="ADMINISTER BULK OPERATIONS",
        )
    ]
    source = dict(
        version=2,
        permission_model="direct_application_v1",
        database="ROK_TRACKER",
        roots=["dbo.UPDATE_ALL2", "KVK.ingest"],
        signatures=[],
        grants=grants,
        modules=[
            dict(
                name=n,
                definition_sha256=legacy_definition_hash(d),
                object_type="P",
                execute_as=None,
            )
            for n, d in definitions.items()
        ],
    )
    monkeypatch.setattr(direct, "DIRECT_SOURCE_HASH", digest(source).hex())
    approved = dict(
        version=2,
        server="fixture-server",
        database="ROK_TRACKER",
        principal="fixture-app",
        login_sid="12" * 16,
        source=source,
        migration_hash="a" * 64,
        metadata_hash="b" * 64,
    )
    observed = {k: [] for k in legacy_permission_queries(source)} | dict(version=2)
    observed["target"] = [
        dict(
            ServerName="fixture-server",
            DatabaseName="ROK_TRACKER",
            Principal="fixture-app",
            LoginName="fixture-app",
            LoginSID="12" * 16,
            DefaultSchema="dbo",
            MajorVersion=16,
            Sysadmin=0,
            DatabaseOwner=0,
            ViewDefinition=1,
            EntryRole=1,
            ReaderRole=0,
            AuthorityRole=1,
            ImpersonateUser=0,
            ImpersonateLogin=0,
        )
    ]
    observed["modules"] = [
        dict(
            ObjectName=n,
            ObjectType="P",
            ModuleDefinition=d,
            AnsiNulls=1,
            QuotedIdentifier=1,
            ExecuteAsPrincipal=None,
            OwnerName="dbo",
        )
        for n, d in definitions.items()
    ]
    observed["grants"] = [
        dict(
            DatabaseName=g["database"],
            PrincipalName=g["principal"],
            SecurableClass=g["securable_class"],
            TargetName=g["target"],
            PermissionName=g["permission"],
            GrantState="G",
            MinorID=0,
        )
        for g in grants
    ]
    observed["application_grants"] = direct.application_grant_rows()
    observed["capabilities"] = [
        dict(
            SecurableClass="DATABASE",
            TargetName="ROK_TRACKER",
            PermissionName=p,
            Allowed=int(p == "CREATE TABLE"),
        )
        for p in LEGACY_DATABASE_CAPABILITIES
    ]
    observed["capabilities"] += [
        dict(
            SecurableClass="SERVER",
            TargetName=None,
            PermissionName=p,
            Allowed=int(p == "ADMINISTER BULK OPERATIONS"),
        )
        for p in LEGACY_SERVER_CAPABILITIES
    ]
    observed["capabilities"] += [
        dict(
            SecurableClass="SCHEMA",
            TargetName=s,
            PermissionName=p,
            Allowed=int(s == "dbo" and p == "ALTER"),
        )
        for s in ("dbo", "KVK")
        for p in ("ALTER", "CONTROL", "TAKE OWNERSHIP")
    ]
    observed["capabilities"] += [
        dict(
            SecurableClass="DATABASE",
            TargetName="ROK_TRACKER",
            PermissionName="CHECKPOINT",
            Allowed=0,
        )
    ]
    observed["module_permissions"] = [
        dict(
            ObjectName=n,
            PermissionName=p,
            Allowed=int(
                (p == "EXECUTE" and n in ("dbo.UPDATE_ALL2", "KVK.ingest"))
                or (p == "ALTER" and n.startswith("dbo."))
            ),
        )
        for n in definitions
        for p in ("EXECUTE", "ALTER", "CONTROL", "TAKE OWNERSHIP")
    ]
    observed["token_grants"] = [
        dict(
            SecurableClass="OBJECT_OR_COLUMN",
            TargetName="dbo.child",
            PermissionName="ALTER",
            GrantState="G",
        ),
        dict(SecurableClass="SCHEMA", TargetName="dbo", PermissionName="ALTER", GrantState="G"),
        dict(
            SecurableClass="DATABASE",
            TargetName="ROK_TRACKER",
            PermissionName="CREATE TABLE",
            GrantState="G",
        ),
    ]
    observed["memberships"] = [
        dict(PrincipalName="fixture-app", RoleName=r)
        for r in ("ExportExecutionAuthority", "ExportLegacyEntryReader")
    ]
    observed["ownership"] = [
        dict(OwnedSchemas=0, OwnedObjects=0, OwnedPrincipals=0, OwnedServerPrincipals=0)
    ]
    observed["migration"] = [
        dict(MigrationId=direct.DIRECT_MIGRATION, ChecksumSha256="a" * 64, Status="Applied"),
        dict(
            MigrationId=direct.STATS_OUTCOME_MIGRATION,
            ChecksumSha256=direct.STATS_OUTCOME_CHECKSUM,
            Status="Applied",
        ),
    ]
    approved["metadata_hash"] = digest(observed).hex()
    return observed, approved


def test_explicit_direct_contract_has_no_signing_inputs(contract):
    observed, approved = contract
    validate_legacy_installation_contract(approved)
    assert (
        verify_legacy_installation_contract(observed, approved, profile="application")
        == digest(observed).hex()
    )
    assert not {"signatures", "certificates", "master_certificates", "principals"} & observed.keys()
    assert "certificate_pins" not in approved


@pytest.fixture
def file_visibility_contract(contract, monkeypatch):
    """Synthetic bodies exercise the same finite, three-module amendment."""
    observed, approved = copy.deepcopy(contract)
    postimages = {}
    historical = {}
    for name in direct.FILE_VISIBILITY_MODULE_HASHES:
        before = f"CREATE PROCEDURE {name} AS SELECT 10;"
        after = f"CREATE PROCEDURE {name} AS SELECT 20;"
        historical[name] = before
        postimages[name] = legacy_definition_hash(after)
        approved["source"]["modules"].append(
            dict(
                name=name,
                definition_sha256=legacy_definition_hash(before),
                object_type="P",
                execute_as=None,
            )
        )
        observed["modules"].append(
            dict(
                ObjectName=name,
                ObjectType="P",
                ModuleDefinition=after,
                AnsiNulls=1,
                QuotedIdentifier=1,
                ExecuteAsPrincipal=None,
                OwnerName="dbo",
            )
        )
        observed["module_permissions"].extend(
            dict(ObjectName=name, PermissionName=right, Allowed=int(right == "ALTER"))
            for right in ("EXECUTE", "ALTER", "CONTROL", "TAKE OWNERSHIP")
        )
    monkeypatch.setattr(direct, "FILE_VISIBILITY_MODULE_HASHES", postimages)
    monkeypatch.setattr(direct, "DIRECT_SOURCE_HASH", digest(approved["source"]).hex())
    approved["module_amendment"] = direct.FILE_VISIBILITY_MIGRATION
    observed["migration"].append(
        dict(
            MigrationId=direct.FILE_VISIBILITY_MIGRATION,
            ChecksumSha256=direct.FILE_VISIBILITY_CHECKSUM,
            Status="Applied",
        )
    )
    approved["metadata_hash"] = digest(observed).hex()
    return observed, approved, historical


def test_file_visibility_amendment_requires_exact_postimages_and_receipt(file_visibility_contract):
    observed, approved, _ = file_visibility_contract
    assert (
        verify_legacy_installation_contract(observed, approved, profile="application")
        == digest(observed).hex()
    )
    query, params = legacy_permission_queries(approved["source"])["migration"]
    assert "MigrationId IN (?,?,?)" in query
    assert params == (
        direct.DIRECT_MIGRATION,
        direct.FILE_VISIBILITY_MIGRATION,
        direct.STATS_OUTCOME_MIGRATION,
    )


@pytest.mark.parametrize(
    "name",
    (
        "dbo.ARCHIVE_IMPORT_STAGING_FILE",
        "dbo.CLAIM_KS4_IMPORT_FILE",
        "dbo.IMPORT_STAGING_PROC_CORE",
    ),
)
@pytest.mark.parametrize("change", ("downgrade", "other_body", "owner", "set_flag", "context"))
def test_file_visibility_amendment_refuses_module_drift_with_resealed_fingerprint(
    file_visibility_contract, name, change
):
    observed, approved, historical = file_visibility_contract
    row = next(r for r in observed["modules"] if r["ObjectName"] == name)
    if change == "downgrade":
        row["ModuleDefinition"] = historical[name]
    elif change == "other_body":
        row["ModuleDefinition"] += " SELECT 30;"
    elif change == "owner":
        row["OwnerName"] = "other"
    elif change == "set_flag":
        row["QuotedIdentifier"] = 0
    else:
        row["ExecuteAsPrincipal"] = 1
    approved["metadata_hash"] = digest(observed).hex()
    with pytest.raises(SourceConflict, match="source/context/owner"):
        verify_legacy_installation_contract(observed, approved, profile="application")


@pytest.mark.parametrize("field,value", (("ChecksumSha256", "0" * 64), ("Status", "Failed")))
def test_file_visibility_amendment_refuses_wrong_receipt(file_visibility_contract, field, value):
    observed, approved, _ = file_visibility_contract
    observed["migration"][-1][field] = value
    approved["metadata_hash"] = digest(observed).hex()
    with pytest.raises(SourceConflict, match="migration receipt"):
        verify_legacy_installation_contract(observed, approved, profile="application")


def test_file_visibility_amendment_cannot_be_selected_by_installed_hash(file_visibility_contract):
    observed, approved, _ = file_visibility_contract
    del approved["module_amendment"]
    with pytest.raises(SourceConflict, match="source/context/owner"):
        verify_legacy_installation_contract(observed, approved, profile="application")


def test_file_visibility_amendment_refuses_arbitrary_amendment(file_visibility_contract):
    _, approved, _ = file_visibility_contract
    approved["module_amendment"] = "unreviewed"
    with pytest.raises(SourceConflict, match="Complete reviewed"):
        validate_legacy_installation_contract(approved)


def test_file_visibility_amendment_preserves_privilege_checks(file_visibility_contract):
    observed, approved, _ = file_visibility_contract
    observed["application_grants"][0]["GrantState"] = "W"
    approved["metadata_hash"] = digest(observed).hex()
    with pytest.raises(SourceConflict, match="grant plan"):
        verify_legacy_installation_contract(observed, approved, profile="application")


@pytest.mark.parametrize(
    "category,field,value",
    [
        ("target", "LoginSID", "34" * 16),
        ("target", "LoginName", "admin"),
        ("target", "Sysadmin", 1),
        ("target", "DatabaseOwner", 1),
        ("target", "AuthorityRole", 0),
        ("target", "ReaderRole", 1),
        ("modules", "ModuleDefinition", "CREATE PROCEDURE dbo.UPDATE_ALL2 AS DELETE dbo.X;"),
        ("modules", "OwnerName", "foreign"),
        ("modules", "ExecuteAsPrincipal", -2),
        ("modules", "AnsiNulls", True),
        ("grants", "GrantState", "W"),
        ("token_grants", "TargetName", "KVK"),
        ("migration", "ChecksumSha256", "c" * 64),
    ],
)
def test_direct_rejects_source_identity_or_privilege_drift_even_with_resealed_metadata(
    contract, category, field, value
):
    observed, approved = contract
    observed[category][0][field] = value
    approved["metadata_hash"] = digest(observed).hex()
    with pytest.raises(SourceConflict):
        verify_legacy_installation_contract(observed, approved, profile="application")


def test_direct_cannot_fall_back_to_reader_or_signed_profile(contract):
    observed, approved = contract
    with pytest.raises(SourceConflict):
        verify_legacy_installation_contract(observed, approved, profile="reader")
    approved["version"] = 1
    with pytest.raises(SourceConflict):
        validate_legacy_installation_contract(approved)


def test_direct_source_mutation_is_not_accepted(contract):
    _, approved = contract
    source = copy.deepcopy(approved["source"])
    source["grants"].append(
        dict(
            database="master",
            principal="$application",
            securable_class="SERVER",
            target="",
            permission="CONTROL SERVER",
        )
    )
    with pytest.raises(SourceConflict):
        validate_legacy_permission_source(source)


@pytest.mark.parametrize(
    "database,permission", [("ROK_TRACKER", "BACKUP DATABASE"), ("master", "CONTROL")]
)
def test_unexpected_direct_database_grants_fail_even_when_metadata_is_resealed(
    contract, database, permission
):
    observed, approved = contract
    observed["application_grants"].append(
        dict(
            DatabaseName=database,
            SecurableClass="DATABASE",
            TargetName=database,
            PermissionName=permission,
            GrantState="G",
            ColumnName=None,
        )
    )
    approved["metadata_hash"] = digest(observed).hex()
    with pytest.raises(SourceConflict, match="exact reviewed grant plan"):
        verify_legacy_installation_contract(observed, approved, profile="application")


def test_application_snapshot_does_not_filter_database_or_object_grant_classes(contract):
    _, approved = contract
    query, _ = legacy_permission_queries(approved["source"])["application_grants"]
    assert "WHERE u.principal_id=USER_ID()" in query
    assert "WHERE u.sid=SUSER_SID()" in query
    assert "AND p.class=1" not in query


def test_application_expected_grants_reject_unreviewed_source(monkeypatch):
    monkeypatch.setattr(direct, "APPLICATION_GRANT_PLAN_HASH", "a" * 64)
    with pytest.raises(SourceConflict, match="grant source differs"):
        direct.application_grant_rows()


def test_master_connect_matches_created_user_and_full_contract(contract):
    observed, approved = contract
    assert [
        row
        for row in observed["application_grants"]
        if row["DatabaseName"] == "master" and row["SecurableClass"] == "DATABASE"
    ] == [
        dict(
            DatabaseName="master",
            SecurableClass="DATABASE",
            TargetName="master",
            PermissionName="CONNECT",
            GrantState="G",
            ColumnName=None,
        )
    ]
    verify_legacy_installation_contract(observed, approved, profile="application")


@pytest.mark.parametrize("drift", [False, True])
def test_direct_application_producer_session_preserves_actual_profile(contract, monkeypatch, drift):
    from unittest.mock import Mock

    from services import export_execution_dal as evidence
    from services.legacy_export_snapshot_dal import LegacySnapshotDAL

    observed, approved = contract
    dal = LegacySnapshotDAL(
        Mock(),
        output_operations=True,
        execution_evidence=True,
        legacy_sql_contract=approved,
        sql_profile="application",
    )
    dal.authorize = Mock()
    cursor = Mock()
    connection = Mock(autocommit=True)
    connection.cursor.return_value = cursor
    snapshot = Mock(return_value=observed)
    monkeypatch.setattr(evidence, "legacy_installation_snapshot", snapshot)
    if drift:
        observed["application_grants"].append(
            dict(
                DatabaseName="master",
                SecurableClass="DATABASE",
                TargetName="master",
                PermissionName="CONTROL",
                GrantState="G",
                ColumnName=None,
            )
        )
        # A new observation fingerprint cannot authorize an unexpected permission.
        dal.legacy_sql_contract["metadata_hash"] = digest(observed).hex()
        with pytest.raises(SourceConflict, match="exact reviewed grant plan"):
            with dal.session("claim", connection):
                pytest.fail("Producer must not enter with unexpected permissions")
        cursor.execute.assert_not_called()
    else:
        with dal.session("claim", connection) as admitted:
            assert admitted == "claim"
        assert "sp_getapplock" in cursor.execute.call_args_list[0].args[0]
        assert "sp_releaseapplock" in cursor.execute.call_args_list[-1].args[0]
    snapshot.assert_called_once_with(cursor, dal.legacy_sql_contract["source"])
    cursor.close.assert_called_once()
    connection.commit.assert_not_called()
    connection.rollback.assert_not_called()
    connection.close.assert_not_called()


@pytest.mark.parametrize("change", ["missing", "deny", "grant_option", "wrong_target"])
def test_master_connect_must_match_exact_reviewed_permission(contract, change):
    observed, approved = contract
    row = next(
        row
        for row in observed["application_grants"]
        if row["DatabaseName"] == "master" and row["PermissionName"] == "CONNECT"
    )
    if change == "missing":
        observed["application_grants"].remove(row)
    elif change == "wrong_target":
        row["TargetName"] = "msdb"
    else:
        row["GrantState"] = "D" if change == "deny" else "W"
    approved["metadata_hash"] = digest(observed).hex()
    with pytest.raises(SourceConflict, match="exact reviewed grant plan"):
        verify_legacy_installation_contract(observed, approved, profile="application")


def test_fixed_direct_profile_retains_evidence_denies_and_old_profiles():
    old = installation_permissions("application")
    new = installation_permissions("application", direct=True)
    assert old[("dbo.usp_ExportReconciliationProofIssue", None, "ALTER")] == 0
    assert new[("dbo.usp_ExportReconciliationProofIssue", None, "ALTER")] == 1
    assert new[("dbo.ExportReconciliationProof", None, "ALTER")] == 0
    assert new[("dbo.ExportReconciliationProof", None, "INSERT")] == 0
    assert new[("KVK.SourceOutputOperation", None, "ALTER")] == 0
    assert "20261001_010_reconciliation_file_id_characters" in installation_migrations(
        dict(version=4)
    )
    assert "20260929_001_manual_export_registration" in installation_migrations(dict(version=3))


def test_direct_renderer_binds_master_user_and_specific_server_grants():
    plan = json.loads(Path("deploy/s11_application_grants.json").read_bytes())
    sql = render(
        plan,
        server="mini_AMD",
        database="ROK_TRACKER",
        principal="S11_ExportApplication",
        login_sid="0x" + "12" * 16,
    )
    assert "Existing master user is not adopted" in sql
    assert "GRANT ADMINISTER BULK OPERATIONS TO [S11_ExportApplication]" in sql
    assert "GRANT EXECUTE ON OBJECT::[dbo].[xp_cmdshell]" in sql
    assert "USE [master];\n" in sql
    assert "GRANT CONNECT TO [S11_ExportApplication];" in sql
    assert (
        "GRANT SELECT ON OBJECT::[sys].[sql_expression_dependencies] TO [S11_ExportApplication];"
        in sql
    )
    assert "ADD SIGNATURE" not in sql and "CREATE CERTIFICATE" not in sql
    assert "ALTER LOGIN [S11_ExportApplication] ENABLE" not in sql
    assert "IF @@TRANCOUNT>0 ROLLBACK TRANSACTION" in sql
    plan["server_permissions"].append("CONTROL SERVER")
    with pytest.raises(ValueError):
        render(
            plan,
            server="mini_AMD",
            database="ROK_TRACKER",
            principal="S11_ExportApplication",
            login_sid="0x" + "12" * 16,
        )


@pytest.mark.parametrize(
    "name,permission,column",
    [
        ("sys.sql_expression_dependencies", "UPDATE", None),
        ("sys.sql_expression_dependencies", "SELECT", "referencing_id"),
        ("sys.sql_modules", "SELECT", None),
    ],
)
def test_renderer_does_not_widen_metadata_catalog_exception(name, permission, column):
    plan = json.loads(Path("deploy/s11_application_grants.json").read_bytes())
    plan["grants"][0].update(object=name, permission=permission)
    if column is not None:
        plan["grants"][0]["column"] = column
    with pytest.raises(ValueError):
        render(
            plan,
            server="mini_AMD",
            database="ROK_TRACKER",
            principal="S11_ExportApplication",
            login_sid="0x" + "12" * 16,
        )


def test_direct_contract_includes_only_approved_dependency_catalog_read():
    rows = direct.application_grant_rows()
    assert [row for row in rows if row["TargetName"].startswith("sys.")] == [
        dict(
            DatabaseName="ROK_TRACKER",
            SecurableClass="OBJECT",
            TargetName="sys.sql_expression_dependencies",
            PermissionName="SELECT",
            GrantState="G",
            ColumnName=None,
        )
    ]


@pytest.mark.parametrize("permissions", [[], ["CONTROL"], ["CONNECT", "CONTROL"]])
def test_renderer_rejects_master_database_permission_widening(permissions):
    plan = json.loads(Path("deploy/s11_application_grants.json").read_bytes())
    plan["master_database_permissions"] = permissions
    with pytest.raises(ValueError, match="Exact reviewed direct legacy grant plan"):
        render(
            plan,
            server="mini_AMD",
            database="ROK_TRACKER",
            principal="S11_ExportApplication",
            login_sid="0x" + "12" * 16,
        )


@pytest.mark.skipif(
    not Path("C:/K98-bot-SQL-Server").is_dir(), reason="Separate SQL source repository required"
)
def test_real_direct_manifest_is_pinned_and_only_changes_permission_delivery():
    root = Path("C:/K98-bot-SQL-Server")
    old = json.loads((root / "deploy/export_legacy_module_permission_manifest.json").read_bytes())
    new = json.loads((root / "deploy/export_legacy_direct_permission_manifest.json").read_bytes())
    with pytest.raises(SourceConflict):
        validate_legacy_permission_source(new)
    assert new["modules"] == old["modules"] and new["roots"] == old["roots"]
    assert new["signatures"] == []
    assert {g["principal"] for g in new["grants"]} == {"ExportLegacyEntryReader", "$application"}


def test_outcome_source_pin_is_explicit_and_rejects_changes():
    source = json.loads(Path("deploy/export_stats_import_outcome_source.json").read_bytes())
    validate_legacy_permission_source(source)
    wrapper = next(m for m in source["modules"] if m["name"] == "dbo.usp_S11RunStatsImport")
    assert wrapper["calls"] == ["dbo.UPDATE_ALL2"]
    assert wrapper["execute_as"] is None
    assert source["signatures"] == []
    wrapper["definition_sha256"] = "0" * 64
    with pytest.raises(SourceConflict):
        validate_legacy_permission_source(source)


def test_outcome_migration_receipt_cannot_be_omitted_or_resealed(contract):
    observed, approved = contract
    observed["migration"] = [observed["migration"][0]]
    approved["metadata_hash"] = digest(observed).hex()
    with pytest.raises(SourceConflict, match="migration receipt"):
        verify_legacy_installation_contract(observed, approved, profile="application")


def test_membership_union_has_explicit_collation_for_each_name(contract):
    """Catalog names from master/server retain exact case across DB collations."""
    source = contract[1]["source"]
    query, parameters = legacy_permission_queries(source)["memberships"]
    assert parameters == ()
    assert "u.name COLLATE Latin1_General_100_BIN2 AS PrincipalName" in query
    assert "r.name COLLATE Latin1_General_100_BIN2 AS RoleName" in query
    assert (
        "'$master' COLLATE Latin1_General_100_BIN2,r.name COLLATE Latin1_General_100_BIN2" in query
    )
    assert (
        "'$server' COLLATE Latin1_General_100_BIN2,r.name COLLATE Latin1_General_100_BIN2" in query
    )
    assert "u.sid=SUSER_SID()" in query
    assert "WHERE u.name=USER_NAME() OR u.name='ExportLegacyEntryReader'" in query


@pytest.mark.parametrize(
    "category", ["grants", "memberships", "application_grants", "token_grants"]
)
def test_direct_snapshot_order_covers_projection_and_stabilizes_fingerprint(contract, category):
    """An omitted field must not leave equal sort keys for distinct fingerprint rows."""
    observed, approved = contract
    query, _ = legacy_permission_queries(approved["source"])[category]
    match = re.search(r"\bORDER BY\s+([A-Za-z_,\s]+)\s*$", query)
    assert match is not None, "The complete UNION result needs a terminal ORDER BY."
    fields = tuple(observed[category][0])
    order = tuple(name.strip() for name in match[1].split(","))
    assert len(order) == len(set(order)) and set(order) == set(fields)

    # Each row differs from the base in only one projected field. Missing any
    # sort key would tie two different rows and make their digest order-sensitive.
    base = {
        name: 0 if name == "MinorID" else None if name == "ColumnName" else "A" for name in fields
    }
    samples = [base]
    for name in fields:
        samples.append({**base, name: 1 if name == "MinorID" else "B"})
    fingerprints = []
    with sqlite3.connect(":memory:") as connection:
        connection.create_collation(
            "Latin1_General_100_BIN2",
            lambda left, right: (
                (left.encode("utf-16-be") > right.encode("utf-16-be"))
                - (left.encode("utf-16-be") < right.encode("utf-16-be"))
            ),
        )
        projections = ",".join(
            "?" + ("" if name == "MinorID" else " COLLATE Latin1_General_100_BIN2") + " AS " + name
            for name in fields
        )
        statement = " UNION ALL ".join("SELECT " + projections for _ in samples)
        statement += " ORDER BY " + ",".join(order)
        for inputs in (samples, list(reversed(samples)), samples[1:] + samples[:1]):
            rows = connection.execute(statement, [row[name] for row in inputs for name in fields])
            fingerprints.append(digest([dict(zip(fields, row, strict=True)) for row in rows]))
    assert len(set(fingerprints)) == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("SecurableClass", "OBJECT"),
        ("TargetName", "dbo.other"),
        ("PermissionName", "CONTROL"),
        ("GrantState", "W"),
    ],
)
def test_token_object_grant_requires_exact_catalog_class_and_privilege(contract, field, value):
    observed, approved = contract
    row = next(r for r in observed["token_grants"] if r["SecurableClass"] == "OBJECT_OR_COLUMN")
    row[field] = value
    approved["metadata_hash"] = digest(observed).hex()
    with pytest.raises(SourceConflict):
        verify_legacy_installation_contract(observed, approved, profile="application")
