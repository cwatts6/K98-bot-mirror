"""Offline authority transport boundaries; no provider identity or network is used."""

from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from kvk.services.new_source_delivery_service import (
    RemoteOutcomeUnknown,
    deliver_coordinated_export,
)
from kvk.services.new_source_export_service import GoogleSheetsTransport, SheetsRegistration
from services.export_runtime_composition import OutputOperationStreams, output_operation_scope


def test_runtime_shutdown_preserves_entered_child_and_refuses_delayed_context():
    from contextvars import copy_context

    from services.export_runtime_composition import RuntimeLifetime

    runtime = RuntimeLifetime(object())
    with runtime.owned():
        context = copy_context()
        child = context.run(runtime.owned)
        context.run(child.__enter__)
        runtime.stop()
        # Owned nested work can finish after new admission closes.
        with runtime.owned():
            pass
    assert len(runtime._calls) == 1

    def delayed():
        with runtime.owned():
            pass

    with pytest.raises(SourceConflict, match="stale"):
        context.run(delayed)
    context.run(child.__exit__, None, None, None)
    assert not runtime._calls
    runtime.drain()
    with pytest.raises(SourceConflict, match="closed"):
        with runtime.owned():
            pass


@pytest.mark.asyncio
async def test_bound_actual_async_caller_drains_on_repeated_cancellation(monkeypatch):
    import asyncio
    import threading

    import services.export_runtime_composition as composition
    from services.legacy_export_snapshot_service import bound_runtime, drain_thread, require_runtime

    runtime = composition.RuntimeLifetime(object())
    monkeypatch.setattr(composition, "_installed", runtime)
    monkeypatch.setattr("bot_config.EXPORT_COORDINATION_ENABLED", True)
    entered, release = threading.Event(), threading.Event()

    def work():
        assert require_runtime() is runtime.legacy
        entered.set()
        assert release.wait(5)

    @bound_runtime
    async def caller():
        return await drain_thread(work)

    task = asyncio.create_task(caller())
    while not entered.is_set():
        await asyncio.sleep(0)
    task.cancel()
    await asyncio.sleep(0)
    task.cancel()
    runtime.stop()
    await asyncio.sleep(0)
    assert runtime._calls and not task.done()
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert not runtime._calls


def test_startup_flags_or_missing_packet_cannot_construct_runtime(monkeypatch):
    import services.export_runtime_composition as composition

    constructor = Mock(side_effect=AssertionError("runtime constructed before readiness"))
    monkeypatch.setattr(composition, "_installed", None)
    monkeypatch.setattr(composition, "_runtime_stopped", False)
    monkeypatch.setattr(composition, "_installing", False)
    monkeypatch.setattr(composition, "ExportRuntime", constructor)
    monkeypatch.setattr("bot_config.EXPORT_COORDINATION_ENABLED", False)
    assert composition.install_configured_runtime() is None
    monkeypatch.setattr("bot_config.EXPORT_COORDINATION_ENABLED", True)
    monkeypatch.delenv("K98_EXPORT_RUNTIME_MANIFEST", raising=False)
    with pytest.raises(SourceConflict, match="manifest"):
        composition.install_configured_runtime()
    with pytest.raises(SourceConflict, match="readiness"):
        composition.configured_runtime()
    constructor.assert_not_called()


def test_shutdown_during_slow_readiness_never_blocks_callers_or_publishes_bundle(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    import threading

    import services.export_runtime_composition as composition

    monkeypatch.setattr(composition, "_installed", None)
    monkeypatch.setattr(composition, "_installing", False)
    monkeypatch.setattr(composition, "_runtime_stopped", False)
    monkeypatch.setattr("bot_config.EXPORT_COORDINATION_ENABLED", True)
    entered, release = threading.Event(), threading.Event()
    bundle = composition.RuntimeLifetime(object())

    def prepare():
        entered.set()
        assert release.wait(5)
        return bundle

    monkeypatch.setattr(composition, "_prepare_configured_runtime", prepare)
    with ThreadPoolExecutor(max_workers=1) as executor:
        pending = executor.submit(composition.install_configured_runtime)
        assert entered.wait(5)
        try:
            with pytest.raises(SourceConflict, match="readiness"):
                composition.configured_runtime()
            with pytest.raises(SourceConflict, match="progress"):
                composition.install_configured_runtime()
            composition.stop_runtime_admission()
        finally:
            release.set()
        with pytest.raises(SourceConflict, match="Shutdown"):
            pending.result(timeout=5)
    assert composition._installed is None and bundle._accepting is False
    assert composition._installing is False


def application_installation_fixture(monkeypatch):
    import services.export_execution_dal as evidence

    sources = [
        dict(name="dbo.fixture", type="U", path="sql_schema/dbo.fixture.Table.sql", sha256="a" * 64)
    ]
    monkeypatch.setattr(evidence, "APPLICATION_SCHEMA_SOURCE_HASH", digest(sources).hex())
    metadata = {key: [] for key in evidence.INSTALLATION_METADATA}
    metadata.update(table_types=[], dependencies=[], synonyms=[], database_triggers=[])
    metadata["objects"] = [dict(ObjectName="dbo.fixture", ObjectType="U", ModuleDefinition=None)]
    metadata["columns"] = [dict(ObjectName="dbo.fixture", ColumnName="id", Ordinal=1)]
    permissions = dict(
        schema_permissions=[],
        object_permissions=[],
        column_permissions=[
            dict(ObjectName="dbo.fixture", ColumnName="id", PermissionName="SELECT", Allowed=1)
        ],
    )
    approved = dict(
        version=1,
        server="fixture",
        database="ROK_TRACKER",
        principal="restricted",
        sources=sources,
        dynamic_objects=[],
        metadata_hash=digest(metadata).hex(),
        permissions_hash=digest(permissions).hex(),
        review_id=str(uuid4()),
    )
    observed = dict(
        version=1,
        target=dict(
            ServerName="fixture",
            DatabaseName="ROK_TRACKER",
            Principal="restricted",
            ViewDefinition=1,
        ),
        metadata=metadata,
        **permissions,
    )
    return observed, approved


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "source",
        "permission",
        "unknown_permission",
        "trigger",
        "dependency",
        "column",
        "extra_table",
        "target",
        "missing_type",
        "dynamic_unknown_root",
    ],
)
def test_application_readiness_covers_source_shapes_dependencies_and_effective_permissions(
    monkeypatch, damage
):
    from services.export_runtime_composition import verify_application_installation_contract

    observed, approved = application_installation_fixture(monkeypatch)
    if damage == "source":
        approved["sources"].clear()
    elif damage in {"permission", "unknown_permission"}:
        observed["column_permissions"][0]["Allowed"] = 0 if damage == "permission" else None
    elif damage == "trigger":
        observed["metadata"]["database_triggers"].append(
            dict(TriggerName="unknown", ModuleDefinition=None, Disabled=0)
        )
    elif damage == "dependency":
        observed["metadata"]["dependencies"].append(
            dict(ObjectName="dbo.fixture", EntityName="foreign")
        )
    elif damage == "column":
        observed["metadata"]["columns"][0]["ColumnName"] = "different"
    elif damage == "extra_table":
        observed["metadata"]["objects"].append(
            dict(ObjectName="dbo.unknown", ObjectType="U", ModuleDefinition=None)
        )
    elif damage == "target":
        observed["target"]["Principal"] = "another"
    elif damage == "missing_type":
        observed["metadata"].pop("table_types")
    elif damage == "dynamic_unknown_root":
        approved["dynamic_objects"] = [
            dict(name="dbo.dynamic", type="U", producer_modules=["dbo.not_reviewed"])
        ]
    if damage:
        with pytest.raises(SourceConflict):
            verify_application_installation_contract(observed, approved)
    else:
        assert (
            verify_application_installation_contract(observed, approved) == digest(observed).hex()
        )


def test_local_authority_probe_uses_registered_broker_without_connecting_to_its_own_pipe(
    monkeypatch,
):
    from scripts.run_export_authority import AuthorityBroker
    from services.export_execution_protocol import ProviderRequest
    from services.export_runtime_composition import (
        AuthorityClient,
        LocalAuthorityClient,
        RuntimeRegistration,
    )
    from tests.test_export_authority_launcher import scope

    authority = SimpleNamespace(
        enrollment_plan=None,
        open_stream=Mock(side_effect=lambda **kw: kw["stream_id"]),
        execute=Mock(return_value={"id": "index-0"}),
        close_stream=Mock(side_effect=lambda identifier: dict(stream_id=identifier, version=5)),
    )
    connector = Mock(side_effect=AssertionError("local proof tried self-IPC"))
    monkeypatch.setattr(AuthorityClient, "_connect_pipe", connector)
    client = LocalAuthorityClient(
        AuthorityBroker(authority, RuntimeRegistration(registration_fixture()))
    )
    with client.stream(scope() | {"Purpose": "probe"}) as stream:
        request = ProviderRequest.parse(
            dict(
                version=1,
                request_id=str(uuid4()),
                stream_id=stream.stream_id,
                operation="drive.files.get",
                target="index-0",
                arguments={"fields": "id"},
            )
        )
        assert stream.execute(request.message()) == {"id": "index-0"}
    authority.open_stream.assert_called_once()
    authority.execute.assert_called_once()
    authority.close_stream.assert_called_once_with(stream.stream_id)
    connector.assert_not_called()


def test_local_probe_preserves_registration_rejection_and_cannot_use_creation_profile():
    from scripts.run_export_authority import AuthorityBroker
    from services.export_execution_authority import ExecutionUncertain
    from services.export_runtime_composition import LocalAuthorityClient, RuntimeRegistration
    from tests.test_export_authority_launcher import scope

    authority = SimpleNamespace(enrollment_plan=None, open_stream=Mock())
    broker = AuthorityBroker(authority, RuntimeRegistration(registration_fixture()))
    client = LocalAuthorityClient(broker)
    with pytest.raises(ExecutionUncertain):
        with client.stream(scope() | {"AccountKey": "unregistered"}):
            pytest.fail("unregistered probe opened")
    with pytest.raises(ExecutionUncertain):
        with client.stream(scope()):
            pytest.fail("local proof opened a mutation stream")
    authority.open_stream.assert_not_called()
    authority.enrollment_plan = object()
    with pytest.raises(SourceConflict):
        LocalAuthorityClient(broker)


def legacy_stream_fixture(*, consumer="all_kvk"):
    from services.export_coordination_dal import Claim, bounded_json
    from services.export_runtime_composition import LegacyExecutionStreams
    from services.legacy_export_snapshot_dal import PreparationClaim
    from services.legacy_export_snapshot_service import configuration_digest

    configuration = {
        "all_kvk": dict(
            consumer="all_kvk", kvk_no=16, destinations=["legacy-aaa"], label="\u00c9poque"
        ),
        "scan_data": dict(consumer="scan_data", kvk_no=None, destinations=["daily-aaaa"]),
        "config": dict(consumer="config", kvk_no=None, destinations=["config-aaa"]),
    }
    configured = configuration[consumer]
    files = tuple(configured["destinations"])
    resources = tuple(
        (key, 4) for key in sorted(["account:account-a", *("destination:" + f for f in files)])
    )
    identifier, owner = str(uuid4()), str(uuid4())
    if consumer == "config":
        claim = PreparationClaim(identifier, "account-a", owner, 3, 5, resources)
        request = dict(
            consumer="config",
            kvk_no=None,
            request={"read_configuration": str(uuid4())},
            storage_owner="spool-owner",
        )
        row = dict(
            PreparationID=identifier,
            ConsumerKind=consumer,
            AccountKey="account-a",
            OwnerID=owner,
            Fence=3,
            Version=5,
            State="preflight",
            KVK_NO=None,
            StorageOwner="spool-owner",
            RequestJson=bounded_json(request),
            RequestHash=digest(request),
            SpoolKey=None,
            SpoolBytes=None,
            SpoolHash=None,
            JobID=None,
        )
    else:
        claim = Claim(identifier, "account-a", owner, 3, 5, resources, None)
        row = dict(
            JobID=identifier,
            ConsumerKind=consumer,
            AccountKey="account-a",
            OwnerID=owner,
            Fence=3,
            Version=5,
            State="running",
            KVK_NO=configured["kvk_no"],
            PoolEpoch=None,
            SourceKey=None,
            IntentID=None,
            StorageOwner="spool-owner",
            DestinationSetHash=digest(files),
            InputHash=b"a" * 32,
            SpoolKey="retained",
            SpoolBytes=42,
            ProvenanceJson=bounded_json({"registration_sha256": configuration_digest(configured)}),
        )
    coordinator = Mock(execution_evidence=True, output_operations=True, preparations=True)
    preparations = Mock(execution_evidence=True, output_operations=True)
    coordinator.authorize.return_value = row
    preparations.authorize.return_value = row
    client = Mock()
    streams = LegacyExecutionStreams(
        coordinator=coordinator,
        preparations=preparations,
        client=client,
        account="account-a",
        storage_owner="spool-owner",
        configuration=configuration,
    )
    return SimpleNamespace(
        streams=streams,
        client=client,
        coordinator=coordinator,
        preparations=preparations,
        row=row,
        claim=claim,
        files=files,
        configuration=configuration,
    )


@pytest.mark.parametrize("consumer", ["all_kvk", "scan_data", "config"])
def test_legacy_streams_pin_immutable_registration_and_current_claim(consumer):
    from services.legacy_export_snapshot_service import configuration_digest

    f = legacy_stream_fixture(consumer=consumer)
    expected_hash = configuration_digest(f.configuration[consumer])
    f.configuration[consumer]["destinations"].append("not-retained")
    if consumer == "config":
        f.streams.configuration(f.claim, f.files)
    else:
        f.streams.delivery(f.row, f.claim, f.files)
    scope = f.client.stream.call_args.args[0]
    assert scope["RegistrationHash"] == expected_hash
    assert (scope["OwnerID"], scope["Fence"], scope["ClaimVersion"]) == (f.row["OwnerID"], 3, 5)
    assert scope["ScopeJson"]["resources"] == [
        {"key": k, "version": v} for k, v in f.claim.resources
    ]
    assert scope["NestedToken"] is None and scope["Epoch"] is None
    assert scope["Purpose"] == ("probe" if consumer == "config" else "mutation")
    f.coordinator.claim_next.assert_not_called()
    f.preparations.claim.assert_not_called()


@pytest.mark.parametrize("consumer", ["all_kvk", "scan_data", "config"])
@pytest.mark.parametrize(
    "damage", ["owner", "version", "fence", "storage", "account", "resource", "state"]
)
def test_legacy_streams_refuse_changed_claim_without_provider_or_adoption(consumer, damage):
    from dataclasses import replace

    f = legacy_stream_fixture(consumer=consumer)
    if damage == "resource":
        f.claim = replace(f.claim, resources=f.claim.resources[:-1])
    else:
        key, value = {
            "owner": ("OwnerID", str(uuid4())),
            "version": ("Version", 7),
            "fence": ("Fence", 9),
            "storage": ("StorageOwner", "another-owner"),
            "account": ("AccountKey", "other-account"),
            "state": ("State", "uncertain"),
        }[damage]
        f.row[key] = value
    with pytest.raises(SourceConflict):
        if consumer == "config":
            f.streams.configuration(f.claim, f.files)
        else:
            f.streams.delivery(f.row, f.claim, f.files)
    f.client.stream.assert_not_called()


@pytest.mark.parametrize("damage", ["input", "provenance", "destination", "epoch", "season"])
def test_legacy_delivery_refuses_stale_capture_or_new_source_scope(damage):
    f = legacy_stream_fixture()
    original = deepcopy(f.row)
    if damage == "input":
        f.row["InputHash"] = b"b" * 32
    elif damage == "provenance":
        f.row["ProvenanceJson"] = "{}"
        original = f.row
    elif damage == "destination":
        f.row["DestinationSetHash"] = b"c" * 32
        original = f.row
    elif damage == "epoch":
        f.row["PoolEpoch"] = 2
        original = f.row
    else:
        f.row["KVK_NO"] = 17
        original = f.row
    with pytest.raises(SourceConflict):
        f.streams.delivery(original, f.claim, f.files)
    f.client.stream.assert_not_called()


@pytest.mark.parametrize("damage", ["request", "destinations", "job"])
def test_configuration_probe_refuses_changed_request_or_other_files(damage):
    f = legacy_stream_fixture(consumer="config")
    files = f.files
    if damage == "request":
        f.row["RequestHash"] = b"f" * 32
    elif damage == "destinations":
        files = ("another-file",)
    else:
        f.row["JobID"] = str(uuid4())
    with pytest.raises(SourceConflict):
        f.streams.configuration(f.claim, files)
    f.client.stream.assert_not_called()


def operation_snapshot(*, running=False):
    pool_id, operation_id = str(uuid4()), str(uuid4())
    owner = str(uuid4()) if running else None
    pool = dict(
        PoolID=pool_id,
        AccountKey="account-a",
        IndexFileID="index-id",
        Epoch=2,
        OwnerID=operation_id,
        PoolState="closing",
        Version=10,
        RegistrationJson='{"registered":true}',
        RegistrationHash=digest({"registered": True}).hex(),
    )
    slots = [{"FileID": "slot-aaa"}, {"FileID": "slot-bbb"}]
    plan = dict(snapshot=dict(pool=pool, slots=slots))
    op = dict(
        PoolID=pool_id,
        ActivePoolID=pool_id,
        OperationID=operation_id,
        AccountKey="account-a",
        OwnerID=owner,
        Fence=3 if running else 0,
        Version=7,
        OldEpoch=2,
        State="running" if running else "closing",
        Phase="clear_pending" if running else "draining",
        CurrentFileID="slot-aaa" if running else None,
        PlanJson=json.dumps(plan),
        PlanHash=digest(plan).hex(),
    )
    keys = [
        "account:account-a",
        "destination:index-id",
        "destination:slot-aaa",
        "destination:slot-bbb",
    ]
    resources = [
        dict(
            ResourceKey=key,
            Version=4,
            OwnerID=owner,
            Fence=3,
            ActiveJobID=None,
            ActivePreparationID=None,
            BlockedReason=None,
            ActiveOutputOperationID=operation_id if running else None,
        )
        for key in keys
    ]
    return dict(
        operation=op, resources=resources, pool=dict(pool=pool, slots=slots, registration_count=1)
    )


def test_closing_probe_pins_drain_snapshot_without_claiming_or_fabricating_owner():
    snapshot = operation_snapshot()
    original = deepcopy(snapshot)
    scope = output_operation_scope(snapshot, purpose="probe")
    assert scope["OwnerID"] is None and scope["Fence"] == 0
    assert scope["SnapshotHash"] == digest(snapshot["pool"]).hex()
    assert scope["ObjectID"] == snapshot["operation"]["OperationID"]
    client = Mock()
    pools = Mock(execution_evidence=True)
    pools.operation_snapshot.return_value = snapshot
    OutputOperationStreams(pools=pools, client=client).closing_probe(snapshot)
    client.stream.assert_called_once_with(scope)
    pools.assert_not_called()
    assert snapshot == original


@pytest.mark.parametrize(
    "damage",
    [
        lambda s: s["operation"].update(State="ready"),
        lambda s: s["operation"].update(Phase="ready"),
        lambda s: s["operation"].update(Fence=1),
        lambda s: s["operation"].update(Version=0),
        lambda s: s["operation"].update(OldEpoch=3),
        lambda s: s["pool"]["pool"].update(OwnerID=str(uuid4())),
        lambda s: s["pool"]["pool"].update(RegistrationHash="f" * 64),
        lambda s: s["resources"][0].update(OwnerID=str(uuid4())),
        lambda s: s["resources"][0].update(ActiveJobID=str(uuid4())),
        lambda s: s["resources"][0].update(ActivePreparationID=str(uuid4())),
        lambda s: s["resources"][0].update(ActiveOutputOperationID=str(uuid4())),
        lambda s: s["resources"][0].update(Version=0),
        lambda s: s["resources"].pop(),
        lambda s: s["resources"].append(deepcopy(s["resources"][0])),
    ],
)
def test_closing_probe_rejects_changed_scope_before_ipc(damage):
    snapshot = operation_snapshot()
    damage(snapshot)
    client = Mock()
    with pytest.raises(SourceConflict):
        OutputOperationStreams(pools=Mock(execution_evidence=True), client=client).closing_probe(
            snapshot
        )
    client.stream.assert_not_called()


def test_closing_probe_cannot_become_a_mutation_stream():
    with pytest.raises(SourceConflict, match="unowned closing"):
        output_operation_scope(operation_snapshot(), purpose="mutation")


def test_phase_binding_checks_exact_claim_before_open_and_binds_fresh_snapshot():
    from kvk.dal.source_output_pool_dal import OutputClaim

    snapshot = operation_snapshot(running=True)
    op = snapshot["operation"]
    claim = OutputClaim(
        op["OperationID"],
        op["AccountKey"],
        op["OwnerID"],
        op["Fence"],
        op["Version"],
        tuple((r["ResourceKey"], r["Version"]) for r in snapshot["resources"]),
        10,
    )
    client, pools = Mock(), Mock(execution_evidence=True)
    pools.operation_snapshot.return_value = snapshot
    streams = OutputOperationStreams(pools=pools, client=client)
    streams(claim, op, "clear_pending", "slot-aaa")
    scope = client.stream.call_args.args[0]
    assert (
        scope["ClaimVersion"] == claim.version and scope["SnapshotHash"] == digest(snapshot).hex()
    )
    client.reset_mock()
    op["Version"] += 1
    with pytest.raises(SourceConflict, match="exact claimed version"):
        streams(claim, op, "clear_pending", "slot-aaa")
    client.stream.assert_not_called()


def transport(execution):
    registration = SheetsRegistration(
        "index-id",
        ("slot-aaa", "slot-bbb"),
        "owner@example.invalid",
        "editor@example.iam.gserviceaccount.com",
    )
    authorize = Mock()
    result = GoogleSheetsTransport.from_authority(
        registration=registration,
        reuse_guard=lambda *_: False,
        protected_file_ids=(),
        execution=execution,
        stream_id=str(uuid4()),
        authorize=authorize,
    )
    return result, authorize


def owned_new_source_snapshot(*, recovery=False):
    from tests.test_kvk_output_rollover import interrupted_retirement_fixture

    snapshot, _ = interrupted_retirement_fixture()
    job = snapshot["job"]
    job.update(
        JobID=str(uuid4()), OwnerID=str(uuid4()), State="running", Version=9, PoolEpoch=1, KVK_NO=43
    )
    pool = snapshot["pool"]["pool"]
    pool.update(
        PoolID=str(uuid4()),
        ActiveKVK=43,
        AccountKey="acct",
        RegistrationJson='{"registered":true}',
        RegistrationHash=digest({"registered": True}).hex(),
    )
    snapshot["pool"]["slots"].append(dict(FileID="fake-2", State="free"))
    snapshot["pool"]["registration_count"] = 1
    event = snapshot["retirement_events"][0]
    event.update(OwnerID=job["OwnerID"], PoolID=pool["PoolID"])
    files = ("fake-1", "fake-2", "fake-index")
    job["DestinationSetHash"] = digest(files).hex()
    snapshot["resources"] = [
        dict(
            ResourceKey=key,
            Version=7,
            Fence=5,
            OwnerID=job["OwnerID"],
            ActiveJobID=job["JobID"],
            ActivePreparationID=None,
            ActiveOutputOperationID=None,
            BlockedReason=None,
        )
        for key in ("account:acct", *("destination:" + f for f in files))
    ]
    if recovery:
        job["ProvenanceJson"] = json.dumps(
            dict(
                retirement_recovery=dict(
                    token=str(uuid4()),
                    state="owned",
                    version=9,
                    pool_id=pool["PoolID"],
                    epoch=1,
                    registration_hash=pool["RegistrationHash"],
                    attempt_id="current",
                )
            )
        )
    claim = SimpleNamespace(
        job_id=job["JobID"],
        owner_id=job["OwnerID"],
        account="acct",
        fence=5,
        version=9,
        resources=tuple((r["ResourceKey"], r["Version"]) for r in snapshot["resources"]),
    )
    return snapshot, claim


@pytest.mark.parametrize("recovery", [False, True])
def test_job_retirement_stream_factory_binds_exact_journal_and_nested_owner(recovery):
    from kvk.dal.source_output_pool_dal import pending_retirements
    from services.export_runtime_composition import NewSourceJobStreams

    snapshot, claim = owned_new_source_snapshot(recovery=recovery)
    original = deepcopy(snapshot)
    token = pending_retirements(snapshot)[0]
    coordinator = Mock(execution_evidence=True, output_operations=True)
    coordinator.operator_snapshot.return_value = snapshot
    client = Mock()
    streams = NewSourceJobStreams(coordinator=coordinator, client=client)
    streams.retirement(claim, token, token["slots"][0])
    scope = client.stream.call_args.args[0]
    assert scope["ObjectID"] == claim.job_id and scope["ClaimVersion"] == claim.version
    assert scope["SnapshotHash"] == digest(snapshot).hex()
    assert (scope["NestedToken"] is not None) == recovery
    assert snapshot == original
    client.reset_mock()
    member = dict(token["slots"][0], version=999)
    with pytest.raises(SourceConflict, match="durable journal"):
        streams.retirement(claim, token, member)
    client.stream.assert_not_called()
    if recovery:
        with pytest.raises(SourceConflict, match="cannot replay delivery"):
            streams.delivery(claim)
        client.stream.assert_not_called()
    else:
        with pytest.raises(SourceConflict, match="never replay"):
            streams.delivery(claim)
        snapshot["attempts"] = []
        streams.delivery(claim)
        assert client.stream.call_args.args[0]["SnapshotHash"] == digest(snapshot).hex()


@pytest.mark.parametrize(
    "damage",
    [
        lambda s: s["job"].update(Version=10),
        lambda s: s["job"].update(OwnerID=str(uuid4())),
        lambda s: s["job"].update(State="uncertain"),
        lambda s: s["job"].update(DestinationSetHash="f" * 64),
        lambda s: s["pool"]["pool"].update(RegistrationHash="f" * 64),
        lambda s: s["pool"]["pool"].update(Epoch=2),
        lambda s: s["pool"]["pool"].update(ActiveKVK=44),
        lambda s: s["pool"].update(registration_count=9),
        lambda s: s["resources"].pop(),
        lambda s: s["resources"][0].update(Version=8),
        lambda s: s["resources"][0].update(BlockedReason="uncertain"),
        lambda s: s["resources"][0].update(ActivePreparationID=str(uuid4())),
        lambda s: s["job"].update(ProvenanceJson='{"retirement_recovery":{"state":"complete"}}'),
    ],
)
def test_job_stream_scope_rejects_stale_registration_and_owner_before_ipc(damage):
    from services.export_runtime_composition import NewSourceJobStreams

    snapshot, claim = owned_new_source_snapshot()
    damage(snapshot)
    coordinator = Mock(execution_evidence=True, output_operations=True)
    coordinator.operator_snapshot.return_value = snapshot
    client = Mock()
    with pytest.raises(SourceConflict):
        NewSourceJobStreams(coordinator=coordinator, client=client).delivery(claim)
    client.stream.assert_not_called()


@pytest.mark.parametrize("state", ["running", "uncertain", "confirmed"])
def test_job_probe_keeps_original_owner_and_exact_free_or_retained_resources(state):
    from services.export_runtime_composition import NewSourceJobStreams

    snapshot, claim = owned_new_source_snapshot()
    snapshot["job"].update(State=state, IntentID=str(uuid4()))
    if state == "confirmed":
        for resource in snapshot["resources"]:
            resource.update(ActiveJobID=None, OwnerID=None)
    elif state == "uncertain":
        for resource in snapshot["resources"]:
            resource["BlockedReason"] = "Retained uncertainty"
    coordinator = Mock(execution_evidence=True, output_operations=True)
    coordinator.operator_snapshot.return_value = snapshot
    client = Mock()
    NewSourceJobStreams(coordinator=coordinator, client=client).probe(snapshot)
    scope = client.stream.call_args.args[0]
    assert scope["Purpose"] == "probe" and scope["OwnerID"] == claim.owner_id
    assert (
        scope["ClaimVersion"] == claim.version and scope["SnapshotHash"] == digest(snapshot).hex()
    )
    assert scope["NestedToken"] is None


@pytest.mark.parametrize("recovery_state", ["owned", "complete"])
@pytest.mark.parametrize("version_gap", [0, 1, 2])
def test_job_probe_binds_exact_interrupted_or_completed_nested_journal(recovery_state, version_gap):
    from services.export_runtime_composition import NewSourceJobStreams

    snapshot, _claim = owned_new_source_snapshot(recovery=True)
    snapshot["job"].update(State="uncertain", Version=9 + version_gap, IntentID=str(uuid4()))
    provenance = json.loads(snapshot["job"]["ProvenanceJson"])
    provenance["retirement_recovery"]["state"] = recovery_state
    snapshot["job"]["ProvenanceJson"] = json.dumps(provenance)
    coordinator = Mock(execution_evidence=True, output_operations=True)
    coordinator.operator_snapshot.return_value = snapshot
    client = Mock()
    service = NewSourceJobStreams(coordinator=coordinator, client=client)
    allowed = (version_gap in (0, 1)) if recovery_state == "owned" else version_gap > 0
    if not allowed:
        with pytest.raises(SourceConflict, match="nested owner version"):
            service.probe(snapshot)
        client.stream.assert_not_called()
    else:
        service.probe(snapshot)
        scope = client.stream.call_args.args[0]
        assert scope["ClaimVersion"] == 9 + version_gap
        assert scope["NestedToken"] == (
            provenance["retirement_recovery"]["token"] if recovery_state == "owned" else None
        )


def test_probe_never_adopts_another_owner_or_stale_snapshot():
    from services.export_runtime_composition import NewSourceJobStreams

    snapshot, _claim = owned_new_source_snapshot()
    snapshot["job"]["IntentID"] = str(uuid4())
    coordinator = Mock(execution_evidence=True, output_operations=True)
    coordinator.operator_snapshot.return_value = {}
    client = Mock()
    service = NewSourceJobStreams(coordinator=coordinator, client=client)
    with pytest.raises(SourceConflict, match="snapshot changed"):
        service.probe(snapshot)
    coordinator.operator_snapshot.return_value = snapshot
    snapshot["resources"][0]["OwnerID"] = str(uuid4())
    with pytest.raises(SourceConflict, match="owner/fence/version"):
        service.probe(snapshot)
    client.stream.assert_not_called()


def test_interrupted_nested_owner_probe_does_not_revive_mutation_admission():
    from services.export_runtime_composition import new_source_job_scope

    snapshot, claim = owned_new_source_snapshot(recovery=True)
    snapshot["job"]["Version"] += 1
    claim.version += 1
    with pytest.raises(SourceConflict, match="nested owner version"):
        new_source_job_scope(snapshot, claim)


def recorded_google_memory():
    """Actual static SDK requests cross the typed boundary into an offline API fake."""
    from services.export_execution_protocol import ProviderRequest, validate_response
    from tests.test_kvk_source_delivery import google_delivery

    args, _, api = google_delivery()
    original = args["transport"]
    messages = []

    def execute(message):
        request = ProviderRequest.parse(message)
        messages.append(request)
        operation = request.operation
        arguments = request.arguments
        if operation.startswith("drive."):
            _, resource, method = operation.split(".")
            arguments["fileId"] = request.target
            result = api.execute("/" + resource, method, arguments, 0)
        else:
            arguments["spreadsheetId"] = request.target
            method = operation.split(".")[-1]
            path = (
                "/spreadsheets/values"
                if operation.startswith("sheets.values.")
                else "/spreadsheets"
            )
            result = api.execute(path, method, arguments, 0)
            if operation == "sheets.values.get":
                result["range"] = arguments["range"]
            else:
                result["spreadsheetId"] = request.target
            if operation == "sheets.batchUpdate":
                result["replies"] = [
                    (
                        {
                            "deleteDeveloperMetadata": {
                                "deletedDeveloperMetadata": [
                                    {
                                        "metadataId": item["deleteDeveloperMetadata"]["dataFilter"][
                                            "developerMetadataLookup"
                                        ]["metadataId"]
                                    }
                                ]
                            }
                        }
                        if "deleteDeveloperMetadata" in item
                        else {}
                    )
                    for item in arguments["body"]["requests"]
                ]
            if operation == "sheets.values.update":
                values = arguments["body"]["values"]
                result.update(
                    updatedRange=arguments["range"],
                    updatedRows=len(values),
                    updatedColumns=max(map(len, values), default=0),
                    updatedCells=sum(map(len, values)),
                )
        validate_response(request, result)
        return result

    from services.export_runtime_composition import AuthorityStream

    client = Mock(execute=Mock(side_effect=execute))
    stream = AuthorityStream(client, {})
    args["authority_stream"] = stream
    args["transport"] = GoogleSheetsTransport.from_authority(
        registration=original.registration,
        reuse_guard=original.reuse_guard,
        protected_file_ids=original.protected,
        execution=stream.execute,
        stream_id=stream.stream_id,
        authorize=lambda **_: None,
    )
    return args, api, messages


@pytest.mark.parametrize("failure", [None, "close", "transport"])
def test_actual_new_source_worker_readback_crosses_typed_batch_read_boundary(monkeypatch, failure):
    from threading import Event

    args, api, messages = recorded_google_memory()
    generation = args["generation"]
    monkeypatch.setattr(
        "kvk.services.new_source_export_service.load_intent_generation", lambda **_: generation
    )
    dal = Mock(execution_evidence=True, output_operations=False)
    dal.begin_attempt.return_value = "attempt-a"
    claim = SimpleNamespace(fence=10)
    job = dict(
        ConsumerKind="new_source",
        IntentID="intent-a",
        InputHash=b"a" * 32,
        DestinationSetHash=digest(tuple(sorted(("fake-index", "fake-1", "fake-2")))),
    )
    stream = args["authority_stream"]

    def close(stream_id):
        assert stream_id == stream.stream_id
        dal.confirm.assert_not_called()
        if failure == "close":
            raise SourceConflict("close acknowledgment lost")
        return dict(stream_id=stream_id, version=3)

    stream.client.close_stream.side_effect = close
    if failure == "transport":
        args["transport"]._authority_adapter.execution = Mock()
    kwargs = dict(
        job=job,
        claim=claim,
        dal=dal,
        transport=args["transport"],
        connect=None,
        budget=Mock(side_effect=AssertionError("local budget escaped")),
        stop=Event(),
        authority_stream=args["authority_stream"],
    )
    if failure:
        with pytest.raises(SourceConflict):
            deliver_coordinated_export(**kwargs)
        dal.confirm.assert_not_called()
        if failure == "transport":
            assert messages == []
        return
    result = deliver_coordinated_export(**kwargs)
    assert result["files"] == ["fake-index", "fake-1"]
    assert any(r.operation == "sheets.values.batchGet" for r in messages)
    assert len({r.request_id for r in messages}) == len(messages)
    dal.confirm.assert_called_once_with(claim, "attempt-a", result)
    assert api.values["fake-index", "Sheet1"][0][0] == generation.key
    assert args["authority_stream"]._closed
    args["authority_stream"].client.close_stream.assert_called_once()


def retirement_stream_fixture(claim, pool, *, recovery=False, fail=None):
    """Real client-stream lifecycle with fake provider operations and durable calls."""
    from services.export_runtime_composition import AuthorityStream

    trace, streams = [], []

    def stream_factory(current, retirement, member):
        assert current is claim
        file_id = member["file_id"]
        scope = dict(
            OwnerKind="job",
            ObjectID=claim.job_id,
            AccountKey=claim.account,
            OwnerID=claim.owner_id,
            Fence=claim.fence,
            ClaimVersion=claim.version,
            RegistrationHash=pool["RegistrationHash"],
            Epoch=pool["Epoch"],
            Purpose="mutation",
            NestedToken=str(uuid4()) if recovery else None,
            ScopeJson={"resources": [{"key": k, "version": v} for k, v in sorted(claim.resources)]},
        )

        def close(stream_id):
            trace.append((file_id, "close"))
            if fail == "close":
                raise SourceConflict("closure unknown")
            return dict(stream_id=stream_id, version=3)

        client = Mock()
        client.open_stream.side_effect = lambda *_: trace.append((file_id, "open"))
        client.close_stream.side_effect = close
        stream = AuthorityStream(client, scope)
        stream.file_id = file_id
        streams.append(stream)
        return stream

    def transport_factory(snapshot, stream):
        context = snapshot["pool"] if "pool" in snapshot["pool"] else snapshot
        transport = object.__new__(GoogleSheetsTransport)
        transport.registration = SimpleNamespace(
            index_file_id=pool["IndexFileID"],
            slot_file_ids=tuple(s["FileID"] for s in context["slots"]),
        )
        transport._authority_adapter = SimpleNamespace(
            execution=stream.execute,
            stream_id=stream.stream_id,
        )
        if fail == "transport":
            transport._authority_adapter.stream_id = str(uuid4())

        def operation(phase, file_id):
            assert file_id == stream.file_id
            assert stream._entered and not stream._closed
            trace.append((file_id, phase))
            if phase == fail:
                raise SourceConflict("provider unknown")
            return dict(file_id=file_id, private=True, empty=True, manifest_hash="exact")

        transport.rollover_private = lambda file_id: operation("private", file_id)
        transport.rollover_clear = lambda file_id: operation("clear", file_id)
        transport.retirement_readback = lambda file_id: operation("read", file_id) and None
        return transport

    return stream_factory, transport_factory, trace, streams


@pytest.mark.parametrize("failure", [None, "private", "clear", "close", "commit", "transport"])
def test_retirement_closes_each_exact_writer_before_audited_reuse(failure):
    from kvk.services.source_output_pool_service import retire_superseded_generations
    from tests.test_kvk_output_rollover import retirement_snapshot_fixture

    snapshot = retirement_snapshot_fixture()
    snapshot["pool"].update(RegistrationHash="a" * 64, IndexFileID="index")
    claim = SimpleNamespace(
        job_id=str(uuid4()),
        owner_id=str(uuid4()),
        account="acct",
        fence=5,
        version=8,
        resources=(("account:acct", 6),),
    )
    stream_factory, transport_factory, trace, streams = retirement_stream_fixture(
        claim,
        snapshot["pool"],
        fail=failure,
    )
    pools = Mock(execution_evidence=True)
    pools.retirement_snapshot.side_effect = [snapshot, dict(snapshot, slots=[])]
    pools.retire_generation.return_value = dict(slots=[dict(file_id="a"), dict(file_id="b")])

    def commit(_coordinator, _claim, _retirement, member, _evidence):
        assert streams[-1].closure is not None
        trace.append((member["file_id"], "commit"))
        if failure == "commit":
            raise SourceConflict("commit unknown")

    pools.clear_retired_slot.side_effect = commit
    kwargs = dict(
        pools=pools,
        coordinator=Mock(execution_evidence=True),
        claim=claim,
        current_attempt_id="new",
        transport=Mock(),
        verifier=Mock(),
        stream_factory=stream_factory,
        transport_factory=transport_factory,
    )
    if failure:
        with pytest.raises(SourceConflict):
            retire_superseded_generations(**kwargs)
        assert len(streams) == 1
        assert pools.clear_retired_slot.call_count == (failure == "commit")
    else:
        retire_superseded_generations(**kwargs)
        assert trace == [
            (f, phase)
            for f in ("a", "b")
            for phase in ("open", "private", "clear", "close", "commit")
        ]
        assert len({s.stream_id for s in streams}) == 2
    assert all(s._closed for s in streams)


@pytest.mark.parametrize("failure", [None, "clear", "close", "commit", "transport"])
def test_nested_recovery_closes_before_slot_reuse_and_owner_revocation(failure):
    from kvk.services.source_output_pool_service import RetirementRecovery
    from tests.test_kvk_output_rollover import interrupted_retirement_fixture

    snapshot, proof = interrupted_retirement_fixture()
    claim = SimpleNamespace(
        job_id="job",
        owner_id="owner",
        account="acct",
        fence=5,
        version=9,
        resources=(("account:acct", 7),),
    )
    stream_factory, transport_factory, trace, streams = retirement_stream_fixture(
        claim,
        snapshot["pool"]["pool"],
        recovery=True,
        fail=failure,
    )
    pools = Mock(execution_evidence=True)
    pools.claim_retirement_recovery.return_value = claim

    def commit(*_args, **_kwargs):
        assert streams[-1].closure is not None
        trace.append(("fake-1", "commit"))
        if failure == "commit":
            raise SourceConflict("commit unknown")

    pools.clear_retired_slot.side_effect = commit
    pools.finish_retirement_recovery.side_effect = lambda *_: trace.append(("fake-1", "revoke"))
    recovery = RetirementRecovery(
        pools=pools,
        coordinator=Mock(),
        transport_factory=transport_factory,
        stream_factory=stream_factory,
        budget_factory=Mock(),
    )
    if failure:
        with pytest.raises(SourceConflict):
            recovery.resume(snapshot, proof, actor="admin")
        pools.interrupt_retirement_recovery.assert_called_once()
        pools.finish_retirement_recovery.assert_not_called()
        assert pools.clear_retired_slot.call_count == (failure == "commit")
    else:
        recovery.resume(snapshot, proof, actor="admin")
        assert trace == [
            ("fake-1", phase) for phase in ("open", "read", "clear", "close", "commit", "revoke")
        ]
        pools.interrupt_retirement_recovery.assert_not_called()


def test_s11_recovery_without_owned_stream_factory_does_not_claim():
    from kvk.services.source_output_pool_service import RetirementRecovery

    pools = Mock(execution_evidence=True)
    recovery = RetirementRecovery(
        pools=pools, coordinator=Mock(), transport_factory=Mock(), budget_factory=Mock()
    )
    with pytest.raises(SourceConflict, match="independent clear streams"):
        recovery.resume({}, {}, actor="admin")
    pools.claim_retirement_recovery.assert_not_called()


@pytest.mark.parametrize("action", ["clear", "complete"])
def test_active_stream_blocks_reuse_and_recovery_completion_inside_owner_transaction(
    monkeypatch, action
):
    from contextlib import contextmanager

    from kvk.dal.source_output_pool_dal import SourceOutputPoolDAL
    from services.export_execution_dal import ExportExecutionDAL

    pools = SourceOutputPoolDAL(Mock(), execution_evidence=True)
    coordinator = Mock(execution_evidence=True)
    cursor, claim = Mock(), SimpleNamespace(account="acct")
    entered = []

    @contextmanager
    def owned(*_args):
        entered.append(True)
        yield cursor, {}, {}

    def gate(actual_cursor, account):
        assert entered and actual_cursor is cursor and account == "acct"
        cursor.execute.assert_not_called()
        raise SourceConflict("active writer")

    monkeypatch.setattr(pools, "_retirement_owned", owned)
    monkeypatch.setattr(pools, "_recovery_owned", owned)
    monkeypatch.setattr(ExportExecutionDAL, "assert_no_active_stream", gate)
    with pytest.raises(SourceConflict, match="active writer"):
        if action == "complete":
            pools.finish_retirement_recovery(coordinator, claim, "attempt")
        else:
            pools.clear_retired_slot(
                coordinator,
                claim,
                {"current_attempt_id": "attempt"},
                {"file_id": "file"},
                dict(file_id="file", private=True, empty=True, manifest_hash="hash"),
            )
    cursor.execute.assert_not_called()


def test_actual_rollover_clear_crosses_typed_metadata_and_empty_property_boundary():
    args, api, messages = recorded_google_memory()
    transport = args["transport"]
    transport._request_guard = lambda _: None
    api.named_ranges["fake-1"] = [{"namedRangeId": "retained-name"}]
    api.metadata["fake-1"] = [{"metadataId": 17}]
    api.files_data["fake-1"]["description"] = "retained old description"
    # Empty appProperties is real when only a description needs clearing.
    assert api.files_data["fake-1"]["appProperties"] == {}
    with args["authority_stream"]:
        evidence = transport.rollover_clear("fake-1")
    assert evidence["private"] and evidence["empty"]
    assert not api.named_ranges["fake-1"] and not api.metadata["fake-1"]
    operations = [
        item
        for r in messages
        if r.operation == "sheets.batchUpdate"
        for item in r.arguments["body"]["requests"]
    ]
    assert any("deleteNamedRange" in item for item in operations)
    assert any("deleteDeveloperMetadata" in item for item in operations)
    assert api.files_data["fake-1"]["description"] == ""


def test_authority_transport_uses_static_clients_without_credentials_or_local_pacing():
    execute = Mock(return_value={"spreadsheetId": "index-id", "sheets": []})
    sheets, authorize = transport(execute)
    pacer = Mock(side_effect=AssertionError("local pacing escaped"))
    sheets._request_pacer = pacer
    guard = Mock()
    sheets._request_guard = guard
    request = sheets.sheets.spreadsheets().get(spreadsheetId="index-id", fields="sheets.properties")
    assert sheets._execute(request)["spreadsheetId"] == "index-id"
    sent = execute.call_args.args[0]
    assert sent["operation"] == "sheets.get" and sent["target"] == "index-id"
    assert sent["arguments"] == {"fields": "sheets.properties"}
    guard.assert_called_once_with(request)
    authorize.assert_called_once_with(mutation=False)
    pacer.assert_not_called()


def test_authority_transport_retains_ambiguous_mutation_and_refuses_another_send():
    execute = Mock(side_effect=TimeoutError("reply lost"))
    sheets, authorize = transport(execute)
    request = sheets.drive.files().update(
        fileId="slot-aaa", body={"appProperties": {"k98Generation": "abc"}}, fields="id"
    )
    for _ in range(2):
        with pytest.raises(RemoteOutcomeUnknown):
            sheets._mutate(request)
    execute.assert_called_once()


def test_authority_reconciliation_needs_pinned_sql_manifest():
    sheets, authorize = transport(Mock())
    key = "a" * 64
    claim = SimpleNamespace(receipt=json.dumps({"export_key": key}), fence=4)
    file = dict(id="slot-aaa", description=json.dumps({"table": "remote-self-consistent"}))
    sheets._file = Mock(return_value=file)
    sheets._index = Mock(return_value=dict(id="index-id"))
    sheets._pointer = Mock(return_value=[[key, "4", "registered-url"]])
    sheets.verify = Mock(return_value={"table": "remote-self-consistent"})
    assert sheets.reconcile(object(), claim, pinned_manifest={"table": "pinned"}) == (
        "unknown",
        None,
    )
    assert sheets.reconcile(object(), claim) == ("unknown", None)
    sheets.verify.assert_not_called()


def test_s11_new_source_refuses_unrecorded_transport_before_claim_or_provider():
    transport = object.__new__(GoogleSheetsTransport)
    transport._authority_adapter = None
    dal = Mock(execution_evidence=True)
    with pytest.raises(RemoteOutcomeUnknown, match="recorded authority stream"):
        deliver_coordinated_export(
            job={"ConsumerKind": "new_source"},
            claim=object(),
            dal=dal,
            transport=transport,
            connect=Mock(),
            budget=Mock(),
            stop=Mock(),
        )
    dal.authorize.assert_not_called()


def test_s11_configuration_refuses_unscoped_read_before_preparation_request():
    from services.legacy_export_snapshot_service import LegacyExportRuntime, SnapshotUnavailable

    dal = Mock(execution_evidence=True)
    coordinator = Mock(preparations=True, execution_evidence=True)
    runtime = LegacyExportRuntime(
        dal=dal,
        coordinator=coordinator,
        store=Mock(),
        account="account-a",
        configuration={},
    )
    with pytest.raises(SnapshotUnavailable, match="authority probe"):
        with runtime.configuration_requests():
            pass
    dal.request.assert_not_called()


def test_configuration_binds_real_authority_stream_and_closes_before_release():
    from services.export_provider_adapter import current_provider
    from services.export_runtime_composition import AuthorityStream
    from services.legacy_export_snapshot_service import LegacyExportRuntime

    trace = []
    client = Mock()
    client.close_stream.side_effect = lambda _: trace.append("closed")
    stream = AuthorityStream(client, {})
    dal = Mock(execution_evidence=True)
    dal.transition.side_effect = lambda *_args, **_kw: trace.append("released")
    runtime = LegacyExportRuntime(
        dal=dal,
        coordinator=Mock(preparations=True, execution_evidence=True),
        store=Mock(),
        account="account-a",
        configuration={"config": {"destinations": ["file-aaa"]}},
        authority_stream=lambda *_args: stream,
    )
    with runtime.configuration_requests():
        adapter = current_provider()
        assert adapter.execution.__self__ is stream and adapter.stream_id == stream.stream_id
        trace.append("configured")
    assert trace == ["configured", "closed", "released"]


def test_bot_pipe_client_opens_executes_and_closes_exact_one_stream(monkeypatch):
    from scripts.run_export_authority import AuthorityBroker
    from services.export_execution_authority import ExecutionUncertain
    from services.export_runtime_composition import AuthorityClient, RuntimeRegistration

    opened = []
    authority = SimpleNamespace(
        open_stream=Mock(side_effect=lambda **kw: opened.append(kw) or kw["stream_id"]),
        execute=Mock(return_value={"id": "file-aaa"}),
        close_stream=Mock(side_effect=lambda stream_id: {"stream_id": stream_id, "version": 4}),
    )
    registered = registration_fixture()
    registered["pools"][0]["index_file_id"] = "file-aaa"
    broker = AuthorityBroker(authority, RuntimeRegistration(registered))
    handles = []

    class Handle:
        closed = False

        def Close(self):
            self.closed = True

    class Pipe:
        def __init__(self, handle):
            self.handle = handle

        def send(self, message):
            self.message = message

        def receive(self):
            return {"version": 1, "result": broker.dispatch(self.message)}

    monkeypatch.setattr("core.export_execution_host.MessagePipe", Pipe)

    def new_handle():
        handle = Handle()
        handles.append(handle)
        return handle

    client = AuthorityClient(
        pipe_id=str(uuid4()),
        authority_sid="S-1-5-21-1",
        bot_sid="S-1-5-21-2",
        pipe_factory=new_handle,
        verify_server=lambda _: Handle(),
    )
    scope = dict(
        AccountKey="account-a",
        OwnerKind="job",
        ObjectID=str(uuid4()),
        OwnerID=str(uuid4()),
        Fence=1,
        ClaimVersion=1,
        NestedToken=None,
        RegistrationHash=registered["pools"][0]["registration_sha256"],
        Epoch=1,
        SnapshotHash="b" * 64,
        ScopeJson={
            "resources": [
                {"key": "account:account-a", "version": 1},
                {"key": "destination:file-aaa", "version": 1},
                {"key": "destination:slot-0-0", "version": 1},
                {"key": "destination:slot-0-1", "version": 1},
            ]
        },
        Purpose="probe",
    )
    stream = client.stream(scope)
    with stream:
        request = dict(
            version=1,
            request_id=str(uuid4()),
            stream_id=stream.stream_id,
            operation="drive.files.get",
            target="file-aaa",
            arguments={"fields": "id"},
        )
        assert stream.execute(request) == {"id": "file-aaa"}
        with pytest.raises(ExecutionUncertain):
            stream.execute(request | {"stream_id": str(uuid4())})
    assert len(opened) == 1 and authority.execute.call_count == 1
    authority.close_stream.assert_called_once_with(stream.stream_id)
    assert len(handles) == 3 and all(handle.closed for handle in handles)
    with pytest.raises(ExecutionUncertain):
        with stream:
            pass


def installation_fixture(*, profile="authority"):
    from services.export_execution_dal import (
        INSTALLATION_METADATA,
        INSTALLATION_MIGRATIONS,
        INSTALLATION_OBJECTS,
        installation_permissions,
    )

    metadata = {key: [] for key in INSTALLATION_METADATA}
    for name, kind in sorted(INSTALLATION_OBJECTS.items()):
        metadata["objects"].append(
            dict(
                ObjectName=name,
                ObjectType=kind,
                ExecuteAsPrincipal=None,
                ModuleDefinition="CREATE PROCEDURE fixture AS SELECT 1;" if kind == "P" else None,
                AnsiNulls=1 if kind == "P" else None,
                QuotedIdentifier=1 if kind == "P" else None,
                MemoryOptimized=0 if kind == "U" else None,
                TemporalType=0 if kind == "U" else None,
            )
        )
        if kind == "U":
            metadata["columns"].append(dict(ObjectName=name, ColumnName="fixture_id", Ordinal=1))
    metadata["indexes"] = [
        dict(ObjectName="dbo.ExportResource", Disabled=0, Hypothetical=0, FilterDefinition=None)
    ]
    metadata["checks"] = [
        dict(ObjectName="dbo.ExportResource", Disabled=0, Untrusted=0, Definition="fixture")
    ]
    metadata["foreign_keys"] = [
        dict(ObjectName="dbo.ExportResource", Disabled=0, Untrusted=0, ReferencedColumn="fixture")
    ]
    target = dict(
        ServerName="fixture-server",
        DatabaseName="fixture-db",
        DatabaseCollation="Latin1_General_CI_AS",
        Principal="fixture-authority" if profile == "authority" else "fixture-reader",
        Sysadmin=0,
        DatabaseOwner=0,
        ViewDefinition=1,
        AuthorityRole=int(profile == "authority"),
        ReaderRole=int(profile == "reader"),
        ControlDatabase=0,
        AlterRole=0,
        AlterUser=0,
        ImpersonateUser=0,
    )
    approved = dict(
        version=2,
        server=target["ServerName"],
        database=target["DatabaseName"],
        collation=target["DatabaseCollation"],
        principal=target["Principal"],
        profile=profile,
        migration_hashes={key: digest(key).hex() for key in INSTALLATION_MIGRATIONS},
        metadata_hash=digest(metadata).hex(),
    )
    permissions = installation_permissions(profile)
    for column in metadata["columns"]:
        for permission in ("SELECT", "UPDATE"):
            permissions[(column["ObjectName"], column["ColumnName"], permission)] = permissions[
                (column["ObjectName"], None, permission)
            ]
    observed = dict(
        version=2,
        target=target,
        metadata=metadata,
        migrations=[
            dict(MigrationId=key, ChecksumSha256=value, Status="Applied")
            for key, value in approved["migration_hashes"].items()
        ],
        permissions=[
            dict(
                ObjectName=name,
                ColumnName=column,
                PermissionName=permission,
                Allowed=allowed,
            )
            for (name, column, permission), allowed in permissions.items()
        ],
    )
    return observed, approved


def legacy_permission_fixture(monkeypatch):
    """Synthetic SQL metadata only. Replace the source pin solely in this fixture.

    The separate SQL source checker validates the real 38 definitions/signing
    closure; these tests exercise refusal behavior without an installed server.
    """
    import services.export_execution_dal as module

    definitions = {
        "dbo.UPDATE_ALL2": "CREATE PROCEDURE dbo.UPDATE_ALL2 AS SELECT 1;",
        "dbo.child": "CREATE PROCEDURE dbo.child AS SELECT 2;",
    }
    source = dict(
        database="ROK_TRACKER",
        roots=["dbo.UPDATE_ALL2"],
        modules=[
            dict(
                name=n,
                definition_sha256=module.legacy_definition_hash(d),
                object_type="P",
                execute_as=None,
            )
            for n, d in definitions.items()
        ],
        signatures=[
            dict(module="dbo.UPDATE_ALL2", certificate="S11LegacyImport", crypt_type="SPVC"),
            dict(module="dbo.child", certificate="S11LegacyImport", crypt_type="CPVC"),
        ],
        grants=[
            dict(
                database="ROK_TRACKER",
                principal="S11LegacyImportUser",
                securable_class="SCHEMA",
                target="dbo",
                permission="ALTER",
            )
        ],
    )
    monkeypatch.setattr(module, "LEGACY_PERMISSION_SOURCE_HASH", digest(source).hex())
    approved = dict(
        version=1,
        server="fixture-server",
        database="ROK_TRACKER",
        principal="fixture-bot",
        source=source,
        certificate_pins={"S11LegacyImport": dict(thumbprint="a" * 40, public_key_hash="b" * 64)},
        signature_hashes={
            "|".join((s["module"], s["certificate"], s["crypt_type"])): "c" * 64
            for s in source["signatures"]
        },
        migration_hash="d" * 64,
        metadata_hash="e" * 64,
    )
    queries = module.legacy_permission_queries(source)
    observed = {key: [] for key in queries} | {"version": 1}
    observed["target"] = [
        dict(
            ServerName="fixture-server",
            DatabaseName="ROK_TRACKER",
            Principal="fixture-bot",
            DefaultSchema="dbo",
            MajorVersion=16,
            Sysadmin=0,
            DatabaseOwner=0,
            ViewDefinition=1,
            EntryRole=1,
            ReaderRole=1,
            AuthorityRole=0,
        )
    ]
    observed["modules"] = [
        dict(
            ObjectName=n,
            ObjectType="P",
            ModuleDefinition=d,
            AnsiNulls=1,
            QuotedIdentifier=1,
            ExecuteAsPrincipal=None,
            OwnerName="dbo",
        )
        for n, d in definitions.items()
    ]
    observed["signatures"] = [
        dict(
            ObjectName=s["module"],
            CertificateName=s["certificate"],
            CryptType=s["crypt_type"],
            Thumbprint="a" * 40,
            SignatureHash="c" * 64,
            IsSigned=1,
            IsValid=1,
        )
        for s in source["signatures"]
    ]
    observed["certificates"] = [
        dict(
            DatabaseName=db,
            CertificateName="S11LegacyImport",
            OwnerName="dbo",
            PrivateKeyType="NA",
            Thumbprint="a" * 40,
            PublicKeyHash="b" * 64,
        )
        for db in ("ROK_TRACKER", "master")
    ]
    observed["master_certificates"] = [
        c for c in observed["certificates"] if c["DatabaseName"] == "master"
    ]
    observed["certificates"] = [
        c for c in observed["certificates"] if c["DatabaseName"] == "ROK_TRACKER"
    ]
    observed["grants"] = [
        dict(
            DatabaseName="ROK_TRACKER",
            PrincipalName="S11LegacyImportUser",
            SecurableClass="SCHEMA",
            TargetName="dbo",
            PermissionName="ALTER",
            GrantState="G",
            MinorID=0,
        )
    ]
    observed["principals"] = [
        dict(
            DatabaseName=db,
            PrincipalName=p,
            PrincipalType="C",
            PrincipalSID="ff" * 20,
            CertificateSID="ff" * 20,
            CertificateName="S11LegacyImport",
        )
        for db, p in (
            ("ROK_TRACKER", "S11LegacyImportUser"),
            ("master", "S11LegacyImportUser"),
            ("server", "S11LegacyImportLogin"),
        )
    ]
    observed["capabilities"] = [
        dict(
            SecurableClass=p["kind"],
            TargetName=p["target"],
            PermissionName=p["permission"],
            Allowed=0,
        )
        for p in json.loads(queries["capabilities"][1][0])
    ]
    observed["module_permissions"] = [
        dict(ObjectName=n, PermissionName=p, Allowed=int(n in source["roots"] and p == "EXECUTE"))
        for n in definitions
        for p in ("EXECUTE", "ALTER", "CONTROL", "TAKE OWNERSHIP")
    ]
    observed["ownership"] = [
        dict(OwnedSchemas=0, OwnedObjects=0, OwnedPrincipals=0, OwnedServerPrincipals=0)
    ]
    observed["migration"] = [
        dict(
            MigrationId=module.LEGACY_PERMISSION_MIGRATION,
            ChecksumSha256="d" * 64,
            Status="Applied",
        )
    ]
    approved["metadata_hash"] = digest(observed).hex()
    return observed, approved


def test_legacy_permission_contract_matches_without_mutation(monkeypatch):
    from services.export_runtime_composition import verify_legacy_installation_contract

    observed, approved = legacy_permission_fixture(monkeypatch)
    before = deepcopy((observed, approved))
    assert verify_legacy_installation_contract(observed, approved) == digest(observed).hex()
    assert (observed, approved) == before


@pytest.mark.parametrize(
    "section,field,value",
    [
        ("target", "DefaultSchema", "attacker"),
        ("target", "DatabaseName", "another-db"),
        ("target", "MajorVersion", 15),
        ("target", "Sysadmin", 1),
        ("target", "ViewDefinition", 0),
        ("target", "AuthorityRole", 1),
        ("target", "ReaderRole", 0),
        ("target", "EntryRole", True),
        ("modules", "ModuleDefinition", "ALTER PROCEDURE dbo.UPDATE_ALL2 AS SELECT 3;"),
        ("modules", "ExecuteAsPrincipal", -2),
        ("modules", "OwnerName", "attacker"),
        ("modules", "AnsiNulls", True),
        ("modules", "QuotedIdentifier", 0),
        ("signatures", "CryptType", "CPVC"),
        ("signatures", "SignatureHash", "f" * 64),
        ("signatures", "IsValid", 0),
        ("signatures", "IsSigned", True),
        ("certificates", "PrivateKeyType", "MK"),
        ("certificates", "PublicKeyHash", "f" * 64),
        ("certificates", "OwnerName", "attacker"),
        ("grants", "GrantState", "W"),
        ("grants", "MinorID", 1),
        ("grants", "PermissionName", "CONTROL"),
        ("principals", "PrincipalType", "S"),
        ("principals", "CertificateSID", "00"),
        ("capabilities", "Allowed", 1),
        ("capabilities", "Allowed", None),
        ("capabilities", "Allowed", False),
        ("module_permissions", "Allowed", 0),
        ("ownership", "OwnedObjects", 1),
        ("ownership", "OwnedPrincipals", 1),
        ("ownership", "OwnedServerPrincipals", 1),
        ("migration", "Status", "Failed"),
        ("migration", "ChecksumSha256", "f" * 64),
    ],
)
def test_legacy_permission_contract_rejects_semantic_drift_even_with_matching_fingerprint(
    monkeypatch, section, field, value
):
    from services.export_runtime_composition import verify_legacy_installation_contract

    observed, approved = legacy_permission_fixture(monkeypatch)
    observed[section][0][field] = value
    approved["metadata_hash"] = digest(observed).hex()
    with pytest.raises(SourceConflict):
        verify_legacy_installation_contract(observed, approved)


@pytest.mark.parametrize(
    "section",
    [
        "modules",
        "signatures",
        "certificates",
        "grants",
        "principals",
        "capabilities",
        "module_permissions",
        "ownership",
        "migration",
    ],
)
@pytest.mark.parametrize("mode", ["missing", "duplicate", "extra_field"])
def test_legacy_permission_contract_requires_exact_rows(monkeypatch, section, mode):
    from services.export_runtime_composition import verify_legacy_installation_contract

    observed, approved = legacy_permission_fixture(monkeypatch)
    if mode == "missing":
        observed[section].pop()
    elif mode == "duplicate":
        observed[section].append(deepcopy(observed[section][0]))
    else:
        observed[section][0]["ignored"] = "no"
    approved["metadata_hash"] = digest(observed).hex()
    with pytest.raises(SourceConflict):
        verify_legacy_installation_contract(observed, approved)


@pytest.mark.parametrize("section", ["memberships", "token_grants"])
def test_legacy_permission_contract_rejects_inherited_escalation(monkeypatch, section):
    from services.export_runtime_composition import verify_legacy_installation_contract

    observed, approved = legacy_permission_fixture(monkeypatch)
    observed[section].append(dict(PrincipalName="fixture-bot", PermissionName="CONTROL"))
    approved["metadata_hash"] = digest(observed).hex()
    with pytest.raises(SourceConflict):
        verify_legacy_installation_contract(observed, approved)


def test_legacy_source_pin_cannot_be_replaced_by_observed_hash(monkeypatch):
    from services.export_runtime_composition import verify_legacy_installation_contract

    observed, approved = legacy_permission_fixture(monkeypatch)
    approved["source"]["modules"][0]["definition_sha256"] = "f" * 64
    with pytest.raises(SourceConflict, match="source manifest"):
        verify_legacy_installation_contract(observed, approved)


def test_legacy_permission_fingerprint_and_server_pins_are_independent(monkeypatch):
    from services.export_runtime_composition import verify_legacy_installation_contract

    observed, approved = legacy_permission_fixture(monkeypatch)
    for change in (
        {"metadata_hash": "f" * 64},
        {"server": "other-server"},
        {"principal": "other-bot"},
    ):
        with pytest.raises(SourceConflict):
            verify_legacy_installation_contract(observed, approved | change)


def test_legacy_permission_collector_uses_this_cursor_without_writes_or_commit(monkeypatch):
    import services.export_execution_dal as module

    observed, approved = legacy_permission_fixture(monkeypatch)
    cursor = Mock()
    result_rows = iter(observed[k] for k in module.legacy_permission_queries(approved["source"]))
    monkeypatch.setattr(module, "rows", lambda c: next(result_rows))
    assert module.legacy_installation_snapshot(cursor, approved["source"]) == observed
    assert cursor.execute.call_count == len(module.legacy_permission_queries(approved["source"]))
    cursor.commit.assert_not_called()
    cursor.close.assert_not_called()
    assert not any(
        "GRANT " in call.args[0] or "EXEC dbo." in call.args[0]
        for call in cursor.execute.call_args_list
    )
    cursor.reset_mock()
    monkeypatch.setattr(
        module, "rows", lambda c: [observed["target"][0] | {"DefaultSchema": "other"}]
    )
    with pytest.raises(SourceConflict, match="resolution"):
        module.legacy_installation_snapshot(cursor, approved["source"])
    assert cursor.execute.call_count == 1


def test_legacy_definition_fingerprint_normalizes_only_ddl_introducer_and_outer_whitespace():
    from services.export_execution_dal import legacy_definition_hash

    base = "CREATE PROCEDURE dbo.p AS\nSELECT N'\U0001f642';"
    expected = legacy_definition_hash(base)
    assert (
        legacy_definition_hash(
            " \r\n" + base.replace("CREATE", "ALTER").replace("\n", "\r\n") + "\t\n"
        )
        == expected
    )
    assert legacy_definition_hash(base.replace("CREATE", "CREATE OR ALTER")) == expected
    assert legacy_definition_hash(base.replace("SELECT ", "SELECT  ")) != expected


@pytest.mark.parametrize("profile", ["authority", "reader"])
def test_installation_observation_matches_exact_protected_contract_only(profile):
    from services.export_runtime_composition import verify_installation_contract

    observed, approved = installation_fixture(profile=profile)
    original = deepcopy((observed, approved))
    result = verify_installation_contract(observed, approved)
    assert result == digest(observed).hex()
    assert (observed, approved) == original
    # This is a fingerprint, not a runtime bundle, ProofID or readiness flag.
    assert isinstance(result, str) and len(result) == 64


@pytest.mark.parametrize(
    "field,value",
    [
        ("ServerName", "other-server"),
        ("DatabaseName", "other-db"),
        ("DatabaseCollation", "different-collation"),
        ("Principal", "bot-principal"),
        ("Sysadmin", 1),
        ("DatabaseOwner", 1),
        ("ViewDefinition", 0),
        ("AuthorityRole", None),
        ("ReaderRole", 1),
        ("ControlDatabase", 1),
        ("AlterRole", 1),
        ("AlterUser", 1),
        ("ImpersonateUser", 1),
    ],
)
def test_installation_rejects_wrong_target_visibility_and_privileged_or_mixed_principal(
    field, value
):
    from services.export_runtime_composition import verify_installation_contract

    observed, approved = installation_fixture()
    observed["target"][field] = value
    with pytest.raises(SourceConflict, match="target"):
        verify_installation_contract(observed, approved)


@pytest.mark.parametrize("change", ["missing", "duplicate", "failed", "checksum", "history_only"])
def test_installation_stamps_cannot_hide_missing_or_changed_contract(change):
    from services.export_runtime_composition import verify_installation_contract

    observed, approved = installation_fixture()
    if change == "missing":
        observed["migrations"].pop()
    elif change == "duplicate":
        observed["migrations"][0] = observed["migrations"][1]
    elif change == "failed":
        observed["migrations"][0]["Status"] = "Failed"
    elif change == "checksum":
        observed["migrations"][0]["ChecksumSha256"] = "0" * 64
    else:
        observed["metadata"] = {}
    with pytest.raises(SourceConflict):
        verify_installation_contract(observed, approved)


@pytest.mark.parametrize(
    "section,field",
    [
        ("columns", "ColumnName"),
        ("indexes", "FilterDefinition"),
        ("checks", "Definition"),
        ("foreign_keys", "ReferencedColumn"),
    ],
)
def test_installation_definition_drift_rejects_unchanged_applied_migration_stamps(section, field):
    from services.export_runtime_composition import verify_installation_contract

    observed, approved = installation_fixture()
    observed["metadata"][section][0][field] = "different"
    with pytest.raises(SourceConflict, match="fingerprint"):
        verify_installation_contract(observed, approved)


@pytest.mark.parametrize(
    "change",
    [
        "missing_object",
        "wrong_type",
        "missing_columns",
        "disabled_check",
        "untrusted_fk",
        "disabled_index",
        "hypothetical_index",
        "encrypted_module",
        "execute_as",
        "opaque_trigger",
    ],
)
def test_installation_refuses_unsafe_shapes_even_if_manifest_hash_was_mistakenly_updated(change):
    from services.export_runtime_composition import verify_installation_contract

    observed, approved = installation_fixture()
    metadata = observed["metadata"]
    if change == "missing_object":
        metadata["objects"].pop()
    elif change == "wrong_type":
        metadata["objects"][0]["ObjectType"] = "V"
    elif change == "missing_columns":
        metadata["columns"].pop()
    elif change == "disabled_check":
        metadata["checks"][0]["Disabled"] = 1
    elif change == "untrusted_fk":
        metadata["foreign_keys"][0]["Untrusted"] = 1
    elif change in {"disabled_index", "hypothetical_index"}:
        metadata["indexes"][0]["Disabled" if change == "disabled_index" else "Hypothetical"] = 1
    elif change == "opaque_trigger":
        metadata["triggers"].append(dict(ModuleDefinition=None, ExecuteAsPrincipal=None))
    else:
        module = next(o for o in metadata["objects"] if o["ObjectType"] == "P")
        module["ModuleDefinition" if change == "encrypted_module" else "ExecuteAsPrincipal"] = (
            None if change == "encrypted_module" else -2
        )
    approved["metadata_hash"] = digest(metadata).hex()
    with pytest.raises(SourceConflict):
        verify_installation_contract(observed, approved)


@pytest.mark.parametrize("change", ["partial", "extra", "hash", "version"])
def test_installation_needs_complete_versioned_approved_contract(change):
    from services.export_runtime_composition import verify_installation_contract

    observed, approved = installation_fixture()
    if change == "partial":
        approved["migration_hashes"].pop(next(iter(approved["migration_hashes"])))
    elif change == "extra":
        approved["ready"] = True
    elif change == "hash":
        approved["metadata_hash"] = "not-an-approved-hash"
    else:
        approved["version"] = True
    with pytest.raises(SourceConflict, match="approved"):
        verify_installation_contract(observed, approved)


@pytest.mark.parametrize("profile", ["authority", "reader"])
@pytest.mark.parametrize(
    "change", ["direct_write", "alter", "control", "unknown", "missing", "duplicate", "execute"]
)
def test_installation_checks_effective_permissions_not_just_role_membership(profile, change):
    from services.export_runtime_composition import verify_installation_contract

    observed, approved = installation_fixture(profile=profile)
    permissions = observed["permissions"]
    if change == "missing":
        permissions.pop()
    elif change == "duplicate":
        permissions[0] = permissions[1]
    else:
        permission = {
            "direct_write": "INSERT",
            "alter": "ALTER",
            "control": "CONTROL",
            "unknown": "SELECT",
            "execute": "EXECUTE",
        }[change]
        row = next(p for p in permissions if p["PermissionName"] == permission)
        row["Allowed"] = None if change == "unknown" else 1 - row["Allowed"]
    with pytest.raises(SourceConflict, match="Effective export permissions"):
        verify_installation_contract(observed, approved)


@pytest.mark.parametrize(
    "name,permission,authority,reader",
    [
        ("dbo.ExportRequestBudget", "INSERT", 1, 1),
        ("dbo.ExportRequestBudget", "UPDATE", 1, 1),
        ("dbo.ExportPreparation", "SELECT", 1, 1),
        ("dbo.ExportPreparation", "INSERT", 0, 1),
        ("dbo.ExportPreparation", "UPDATE", 0, 1),
        ("dbo.ExportPreparationResource", "UPDATE", 0, 0),
        ("dbo.ExportJobResource", "INSERT", 0, 1),
        ("dbo.ExportJobResource", "UPDATE", 0, 0),
        ("KVK.SourceOutputFile", "INSERT", 0, 0),
        ("KVK.SourceOutputPool", "INSERT", 0, 0),
        ("KVK.SourceOutputPool", "UPDATE", 0, 1),
        ("KVK.SourceOutputSlot", "UPDATE", 0, 1),
        ("KVK.SourceOutputDisposition", "INSERT", 0, 1),
        ("KVK.SourceOutputDisposition", "UPDATE", 0, 0),
        ("KVK.SourceOutputOperationResource", "INSERT", 0, 1),
        ("KVK.SourceOutputOperationResource", "UPDATE", 0, 0),
        ("KVK.SeasonSource", "UPDATE", 0, 1),
        ("KVK.SourceRouting", "INSERT", 0, 1),
        ("KVK.SourceRouting", "UPDATE", 0, 0),
        ("KVK.SourcePublication", "INSERT", 0, 1),
        ("dbo.ExportReconciliationProof", "UPDATE", 0, 0),
        ("dbo.usp_ExportReconciliationProofIssue", "EXECUTE", 1, 0),
        ("dbo.usp_ExportOutputEnrollmentTransition", "EXECUTE", 1, 0),
        ("sys.sp_getapplock", "EXECUTE", 1, 1),
        ("sys.sp_releaseapplock", "EXECUTE", 1, 1),
    ],
)
def test_installation_profiles_preserve_existing_callers_and_forbid_other_writes(
    name, permission, authority, reader
):
    from services.export_execution_dal import installation_permissions

    for profile, expected in (("authority", authority), ("reader", reader)):
        permissions = installation_permissions(profile)
        assert permissions[(name, None, permission)] == expected
        assert all(
            allowed == 0
            for (_, _, action), allowed in permissions.items()
            if action in {"DELETE", "ALTER", "CONTROL", "TAKE OWNERSHIP"}
        )


@pytest.mark.parametrize("profile", ["authority", "reader"])
@pytest.mark.parametrize(
    "name,column,permission",
    [
        ("dbo.ExportRequestBudget", None, "INSERT"),
        ("dbo.ExportRequestBudget", "fixture_id", "UPDATE"),
        ("dbo.ExportPreparation", None, "SELECT"),
        ("dbo.ExportJob", "fixture_id", "SELECT"),
        ("KVK.SourceOutputPool", None, "UPDATE"),
        ("KVK.SourceOutputDisposition", "fixture_id", "UPDATE"),
        ("dbo.ExportReconciliationProof", "fixture_id", "UPDATE"),
        ("dbo.ExportManagedFileOrigin", "fixture_id", "UPDATE"),
        ("sys.sp_getapplock", None, "EXECUTE"),
        ("sys.sp_releaseapplock", None, "EXECUTE"),
    ],
)
def test_missing_or_extra_domain_and_column_capabilities_block_readiness(
    profile, name, column, permission
):
    from services.export_runtime_composition import verify_installation_contract

    observed, approved = installation_fixture(profile=profile)
    row = next(
        p
        for p in observed["permissions"]
        if (p["ObjectName"], p["ColumnName"], p["PermissionName"]) == (name, column, permission)
    )
    row["Allowed"] = 1 - row["Allowed"]
    with pytest.raises(SourceConflict, match="Effective export permissions"):
        verify_installation_contract(observed, approved)


@pytest.mark.parametrize(
    "change",
    [
        "missing_column",
        "duplicate_column",
        "unknown_column",
        "extra_field",
        "bool",
        "float",
        "null",
        "negative",
        "object_type",
        "column_type",
        "permission_type",
        "evidence_only",
    ],
)
def test_installation_requires_complete_typed_permission_rows(change):
    from services.export_execution_dal import EVIDENCE_TABLES
    from services.export_runtime_composition import verify_installation_contract

    observed, approved = installation_fixture()
    permissions = observed["permissions"]
    index = next(i for i, p in enumerate(permissions) if p["ColumnName"] is not None)
    row = permissions[index]
    if change == "missing_column":
        permissions.pop(index)
    elif change == "duplicate_column":
        permissions[index + 1] = dict(row)
    elif change == "unknown_column":
        row["ColumnName"] = "not_installed"
    elif change == "extra_field":
        row["Trusted"] = True
    elif change == "object_type":
        row["ObjectName"] = []
    elif change == "column_type":
        row["ColumnName"] = []
    elif change == "permission_type":
        row["PermissionName"] = []
    elif change == "evidence_only":
        observed["permissions"] = [p for p in permissions if p["ObjectName"] in EVIDENCE_TABLES]
    else:
        row["Allowed"] = {"bool": True, "float": 1.0, "null": None, "negative": -1}[change]
    with pytest.raises(SourceConflict, match="Effective export permissions"):
        verify_installation_contract(observed, approved)


@pytest.mark.parametrize("change", ["added", "duplicate_name", "duplicate_ordinal"])
def test_new_or_ambiguous_columns_cannot_escape_permission_observation(change):
    from services.export_runtime_composition import verify_installation_contract

    observed, approved = installation_fixture()
    column = dict(observed["metadata"]["columns"][0])
    if change != "duplicate_name":
        column["ColumnName"] = "AdditionalColumn"
    if change != "duplicate_ordinal":
        column["Ordinal"] = 2
    observed["metadata"]["columns"].append(column)
    approved["metadata_hash"] = digest(observed["metadata"]).hex()
    with pytest.raises(SourceConflict):
        verify_installation_contract(observed, approved)


@pytest.mark.parametrize("part", ["approved", "observed"])
def test_v1_evidence_only_installation_contract_cannot_enable_new_composition(part):
    from services.export_runtime_composition import verify_installation_contract

    observed, approved = installation_fixture()
    (approved if part == "approved" else observed)["version"] = 1
    with pytest.raises(SourceConflict):
        verify_installation_contract(observed, approved)


@pytest.mark.parametrize("failure", [None, "visibility", "metadata"])
def test_installation_reader_is_explicit_parameterized_and_closes_every_connection(
    monkeypatch, failure
):
    import services.export_execution_dal as module

    observed, _approved = installation_fixture()
    connection, cursor = Mock(), Mock()
    connection.cursor.return_value = cursor
    connect = Mock(return_value=connection)
    dal = module.ExportExecutionDAL(connect)
    connect.assert_not_called()
    if failure == "visibility":
        observed["target"]["ViewDefinition"] = None
    monkeypatch.setattr(module, "one", lambda _: deepcopy(observed["target"]))
    rowsets = iter(
        [
            observed["migrations"],
            *(observed["metadata"][k] for k in module._METADATA_QUERIES),
            observed["permissions"],
        ]
    )

    def fetch(_cursor):
        if failure == "metadata" and cursor.execute.call_count == 4:
            raise RuntimeError("metadata read failed")
        return deepcopy(next(rowsets))

    monkeypatch.setattr(module, "rows", fetch)
    if failure:
        with pytest.raises((SourceConflict, RuntimeError)):
            dal.installation_snapshot()
    else:
        assert dal.installation_snapshot() == observed
        assert cursor.execute.call_count == 9
    cursor.close.assert_called_once_with()
    connection.close.assert_called_once_with()
    connection.commit.assert_not_called()
    assert connection.autocommit is True
    for call in cursor.execute.call_args_list:
        query, *parameters = call.args
        assert query.startswith(("SELECT", "WITH required AS", "WITH permission_scope AS"))
        if parameters:
            assert len(parameters) == 1 and isinstance(json.loads(parameters[0]), list)
    if failure is None:
        query, scope = cursor.execute.call_args.args
        assert "c.name,'COLUMN'" in query
        assert "sys.columns" in query
        assert {row["object"] for row in json.loads(scope)} >= {
            "dbo.ExportRequestBudget",
            "dbo.ExportPreparation",
            "KVK.SourceOutputDisposition",
            "dbo.ExportReconciliationProof",
            "sys.sp_getapplock",
            "sys.sp_releaseapplock",
        }


def registration_fixture(*, pool_count=1, slot_count=2):
    from kvk.dal.new_source_import_dal import digest

    return dict(
        version=1,
        account="account-a",
        storage_owner="spool-a",
        service_account_email="editor@example.iam.gserviceaccount.com",
        legacy_configuration={
            kind: dict(
                consumer=kind,
                kvk_no=42 if kind == "all_kvk" else None,
                destinations=["legacy-" + kind],
            )
            for kind in ("all_kvk", "scan_data", "config")
        },
        protected_file_ids=sorted("legacy-" + k for k in ("all_kvk", "scan_data", "config")),
        pools=[
            dict(
                pool_id=str(uuid4()),
                registration_sha256=digest(dict(pool=i)).hex(),
                index_file_id=f"index-{i}",
                slot_file_ids=[f"slot-{i}-{n}" for n in range(slot_count)],
                owner_email="owner@example.com",
                audience="private",
            )
            for i in range(pool_count)
        ],
    )


def test_runtime_registration_is_copied_and_enforces_full_pool_snapshot():
    from services.export_runtime_composition import RuntimeRegistration

    supplied = registration_fixture(pool_count=8, slot_count=16)
    registration = RuntimeRegistration(supplied)
    pool = supplied["pools"][0]
    context = dict(
        pool=dict(
            PoolID=pool["pool_id"],
            AccountKey="account-a",
            SourceKey="snapshot_report_v1",
            RegistrationHash=pool["registration_sha256"],
            RegistrationJson='{"pool":0}',
            ExpectedOwner=pool["owner_email"],
            IndexFileID=pool["index_file_id"],
        ),
        slots=[dict(FileID=f) for f in pool["slot_file_ids"]],
        registration_count=8,
    )
    original = registration.fingerprint
    supplied["account"] = "changed"
    registration.value()["pools"][0]["slot_file_ids"].clear()
    assert registration.fingerprint == original
    result = registration.sheets(context)
    assert result.index_file_id == "index-0" and len(result.slot_file_ids) == 16
    for path, value in (
        ("PoolID", str(uuid4())),
        ("AccountKey", "other"),
        ("SourceKey", "other"),
        ("RegistrationHash", "a" * 64),
        ("RegistrationJson", '{"pool":1}'),
        ("ExpectedOwner", "other@example.com"),
        ("IndexFileID", "index-other"),
    ):
        with pytest.raises(SourceConflict):
            registration.sheets(context | {"pool": context["pool"] | {path: value}})
    with pytest.raises(SourceConflict):
        registration.sheets(context | {"registration_count": 7})
    with pytest.raises(SourceConflict):
        registration.sheets(context | {"slots": context["slots"][:-1]})


@pytest.mark.parametrize(
    "damage",
    [
        lambda v: v.update(version=True),
        lambda v: v.update(account=""),
        lambda v: v.update(storage_owner="../other"),
        lambda v: v.update(service_account_email="ordinary@example.com"),
        lambda v: v["legacy_configuration"].pop("config"),
        lambda v: v["legacy_configuration"]["all_kvk"].update(kvk_no=True),
        lambda v: v["legacy_configuration"]["scan_data"].update(kvk_no=42),
        lambda v: v["legacy_configuration"]["config"].update(destinations=["bad/id"]),
        lambda v: v.update(protected_file_ids=[]),
        lambda v: v["protected_file_ids"].append(v["protected_file_ids"][0]),
        lambda v: v["pools"][0].update(index_file_id="legacy-config"),
        lambda v: v["pools"][0].update(slot_file_ids=["index-0", "slot-other"]),
        lambda v: v["pools"][0].update(slot_file_ids=["slot-one"]),
        lambda v: v["pools"][0].update(slot_file_ids=[f"slot-{n}" for n in range(17)]),
        lambda v: v["pools"][0].update(audience="anyone"),
        lambda v: v["pools"].append(dict(v["pools"][0])),
        lambda v: v["pools"][0].update(registration_sha256="A" * 64),
        lambda v: v.update(pools=[]),
        lambda v: v.update(pools=[dict(v["pools"][0]) for _ in range(9)]),
    ],
)
def test_runtime_registration_rejects_incomplete_or_overlapping_inventory(damage):
    from services.export_runtime_composition import RuntimeRegistration

    value = registration_fixture()
    damage(value)
    with pytest.raises((ValueError, SourceConflict)):
        RuntimeRegistration(value)


@pytest.mark.parametrize("kind", ["all_kvk", "scan_data", "config"])
def test_protected_registration_authorizes_only_exact_legacy_scope(kind):
    from services.export_runtime_composition import RuntimeRegistration
    from services.legacy_export_snapshot_service import configuration_digest

    supplied = registration_fixture()
    registered = RuntimeRegistration(supplied)
    config = supplied["legacy_configuration"][kind]
    scope = dict(
        AccountKey="account-a",
        OwnerKind="preparation" if kind == "config" else "job",
        RegistrationHash=configuration_digest(config),
        Epoch=None,
        NestedToken=None,
        Purpose="probe" if kind == "config" else "mutation",
        ScopeJson={
            "resources": [
                {"key": "account:account-a", "version": 1},
                {"key": "destination:legacy-" + kind, "version": 3},
            ]
        },
    )
    registered.authorize_scope(scope)
    for change in (
        {"AccountKey": "other"},
        {"OwnerKind": "operation"},
        {"Epoch": 1},
        {"NestedToken": str(uuid4())},
        {"RegistrationHash": "a" * 64},
        {"Purpose": "mutation" if kind == "config" else "probe"},
        {
            "ScopeJson": {
                "resources": [
                    {"key": "account:account-a", "version": 1},
                    {"key": "destination:wrong-file", "version": 3},
                ]
            }
        },
    ):
        with pytest.raises(SourceConflict):
            registered.authorize_scope(scope | change)


def test_historical_application_dispositions_must_match_review_without_unrelated_repairs(
    monkeypatch,
):
    from services.export_runtime_composition import verify_application_installation_contract

    observed, approved = application_installation_fixture(monkeypatch)
    observed["metadata"]["checks"] = [dict(ObjectName="dbo.fixture", Disabled=1, Untrusted=1)]
    observed["metadata"]["triggers"] = [
        dict(ObjectName="dbo.fixture", Disabled=1, ModuleDefinition="reviewed definition")
    ]
    approved["metadata_hash"] = digest(observed["metadata"]).hex()
    verify_application_installation_contract(observed, approved)
    observed["metadata"]["checks"][0]["Disabled"] = 0
    with pytest.raises(SourceConflict):
        verify_application_installation_contract(observed, approved)


def test_closed_runtime_constructs_actual_factories_without_connecting(monkeypatch, tmp_path):
    from kvk.services.source_export_operator_service import configured_operator_service
    import services.export_coordination_service as coordinator_service
    import services.export_runtime_composition as composition
    from services.export_runtime_composition import (
        AuthorityClient,
        ExportRuntime,
        RuntimeRegistration,
    )
    from services.export_snapshot_store import ExportSnapshotStore

    _, legacy = legacy_permission_fixture(monkeypatch)
    _, application = application_installation_fixture(monkeypatch)
    connect = Mock(side_effect=AssertionError("construction attempted SQL"))
    client = AuthorityClient(
        pipe_id=str(uuid4()),
        authority_sid="S-1-5-21-1",
        bot_sid="S-1-5-21-2",
        deployment_hash="a" * 64,
    )
    bundle = ExportRuntime(
        connect=connect,
        registration=RuntimeRegistration(registration_fixture()),
        store=ExportSnapshotStore(tmp_path, "spool-a"),
        client=client,
        legacy_sql_contract=legacy,
        application_sql_contract=application,
    )
    monkeypatch.setattr(composition, "_installed", bundle)
    assert coordinator_service.configured_coordinator() is bundle
    assert configured_operator_service() is bundle.operator
    assert (
        bundle.dal.execution_evidence and bundle.dal.output_operations and bundle.dal.preparations
    )
    assert bundle.pools.execution_evidence and bundle.legacy.dal.execution_evidence
    assert bundle.legacy.dal.application_sql_contract == application
    assert bundle.coordinator.adapters["all_kvk"] is bundle.coordinator.adapters["scan_data"]
    assert bundle.coordinator.adapters["new_source"].__self__ is bundle
    connect.assert_not_called()
