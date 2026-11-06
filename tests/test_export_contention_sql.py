"""Opt-in synthetic native evidence; never executes a business producer."""

import ast
import os
from pathlib import Path
import re
import threading
import time
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import UncertainCommit
from services.export_contention import CoordinationLockRefused, retry_coordination, transaction
from services.export_coordination_dal import _mutex

pytestmark = pytest.mark.skipif(
    os.environ.get("K98_CONTENTION_SQL") != "LOCAL_SYNTHETIC_ONLY",
    reason="Explicit local isolated SQL target required",
)


@pytest.fixture
def connect():
    import pyodbc

    database = os.environ["K98_CONTENTION_DATABASE"]
    assert re.fullmatch(r"S11_Contention_Disposable_20261008_[a-f0-9]{8}", database)

    def open_connection(*, autocommit=False):
        cn = pyodbc.connect(
            r"DRIVER={ODBC Driver 17 for SQL Server};SERVER=lpc:localhost\K98DEV;"
            "DATABASE=" + database + ";Trusted_Connection=yes;TrustServerCertificate=yes",
            autocommit=True,
            timeout=5,
        )
        cn.timeout = 5
        identity = cn.cursor().execute("SELECT @@SERVERNAME,DB_NAME()").fetchone()
        assert identity[0].lower() == r"9sx2vf4\k98dev" and identity[1] == database
        cn.autocommit = autocommit
        return cn

    return open_connection


def test_real_rollback_then_retry_releases_all_connections(connect):
    key = "local-native:" + uuid4().hex
    holder = connect(autocommit=True)
    holder.cursor().execute("BEGIN TRANSACTION")
    _mutex(holder.cursor(), key)
    failed = threading.Event()
    results = []
    attempts = []

    @retry_coordination
    def authorize():
        attempts.append(True)
        try:
            with transaction(connect) as cursor:
                _mutex(cursor, key)
                return cursor.execute("SELECT @@SPID").fetchone()[0]
        except CoordinationLockRefused as error:
            assert error.transaction_released and error.result == -1
            failed.set()
            raise

    def run():
        try:
            results.append(authorize())
        except BaseException as error:
            results.append(error)

    worker = threading.Thread(target=run)
    try:
        worker.start()
        assert failed.wait(5)
        # The first failed transaction has already rolled back and closed.
        holder.cursor().execute("ROLLBACK")
        worker.join(6)
        assert not worker.is_alive()
        assert len(results) == 1 and isinstance(results[0], int), results
        assert 2 <= len(attempts) <= 8
    finally:
        holder.cursor().execute("IF @@TRANCOUNT>0 ROLLBACK")
        holder.close()
        worker.join(6)


def test_real_permanent_contention_is_bounded(connect):
    key = "local-exhaustion:" + uuid4().hex
    holder = connect(autocommit=True)
    holder.cursor().execute("BEGIN TRANSACTION")
    _mutex(holder.cursor(), key)
    attempts = []

    @retry_coordination
    def authorize():
        attempts.append(True)
        with transaction(connect) as cursor:
            _mutex(cursor, key)

    try:
        started = time.monotonic()
        with pytest.raises(CoordinationLockRefused) as caught:
            authorize()
        assert caught.value.transaction_released
        assert 1 <= len(attempts) <= 8
        assert time.monotonic() - started < 3
    finally:
        holder.cursor().execute("ROLLBACK")
        holder.close()


def test_commit_ack_loss_is_never_replayed_and_durable_row_survives(connect):
    identifier = int(uuid4().hex[:7], 16) + 100
    attempts = []

    class LostAcknowledgement:
        def __init__(self):
            self.cn = connect()

        def __getattr__(self, name):
            return getattr(self.cn, name)

        def commit(self):
            self.cn.commit()
            raise OSError("synthetic commit acknowledgement lost")

    @retry_coordination
    def checkpoint():
        attempts.append(True)
        with transaction(LostAcknowledgement) as cursor:
            cursor.execute("INSERT dbo.SyntheticOutcome VALUES (?,'ack_lost')", identifier)

    with pytest.raises(UncertainCommit):
        checkpoint()
    assert len(attempts) == 1
    cn = connect(autocommit=True)
    try:
        assert (
            cn.cursor()
            .execute(
                "SELECT COUNT(*) FROM dbo.SyntheticOutcome WHERE ID=? AND Outcome='ack_lost'",
                identifier,
            )
            .fetchone()[0]
            == 1
        )
    finally:
        cn.close()


def test_actual_generation_parameter_description_has_explicit_type(connect):
    import pyodbc

    path = Path(__file__).resolve().parents[1] / "services/legacy_export_snapshot_dal.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    query = next(
        n.value
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant)
        and isinstance(n.value, str)
        and n.value.startswith("UPDATE dbo.ExportPreparation SET State=?,GenerationJson=")
    )
    query = query.replace("dbo.ExportPreparation", "@Preparation")
    for number in range(1, query.count("?") + 1):
        query = query.replace("?", f"@P{number}", 1)
    declaration = (
        "DECLARE @Preparation TABLE (State varchar(32),GenerationJson nvarchar(max),"
        "Version bigint,UpdatedUTC datetime2(3),PreparationID uniqueidentifier,"
        "OwnerID uniqueidentifier,Fence bigint); "
    )
    cn = connect(autocommit=True)
    try:
        with pytest.raises(pyodbc.Error, match="11502"):
            cn.cursor().execute(
                "EXEC sys.sp_describe_undeclared_parameters @tsql=?",
                declaration + query.replace("CAST(@P2 AS nvarchar(max))", "@P2"),
            )
        cursor = cn.cursor().execute(
            "EXEC sys.sp_describe_undeclared_parameters @tsql=?", declaration + query
        )
        names = [column[0] for column in cursor.description]
        rows = [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]
        assert (
            next(row for row in rows if row["name"] == "@P2")["suggested_system_type_name"]
            == "nvarchar(max)"
        )
    finally:
        cn.close()
