"""Real local holder/requester identity in a new disposable database only."""

from time import monotonic
from uuid import UUID

import pytest

from services import sql_lock_holder_diagnostics as diagnostics
from services.legacy_snapshot_admission import SnapshotAdmissionRefused, acquire_snapshot_guard
from services.sql_lock_holder_diagnostics import SNAPSHOT_RESOURCE, observe_holder


@pytest.mark.parametrize("owner", ["Session", "Transaction"])
def test_actual_holder_identity_and_disappearing_owner(snapshot_database, owner):
    import pyodbc

    holder = pyodbc.connect(snapshot_database.connection_string, autocommit=True, timeout=5)
    requester = pyodbc.connect(snapshot_database.connection_string, autocommit=True, timeout=5)
    try:
        holder.timeout = requester.timeout = 15
        holder_id = holder.execute("SELECT @@SPID").fetchval()
        requester_id = requester.execute("SELECT @@SPID").fetchval()
        holder.execute("BEGIN TRANSACTION")
        holder.execute(
            "DECLARE @r int; EXEC @r=sys.sp_getapplock "
            "@Resource=?,@LockMode='Exclusive',@LockOwner=?,@LockTimeout=0; "
            "IF @r<0 THROW 50000,'Fixture refused',1;",
            SNAPSHOT_RESOURCE,
            owner,
        )
        started = monotonic()
        with pytest.raises(SnapshotAdmissionRefused) as caught:
            acquire_snapshot_guard(requester.cursor())
        assert monotonic() - started < 3
        evidence = caught.value.holder_observation
        assert evidence["status"] == "observed_after_refusal", (
            evidence,
            getattr(caught.value.__cause__, "__notes__", []),
        )
        assert evidence["holder"]["session_id"] == holder_id != requester_id
        assert evidence["requester"]["session_id"] == requester_id
        assert evidence["holder"]["owner_type"] == owner.upper()
        UUID(evidence["holder"]["connection_id"])
        assert requester.timeout == 15
        holder.execute("ROLLBACK")
        if owner == "Session":
            holder.execute(
                "EXEC sys.sp_releaseapplock @Resource=?,@LockOwner='Session'", SNAPSHOT_RESOURCE
            )
        # A similarly named foreign lock is not the refused resource.
        holder.execute(
            "EXEC sys.sp_getapplock @Resource=?,@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0",
            SNAPSHOT_RESOURCE + "-other",
        )
        missing = observe_holder(
            requester.cursor(),
            resource=SNAPSHOT_RESOURCE,
            requester=requester_id,
            original=RuntimeError(),
        )
        assert missing == dict(status="unavailable", reason="holder_disappeared_or_ambiguous")
    finally:
        holder.close()
        requester.close()


def test_unprivileged_diagnostic_is_unavailable_without_new_grants(snapshot_database):
    import pyodbc

    connection = pyodbc.connect(snapshot_database.connection_string, autocommit=True, timeout=5)
    try:
        connection.timeout = 15
        connection.execute("CREATE USER HolderProbe WITHOUT LOGIN; EXECUTE AS USER='HolderProbe'")
        result = observe_holder(
            connection.cursor(),
            resource=SNAPSHOT_RESOURCE,
            requester=connection.execute("SELECT @@SPID").fetchval(),
            original=RuntimeError(),
        )
        assert result == dict(status="unavailable", reason="permission_unavailable")
        assert connection.timeout == 15
    finally:
        connection.close()


def test_actual_diagnostic_timeout_preserves_refusal_and_restores_budget(
    snapshot_database, monkeypatch
):
    import pyodbc

    holder = pyodbc.connect(snapshot_database.connection_string, autocommit=True, timeout=5)
    requester = pyodbc.connect(snapshot_database.connection_string, autocommit=True, timeout=5)
    try:
        holder.timeout = requester.timeout = 15
        holder.execute(
            "EXEC sys.sp_getapplock @Resource=?,@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0",
            SNAPSHOT_RESOURCE,
        )
        monkeypatch.setattr(
            diagnostics, "_QUERY", "WAITFOR DELAY '00:00:05'; " + diagnostics._QUERY
        )
        started = monotonic()
        with pytest.raises(SnapshotAdmissionRefused) as caught:
            acquire_snapshot_guard(requester.cursor())
        assert monotonic() - started < 3
        assert caught.value.holder_observation == dict(
            status="unavailable", reason="observation_failed"
        )
        assert caught.value.__cause__.args[0] == "42000"
        assert "(51421)" in caught.value.__cause__.args[1]
        assert requester.timeout == 15
        assert requester.execute("SELECT 1").fetchval() == 1
    finally:
        holder.close()
        requester.close()
