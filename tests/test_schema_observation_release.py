"""Shared observer must preserve actual SQL transaction state, not infer it."""

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.application_maintenance_dal import schema_observation
from tests.test_application_maintenance_contract import Cursor


@pytest.mark.parametrize("autocommit", [True, False])
@pytest.mark.parametrize("transaction_count", [0, 1, 2])
def test_observation_preserves_both_transaction_states(autocommit, transaction_count):
    cursor = Cursor([], autocommit=autocommit, transaction_count=transaction_count)
    with schema_observation(cursor):
        assert cursor.held
        assert cursor.transaction_count == transaction_count
        assert cursor.connection.autocommit is autocommit
    assert not cursor.held
    assert cursor.transaction_count == transaction_count
    assert cursor.connection.autocommit is autocommit
    sql = " ".join(s for s, _ in cursor.calls).upper()
    assert "BEGIN TRAN" not in sql and "COMMIT TRAN" not in sql and "ROLLBACK" not in sql
    assert "SET TRANSACTION ISOLATION" not in sql


@pytest.mark.parametrize("owner", ["session", "transaction"])
@pytest.mark.parametrize("mode", ["Shared", "Exclusive", "Update"])
def test_existing_locks_refused_without_upgrade(owner, mode):
    cursor = Cursor(
        [],
        transaction_count=1,
        mode=mode if owner == "session" else "NoLock",
        transaction_mode=mode if owner == "transaction" else "NoLock",
    )
    with pytest.raises(SourceConflict):
        with schema_observation(cursor):
            pytest.fail("Must not enter under caller-owned lock")
    assert len(cursor.calls) == 1
    assert cursor.transaction_count == 1


def test_engine_model_rejects_original_unconditional_transaction_function():
    cursor = Cursor([], autocommit=True, transaction_count=0)
    with pytest.raises(RuntimeError, match="SQL3918"):
        cursor.execute("SELECT APPLOCK_MODE('public',?,'Transaction') FROM sys.dm_exec_sessions")


def test_no_transaction_function_is_in_control_flow_branch():
    cursor = Cursor([], autocommit=True)
    with schema_observation(cursor):
        pass
    sql, parameters = cursor.calls[0]
    assert sql.startswith("DECLARE @transaction_mode nvarchar(32)=N'NoLock'; ")
    assert "IF @@TRANCOUNT>0 SET @transaction_mode=APPLOCK_MODE('public',?,'Transaction');" in sql
    assert "CASE" not in sql  # Do not rely on optimizer expression evaluation order.
    assert len(parameters) == 2 and parameters[0] == parameters[1]
