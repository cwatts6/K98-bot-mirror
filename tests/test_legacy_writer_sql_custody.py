"""An ended Python scope does not prove a writer's SQL handles or guard released."""

from unittest.mock import Mock

import pytest

from core import sql_connection_custody as custody
from services.legacy_export_snapshot_dal import LegacySnapshotDAL
from services.legacy_export_snapshot_service import LegacyExportRuntime, WriterOwner


@pytest.mark.parametrize("failure_phase", ["grant", "body", "release", "cursor_close"])
def test_session_guard_preserves_first_failure_and_checks_lost_grant(failure_phase):
    dal = LegacySnapshotDAL(Mock())
    dal.authorize = Mock()
    cn = Mock(autocommit=True)
    cur = cn.cursor.return_value
    cur.fetchone.return_value = ("NoLock",)
    first = OSError("private first")

    def execute(sql, *_):
        if failure_phase == "grant" and "sp_getapplock" in sql:
            raise first
        if failure_phase == "release" and "sp_releaseapplock" in sql:
            raise first

    cur.execute.side_effect = execute
    if failure_phase == "cursor_close":
        cur.close.side_effect = first
    expected = OSError if failure_phase in {"grant", "body"} else custody.SqlCleanupUnknown
    with pytest.raises(expected) as caught:
        with dal.session("claim", cn):
            if failure_phase == "body":
                raise first
    assert (caught.value is first) if expected is OSError else (caught.value.__cause__ is first)
    assert any("APPLOCK_MODE" in call.args[0] for call in cur.execute.call_args_list)
    cur.close.assert_called_once()
    cn.close.assert_not_called()  # Caller owns this connection.
    assert bool(custody.custody_snapshot()["unconfirmed"]) is (
        failure_phase in {"release", "cursor_close"}
    )


def test_unacknowledged_guard_mode_is_not_physical_release():
    dal = LegacySnapshotDAL(Mock())
    dal.authorize = Mock()
    cn = Mock(autocommit=True)
    cn.cursor.return_value.fetchone.return_value = ("Exclusive",)
    with pytest.raises(custody.SqlCleanupUnknown):
        with dal.session("claim", cn):
            pass
    assert custody.custody_snapshot()["unconfirmed"] == 1


def test_runtime_attempts_both_closes_preserves_first_and_retains_owner():
    runtime = LegacyExportRuntime.__new__(LegacyExportRuntime)
    cn, guard = Mock(), Mock()
    first = OSError("guard")
    guard.__exit__ = Mock(side_effect=first)
    cn.close.side_effect = OSError("connection")
    owner = WriterOwner("claim", cn, guard, "scan_data", runtime)
    with pytest.raises(OSError) as caught:
        runtime._close_writer(owner)
    assert caught.value is first and owner.closed
    cn.close.assert_called_once()
    assert next(iter(custody._holds.values())).retained_connection is owner
    with pytest.raises(custody.SqlCleanupUnknown):
        custody.require_sql_admission()


def test_uncertainty_write_failure_is_not_replaced_by_cleanup_failure():
    runtime = LegacyExportRuntime.__new__(LegacyExportRuntime)
    first = OSError("durable uncertainty")
    runtime.dal = Mock()
    runtime.dal.uncertain.side_effect = first
    cn, guard = Mock(), Mock()
    guard.__exit__ = Mock(side_effect=OSError("cleanup"))
    owner = WriterOwner("claim", cn, guard, "scan_data", runtime)
    with pytest.raises(OSError) as caught:
        runtime.uncertain_writer(owner)
    assert caught.value is first
    cn.close.assert_called_once()
