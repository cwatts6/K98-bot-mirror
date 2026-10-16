"""Compile the actual target procedure in tempdb; exercise its atomic entry gate."""

import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

import pytest

from tests.test_import_capture_recovery_sql import recovery as recovery
from tests.test_player_report_recovery_sql import uncommitted

pytestmark = [
    pytest.mark.skipif(
        os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Temporary SQL opt-in required"
    ),
    pytest.mark.parametrize("recovery", ["configuration_producer"], indirect=True),
]


@pytest.fixture
def targets(recovery):
    r = recovery
    ns = uuid4().hex
    proc, delta, config, mutations = [
        "##ConfigContract_" + ns + suffix for suffix in ("_target", "_delta", "_config", "_writes")
    ]
    r.owner.execute(
        f"CREATE TABLE {config}(KVKVersion int,ConfigKey varchar(50),ConfigValue float)"
    )
    r.owner.execute(f"CREATE TABLE {mutations}(Value int)")
    # The unchanged delta callee's nested transaction shape is represented by a
    # disposable stub. Full business-data publication remains separate coverage.
    r.owner.execute(
        f"CREATE PROCEDURE {delta} AS BEGIN BEGIN TRANSACTION; INSERT {mutations} VALUES (7); COMMIT TRANSACTION; END"
    )
    source = (
        Path(os.environ["K98_RECOVERY_SQL_SCHEMA"]) / "dbo.sp_TARGETS_MASTER.StoredProcedure.sql"
    )
    raw = source.read_text(encoding="utf-8-sig")
    raw = raw[raw.index("ALTER PROCEDURE [dbo].[sp_TARGETS_MASTER]") :]
    raw = raw.replace("ALTER PROCEDURE [dbo].[sp_TARGETS_MASTER]", "CREATE PROCEDURE " + proc, 1)
    raw = r.rewrite(raw).replace("dbo.ProcConfig", config).replace("dbo.CREATE_DELTA_TABLES", delta)
    raw = raw.replace("K98:TargetPublication:DeltaPreprocessing", "test:" + ns)
    r.owner.execute(raw)
    r.target_proc, r.target_writes = proc, mutations
    return r


def test_migration_and_source_pin_match_literal_compiled_procedure(targets):
    from services.export_execution_dal import CURRENT_INSTALLATION_MIGRATIONS

    root = Path(os.environ["K98_RECOVERY_SQL_SCHEMA"]).parent
    migration = (root / "migrations/20261016_002_atomic_configuration_publication.sql").read_text(
        encoding="utf-8-sig"
    )
    raw = (root / "sql_schema/dbo.sp_TARGETS_MASTER.StoredProcedure.sql").read_text(
        encoding="utf-8-sig"
    )
    body = raw[raw.index("ALTER PROCEDURE [dbo].[sp_TARGETS_MASTER]") :].strip() + "\n"
    assert "DECLARE @Apply nvarchar(max)=N'" + body.replace("'", "''") + "';" in migration
    assert (
        hashlib.sha256(
            body.replace("ALTER PROCEDURE", "CREATE PROCEDURE", 1).encode("utf-16-le")
        ).hexdigest()
        in migration
    )
    assert "sys.crypt_properties" in migration and "IF XACT_STATE()<>0 ROLLBACK" in migration
    assert "20261016_002_atomic_configuration_publication" in CURRENT_INSTALLATION_MIGRATIONS
    manifest = json.loads(
        (
            Path(__file__).resolve().parents[1] / "deploy/export_application_schema_source.json"
        ).read_text()
    )
    assert (
        next(r["sha256"] for r in manifest if r["name"] == "dbo.sp_TARGETS_MASTER")
        == hashlib.sha256(raw.encode()).hexdigest()
    )


@pytest.mark.parametrize("commit", [True, False])
def test_nested_target_transaction_leaves_outer_commit_to_producer(targets, commit):
    r = targets
    generation = json.loads(r.outcomes.inspect(r.source)["preparation"]["GenerationJson"])
    _, claim = uncommitted(r)
    conn = r.outcomes.connect()
    try:
        cur = conn.cursor()
        r.runtime.dal.begin_producer_transaction(claim, cur)
        cur.execute(f"EXEC {r.target_proc} @KVK=1,@ExportPreparationID=?", r.source)
        while cur.nextset():
            pass
        cur.execute("SELECT @@TRANCOUNT")
        assert cur.fetchone()[0] == 1
        while cur.nextset():
            pass
        r.runtime.dal.transition(
            claim, expected="writing", state="committed", generation=generation, external_cursor=cur
        )
        (conn.commit if commit else conn.rollback)()
        assert r.owner.execute(f"SELECT COUNT(*) FROM {r.target_writes}").fetchval() == int(commit)
        assert r.outcomes.inspect(r.source)["action"] == (
            "resume_capture" if commit else "cancel_configuration"
        )
    finally:
        conn.close()


@pytest.mark.parametrize("case", ["no_transaction", "wrong_id", "wrong_type", "legacy_ambient"])
def test_invalid_ambient_contract_never_enters_delta_work(targets, case):
    import pyodbc

    r = targets
    _, claim = uncommitted(r)
    conn = r.outcomes.connect()
    try:
        if case == "no_transaction":
            conn.autocommit = True
        cur = conn.cursor()
        if case != "no_transaction":
            r.runtime.dal.begin_producer_transaction(claim, cur)
        if case == "wrong_type":
            cur.execute(
                "UPDATE dbo.ExportPreparation SET RequestJson=JSON_MODIFY(RequestJson,'$.request.producer.kind','player_stats_report') WHERE PreparationID=?",
                r.source,
            )
        with pytest.raises(pyodbc.Error):
            if case == "legacy_ambient":
                cur.execute(f"EXEC {r.target_proc} @KVK=1")
            else:
                cur.execute(
                    f"EXEC {r.target_proc} @KVK=1,@ExportPreparationID=?",
                    str(uuid4()) if case == "wrong_id" else r.source,
                )
            while cur.nextset():
                pass
        conn.rollback()
        assert r.owner.execute(f"SELECT COUNT(*) FROM {r.target_writes}").fetchval() == 0
    finally:
        conn.close()
