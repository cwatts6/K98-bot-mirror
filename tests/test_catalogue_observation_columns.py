"""Column decomposition preserves joins and stops on an invalidated read."""

from copy import deepcopy

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.catalogue_observation_columns_dal import (
    column_batch,
    column_query,
    identity_column_query,
)
from services.catalogue_observation_dal import ObservationDeferred


class Cursor:
    def __init__(self, facts):
        self.facts = iter(deepcopy(facts))
        self.commands = []

    def execute(self, statement, *parameters):
        self.commands.append((statement, parameters))


@pytest.mark.parametrize("count", [0, 49, True])
def test_identity_query_refuses_unbounded_or_noninteger_placeholder_counts(count):
    with pytest.raises(SourceConflict):
        identity_column_query(count)


def facts():
    return [
        [
            dict(
                ObjectName="dbo.A",
                NativeObjectID=17,
                NativeDefaultID=90,
                Ordinal=1,
                ColumnName="ID",
            ),
            dict(
                ObjectName="dbo.A",
                NativeObjectID=17,
                NativeDefaultID=0,
                Ordinal=3,
                ColumnName="Derived",
            ),
            dict(
                ObjectName="dbo.A",
                NativeObjectID=17,
                NativeDefaultID=91,
                Ordinal=4,
                ColumnName="LegacyDefault",
            ),
        ],
        [dict(NativeDefaultID=90, DefaultName="DF_A", DefaultDefinition="((1))")],
        [dict(NativeObjectID=17, Ordinal=3, ComputedDefinition="[ID]+(1)", ComputedPersisted=True)],
        [dict(NativeObjectID=17, Ordinal=1, IdentitySeed="1", IdentityIncrement="3")],
    ]


def test_column_parts_keep_native_order_and_original_left_join_nulls():
    cursor = Cursor(facts())
    result = column_batch(cursor, ["dbo.A"], lambda c: next(c.facts))
    assert [row["Ordinal"] for row in result] == [1, 3, 4]
    assert result[0] == dict(
        ObjectName="dbo.A",
        Ordinal=1,
        ColumnName="ID",
        DefaultName="DF_A",
        DefaultDefinition="((1))",
        ComputedDefinition=None,
        ComputedPersisted=None,
        IdentitySeed="1",
        IdentityIncrement="3",
    )
    assert result[1]["ComputedPersisted"] is True and result[1]["IdentitySeed"] is None
    # An old bound default need not be present in sys.default_constraints.
    assert result[2]["DefaultDefinition"] is None
    assert all(not any(key.startswith("Native") for key in row) for row in result)
    assert len(cursor.commands) == 4


def test_object_names_are_only_parameters_in_the_column_lookup():
    cursor = Cursor(facts())
    names = ["dbo.A", "dbo.LATEST_T4&T5_KILLS"]
    column_batch(cursor, names, lambda c: next(c.facts))
    sql, parameters = cursor.commands[0]
    assert sql.count("?") == 2 and parameters == tuple(names)
    assert all(name not in sql for name in names)


@pytest.mark.parametrize("count", [0, 17, True])
def test_column_parameter_shape_is_finite(count):
    with pytest.raises(SourceConflict):
        column_query(count)


def test_smaller_base_reads_cover_each_object_once_before_shared_decorations():
    values = facts()
    cursor = Cursor([values[0], [], [], *values[1:]])
    scope = ["dbo.A", *[f"dbo.Table{n}" for n in range(32)]]
    result = column_batch(cursor, scope, lambda c: next(c.facts))
    assert len(result) == 3 and result[0]["DefaultName"] == "DF_A"
    assert [len(p) for _, p in cursor.commands[:3]] == [16, 16, 1]
    assert [name for _, p in cursor.commands[:3] for name in p] == scope
    assert len(cursor.commands) == 6


def test_changed_generation_stops_before_any_following_column_part():
    cursor = Cursor(facts())

    def consume(actual):
        if len(actual.commands) == 2:
            raise ObservationDeferred("generation_changed")
        return next(actual.facts)

    with pytest.raises(ObservationDeferred):
        column_batch(cursor, ["dbo.A"], consume)
    assert len(cursor.commands) == 2


@pytest.mark.parametrize("invalid", ["duplicate", "outside"])
def test_column_decoration_cannot_silently_overwrite_or_hide_rows(invalid):
    values = facts()
    if invalid == "duplicate":
        values[2].append(dict(values[2][0]))
    else:
        values[2][0]["NativeObjectID"] = 88
    cursor = Cursor(values)
    with pytest.raises(SourceConflict):
        column_batch(cursor, ["dbo.A"], lambda c: next(c.facts))
