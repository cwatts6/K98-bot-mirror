from unittest.mock import Mock

import pytest

from core.export_startup_windows import TerminatedPair
from kvk.dal.new_source_import_dal import SourceConflict
import services.export_startup_reconciliation as module


def setup(monkeypatch, *, held=0, streams=0, sessions=(), reopened=0):
    first, second = Mock(), Mock()
    connections = [first, second]
    connect = Mock(side_effect=connections)
    singles = iter(
        [{"Held": held}, {"Held": streams}, {"Held": 0}, {"Held": 0}, {"OpenSessions": reopened}]
    )
    monkeypatch.setattr(module, "one", lambda _: next(singles))
    monkeypatch.setattr(module, "rows", lambda _: list(sessions))
    registration = dict(
        account="fixture-account",
        legacy_configuration={"config": dict(destinations=["legacy-file"])},
        pools=[dict(index_file_id="pool-index", slot_file_ids=["pool-slot"])],
    )
    reconciler = module.StartupReconciler(connect, registration, dict(hostname="fixture-host"))
    return reconciler, connect, connections


def test_clean_readiness_changes_no_jobs_or_resources(monkeypatch):
    reconciler, connect, connections = setup(monkeypatch)
    reconciler.prepare()
    assert connect.call_count == 2
    for connection in connections:
        connection.close.assert_called_once()
        for call in connection.cursor.return_value.execute.call_args_list:
            assert call.args[0].startswith("SELECT")
            assert call.args[0].count("?") == len(call.args) - 1


def test_restart_keeps_uncertain_preparation_quarantined(monkeypatch, caplog):
    reconciler, _, connections = setup(monkeypatch)
    observations = iter(
        [
            {"Held": 1},
            {"UnsafeHeld": 0},
            {"Held": 0},
            {"Held": 1},
            {"UnsafeHeld": 0},
            {"Held": 0},
            {"OpenSessions": 0},
        ]
    )
    monkeypatch.setattr(module, "one", lambda _: next(observations))
    native = Mock()
    monkeypatch.setattr(TerminatedPair, "verify", native)
    transitions = Mock()
    monkeypatch.setattr(module, "ExportExecutionDAL", transitions)
    reconciler.prepare(previous_hash="a" * 64, termination=TerminatedPair({}))
    assert native.call_count == 2
    transitions.assert_not_called()
    assert "resources_quarantined=1 replay_enabled=false" in caplog.text
    for connection in connections:
        for call in connection.cursor.return_value.execute.call_args_list:
            assert call.args[0].startswith("SELECT")
            assert call.args[0].count("?") == len(call.args) - 1


@pytest.mark.parametrize("unsafe", [None, {}, {"UnsafeHeld": 1}, {"UnsafeHeld": False}])
def test_restart_never_bypasses_unexplained_ownership(monkeypatch, unsafe):
    reconciler, _, _ = setup(monkeypatch)
    observations = iter([{"Held": 1}, unsafe])
    monkeypatch.setattr(module, "one", lambda _: next(observations))
    native = Mock()
    monkeypatch.setattr(TerminatedPair, "verify", native)
    with pytest.raises(SourceConflict, match="quarantined"):
        reconciler.prepare(previous_hash="a" * 64, termination=TerminatedPair({}))
    native.assert_not_called()


def test_quarantined_preparation_does_not_bypass_open_provider_stream(monkeypatch):
    reconciler, _, _ = setup(monkeypatch)
    observations = iter([{"Held": 1}, {"UnsafeHeld": 0}, {"Held": 1}])
    monkeypatch.setattr(module, "one", lambda _: next(observations))
    with pytest.raises(SourceConflict, match="stream closure"):
        reconciler.prepare(previous_hash="a" * 64, termination=TerminatedPair({}))


@pytest.mark.parametrize("held,streams", [(1, 0), (0, 1)])
def test_unresolved_work_prevents_any_session_transition(monkeypatch, held, streams):
    reconciler, connect, _ = setup(monkeypatch, held=held, streams=streams)
    transition = Mock()
    monkeypatch.setattr(module, "ExportExecutionDAL", transition)
    with pytest.raises(SourceConflict):
        reconciler.prepare()
    transition.assert_not_called()
    assert connect.call_count == 1


@pytest.mark.parametrize("previous", [None, "b" * 64])
def test_unknown_open_session_is_not_adopted(monkeypatch, previous):
    row = dict(SessionID="fixture-session", ManifestHash=bytes.fromhex("a" * 64), Version=1)
    reconciler, _, _ = setup(monkeypatch, sessions=[row])
    transition = Mock()
    monkeypatch.setattr(module, "ExportExecutionDAL", transition)
    with pytest.raises(SourceConflict):
        reconciler.prepare(previous_hash=previous)
    transition.assert_not_called()


def test_exact_previous_session_requires_native_termination_then_rechecks(monkeypatch):
    row = dict(SessionID="fixture-session", ManifestHash=bytes.fromhex("a" * 64), Version=1)
    reconciler, _, _ = setup(monkeypatch, sessions=[row])
    proof = TerminatedPair({})
    native = Mock()
    monkeypatch.setattr(TerminatedPair, "verify", native)
    dal = Mock()
    dal.transition.return_value = dict(State="closed", Version=2)
    monkeypatch.setattr(module, "ExportExecutionDAL", lambda _: dal)
    reconciler.prepare(previous_hash="a" * 64, termination=proof)
    native.assert_called_once()
    dal.transition.assert_called_once_with(
        "session", SessionID="fixture-session", Action="close", ExpectedVersion=1
    )


def test_failed_native_termination_never_closes_session(monkeypatch):
    row = dict(SessionID="fixture-session", ManifestHash=bytes.fromhex("a" * 64), Version=1)
    reconciler, _, _ = setup(monkeypatch, sessions=[row])
    proof = TerminatedPair({})
    monkeypatch.setattr(TerminatedPair, "verify", Mock(side_effect=ValueError("not proven")))
    transition = Mock()
    monkeypatch.setattr(module, "ExportExecutionDAL", transition)
    with pytest.raises(ValueError):
        reconciler.prepare(previous_hash="a" * 64, termination=proof)
    transition.assert_not_called()


def test_changed_admission_after_old_session_close_stays_stopped(monkeypatch):
    reconciler, _, _ = setup(monkeypatch, reopened=1)
    with pytest.raises(SourceConflict, match="admission changed"):
        reconciler.prepare()


@pytest.mark.parametrize("value", [None, {}, {"Held": False}, {"Held": "0"}])
def test_missing_or_malformed_readiness_is_not_permission_to_start(monkeypatch, value):
    reconciler, connect, _ = setup(monkeypatch)
    monkeypatch.setattr(module, "one", lambda _: value)
    transition = Mock()
    monkeypatch.setattr(module, "ExportExecutionDAL", transition)
    with pytest.raises(SourceConflict):
        reconciler.prepare()
    transition.assert_not_called()
    assert connect.call_count == 1


@pytest.mark.parametrize("version", [None, "1", False, 0])
def test_bad_session_version_never_closes_a_session(monkeypatch, version):
    row = dict(SessionID="fixture-session", ManifestHash=bytes.fromhex("a" * 64), Version=version)
    reconciler, _, _ = setup(monkeypatch, sessions=[row])
    native = Mock()
    monkeypatch.setattr(TerminatedPair, "verify", native)
    transition = Mock()
    monkeypatch.setattr(module, "ExportExecutionDAL", transition)
    with pytest.raises(SourceConflict):
        reconciler.prepare(previous_hash="a" * 64, termination=TerminatedPair({}))
    native.assert_not_called()
    transition.assert_not_called()
