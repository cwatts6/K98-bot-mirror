"""The candidate must retain the full comparator and stop between real batches."""

from copy import deepcopy

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services import (
    application_maintenance_dal as lifecycle,
    catalogue_observation_dal as observation,
    export_execution_dal as sql_dal,
    export_runtime_composition as runtime,
)
from services.export_schema_fingerprint import FORMAT
from tests.test_application_maintenance_contract import defer, opt_in, sample as maintenance_sample
from tests.test_catalogue_observation import Cursor, expected, token


@pytest.fixture
def sample(monkeypatch):
    return maintenance_sample.__wrapped__(monkeypatch)


class LifecycleCursor(Cursor):
    def __init__(self, outputs, *, changed=False):
        boundaries = [token() for _ in range(3)]
        for row in boundaries:
            row[1], row[3] = "ROK_TRACKER", "app"
        if changed:
            boundaries[-1][9] = boundaries[-1][11] = 3
        super().__init__(*boundaries)
        self.outputs = outputs

    def execute(self, statement, *parameters):
        if statement == observation.BOUNDARY_SQL:
            return super().execute(statement)
        assert "LEFT JOIN dbo.KVKFinalReportHeader" in statement
        self.commands.append(statement)
        self.description = [(key,) for key in self.outputs[0]]

    def fetchall(self):
        return [tuple(row.values()) for row in self.outputs]


def coherent_sample(sample, *, changed=False):
    observed, approved, outputs = deepcopy(sample)
    opt_in(observed, approved, outputs)
    cursor = LifecycleCursor(outputs, changed=changed)
    proof = lifecycle.coherent_maintenance_snapshot(
        cursor, approved, expected(), lambda checkpoint: observed
    )
    assert all("sp_getapplock" not in statement for statement in cursor.commands)
    return observed, approved, proof


@pytest.mark.parametrize("missing_indexes", [0, 1, 2])
def test_new_observer_uses_full_existing_comparator_and_narrow_index_policy(
    sample, missing_indexes
):
    observed, approved, proof = coherent_sample(sample)
    defer(observed, count=missing_indexes)
    before = deepcopy(observed)
    assert (
        runtime.verify_application_installation_contract(observed, approved, observation=proof)
        == digest(observed).hex()
    )
    assert observed == before
    with pytest.raises(SourceConflict, match="guarded observation"):
        runtime.verify_application_installation_contract(observed, approved)


@pytest.mark.parametrize("corruption", ["column", "permission", "lifecycle", "target"])
def test_coherent_label_never_bypasses_existing_metadata_permissions_or_identity(
    sample, corruption
):
    observed, approved, proof = coherent_sample(sample)
    if corruption == "column":
        observed["metadata"]["columns"][0]["Nullable"] = True
    elif corruption == "permission":
        observed["schema_permissions"].append({"unexpected": "permission"})
    elif corruption == "lifecycle":
        defer(observed, count=1)
        observed["maintenance_lifecycle"]["outputs"][0]["DueObjectID"] = 999
    else:
        observed["target"]["Principal"] = "other"
    with pytest.raises(SourceConflict):
        runtime.verify_application_installation_contract(observed, approved, observation=proof)


def test_generation_change_during_lifecycle_read_discards_complete_candidate(sample):
    with pytest.raises(observation.ObservationDeferred, match="generation_changed"):
        coherent_sample(sample, changed=True)


def test_proof_cannot_be_attached_to_a_different_observation(sample):
    observed, approved, proof = coherent_sample(sample)
    with pytest.raises(SourceConflict, match="Exact coherent"):
        runtime.verify_application_installation_contract(
            deepcopy(observed), approved, observation=proof
        )


class MetadataCursor:
    def __init__(self):
        self.commands = []
        self.consumed = True

    def execute(self, statement, *parameters):
        assert self.consumed
        self.commands.append(statement)
        self.consumed = False
        self.description = [
            (key,) for key in ("ServerName", "DatabaseName", "Principal", "ViewDefinition")
        ]

    def fetchone(self):
        self.consumed = True
        return ("lab", "ROK_TRACKER", "app", 1)

    def fetchall(self):
        self.consumed = True
        return []


def test_actual_full_collector_checks_every_consumed_category_without_changing_results():
    first, second = MetadataCursor(), MetadataCursor()
    unchanged = sql_dal.application_installation_snapshot(
        first, scope=["dbo.Fixture"], metadata_format=FORMAT
    )
    checked = []

    def checkpoint():
        assert second.consumed
        checked.append(len(second.commands))

    candidate = sql_dal.application_installation_snapshot(
        second, scope=["dbo.Fixture"], metadata_format=FORMAT, checkpoint=checkpoint
    )
    assert candidate == unchanged
    assert second.commands == first.commands
    assert checked == list(range(1, len(second.commands) + 1))
    assert len(candidate["metadata"]) == 10 and candidate["schema_identity"]


def test_actual_collector_stops_dispatch_after_changed_generation():
    cursor = MetadataCursor()

    def changed():
        if len(cursor.commands) == 3:
            raise observation.ObservationDeferred("generation_changed")

    with pytest.raises(observation.ObservationDeferred):
        sql_dal.application_installation_snapshot(cursor, checkpoint=changed)
    assert len(cursor.commands) == 3 and cursor.consumed
