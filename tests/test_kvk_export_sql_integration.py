"""Explicit opt-in S10B SQL concurrency evidence; never use application defaults.

These tests retain synthetic rows. They require a separately approved, prepared
S10B disposable database with merged S10A installed. They create no database and
never use or alter predecessor evidence databases. Offline runs skip this module.
"""

from concurrent.futures import ThreadPoolExecutor
import os
import re
from uuid import uuid4

import pytest

from services.export_coordination_dal import ExportCoordinationDAL, JobSpec


@pytest.fixture
def sql_dal():
    database = os.environ.get("K98_S10B_SQL_DATABASE", "")
    if os.environ.get("K98_S10B_SQL_AUTHORIZED") != "S10B_EXACT_DISPOSABLE_OPERATIONS_APPROVED":
        pytest.skip("S10B disposable SQL execution requires separate exact-operation approval")
    if not re.fullmatch(r"K98_S10B_Disposable_[0-9]{8}_validation", database):
        pytest.fail("Exact new S10B disposable target required; predecessor targets prohibited")
    import pyodbc

    def connect():
        connection = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};SERVER=lpc:localhost\\K98DEV;"
            f"DATABASE={database};Trusted_Connection=yes;",
            autocommit=False,
            timeout=5,
        )
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT CAST(SERVERPROPERTY('ServerName') AS nvarchar(128)),DB_NAME()")
            server, actual = cursor.fetchone()
            if server != "9SX2VF4\\K98DEV" or actual != database:
                raise ValueError("S10B exact server/database mismatch")
            connection.commit()
            return connection
        except BaseException:
            connection.close()
            raise

    return ExportCoordinationDAL(connect)


def daily(account, destination, content=b"a" * 32):
    return JobSpec(
        account=account,
        consumer="scan_data",
        input_hash=content,
        destinations=(destination,),
        actor="synthetic:S10B",
        reason="Approved concurrency test",
        spool_key=uuid4().hex,
        spool_bytes=1,
        storage_owner="synthetic:S10B",
    )


def test_sql_account_reservations_survive_fresh_connections(sql_dal):
    account = uuid4().hex
    a = sql_dal.reserve_request(account)
    b = sql_dal.reserve_request(account)
    assert (b["ReservedUTC"] - a["ReservedUTC"]).total_seconds() >= 2.1
    sql_dal.extend_cooldown(account, 30)
    c = sql_dal.reserve_request(account)
    assert c["WaitSeconds"] >= 29


def test_sql_duplicate_null_tuple_and_resource_admission(sql_dal):
    account, dest = uuid4().hex, uuid4().hex
    request = daily(account, dest)
    first = sql_dal.enqueue(request)
    assert sql_dal.enqueue(request)["JobID"] == first["JobID"]
    claim = sql_dal.claim_next(account, storage_owner="synthetic:S10B")
    assert claim is not None
    assert sql_dal.claim_next(account, storage_owner="synthetic:S10B") is None
    assert sql_dal.authorize(claim)["JobID"] == first["JobID"]


def test_sql_two_workers_cannot_both_claim(sql_dal):
    account, dest = uuid4().hex, uuid4().hex
    sql_dal.enqueue(daily(account, dest))

    def claim():
        try:
            return sql_dal.claim_next(account, storage_owner="synthetic:S10B")
        except Exception as exc:
            # Only the deliberate nonblocking admission contention is expected.
            if "Export admission busy" not in str(exc):
                raise
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: claim(), range(2)))
    assert sum(result is not None for result in results) == 1


def test_sql_uncertain_attempt_retains_account_and_destination(sql_dal):
    account, dest = uuid4().hex, uuid4().hex
    sql_dal.enqueue(daily(account, dest))
    claim = sql_dal.claim_next(account, storage_owner="synthetic:S10B")
    parts = [dict(file_id=dest, role="output", manifest_hash="a" * 64, grids=1, rows=1, cells=1)]
    sql_dal.begin_attempt(claim, {"export_key": "synthetic"}, parts)
    sql_dal.fail(claim)
    sql_dal.enqueue(daily(account, dest, b"b" * 32))
    assert sql_dal.claim_next(account, storage_owner="synthetic:S10B") is None
