"""Direct privilege boundaries and explicit model selection; no SQL workflows."""

import copy
import json
from pathlib import Path

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
        dict(MigrationId=direct.DIRECT_MIGRATION, ChecksumSha256="a" * 64, Status="Applied")
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
    validate_legacy_permission_source(new)
    assert new["modules"] == old["modules"] and new["roots"] == old["roots"]
    assert new["signatures"] == []
    assert {g["principal"] for g in new["grants"]} == {"ExportLegacyEntryReader", "$application"}
