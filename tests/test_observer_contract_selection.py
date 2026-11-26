"""Explicit source/installation selection and lossless retained proof transport."""

from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services import export_runtime_composition as composition
from services.application_maintenance_contract import POLICY
from services.application_observation_fingerprint import FORMAT
from services.catalogue_observation_contract import PROTOCOL_SHA256
from services.catalogue_observation_dal import CoherentObservation, ObservationBoundary
from services.export_d4_contract import MIGRATION_ID as D4_MIGRATION
from services.export_observer_contract import (
    ACTIVATION_SCOPE_SHA256,
    LEGACY_FINGERPRINT_FORMAT,
    MIGRATION_ID,
    observation_record,
    require_observer_contract_pair,
    retained_observation,
)
from services.export_phase1_contract import MIGRATION_ID as PHASE1_MIGRATION

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def approved():
    binding = dict(
        version=1,
        protocol_sha256=PROTOCOL_SHA256,
        server="server",
        database="ROK_TRACKER",
        database_id=7,
        principal="app",
        login="app",
        sequence_object_id=100,
        sequence_created="2026-11-20T12:00:00.000000",
        sequence_modified="2026-11-20T12:00:00.000000",
        bootstrap_generation=1,
    )
    return dict(
        version=3,
        server="server",
        database="ROK_TRACKER",
        principal="app",
        sources=json.loads((ROOT / "deploy/p02_observer_application_sources.json").read_bytes()),
        dynamic_objects=[
            dict(
                name="dbo.EXCEL_EXPORT_KVK_TARGETS_16",
                type="U",
                producer_modules=["dbo.sp_TARGETS_MASTER"],
            ),
            dict(
                name="dbo.EXCEL_FOR_KVK_16", type="U", producer_modules=["dbo.sp_ExcelOutput_ByKVK"]
            ),
            dict(
                name="dbo.EXCEL_OUTPUT_KVK_TARGETS_16",
                type="U",
                producer_modules=["dbo.sp_Prep_ExcelOutputTable"],
            ),
            dict(name="dbo.TARGETS_16", type="U", producer_modules=["dbo.sp_Prep_TargetTable"]),
        ],
        metadata_hash="f575d6a9dfdfa74bc628d2e22e79924c4ce9cec63428321814a6f6b9d8c9994c",
        permissions_hash="0be05a7afb3dd97d135e3bbca1bea01dc13785caac416583a0f747656bf111b4",
        review_id="93374171-9958-498a-a40a-04d994f8738f",
        phase1_installation=PHASE1_MIGRATION,
        d4_installation=D4_MIGRATION,
        observer_installation=MIGRATION_ID,
        observation_installation=binding,
        scope_hash=ACTIVATION_SCOPE_SHA256,
        fingerprint_format=FORMAT,
        maintenance_policy=POLICY,
    )


def test_actual_source_contract_retains_complete_four_output_scope(approved):
    composition.validate_application_installation_contract(approved)
    scope = composition.application_contract_scope(approved)
    assert len(scope) == 487
    assert {row["name"] for row in approved["dynamic_objects"]} <= set(scope)


@pytest.mark.parametrize(
    "damage",
    [
        "lineage",
        "source",
        "format",
        "protocol",
        "target",
        "impersonation",
        "bootstrap",
        "scope",
        "policy",
    ],
)
def test_wrong_source_or_binding_fails_before_any_sql(approved, damage):
    if damage == "lineage":
        del approved["d4_installation"]
    elif damage == "source":
        approved["sources"][0]["sha256"] = "0" * 64
    elif damage == "format":
        approved["fingerprint_format"] = "application_schema_v1"
    elif damage == "scope":
        approved["scope_hash"] = "0" * 64
    elif damage == "policy":
        del approved["maintenance_policy"]
    else:
        field, value = {
            "protocol": ("protocol_sha256", "0" * 64),
            "target": ("database", "lab"),
            "impersonation": ("login", "administrator"),
            "bootstrap": ("bootstrap_generation", True),
        }[damage]
        approved["observation_installation"][field] = value
    with pytest.raises(SourceConflict):
        composition.application_snapshot_for_contract(object(), approved)


def test_successor_cannot_be_approved_as_plain_unbracketed_metadata(approved):
    with pytest.raises(SourceConflict, match="coherent proof"):
        composition.verify_application_installation_contract({}, approved)


def test_successor_dispatches_complete_collector_with_protected_identity(monkeypatch, approved):
    from services import application_maintenance_dal, export_execution_dal
    from services.catalogue_observation_batch_dal import CatalogueBatchCursor

    cursor, checkpoint, collected = object(), lambda: None, {}

    def read(actual, **kwargs):
        assert type(actual) is CatalogueBatchCursor and actual._cursor is cursor
        assert kwargs == dict(
            scope=composition.application_contract_scope(approved),
            metadata_format=FORMAT,
            checkpoint=checkpoint,
            observation_batches=True,
        )
        return collected

    def guarded(actual, contract, modules, collect, *, installation):
        assert type(actual) is CatalogueBatchCursor and contract is approved
        installation.require_modules(modules)
        assert installation.identity[:5] == ("server", "ROK_TRACKER", 7, "app", "app")
        assert collect(checkpoint) is collected
        return "coherent-result"

    monkeypatch.setattr(export_execution_dal, "application_installation_snapshot", read)
    monkeypatch.setattr(application_maintenance_dal, "coherent_maintenance_snapshot", guarded)
    assert composition.application_snapshot_for_contract(cursor, approved) == "coherent-result"


def test_pair_requires_matching_successor_authority_and_true_application_login(approved):
    fixed = dict(
        version=4, profile="application", server="server", database="ROK_TRACKER", principal="app"
    )
    legacy = dict(approved, version=2, fingerprint_format=LEGACY_FINGERPRINT_FORMAT)
    require_observer_contract_pair(fixed, legacy, approved)
    old = deepcopy(legacy)
    del old["observer_installation"]
    with pytest.raises(SourceConflict, match="selections must agree"):
        require_observer_contract_pair(fixed, old, approved)
    with pytest.raises(SourceConflict, match="same application target"):
        require_observer_contract_pair(dict(fixed, principal="other"), legacy, approved)


def sample_proof():
    stamp = datetime(2026, 11, 20, 12)
    return CoherentObservation(
        {"raw": "unchanged"},
        ObservationBoundary(
            ("server", "ROK_TRACKER", 7, "app", "app", 51, 1, 1, 2, 100, stamp, stamp), 19
        ),
    )


def test_retained_evidence_roundtrips_without_becoming_reuse_authority():
    proof = sample_proof()
    record = json.loads(json.dumps(observation_record(proof)))
    restored = retained_observation(proof.value, record)
    assert restored == proof and restored.value is proof.value
    assert set(record) == {"version", "guard", "identity", "generation"}


@pytest.mark.parametrize(
    "damage",
    [
        "extra",
        "generation_bool",
        "generation_zero",
        "nested",
        "doomed",
        "isolation",
        "session_bool",
        "timestamp",
    ],
)
def test_retained_evidence_refuses_corrupt_or_unsupported_state(damage):
    proof = sample_proof()
    record = observation_record(proof)
    if damage == "extra":
        record["accepted"] = True
    elif damage.startswith("generation"):
        record["generation"] = True if damage.endswith("bool") else 0
    else:
        index, value = {
            "nested": (6, 2),
            "doomed": (7, -1),
            "isolation": (8, 5),
            "session_bool": (5, True),
            "timestamp": (10, "2026-11-20T12:00:00"),
        }[damage]
        record["identity"][index] = value
    with pytest.raises(SourceConflict):
        retained_observation(proof.value, record)
