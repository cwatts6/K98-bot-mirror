"""Shared-account contracts with inert process, SQL and provider boundaries."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from core.export_execution_host import DeploymentBoundary, HostBoundaryError
from core.export_process_identity import (
    TRUST_MODEL,
    open_pinned_process,
    validate_process_bindings,
    verify_process_snapshot,
)
from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_execution_authority import ExecutionUncertain
from services.export_execution_protocol import encode
from services.export_runtime_composition import AuthorityClient, verify_installation_contract
from tests.test_export_execution_host import deployment_fixture
from tests.test_export_runtime_composition import installation_fixture

SID = "S-1-5-21-111-222-333-444"


def process_bindings():
    def descriptor(pid):
        return dict(
            pid=pid,
            created_filetime=133000000000000000 + pid,
            executable="C:/K98/python.exe",
            sha256="a" * 64,
            token_profile=dict(
                user_sid=SID,
                group_sids=["S-1-5-32-545"],
                privileges=["SeChangeNotifyPrivilege"],
                elevation_type=1,
                elevated=False,
                ui_access=False,
            ),
        )

    return dict(authority=descriptor(100), bot=descriptor(200))


def shared_deployment(tmp_path):
    m, records, reads = deployment_fixture(tmp_path)
    m.update(trust_model=TRUST_MODEL, bot_sid=SID, process_bindings=process_bindings())
    boundary = m["deployment_boundary"]
    boundary.update(
        version=2,
        trust_model=TRUST_MODEL,
        bot_sid=SID,
        process_bindings=deepcopy(m["process_bindings"]),
    )
    records["bot_identity"]["observations"][0]["user_sid"] = SID
    for kind, record in records.items():
        record.update(version=2, trust_model=TRUST_MODEL)
        reference = boundary["review"]["records"][kind]
        Path(reference["path"]).write_bytes(encode(record))
        reference["sha256"] = hashlib.sha256(encode(record)).hexdigest()
    return m, records, reads


def test_shared_deployment_rechecks_all_seven_versioned_records(tmp_path):
    m, records, reads = shared_deployment(tmp_path)
    boundary = DeploymentBoundary(m, **reads)
    assert boundary.recheck() == digest(m["deployment_boundary"]).hex()
    assert len(records) == 7
    # Original evidence is not relabelled by the reader.
    path = Path(m["deployment_boundary"]["review"]["records"]["key_inventory"]["path"])
    original = path.read_bytes()
    boundary.recheck()
    assert path.read_bytes() == original


@pytest.mark.parametrize("kind", sorted(DeploymentBoundary.RECORDS))
def test_old_observation_cannot_be_relabelled_as_shared_custody(tmp_path, kind):
    m, records, reads = shared_deployment(tmp_path)
    records[kind]["version"] = 1
    ref = m["deployment_boundary"]["review"]["records"][kind]
    raw = encode(records[kind])
    Path(ref["path"]).write_bytes(raw)
    ref["sha256"] = hashlib.sha256(raw).hexdigest()
    with pytest.raises(HostBoundaryError, match="observations"):
        DeploymentBoundary(m, **reads)


@pytest.mark.parametrize(
    "field,value",
    [
        ("pid", 101),
        ("created_filetime", 133000000000000001),
        ("executable", "C:/Other/python.exe"),
        ("sha256", "b" * 64),
    ],
)
def test_recycled_pid_other_executable_or_hash_is_not_the_approved_process(field, value):
    expected = process_bindings()["authority"]
    with pytest.raises(ValueError, match="incarnation"):
        verify_process_snapshot(expected | {field: value}, expected)


def test_token_drift_is_not_accepted_even_with_same_pid_and_sid():
    expected = process_bindings()["authority"]
    observed = deepcopy(expected)
    observed["token_profile"]["privileges"].append("SeDebugPrivilege")
    with pytest.raises(ValueError):
        verify_process_snapshot(observed, expected)


def test_privileged_shared_account_is_explicitly_pinned_not_called_restricted():
    bindings = process_bindings()
    for item in bindings.values():
        item["token_profile"].update(group_sids=["S-1-5-32-544"], elevated=True, elevation_type=2)
    validate_process_bindings(bindings, SID)
    observed = deepcopy(bindings["bot"])
    observed["token_profile"]["elevated"] = False
    with pytest.raises(ValueError):
        verify_process_snapshot(observed, bindings["bot"])


@pytest.mark.parametrize("failed", [False, True])
def test_pinned_process_handle_retained_or_closed_on_failed_observation(monkeypatch, failed):
    import sys

    import core.export_process_identity as identity

    handle = SimpleNamespace(Close=Mock())
    opener = Mock(return_value=handle)
    monkeypatch.setitem(sys.modules, "win32api", SimpleNamespace(OpenProcess=opener))
    expected = process_bindings()["authority"]
    snapshot = Mock(return_value=deepcopy(expected))
    if failed:
        snapshot.side_effect = ValueError("exited")
    monkeypatch.setattr(identity, "process_snapshot", snapshot)
    if failed:
        with pytest.raises(ValueError):
            open_pinned_process(expected["pid"], expected)
        handle.Close.assert_called_once()
    else:
        assert open_pinned_process(expected["pid"], expected) is handle
        handle.Close.assert_not_called()
    snapshot.assert_called_once_with(handle)
    with pytest.raises(ValueError, match="PID"):
        open_pinned_process(expected["pid"] + 1, expected)
    assert opener.call_count == 1


def application_installation():
    observed, approved = installation_fixture(profile="application")
    approved["version"] = 3
    observed["target"].update(AuthorityRole=1, ReaderRole=0)
    return observed, approved


def test_application_permission_union_preserves_denied_capabilities():
    from services.export_execution_dal import installation_permissions

    authority = installation_permissions("authority")
    reader = installation_permissions("reader")
    expected = {key: int(bool(authority[key] or reader[key])) for key in authority}
    assert installation_permissions("application") == expected
    observed, approved = application_installation()
    assert verify_installation_contract(observed, approved) == digest(observed).hex()
    # Reader membership would deny authority EXECUTEs in the actual SQL roles.
    observed["target"]["ReaderRole"] = 1
    with pytest.raises(SourceConflict, match="target"):
        verify_installation_contract(observed, approved)


@pytest.mark.parametrize("damage", ["extra_grant", "sysadmin", "old_version"])
def test_application_profile_rejects_broad_permissions_and_old_contract(damage):
    observed, approved = application_installation()
    if damage == "extra_grant":
        next(p for p in observed["permissions"] if p["Allowed"] == 0)["Allowed"] = 1
    elif damage == "sysadmin":
        observed["target"]["Sysadmin"] = 1
    else:
        approved["version"] = 2
    with pytest.raises(SourceConflict):
        verify_installation_contract(observed, approved)


def test_source_inventory_digest_tracks_pinned_git_bytes_and_rejects_old_pin():
    from services.export_execution_dal import APPLICATION_SCHEMA_SOURCE_HASH

    manifest = json.loads(
        (Path(__file__).parents[1] / "deploy/export_application_schema_source.json").read_bytes()
    )
    assert len(manifest) == len({item["name"] for item in manifest}) == 540
    assert digest(manifest).hex() == APPLICATION_SCHEMA_SOURCE_HASH
    original = deepcopy(manifest)
    next(item for item in original if item["name"] == "dbo.usp_ExportExecutionSessionTransition")[
        "sha256"
    ] = "2ee7d56a1a53ae8f9db560b1d16058dcef9375b14061daa7af288fb52b52849f"
    assert digest(original).hex() != APPLICATION_SCHEMA_SOURCE_HASH
    from services.export_runtime_composition import validate_application_installation_contract

    approved = dict(
        version=1,
        server="fixture",
        database="ROK_TRACKER",
        principal="fixture",
        sources=manifest,
        dynamic_objects=[],
        metadata_hash="a" * 64,
        permissions_hash="b" * 64,
        review_id=str(uuid4()),
    )
    validate_application_installation_contract(approved)
    with pytest.raises(SourceConflict):
        validate_application_installation_contract(approved | {"sources": original})


def test_source_inventory_preserves_sql_names_with_sanitized_export_filenames():
    from services.export_runtime_composition import validate_application_installation_contract

    manifest = json.loads(
        (Path(__file__).parents[1] / "deploy/export_application_schema_source.json").read_bytes()
    )
    by_path = {item["path"]: item for item in manifest}
    # Authoritative CREATE TABLE declarations differ from these filesystem-safe names.
    declared_names = {
        "sql_schema/dbo.ID_.Table.sql": "dbo.ID#",
        "sql_schema/dbo.LATEST_T4_T5_KILLS.Table.sql": "dbo.LATEST_T4&T5_KILLS",
    }
    for path, name in declared_names.items():
        assert by_path[path]["name"] == name
        assert by_path[path]["type"] == "U"

    approved = dict(
        version=1,
        server="fixture",
        database="ROK_TRACKER",
        principal="fixture",
        sources=manifest,
        dynamic_objects=[],
        metadata_hash="a" * 64,
        permissions_hash="b" * 64,
        review_id=str(uuid4()),
    )
    validate_application_installation_contract(approved)
    stale = deepcopy(manifest)
    for item in stale:
        if item["path"] in declared_names:
            item["name"] = Path(item["path"]).name.removesuffix(".Table.sql")
    with pytest.raises(SourceConflict):
        validate_application_installation_contract(approved | {"sources": stale})


@pytest.mark.parametrize("enrollment", [False, True])
@pytest.mark.parametrize("venv_launcher", [False, True])
def test_shared_launcher_requires_new_version_and_application_sql_profile(
    monkeypatch, enrollment, venv_launcher
):
    import scripts.run_export_authority as launcher
    from tests.test_export_runtime_composition import registration_fixture

    root = Path(__file__).parents[1]
    names = {
        "scripts/run_export_authority.py",
        "scripts/run_export_provider_child.py",
        "core/export_execution_host.py",
        "services/export_execution_authority.py",
        "services/export_execution_dal.py",
        "services/export_execution_protocol.py",
        "services/export_request_budget.py",
        "services/export_coordination_dal.py",
    }
    monkeypatch.setattr(launcher, "code_files", lambda _: names)
    _, sql = application_installation()
    sql["database"] = "ROK_TRACKER"
    manifest = dict(
        version=2 if enrollment else 3,
        trust_model=TRUST_MODEL,
        authority_sid=SID,
        bot_sid=SID,
        pipe_id=str(uuid4()),
        python="C:/K98/venv/Scripts/python.exe" if venv_launcher else "C:/K98/python.exe",
        child_script=str(root / "scripts/run_export_provider_child.py"),
        credentials_file="C:/K98/key.json",
        evidence_root="C:/K98/evidence",
        storage_owner="fixture",
        sql_server=sql["server"],
        sql_database=sql["database"],
        sql_contract=sql,
        service_account_email="editor@example.iam.gserviceaccount.com",
        project_id="project",
        source_hashes={
            name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names
        },
    )
    if enrollment:
        manifest["enrollment_profile"] = dict(
            version=1,
            owner_email="owner@example.com",
            client_id="123-app.apps.googleusercontent.com",
            scopes=["https://www.googleapis.com/auth/drive.file"],
        )
    else:
        manifest.update(
            process_bindings=process_bindings(),
            deployment_boundary={},
            runtime_registration=registration_fixture(),
        )
    kwargs = dict(
        script=root / "scripts/run_export_authority.py",
        current_sid=SID,
        inspect_path=Mock(),
        enrollment=enrollment,
    )
    assert launcher.manifest_contract(manifest, **kwargs) is manifest
    with pytest.raises(launcher.AuthorityStartupError, match="manifest"):
        launcher.manifest_contract(manifest | {"version": manifest["version"] - 1}, **kwargs)
    _, old_sql = installation_fixture()
    with pytest.raises(launcher.AuthorityStartupError, match="SQL"):
        launcher.manifest_contract(manifest | {"sql_contract": old_sql}, **kwargs)


@pytest.mark.parametrize("failure", [None, "peer", "recycled_after_read", "dispatch", "reply"])
def test_shared_server_binds_both_processes_and_never_replays(monkeypatch, failure):
    import core.export_execution_host as host
    import core.export_process_identity as identity
    import scripts.run_export_authority as launcher

    lifetime, own, peer, handle = (SimpleNamespace(Close=Mock()) for _ in range(4))
    pipe = SimpleNamespace(connect=Mock(), receive=Mock(return_value={"version": 1}), send=Mock())
    snapshot = process_bindings()["bot"]
    if failure == "recycled_after_read":
        snapshot = snapshot | {"created_filetime": 1}
    monkeypatch.setattr(identity, "process_snapshot", lambda _: snapshot)
    authenticate = Mock(return_value=peer)
    if failure == "peer":
        authenticate.side_effect = ValueError("wrong incarnation")
    monkeypatch.setattr(identity, "authenticate_process_peer", authenticate)
    opener = Mock(side_effect=[lifetime, own, own])
    monkeypatch.setattr(identity, "open_pinned_process", opener)
    monkeypatch.setattr(identity, "pinned_process_alive", Mock(return_value=True))
    pipe_factory = Mock(return_value=pipe)
    monkeypatch.setattr(host, "MessagePipe", pipe_factory)
    broker = SimpleNamespace(dispatch=Mock(return_value="ok"))
    if failure == "dispatch":
        broker.dispatch.side_effect = ValueError("unresolved")
    if failure == "reply":
        pipe.send.side_effect = EOFError("lost reply")
    with pytest.raises(KeyboardInterrupt):
        launcher.serve(
            manifest=dict(
                pipe_id=str(uuid4()),
                authority_sid=SID,
                bot_sid=SID,
                trust_model=TRUST_MODEL,
                process_bindings=process_bindings(),
            ),
            authority=Mock(),
            make_pipe=Mock(side_effect=[handle, KeyboardInterrupt()]),
            authenticate=Mock(side_effect=AssertionError("legacy token path")),
            broker=broker,
        )
    assert broker.dispatch.call_count == (0 if failure in {"peer", "recycled_after_read"} else 1)
    assert peer.Close.call_count == (0 if failure == "peer" else 1)
    assert pipe.receive.call_count == (0 if failure == "peer" else 1)
    handle.Close.assert_called_once()
    assert own.Close.call_count == 2
    assert opener.call_count == 3
    lifetime.Close.assert_called_once()
    pipe_factory.assert_called_once_with(handle, timeout_ms=30000, process=lifetime)


@pytest.mark.parametrize("failure", [None, ValueError("unavailable observation")])
def test_shared_server_exited_bot_returns_to_drain_without_opening_pipe(monkeypatch, failure):
    import core.export_process_identity as identity
    import scripts.run_export_authority as launcher

    lifetime = SimpleNamespace(Close=Mock())
    monkeypatch.setattr(identity, "open_pinned_process", Mock(return_value=lifetime))
    monkeypatch.setattr(
        identity, "pinned_process_alive", Mock(return_value=False, side_effect=failure)
    )
    make_pipe, broker = Mock(), SimpleNamespace(dispatch=Mock())
    kwargs = dict(
        manifest=dict(
            pipe_id=str(uuid4()),
            authority_sid=SID,
            bot_sid=SID,
            trust_model=TRUST_MODEL,
            process_bindings=process_bindings(),
        ),
        authority=Mock(),
        make_pipe=make_pipe,
        authenticate=Mock(),
        broker=broker,
    )
    if failure:
        with pytest.raises(ValueError, match="unavailable"):
            launcher.serve(**kwargs)
    else:
        assert launcher.serve(**kwargs) is None
    make_pipe.assert_not_called()
    broker.dispatch.assert_not_called()
    lifetime.Close.assert_called_once()


@pytest.mark.parametrize(
    "waits,snapshot_failure,expected",
    [([0], False, False), ([258], False, True), ([258, 0], True, False)],
)
def test_pinned_liveness_handles_exit_and_snapshot_race(
    monkeypatch, waits, snapshot_failure, expected
):
    import core.export_process_identity as identity

    descriptor = process_bindings()["bot"]
    wait = Mock(side_effect=waits)
    snapshot = Mock(return_value=descriptor)
    if snapshot_failure:
        snapshot.side_effect = ValueError("process exited during snapshot")
    monkeypatch.setitem(sys.modules, "win32event", SimpleNamespace(WaitForSingleObject=wait))
    monkeypatch.setattr(identity, "process_snapshot", snapshot)
    handle = object()
    assert identity.pinned_process_alive(handle, descriptor) is expected
    assert snapshot.call_count == int(waits[0] == 258)
    assert all(call.args == (handle, 0) for call in wait.call_args_list)


@pytest.mark.parametrize("waits", [[-1], [258, 258]])
def test_pinned_liveness_never_treats_uncertain_or_wrong_live_identity_as_exit(monkeypatch, waits):
    import core.export_process_identity as identity

    descriptor = process_bindings()["bot"]
    monkeypatch.setitem(
        sys.modules, "win32event", SimpleNamespace(WaitForSingleObject=Mock(side_effect=waits))
    )
    monkeypatch.setattr(
        identity, "process_snapshot", Mock(return_value=descriptor | {"created_filetime": 1})
    )
    with pytest.raises(ValueError):
        identity.pinned_process_alive(object(), descriptor)


def test_shared_client_requires_explicit_model_and_both_incarnations():
    args = dict(pipe_id=str(uuid4()), authority_sid=SID, bot_sid=SID, deployment_hash="b" * 64)
    with pytest.raises(ValueError):
        AuthorityClient(**args)
    with pytest.raises(ValueError):
        AuthorityClient(**args, trust_model=TRUST_MODEL)
    bindings = process_bindings()
    client = AuthorityClient(**args, trust_model=TRUST_MODEL, process_bindings=bindings)
    bindings["authority"]["pid"] = 300
    assert client.process_bindings["authority"]["pid"] == 100


@pytest.mark.parametrize(
    "damage", [None, "old_version", "principal", "supervisor_sql", "manual_pair"]
)
def test_actual_bot_factory_binds_shared_profile_and_same_sql_contract(
    monkeypatch, tmp_path, damage
):
    import constants
    import core.export_execution_host as host
    import kvk.dal.new_source_admin_dal as admin
    import scripts.run_export_authority as launcher
    import services.export_execution_dal as dal
    import services.export_runtime_composition as runtime
    import services.export_snapshot_store as store
    from tests.test_export_runtime_composition import registration_fixture

    observed, sql = application_installation()
    target = {key: sql[key] for key in ("server", "database", "principal")}
    export = tmp_path / "export.json"
    export.write_text("[]")
    config = dict(
        version=2,
        trust_model=TRUST_MODEL,
        authority=dict(
            host="fixture",
            authority_sid=SID,
            bot_sid=SID,
            pipe_id=str(uuid4()),
            deployment_hash="c" * 64,
            process_bindings=process_bindings(),
        ),
        registration=registration_fixture(),
        sql_contract=sql,
        legacy_sql_contract=dict(target, version=1, source={}),
        application_sql_contract=dict(target, version=1),
        spool_root=str(tmp_path / "spool"),
        source_hashes={},
        export_config_file=str(export),
        export_config_sha256=hashlib.sha256(export.read_bytes()).hexdigest(),
    )
    if damage == "manual_pair":
        from core.export_process_pair import bind_templates
        from tests.test_export_process_pair import pair_fixture

        plan, templates, bindings = pair_fixture(tmp_path, monkeypatch)
        plan["source_hashes"] = {}
        templates["authority"].update(
            source_hashes={},
            runtime_registration=config["registration"],
            sql_contract=config["sql_contract"],
            pipe_id=config["authority"]["pipe_id"],
        )
        templates["bot"] = deepcopy(config)
        templates["bot"]["authority"].update(process_bindings=None, deployment_hash=None)
        config = bind_templates(plan, templates, bindings)["bot"]
    if damage == "old_version":
        config["version"] = 1
    elif damage == "principal":
        config["application_sql_contract"]["principal"] = "other"
    path = tmp_path / "runtime.json"
    path.write_bytes(encode(config))
    monkeypatch.setenv("K98_EXPORT_RUNTIME_MANIFEST", str(path))
    monkeypatch.setattr(host, "assert_protected_path", lambda p, **_: Path(p))
    monkeypatch.setattr(host, "machine_identity", lambda: "fixture")
    monkeypatch.setattr(host, "current_sid", lambda: SID)
    monkeypatch.setattr(launcher, "code_files", lambda _: set())
    monkeypatch.setattr(constants, "CONFIG_FILE", str(export))
    for name in (
        "validate_capture_configuration",
        "validate_legacy_installation_contract",
        "validate_application_installation_contract",
        "verify_legacy_installation_contract",
        "verify_application_installation_contract",
    ):
        monkeypatch.setattr(runtime, name, Mock())
    monkeypatch.setattr(dal, "legacy_installation_snapshot", Mock())
    monkeypatch.setattr(dal, "application_installation_snapshot", Mock())
    connection = Mock()
    connector = Mock(return_value=connection)
    monkeypatch.setattr(admin, "configured_connection", connector)
    monkeypatch.setattr(
        dal,
        "ExportExecutionDAL",
        lambda _: SimpleNamespace(installation_snapshot=lambda: observed),
    )
    reply = dict(
        deployment_hash=config["authority"]["deployment_hash"],
        registration_hash=runtime.RuntimeRegistration(config["registration"]).fingerprint,
        sql_contract_hash=digest(sql).hex(),
    )
    if damage == "supervisor_sql":
        reply["sql_contract_hash"] = "d" * 64
    client_factory = Mock(return_value=SimpleNamespace(_invoke=Mock(return_value=reply)))
    monkeypatch.setattr(runtime, "AuthorityClient", client_factory)
    bundle_factory = Mock()
    monkeypatch.setattr(runtime, "ExportRuntime", bundle_factory)
    monkeypatch.setattr(store, "ExportSnapshotStore", Mock())
    if damage and damage != "manual_pair":
        with pytest.raises(SourceConflict):
            runtime._prepare_configured_runtime()
        bundle_factory.assert_not_called()
        if damage != "supervisor_sql":
            connector.assert_not_called()
    else:
        assert runtime._prepare_configured_runtime() is bundle_factory.return_value
        assert (
            client_factory.call_args.kwargs["process_bindings"]
            == config["authority"]["process_bindings"]
        )
        assert client_factory.call_args.kwargs["trust_model"] == TRUST_MODEL
        assert (
            runtime.verify_legacy_installation_contract.call_args.kwargs["profile"] == "application"
        )
        connection.close.assert_called_once()


@pytest.mark.parametrize("failure", ["authenticate", "reply", "exited", None])
def test_shared_client_never_replays_connected_requests_and_retains_peer_handle(
    monkeypatch, failure
):
    import core.export_execution_host as host
    import core.export_process_identity as identity

    pipe_handle, process = SimpleNamespace(Close=Mock()), SimpleNamespace(Close=Mock())
    pipe = SimpleNamespace(send=Mock(), receive=Mock(return_value={"version": 1, "result": "ok"}))
    factory = Mock(return_value=pipe_handle)
    verifier = Mock(return_value=process)
    snapshots = Mock(return_value=process_bindings()["authority"])
    if failure == "authenticate":
        verifier.side_effect = ValueError("wrong peer")
    elif failure == "reply":
        pipe.receive.side_effect = EOFError("lost reply")
    elif failure == "exited":
        snapshots.side_effect = ValueError("peer exited")
    monkeypatch.setattr(host, "MessagePipe", lambda _: pipe)
    monkeypatch.setattr(identity, "process_snapshot", snapshots)
    client = AuthorityClient(
        pipe_id=str(uuid4()),
        authority_sid=SID,
        bot_sid=SID,
        trust_model=TRUST_MODEL,
        process_bindings=process_bindings(),
        deployment_hash="b" * 64,
        pipe_factory=factory,
        verify_server=verifier,
    )
    if failure:
        with pytest.raises(ExecutionUncertain):
            client._invoke({"version": 1, "action": "ready"})
    else:
        assert client._invoke({"version": 1, "action": "ready"}) == "ok"
    factory.assert_called_once()
    assert pipe.send.call_count == (0 if failure == "authenticate" else 1)
    assert process.Close.call_count == (0 if failure == "authenticate" else 1)
    pipe_handle.Close.assert_called_once()
