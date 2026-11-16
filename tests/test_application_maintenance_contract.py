"""Producer post-states through the real shared guard, not an isolated hash stub."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from core import sql_connection_custody as custody
from kvk.dal.new_source_import_dal import SourceConflict, digest
from services import (
    application_maintenance_contract as policy,
    application_maintenance_dal as lifecycle_dal,
    export_d4_contract,
    export_execution_dal,
    export_runtime_composition as runtime,
)
from services.export_schema_fingerprint import (
    FORMAT,
    IDENTITY_FIELDS,
    METADATA_FIELDS,
    application_metadata_fingerprint,
)
from tests.test_export_schema_fingerprint import column


def publication(name, season):
    return dict(
        ObjectName=name,
        ObjectID=100 + season,
        ObjectCreated="2026-11-16T12:01:43.930",
        HeaderRevision=7,
        HeaderState="OUTPUT_COMPLETE",
        KVKNo=season,
        DueGeneration=4,
        CompletedGeneration=3,
        DueObjectID=100 + season,
        DueObjectCreated="2026-11-16T12:01:43.930",
        DueHeaderRevision=7,
        State="pending",
        ClaimedGeneration=3,
        AggregateDue=4,
        AggregateCompleted=3,
        AggregateState="pending",
    )


@pytest.fixture
def sample(monkeypatch):
    metadata = {k: [] for k in METADATA_FIELDS}
    identity = {k: [] for k in IDENTITY_FIELDS}
    producer = "dbo.sp_ExcelOutput_ByKVK"
    source = [dict(name=producer, type="P", path="fixture.sql", sha256="a" * 64)]
    metadata["objects"].append(
        dict(
            ObjectName=producer,
            ObjectType="P",
            ModuleDefinition="CREATE PROCEDURE dbo.sp_ExcelOutput_ByKVK AS RETURN 0;",
            AnsiNulls=True,
            QuotedIdentifier=True,
            ExecuteAsPrincipal=None,
            MemoryOptimized=False,
            TemporalType=0,
        )
    )
    dynamic = []
    outputs = []
    for season in (16, 17):
        name = f"dbo.EXCEL_FOR_KVK_{season}"
        dynamic.append(dict(name=name, type="U", producer_modules=[producer]))
        outputs.append(publication(name, season))
        metadata["objects"].append(
            dict(
                ObjectName=name,
                ObjectType="U",
                ModuleDefinition=None,
                AnsiNulls=None,
                QuotedIdentifier=None,
                ExecuteAsPrincipal=None,
                MemoryOptimized=False,
                TemporalType=0,
            )
        )
        for position, (suffix, label) in enumerate((("GovID", "Gov_ID"), ("KVK_NO", "KVK_NO")), 1):
            metadata["columns"].append(dict(column(label, position), ObjectName=name))
            identity["columns"].append(
                dict(
                    object_name=name,
                    column_id=position,
                    column_name=label,
                    visible_position=position,
                    max_column_id_used=2,
                    is_computed=False,
                )
            )
            expected = policy.expected_index(name, suffix, label)
            index_name = expected["identity"]["name"]
            metadata["indexes"].append(dict(expected["rows"][0], IndexName=index_name))
            identity["indexes"].append(
                dict(
                    object_name=name,
                    name=index_name,
                    index_id=position,
                    type_desc="NONCLUSTERED",
                    is_unique=False,
                    is_primary_key=False,
                    is_unique_constraint=False,
                    is_disabled=False,
                    has_filter=False,
                    filter_definition=None,
                )
            )
    observed = dict(
        version=2,
        metadata=metadata,
        schema_identity=identity,
        target=dict(
            ServerName="lab", DatabaseName="ROK_TRACKER", Principal="app", ViewDefinition=1
        ),
        schema_permissions=[],
        object_permissions=[],
        column_permissions=[],
    )
    approved = dict(
        version=3,
        server="lab",
        database="ROK_TRACKER",
        principal="app",
        fingerprint_format=FORMAT,
        metadata_hash=application_metadata_fingerprint(metadata, identity),
        permissions_hash=digest(
            dict(schema_permissions=[], object_permissions=[], column_permissions=[])
        ).hex(),
        review_id="00000000-0000-4000-8000-000000000001",
        sources=source,
        dynamic_objects=dynamic,
        phase1_installation="20261109_001_p02_phase1_sql_exports",
        d4_installation="20261111_001_p02_d4_combined",
        scope_hash=export_d4_contract.ACTIVATION_SCOPE_SHA256,
    )
    monkeypatch.setattr(export_d4_contract, "APPLICATION_SOURCE_SHA256", digest(source).hex())
    monkeypatch.setattr(
        export_execution_dal, "application_activation_scope", lambda **kw: [producer]
    )
    return observed, approved, outputs


def defer(observed, season=16, count=2):
    """Model the exact published/partial-index post-states, retaining raw identity."""
    names = [f"IX_EXCEL_FOR_KVK_{season}_{s}" for s in ("GovID", "KVK_NO")][:count]
    observed["metadata"]["indexes"] = [
        r for r in observed["metadata"]["indexes"] if r["IndexName"] not in names
    ]
    observed["schema_identity"]["indexes"] = [
        r for r in observed["schema_identity"]["indexes"] if r["name"] not in names
    ]


def opt_in(observed, approved, outputs):
    approved["maintenance_policy"] = policy.POLICY
    observed["maintenance_lifecycle"] = dict(
        policy=policy.POLICY, guard="exclusive_schema_observation", outputs=outputs
    )


@pytest.mark.parametrize("count", [0, 1, 2])
@pytest.mark.parametrize("state", ["pending", "failed", "unknown"])
def test_real_guard_accepts_only_opted_in_composed_poststate(sample, count, state):
    observed, approved, outputs = sample
    runtime.verify_application_installation_contract(observed, approved)
    defer(observed, count=count)
    if count:
        with pytest.raises(SourceConflict, match="source shapes"):
            runtime.verify_application_installation_contract(observed, approved)
    outputs[0].update(State=state, AggregateState=state)
    opt_in(observed, approved, outputs)
    before = deepcopy((observed, approved))
    assert (
        runtime.verify_application_installation_contract(observed, approved)
        == digest(observed).hex()
    )
    assert (observed, approved) == before  # no rewritten evidence or completion
    assert outputs[0]["CompletedGeneration"] == 3


def test_old_indexed_baseline_does_not_require_invented_maintenance_history(sample):
    observed, approved, outputs = sample
    for row in outputs:
        row.update({key: None for key in row if key != "ObjectName"})
    opt_in(observed, approved, outputs)
    runtime.verify_application_installation_contract(observed, approved)


@pytest.mark.parametrize(
    "field,value",
    [
        ("ObjectID", 999),
        ("ObjectID", True),
        ("DueObjectID", True),
        ("DueHeaderRevision", True),
        ("ObjectCreated", []),
        ("DueObjectCreated", "old"),
        ("HeaderRevision", 8),
        ("HeaderState", "pending"),
        ("KVKNo", 15),
        ("DueGeneration", None),
        ("DueGeneration", True),
        ("DueGeneration", 2**63),
        ("CompletedGeneration", 4),
        ("CompletedGeneration", -1),
        ("ClaimedGeneration", 5),
        ("AggregateDue", 3),
        ("AggregateCompleted", 4),
        ("State", "complete"),
        ("State", "running"),
        ("AggregateState", "running"),
        ("State", None),
    ],
)
def test_false_or_stale_due_proof_refuses(sample, field, value):
    observed, approved, outputs = sample
    defer(observed)
    outputs[0][field] = value
    opt_in(observed, approved, outputs)
    with pytest.raises(SourceConflict, match="Deferred maintenance contract"):
        runtime.verify_application_installation_contract(observed, approved)


@pytest.mark.parametrize(
    "damage",
    [
        "extra",
        "duplicate",
        "missing",
        "guard",
        "policy",
        "permission",
        "column",
        "module",
        "index",
        "metadata",
        "unregistered",
    ],
)
def test_policy_does_not_mask_unrelated_drift(sample, damage):
    observed, approved, outputs = sample
    defer(observed)
    opt_in(observed, approved, outputs)
    if damage == "extra":
        outputs[0]["extra"] = 1
    elif damage == "duplicate":
        outputs[1] = deepcopy(outputs[0])
    elif damage == "missing":
        outputs.pop()
    elif damage == "guard":
        observed["maintenance_lifecycle"]["guard"] = "unconfirmed"
    elif damage == "policy":
        approved["maintenance_policy"] = "allow_everything"
    elif damage == "permission":
        observed["schema_permissions"].append({"Allowed": 1})
    elif damage == "column":
        observed["metadata"]["columns"][0]["Nullable"] = True
    elif damage == "module":
        observed["metadata"]["objects"][0]["ModuleDefinition"] += " -- drift"
    elif damage == "index":
        observed["metadata"]["indexes"][0]["DescendingKey"] = True
    elif damage == "metadata":
        del observed["metadata"]["dependencies"]
    else:
        approved["dynamic_objects"][0]["name"] = "dbo.EXCEL_FOR_KVK_18"
    with pytest.raises(SourceConflict):
        runtime.verify_application_installation_contract(observed, approved)


class Cursor:
    def __init__(self, outputs, *, failure=None, mode="NoLock", isolation=2):
        self.connection = SimpleNamespace(autocommit=False)
        self.outputs, self.failure, self.mode, self.isolation = outputs, failure, mode, isolation
        self.calls, self.answer, self.held = [], None, False

    def execute(self, sql, *args):
        self.calls.append((sql, args))
        if "sp_releaseapplock" in sql:
            if self.failure == "release":
                raise OSError("lost release")
            self.answer, self.held = (0, "NoLock"), False
        elif "sp_getapplock" in sql:
            if self.failure == "acquire":
                raise OSError("lost acquire")
            self.answer = (-1,) if self.failure == "busy" else (0,)
            self.held = self.failure != "busy"
        elif "dm_exec_sessions" in sql:
            self.answer = (self.mode, "NoLock", self.isolation)
        else:
            assert self.held
            assert "OPENJSON(?)" in sql and len(args) == 1
            self.description = [(key,) for key in policy.PROOF_FIELDS]
        return self

    def fetchone(self):
        return self.answer

    def fetchall(self):
        return [tuple(row[col[0]] for col in self.description) for row in self.outputs]


def test_complete_shared_snapshot_query_guard_and_verification(sample, monkeypatch):
    observed, approved, outputs = sample
    defer(observed)
    approved["maintenance_policy"] = policy.POLICY
    cursor = Cursor(outputs)

    def read_metadata(actual_cursor, **kwargs):
        assert actual_cursor is cursor and cursor.held
        assert kwargs["metadata_format"] == FORMAT
        return deepcopy(observed)

    monkeypatch.setattr(export_execution_dal, "application_installation_snapshot", read_metadata)
    snapshot = runtime.application_snapshot_for_contract(cursor, approved)
    runtime.verify_application_installation_contract(snapshot, approved)
    assert not cursor.held
    assert not cursor.connection.autocommit
    assert all("COMMIT" not in sql and "ROLLBACK" not in sql for sql, _ in cursor.calls)
    assert not any("k98-legacy-output-snapshot" in sql for sql, _ in cursor.calls)


@pytest.mark.parametrize("failure", ["busy", "acquire", "release", "metadata"])
def test_guard_failure_no_retry_and_unknown_cleanup_keeps_custody(sample, failure):
    observed, approved, outputs = sample
    approved["maintenance_policy"] = policy.POLICY
    cursor = Cursor(outputs, failure=failure)
    reader = (
        Mock(side_effect=ValueError("metadata failed"))
        if failure == "metadata"
        else Mock(return_value=observed)
    )
    with pytest.raises((SourceConflict, custody.SqlCleanupUnknown, ValueError)):
        lifecycle_dal.maintenance_snapshot(cursor, approved, reader)
    assert sum("sp_getapplock" in sql for sql, _ in cursor.calls) == 1
    assert custody.connection_retained(cursor.connection) == (failure in {"acquire", "release"})
    if failure in {"busy", "acquire"}:
        reader.assert_not_called()


@pytest.mark.parametrize("mode,isolation", [("Shared", 2), ("Exclusive", 2), ("NoLock", 5)])
def test_no_lock_upgrade_or_isolation_change(sample, mode, isolation):
    observed, approved, outputs = sample
    approved["maintenance_policy"] = policy.POLICY
    cursor = Cursor(outputs, mode=mode, isolation=isolation)
    with pytest.raises(SourceConflict):
        lifecycle_dal.maintenance_snapshot(cursor, approved, lambda: observed)
    assert len(cursor.calls) == 1


@pytest.mark.parametrize("drift", [False, True])
def test_actual_producer_entry_point_uses_lifecycle_guard(sample, monkeypatch, drift):
    from services.legacy_export_snapshot_dal import LegacySnapshotDAL
    from tests.test_export_runtime_composition import legacy_permission_fixture

    observed, approved, outputs = sample
    legacy_observed, legacy = legacy_permission_fixture(monkeypatch)
    defer(observed)
    approved["maintenance_policy"] = policy.POLICY
    if drift:
        outputs[0]["DueObjectID"] += 1
    cursor = Cursor(outputs)
    monkeypatch.setattr(
        export_execution_dal, "legacy_installation_snapshot", lambda *a: legacy_observed
    )
    monkeypatch.setattr(
        export_execution_dal,
        "application_installation_snapshot",
        lambda *a, **kw: deepcopy(observed),
    )
    dal = LegacySnapshotDAL(
        Mock(),
        output_operations=True,
        execution_evidence=True,
        legacy_sql_contract=legacy,
        application_sql_contract=approved,
    )
    dal.authorize = Mock()
    if drift:
        with pytest.raises(SourceConflict):
            dal.verify_producer_cursor("claim", cursor)
    else:
        dal.verify_producer_cursor("claim", cursor)
    dal.authorize.assert_called_once_with("claim")
    assert not cursor.held
    assert all("COMMIT" not in sql and "ROLLBACK" not in sql for sql, _ in cursor.calls)
    assert sum("sp_getapplock" in sql for sql, _ in cursor.calls) == 1
