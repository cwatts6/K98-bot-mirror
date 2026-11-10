"""Explicitly opted-in, uniquely owned local databases for snapshot SQL tests."""

import os
from types import SimpleNamespace
from uuid import uuid4

import pytest


@pytest.fixture(scope="module")
def snapshot_database():
    if os.getenv("K98_P021_NATIVE_SQL") != "CREATE_DISPOSABLE_LOCAL_ONLY":
        pytest.skip("Snapshot regression tests require a new disposable local database opt-in")
    import pyodbc

    pyodbc.pooling = False
    name = "K98_P021_Disposable_" + uuid4().hex
    base = (
        r"DRIVER={ODBC Driver 18 for SQL Server};SERVER=lpc:localhost\K98DEV;"
        "Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;DATABASE="
    )
    admin = pyodbc.connect(base + "master;", autocommit=True, timeout=5)
    admin.timeout = 10
    assert tuple(admin.execute("SELECT @@SERVERNAME,DB_NAME()").fetchone()) == (
        r"9SX2VF4\K98DEV",
        "master",
    )
    assert admin.execute("SELECT DB_ID(?)", name).fetchval() is None
    created = False
    try:
        admin.execute(f"CREATE DATABASE [{name}]")
        created = True
        admin.execute(f"ALTER DATABASE [{name}] SET ALLOW_SNAPSHOT_ISOLATION ON")
        yield SimpleNamespace(name=name, connection_string=base + name + ";")
    finally:
        try:
            if created:
                # Never force-disconnect sessions or target a retained database.
                # A leaked test connection is a cleanup failure, not permission
                # to use SINGLE_USER/ROLLBACK IMMEDIATE.
                admin.execute("SET LOCK_TIMEOUT 1000")
                admin.execute(f"DROP DATABASE [{name}]")
        finally:
            admin.close()
