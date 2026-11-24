"""Read column facts without multiplying expensive catalogue-view joins.

All component reads belong to the same generation-bracketed batch. Native object and
column IDs join these temporary results only; they never become cached authority.
"""

import json

from kvk.dal.new_source_import_dal import SourceConflict
from services.catalogue_observation_batches import COLUMN_BASE_WIDTH
from services.catalogue_observation_query_dal import _SCOPE

COLUMN_QUERIES = {
    "columns": """SELECT s.name+'.'+o.name AS ObjectName,c.object_id AS NativeObjectID,
        c.default_object_id AS NativeDefaultID,
        c.column_id AS Ordinal,c.name AS ColumnName,ts.name+'.'+t.name AS TypeName,
        c.max_length AS MaxLength,c.precision AS [Precision],c.scale AS Scale,c.collation_name AS Collation,
        c.is_nullable AS Nullable,c.is_identity AS IsIdentity,c.is_computed AS IsComputed,
        c.is_rowguidcol AS IsRowGuid,c.is_sparse AS IsSparse,c.generated_always_type AS GeneratedAlways
        FROM sys.columns c JOIN sys.objects o ON o.object_id=c.object_id
        JOIN sys.schemas s ON s.schema_id=o.schema_id
        JOIN sys.types t ON t.user_type_id=c.user_type_id
        JOIN sys.schemas ts ON ts.schema_id=t.schema_id
        WHERE c.object_id IN (__OBJECT_IDS__)
        ORDER BY s.name COLLATE Latin1_General_100_BIN2,o.name COLLATE Latin1_General_100_BIN2,c.column_id""",
    "defaults": _SCOPE
    + """SELECT object_id AS NativeDefaultID,name AS DefaultName,definition AS DefaultDefinition
        FROM sys.default_constraints WHERE parent_object_id IN (SELECT object_id FROM @required)""",
    "computed": _SCOPE
    + """SELECT object_id AS NativeObjectID,column_id AS Ordinal,
        definition AS ComputedDefinition,is_persisted AS ComputedPersisted
        FROM sys.computed_columns WHERE object_id IN (SELECT object_id FROM @required)""",
    "identity": _SCOPE
    + """SELECT object_id AS NativeObjectID,column_id AS Ordinal,
        CONVERT(nvarchar(128),seed_value) AS IdentitySeed,
        CONVERT(nvarchar(128),increment_value) AS IdentityIncrement
        FROM sys.identity_columns WHERE object_id IN (SELECT object_id FROM @required)""",
}


def identity_column_query(count):
    """Generate placeholders only; the caller binds every validated object name."""
    from services.catalogue_observation_query_dal import IDENTITY_BATCH_QUERIES

    if type(count) is not int or not 1 <= count <= 48:
        raise SourceConflict("Identity column reads require 1-48 bound object names.")
    return IDENTITY_BATCH_QUERIES["identity.columns"].replace(
        "__IDENTITY_OBJECT_IDS__", ",".join("OBJECT_ID(?)" for _ in range(count))
    )


def column_query(count):
    """Finite scalar placeholders permit object-ID seeks without interpolated names."""
    if type(count) is not int or not 1 <= count <= COLUMN_BASE_WIDTH:
        raise SourceConflict("One to 16 column scope parameters required.")
    return COLUMN_QUERIES["columns"].replace(
        "__OBJECT_IDS__", ",".join("OBJECT_ID(?)" for _ in range(count))
    )


def _unique(rows, keys):
    result = {}
    for row in rows:
        key = tuple(row.get(name) for name in keys)
        if any(type(value) is not int or value <= 0 for value in key) or key in result:
            raise SourceConflict("Invalid or duplicate native column catalogue identity.")
        result[key] = row
    return result


def column_batch(cursor, scope, consume):
    """Preserve the original left-join semantics and checkpoint every native read."""
    facts = {}
    for category, statement in COLUMN_QUERIES.items():
        if category == "columns":
            facts[category] = []
            for offset in range(0, len(scope), COLUMN_BASE_WIDTH):
                part = scope[offset : offset + COLUMN_BASE_WIDTH]
                cursor.execute(column_query(len(part)), *part)
                facts[category].extend(consume(cursor))
        else:
            cursor.execute(statement, json.dumps(scope))
            facts[category] = consume(cursor)
    columns = facts["columns"]
    column_keys = _unique(columns, ("NativeObjectID", "Ordinal"))
    defaults = _unique(facts["defaults"], ("NativeDefaultID",))
    computed = _unique(facts["computed"], ("NativeObjectID", "Ordinal"))
    identity = _unique(facts["identity"], ("NativeObjectID", "Ordinal"))
    default_keys = {(row["NativeDefaultID"],) for row in columns if row["NativeDefaultID"]}
    if not (
        computed.keys() <= column_keys.keys()
        and identity.keys() <= column_keys.keys()
        and defaults.keys() <= default_keys
    ):
        raise SourceConflict("Column decoration returned an undeclared native identity.")
    result = []
    for original in columns:
        row = dict(original)
        key = (row.pop("NativeObjectID"), row["Ordinal"])
        default = defaults.get((row.pop("NativeDefaultID"),), {})
        for source, names in (
            (default, ("DefaultName", "DefaultDefinition")),
            (computed.get(key, {}), ("ComputedDefinition", "ComputedPersisted")),
            (identity.get(key, {}), ("IdentitySeed", "IdentityIncrement")),
        ):
            row.update((name, source.get(name)) for name in names)
        result.append(row)
    return result
