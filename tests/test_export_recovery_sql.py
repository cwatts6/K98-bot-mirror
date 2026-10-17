"""Recovery custody filters against authoritative schemas in local temporary tables."""

from datetime import datetime
import json
import os
from pathlib import Path
import re
from types import SimpleNamespace
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_recovery_dal import ExportRecoveryDAL

pytestmark = pytest.mark.skipif(
    os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Explicit local temporary SQL opt-in"
)


@pytest.fixture
def scoped_jobs():
    import pyodbc

    names = (
        "ExportJobResource",
        "ExportResource",
        "ExportAttempt",
        "ExportJob",
        "ExportExecutionStream",
        "ExportContainedTarget",
    )
    sql = pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost\\K98DEV;DATABASE=master;Trusted_Connection=yes;TrustServerCertificate=yes",
        autocommit=True,
        timeout=5,
    )

    def rewrite(text):
        for name in names:
            text = re.sub(r"\bdbo\." + name + r"\b", "#" + name, text)
        text = text.replace("KVK.SourceDelivery", "#SourceDelivery")
        text = text.replace("KVK.SeasonSource", "#SeasonSource")
        return text

    try:
        schema = Path(
            os.getenv("K98_RECOVERY_SQL_SCHEMA")
            or os.getenv("K98_CAPTURE_SQL_SCHEMA", "C:/K98-bot-SQL-Server/sql_schema")
        )
        for name in names:
            text = (schema / f"dbo.{name}.Table.sql").read_text(encoding="utf-8-sig")
            text = "\n".join(line for line in text.splitlines() if "FOREIGN KEY" not in line)
            text = re.sub(r",\s*\);", "\n);", text)
            text = re.sub(
                r"CONSTRAINT (\w+)", lambda m: "CONSTRAINT " + m[1] + "_" + uuid4().hex, text
            )
            sql.execute(rewrite(text))
        text = (schema / "KVK.SourceDelivery.Table.sql").read_text(encoding="utf-8-sig")
        text = "\n".join(line for line in text.splitlines() if "FOREIGN KEY" not in line)
        text = re.sub(r"CONSTRAINT (\w+)", lambda m: "CONSTRAINT " + m[1] + "_" + uuid4().hex, text)
        sql.execute(rewrite(text))

        text = (schema / "KVK.SeasonSource.Table.sql").read_text(encoding="utf-8-sig")
        text = re.sub(r"CONSTRAINT (\w+)", lambda m: "CONSTRAINT " + m[1] + "_" + uuid4().hex, text)
        sql.execute(rewrite(text))
        sql.execute(
            "INSERT #SeasonSource(KVK_NO,SourceKey,ChoiceID,ChosenBy,ChosenUTC,Reason,ProvenanceJson,SeasonState,SeasonVersion) "
            "VALUES (1,'snapshot_report_v1',?,'test',SYSUTCDATETIME(),'temp fixture','{}','open',1)",
            str(uuid4()),
        )

        class Cursor:
            def __init__(self):
                self.inner = sql.cursor()

            def execute(self, statement, *args):
                self.inner.execute(rewrite(statement), *args)
                return self

            def __getattr__(self, name):
                return getattr(self.inner, name)

        class Connection:
            @property
            def autocommit(self):
                return sql.autocommit

            def cursor(self):
                return Cursor()

            def commit(self):
                sql.commit()

            def rollback(self):
                sql.rollback()

            def close(self):
                pass

        def connect():
            sql.autocommit = False
            return Connection()

        pool = dict(
            pool_id=str(uuid4()),
            index_file_id="index-registered",
            slot_file_ids=["slot-one", "slot-two"],
        )
        registration = SimpleNamespace(
            value=lambda: dict(account="account", storage_owner="disk", pools=[pool])
        )
        dal = ExportRecoveryDAL(connect, registration=registration)
        ids = {}
        destination_sets = {
            "registered": [pool["index_file_id"], *pool["slot_file_ids"]],
            "foreign": ["foreign-index", "foreign-one", "foreign-two"],
        }
        for label, consumer, account, owner in (
            ("registered", "new_source", "account", None),
            ("foreign", "new_source", "account", None),
            ("legacy", "scan_data", "account", "disk"),
            ("foreign-disk", "scan_data", "account", "other-disk"),
            ("foreign-account", "scan_data", "other-account", "disk"),
        ):
            job_id = ids[label] = str(uuid4())
            files = destination_sets.get(label, ["legacy-output"])
            row = dict(
                JobID=job_id,
                ConsumerKind=consumer,
                AccountKey=account,
                DestinationSetHash=digest(sorted(files)),
                InputHash=digest(label),
                StorageOwner=owner,
                EnqueueSequence=1,
                State="failed",
                OwnerID=str(uuid4()),
                Fence=1,
                Version=1,
                CreatedUTC=datetime(2026, 10, 1),
                UpdatedUTC=datetime(2026, 10, 1),
                Actor="test",
                Reason="temp fixture",
                ProvenanceJson="{}",
            )
            if consumer == "new_source":
                row.update(
                    SourceKey="snapshot_report_v1", IntentID=str(uuid4()), KVK_NO=1, PoolEpoch=1
                )
            else:
                row.update(SpoolKey="immutable", SpoolBytes=10)
            columns = list(row)
            placeholders = [
                "CAST(? AS binary(32))" if name.endswith("Hash") else "?" for name in columns
            ]
            sql.execute(
                f"INSERT #ExportJob ({','.join(columns)}) VALUES ({','.join(placeholders)})",
                *(row[name] for name in columns),
            )
            for key in ["account:" + account, *("destination:" + f for f in files)]:
                sql.execute(
                    "IF NOT EXISTS(SELECT 1 FROM #ExportResource WHERE ResourceKey=?) INSERT #ExportResource(ResourceKey,ResourceKind,Fence,Version) VALUES (?,?,0,1)",
                    key,
                    key,
                    key.split(":")[0],
                )
                sql.execute(
                    "INSERT #ExportJobResource(JobID,ResourceKey) VALUES (?,?)", job_id, key
                )
        yield dal, ids, sql
    finally:
        sql.close()


def test_discovery_and_direct_lookup_require_exact_registered_custody(scoped_jobs):
    dal, ids, _ = scoped_jobs
    assert set(dal.pending_jobs()) == {ids["registered"], ids["legacy"]}
    for key in ("foreign", "foreign-disk", "foreign-account"):
        with pytest.raises(SourceConflict):
            dal.job(ids[key])
    assert dal.job(ids["registered"])["job"]["ConsumerKind"] == "new_source"
    assert dal.job(ids["legacy"])["job"]["StorageOwner"] == "disk"


def test_hash_match_does_not_bypass_complete_resource_membership(scoped_jobs):
    dal, ids, sql = scoped_jobs
    sql.execute(
        "DELETE #ExportJobResource WHERE JobID=? AND ResourceKey='destination:slot-one'",
        ids["registered"],
    )
    sql.commit()
    with pytest.raises(SourceConflict, match="membership"):
        dal.job(ids["registered"])


def test_confirmed_damage_is_discovered_and_repair_lookup_is_scoped(scoped_jobs):
    dal, ids, sql = scoped_jobs
    sql.execute(
        "UPDATE #ExportJob SET State='confirmed',ProvenanceJson=? WHERE JobID=?",
        json.dumps(dict(reconciliations=[dict(proof=dict(state="damaged"))])),
        ids["registered"],
    )
    sql.commit()
    assert ids["registered"] in dal.pending_jobs()
    assert dal.repairs(ids["registered"]) == []
    # A foreign registered set cannot masquerade as an admitted repair of this job.
    sql.execute(
        "UPDATE #ExportJob SET RepairID=?,ProvenanceJson=? WHERE JobID=?",
        str(uuid4()),
        json.dumps(dict(repair=dict(snapshot=dict(job=dict(JobID=ids["registered"]))))),
        ids["foreign"],
    )
    sql.commit()
    assert dal.repairs(ids["registered"]) == []
