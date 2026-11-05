"""Read-only local SQL regression for the release contract's mixed collations."""

from copy import deepcopy
import os

import pytest

from scripts.rehearse_p0a_dependency_order import order_dependencies, order_object_permissions


@pytest.mark.skipif(
    os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Local SQL opt-in required"
)
def test_dependency_order_matches_observer_collations_and_preserves_duplicates():
    pyodbc = pytest.importorskip("pyodbc")
    with pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};SERVER=lpc:localhost\\K98DEV;"
        "DATABASE=master;Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;",
        autocommit=True,
        timeout=5,
    ) as connection:
        assert tuple(
            connection.execute(
                "SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')),DB_NAME()"
            ).fetchone()
        ) == ("9SX2VF4\\K98DEV", "master")
        rows = [
            dict(
                ObjectName=owner,
                MinorID=0,
                ServerName=None,
                DatabaseName=None,
                SchemaName=schema,
                EntityName=entity,
                ReferencedMinorID=0,
                SchemaBound=False,
                CallerDependent=False,
                Ambiguous=False,
            )
            for owner, schema, entity in (
                ("KVK.root", "KVK", "Alpha"),
                ("KVK.root", "dbo", "Beta"),
                ("KVK.root", "dbo", "alpha"),
                ("dbo.root", "dbo", "alpha"),
                ("KVK.root", "dbo", "alpha"),
            )
        ]
        before = deepcopy(rows)
        actual = order_dependencies(connection.cursor(), rows)
        assert rows == before
        assert actual == [rows[2], rows[4], rows[1], rows[0], rows[3]]
        assert order_dependencies(connection.cursor(), actual) == actual
        permissions = [
            dict(ObjectName="KVK.source", PermissionName="SELECT", Subentity=column)
            for column in ("IngestToken", "campid", "GovernorID")
        ]
        assert order_object_permissions(connection.cursor(), permissions) == [
            permissions[1],
            permissions[2],
            permissions[0],
        ]


def test_dependency_order_rejects_a_query_that_changes_evidence():
    class Cursor:
        def execute(self, query, raw):
            assert query.startswith("SELECT value FROM OPENJSON(?)")

        def fetchall(self):
            return []

    with pytest.raises(ValueError, match="preserve every expected row"):
        order_dependencies(Cursor(), [{"ObjectName": "dbo.original"}])
