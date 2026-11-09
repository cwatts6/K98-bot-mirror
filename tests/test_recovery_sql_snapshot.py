"""Passive observations cannot commit, retain locks, or conceal cleanup failure."""

from unittest.mock import Mock

import pytest

from core.recovery_sql_snapshot import RecoveryObservationCleanupUnknown, recovery_snapshot
from core.sql_observation import ObservationBusy, observing
from services.stats_import_outcome_dal import ImportExecutionActive, StatsImportOutcomeDAL


def connection():
    return Mock(autocommit=False, timeout=15)


def test_owned_read_rolls_back_restores_and_closes_without_commit():
    cn = connection()
    with recovery_snapshot(lambda: cn) as cursor:
        assert observing()
        assert cn.timeout == 3
        assert cursor is cn.cursor.return_value
    assert not observing()
    assert cn.rollback.call_count == 2
    cn.close.assert_called_once()
    cn.commit.assert_not_called()
    assert [x.args for x in cn.set_attr.call_args_list] == [(1227, 0x20), (1227, 0x02)]


@pytest.mark.parametrize("phase", ["rollback", "cursor_close", "isolation_restore", "close"])
def test_first_failure_survives_failed_cleanup_and_every_cleanup_is_attempted(phase):
    cn = connection()
    first = ImportExecutionActive("busy")
    cleanup = OSError("private cleanup detail")
    if phase == "cursor_close":
        cn.cursor.return_value.close.side_effect = cleanup
    elif phase == "isolation_restore":
        cn.set_attr.side_effect = [None, cleanup]
    else:
        getattr(cn, phase).side_effect = cleanup
        if phase == "rollback":
            cn.rollback.side_effect = [None, cleanup]
    with pytest.raises(RecoveryObservationCleanupUnknown) as caught:
        with recovery_snapshot(lambda: cn):
            raise first
    assert caught.value.__cause__ is first
    assert "private cleanup detail" not in str(caught.value)
    assert cn.rollback.call_count == 2
    cn.cursor.return_value.close.assert_called_once()
    cn.close.assert_called_once()
    cn.commit.assert_not_called()


@pytest.mark.parametrize("error", [KeyboardInterrupt(), OSError("lost reply"), ValueError("scope")])
def test_cancellation_and_first_failure_are_preserved_after_cleanup(error):
    cn = connection()
    with pytest.raises(type(error)) as caught:
        with recovery_snapshot(lambda: cn):
            raise error
    assert caught.value is error
    assert cn.rollback.call_count == 2
    cn.close.assert_called_once()


def test_only_acknowledged_contention_becomes_busy():
    cn = connection()
    with pytest.raises(ObservationBusy):
        with recovery_snapshot(lambda: cn):
            raise Exception("42000", "lock timeout (1222)")
    cn.close.assert_called_once()


def test_snapshot_unavailable_never_falls_back_or_retries():
    cn = connection()
    failure = Exception("42000", "snapshot isolation unavailable (3952)")
    connect = Mock(return_value=cn)
    with pytest.raises(Exception) as caught:
        with recovery_snapshot(connect):
            raise failure
    assert caught.value is failure
    connect.assert_called_once()
    cn.commit.assert_not_called()


def test_activity_probes_use_exact_mutex_identity_without_acquisition(monkeypatch):
    from services import stats_import_outcome_dal as module
    from services.export_coordination_dal import coordination_lock_name

    cursor = Mock()
    monkeypatch.setattr(module, "one", lambda _: {"Available": 1})
    StatsImportOutcomeDAL._observe_available(cursor, "account")
    calls = cursor.execute.call_args_list
    assert calls[1].args[1] == coordination_lock_name("account:account")
    assert all("APPLOCK_TEST" in x.args[0] and "sp_getapplock" not in x.args[0] for x in calls)


@pytest.mark.parametrize("available", [0, None, -999])
def test_unknown_activity_probe_fails_closed(monkeypatch, available):
    from services import stats_import_outcome_dal as module

    monkeypatch.setattr(module, "one", lambda _: {"Available": available})
    with pytest.raises(ImportExecutionActive):
        StatsImportOutcomeDAL._observe_available(Mock(), "account")
