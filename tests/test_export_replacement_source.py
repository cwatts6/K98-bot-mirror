"""Replacement source planning preserves the exact intent and reader generation."""

from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from kvk.rendering.new_source_workbook import build_workbook_generation
from services.export_runtime_composition import ExportRuntime, RuntimeRegistration
from tests.test_export_runtime_composition import registration_fixture
from tests.test_kvk_source_checkpoints import build, fixture


@pytest.fixture
def source():
    runtime = ExportRuntime.__new__(ExportRuntime)
    value = registration_fixture(slot_count=8)
    runtime.registration = RuntimeRegistration(value)
    registered = value["pools"][0]
    context = dict(
        pool=dict(
            PoolID=registered["pool_id"],
            AccountKey=value["account"],
            SourceKey="snapshot_report_v1",
            RegistrationHash=registered["registration_sha256"],
            RegistrationJson='{"pool":0}',
            ExpectedOwner=registered["owner_email"],
            IndexFileID=registered["index_file_id"],
            ActiveKVK=16,
            PoolState="active",
            Epoch=1,
            Version=1,
        ),
        slots=[dict(FileID=f, State="free", AttemptID=None) for f in registered["slot_file_ids"]],
        registration_count=1,
    )
    runtime.pools = SimpleNamespace(snapshot=Mock(return_value=context))
    old_pool = str(uuid4())
    runtime.dal = SimpleNamespace(
        operator_snapshot=Mock(return_value=dict(pool=dict(pool=dict(PoolID=old_pool))))
    )
    generation = build_workbook_generation(build(fixture(names=("Pass 4",))))
    runtime.load_generation = Mock(return_value=generation)
    job = dict(
        JobID=str(uuid4()),
        IntentID=str(uuid4()),
        InputHash=(b"i" * 32).hex(),
        ConsumerKind="new_source",
        AccountKey=value["account"],
        KVK_NO=16,
    )
    activation = dict(
        activation_id=str(uuid4()),
        replacement_id=registered["pool_id"],
        mapping={
            "old-index": registered["index_file_id"],
            **{f"old-slot-{i}": f for i, f in enumerate(registered["slot_file_ids"])},
        },
    )
    return SimpleNamespace(
        runtime=runtime,
        context=context,
        job=job,
        activation=activation,
        old_pool=old_pool,
        generation=generation,
    )


def test_replacement_plan_loads_original_intent_and_checks_new_pool_capacity(source):
    r = source
    spec = r.runtime.replacement_source_plan(
        dict(job=r.job), r.activation, "admin", "Confirmed replacement"
    )
    r.runtime.load_generation.assert_called_once_with(
        r.job["IntentID"],
        bytes.fromhex(r.job["InputHash"]),
        pool_id=r.old_pool,
        job_id=r.job["JobID"],
    )
    assert spec.intent_id == r.job["IntentID"] and spec.input_hash.hex() == r.job["InputHash"]
    proof = json.loads(spec.provenance)
    assert proof["output_preflight"]["manifest_hash"] == digest(r.generation.manifest()).hex()
    assert proof["replacement"]["original_job_id"] == r.job["JobID"]
    assert set(spec.destinations) == set(r.activation["mapping"].values())


@pytest.mark.parametrize(
    "damage", ["missing_slot", "season", "blocked", "registration", "capacity"]
)
def test_changed_replacement_pool_never_queues_retained_source(source, damage):
    r = source
    if damage == "missing_slot":
        r.activation["mapping"].pop("old-slot-0")
    elif damage == "season":
        r.context["pool"]["ActiveKVK"] = 17
    elif damage == "blocked":
        r.context["pool"]["PoolState"] = "blocked"
    elif damage == "registration":
        r.context["pool"]["RegistrationHash"] = "0" * 64
    else:
        for slot in r.context["slots"]:
            slot["State"] = "quarantined"
    before = deepcopy(r.job)
    with pytest.raises(SourceConflict):
        r.runtime.replacement_source_plan(
            dict(job=r.job), r.activation, "admin", "Confirmed replacement"
        )
    assert r.job == before


def test_reader_lineage_requires_exact_immutable_delivery_link(monkeypatch):
    runtime = ExportRuntime.__new__(ExportRuntime)
    runtime.connect, runtime.dal = object(), Mock()
    registration = RuntimeRegistration(registration_fixture())
    runtime.registration = registration
    pool_id = registration.value()["pools"][0]["pool_id"]
    original, activation, current = (str(uuid4()) for _ in range(3))
    job = dict(
        JobID=current,
        IntentID="intent",
        AccountKey="account-a",
        ProvenanceJson=json.dumps(
            dict(replacement=dict(original_job_id=original, activation_id=activation))
        ),
    )
    runtime.pools = SimpleNamespace(snapshot=lambda _: dict(jobs=[job], attempts=[]))
    monkeypatch.setattr(
        "kvk.dal.source_reader_activation_dal.intent_scope", lambda *_: (16, {"version"})
    )
    read = Mock(
        return_value=dict(
            ReplacementJobID="foreign-job",
            OriginalInputHash=(b"i" * 32).hex(),
            ReplacementInputHash=(b"i" * 32).hex(),
        )
    )
    monkeypatch.setattr(
        "services.export_replacement_delivery_dal.ReplacementDeliveryDAL.read", read
    )
    with pytest.raises(SourceConflict, match="exact original delivery link"):
        runtime.reader_binding("intent", b"i" * 32, pool_id=pool_id, job_id=current)
    runtime.dal.operator_snapshot.assert_not_called()
