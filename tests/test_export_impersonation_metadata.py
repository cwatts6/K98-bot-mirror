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
    assert "HAS_PERMS_BY_NAME(p.name,'USER','IMPERSONATE')" in sql
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
    assert dal.USER_IMPERSONATION_SQL in queries["target"][0]
    assert "AS ImpersonateUser" in queries["target"][0]


@pytest.mark.parametrize("value", [None, 1])
def test_direct_unknown_or_present_impersonation_fails_closed(monkeypatch, value):
    from services.export_sql_direct_permissions import verify

    observed, approved = direct_fixture(monkeypatch)
    observed["target"][0]["ImpersonateUser"] = value
    with pytest.raises(SourceConflict):
        verify(observed, approved, profile="application")
