"""Real driver lifecycle in a unique disposable local database, never business data."""

import pytest

from event_calendar.sql_lifecycle import SqlOutcome
from stats.profile_cache_repository import read_profiles


def test_native_profile_rollback_close_and_retained_failed_close(snapshot_database):
    import pyodbc

    db = snapshot_database
    setup = pyodbc.connect(db.connection_string, autocommit=True, timeout=5)
    setup.timeout = 5
    handles = []
    try:
        assert (
            setup.execute(
                "SELECT used_log_space_in_percent FROM sys.dm_db_log_space_usage"
            ).fetchval()
            < 70
        )
        # Synthetic projections use the authoritative view names/columns. They
        # qualify driver custody, not the production joins or business values.
        setup.execute(
            "CREATE VIEW dbo.v_PlayerProfile AS "
            "SELECT CAST(1 AS bigint) AS GovernorID, CAST('Synthetic' AS nvarchar(30)) AS Governor_Name"
        )
        setup.execute(
            "CREATE VIEW dbo.v_PlayerScanMeta AS SELECT CAST(1 AS bigint) AS GovernorID, "
            "CAST('20260101' AS datetime2) AS FirstScanDate, "
            "CAST('20260102' AS datetime2) AS LastScanDate, CAST(0 AS int) AS OfflineDaysOver30"
        )
        setup.execute(
            "CREATE VIEW dbo.v_PlayerKVK_Last3 AS SELECT CAST(1 AS bigint) AS GovernorID, "
            "CAST(16 AS int) AS KVK_NUMBER, CAST(2 AS int) AS KVK_KILL_RANK, "
            "CAST(50 AS decimal(9,2)) AS KillPercent"
        )
        setup.execute("CREATE USER profile_reader WITHOUT LOGIN")
        setup.execute("GRANT SELECT ON SCHEMA::dbo TO profile_reader")

        def connect():
            conn = pyodbc.connect(db.connection_string, autocommit=False, timeout=5)
            handles.append(conn)
            conn.timeout = 5
            conn.execute("EXECUTE AS USER='profile_reader'")
            return conn

        outcome = SqlOutcome()
        players, omitted = read_profiles(connect, sql_outcome=outcome)
        assert players["1"]["KVK"][0] == {"KVK": 16, "Rank": 2, "Percent": 50.0}
        assert omitted == () and outcome.rollback == "confirmed" and outcome.cleanup == "settled"
        with pytest.raises(pyodbc.ProgrammingError):
            handles[-1].cursor()

        class RefusedClose:
            def __init__(self):
                self.connection = connect()
                cursor = self.connection.cursor()
                try:
                    self.session_id = cursor.execute("SELECT @@SPID").fetchval()
                finally:
                    cursor.close()

            def cursor(self):
                return self.connection.cursor()

            def rollback(self):
                self.connection.rollback()

            def close(self):
                raise OSError("injected before real driver close")

        owned, uncertain = RefusedClose(), SqlOutcome()
        connection_id = setup.execute(
            "SELECT connection_id FROM sys.dm_exec_connections WHERE session_id=?",
            owned.session_id,
        ).fetchval()
        assert connection_id is not None
        with pytest.raises(RuntimeError, match="cleanup_unconfirmed"):
            read_profiles(lambda: owned, sql_outcome=uncertain)
        assert uncertain.retained_connection is owned and uncertain.rollback == "confirmed"
        # The driver may begin another transaction after SQL end-transaction;
        # rollback acknowledgement alone is never physical cleanup evidence.
        assert (
            setup.execute(
                "SELECT COUNT(*) FROM sys.dm_exec_connections WHERE connection_id=?",
                connection_id,
            ).fetchval()
            == 1
        )
        owned.connection.close()
        assert (
            setup.execute(
                "SELECT COUNT(*) FROM sys.dm_exec_connections WHERE connection_id=?",
                connection_id,
            ).fetchval()
            == 0
        )
    finally:
        # The test owns its injected refusal and explicitly settles only its own
        # handles. Fixture teardown refuses forced eviction if anything leaks.
        for conn in handles:
            try:
                conn.close()
            except pyodbc.ProgrammingError:
                pass
        setup.close()
