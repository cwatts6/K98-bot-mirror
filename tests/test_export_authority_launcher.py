"""Offline supervisor contract tests; no process, SQL connection or named pipe."""

import hashlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from scripts.run_export_authority import (
    AuthorityBroker,
    AuthorityStartupError,
    code_files,
    manifest_contract,
)
from services.export_runtime_composition import RuntimeRegistration
from tests.test_export_runtime_composition import registration_fixture


@pytest.fixture
def authority_launch(monkeypatch, tmp_path):
    import json

    import core.export_execution_host as host
    import kvk.dal.source_output_pool_dal as pools
    import scripts.enroll_export_output_pool as enrollment
    import scripts.run_export_authority as launcher
    import services.export_coordination_dal as coordination
    import services.export_enrollment_service as enrollment_service
    import services.export_execution_authority as execution
    import services.export_execution_dal as persistence
    import services.export_reconciliation_service as reconciliation
    import services.export_runtime_composition as runtime

    path = tmp_path / "fixture-manifest.json"
    manifest = {
        "sql_contract": {},
        "python": str(path),
        "child_script": "fixture-child",
        "authority_sid": "fixture-sid",
        "evidence_root": "fixture-store",
        "storage_owner": "fixture-owner",
        "runtime_registration": {},
    }
    path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(launcher, "bootstrap", Mock())
    monkeypatch.setattr(launcher, "manifest_contract", lambda value, **_: value)
    monkeypatch.setattr(host, "assert_protected_path", lambda value, **_: Path(value))
    monkeypatch.setattr(host, "current_sid", lambda: "fixture-sid")
    for name in ("DeploymentBoundary", "WindowsExecutionHost", "PrivateEvidenceStore"):
        monkeypatch.setattr(host, name, Mock())
    connector = Mock(side_effect=AssertionError("real SQL escaped offline test"))
    monkeypatch.setattr(launcher, "connection_factory", lambda _: connector)
    monkeypatch.setattr(runtime, "verify_installation_contract", Mock())
    factories = {}
    for name, module in {
        "RuntimeRegistration": runtime,
        "LocalAuthorityClient": runtime,
        "TrustedProofIssuer": reconciliation,
        "SourceOutputPoolDAL": pools,
        "ExportCoordinationDAL": coordination,
        "AuthorityBroker": launcher,
        "OutputEnrollment": enrollment_service,
    }.items():
        factories[name] = Mock()
        monkeypatch.setattr(module, name, factories[name])
    dal = Mock()
    dal.transition.return_value = {"Version": 7}
    monkeypatch.setattr(persistence, "ExportExecutionDAL", Mock(return_value=dal))
    authority = Mock()
    authority.drain.return_value = True
    factories["ExportExecutionAuthority"] = Mock(return_value=authority)
    monkeypatch.setattr(
        execution, "ExportExecutionAuthority", factories["ExportExecutionAuthority"]
    )
    serve = Mock()
    monkeypatch.setattr(launcher, "serve", serve)
    monkeypatch.setattr(enrollment, "bootstrap", Mock())
    monkeypatch.setattr(enrollment, "approved_plan", Mock())
    arguments = ["--manifest", str(path)]
    return SimpleNamespace(
        dal=dal,
        authority=authority,
        connector=connector,
        factories=factories,
        serve=serve,
        launchers={
            "authority": lambda: launcher.main(arguments),
            "enrollment": lambda: enrollment.main(
                arguments
                + [
                    "--plan",
                    str(path),
                    "--actor",
                    "fixture",
                    "--reason",
                    "fixture",
                    "--authorize-operation",
                    "S11_CREATE_PRIVATE_OUTPUT_POOL",
                ]
            ),
        },
    )


@pytest.mark.parametrize("drained", [False, True])
@pytest.mark.parametrize("serve_error", [None, KeyboardInterrupt, RuntimeError])
def test_authority_shutdown_reports_retained_session_and_preserves_service_errors(
    authority_launch, drained, serve_error
):
    setup = authority_launch
    authority, dal = setup.authority, setup.dal
    authority.drain.return_value = drained
    setup.serve.side_effect = serve_error

    if serve_error is RuntimeError:
        with pytest.raises(RuntimeError):
            setup.launchers["authority"]()
    else:
        assert setup.launchers["authority"]() == (0 if drained else 1)
    authority.drain.assert_called_once_with()
    transitions = dal.transition.call_args_list
    assert [call.kwargs["Action"] for call in transitions] == (
        ["open", "close"] if drained else ["open"]
    )
    if drained:
        assert transitions[-1].kwargs["ExpectedVersion"] == 7
        assert transitions[-1].kwargs["SessionID"] == transitions[0].kwargs["SessionID"]
    setup.connector.assert_not_called()


@pytest.mark.parametrize(
    "launcher,stage",
    [
        (launcher, stage)
        for launcher in ("authority", "enrollment")
        for stage in ("ExportCoordinationDAL", "ExportExecutionAuthority")
    ]
    + [
        ("authority", stage)
        for stage in (
            "RuntimeRegistration",
            "AuthorityBroker",
            "SourceOutputPoolDAL",
            "LocalAuthorityClient",
            "TrustedProofIssuer",
            "proof_import",
        )
    ]
    + [("enrollment", "OutputEnrollment")],
)
def test_post_open_initialization_failure_closes_empty_session(
    authority_launch, monkeypatch, launcher, stage
):
    import builtins

    setup = authority_launch
    failure = RuntimeError("inert initialization failure")
    if stage == "proof_import":
        original = builtins.__import__

        def import_fixture(name, *args, **kwargs):
            if name == "services.export_reconciliation_service":
                raise failure
            return original(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", import_fixture)
    else:
        setup.factories[stage].side_effect = failure
    with pytest.raises(RuntimeError) as caught:
        setup.launchers[launcher]()
    assert caught.value is failure
    calls = setup.dal.transition.call_args_list
    assert [call.kwargs["Action"] for call in calls] == ["open", "close"]
    assert calls[-1].kwargs["SessionID"] == calls[0].kwargs["SessionID"]
    assert calls[-1].kwargs["ExpectedVersion"] == 7
    if stage in {"ExportCoordinationDAL", "ExportExecutionAuthority"}:
        setup.authority.drain.assert_not_called()
    else:
        setup.authority.drain.assert_called_once_with()
    setup.serve.assert_not_called()
    setup.factories["OutputEnrollment"].return_value.run.assert_not_called()
    setup.connector.assert_not_called()


@pytest.mark.parametrize(
    "launcher,stage", [("authority", "TrustedProofIssuer"), ("enrollment", "OutputEnrollment")]
)
@pytest.mark.parametrize("drain_error", [False, True])
def test_startup_failure_retains_session_when_drain_is_unproven(
    authority_launch, launcher, stage, drain_error
):
    setup = authority_launch
    setup.factories[stage].side_effect = RuntimeError("initialization failed")
    setup.authority.drain.return_value = False
    if drain_error:
        setup.authority.drain.side_effect = RuntimeError("closure unknown")
    with pytest.raises(RuntimeError):
        setup.launchers[launcher]()
    setup.authority.drain.assert_called_once_with()
    assert [call.kwargs["Action"] for call in setup.dal.transition.call_args_list] == ["open"]


@pytest.mark.parametrize("launcher", ["authority", "enrollment"])
def test_uncertain_session_open_never_attempts_cleanup_or_retry(authority_launch, launcher):
    from services.export_execution_dal import EvidenceCommitUnknown

    setup = authority_launch
    setup.dal.transition.side_effect = EvidenceCommitUnknown("open acknowledgement lost")
    with pytest.raises(EvidenceCommitUnknown):
        setup.launchers[launcher]()
    setup.dal.transition.assert_called_once()
    assert setup.dal.transition.call_args.kwargs["Action"] == "open"
    setup.factories["ExportCoordinationDAL"].assert_not_called()
    setup.authority.drain.assert_not_called()


@pytest.mark.parametrize("launcher", ["authority", "enrollment"])
def test_startup_cleanup_close_failure_is_not_retried(authority_launch, launcher):
    from services.export_execution_dal import EvidenceCommitUnknown

    setup = authority_launch
    setup.factories["ExportCoordinationDAL"].side_effect = RuntimeError("setup failed")
    setup.dal.transition.side_effect = [
        {"Version": 7},
        EvidenceCommitUnknown("close acknowledgement lost"),
    ]
    with pytest.raises(EvidenceCommitUnknown):
        setup.launchers[launcher]()
    assert [call.kwargs["Action"] for call in setup.dal.transition.call_args_list] == [
        "open",
        "close",
    ]


@pytest.mark.parametrize("drained", [False, True])
def test_enrollment_exit_reports_incomplete_drain(authority_launch, drained):
    setup = authority_launch
    setup.authority.drain.return_value = drained
    assert setup.launchers["enrollment"]() == (0 if drained else 1)
    setup.authority.drain.assert_called_once_with()
    assert [call.kwargs["Action"] for call in setup.dal.transition.call_args_list] == (
        ["open", "close"] if drained else ["open"]
    )


@pytest.mark.parametrize("operation", ["reserve", "cooldown", "evidence"])
def test_authority_connection_factory_supports_budget_and_procedure_transactions(
    monkeypatch, operation
):
    from datetime import datetime

    import pyodbc

    from scripts.run_export_authority import connection_factory
    from services.export_coordination_dal import ExportCoordinationDAL
    from services.export_execution_dal import ExportExecutionDAL

    now = datetime(2026, 9, 25)
    responses = iter(
        {
            "reserve": [{"NowUTC": now}, None],
            "cooldown": [{"NowUTC": now}, {"CooldownUntilUTC": None, "Version": 7}, {"Version": 8}],
            "evidence": [{"Version": 1}],
        }[operation]
    )
    connections = []

    def open_fixture(target, *, autocommit, timeout):
        assert target == (
            "DRIVER={ODBC Driver 18 for SQL Server};SERVER=fixture-server;"
            "DATABASE=fixture-database;Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=no;"
        )
        assert timeout == 5
        connection, cursor = Mock(), Mock()
        connection.autocommit = autocommit
        connection.cursor.return_value = cursor
        cursor.description = [("Version",)]
        cursor.fetchall.return_value = []
        cursor.nextset.return_value = False

        def execute(query, *arguments):
            assert query.count("?") == len(arguments)
            # Exercise the actual DAL/transaction helpers, not a patched transaction.
            assert connection.autocommit is (operation == "evidence")

        def fetchone():
            row = next(responses)
            if row is None:
                return None
            cursor.description = [(key,) for key in row]
            return tuple(row.values())

        cursor.execute.side_effect = execute
        cursor.fetchone.side_effect = fetchone
        connections.append(connection)
        return connection

    driver = Mock(side_effect=open_fixture)
    monkeypatch.setattr(pyodbc, "connect", driver)
    connect = connection_factory(
        {"sql_server": "fixture-server", "sql_database": "fixture-database"}
    )
    if operation == "reserve":
        assert ExportCoordinationDAL(connect).reserve_request("fixture") == {
            "ReservedUTC": now,
            "WaitSeconds": 0,
        }
    elif operation == "cooldown":
        ExportCoordinationDAL(connect).extend_cooldown("fixture", 12)
    else:
        assert ExportExecutionDAL(connect).transition(
            "session",
            SessionID=str(uuid4()),
            Action="close",
            ExpectedVersion=7,
        ) == {"Version": 1}
    driver.assert_called_once()
    assert driver.call_args.kwargs["autocommit"] is False
    connection = connections[0]
    if operation == "evidence":
        connection.commit.assert_not_called()  # the stored procedure owns its transaction
    else:
        connection.commit.assert_called_once_with()
    connection.rollback.assert_not_called()
    connection.close.assert_called_once_with()


def registration():
    return RuntimeRegistration(registration_fixture())


def scope(account="account-a"):
    return dict(
        AccountKey=account,
        OwnerKind="job",
        ObjectID=str(uuid4()),
        OwnerID=str(uuid4()),
        Fence=3,
        ClaimVersion=7,
        NestedToken=None,
        RegistrationHash=registration().value()["pools"][0]["registration_sha256"],
        Epoch=2,
        SnapshotHash="b" * 64,
        Purpose="mutation",
        ScopeJson={
            "resources": [
                {"key": "account:" + account, "version": 4},
                {"key": "destination:index-0", "version": 7},
                {"key": "destination:slot-0-0", "version": 7},
                {"key": "destination:slot-0-1", "version": 7},
            ]
        },
    )


def test_broker_accepts_only_typed_open_execute_and_close():
    authority = SimpleNamespace(
        open_stream=Mock(side_effect=lambda **kw: kw["stream_id"]),
        execute=Mock(return_value={"id": "file-aaa"}),
        close_stream=Mock(return_value={"version": 4}),
    )
    broker = AuthorityBroker(authority, registration())
    stream_id = str(uuid4())
    assert (
        broker.dispatch(dict(version=1, action="open", stream_id=stream_id, scope=scope()))["state"]
        == "open"
    )
    submitted = authority.open_stream.call_args.kwargs["scope"]
    assert submitted["RegistrationHash"] == bytes.fromhex(scope()["RegistrationHash"])
    assert submitted["ScopeJson"].startswith('{"resources":')
    request = dict(
        version=1,
        request_id=str(uuid4()),
        stream_id=stream_id,
        operation="drive.files.get",
        target="file-aaa",
        arguments={"fields": "id"},
    )
    assert (
        broker.dispatch(dict(version=1, action="execute", request=request))["request_id"]
        == request["request_id"]
    )
    assert broker.dispatch(dict(version=1, action="close", stream_id=stream_id)) == {"version": 4}


def test_broker_preserves_absent_owner_and_zero_fence_for_closing_probe():
    authority = SimpleNamespace(open_stream=Mock(side_effect=lambda **kw: kw["stream_id"]))
    request_scope = scope() | {
        "OwnerKind": "operation",
        "OwnerID": None,
        "Fence": 0,
        "Purpose": "probe",
    }
    AuthorityBroker(authority, registration()).dispatch(
        dict(version=1, action="open", stream_id=str(uuid4()), scope=request_scope)
    )
    submitted = authority.open_stream.call_args.kwargs["scope"]
    assert submitted["OwnerID"] is None and submitted["Fence"] == 0


@pytest.mark.parametrize(
    "damage",
    [
        lambda s: s.update(AccountKey="unregistered"),
        lambda s: s.update(RegistrationHash="f" * 64),
        lambda s: s.update(Epoch=None),
        lambda s: s.update(OwnerKind="preparation"),
        lambda s: s["ScopeJson"]["resources"].pop(),
        lambda s: s["ScopeJson"]["resources"][-1].update(key="destination:slot-other"),
        lambda s: s["ScopeJson"]["resources"].append(
            {"key": "sql_snapshot:legacy_outputs", "version": 1}
        ),
    ],
)
def test_unregistered_stream_is_refused_before_child_or_sql_creation(damage):
    from kvk.dal.new_source_import_dal import SourceConflict

    authority = Mock()
    request_scope = scope()
    damage(request_scope)
    # Preserve valid wire ordering so this exercises protected registration too.
    request_scope["ScopeJson"]["resources"].sort(key=lambda r: r["key"])
    with pytest.raises((SourceConflict, ValueError)):
        AuthorityBroker(authority, registration()).dispatch(
            dict(version=1, action="open", stream_id=str(uuid4()), scope=request_scope)
        )
    authority.open_stream.assert_not_called()


@pytest.mark.parametrize(
    "change",
    [
        {"OwnerKind": "job"},
        {"OwnerKind": "preparation"},
        {"Purpose": "mutation"},
        {"Fence": 1},
        {"Fence": False},
        {"NestedToken": str(uuid4())},
    ],
)
def test_broker_rejects_other_ownerless_scopes(change):
    authority = Mock()
    request_scope = (
        scope()
        | {"OwnerKind": "operation", "OwnerID": None, "Fence": 0, "Purpose": "probe"}
        | change
    )
    with pytest.raises(ValueError):
        AuthorityBroker(authority, registration()).dispatch(
            dict(version=1, action="open", stream_id=str(uuid4()), scope=request_scope)
        )
    authority.open_stream.assert_not_called()


@pytest.mark.parametrize(
    "damage",
    [
        lambda x: x | {"version": True},
        lambda x: x | {"action": "proof"},
        lambda x: x | {"arbitrary": "extra"},
        lambda x: x | {"scope": scope() | {"Fence": True}},
        lambda x: x
        | {
            "scope": scope()
            | {
                "ScopeJson": {
                    "resources": [
                        {"key": "destination:file-aaa", "version": 7},
                        {"key": "account:account-a", "version": 4},
                    ]
                }
            }
        },
    ],
)
def test_malformed_or_proof_authoring_message_never_reaches_authority(damage):
    authority = Mock()
    broker = AuthorityBroker(authority, registration())
    original = dict(version=1, action="open", stream_id=str(uuid4()), scope=scope())
    with pytest.raises(ValueError):
        broker.dispatch(damage(original))
    authority.open_stream.assert_not_called()
    authority.execute.assert_not_called()


@pytest.mark.parametrize("enrollment", [False, True])
def test_manifest_requires_exact_distinct_ids_and_full_source_inventory(enrollment):
    from tests.test_export_runtime_composition import installation_fixture

    _observation, sql_contract = installation_fixture()
    sql_contract["database"] = "K98"
    root = Path(__file__).resolve().parents[1]
    sources = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in code_files(root)
    }
    manifest = dict(
        version=1,
        authority_sid="S-1-5-21-111-222-333-444",
        bot_sid="S-1-5-21-111-222-333-555",
        pipe_id=str(uuid4()),
        python="C:/protected/python.exe",
        child_script=str(root / "scripts/run_export_provider_child.py"),
        credentials_file="C:/protected/credentials.json",
        evidence_root="C:/protected/evidence",
        storage_owner="s11-evidence",
        sql_server="sql-host",
        sql_database="K98",
        sql_contract=sql_contract,
        service_account_email="editor@example.iam.gserviceaccount.com",
        project_id="project",
        source_hashes=sources,
        runtime_registration=registration_fixture(),
    )
    inspect = Mock()
    if not enrollment:
        manifest.update(version=2, deployment_boundary={})
    if enrollment:
        manifest.pop("runtime_registration")
        manifest["enrollment_profile"] = dict(
            version=1,
            owner_email="owner@example.com",
            client_id="123-app.apps.googleusercontent.com",
            scopes=["https://www.googleapis.com/auth/drive.file"],
        )
    assert (
        manifest_contract(
            manifest,
            script=root / "scripts/run_export_authority.py",
            current_sid=manifest["authority_sid"],
            inspect_path=inspect,
            enrollment=enrollment,
        )
        is manifest
    )
    with pytest.raises(AuthorityStartupError, match="Separate"):
        manifest_contract(
            manifest | {"bot_sid": manifest["authority_sid"]},
            script=root / "scripts/run_export_authority.py",
            current_sid=manifest["authority_sid"],
            inspect_path=inspect,
            enrollment=enrollment,
        )
    with pytest.raises(AuthorityStartupError, match="inventory"):
        manifest_contract(
            manifest | {"source_hashes": {}},
            script=root / "scripts/run_export_authority.py",
            current_sid=manifest["authority_sid"],
            inspect_path=inspect,
            enrollment=enrollment,
        )
    for contract in (
        {},
        sql_contract | {"version": 1},
        sql_contract | {"database": "other-db"},
        sql_contract | {"profile": "reader"},
    ):
        with pytest.raises(AuthorityStartupError, match="SQL"):
            manifest_contract(
                manifest | {"sql_contract": contract},
                script=root / "scripts/run_export_authority.py",
                current_sid=manifest["authority_sid"],
                inspect_path=inspect,
                enrollment=enrollment,
            )
    with pytest.raises(AuthorityStartupError, match="manifest"):
        manifest_contract(
            manifest,
            script=root / "scripts/run_export_authority.py",
            current_sid=manifest["authority_sid"],
            inspect_path=inspect,
            enrollment=not enrollment,
        )


@pytest.mark.parametrize("enrollment", [False, True])
@pytest.mark.parametrize(
    "mismatch", ["migration", "target", "definition", "budget", "origin_read", "column_write"]
)
def test_explicit_authority_startup_checks_installation_before_session_store_or_child(
    monkeypatch, tmp_path, mismatch, enrollment
):
    import json

    import core.export_execution_host as host
    from kvk.dal.new_source_import_dal import SourceConflict
    import scripts.run_export_authority as launcher
    import services.export_execution_dal as persistence
    from tests.test_export_runtime_composition import installation_fixture

    observation, approved = installation_fixture()
    if mismatch == "migration":
        observation["migrations"].pop()
    elif mismatch == "target":
        observation["target"]["DatabaseName"] = "other-database"
    elif mismatch == "definition":
        observation["metadata"]["columns"][0]["ColumnName"] = "changed"
    else:
        name, column, permission = {
            "budget": ("dbo.ExportRequestBudget", None, "INSERT"),
            "origin_read": ("dbo.ExportPreparation", None, "SELECT"),
            "column_write": ("dbo.ExportReconciliationProof", "fixture_id", "UPDATE"),
        }[mismatch]
        row = next(
            p
            for p in observation["permissions"]
            if (p["ObjectName"], p["ColumnName"], p["PermissionName"]) == (name, column, permission)
        )
        row["Allowed"] = 1 - row["Allowed"]
    manifest = {"sql_contract": approved}
    path = tmp_path / "fixture-manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(launcher.sys, "path", list(launcher.sys.path))
    monkeypatch.setattr(host, "assert_protected_path", lambda value, **_: Path(value))
    monkeypatch.setattr(host, "current_sid", lambda: "fixture-sid")
    monkeypatch.setattr(launcher, "manifest_contract", lambda value, **_: value)
    monkeypatch.setattr(launcher, "bootstrap", lambda *_, **__: None)
    monkeypatch.setattr(host, "DeploymentBoundary", Mock())
    connector = Mock(side_effect=AssertionError("real SQL open escaped offline test"))
    monkeypatch.setattr(launcher, "connection_factory", lambda _: connector)
    dal = Mock()
    dal.installation_snapshot.return_value = observation
    monkeypatch.setattr(persistence, "ExportExecutionDAL", Mock(return_value=dal))
    process_factory, store_factory = Mock(), Mock()
    monkeypatch.setattr(host, "WindowsExecutionHost", process_factory)
    monkeypatch.setattr(host, "PrivateEvidenceStore", store_factory)
    run, arguments = launcher.main, ["--manifest", str(path)]
    if enrollment:
        import scripts.enroll_export_output_pool as enrollment_launcher

        monkeypatch.setattr(enrollment_launcher, "bootstrap", lambda *_: None)
        monkeypatch.setattr(enrollment_launcher, "approved_plan", lambda *_: object())
        run = enrollment_launcher.main
        arguments += [
            "--plan",
            str(path),
            "--actor",
            "fixture",
            "--reason",
            "fixture",
            "--authorize-operation",
            "S11_CREATE_PRIVATE_OUTPUT_POOL",
        ]
    with pytest.raises(SourceConflict):
        run(arguments)
    connector.assert_not_called()
    dal.transition.assert_not_called()
    process_factory.assert_not_called()
    store_factory.assert_not_called()
