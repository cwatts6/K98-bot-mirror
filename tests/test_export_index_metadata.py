"""Scoped application catalogue reads preserve the startup fingerprint contract."""

import json

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services import export_execution_dal as dal
from services.export_schema_fingerprint import FORMAT


class CatalogueCursor:
    def __init__(self, *, visible=1, fail_indexes=False):
        self.visible = visible
        self.fail_indexes = fail_indexes
        self.calls = []
        self.description = []
        self.result = []

    def execute(self, sql, *parameters):
        self.calls.append((sql, parameters))
        if "AS ViewDefinition" in sql:
            names = ["ServerName", "DatabaseName", "Principal", "ViewDefinition"]
            self.result = [("LAB", "Fixture", "Application", self.visible)]
        elif "FROM sys.indexes" in sql and "AS ObjectName" in sql:
            if self.fail_indexes:
                raise RuntimeError("metadata read refused")
            names = ["ObjectName", "IndexName", "Ordinal", "ColumnName", "IncludedColumn"]
            self.result = [
                ("dbo.Heap", None, None, None, None),
                ("dbo.Composite", "IX", 1, "Key", False),
                ("dbo.Composite", "IX", 2, "Included", True),
            ]
        elif "FROM sys.indexes" in sql and "AS object_name" in sql:
            names = ["object_name", "index_id", "name", "has_filter", "filter_definition"]
            self.result = [
                ("dbo.Heap", 0, None, False, None),
                ("dbo.Composite", 4, "IX", True, "([Key] IS NOT NULL)"),
            ]
        else:
            names, self.result = [], []
        self.description = [(name,) for name in names]
        return self

    def fetchone(self):
        return self.result[0] if self.result else None

    def fetchall(self):
        return self.result


@pytest.mark.parametrize(
    "scope",
    [
        [],
        ["dbo.Heap", "dbo.Composite"],
        ["dbo.Heap", "dbo.Heap", "dbo.Missing"],
        ["dbo.Heap'); DROP TABLE dbo.Heap;--"],
    ],
)
@pytest.mark.parametrize("metadata_format", [None, FORMAT])
def test_scoped_index_reads_bind_scope_and_preserve_rows(scope, metadata_format):
    cursor = CatalogueCursor()
    result = dal.application_installation_snapshot(
        cursor, scope=scope, metadata_format=metadata_format
    )
    materialized = [(sql, params) for sql, params in cursor.calls if "DECLARE @required" in sql]
    assert len(materialized) == (1 if metadata_format is None else 2)
    for sql, params in materialized:
        assert params == (json.dumps(scope),)
        assert sql.count("?") == 1
        assert "SELECT DISTINCT OBJECT_ID(value)" in sql
        assert "WHERE OBJECT_ID(value) IS NOT NULL" in sql
        assert "JOIN sys.objects o ON o.object_id=i.object_id" in sql
        assert "JOIN sys.schemas s ON s.schema_id=o.schema_id" in sql
        assert "i.object_id IN (SELECT object_id FROM @required)" in sql
        assert "DROP TABLE" not in sql
    assert result["metadata"]["indexes"] == [
        {
            "ObjectName": "dbo.Heap",
            "IndexName": None,
            "Ordinal": None,
            "ColumnName": None,
            "IncludedColumn": None,
        },
        {
            "ObjectName": "dbo.Composite",
            "IndexName": "IX",
            "Ordinal": 1,
            "ColumnName": "Key",
            "IncludedColumn": False,
        },
        {
            "ObjectName": "dbo.Composite",
            "IndexName": "IX",
            "Ordinal": 2,
            "ColumnName": "Included",
            "IncludedColumn": True,
        },
    ]
    if metadata_format is not None:
        assert result["schema_identity"]["indexes"][1] == {
            "object_name": "dbo.Composite",
            "index_id": 4,
            "name": "IX",
            "has_filter": True,
            "filter_definition": "([Key] IS NOT NULL)",
        }
        assert result["version"] == 2
    else:
        assert "schema_identity" not in result and result["version"] == 1


def test_unscoped_catalogue_retains_legacy_query():
    cursor = CatalogueCursor()
    dal.application_installation_snapshot(cursor)
    assert not any("DECLARE @required" in sql for sql, _ in cursor.calls)
    index_sql, params = next(
        (sql, params) for sql, params in cursor.calls if "FROM sys.indexes" in sql
    )
    assert index_sql.endswith(dal._METADATA_QUERIES["indexes"])
    assert params == ()


@pytest.mark.parametrize("visible", [None, 0])
def test_metadata_visibility_fails_before_catalogue_reads(visible):
    cursor = CatalogueCursor(visible=visible)
    with pytest.raises(SourceConflict, match="metadata must be visible"):
        dal.application_installation_snapshot(cursor, scope=["dbo.Heap"], metadata_format=FORMAT)
    assert len(cursor.calls) == 1


def test_failed_index_query_is_not_retried_or_fallen_back():
    cursor = CatalogueCursor(fail_indexes=True)
    with pytest.raises(RuntimeError, match="metadata read refused"):
        dal.application_installation_snapshot(cursor, scope=["dbo.Heap"], metadata_format=FORMAT)
    assert len([sql for sql, _ in cursor.calls if "FROM sys.indexes" in sql]) == 1
    assert "DECLARE @required" in cursor.calls[-1][0]
