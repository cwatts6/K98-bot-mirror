"""An active foreign stream must not strand an unclaimed configuration ticket."""

from copy import deepcopy
import json
import os
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_execution_dal import ExportExecutionDAL
from services.legacy_export_snapshot_dal import LegacySnapshotDAL
from services.legacy_export_snapshot_service import ConfigurationAdmissionDeferred
from tests.test_import_capture_recovery_sql import recovery as recovery
from tests.test_legacy_export_snapshot import producer_runtime

pytestmark = [
    pytest.mark.skipif(
        os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Local disposable SQL opt-in"
    ),
    pytest.mark.parametrize("recovery", ["configuration_continuation"], indirect=True),
]


def test_refused_probe_withdraws_its_ticket_without_changing_foreign_stream(recovery, tmp_path):
    runtime, _ = producer_runtime(
        tmp_path, configuration={"config": {"destinations": ["file-probe-test"]}}
    )
    runtime.account = "probe-" + uuid4().hex
    # The disposable schema has no installed production permission profile.
    # Exercise the real locked gate against the fixture's exact stream table.
    runtime.dal = LegacySnapshotDAL(recovery.connect, output_operations=True)
    runtime.dal.execution_evidence = True
    runtime.authority_stream = Mock()
    stream = str(uuid4())
    recovery.owner.execute(
        recovery.rewrite(
            "INSERT dbo.ExportExecutionStream "
            "(StreamID,SessionID,AccountKey,ActiveAccountKey,JobID,OwnerID,Fence,"
            "ClaimVersion,RegistrationHash,SnapshotHash,ScopeJson,Purpose,State,"
            "Version,LastSequence,ChildIdentity,CreatedUTC) "
            "VALUES(?,?,?,?,?,?,1,1,?,?,?,'mutation','open',1,0,?,SYSUTCDATETIME())"
        ),
        stream,
        str(uuid4()),
        runtime.account,
        runtime.account,
        str(uuid4()),
        str(uuid4()),
        b"a" * 32,
        b"b" * 32,
        json.dumps({"resources": []}),
        str(uuid4()),
    )

    def stream_row():
        return tuple(
            recovery.owner.execute(
                recovery.rewrite("SELECT * FROM dbo.ExportExecutionStream WHERE StreamID=?"),
                stream,
            ).fetchone()
        )

    before = deepcopy(stream_row())
    # Release/settlement callers still receive a conflict, not a successful gate.
    connection = recovery.connect()
    try:
        with pytest.raises(SourceConflict):
            ExportExecutionDAL.assert_no_active_stream(connection.cursor(), runtime.account)
    finally:
        connection.rollback()
        connection.close()
    with pytest.raises(ConfigurationAdmissionDeferred):
        with runtime.configuration_requests():
            pytest.fail("A refused probe must never contact the provider")
    runtime.authority_stream.assert_not_called()
    assert stream_row() == before
    row = recovery.owner.execute(
        recovery.rewrite(
            "SELECT State,OwnerID,Fence FROM dbo.ExportPreparation WHERE AccountKey=?"
        ),
        runtime.account,
    ).fetchone()
    assert row.State == "unavailable"
    assert row.OwnerID is not None and row.Fence == 1
    assert (
        recovery.owner.execute(
            recovery.rewrite(
                "SELECT COUNT(*) FROM dbo.ExportResource WHERE ActivePreparationID IN "
                "(SELECT PreparationID FROM dbo.ExportPreparation WHERE AccountKey=?)"
            ),
            runtime.account,
        ).fetchval()
        == 0
    )
