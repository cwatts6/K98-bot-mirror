"""SQL Server impersonation read regression; no execution or grants."""

import json
from unittest.mock import Mock

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services import export_execution_dal as dal
from services.export_runtime_composition import verify_installation_contract
from tests.test_export_runtime_composition import installation_fixture
from tests.test_export_sql_direct_permissions import contract

direct_fixture = contract.__wrapped__


def test_fixed_read_uses_effective_user_permission_and_bounded_scope(monkeypatch):
    observed, _ = installation_fixture()
    connection, cursor = Mock(), Mock()
    connection.cursor.return_value = cursor
    monkeypatch.setattr(dal, "one", lambda _: observed["target"])
    results = iter(
        [
            observed["migrations"],
            *(observed["metadata"][k] for k in dal._METADATA_QUERIES),
            observed["permissions"],
        ]
    )
    monkeypatch.setattr(dal, "rows", lambda _: next(results))
    dal.ExportExecutionDAL(lambda: connection).installation_snapshot()
    sql = cursor.execute.call_args_list[0].args[0]
    assert "'DATABASE','IMPERSONATE ANY USER'" not in sql
    assert "HAS_PERMS_BY_NAME(p.name,''USER'',''IMPERSONATE'')" in sql
    assert "TOP (1001)" in sql and "COUNT_BIG(*)>1000 THEN NULL" in sql
    assert "COUNT(Allowed)<>COUNT_BIG(*) THEN NULL" in sql
    assert "p.principal_id<>USER_ID()" in sql
    assert "EXECUTE AS" not in sql
    connection.commit.assert_not_called()
    cursor.close.assert_called_once()


@pytest.mark.parametrize("value", [None, 1])
def test_fixed_unknown_or_present_impersonation_fails_closed(value):
    observed, approved = installation_fixture()
    observed["target"]["ImpersonateUser"] = value
    with pytest.raises(SourceConflict):
        verify_installation_contract(observed, approved)


def test_legacy_query_has_no_invalid_database_capability(monkeypatch):
    _, approved = direct_fixture(monkeypatch)
    queries = dal.legacy_permission_queries(approved["source"])
    capabilities = json.loads(queries["capabilities"][1][0])
    assert not any(c["permission"] == "IMPERSONATE ANY USER" for c in capabilities)
    assert "sys.databases" in queries["target"][0]
    assert "QUOTENAME(@database)" in queries["target"][0]
    assert "AS ImpersonateUser" in queries["target"][0]


@pytest.mark.parametrize("value", [None, 1])
def test_direct_unknown_or_present_impersonation_fails_closed(monkeypatch, value):
    from services.export_sql_direct_permissions import verify

    observed, approved = direct_fixture(monkeypatch)
    observed["target"][0]["ImpersonateUser"] = value
    with pytest.raises(SourceConflict):
        verify(observed, approved, profile="application")


def test_cross_database_scope_uses_actual_caller_and_fails_closed():
    sql = dal.user_impersonation_query(
        "SELECT " + dal.USER_IMPERSONATION_SQL + " AS ImpersonateUser"
    )
    assert "HAS_DBACCESS(name)" in sql
    assert "FROM sys.databases" in sql
    assert "DatabaseName sysname COLLATE Latin1_General_100_BIN2" in sql
    assert "HAS_PERMS_BY_NAME(NULL,NULL,'VIEW ANY DATABASE')" in sql
    assert "COUNT_BIG(*) FROM @databases)>1000" in sql
    assert "CanAccess IS NULL" in sql
    assert "IF @allowed IS NULL" in sql
    assert "QUOTENAME(@database)" in sql
    assert "EXECUTE AS" not in sql and "GRANT " not in sql
    assert "SELECT @user_impersonation AS ImpersonateUser" in sql


def test_server_capabilities_use_documented_null_server_class(monkeypatch):
    _, approved = direct_fixture(monkeypatch)
    query = dal.legacy_permission_queries(approved["source"])["capabilities"][0]
    assert "SecurableClass='SERVER' THEN HAS_PERMS_BY_NAME(NULL,NULL,PermissionName)" in query
    assert "ELSE HAS_PERMS_BY_NAME(TargetName,SecurableClass,PermissionName)" in query


@pytest.mark.parametrize("value", [None, 1])
def test_signed_unknown_or_present_impersonation_fails_closed(monkeypatch, value):
    from services.export_runtime_composition import verify_legacy_installation_contract
    from tests.test_export_runtime_composition import legacy_permission_fixture

    observed, approved = legacy_permission_fixture(monkeypatch)
    observed["target"][0]["ImpersonateUser"] = value
    approved["metadata_hash"] = dal.digest(observed).hex()
    with pytest.raises(SourceConflict):
        verify_legacy_installation_contract(observed, approved)
