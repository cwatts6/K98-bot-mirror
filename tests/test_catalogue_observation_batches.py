"""Bounded reads must retain permissions, object membership and fail-fast checks."""

import json

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.catalogue_observation_dal import ObservationDeferred
from services.export_execution_dal import (
    _application_scoped_rows,
    application_authority_snapshot,
    application_installation_snapshot,
)
from services.export_schema_fingerprint import FORMAT


class AuthorityCursor:
    def __init__(self):
        self.commands = []
        self.consumed = True
        self.data = []

    def execute(self, sql, *parameters):
        assert self.consumed
        self.commands.append((sql, parameters))
        self.consumed = False
        if "AS Principal,HAS_PERMS_BY_NAME" in sql:
            self.data = [
                dict(
                    ServerName="lab", DatabaseName="ROK_TRACKER", Principal="app", ViewDefinition=1
                )
            ]
        elif "FROM sys.schemas s CROSS APPLY" in sql:
            self.data = [dict(SchemaName="dbo", PermissionName="SELECT", Subentity="")]
        else:
            names = sorted(json.loads(parameters[0]))
            if "HAS_PERMS_BY_NAME" in sql:
                self.data = [
                    dict(
                        ObjectName=name, ColumnName=column, PermissionName="SELECT", Allowed=allowed
                    )
                    for name in names
                    for column, allowed in (("A", 1), ("ä¸­", 0), ("ðŸ˜€", 1))
                ]
            else:
                self.data = [
                    dict(ObjectName=name, PermissionName=permission, Subentity="")
                    for name in names
                    for permission in ("EXECUTE", "SELECT", "SELECT")
                ]
        self.description = [(key,) for key in self.data[0]]

    def fetchone(self):
        self.consumed = True
        return tuple(self.data[0].values())

    def fetchall(self):
        self.consumed = True
        return [tuple(row.values()) for row in self.data]


def test_actual_authority_collector_preserves_every_permission_and_native_column_order():
    scope = sorted([f"dbo.Table_{number:03}" for number in range(258)] + ["dbo.LATEST_T4&T5_KILLS"])
    ordinary, batched = AuthorityCursor(), AuthorityCursor()
    expected = application_authority_snapshot(ordinary, scope=scope)
    checkpoints = []

    def checkpoint():
        assert batched.consumed
        checkpoints.append(len(batched.commands))

    actual = application_authority_snapshot(
        batched, scope=scope, checkpoint=checkpoint, observation_batches=True
    )
    assert actual == expected and digest(actual) == digest(expected)
    assert len(checkpoints) == len(batched.commands) == 16
    # Both permission queries cover the entire declared object set exactly once.
    by_query = {}
    for sql, parameters in batched.commands:
        if parameters:
            by_query.setdefault(sql, []).extend(json.loads(parameters[0]))
    assert len(by_query) == 2
    assert all(sorted(names) == scope for names in by_query.values())
    assert all(
        len(json.loads(p[0])) <= (64 if "HAS_PERMS_BY_NAME" in sql else 32)
        for sql, p in batched.commands
        if p
    )


def test_changed_generation_between_batches_stops_before_any_further_query():
    cursor = AuthorityCursor()

    def checkpoint():
        if len(cursor.commands) == 3:
            raise ObservationDeferred("generation_changed")

    with pytest.raises(ObservationDeferred):
        application_authority_snapshot(
            cursor,
            scope=[f"dbo.Table_{number}" for number in range(260)],
            checkpoint=checkpoint,
            observation_batches=True,
        )
    assert len(cursor.commands) == 3 and cursor.consumed


@pytest.mark.parametrize(
    "scope",
    [
        None,
        [],
        ("dbo.A",),
        ["dbo.A", "dbo.a"],
        ["dbo.A; DROP"],
        ["other.A"],
        ["dbo.ä¸­"],
        ["dbo.A"] * 2049,
    ],
)
def test_invalid_observer_scope_is_refused_before_sql(scope):
    cursor = AuthorityCursor()
    with pytest.raises(SourceConflict):
        application_authority_snapshot(
            cursor, scope=scope, checkpoint=lambda: None, observation_batches=True
        )
    assert cursor.commands == []


@pytest.mark.parametrize(
    "kwargs", [dict(checkpoint=None), dict(metadata_format=None), dict(observation_batches=1)]
)
def test_full_batching_requires_portable_contract_and_checkpoint_before_sql(kwargs):
    cursor = AuthorityCursor()
    options = dict(
        scope=["dbo.A"], checkpoint=lambda: None, metadata_format=FORMAT, observation_batches=True
    )
    options.update(kwargs)
    with pytest.raises(SourceConflict):
        application_installation_snapshot(cursor, **options)
    assert cursor.commands == []


def test_unexpected_object_cannot_be_hidden_by_batch_merging():
    class WrongObject(AuthorityCursor):
        def fetchall(self):
            self.consumed = True
            return [("dbo.Outside", "SELECT", "")]

    cursor = WrongObject()
    with pytest.raises(SourceConflict, match="outside"):
        _application_scoped_rows(
            cursor,
            "SELECT object permissions",
            [f"dbo.Table_{n}" for n in range(129)],
            lambda: None,
            "object_permissions",
            True,
        )


def test_statement_ceiling_is_checked_before_any_catalogue_dispatch():
    cursor = AuthorityCursor()
    with pytest.raises(SourceConflict, match="256-statement"):
        application_installation_snapshot(
            cursor,
            scope=[f"dbo.Table_{number}" for number in range(2048)],
            checkpoint=lambda: None,
            metadata_format=FORMAT,
            observation_batches=True,
        )
    assert cursor.commands == []


def test_combined_partitions_keep_every_object_once_and_separate_path_unchanged():
    from services.catalogue_observation_batches import scopes, statement_count

    scope = [f"dbo.Table_{number:03}" for number in range(484)]
    for category, before, after, width in (
        ("metadata.indexes", 6, 8, 64),
        ("identity.default_constraints", 1, 4, 128),
        ("metadata.triggers", 1, 2, 256),
        ("metadata.foreign_keys", 2, 4, 128),
    ):
        assert len(scopes(scope, category)) == before
        parts = scopes(scope, category, combined_boundaries=True)
        assert len(parts) == after and max(map(len, parts)) <= width
        assert sorted(name for part in parts for name in part) == scope
    assert statement_count(scope) == 254
    assert statement_count(scope, combined_boundaries=True) == 136


def test_combined_full_collector_still_refuses_oversized_scope_before_sql():
    from services.catalogue_observation_batch_dal import CatalogueBatchCursor

    raw = AuthorityCursor()
    with pytest.raises(SourceConflict, match="256-statement"):
        application_installation_snapshot(
            CatalogueBatchCursor(raw),
            scope=[f"dbo.Table_{number}" for number in range(2048)],
            checkpoint=lambda: None,
            metadata_format=FORMAT,
            observation_batches=True,
        )
    assert raw.commands == []
