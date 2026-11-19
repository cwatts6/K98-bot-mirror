"""Real restricted metadata visibility; dispatch responses are simulated, never jobs."""

from contextlib import closing
from unittest.mock import Mock

import log_backup


def simulated_dispatch(metadata, *, job_id=None):
    cursor = Mock()
    cursor.fetchmany.return_value = [tuple(metadata)]
    cursor.nextset.return_value = False
    return log_backup.request_once(cursor, job_id=job_id), cursor


def test_restricted_visibility_distinguishes_absent_hidden_and_denied(snapshot_database):
    import pyodbc

    with closing(
        pyodbc.connect(snapshot_database.connection_string, autocommit=True, timeout=5)
    ) as con:
        con.timeout = 3
        con.execute(
            "CREATE USER d4_route_hidden WITHOUT LOGIN;"
            "CREATE USER d4_route_visible WITHOUT LOGIN;"
            "CREATE USER d4_route_execute WITHOUT LOGIN;"
            "CREATE USER d4_route_object_deny WITHOUT LOGIN;"
            "GRANT VIEW DEFINITION TO d4_route_visible;"
            "GRANT VIEW DEFINITION TO d4_route_object_deny;"
        )

        def observe(user):
            # User names are fixed fixture literals; no caller-supplied identifier.
            assert user in {
                "d4_route_hidden",
                "d4_route_visible",
                "d4_route_execute",
                "d4_route_object_deny",
            }
            con.execute("EXECUTE AS USER='" + user + "'")
            try:
                return tuple(con.execute(log_backup.BACKUP_ROUTE_METADATA).fetchone())
            finally:
                con.execute("REVERT")

        # This test's already-owned dbo context can establish absence. A broad
        # VIEW DEFINITION grant to a restricted user cannot: object DENY wins.
        absent = tuple(con.execute(log_backup.BACKUP_ROUTE_METADATA).fetchone())
        assert absent[:2] == (None, 1) and absent[2] in (0, None)
        result, cursor = simulated_dispatch(absent, job_id="fixed-fixture-job")
        assert result["outcome"] == "requested" and result["used_method"] == "job_id"
        assert cursor.execute.call_count == 2

        restricted_absent = observe("d4_route_visible")
        assert restricted_absent[:2] == (None, 0)
        result, cursor = simulated_dispatch(restricted_absent)
        assert result["outcome"] == "not_attempted" and cursor.execute.call_count == 1

        # This deliberately inert fixture is not an installed-wrapper definition.
        con.execute(
            "CREATE PROCEDURE dbo.usp_start_rok_tracker_log_backup AS "
            "THROW 50000,'Fixture must never dispatch.',1"
        )
        con.execute(
            "GRANT EXECUTE ON dbo.usp_start_rok_tracker_log_backup TO d4_route_execute;"
            "DENY EXECUTE ON dbo.usp_start_rok_tracker_log_backup TO d4_route_visible;"
            "DENY VIEW DEFINITION ON dbo.usp_start_rok_tracker_log_backup TO d4_route_object_deny;"
        )
        hidden = observe("d4_route_hidden")
        assert hidden[:2] == (None, 0) and hidden[2] in (0, None)
        result, cursor = simulated_dispatch(hidden, job_id="fixed-fixture-job")
        assert result["outcome"] == "not_attempted" and cursor.execute.call_count == 1

        denied = observe("d4_route_visible")
        assert denied[0] is not None and denied[1:] == (0, 0)
        result, cursor = simulated_dispatch(denied)
        assert result["outcome"] == "not_attempted" and cursor.execute.call_count == 1

        executable = observe("d4_route_execute")
        assert executable[0] is not None and executable[1:] == (0, 1)
        result, cursor = simulated_dispatch(executable)
        assert result["outcome"] == "requested" and result["used_method"] == "wrapper"
        assert cursor.execute.call_count == 2

        object_denied = observe("d4_route_object_deny")
        result, cursor = simulated_dispatch(object_denied)
        assert result["outcome"] == "not_attempted", object_denied
        assert cursor.execute.call_count == 1


def test_real_msdb_inspection_preserves_master_caller_context(snapshot_database):
    import pyodbc

    local_master = snapshot_database.connection_string.replace(snapshot_database.name, "master")
    with closing(pyodbc.connect(local_master, autocommit=True, timeout=5)) as con:
        con.timeout = 3
        assert con.execute("SELECT DB_NAME()").fetchval() == "master"
        cursor = con.execute(log_backup.BACKUP_ROUTE_QUERY)
        rows = cursor.fetchmany(2)
        assert len(rows) == 1 and len(rows[0]) == 3
        assert not cursor.nextset()
        assert con.execute("SELECT DB_NAME()").fetchval() == "master"
