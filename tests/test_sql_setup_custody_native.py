"""Dedicated setup cleanup using only the explicitly opted-in disposable database."""

import pytest

from core import export_sql_connection as factory


def test_native_factory_handoff_and_failed_setup_custody(snapshot_database, monkeypatch):
    import pyodbc

    real_connect = pyodbc.connect
    observer = real_connect(snapshot_database.connection_string, autocommit=True, timeout=5)
    observer.timeout = 5
    handles = []
    mode = {"setup_fails": False, "close_fails": False}
    monkeypatch.setattr(factory, "_setup_holds", {})
    monkeypatch.setattr(
        factory,
        "settings",
        lambda **kw: {
            "server": "synthetic",
            "database": "synthetic",
            "username": "synthetic",
            "password": "synthetic",
        },
    )
    try:
        assert (
            observer.execute(
                "SELECT used_log_space_in_percent FROM sys.dm_db_log_space_usage"
            ).fetchval()
            < 70
        )
        observer.execute("CREATE USER setup_reader WITHOUT LOGIN")
        observer.execute("GRANT SELECT ON SCHEMA::dbo TO setup_reader")

        class Connection:
            def __init__(self, raw):
                self.raw = raw

            @property
            def timeout(self):
                return self.raw.timeout

            @timeout.setter
            def timeout(self, value):
                self.raw.timeout = value

            @property
            def autocommit(self):
                return self.raw.autocommit

            @autocommit.setter
            def autocommit(self, value):
                self.raw.autocommit = value

            def cursor(self):
                raw = self.raw.cursor()

                class Cursor:
                    def execute(self, sql):
                        raw.execute(sql)
                        if mode["setup_fails"]:
                            raise OSError("injected after real SET")

                    def close(self):
                        raw.close()

                return Cursor()

            def close(self):
                if mode["close_fails"]:
                    raise OSError("injected before real close")
                self.raw.close()

        def connect(target, **kwargs):
            assert "SERVER={synthetic}" in target
            raw = real_connect(snapshot_database.connection_string, **kwargs)
            handles.append(raw)
            raw.execute("EXECUTE AS USER='setup_reader'")
            return Connection(raw)

        monkeypatch.setattr(pyodbc, "connect", connect)
        configured = factory.connect(server="synthetic", database="synthetic")
        assert configured.timeout == 15 and configured.autocommit is False
        assert configured.raw.execute("SELECT @@LOCK_TIMEOUT").fetchval() == 1000
        configured.close()

        mode["setup_fails"] = True
        with pytest.raises(factory.ExportSqlConfigurationError):
            factory.connect(server="synthetic", database="synthetic")
        with pytest.raises(pyodbc.ProgrammingError):
            handles[-1].cursor()
        assert factory.setup_custody_snapshot()["admission"] == "open"

        mode["close_fails"] = True
        with pytest.raises(factory.ExportSqlSetupAdmissionClosed):
            factory.connect(server="synthetic", database="synthetic")
        held = next(iter(factory._setup_holds.values())).retained_connection
        assert held.raw is handles[-1]
        cursor = held.raw.cursor()
        try:
            session_id = cursor.execute("SELECT @@SPID").fetchval()
        finally:
            cursor.close()
        identity = observer.execute(
            "SELECT connection_id FROM sys.dm_exec_connections WHERE session_id=?", session_id
        ).fetchval()
        assert identity is not None
        with pytest.raises(factory.ExportSqlSetupAdmissionClosed):
            factory.connect(server="synthetic", database="synthetic")
        assert len(handles) == 3
        held.raw.close()
        assert (
            observer.execute(
                "SELECT COUNT(*) FROM sys.dm_exec_connections WHERE connection_id=?", identity
            ).fetchval()
            == 0
        )
        # An out-of-band test close does not silently clear the factory's hold.
        assert factory.setup_custody_snapshot()["unconfirmed"] == 1
    finally:
        for raw in handles:
            try:
                raw.close()
            except pyodbc.ProgrammingError:
                pass
        observer.close()
