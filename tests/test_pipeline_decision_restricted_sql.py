"""Run the size regression under a real, disposable least-privilege SQL login.

Only localhost\\K98DEV is used. Pipeline constraints and its FK are unchanged;
unrelated export FKs are omitted from the synthetic prerequisite tables.
"""

import os
from pathlib import Path
import re
import secrets
from types import SimpleNamespace
from uuid import uuid4

import pytest

from services.processing_pipeline_receipt_dal import PipelineReceiptDAL
from services.processing_pipeline_recovery import ProcessingPipelineRecovery
from tests.test_import_capture_recovery_sql import recovery as recovery
from tests.test_pipeline_decision_bound import (
    test_exhausted_history_is_rejected_before_sql_update_without_truncation as test_exhausted_history_is_rejected_before_sql_update_without_truncation,
    test_full_prior_snapshot_then_disposition_preserves_receipts_and_reconciles as test_full_prior_snapshot_then_disposition_preserves_receipts_and_reconciles,
    test_receipt_verification_uses_fingerprint_and_preserves_prior_history as test_receipt_verification_uses_fingerprint_and_preserves_prior_history,
)
from tests.test_processing_pipeline_recovery_sql import pipeline as pipeline_base  # noqa: F401

pytestmark = pytest.mark.skipif(
    os.getenv("K98_PIPELINE_RESTRICTED_SQL") != "1", reason="Disposable restricted SQL opt-in"
)


@pytest.fixture
def pipeline(pipeline_base):  # noqa: F811
    import pyodbc

    base = pipeline_base
    tables = (
        "ExportJob",
        "ExportJobResource",
        "ExportAttempt",
        "ExportPreparation",
        "ExportPreparationResource",
        "ExportResource",
        "StatsImportExecution",
        "ExportExecutionStream",
        "ProcessingPipelineRun",
        "ProcessingPipelineStage",
    )
    schema = Path(os.environ["K98_CAPTURE_SQL_SCHEMA"])
    namespace = uuid4().hex
    database = "K98PipelineTest_" + namespace
    login = "K98Pipeline_" + namespace
    password = "Aa1!" + secrets.token_hex(24)
    prefix = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost\\K98DEV;"
    suffix = "Encrypt=yes;TrustServerCertificate=yes;"
    admin = pyodbc.connect(
        prefix + "DATABASE=master;Trusted_Connection=yes;" + suffix, autocommit=True, timeout=5
    )
    owner = None
    try:
        assert (
            admin.execute("SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName'))").fetchval()
            == "9SX2VF4\\K98DEV"
        )
        admin.execute(f"CREATE DATABASE [{database}]")
        owner = pyodbc.connect(
            prefix + f"DATABASE={database};Trusted_Connection=yes;" + suffix,
            autocommit=True,
            timeout=5,
        )
        for table in tables:
            raw = (schema / ("dbo." + table + ".Table.sql")).read_text(encoding="utf-8-sig")
            if not table.startswith("ProcessingPipeline"):
                raw = "\n".join(line for line in raw.splitlines() if "FOREIGN KEY" not in line)
                raw = re.sub(r",\s*\);", "\n);", raw)
            owner.execute(raw)
            cursor = base.owner.execute(base.rewrite("SELECT * FROM dbo." + table))
            columns = [column[0] for column in cursor.description]
            for row in cursor.fetchall():
                owner.execute(
                    f"INSERT dbo.{table} ({','.join('[' + c + ']' for c in columns)}) "
                    f"VALUES ({','.join('?' for _ in columns)})",
                    *row,
                )
        admin.execute(f"CREATE LOGIN [{login}] WITH PASSWORD='{password}',CHECK_POLICY=ON")
        owner.execute(f"CREATE USER PipelineApp FOR LOGIN [{login}]")
        for table in tables:
            owner.execute(f"GRANT SELECT ON dbo.{table} TO PipelineApp")
        for table in ("ProcessingPipelineRun", "ProcessingPipelineStage"):
            owner.execute(f"GRANT INSERT,UPDATE ON dbo.{table} TO PipelineApp")

        def connect():
            connection = pyodbc.connect(
                prefix + f"DATABASE={database};UID={login};PWD={password};" + suffix,
                autocommit=False,
                timeout=5,
            )
            connection.timeout = 5
            return connection

        connection = connect()
        try:
            assert tuple(
                connection.execute(
                    "SELECT IS_SRVROLEMEMBER('sysadmin'),IS_ROLEMEMBER('db_owner'),"
                    "HAS_PERMS_BY_NAME('dbo.ProcessingPipelineStage','OBJECT','ALTER'),"
                    "HAS_PERMS_BY_NAME('dbo.StatsImportExecution','OBJECT','UPDATE'),"
                    "HAS_PERMS_BY_NAME('dbo.ExportResource','OBJECT','UPDATE')"
                ).fetchone()
            ) == (0, 0, 0, 0, 0)
        finally:
            connection.close()
        runtime = SimpleNamespace(**vars(base.runtime))
        runtime.dal = SimpleNamespace(connect=connect)
        dal = PipelineReceiptDAL(runtime)
        yield SimpleNamespace(
            **(
                vars(base)
                | dict(
                    dal=dal,
                    adapter=ProcessingPipelineRecovery(dal),
                    runtime=runtime,
                    owner=owner,
                    rewrite=lambda sql: sql,
                )
            )
        )
    finally:
        if owner is not None:
            owner.close()
        assert re.fullmatch(r"K98PipelineTest_[0-9a-f]{32}", database)
        if admin.execute("SELECT DB_ID(?)", database).fetchval() is not None:
            admin.execute(
                f"ALTER DATABASE [{database}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE; "
                f"DROP DATABASE [{database}]"
            )
        if admin.execute("SELECT SUSER_ID(?)", login).fetchval() is not None:
            admin.execute(f"DROP LOGIN [{login}]")
        admin.close()
