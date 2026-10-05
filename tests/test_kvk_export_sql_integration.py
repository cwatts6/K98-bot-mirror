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
def s10e_pool_dal():
    """S10E approval is independent of every predecessor gate; not run offline."""
    if os.environ.get("K98_S10E_SQL_AUTHORIZED") != "S10E_EXACT_DISPOSABLE_OPERATIONS_APPROVED":
        pytest.skip("S10E transactions not authorized; authored coverage only")
    database = os.environ.get("K98_S10E_SQL_DATABASE", "")
    server = os.environ.get("K98_S10E_SQL_SERVER", "")
    if (
        not re.fullmatch(r"K98_S10E_Disposable_[0-9]{8}_validation", database)
        or server != "9SX2VF4\\K98DEV"
    ):
        pytest.fail("Exact separately prepared S10E target required")
    if not all(
        os.environ.get(k) for k in ("K98_S10E_BACKUP_EVIDENCE", "K98_S10E_RESTORE_EVIDENCE")
    ):
        pytest.fail("Backup and actual restore evidence required")
    import pyodbc

    from kvk.dal.source_output_pool_dal import SourceOutputPoolDAL

    def connect():
        connection = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};SERVER=lpc:localhost\\K98DEV;"
            + f"DATABASE={database};Trusted_Connection=yes;",
            autocommit=False,
            timeout=5,
        )
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT CAST(SERVERPROPERTY('ServerName') AS nvarchar(128)),DB_NAME()")
            if tuple(cursor.fetchone()) != (server, database):
                raise ValueError("Exact S10E server/database mismatch")
            connection.commit()
            return connection
        except BaseException:
            connection.close()
            raise

    return SourceOutputPoolDAL(connect)


def test_s10e_two_connections_cannot_claim_one_ready_operation(s10e_pool_dal):
    """Requires an explicitly seeded ready operation; preserves every resulting claim."""
    from uuid import UUID

    from kvk.dal.new_source_import_dal import SourceConflict
    from kvk.dal.source_output_pool_dal import SourceOutputPoolDAL

    operation_id = str(UUID(os.environ["K98_S10E_READY_OPERATION_ID"]))

    def claim():
        try:
            return SourceOutputPoolDAL(s10e_pool_dal.connect).claim(operation_id)
        except SourceConflict:
            return None

    with ThreadPoolExecutor(max_workers=2) as workers:
        claims = list(workers.map(lambda _: claim(), range(2)))
    assert sum(c is not None for c in claims) == 1
    winner = next(c for c in claims if c is not None)
    assert SourceOutputPoolDAL(s10e_pool_dal.connect).authorize(winner)["State"] == "running"
    # No cleanup release, lease expiry or provider execution.


def test_s10e_stale_tokens_and_uncertainty_keep_every_resource(s10e_pool_dal):
    """A distinct seeded case is required; retain claims as evidence after this test."""
    from dataclasses import replace
    from uuid import UUID

    from kvk.dal.new_source_import_dal import SourceConflict

    identifier = str(UUID(os.environ["K98_S10E_CAS_OPERATION_ID"]))
    claim = s10e_pool_dal.claim(identifier)
    assert claim is not None
    before = s10e_pool_dal.operation_snapshot(identifier)
    for stale in (
        replace(claim, owner=str(uuid4())),
        replace(claim, fence=claim.fence + 1),
        replace(claim, version=claim.version + 1),
        replace(claim, pool_version=claim.pool_version + 1),
    ):
        with pytest.raises(SourceConflict):
            s10e_pool_dal.authorize(stale)
    assert s10e_pool_dal.operation_snapshot(identifier) == before
    s10e_pool_dal.uncertain(claim)
    after = s10e_pool_dal.operation_snapshot(identifier)
    assert after["operation"]["State"] == "uncertain"
    assert after["resources"] == before["resources"]
    with pytest.raises(SourceConflict):
        s10e_pool_dal.claim(identifier)
    assert s10e_pool_dal.operation_snapshot(identifier)["resources"] == before["resources"]


def test_s10e_operation_blocks_daily_and_preparation_claims(s10e_pool_dal):
    from uuid import UUID

    from services.legacy_export_snapshot_dal import LegacySnapshotDAL

    identifier = str(UUID(os.environ["K98_S10E_CONTENTION_OPERATION_ID"]))
    claim = s10e_pool_dal.claim(identifier)
    assert claim is not None
    coordinator = ExportCoordinationDAL(
        s10e_pool_dal.connect, preparations=True, output_operations=True
    )
    coordinator.enqueue(daily(claim.account, "s10e-" + uuid4().hex))
    assert coordinator.claim_next(claim.account, storage_owner="synthetic:S10B") is None
    preparer = LegacySnapshotDAL(s10e_pool_dal.connect, output_operations=True)
    preparation = preparer.request(
        account=claim.account,
        consumer="scan_data",
        kvk_no=None,
        request={"fixture": str(uuid4())},
        storage_owner="synthetic:S10E",
        actor="fixture",
        reason="S10E exclusive ownership case",
    )
    assert (
        preparer.claim(
            preparation,
            account=claim.account,
            storage_owner="synthetic:S10E",
            stage="preflight",
            resource_keys=("account:" + claim.account,),
        )
        is None
    )
    assert s10e_pool_dal.authorize(claim)["State"] == "running"


def test_s10e_closing_ack_replay_preserves_plan_and_ticket(s10e_pool_dal):
    from uuid import UUID

    from kvk.dal.new_source_import_dal import SourceConflict
    from kvk.dal.source_output_pool_dal import SourceOutputPoolDAL
    from kvk.services.new_source_admin_service import SourceActor
    from kvk.services.source_output_pool_service import checked_plan

    pool_id = str(UUID(os.environ["K98_S10E_CONFIRM_POOL_ID"]))
    target = int(os.environ["K98_S10E_CONFIRM_NEW_KVK"])
    plan = checked_plan(
        s10e_pool_dal.snapshot(pool_id),
        s10e_pool_dal.choice(target),
        actor=SourceActor(1, 2, 3, frozenset()),
        reason="separately approved S10E closing replay fixture",
    )
    operation_id = str(uuid4())
    first = s10e_pool_dal.confirm(operation_id, plan)
    # Simulate caller losing the first acknowledgment and reconstructing its DAL.
    restarted = SourceOutputPoolDAL(s10e_pool_dal.connect)
    assert restarted.confirm(operation_id, plan) == first
    assert restarted.snapshot(pool_id)["pool"]["PoolState"] == "closing"
    with pytest.raises(SourceConflict):
        restarted.confirm(operation_id, dict(plan, reason="changed replay"))
    assert restarted.operation(operation_id)["EnqueueSequence"] == first["EnqueueSequence"]


@pytest.fixture
def s10c_preparation_dal():
    """Distinct, unexecuted S10C gate; S10B approval cannot enable these tests."""
    if os.environ.get("K98_S10C_SQL_AUTHORIZED") != "S10C_EXACT_DISPOSABLE_OPERATIONS_APPROVED":
        pytest.skip("S10C SQL execution not authorized; authored coverage only")
    database = os.environ.get("K98_S10C_SQL_DATABASE", "")
    if not re.fullmatch(r"K98_S10C_Disposable_[0-9]{8}_validation", database):
        pytest.fail("A distinct S10C disposable target is required")
    import pyodbc

    from services.legacy_export_snapshot_dal import LegacySnapshotDAL

    def connect():
        con = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};SERVER=lpc:localhost\\K98DEV;"
            + f"DATABASE={database};Trusted_Connection=yes;",
            autocommit=False,
            timeout=5,
        )
        try:
            cur = con.cursor()
            cur.execute("SELECT CAST(SERVERPROPERTY('ServerName') AS nvarchar(128)),DB_NAME()")
            if tuple(cur.fetchone()) != ("9SX2VF4\\K98DEV", database):
                raise ValueError("S10C exact server/database mismatch")
            con.commit()
            return con
        except BaseException:
            con.close()
            raise

    return LegacySnapshotDAL(connect)


def test_s10c_sql_preparation_claim_survives_fresh_dal_and_blocks_job(s10c_preparation_dal):
    dal = s10c_preparation_dal
    account = "s10c-" + uuid4().hex
    identifier = dal.request(
        account=account,
        consumer="scan_data",
        kvk_no=None,
        request={"fixture": str(uuid4())},
        storage_owner="synthetic:S10C",
        actor="fixture",
        reason="separately approved S10C fixture",
    )
    claim = dal.claim(
        identifier,
        account=account,
        storage_owner="synthetic:S10C",
        stage="preflight",
        resource_keys=("account:" + account,),
    )
    assert claim is not None
    coordinator = ExportCoordinationDAL(dal.connect, preparations=True)
    coordinator.enqueue(daily(account, "s10c-" + uuid4().hex))
    assert coordinator.claim_next(account, storage_owner="synthetic:S10B") is None
    from services.legacy_export_snapshot_dal import LegacySnapshotDAL

    assert LegacySnapshotDAL(dal.connect).authorize(claim)["State"] == "preflight"
    # Retain synthetic evidence and claims; no lease-based fixture cleanup.


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
