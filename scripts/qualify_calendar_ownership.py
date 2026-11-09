"""Guarded native P01.5 rehearsal: new disposable database, synthetic inputs only.

No production configuration is loaded. The exact database must not already exist.
Only five source-authoritative calendar tables are installed; the created database
is dropped after its receipt is saved. No retained database is made writable.
"""

import argparse
from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute or not re.fullmatch(
        r"K98_P015_Disposable_\d{8}_[a-f0-9]{8}", args.database
    ):
        parser.error("Explicit execution and a uniquely named P01.5 disposable target required")
    for key, value in {
        "PYTHON_DOTENV_DISABLED": "1",
        "K98_TEST_MODE": "1",
        "OUR_KINGDOM": "98",
        "DISCORD_BOT_TOKEN": "offline",
        "SQL_SERVER": "unused",
        "SQL_DATABASE": "unused",
    }.items():
        os.environ[key] = value
    import pyodbc

    pyodbc.pooling = False
    server = r"lpc:localhost\K98DEV"
    connection_string = (
        "DRIVER={ODBC Driver 17 for SQL Server};SERVER="
        + server
        + ";Trusted_Connection=yes;TrustServerCertificate=yes;DATABASE="
    )
    master = pyodbc.connect(connection_string + "master", timeout=2, autocommit=True)
    identity = master.execute(
        "SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName'))"
    ).fetchval()
    if identity != r"9SX2VF4\K98DEV":
        raise RuntimeError("Unexpected local SQL instance")
    if master.execute("SELECT DB_ID(?)", args.database).fetchval() is not None:
        raise RuntimeError("Target already exists; no writes or cleanup authorized")
    artifact = ROOT / ".codex_artifacts" / "p015-qualification-20261105" / args.database
    if artifact.exists():
        from uuid import uuid4

        artifact = artifact.with_name(args.database + "-" + uuid4().hex[:8])
    artifact.mkdir(parents=True, exist_ok=False)
    receipt: dict[str, Any] = dict(
        server=identity,
        database=args.database,
        new_target_verified=True,
        cases={},
        connections=[],
        schema_hashes={},
        status="running",
    )
    created_id = None
    connections = []
    try:
        # Identifier is constrained above, and absence is checked on the same master session.
        master.execute(f"CREATE DATABASE [{args.database}]")
        created_id = master.execute("SELECT DB_ID(?)", args.database).fetchval()
        receipt["database_id"] = created_id
        files = [
            row[0]
            for row in master.execute(
                "SELECT physical_name FROM sys.master_files WHERE database_id=?", created_id
            ).fetchall()
        ]
        if not files or any(not Path(name).name.startswith(args.database) for name in files):
            raise RuntimeError("Unexpected disposable database file target")
        receipt["verified_new_files"] = files

        def connect(*, lost_ack=False, close_failure=False, denied=False, slow=False):
            began = time.perf_counter()
            native = pyodbc.connect(connection_string + args.database, timeout=2, autocommit=False)
            identity_row = native.execute("SELECT DB_ID(), @@SPID").fetchone()
            if identity_row is None:
                native.close()
                raise RuntimeError("Fixture database identity is unavailable")
            db_id, spid = identity_row
            if db_id != created_id:
                native.close()
                raise RuntimeError("Fixture database identity changed")
            if denied:
                native.execute("EXECUTE AS USER = 'P015Denied'")
            record = dict(spid=spid, login_ms=(time.perf_counter() - began) * 1000, closed=False)
            receipt["connections"].append(record)

            class Connection:
                @property
                def timeout(self):
                    return native.timeout

                @timeout.setter
                def timeout(self, value):
                    native.timeout = value

                def cursor(self):
                    cursor = native.cursor()
                    if not slow:
                        return cursor

                    class SlowCursor:
                        def execute(self, sql, *parameters):
                            if "INSERT INTO dbo.EventSyncLog" in sql:
                                sql = "WAITFOR DELAY '00:00:04'; " + sql
                            return cursor.execute(sql, *parameters)

                        def fetchone(self):
                            return cursor.fetchone()

                        def close(self):
                            cursor.close()

                    return SlowCursor()

                def commit(self):
                    began = time.perf_counter()
                    native.commit()
                    record["commit_ms"] = (time.perf_counter() - began) * 1000
                    if lost_ack:
                        raise RuntimeError("simulated lost commit reply")

                def rollback(self):
                    native.rollback()

                def close(self):
                    if close_failure:
                        raise RuntimeError("simulated unconfirmed close")
                    self.settle_fixture()

                def settle_fixture(self):
                    if record["closed"]:
                        return
                    began = time.perf_counter()
                    native.close()
                    record["close_ms"] = (time.perf_counter() - began) * 1000
                    record["closed"] = True

            connection = Connection()
            connections.append(connection)
            return connection

        setup = pyodbc.connect(connection_string + args.database, timeout=2, autocommit=True)
        try:
            if setup.execute("SELECT COUNT(*) FROM sys.tables WHERE is_ms_shipped=0").fetchval():
                raise RuntimeError("New fixture is not empty")
            for name in (
                "EventRecurringRules",
                "EventOneOffEvents",
                "EventOverrides",
                "EventInstances",
                "EventSyncLog",
            ):
                source = Path(r"C:\K98-bot-SQL-Server\sql_schema") / f"dbo.{name}.Table.sql"
                raw = source.read_bytes()
                receipt["schema_hashes"][name] = hashlib.sha256(raw).hexdigest()
                setup.execute(raw.decode("utf-8-sig"))
            setup.execute("CREATE USER P015Denied WITHOUT LOGIN")
            setup.execute("DENY INSERT, UPDATE ON dbo.EventSyncLog TO P015Denied")
        finally:
            setup.close()
        from event_calendar import audit_dal, cache_publisher, event_generator, sheets_sync
        from event_calendar.sql_lifecycle import SqlSession

        now = datetime.now(UTC)
        row = dict(
            active="TRUE",
            event_id="fixture",
            title="Synthetic calendar",
            type="war",
            start_utc=(now + timedelta(days=1)).isoformat(),
            end_utc=(now + timedelta(days=2)).isoformat(),
        )

        def fetch(sheet, tab):
            return [dict(row)] if tab == "oneoff_events" else []

        def count(table):
            check = connect()
            try:
                cursor = check.cursor()
                try:
                    return cursor.execute("SELECT COUNT(*) FROM dbo." + table).fetchval()
                finally:
                    cursor.close()
            finally:
                check.close()

        with ExitStack() as patches:
            for module in (sheets_sync, event_generator, cache_publisher):
                patches.enter_context(
                    patch.object(module, "get_conn_with_retries", lambda **k: connect())
                )
            patches.enter_context(patch.object(sheets_sync, "fetch_sheet_csv", fetch))
            patches.enter_context(
                patch.object(cache_publisher, "_CACHE_PATH", artifact / "calendar.json")
            )
            patches.enter_context(
                patch.object(cache_publisher, "_TYPE_INDEX_PATH", artifact / "index.json")
            )
            patches.enter_context(patch.object(audit_dal, "_session", lambda: SqlSession(connect)))
            sync = sheets_sync.sync_sheets_to_sql("offline")
            assert sync.ok and sync.rows_upserted_oneoff == 1 and sync.sql.cleanup == "settled"
            generation = event_generator.generate_calendar_instances(horizon_days=30)
            assert generation.ok and generation.instances_written == 1
            before = connect()
            cursor = before.cursor()
            identity_before = cursor.execute("SELECT InstanceID FROM dbo.EventInstances").fetchval()
            cursor.close()
            before.close()
            assert event_generator.generate_calendar_instances(horizon_days=30).ok
            after = connect()
            cursor = after.cursor()
            assert (
                cursor.execute("SELECT InstanceID FROM dbo.EventInstances").fetchval()
                == identity_before
            )
            cursor.close()
            after.close()
            published = cache_publisher.publish_event_calendar_cache(horizon_days=30)
            assert published.ok and published.events_written == 1
            receipt["cases"]["normal_identity_preserving_pipeline"] = "passed"
            row["title"] = "Commit reply lost fixture"
            with patch.object(
                sheets_sync, "get_conn_with_retries", lambda **k: connect(lost_ack=True)
            ):
                unknown = sheets_sync.sync_sheets_to_sql("offline")
            assert (
                not unknown.ok
                and unknown.sql.effect == "unknown"
                and unknown.rows_upserted_oneoff is None
            )
            check = connect()
            cursor = check.cursor()
            assert (
                cursor.execute("SELECT Title FROM dbo.EventOneOffEvents").fetchval() == row["title"]
            )
            cursor.close()
            check.close()
            receipt["cases"]["simulated_lost_ack_actual_commit"] = "passed"
            with patch.object(
                event_generator, "get_conn_with_retries", lambda **k: connect(close_failure=True)
            ):
                closed = event_generator.generate_calendar_instances(horizon_days=30)
            assert (
                closed.ok and closed.sql.cleanup == "unconfirmed" and closed.instances_written == 1
            )
            assert closed.sql.retained_connection is not None
            # Explicit test-fixture disposal after verifying retained custody, never a runtime repair API.
            closed.sql.retained_connection.settle_fixture()
            receipt["cases"]["simulated_close_failure_actual_commit"] = "passed"
            original_write = event_generator.write_event_instances

            def fail_after_write(**kwargs):
                original_write(**kwargs)
                raise RuntimeError("injected statement failure")

            with patch.object(event_generator, "write_event_instances", fail_after_write):
                rolled = event_generator.generate_calendar_instances(horizon_days=30)
            assert (
                not rolled.ok
                and rolled.sql.effect == "rolled_back"
                and count("EventInstances") == 1
            )
            receipt["cases"]["rollback_after_identity_preserving_write"] = "passed"
            started = time.perf_counter()
            audit = audit_dal.start(now)
            receipt["audit_start_ms"] = (time.perf_counter() - started) * 1000
            assert audit.sync_id is not None and audit.sql.effect == "committed"
            started = time.perf_counter()
            terminal = audit_dal.finish(audit.sync_id, vars(sync), now)
            receipt["audit_finish_ms"] = (time.perf_counter() - started) * 1000
            assert terminal.sql.effect == "committed"
            receipt["cases"]["exact_id_audit"] = "passed"
            timings = {"start_ms": [], "finish_ms": []}
            for _ in range(30):
                began = time.perf_counter()
                repeated = audit_dal.start(now)
                timings["start_ms"].append((time.perf_counter() - began) * 1000)
                assert repeated.sync_id is not None and repeated.sql.effect == "committed"
                began = time.perf_counter()
                finished = audit_dal.finish(repeated.sync_id, vars(sync), now)
                timings["finish_ms"].append((time.perf_counter() - began) * 1000)
                assert finished.sql.effect == "committed"
            receipt["native_audit_timings"] = timings
            assert all(sorted(values)[27] <= 250 for values in timings.values())

            with patch.object(
                audit_dal, "_session", lambda: SqlSession(lambda: connect(denied=True))
            ):
                denied = audit_dal.start(now)
            assert denied.sync_id is None and denied.sql.effect != "committed"
            receipt["cases"]["denied_optional_audit"] = denied.sql.public()
            blocker = connect()
            cursor = blocker.cursor()
            try:
                cursor.execute("SELECT * FROM dbo.EventSyncLog WITH (TABLOCKX,HOLDLOCK)").fetchall()
                started = time.perf_counter()
                locked = audit_dal.start(now)
                lock_ms = (time.perf_counter() - started) * 1000
                assert locked.sync_id is None and locked.sql.effect != "committed"
                receipt["cases"]["native_lock_timeout"] = dict(
                    elapsed_ms=lock_ms, outcome=locked.sql.public()
                )
            finally:
                blocker.rollback()
                cursor.close()
                blocker.close()
            with patch.object(
                audit_dal, "_session", lambda: SqlSession(lambda: connect(slow=True))
            ):
                started = time.perf_counter()
                slow = audit_dal.start(now)
                statement_ms = (time.perf_counter() - started) * 1000
            assert slow.sync_id is None and slow.sql.effect != "committed"
            receipt["cases"]["native_statement_timeout"] = dict(
                elapsed_ms=statement_ms, outcome=slow.sql.public()
            )
        receipt["status"] = "passed"
    except Exception as error:
        receipt["status"] = "failed"
        receipt["error_type"] = type(error).__name__
        raise
    finally:
        for connection in connections:
            connection.settle_fixture()
        if created_id is not None:
            remaining = master.execute(
                "SELECT COUNT(*) FROM sys.dm_exec_sessions WHERE database_id=?", created_id
            ).fetchval()
            receipt["remaining_sessions"] = remaining
            if (
                remaining == 0
                and master.execute("SELECT DB_ID(?)", args.database).fetchval() == created_id
            ):
                (artifact / "native-receipt.json").write_text(
                    json.dumps(receipt, indent=2), encoding="utf-8"
                )
                master.execute(f"DROP DATABASE [{args.database}]")
                receipt["new_fixture_dropped"] = True
        (artifact / "native-receipt.json").write_text(
            json.dumps(receipt, indent=2), encoding="utf-8"
        )
        master.close()
    print(
        json.dumps(
            dict(
                status=receipt["status"],
                cases=len(receipt["cases"]),
                receipt=str(artifact / "native-receipt.json"),
            )
        )
    )


if __name__ == "__main__":
    main()
