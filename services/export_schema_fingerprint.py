"""Opt-in application schema identity; never reinterpret legacy fingerprints.

Raw catalogues remain evidence. Only catalogue-proven generated constraint labels
and resolved allocation IDs are portable. This is not SQL text normalization.
"""

from collections import Counter, defaultdict
from copy import deepcopy
import hashlib

from services.export_execution_protocol import encode

FORMAT = "application_schema_v2"


class SchemaFingerprintError(ValueError):
    """A complete, consistent and supported schema observation is required."""


def _require(condition, message):
    if not condition:
        raise SchemaFingerprintError(message)


def _integer(value, *, minimum=0):
    _require(type(value) is int and value >= minimum, "Invalid catalogue ordinal/ID.")
    return value


def _flag(value):
    _require(type(value) in (int, bool) and value in (0, 1), "Invalid catalogue flag.")
    return bool(value)


def _unique(rows, keys):
    result = {}
    for row in rows:
        key = tuple(row[k] for k in keys)
        _require(key not in result, "Duplicate catalogue identity.")
        result[key] = row
    return result


def _multiset(rows):
    return Counter(encode(row) for row in rows)


def _ordered(rows):
    return sorted(rows, key=encode)


def _name(value, generated, module_text):
    _require(isinstance(value, str) and 1 <= len(value) <= 128, "Constraint name missing.")
    if _flag(generated):
        # A generated label used by module logic is not interchangeable. Conservatively
        # refuse this format rather than guessing which occurrence is executable SQL.
        _require(
            not any(value.casefold() in text for text in module_text),
            "Generated constraint label is referenced in module text.",
        )
        return {"kind": "system"}
    return {"kind": "named", "name": value}


def canonical_application_metadata(metadata, identity):
    """Return a versioned semantic envelope, failing closed on partial provenance.

    Column positions retain visible order. Constraint/index groups and duplicate
    multiplicity survive normalization. Permissions are deliberately not inputs:
    the caller must still run the independent unchanged permission comparator.
    """
    _validate_shapes(metadata, METADATA_FIELDS)
    _validate_shapes(identity, IDENTITY_FIELDS)
    _unique(metadata["objects"], ("ObjectName",))
    _unique(metadata["table_types"], ("TypeName", "Ordinal"))
    _unique(metadata["table_types"], ("TypeName", "ColumnName"))
    _unique(metadata["synonyms"], ("ObjectName",))
    _unique(metadata["triggers"], ("ObjectName", "TriggerName"))
    _unique(metadata["database_triggers"], ("TriggerName",))
    result = deepcopy(metadata)
    module_text = [
        r["ModuleDefinition"].casefold()
        for kind in ("objects", "triggers", "database_triggers")
        for r in metadata[kind]
        if isinstance(r["ModuleDefinition"], str)
    ]
    columns = _unique(identity["columns"], ("object_name", "column_name"))
    raw_columns = _unique(metadata["columns"], ("ObjectName", "ColumnName"))
    _require(set(columns) == set(raw_columns), "Column identity coverage differs.")
    column_ids = _unique(identity["columns"], ("object_name", "column_id"))
    by_object = defaultdict(list)
    for row in identity["columns"]:
        _integer(row["column_id"], minimum=1)
        by_object[row["object_name"]].append(row)
    positions = {}
    for name, rows in by_object.items():
        for position, row in enumerate(sorted(rows, key=lambda r: r["column_id"]), 1):
            _require(
                _integer(row["visible_position"], minimum=1) == position,
                "Visible column position is inconsistent.",
            )
            positions[(name, row["column_name"])] = position
    defaults = _unique(identity["default_constraints"], ("object_name", "column_name"))
    used_defaults = set()
    for row in result["columns"]:
        key = (row["ObjectName"], row["ColumnName"])
        proof = columns[key]
        _require(
            _integer(row["Ordinal"], minimum=1) == proof["column_id"]
            and _flag(row["IsComputed"]) == _flag(proof["is_computed"]),
            "Column provenance conflicts with metadata.",
        )
        row["Ordinal"] = positions[key]
        if row["DefaultName"] is None:
            _require(
                key not in defaults and row["DefaultDefinition"] is None,
                "Missing default identity.",
            )
        else:
            _require(key in defaults, "Default identity unavailable.")
            proof = defaults[key]
            _require(
                proof["name"] == row["DefaultName"]
                and proof["definition"] == row["DefaultDefinition"],
                "Default definition provenance differs.",
            )
            row["DefaultName"] = _name(proof["name"], proof["is_system_named"], module_text)
            used_defaults.add(key)
    _require(used_defaults == set(defaults), "Unexpected default identities.")

    indexes = _unique(identity["indexes"], ("object_name", "name"))
    index_ids = _unique(identity["indexes"], ("object_name", "index_id"))
    statistics = _unique(identity["filtered_statistics"], ("object_name", "name"))
    filtered_indexes = {key: row for key, row in indexes.items() if _flag(row["has_filter"])}
    _require(
        set(statistics) == set(filtered_indexes),
        "Standalone or missing filtered statistics are unsupported.",
    )
    for key, row in statistics.items():
        proof = filtered_indexes[key]
        _require(
            _integer(row["stats_id"], minimum=1) == proof["index_id"]
            and _flag(row["has_filter"])
            and not _flag(row["auto_created"])
            and not _flag(row["user_created"])
            and row["filter_definition"] == proof["filter_definition"],
            "Filtered statistics/index provenance differs.",
        )
    keys = _unique(identity["key_constraints"], ("object_name", "name"))
    groups = defaultdict(list)
    for row in metadata["indexes"]:
        groups[(row["ObjectName"], row["IndexName"])].append(row)
    _require(set(groups) == set(indexes), "Index identity coverage differs.")
    used_keys = set()
    result["indexes"] = []
    for key, rows in groups.items():
        proof = indexes[key]
        _integer(proof["index_id"])
        _unique(rows, ("Ordinal",))
        is_key = _flag(proof["is_primary_key"]) or _flag(proof["is_unique_constraint"])
        if is_key:
            _require(key in keys, "Key constraint provenance missing.")
            key_proof = keys[key]
            _require(
                _integer(key_proof["unique_index_id"], minimum=1) == proof["index_id"]
                and key_proof["type_desc"]
                == (
                    "PRIMARY_KEY_CONSTRAINT"
                    if _flag(proof["is_primary_key"])
                    else "UNIQUE_CONSTRAINT"
                ),
                "Key constraint/index relationship differs.",
            )
            label = _name(proof["name"], key_proof["is_system_named"], module_text)
            used_keys.add(key)
        else:
            _require(key not in keys, "Unexpected key constraint.")
            label = {"kind": "named", "name": proof["name"]}
        normalized = []
        for original in rows:
            _require(
                type(original["IndexType"]) is int
                and {0: "HEAP", 1: "CLUSTERED", 2: "NONCLUSTERED"}.get(original["IndexType"])
                == proof["type_desc"],
                "Unsupported or inconsistent index type.",
            )
            for raw, evidence in (
                ("IsUnique", "is_unique"),
                ("IsPrimaryKey", "is_primary_key"),
                ("IsUniqueConstraint", "is_unique_constraint"),
                ("Disabled", "is_disabled"),
                ("HasFilter", "has_filter"),
            ):
                _require(
                    _flag(original[raw]) == _flag(proof[evidence]), "Index flag provenance differs."
                )
            _require(
                original["FilterDefinition"] == proof["filter_definition"],
                "Index filter provenance differs.",
            )
            row = dict(original)
            row.pop("IndexName")
            normalized.append(row)
        result["indexes"].append(
            {"object": key[0], "identity": label, "rows": _ordered(normalized)}
        )
    _require(used_keys == set(keys), "Unexpected key constraint identities.")

    for section, raw_name in (("checks", "ConstraintName"), ("foreign_keys", "ConstraintName")):
        proofs = _unique(identity[section], ("object_name", "name"))
        groups = defaultdict(list)
        for row in metadata[section]:
            groups[(row["ObjectName"], row[raw_name])].append(row)
        _require(set(groups) == set(proofs), "Constraint identity coverage differs.")
        normalized = []
        for key, rows in groups.items():
            proof = proofs[key]
            if section == "checks":
                _require(
                    len(rows) == 1 and rows[0]["Definition"] == proof["definition"],
                    "Check provenance differs.",
                )
                for raw, field in (
                    ("Disabled", "is_disabled"),
                    ("Untrusted", "is_not_trusted"),
                    ("NotForReplication", "is_not_for_replication"),
                ):
                    _require(
                        _flag(rows[0][raw]) == _flag(proof[field]), "Check flag provenance differs."
                    )
            else:
                _unique(rows, ("Ordinal",))
                _require(
                    all(r["ReferencedObject"] == proof["referenced_object"] for r in rows),
                    "Foreign key target differs.",
                )
            normalized.append(
                {
                    "object": key[0],
                    "identity": _name(key[1], proof["is_system_named"], module_text),
                    "rows": _ordered(
                        [{k: v for k, v in row.items() if k != raw_name} for row in rows]
                    ),
                    **(
                        {"parent_column": proof["parent_column_name"]}
                        if section == "checks"
                        else {}
                    ),
                }
            )
        result[section] = normalized

    raw_dependencies = []
    dependencies = []
    for row in identity["dependencies"]:
        raw_dependencies.append(
            {
                "ObjectName": row["object_name"],
                "MinorID": row["referencing_minor_id"],
                "ServerName": row["referenced_server_name"],
                "DatabaseName": row["referenced_database_name"],
                "SchemaName": row["referenced_schema_name"],
                "EntityName": row["referenced_entity_name"],
                "ReferencedMinorID": row["referenced_minor_id"],
                "SchemaBound": row["is_schema_bound_reference"],
                "CallerDependent": row["is_caller_dependent"],
                "Ambiguous": row["is_ambiguous"],
            }
        )
        minor = _integer(row["referencing_minor_id"])
        reference_minor = _integer(row["referenced_minor_id"])
        referencing_class = _integer(row["referencing_class"], minimum=1)
        referenced_class = _integer(row["referenced_class"], minimum=1)
        if referencing_class == 1:
            _require(
                row["referencing_class_desc"] == "OBJECT_OR_COLUMN",
                "Dependency class contradicts description.",
            )
            origin = {"kind": "object", "name": None}
            if minor:
                proof = column_ids.get((row["object_name"], minor))
                _require(
                    proof is not None and proof["column_name"] == row["candidate_column_name"],
                    "Dependent column is unresolved.",
                )
                origin = {"kind": "column", "name": proof["column_name"]}
        elif referencing_class == 7:
            _require(row["referencing_class_desc"] == "INDEX", "Dependency index class differs.")
            proof = index_ids.get((row["object_name"], minor))
            _require(
                proof is not None
                and _flag(proof["has_filter"])
                and _flag(row["candidate_index_filtered"])
                and proof["name"] == row["candidate_index_name"]
                and proof["filter_definition"] == row["candidate_index_filter"],
                "Dependent filtered index is unresolved or inconsistent.",
            )
            origin = {"kind": "index", "name": proof["name"]}
        else:
            raise SchemaFingerprintError("Unsupported referencing dependency class.")
        _require(
            (referenced_class, row["referenced_class_desc"])
            in ((1, "OBJECT_OR_COLUMN"), (6, "TYPE")),
            "Unsupported referenced dependency class.",
        )
        _require(
            referenced_class == 1 or reference_minor == 0,
            "A type reference cannot identify a column.",
        )
        if reference_minor:
            _require(
                isinstance(row["referenced_column_name"], str) and row["referenced_column_name"],
                "Referenced column is unresolved.",
            )
        else:
            _require(
                row["referenced_column_name"] is None, "Whole-object reference has a column label."
            )
        item = dict(raw_dependencies[-1])
        item.pop("MinorID")
        item.pop("ReferencedMinorID")
        item.update(
            Origin=origin,
            ReferencedClass=referenced_class,
            ReferencedColumn=row["referenced_column_name"],
        )
        dependencies.append(item)
    _require(
        _multiset(raw_dependencies) == _multiset(metadata["dependencies"]),
        "Dependency provenance coverage differs.",
    )
    result["dependencies"] = dependencies
    return {"format": FORMAT, "metadata": {name: _ordered(rows) for name, rows in result.items()}}


def application_metadata_fingerprint(metadata, identity):
    return hashlib.sha256(encode(canonical_application_metadata(metadata, identity))).hexdigest()


def _validate_shapes(value, fields):
    _require(
        isinstance(value, dict) and set(value) == set(fields),
        "Incomplete schema catalogue categories.",
    )
    for name, expected in fields.items():
        _require(
            isinstance(value[name], list) and len(value[name]) <= 100000,
            "Catalogue collection is invalid or unbounded.",
        )
        for row in value[name]:
            _require(
                isinstance(row, dict) and set(row) == set(expected),
                "Unexpected catalogue row shape.",
            )
            _require(
                all(v is None or type(v) in (str, int, bool) for v in row.values()),
                "Unsupported catalogue value type.",
            )
    # Reject unsupported values (including non-finite numbers) through the shared codec.
    encode(value)


# Explicit query schemas appended by the implementation preparation step.

METADATA_FIELDS = {
    "checks": [
        "ConstraintName",
        "Definition",
        "Disabled",
        "NotForReplication",
        "ObjectName",
        "Untrusted",
    ],
    "columns": [
        "Collation",
        "ColumnName",
        "ComputedDefinition",
        "ComputedPersisted",
        "DefaultDefinition",
        "DefaultName",
        "GeneratedAlways",
        "IdentityIncrement",
        "IdentitySeed",
        "IsComputed",
        "IsIdentity",
        "IsRowGuid",
        "IsSparse",
        "MaxLength",
        "Nullable",
        "ObjectName",
        "Ordinal",
        "Precision",
        "Scale",
        "TypeName",
    ],
    "database_triggers": ["TriggerName", "Disabled", "ModuleDefinition", "ExecuteAsPrincipal"],
    "dependencies": [
        "Ambiguous",
        "CallerDependent",
        "DatabaseName",
        "EntityName",
        "MinorID",
        "ObjectName",
        "ReferencedMinorID",
        "SchemaBound",
        "SchemaName",
        "ServerName",
    ],
    "foreign_keys": [
        "ColumnName",
        "ConstraintName",
        "DeleteAction",
        "Disabled",
        "NotForReplication",
        "ObjectName",
        "Ordinal",
        "ReferencedColumn",
        "ReferencedObject",
        "Untrusted",
        "UpdateAction",
    ],
    "indexes": [
        "ColumnName",
        "DescendingKey",
        "Disabled",
        "FilterDefinition",
        "HasFilter",
        "Hypothetical",
        "IgnoreDuplicateKey",
        "IncludedColumn",
        "IndexName",
        "IndexType",
        "IsPrimaryKey",
        "IsUnique",
        "IsUniqueConstraint",
        "KeyOrdinal",
        "ObjectName",
        "Ordinal",
        "PartitionOrdinal",
    ],
    "objects": [
        "AnsiNulls",
        "ExecuteAsPrincipal",
        "MemoryOptimized",
        "ModuleDefinition",
        "ObjectName",
        "ObjectType",
        "QuotedIdentifier",
        "TemporalType",
    ],
    "synonyms": ["ObjectName", "Target"],
    "table_types": [
        "Collation",
        "ColumnName",
        "ColumnType",
        "MaxLength",
        "Nullable",
        "Ordinal",
        "Precision",
        "Scale",
        "TypeName",
    ],
    "triggers": [
        "ObjectName",
        "TriggerName",
        "Disabled",
        "InsteadOf",
        "NotForReplication",
        "ModuleDefinition",
        "AnsiNulls",
        "QuotedIdentifier",
        "ExecuteAsPrincipal",
    ],
}

IDENTITY_FIELDS = {
    "checks": [
        "definition",
        "is_disabled",
        "is_not_for_replication",
        "is_not_trusted",
        "is_system_named",
        "name",
        "object_name",
        "parent_column_name",
    ],
    "columns": [
        "column_id",
        "column_name",
        "is_computed",
        "max_column_id_used",
        "object_name",
        "visible_position",
    ],
    "default_constraints": ["column_name", "definition", "is_system_named", "name", "object_name"],
    "dependencies": [
        "candidate_column_name",
        "candidate_index_filter",
        "candidate_index_filtered",
        "candidate_index_name",
        "candidate_statistics_filter",
        "candidate_statistics_filtered",
        "candidate_statistics_name",
        "is_ambiguous",
        "is_caller_dependent",
        "is_schema_bound_reference",
        "object_name",
        "referenced_class",
        "referenced_class_desc",
        "referenced_column_name",
        "referenced_database_name",
        "referenced_entity_name",
        "referenced_minor_id",
        "referenced_schema_name",
        "referenced_server_name",
        "referencing_class",
        "referencing_class_desc",
        "referencing_minor_id",
    ],
    "filtered_statistics": [
        "auto_created",
        "filter_definition",
        "has_filter",
        "name",
        "object_name",
        "stats_id",
        "user_created",
    ],
    "foreign_keys": ["is_system_named", "name", "object_name", "referenced_object"],
    "indexes": [
        "filter_definition",
        "has_filter",
        "index_id",
        "is_disabled",
        "is_primary_key",
        "is_unique",
        "is_unique_constraint",
        "name",
        "object_name",
        "type_desc",
    ],
    "key_constraints": ["is_system_named", "name", "object_name", "type_desc", "unique_index_id"],
}
