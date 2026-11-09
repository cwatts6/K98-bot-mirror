"""Exercise the emitted preview query and optionally compile it on local tempdb."""

from contextlib import contextmanager
import os
from unittest.mock import Mock

import pytest

from kvk.dal import kvk_admin_dal, new_source_import_dal, season_source_dal


def preview_statement(monkeypatch):
    cursor = Mock()

    @contextmanager
    def transaction(_):
        yield cursor

    monkeypatch.setattr(new_source_import_dal, "transaction", transaction)
    monkeypatch.setattr(new_source_import_dal, "lock_scope", Mock())
    monkeypatch.setattr(new_source_import_dal, "rows", lambda _: [])
    monkeypatch.setattr(
        season_source_dal, "lock_season", lambda *_: {"SourceKey": "snapshot_report_v1"}
    )
    assert kvk_admin_dal.fetch_source_windows(16, connect=Mock()) == []
    cursor.execute.assert_called_once()
    return cursor.execute.call_args.args


def test_preview_quotes_reserved_alias_and_preserves_bound_scope(monkeypatch):
    query, source, season = preview_statement(monkeypatch)
    assert "pub.EligibleCount AS [RowCount]" in query
    assert query.count("?") == 2
    assert (source, season) == ("snapshot_report_v1", 16)


@pytest.mark.skipif(
    os.environ.get("K98_READ_ONLY_SQL_COMPILER") != "LOCAL_TEMPDB_COMPILE_ONLY",
    reason="Opt-in local tempdb metadata compiler; no application SQL or writes",
)
def test_actual_preview_compiles_with_expected_result_columns(monkeypatch):
    import pyodbc

    query, _, _ = preview_statement(monkeypatch)
    # Referenced columns/types checked against the authoritative KVK.Source* DDL.
    # Table variables are analyzed only; no persistent objects or application rows.
    shapes = {
        "SourcePeriod": "PeriodID uniqueidentifier,PeriodKey varchar(128),PeriodKind varchar(32),SourceKey varchar(32),KVK_NO int",
        "SourceCompleteSelection": "SourceKey varchar(32),KVK_NO int,PeriodID uniqueidentifier,UpdateID uniqueidentifier,PublicationID uniqueidentifier,PublicSelectionVersion bigint",
        "SourcePublication": "PublicationID uniqueidentifier,StartScanID int,EndScanID int,ConfigVersionID uniqueidentifier,PeriodState varchar(32),BuildState varchar(32),EligibleCount int,StartRevisionID uniqueidentifier,EndRevisionID uniqueidentifier",
        "SourceConfigVersion": "ConfigVersionID uniqueidentifier,ConfigVersion int",
        "SourceConfigRequest": "DesiredConfigVersionID uniqueidentifier,SourceKey varchar(32),KVK_NO int,PeriodID uniqueidentifier,RequestState varchar(32)",
        "SourceWindowConfig": "WindowName nvarchar(40),StartScanID int,EndScanID int,ConfigVersionID uniqueidentifier,SourceKey varchar(32),KVK_NO int,PeriodKey varchar(128)",
        "SourceUpdate": "UpdateID uniqueidentifier,UpdateState varchar(32),SourceKey varchar(32),KVK_NO int,PeriodID uniqueidentifier,ConfigVersionID uniqueidentifier,BaseUpdateID uniqueidentifier,ConfirmedUTC datetime2(0)",
        "SourceObservationRevision": "RevisionID uniqueidentifier,ObservationID uniqueidentifier",
        "SourceObservation": "ObservationID uniqueidentifier,ScanStartUTC datetime2(0)",
    }
    declarations = ""
    for table, columns in shapes.items():
        declarations += f"DECLARE @{table} TABLE ({columns}); "
        query = query.replace(f"KVK.{table} ", f"@{table} ")
    assert "KVK." not in query
    query = query.replace("?", "@source", 1).replace("?", "@season", 1)
    with pyodbc.connect(
        r"DRIVER={ODBC Driver 17 for SQL Server};SERVER=lpc:localhost\K98DEV;"
        "DATABASE=tempdb;Trusted_Connection=yes;TrustServerCertificate=yes",
        autocommit=True,
        timeout=5,
    ) as connection:
        server, database = (
            connection.cursor()
            .execute("SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')),DB_NAME()")
            .fetchone()
        )
        assert server.lower() == r"9sx2vf4\k98dev" and database == "tempdb"
        connection.timeout = 5
        cursor = connection.cursor().execute(
            "EXEC sys.sp_describe_first_result_set @tsql=?, @params=?",
            declarations + query,
            "@source varchar(32),@season int",
        )
        names = [column[0] for column in cursor.description]
        columns = [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]
    assert len(columns) == 20
    row_count = next(column for column in columns if column["name"] == "RowCount")
    assert row_count["system_type_name"] == "int"
