"""An existing provider stream refuses admission without stranding a health ticket."""

from contextlib import contextmanager
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.legacy_export_snapshot_dal import LegacySnapshotDAL
from services.legacy_export_snapshot_service import ConfigurationAdmissionDeferred
from tests.test_legacy_export_snapshot import producer_runtime


@pytest.mark.parametrize("commit_lost", [False, True])
def test_active_stream_health_probe_withdraws_only_after_acknowledged_refusal(
    monkeypatch, tmp_path, commit_lost
):
    import services.export_execution_dal as execution
    import services.legacy_export_snapshot_dal as preparation

    runtime, _ = producer_runtime(tmp_path, configuration={"config": {"destinations": ["file-a"]}})
    cursor = Mock()
    identifier, existing_stream = str(uuid4()), str(uuid4())
    claim_writes = Mock()
    statements = []

    def execute(sql, *params):
        statements.append(sql)
        cursor.answer = None
        if sql.startswith("SELECT * FROM dbo.ExportResource"):
            cursor.answer = dict(
                ResourceKey=params[0],
                ActiveJobID=None,
                ActivePreparationID=None,
                ActiveOutputOperationID=None,
                BlockedReason=None,
                Fence=0,
                Version=1,
            )
        elif sql.startswith("SELECT * FROM dbo.ExportPreparation"):
            cursor.answer = dict(
                AccountKey=runtime.account,
                StorageOwner=runtime.store.storage_owner,
                ConsumerKind="config",
                State="pending",
                EnqueueSequence=4,
                Fence=0,
                Version=1,
            )
        elif sql.startswith("SELECT StreamID FROM dbo.ExportExecutionStream"):
            assert params == (runtime.account,)
            assert "UPDLOCK,HOLDLOCK" in sql
            cursor.answer = {"StreamID": existing_stream}
        return cursor

    @contextmanager
    def transaction(_):
        yield cursor
        if commit_lost:
            raise OSError("synthetic commit acknowledgement lost")

    cursor.execute.side_effect = execute
    monkeypatch.setattr(preparation, "transaction", transaction)
    monkeypatch.setattr(preparation, "one", lambda c: c.answer)
    monkeypatch.setattr(execution, "one", lambda c: c.answer)
    monkeypatch.setattr(preparation, "_mutex", Mock())
    monkeypatch.setattr(preparation, "_cas", claim_writes)
    dal = LegacySnapshotDAL(Mock(), output_operations=True)
    dal.execution_evidence = True
    dal.request = Mock(return_value=identifier)
    dal.withdraw_unstarted = Mock()
    runtime.dal = dal
    runtime.authority_stream = Mock()
    with pytest.raises(OSError if commit_lost else ConfigurationAdmissionDeferred):
        with runtime.configuration_requests():
            pytest.fail("A refused health probe must not execute provider work")
    claim_writes.assert_not_called()
    runtime.authority_stream.assert_not_called()
    assert any(s.startswith("SELECT StreamID") for s in statements)
    if commit_lost:
        dal.withdraw_unstarted.assert_not_called()
    else:
        dal.withdraw_unstarted.assert_called_once_with(identifier)


def test_unknown_admission_failure_is_not_converted_to_refusal(tmp_path):
    runtime, dal = producer_runtime(
        tmp_path, configuration={"config": {"destinations": ["file-a"]}}
    )
    dal.claim.side_effect = SourceConflict("unattributed admission failure")
    with pytest.raises(SourceConflict):
        with runtime.configuration_requests():
            pytest.fail("No provider work may start")
    dal.withdraw_unstarted.assert_not_called()
