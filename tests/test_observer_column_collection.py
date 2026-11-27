"""Complete column facts survive consolidated, coherent catalogue collection."""

from copy import deepcopy
import json

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.catalogue_observation_batches import combine, scopes
from services.catalogue_observation_columns_dal import COLUMN_QUERIES, column_batch, column_scope
from services.catalogue_observation_dal import ObservationDeferred


def catalog(count=137):
    result = {name: [] for name in COLUMN_QUERIES}
    for number in range(count):
        name = f"dbo.Table_{number:03}"
        native = 100 + number
        default = 2000 + number if number % 13 == 0 else 0
        computed, identity = number % 37 == 0, number % 29 == 0
        result["columns"].append(
            dict(
                ObjectName=name,
                NativeObjectID=native,
                NativeDefaultID=default,
                Ordinal=3,
                ColumnName="ä¸­_ðŸ˜€",
                IsComputed=computed,
                IsIdentity=identity,
                Nullable=False,
                TypeName="dbo.AliasType",
                MaxLength=8,
            )
        )
        if default and number != 13:  # Legacy bound default absent from sys.default_constraints.
            result["defaults"].append(
                dict(NativeDefaultID=default, DefaultName=f"DF_{number}", DefaultDefinition="((1))")
            )
        if computed:
            result["computed"].append(
                dict(
                    NativeObjectID=native,
                    Ordinal=3,
                    ComputedDefinition="[A] + (1)",
                    ComputedPersisted=True,
                )
            )
        if identity:
            result["identity"].append(
                dict(
                    NativeObjectID=native,
                    Ordinal=3,
                    IdentitySeed="-9007199254740993",
                    IdentityIncrement="3",
                )
            )
    return result


class CatalogCursor:
    def __init__(self, facts):
        self.facts = deepcopy(facts)
        self.commands = []
        self.consumed = True
        self.fail_at = None

    def execute(self, statement, *parameters):
        assert self.consumed, "Every prior result must be consumed before the next dispatch"
        self.commands.append((statement, parameters))
        self.consumed = False
        category = next((k for k, v in COLUMN_QUERIES.items() if statement == v), "columns")
        names = set(parameters if category == "columns" else json.loads(parameters[0]))
        columns = [row for row in self.facts["columns"] if row["ObjectName"] in names]
        native = {row["NativeObjectID"] for row in columns}
        defaults = {row["NativeDefaultID"] for row in columns}
        self.result = (
            columns
            if category == "columns"
            else [
                row
                for row in self.facts[category]
                if row.get("NativeObjectID") in native or row.get("NativeDefaultID") in defaults
            ]
        )
        return self

    def consume(self, cursor):
        assert cursor is self
        self.consumed = True
        if len(self.commands) == self.fail_at:
            raise ObservationDeferred("generation_changed")
        return deepcopy(self.result)


def test_all_native_fields_order_nulls_and_bound_defaults_equal_existing_reader():
    facts = catalog()
    scope = [row["ObjectName"] for row in facts["columns"]]
    before, after = CatalogCursor(facts), CatalogCursor(facts)
    expected = combine(
        [
            row
            for part in scopes(scope, "metadata.columns")
            for row in column_batch(before, part, before.consume)
        ],
        scope,
        "metadata.columns",
    )
    actual = combine(
        column_batch(after, scope, after.consume, consolidate=True), scope, "metadata.columns"
    )
    assert actual == expected
    assert actual[13]["DefaultDefinition"] is None
    assert actual[0]["IdentitySeed"] == "-9007199254740993"
    assert len(after.commands) < len(before.commands)
    assert all(
        len(parameters) <= 16
        for sql, parameters in after.commands
        if sql not in COLUMN_QUERIES.values()
    )
    assert all(
        len(json.loads(parameters[0])) <= 64
        for sql, parameters in after.commands
        if sql in COLUMN_QUERIES.values()
    )
    assert all(not any(key.startswith("Native") for key in row) for row in actual)


def test_empty_and_undecorated_columns_do_not_request_impossible_decorations():
    cursor = CatalogCursor({key: [] for key in COLUMN_QUERIES})
    assert column_batch(cursor, [], cursor.consume, consolidate=True) == []
    assert cursor.commands == []
    facts = catalog(2)
    facts["columns"] = [facts["columns"][1]]
    cursor = CatalogCursor(facts)
    result = column_batch(cursor, ["dbo.Table_001"], cursor.consume, consolidate=True)
    assert len(cursor.commands) == 1
    assert (
        result[0]["DefaultDefinition"]
        is result[0]["ComputedDefinition"]
        is result[0]["IdentitySeed"]
        is None
    )


@pytest.mark.parametrize("fail_at", [1, 3, 10, 11, 12])
def test_changed_checkpoint_stops_base_or_decoration_reads_without_redispatch(fail_at):
    facts = catalog()
    scope = [row["ObjectName"] for row in facts["columns"]]
    cursor = CatalogCursor(facts)
    cursor.fail_at = fail_at
    with pytest.raises(ObservationDeferred, match="generation_changed"):
        column_batch(cursor, scope, cursor.consume, consolidate=True)
    assert len(cursor.commands) == fail_at and cursor.consumed


@pytest.mark.parametrize(
    "field,value",
    [
        ("IsComputed", None),
        ("IsIdentity", 1),
        ("NativeDefaultID", True),
        ("NativeDefaultID", -1),
        ("ObjectName", "dbo.Outside"),
    ],
)
def test_incomplete_or_outside_base_facts_cannot_suppress_required_checks(field, value):
    facts = catalog(1)
    cursor = CatalogCursor(facts)

    def consume(actual):
        result = actual.consume(actual)
        result[0][field] = value
        return result

    with pytest.raises(SourceConflict):
        column_batch(cursor, ["dbo.Table_000"], consume, consolidate=True)
    assert len(cursor.commands) == 1


def test_duplicate_native_identity_cannot_overwrite_facts():
    facts = catalog(1)
    facts["columns"].append(deepcopy(facts["columns"][0]))
    cursor = CatalogCursor(facts)
    with pytest.raises(SourceConflict, match="duplicate"):
        column_batch(cursor, ["dbo.Table_000"], cursor.consume, consolidate=True)
    assert len(cursor.commands) == 1


def test_only_observed_procedures_and_scalar_functions_leave_column_scope():
    objects = [
        dict(ObjectName=f"dbo.{kind}", ObjectType=kind)
        for kind in ("P", "FN", "U", "V", "IF", "TF", "FT", "IT", "S", "TT", "future")
    ]
    scope = [row["ObjectName"] for row in objects] + ["dbo.Missing"]
    preserved = deepcopy(objects)
    result = column_scope(scope, objects)
    assert result == scope[2:]
    assert objects == preserved and scope[:2] == ["dbo.P", "dbo.FN"]
    assert column_scope(["dbo.p", "dbo.fn"], objects) == []


class FullCatalogCursor(CatalogCursor):
    """SQL-shaped results for both physical dispatch paths, including boundary tails."""

    def __init__(self, facts, objects):
        super().__init__(facts)
        self.objects = objects
        self.connection = object()
        self.description = [("unused",)]

    def execute(self, statement, *parameters):
        from services.catalogue_observation_dal import BOUNDARY_SQL
        from tests.test_catalogue_observation import token

        suffix = "\n;" + BOUNDARY_SQL
        combined = statement.endswith(suffix)
        query = statement[: -len(suffix)] if combined else statement
        if "AS NativeDefaultID" in query or query in COLUMN_QUERIES.values():
            super().execute(query, *parameters)
            data = self.result
        else:
            self.commands.append((query, parameters))
            names = set()
            if parameters:
                names = (
                    set(json.loads(parameters[0]))
                    if len(parameters) == 1 and parameters[0].startswith("[")
                    else set(parameters)
                )
            if "AS ViewDefinition" in query:
                data = [
                    dict(
                        ServerName="lab", DatabaseName="fixture", Principal="dbo", ViewDefinition=1
                    )
                ]
            elif "RTRIM(o.type)" in query:
                data = [r for r in self.objects if r["ObjectName"] in names]
            elif "AS visible_position" in query:
                data = [
                    dict(
                        object_name=r["ObjectName"],
                        column_id=r["Ordinal"],
                        column_name=r["ColumnName"],
                        visible_position=1,
                        max_column_id_used=3,
                        is_computed=r["IsComputed"],
                    )
                    for r in self.facts["columns"]
                    if r["ObjectName"] in names
                ]
            else:
                data = []
        self.description = [(key,) for key in data[0]] if data else [("unused",)]
        self.result = iter(tuple(row.values()) for row in data)
        self.tail = [tuple(token())] if combined else None
        self.consumed = False
        return self

    def fetchone(self):
        result = next(self.result, None)
        if result is None:
            self.consumed = True
        return result

    def fetchall(self):
        self.consumed = True
        return list(self.result)

    def nextset(self):
        if self.tail is None:
            return False
        self.result = iter(self.tail)
        self.tail = None
        self.description = [("unused",)] * 19
        return True


def test_full_collector_preserves_all_categories_and_keeps_every_physical_checkpoint():
    from services.application_observation_fingerprint import FORMAT
    from services.catalogue_observation_batch_dal import CatalogueBatchCursor
    from services.catalogue_observation_dal import read_boundary
    from services.export_execution_dal import application_installation_snapshot
    from tests.test_catalogue_observation import expected

    facts = catalog()
    objects = [dict(ObjectName=row["ObjectName"], ObjectType="U") for row in facts["columns"]]
    objects += [dict(ObjectName=f"dbo.Proc_{n:03}", ObjectType="P") for n in range(70)]
    objects += [dict(ObjectName="dbo.Scalar", ObjectType="FN")]
    scope = sorted(row["ObjectName"] for row in objects)
    before, after = FullCatalogCursor(facts, objects), FullCatalogCursor(facts, objects)
    reference = application_installation_snapshot(
        before,
        scope=scope,
        metadata_format=FORMAT,
        checkpoint=lambda: None,
        observation_batches=True,
    )
    cursor = CatalogueBatchCursor(after)
    checkpoints = []

    def checkpoint():
        assert read_boundary(cursor, expected()).generation == 2
        checkpoints.append(len(after.commands))

    observed = application_installation_snapshot(
        cursor, scope=scope, metadata_format=FORMAT, checkpoint=checkpoint, observation_batches=True
    )
    assert observed == reference
    assert len(checkpoints) == len(after.commands)
    assert len(after.commands) < len(before.commands)
    assert len(observed["metadata"]["objects"]) == len(scope)
    assert (
        len(observed["metadata"]["columns"]) == len(observed["schema_identity"]["columns"]) == 137
    )


def test_dense_decoration_scopes_split_without_losing_any_native_fact():
    facts = {key: [] for key in COLUMN_QUERIES}
    for number in range(83):
        name, native, default = f"dbo.Dense_{number:03}", number + 1, number + 1001
        for ordinal, computed, identity, default_id in (
            (1, False, False, default),
            (3, True, False, 0),
            (8, False, True, 0),
        ):
            facts["columns"].append(
                dict(
                    ObjectName=name,
                    NativeObjectID=native,
                    NativeDefaultID=default_id,
                    Ordinal=ordinal,
                    ColumnName=f"C{ordinal}",
                    IsComputed=computed,
                    IsIdentity=identity,
                )
            )
        facts["defaults"].append(
            dict(NativeDefaultID=default, DefaultName=f"DF{number}", DefaultDefinition="((2))")
        )
        facts["computed"].append(
            dict(
                NativeObjectID=native,
                Ordinal=3,
                ComputedDefinition="[C1]+(1)",
                ComputedPersisted=False,
            )
        )
        facts["identity"].append(
            dict(NativeObjectID=native, Ordinal=8, IdentitySeed="1", IdentityIncrement="2")
        )
    scope = sorted({row["ObjectName"] for row in facts["columns"]})
    before, after = CatalogCursor(facts), CatalogCursor(facts)
    expected = combine(
        [
            row
            for part in scopes(scope, "metadata.columns")
            for row in column_batch(before, part, before.consume)
        ],
        scope,
        "metadata.columns",
    )
    actual = combine(
        column_batch(after, scope, after.consume, consolidate=True), scope, "metadata.columns"
    )
    assert actual == expected and len(actual) == 249
    for category in ("defaults", "computed", "identity"):
        groups = [
            json.loads(parameters[0])
            for query, parameters in after.commands
            if query == COLUMN_QUERIES[category]
        ]
        assert len(groups) == 2 and max(map(len, groups)) <= 64
        assert sorted(name for group in groups for name in group) == scope
