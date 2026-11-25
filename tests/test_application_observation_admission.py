"""Reuse must reduce reads without transferring permission or mutation authority."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace
from itertools import repeat

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services import (
    application_observation_admission as admission,
    catalogue_observation_dal as dal,
)
from services.export_execution_dal import application_authority_snapshot
from services.legacy_export_snapshot_dal import PreparationClaim
from tests.test_application_maintenance_contract import defer
from tests.test_catalogue_observation import Cursor, expected, token
from tests.test_coherent_application_observation import (
    MetadataCursor,
    coherent_sample,
    sample as maintenance_sample,
)


@pytest.fixture
def sample(monkeypatch):
    return maintenance_sample.__wrapped__(monkeypatch)


class EntryCursor(Cursor):
    def __init__(self, outputs, *, session=51, generation=2, absent=1):
        row = token(generation, absent)
        row[1], row[3], row[5] = "ROK_TRACKER", "app", session
        if session != 51:
            row[6], row[7] = 1, 1  # Actual borrowed producer transaction is independently checked.
        super().__init__()
        self.boundaries = repeat(row)
        self.connection = object()
        self.outputs = deepcopy(outputs)
        self.permission_rows = []
        self.row = row
        self.closed = False

    def execute(self, statement, *parameters):
        if self.closed:
            raise RuntimeError("physical cursor closed")
        if statement == dal.BOUNDARY_SQL:
            return super().execute(statement)
        self.commands.append(statement)
        if "LEFT JOIN dbo.KVKFinalReportHeader" in statement:
            result = self.outputs
        elif statement.startswith("SELECT CONVERT(nvarchar(128),SERVERPROPERTY"):
            result = [
                dict(
                    ServerName="lab", DatabaseName="ROK_TRACKER", Principal="app", ViewDefinition=1
                )
            ]
        elif "FROM sys.schemas s CROSS APPLY" in statement:
            result = self.permission_rows
        elif "sys.fn_my_permissions" in statement or "'COLUMN') AS Allowed" in statement:
            result = []
        else:
            pytest.fail("Metadata or business SQL dispatched during reuse: " + statement)
        self.description = [(key,) for key in result[0]] if result else []
        self.result = iter([*(tuple(row.values()) for row in result)])

    def fetchall(self):
        return list(self.result)


def prepared(sample):
    observed, approved, proof = coherent_sample(sample)
    claim = PreparationClaim(
        "preparation", "account", "owner", 4, 8, (("sql_snapshot:legacy_outputs", 2),)
    )
    context = dict(
        configuration={"destination": "first"},
        registration={"runtime": "first"},
        approved=approved,
        expected_modules=expected(),
    )
    binding = admission.AdmissionBinding.for_claim(claim, **context)
    origin = EntryCursor(observed["maintenance_lifecycle"]["outputs"])
    producer = EntryCursor(origin.outputs, session=72)
    return observed, proof, claim, context, binding, origin, producer


def cache(binding, context):
    return admission.AdmissionMetadata(
        binding, approved=context["approved"], expected_modules=context["expected_modules"]
    )


def test_reuse_reads_fresh_actual_permissions_and_lifecycle_without_metadata_scan(sample):
    observed, proof, _, context, binding, origin, producer = prepared(sample)
    with cache(binding, context) as owned:
        owned.remember(origin, proof)
        origin_before = len(origin.commands)
        observed["metadata"]["objects"].clear()  # Caller mutation cannot alter the saved metadata.
        result = owned.consume(producer, binding)
        assert result.value["metadata"]["objects"]
        assert result.value["maintenance_lifecycle"]["outputs"] == producer.outputs
        assert result.boundary.identity[5:8] == (72, 1, 1)
        assert len([q for q in producer.commands if q != dal.BOUNDARY_SQL]) == 5
        assert origin.commands[origin_before:] == [dal.BOUNDARY_SQL]
        assert producer.commands.count(dal.BOUNDARY_SQL) == 1
        with pytest.raises(dal.ObservationContractError, match="Unconsumed"):
            owned.consume(producer, binding)


@pytest.mark.parametrize(
    "changed", ["fence", "version", "resources", "configuration", "registration"]
)
def test_changed_admission_binding_refuses_before_any_sql(sample, changed):
    _, proof, claim, context, binding, origin, producer = prepared(sample)
    with cache(binding, context) as owned:
        owned.remember(origin, proof)
        if changed in {"fence", "version"}:
            claim = replace(claim, **{changed: getattr(claim, changed) + 1})
        elif changed == "resources":
            claim = replace(claim, resources=(("sql_snapshot:legacy_outputs", 3),))
        else:
            context[changed] = {"changed": True}
        changed_binding = admission.AdmissionBinding.for_claim(claim, **context)
        count = len(origin.commands)
        with pytest.raises(dal.ObservationContractError, match="exact admission"):
            owned.consume(producer, changed_binding)
        assert len(origin.commands) == count and producer.commands == []


def test_same_generation_does_not_cache_permissions_or_lifecycle(sample):
    observed, proof, _, context, binding, origin, producer = prepared(sample)
    with cache(binding, context) as owned:
        owned.remember(origin, proof)
        producer.permission_rows = [dict(SchemaName="dbo", PermissionName="CONTROL", Subentity="")]
        with pytest.raises(SourceConflict, match="effective permissions"):
            owned.consume(producer, binding)
    producer.permission_rows = []
    defer(observed, count=1)
    with cache(binding, context) as owned:
        owned.remember(origin, proof)
        producer.outputs[0]["DueObjectID"] = 999
        with pytest.raises(SourceConflict):
            owned.consume(producer, binding)


@pytest.mark.parametrize("where", ["origin", "producer"])
def test_generation_change_discards_candidate_before_business_admission(sample, where):
    _, proof, _, context, binding, origin, producer = prepared(sample)
    with cache(binding, context) as owned:
        owned.remember(origin, proof)
        cursor = origin if where == "origin" else producer
        cursor.row[9] = cursor.row[11] = 3
        with pytest.raises(dal.ObservationDeferred, match="generation_changed"):
            owned.consume(producer, binding)
        if where == "origin":
            assert producer.commands == []
        else:
            # The second token closes the fresh authority/lifecycle read. A
            # change between origin and producer checks discards those rows;
            # it cannot admit business work or start another metadata scan.
            assert producer.commands[-1] == dal.BOUNDARY_SQL
            assert all(q.startswith("SELECT ") for q in producer.commands[:-1])
            assert len(producer.commands) == 6


def test_live_origin_and_actual_target_are_required(sample):
    _, proof, _, context, binding, origin, producer = prepared(sample)
    with cache(binding, context) as owned:
        owned.remember(origin, proof)
        origin.closed = True
        with pytest.raises(RuntimeError, match="physical cursor closed"):
            owned.consume(producer, binding)
        assert producer.commands == []
    origin.closed = False
    with cache(binding, context) as owned:
        owned.remember(origin, proof)
        producer.row[3] = "other-principal"
        with pytest.raises(dal.ObservationContractError, match="target/principal"):
            owned.consume(producer, binding)
        assert producer.commands[-1] == dal.BOUNDARY_SQL
        assert all(q.startswith("SELECT ") for q in producer.commands[:-1])


def test_context_exit_and_parallel_owner_cannot_reuse(sample):
    _, proof, _, context, binding, origin, producer = prepared(sample)
    with cache(binding, context) as owned:
        owned.remember(origin, proof)
        with ThreadPoolExecutor(max_workers=1) as worker:
            attempt = worker.submit(owned.consume, producer, binding)
            with pytest.raises(dal.ObservationContractError, match="live physical owner"):
                attempt.result(timeout=5)
        assert producer.commands == []
    with pytest.raises(dal.ObservationContractError, match="live physical owner"):
        owned.consume(producer, binding)


def test_actual_authority_reader_contains_only_target_and_three_permission_queries():
    cursor = MetadataCursor()
    checkpoints = []
    result = application_authority_snapshot(
        cursor, scope=["dbo.Fixture"], checkpoint=lambda: checkpoints.append(len(cursor.commands))
    )
    assert set(result) == {
        "target",
        "schema_permissions",
        "object_permissions",
        "column_permissions",
    }
    assert checkpoints == [1, 2, 3, 4]
