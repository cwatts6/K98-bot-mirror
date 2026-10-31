"""Portable allocation identities must never hide real schema or permission drift."""

from copy import deepcopy
from unittest.mock import Mock

import pytest

from services.export_schema_fingerprint import (
    FORMAT,
    SchemaFingerprintError,
    application_metadata_fingerprint,
)


def column(name, ordinal, default=None):
    return dict(
        ObjectName="dbo.Fixture",
        Ordinal=ordinal,
        ColumnName=name,
        TypeName="sys.int",
        MaxLength=4,
        Precision=10,
        Scale=0,
        Collation=None,
        Nullable=False,
        IsIdentity=False,
        IsComputed=False,
        IsRowGuid=False,
        IsSparse=False,
        GeneratedAlways=0,
        DefaultName=default,
        DefaultDefinition="((0))" if default else None,
        ComputedDefinition=None,
        ComputedPersisted=None,
        IdentitySeed=None,
        IdentityIncrement=None,
    )


def index(name, primary, column_name):
    return dict(
        ObjectName="dbo.Fixture",
        IndexName=name,
        IndexType=1 if primary else 2,
        IsUnique=primary,
        IsPrimaryKey=primary,
        IsUniqueConstraint=False,
        Disabled=False,
        Hypothetical=False,
        IgnoreDuplicateKey=False,
        HasFilter=not primary,
        FilterDefinition=None if primary else "([Value]>(0))",
        Ordinal=1,
        ColumnName=column_name,
        KeyOrdinal=1,
        PartitionOrdinal=0,
        DescendingKey=False,
        IncludedColumn=False,
    )


def fixture():
    metadata = dict(
        objects=[
            dict(
                ObjectName="dbo.Fixture",
                ObjectType="U",
                ModuleDefinition=None,
                AnsiNulls=None,
                QuotedIdentifier=None,
                ExecuteAsPrincipal=None,
                MemoryOptimized=False,
                TemporalType=0,
            )
        ],
        columns=[column("Id", 1), column("Value", 3, "DF__source")],
        indexes=[index("PK__source", True, "Id"), index("IX_Value", False, "Value")],
        checks=[
            dict(
                ObjectName="dbo.Fixture",
                ConstraintName="CK_Value",
                Definition="([Value]>=(0))",
                Disabled=False,
                Untrusted=False,
                NotForReplication=False,
            )
        ],
        foreign_keys=[
            dict(
                ObjectName="dbo.Fixture",
                ConstraintName="FK__source",
                Ordinal=1,
                ColumnName="Value",
                ReferencedObject="dbo.Parent",
                ReferencedColumn="Id",
                DeleteAction=0,
                UpdateAction=0,
                Disabled=False,
                Untrusted=False,
                NotForReplication=False,
            )
        ],
        triggers=[],
        table_types=[],
        synonyms=[],
        database_triggers=[],
        dependencies=[
            dict(
                ObjectName="dbo.Fixture",
                MinorID=7,
                ServerName=None,
                DatabaseName=None,
                SchemaName="dbo",
                EntityName="Fixture",
                ReferencedMinorID=3,
                SchemaBound=True,
                CallerDependent=False,
                Ambiguous=False,
            )
        ],
    )
    identity = dict(
        columns=[
            dict(
                object_name="dbo.Fixture",
                column_id=i,
                column_name=n,
                visible_position=p,
                max_column_id_used=3,
                is_computed=False,
            )
            for i, n, p in [(1, "Id", 1), (3, "Value", 2)]
        ],
        default_constraints=[
            dict(
                object_name="dbo.Fixture",
                column_name="Value",
                name="DF__source",
                is_system_named=True,
                definition="((0))",
            )
        ],
        key_constraints=[
            dict(
                object_name="dbo.Fixture",
                name="PK__source",
                type_desc="PRIMARY_KEY_CONSTRAINT",
                is_system_named=True,
                unique_index_id=1,
            )
        ],
        foreign_keys=[
            dict(
                object_name="dbo.Fixture",
                name="FK__source",
                is_system_named=True,
                referenced_object="dbo.Parent",
            )
        ],
        checks=[
            dict(
                object_name="dbo.Fixture",
                name="CK_Value",
                is_system_named=False,
                parent_column_name=None,
                definition="([Value]>=(0))",
                is_disabled=False,
                is_not_trusted=False,
                is_not_for_replication=False,
            )
        ],
        indexes=[
            dict(
                object_name="dbo.Fixture",
                index_id=i,
                name=n,
                type_desc=t,
                is_unique=pk,
                is_primary_key=pk,
                is_unique_constraint=False,
                is_disabled=False,
                has_filter=not pk,
                filter_definition=None if pk else "([Value]>(0))",
            )
            for i, n, t, pk in [
                (1, "PK__source", "CLUSTERED", True),
                (7, "IX_Value", "NONCLUSTERED", False),
            ]
        ],
        filtered_statistics=[
            dict(
                object_name="dbo.Fixture",
                stats_id=7,
                name="IX_Value",
                auto_created=False,
                user_created=False,
                has_filter=True,
                filter_definition="([Value]>(0))",
            )
        ],
        dependencies=[
            dict(
                object_name="dbo.Fixture",
                referencing_minor_id=7,
                referencing_class=7,
                referencing_class_desc="INDEX",
                candidate_column_name=None,
                candidate_index_name="IX_Value",
                candidate_index_filtered=True,
                candidate_index_filter="([Value]>(0))",
                candidate_statistics_name="IX_Value",
                candidate_statistics_filtered=True,
                candidate_statistics_filter="([Value]>(0))",
                referenced_class=1,
                referenced_class_desc="OBJECT_OR_COLUMN",
                referenced_server_name=None,
                referenced_database_name=None,
                referenced_schema_name="dbo",
                referenced_entity_name="Fixture",
                referenced_minor_id=3,
                referenced_column_name="Value",
                is_schema_bound_reference=True,
                is_caller_dependent=False,
                is_ambiguous=False,
            )
        ],
    )
    return metadata, identity


def rebuilt():
    metadata, identity = fixture()
    metadata["columns"][1].update(Ordinal=2, DefaultName="DF__rebuilt")
    identity["columns"][1].update(column_id=2, max_column_id_used=2)
    identity["columns"][0]["max_column_id_used"] = 2
    identity["default_constraints"][0]["name"] = "DF__rebuilt"
    metadata["indexes"][0]["IndexName"] = "PK__rebuilt"
    identity["indexes"][0]["name"] = "PK__rebuilt"
    identity["key_constraints"][0]["name"] = "PK__rebuilt"
    metadata["foreign_keys"][0]["ConstraintName"] = "FK__rebuilt"
    identity["foreign_keys"][0]["name"] = "FK__rebuilt"
    metadata["dependencies"][0].update(MinorID=2, ReferencedMinorID=2)
    identity["dependencies"][0].update(
        referencing_minor_id=2, referenced_minor_id=2, candidate_column_name="Value"
    )
    identity["indexes"][1]["index_id"] = 2
    identity["filtered_statistics"][0]["stats_id"] = 2
    return metadata, identity


def test_rebuilt_schema_and_result_order_have_identical_fingerprint_without_mutating_inputs():
    original = fixture()
    other = rebuilt()
    preserved = deepcopy(other)
    assert application_metadata_fingerprint(*original) == application_metadata_fingerprint(*other)
    assert other == preserved
    for section in other:
        for rows in section.values():
            rows.reverse()
    assert application_metadata_fingerprint(*original) == application_metadata_fingerprint(*other)


@pytest.mark.parametrize(
    "section,field,value",
    [
        ("columns", "TypeName", "sys.bigint"),
        ("columns", "MaxLength", 8),
        ("columns", "Precision", 9),
        ("columns", "Scale", 1),
        ("columns", "Nullable", True),
        ("columns", "Collation", "Latin1_General_BIN2"),
        ("columns", "IsIdentity", True),
        ("columns", "IdentitySeed", "2"),
        ("columns", "ComputedDefinition", "([Id]+1)"),
        ("indexes", "DescendingKey", True),
        ("indexes", "IncludedColumn", True),
        ("indexes", "PartitionOrdinal", 1),
        ("indexes", "IgnoreDuplicateKey", True),
        ("indexes", "Hypothetical", True),
        ("foreign_keys", "DeleteAction", 1),
        ("foreign_keys", "UpdateAction", 1),
        ("foreign_keys", "Untrusted", True),
        ("foreign_keys", "Disabled", True),
        ("foreign_keys", "ReferencedColumn", "Other"),
        ("objects", "ModuleDefinition", "CREATE TABLE changed"),
        ("objects", "ExecuteAsPrincipal", -2),
    ],
)
def test_material_shape_changes_never_compare_equal(section, field, value):
    original = fixture()
    altered = deepcopy(original)
    altered[0][section][0][field] = value
    try:
        actual = application_metadata_fingerprint(*altered)
    except SchemaFingerprintError:
        return
    assert actual != application_metadata_fingerprint(*original)


def test_changed_definition_even_with_consistent_provenance_is_rejected_by_hash():
    original = fixture()
    altered = deepcopy(original)
    altered[0]["columns"][1]["DefaultDefinition"] = "((1))"
    altered[1]["default_constraints"][0]["definition"] = "((1))"
    assert application_metadata_fingerprint(*original) != application_metadata_fingerprint(*altered)


def test_explicit_generated_looking_name_is_still_name_sensitive():
    original, altered = fixture(), rebuilt()
    for pair in (original, altered):
        pair[1]["default_constraints"][0]["is_system_named"] = False
    assert application_metadata_fingerprint(*original) != application_metadata_fingerprint(*altered)


@pytest.mark.parametrize(
    "kind",
    [
        "missing",
        "extra",
        "duplicate",
        "boolean_id",
        "unresolved",
        "unknown_class",
        "stats_confusion",
        "referenced_type_column",
    ],
)
def test_incomplete_or_inconsistent_identity_fails_closed(kind):
    metadata, identity = fixture()
    if kind == "missing":
        identity["default_constraints"] = []
    elif kind == "extra":
        identity["columns"][0]["unreviewed"] = 1
    elif kind == "duplicate":
        identity["columns"].append(dict(identity["columns"][0]))
    elif kind == "boolean_id":
        identity["columns"][0]["column_id"] = True
    elif kind == "unresolved":
        identity["dependencies"][0]["referenced_column_name"] = None
    elif kind == "unknown_class":
        identity["dependencies"][0]["referencing_class"] = 99
    elif kind == "stats_confusion":
        identity["indexes"][1]["name"] = "OtherIndex"
    else:
        identity["dependencies"][0].update(referenced_class=6, referenced_class_desc="TYPE")
    with pytest.raises(SchemaFingerprintError):
        application_metadata_fingerprint(metadata, identity)


def test_generated_label_used_by_module_is_not_portable():
    metadata, identity = fixture()
    metadata["objects"][0]["ModuleDefinition"] = "EXEC sp_rename 'PK__source', 'new'"
    with pytest.raises(SchemaFingerprintError, match="module text"):
        application_metadata_fingerprint(metadata, identity)


def test_two_identical_generated_constraints_retain_multiplicity():
    original = fixture()
    altered = deepcopy(original)
    row = dict(altered[0]["foreign_keys"][0], ConstraintName="FK__another")
    altered[0]["foreign_keys"].append(row)
    altered[1]["foreign_keys"].append(dict(altered[1]["foreign_keys"][0], name="FK__another"))
    assert application_metadata_fingerprint(*original) != application_metadata_fingerprint(*altered)


def portable_contract(monkeypatch):
    from kvk.dal.new_source_import_dal import digest
    from services import export_execution_dal as dal

    metadata, identity = fixture()
    sources = [dict(name="dbo.Fixture", type="U", path="fixture.sql", sha256="a" * 64)]
    monkeypatch.setattr(dal, "APPLICATION_SCHEMA_SOURCE_HASH", digest(sources).hex())
    monkeypatch.setattr(dal, "application_activation_scope", lambda: ["dbo.Fixture"])
    observed = dict(
        version=2,
        target=dict(
            ServerName="lab", DatabaseName="ROK_TRACKER", Principal="app", ViewDefinition=1
        ),
        metadata=metadata,
        schema_identity=identity,
        schema_permissions=[],
        object_permissions=[],
        column_permissions=[],
    )
    approved = dict(
        version=3,
        server="lab",
        database="ROK_TRACKER",
        principal="app",
        sources=sources,
        dynamic_objects=[],
        metadata_hash=application_metadata_fingerprint(metadata, identity),
        fingerprint_format=FORMAT,
        permissions_hash=digest(
            {
                k: observed[k]
                for k in ("schema_permissions", "object_permissions", "column_permissions")
            }
        ).hex(),
        scope_hash=dal.APPLICATION_ACTIVATION_SCOPE_HASH,
        review_id="26a303f7-e8b6-4be6-9dce-43086c78d98e",
    )
    return observed, approved


def test_new_contract_accepts_equivalent_schema_and_still_checks_permissions(monkeypatch):
    from kvk.dal.new_source_import_dal import SourceConflict
    from services.export_runtime_composition import verify_application_installation_contract

    observed, approved = portable_contract(monkeypatch)
    observed["metadata"], observed["schema_identity"] = rebuilt()
    assert verify_application_installation_contract(observed, approved)
    observed["schema_permissions"].append(
        dict(SchemaName="dbo", PermissionName="CONTROL", Subentity="")
    )
    with pytest.raises(SourceConflict, match="permissions"):
        verify_application_installation_contract(observed, approved)


@pytest.mark.parametrize("damage", ["version", "format", "scope", "target", "raw_only"])
def test_new_contract_never_falls_back_or_accepts_wrong_scope(monkeypatch, damage):
    from kvk.dal.new_source_import_dal import SourceConflict
    from services.export_runtime_composition import verify_application_installation_contract

    observed, approved = portable_contract(monkeypatch)
    if damage == "version":
        observed["version"] = 1
    elif damage == "format":
        approved["fingerprint_format"] = "guess"
    elif damage == "scope":
        approved["scope_hash"] = "0" * 64
    elif damage == "target":
        observed["target"]["DatabaseName"] = "other"
    else:
        observed.pop("schema_identity")
    with pytest.raises(SourceConflict):
        verify_application_installation_contract(observed, approved)


def test_new_reader_requires_explicit_supported_format_and_pinned_scope_before_sql():
    from kvk.dal.new_source_import_dal import SourceConflict
    from services.export_execution_dal import application_installation_snapshot

    cursor = Mock()
    with pytest.raises(SourceConflict):
        application_installation_snapshot(cursor, metadata_format=FORMAT)
    with pytest.raises(SourceConflict):
        application_installation_snapshot(cursor, scope=["dbo.Fixture"], metadata_format="unknown")
    cursor.execute.assert_not_called()


def test_historical_source_bridge_authenticates_bytes_without_authorizing_updater(tmp_path):
    from pathlib import Path

    from scripts import prepare_k98_update as update
    from tests.updater_source_assertions import before_portable_fingerprint_hash

    root = Path(__file__).resolve().parents[1]
    path = "services/export_execution_dal.py"
    assert before_portable_fingerprint_hash(root, path) != update.sha256(
        (root / path).read_bytes().replace(b"\r\n", b"\n")
    )
    # The new security-sensitive module remains refused without installed authority.
    with pytest.raises(ValueError, match="non-routine release"):
        update.check_source_only(["services/export_schema_fingerprint.py"])
    fixture_path = "tests/fixtures/portable_fingerprint_source_pairs.json"
    (tmp_path / fixture_path).parent.mkdir(parents=True)
    (tmp_path / fixture_path).write_bytes((root / fixture_path).read_bytes())
    (tmp_path / path).parent.mkdir(parents=True)
    (tmp_path / path).write_bytes(b"unreviewed successor")
    with pytest.raises(AssertionError):
        before_portable_fingerprint_hash(tmp_path, path)
