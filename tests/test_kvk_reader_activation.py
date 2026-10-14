"""Activation scope, shared planning and durable recovery regressions."""

from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from kvk.models.new_source_reporting import CALCULATION_VERSION
from kvk.rendering.new_source_workbook import build_workbook_generation, partition_workbook
from kvk.services.source_output_pool_service import capacity
from kvk.services.source_reader_activation import physical_generation, reader_manifest
from services.export_runtime_composition import ExportRuntime, RuntimeRegistration
from tests.test_export_runtime_composition import registration_fixture
from tests.test_kvk_source_checkpoints import build, fixture


def activated():
    value = registration_fixture()
    value.update(
        version=2,
        reader_exports=[
            dict(
                pool_id=value["pools"][0]["pool_id"],
                kvk_no=16,
                guild_id="123",
                calculation_version=CALCULATION_VERSION,
            )
        ],
    )
    return value


@pytest.mark.parametrize(
    "field,value",
    [
        ("pool_id", str(uuid4())),
        ("kvk_no", True),
        ("guild_id", "１２３"),
        ("guild_id", ""),
        ("calculation_version", "snapshot_report_calculation_v2"),
    ],
)
def test_activation_rejects_unbound_scope(field, value):
    packet = activated()
    packet["reader_exports"][0][field] = value
    with pytest.raises(SourceConflict):
        RuntimeRegistration(packet)


def test_activation_versioned_optional_and_immutable():
    old = RuntimeRegistration(registration_fixture())
    assert "reader_exports" not in old.value()
    packet = activated()
    current = RuntimeRegistration(packet)
    packet["reader_exports"][0]["guild_id"] = "456"
    assert current.value()["reader_exports"][0]["guild_id"] == "123"
    packet["version"] = 1
    with pytest.raises(SourceConflict):
        RuntimeRegistration(packet)
    packet = activated()
    packet["reader_exports"] *= 2
    with pytest.raises(SourceConflict):
        RuntimeRegistration(packet)


@pytest.mark.parametrize(
    "season,versions,enabled",
    [
        (16, {CALCULATION_VERSION}, True),
        (17, {CALCULATION_VERSION}, False),
        (16, {"snapshot_report_calculation_v2"}, False),
        (16, {CALCULATION_VERSION, "snapshot_report_calculation_v2"}, False),
    ],
)
def test_activation_only_covers_exact_pinned_calculation_vector(
    monkeypatch, season, versions, enabled
):
    runtime = object.__new__(ExportRuntime)
    runtime.connect = Mock()
    runtime.registration = Mock()
    runtime.registration.value.return_value = activated()
    runtime.pools = Mock()
    runtime.pools.snapshot.return_value = {"pool": {"ActiveKVK": 16}}
    monkeypatch.setattr(
        "kvk.dal.source_reader_activation_dal.intent_scope", Mock(return_value=(season, versions))
    )
    assert (
        bool(
            runtime.reader_binding(
                "intent", b"a" * 32, pool_id=runtime.registration.value()["pools"][0]["pool_id"]
            )
        )
        is enabled
    )
    if enabled:
        runtime.registration.sheets.assert_called_once()
        runtime.pools.snapshot.return_value["pool"]["ActiveKVK"] = 17
        with pytest.raises(SourceConflict):
            runtime.reader_binding(
                "intent", b"a" * 32, pool_id=runtime.registration.value()["pools"][0]["pool_id"]
            )


def test_capacity_and_delivery_use_same_physical_reader_generation():
    generation = build_workbook_generation(build(fixture(names=("Pass 4",))))
    assert physical_generation(generation) is generation
    measured = capacity(
        generation.manifest(), quarantined_parts=0, protected_parts=0, slot_count=16
    )
    assert measured.current_parts == len(partition_workbook(generation.manifest()))
    mixed = deepcopy(generation.manifest())
    next(iter(mixed.values())).pop("version")
    with pytest.raises(SourceConflict):
        reader_manifest(mixed)


@pytest.mark.parametrize("was_reader", [False, True])
def test_generation_recovery_retains_attempt_binding_after_activation_change(
    monkeypatch, was_reader
):
    runtime = object.__new__(ExportRuntime)
    runtime.connect = Mock()
    runtime.registration = Mock()
    packet = activated()
    if was_reader:
        packet.pop("reader_exports")
    runtime.registration.value.return_value = packet
    runtime.pools = Mock()
    runtime.pools.snapshot.return_value = dict(
        jobs=[dict(JobID="job", IntentID="intent")],
        attempts=[dict(JobID="job", AttemptID="attempt")],
        parts=[],
    )
    generation = build_workbook_generation(build(fixture(names=("Pass 4",))))
    tables = generation.manifest() if was_reader else {"legacy": {}}
    monkeypatch.setattr(
        "services.export_coordination_dal.checked_attempt_manifest",
        Mock(return_value=dict(generation=dict(tables=tables, reader_guild_id="123"))),
    )
    monkeypatch.setattr(
        "kvk.dal.source_reader_activation_dal.intent_scope",
        Mock(return_value=(16, {CALCULATION_VERSION})),
    )
    binding = runtime.reader_binding(
        "intent", b"a" * 32, pool_id=runtime.registration.value()["pools"][0]["pool_id"]
    )
    assert bool(binding) is was_reader
    if was_reader:
        assert binding["guild_id"] == "123"
    runtime.registration.sheets.assert_not_called()


@pytest.mark.parametrize("was_reader,now_enabled", [(False, True), (True, False)])
def test_recovery_uses_attempt_layout_not_current_activation(monkeypatch, was_reader, now_enabled):
    from kvk.services.new_source_workbook_transport import ReaderSheetsTransport
    from tests.test_export_retirement_recovery_evidence import recovery_fixture

    args, _, _, _ = recovery_fixture(monkeypatch, empty=True)
    snapshot = args["snapshot"]
    attempt = snapshot["attempts"][0]
    document = json.loads(attempt["ManifestJson"])
    if was_reader:
        generation = build_workbook_generation(build(fixture(names=("Pass 4",))))
        document["generation"]["tables"] = generation.manifest()
        document["generation"]["reader_guild_id"] = "123"
    # Retain the exact durable envelope and part proofs as recovery would read them.
    attempt["ManifestJson"] = json.dumps(document)
    attempt["ManifestHash"] = digest(document).hex()
    runtime = object.__new__(ExportRuntime)
    runtime.registration = Mock()
    runtime.registration.sheets.return_value = args["registration"]
    runtime.registration.value.return_value = {"protected_file_ids": []}
    stream = SimpleNamespace(
        scope={"OwnerKind": "job", "ObjectID": attempt["JobID"], "NestedToken": str(uuid4())},
        stream_id=str(uuid4()),
        execute=args["execute"],
    )
    # Pool identity remains mandatory even when the current binding differs from history.
    pool = snapshot["pool"]["pool"] if "pool" in snapshot["pool"] else snapshot["pool"]
    binding = dict(pool_id=pool["PoolID"], guild_id="999") if now_enabled else None
    transport = runtime.transport(snapshot, stream, reader_binding=binding)
    assert isinstance(transport, ReaderSheetsTransport) is was_reader
    assert transport.reader_guild_id == ("123" if was_reader else None)


def test_two_pool_planning_keeps_reader_activation_and_recovery_local(monkeypatch):
    from kvk.services.source_output_pool_service import SourceOutputPlanner

    packet = activated()
    reader_pool = packet["pools"][0]["pool_id"]
    legacy_pool = str(uuid4())
    packet["pools"].append(dict(packet["pools"][0], pool_id=legacy_pool))
    runtime = object.__new__(ExportRuntime)
    runtime.connect = Mock()
    runtime.registration = Mock()
    runtime.registration.value.return_value = packet
    contexts = {}
    for pool_id, index in ((reader_pool, "reader-index"), (legacy_pool, "legacy-index")):
        contexts[pool_id] = dict(
            pool=dict(
                PoolID=pool_id,
                ActiveKVK=16,
                IndexFileID=index,
                AccountKey="account",
                Epoch=1,
                Version=1,
                RegistrationHash="hash",
                PoolState="active",
            ),
            slots=[dict(FileID=f"{index}-slot-{i}") for i in range(8)],
            jobs=[],
            attempts=[],
            parts=[],
        )
    runtime.pools = Mock()
    runtime.pools.snapshot.side_effect = contexts.__getitem__
    runtime.pools.resolve.side_effect = lambda season, index: {
        "reader-index": reader_pool,
        "legacy-index": legacy_pool,
    }[index]
    runtime.pools.is_index.side_effect = lambda name: name in {"reader-index", "legacy-index"}
    monkeypatch.setattr(
        "kvk.dal.source_reader_activation_dal.intent_scope",
        lambda *args: (16, {CALCULATION_VERSION}),
    )
    reader = build_workbook_generation(build(fixture(names=("Pass 4",))))
    legacy = Mock(key="legacy-key")
    legacy.manifest.return_value = {"legacy": {}}
    monkeypatch.setattr(
        "kvk.services.source_reader_activation.load_reader_generation", lambda **kwargs: reader
    )
    monkeypatch.setattr(
        "kvk.services.new_source_export_service.load_intent_generation", lambda **kwargs: legacy
    )
    monkeypatch.setattr("kvk.services.source_output_pool_service.physical_generation", lambda g: g)
    monkeypatch.setattr(
        "kvk.services.source_output_pool_service.capacity_for_snapshot",
        lambda *args: SimpleNamespace(current_parts=1, required_files=5),
    )
    planner = SourceOutputPlanner(runtime.pools, runtime.load_generation)
    for pool_id, expected in ((reader_pool, reader), (legacy_pool, legacy)):
        context = contexts[pool_id]
        registration = SimpleNamespace(
            kvk_no=16,
            account="account",
            epoch=1,
            destinations=tuple(
                sorted([context["pool"]["IndexFileID"], *(s["FileID"] for s in context["slots"])])
            ),
        )
        proof = planner("intent", b"a" * 32, registration)
        assert proof["pool_id"] == pool_id
        assert proof["generation_key"] == expected.key
        assert proof["manifest_hash"] == digest(expected.manifest()).hex()

    # The same intent has differing durable layouts in the two pools.
    for pool_id, job in ((reader_pool, "reader-job"), (legacy_pool, "legacy-job")):
        contexts[pool_id]["jobs"] = [dict(JobID=job, IntentID="intent")]
        contexts[pool_id]["attempts"] = [dict(JobID=job, AttemptID=job)]
    monkeypatch.setattr(
        "services.export_coordination_dal.checked_attempt_manifest",
        lambda attempt, parts: dict(
            generation=dict(
                tables=reader.manifest() if attempt["JobID"] == "reader-job" else legacy.manifest(),
                reader_guild_id="123",
            )
        ),
    )
    packet.pop("reader_exports")
    assert (
        runtime.reader_binding("intent", b"a" * 32, pool_id=reader_pool, job_id="reader-job")[
            "guild_id"
        ]
        == "123"
    )
    assert (
        runtime.reader_binding("intent", b"a" * 32, pool_id=legacy_pool, job_id="legacy-job")
        is None
    )
    with pytest.raises(SourceConflict, match="destination pool or intent"):
        runtime.reader_binding("intent", b"a" * 32, pool_id=legacy_pool, job_id="reader-job")
    with pytest.raises(SourceConflict, match="registered destination pool"):
        runtime.reader_binding("intent", b"a" * 32, pool_id=str(uuid4()))

    # An unrelated job in the same pool cannot override this job's layout.
    contexts[reader_pool]["jobs"].append(dict(JobID="other-job", IntentID="intent"))
    contexts[reader_pool]["attempts"].append(dict(JobID="other-job", AttemptID="other"))
    assert (
        runtime.reader_binding("intent", b"a" * 32, pool_id=reader_pool, job_id="reader-job")[
            "guild_id"
        ]
        == "123"
    )
