"""Exercise the issuer main loop at the drained-deployment exit boundary."""

import builtins
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import core.export_automatic_pair as automatic
import core.export_deployment_handoff as handoff
import core.export_execution_host as host
import core.export_process_identity as identity
import core.export_process_pair as pair
import core.export_startup_windows as native
import scripts.provision_export_process_pair as provision
import scripts.run_export_startup_issuer as issuer
import services.export_execution_dal as execution
import services.export_runtime_composition as composition
import services.export_startup_reconciliation as reconciliation


class SupervisorHeld(BaseException):
    pass


@pytest.fixture
def run_issuer(tmp_path, monkeypatch):
    events = []
    policy = {
        "version": 1,
        "source_hashes": {},
        "seed_plan": {},
        "state_directory": str(tmp_path),
        "flags": {
            "EXPORT_COORDINATION_ENABLED": True,
            "KVK_SOURCE_INTAKE_ENABLED": False,
            "KVK_SOURCE_RECOVERY_ENABLED": False,
        },
    }
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(policy))
    publication = {
        "version": 1,
        "plan_sha256": "a" * 64,
        "manifests": {"authority": "b" * 64, "bot": "c" * 64},
    }
    authority = {
        "deployment_boundary": {"host": {"machine_guid": "machine"}},
        "sql_contract": {},
        "runtime_registration": {},
        "python": "python",
    }
    plan = {
        "application_sid": "sid",
        "token_profiles": {},
        "commit_file": str(tmp_path / "old" / "commit.json"),
    }
    inspect = lambda p, **kw: Path(p)
    launcher = {
        "protected_path": inspect,
        "bootstrap": Mock(),
        "connection_factory": Mock(return_value=Mock()),
    }
    monkeypatch.setattr(issuer.runpy, "run_path", Mock(return_value=launcher))
    monkeypatch.setattr(
        issuer, "load_seed", Mock(return_value=(plan, {"authority": authority}, {}))
    )
    monkeypatch.setattr(issuer, "release_history", Mock(return_value=(None, str(tmp_path))))
    monkeypatch.setattr(handoff, "previous_termination", Mock(return_value=None))
    monkeypatch.setattr(host, "machine_identity", Mock(return_value={"machine_guid": "machine"}))
    token, mutex = Mock(), Mock()
    monkeypatch.setattr(native, "linked_application_token", Mock(return_value=(token, {})))
    monkeypatch.setattr(native, "startup_mutex", Mock(return_value=mutex))
    monkeypatch.setattr(automatic, "verify_automatic_token", Mock())
    monkeypatch.setattr(
        automatic,
        "incarnation_files",
        Mock(return_value=({"ManualProcessPairPlan-CANDIDATE.json": b"{}"}, {}, {})),
    )
    monkeypatch.setattr(native, "create_private_directory", lambda p, sid: p.mkdir())
    writes = []
    damage = {"phase": None}

    def write(path, raw, sid):
        path = Path(path)
        writes.append(path.name)
        if damage["phase"] == "diagnostic" and "failure" in path.name:
            raise OSError("private detail must not leak")
        path.write_bytes(raw)

    monkeypatch.setattr(native, "write_new_protected", write)
    monkeypatch.setattr(identity, "process_snapshot", Mock(return_value={}))
    monkeypatch.setattr(host, "create_private_pipe", Mock(side_effect=lambda *a, **kw: Mock()))
    create = Mock(side_effect=lambda *a: SimpleNamespace(process=Mock()))
    monkeypatch.setattr(native, "create_role", create)
    handles = []

    def acknowledge(*args):
        handle = Mock()
        handles.append(handle)
        return {"pid": len(handles)}, handle

    monkeypatch.setattr(issuer, "acknowledge_role", acknowledge)
    monkeypatch.setattr(pair, "bind_templates", Mock())
    monkeypatch.setattr(pair, "publication", Mock(return_value=publication))

    def publish(new_plan, raw, templates, bindings, held, inspect, **kw):
        directory = next(tmp_path.glob("*/AutomaticIssuer.json")).parent
        (directory / "commit.json").write_text("{}")
        return publication

    monkeypatch.setattr(provision, "publish_pair", publish)
    monkeypatch.setattr(native, "signalled", Mock(return_value=True))
    monkeypatch.setattr(native.TerminatedPair, "verify", lambda self: events.append("terminated"))
    monkeypatch.setattr(
        handoff, "record_termination", lambda *a: events.append("termination_recorded")
    )
    request = {
        "request": {"release_id": "11111111-1111-1111-1111-111111111111"},
        "request_sha256": "d" * 64,
    }
    monkeypatch.setattr(handoff, "requested_release", Mock(return_value=request))

    def prepare(**kw):
        if kw.get("termination") is not None:
            events.append("sql_closed")
            if damage["phase"] == "sql":
                raise ValueError("closure unconfirmed")

    monkeypatch.setattr(
        reconciliation, "StartupReconciler", Mock(return_value=SimpleNamespace(prepare=prepare))
    )
    monkeypatch.setattr(execution, "ExportExecutionDAL", Mock())
    monkeypatch.setattr(execution, "installation_migrations", Mock())
    monkeypatch.setattr(composition, "verify_installation_contract", Mock())

    def release(role):
        events.append("empty_job_released")
        if damage["phase"] == "job":
            raise ValueError("child still alive")

    monkeypatch.setattr(native, "release_created_role", release)
    stop = Mock()
    monkeypatch.setattr(native, "stop_unadmitted_role", stop)
    real_acknowledge = handoff.acknowledge_deployment

    def drain(*args, **kw):
        events.append("drain")
        if damage["phase"] in {"receipt", "diagnostic"}:
            raise OSError("private path, token or driver details")
        result = real_acknowledge(*args, **kw)
        if damage["phase"] == "readback":
            raise PermissionError("receipt persisted but final inspection failed")
        return result

    monkeypatch.setattr(handoff, "acknowledge_deployment", drain)
    console = []

    def output(value, **kw):
        value = json.loads(value)
        console.append(value["stage"])
        if value["stage"] == "DEPLOYMENT_HANDOFF_READY":
            raise BrokenPipeError("console unavailable after drain")

    monkeypatch.setattr(builtins, "print", output)
    monkeypatch.setattr(
        issuer.time, "sleep", Mock(side_effect=SupervisorHeld("supervisor hold reached"))
    )
    monkeypatch.setitem(sys.modules, "win32api", SimpleNamespace(GetCurrentProcess=Mock()))
    monkeypatch.setitem(sys.modules, "win32event", SimpleNamespace(ReleaseMutex=Mock()))
    monkeypatch.setitem(
        sys.modules, "win32process", SimpleNamespace(GetExitCodeProcess=lambda p: 15)
    )
    return SimpleNamespace(
        run=lambda: issuer.main(["--policy", str(policy_path)]),
        damage=damage,
        events=events,
        console=console,
        creates=create,
        stops=stop,
        handles=handles,
        directory=tmp_path,
        token=token,
        mutex=mutex,
        writes=writes,
    )


def test_drained_deployment_exits_without_console_dependency(run_issuer):
    result = run_issuer.run()
    assert result == 0
    assert "DEPLOYMENT_HANDOFF_READY" not in run_issuer.console
    assert run_issuer.events[:5] == [
        "terminated",
        "termination_recorded",
        "sql_closed",
        "empty_job_released",
        "empty_job_released",
    ]
    assert len(list(run_issuer.directory.glob("deployment-drained-*.json"))) == 1
    assert run_issuer.creates.call_count == 2
    run_issuer.stops.assert_not_called()
    for handle in run_issuer.handles:
        handle.Close.assert_called_once()
    run_issuer.token.Close.assert_called_once()
    run_issuer.mutex.Close.assert_called_once()


@pytest.mark.parametrize("phase", ["receipt", "readback", "diagnostic"])
def test_post_drain_error_exits_without_replay_or_supervisor_hold(run_issuer, phase):
    run_issuer.damage["phase"] = phase
    assert run_issuer.run() == 12
    assert run_issuer.creates.call_count == 2
    run_issuer.stops.assert_not_called()
    receipts = list(run_issuer.directory.glob("deployment-drained-*.json"))
    assert len(receipts) == (1 if phase == "readback" else 0)
    diagnostics = list(run_issuer.directory.glob("deployment-handoff-failure-*.json"))
    assert len(diagnostics) == (0 if phase == "diagnostic" else 1)
    if diagnostics:
        value = json.loads(diagnostics[0].read_text())
        assert value["error_type"] in {"OSError", "PermissionError"}
        assert "private" not in diagnostics[0].read_text()
        assert value["stage"] == "deployment_handoff_failed"
    for handle in run_issuer.handles:
        handle.Close.assert_called_once()
    run_issuer.token.Close.assert_called_once()


@pytest.mark.parametrize("phase", ["sql", "job"])
def test_unfinished_drain_still_retains_published_supervisor(run_issuer, phase):
    run_issuer.damage["phase"] = phase
    with pytest.raises(SupervisorHeld):
        run_issuer.run()
    assert "STOP_RECONCILIATION_REQUIRED" in run_issuer.console
    assert not list(run_issuer.directory.glob("deployment-drained-*.json"))
    assert not list(run_issuer.directory.glob("deployment-handoff-failure-*.json"))
    assert run_issuer.creates.call_count == 2
    run_issuer.stops.assert_not_called()
