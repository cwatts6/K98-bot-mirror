"""Session-local SQL cancellation, late admission fencing and rollback proofs."""

from dataclasses import replace
import json
import os
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services import config_preparation_recovery_dal as recovery_dal
from services.config_read_containment import verify_preparation_receipt
from tests import test_config_read_containment_sql as fixture_module
from tests.test_config_unstarted_read import publication_association

containment = fixture_module.containment
containment_schema = fixture_module.containment_schema
sql_fixture = fixture_module.sql_fixture

pytestmark = pytest.mark.skipif(
    os.environ.get("K98_READ_CONTAINMENT_SQL") != "1", reason="Explicit local temporary SQL opt-in"
)


def empty_preparation(containment, publication=True):
    repair, sql = containment
    original = repair.execution.read_stream(repair.target.stream_ids[0])
    request = {"read_configuration": str(uuid4())}
    if publication:
        request["configuration_import"] = publication_association()
    request = dict(
        consumer="config", kvk_no=None, request=request, storage_owner=repair.storage_owner
    )
    sql.execute("DELETE FROM #ExportExecutionStream")
    sql.execute(
        "UPDATE #ExportPreparation SET RequestJson=?,RequestHash=?",
        json.dumps(request),
        digest(request),
    )
    sql.commit()
    repair.target = replace(repair.target, stream_ids=())
    return repair, sql, original


@pytest.mark.parametrize("publication", [False, True])
def test_real_empty_claim_cancellation_fences_late_open_and_releases_admission(
    containment, publication
):
    import pyodbc

    repair, sql, original = empty_preparation(containment, publication)
    assert repair.dal.pending_recovery(
        account=repair.target.account, storage_owner=repair.storage_owner
    ) == [repair.target.preparation_id]
    report = repair.inspect()
    repair.apply(
        approved_snapshot_sha256=report["snapshot_sha256"],
        actor="test-admin",
        reason="Cancel unstarted read",
    )
    audit = json.loads(sql.execute("SELECT GenerationJson FROM #ExportPreparation").fetchval())
    verify_preparation_receipt(
        repair.store,
        audit,
        preparation_id=repair.target.preparation_id,
        account=repair.target.account,
        storage_owner=repair.storage_owner,
    )
    assert sql.execute("SELECT State FROM #ExportPreparation").fetchval() == "unavailable"
    assert sql.execute("SELECT COUNT(*) FROM #ExportExecutionStream").fetchval() == 0
    assert (
        sql.execute("SELECT COUNT(*) FROM #ExportResource WHERE OwnerID IS NOT NULL").fetchval()
        == 0
    )
    assert sql.execute("SELECT COUNT(*) FROM #ExportPreparationResource").fetchval() == 2
    sql.commit()
    sql.autocommit = True
    scope = json.dumps(
        {
            "resources": [
                {"key": key, "version": version} for key, version in repair.target.resources
            ]
        }
    )
    with pytest.raises(
        pyodbc.Error, match=r"Resource owner/fence/version conflict|Preparation CAS conflict"
    ):
        sql.execute(
            "EXEC #K98ReadContainment @SessionID=?,@StreamID=?,@Action='open',@ExpectedVersion=0,"
            "@AccountKey=?,@OwnerKind='preparation',@ObjectID=?,@OwnerID=?,@Fence=?,@ClaimVersion=?,"
            "@RegistrationHash=?,@SnapshotHash=?,@ScopeJson=?,@Purpose='probe',@ChildIdentity=?",
            original["SessionID"],
            str(uuid4()),
            repair.target.account,
            repair.target.preparation_id,
            repair.target.owner,
            repair.target.fence,
            repair.target.version,
            bytes.fromhex(repair.registration_hash),
            b"s" * 32,
            scope,
            str(uuid4()),
        )
    assert sql.execute("SELECT COUNT(*) FROM #ExportExecutionStream").fetchval() == 0
    assert (
        repair.dal.pending_recovery(
            account=repair.target.account, storage_owner=repair.storage_owner
        )
        == []
    )


def test_real_cancellation_rolls_back_every_release_on_cas_failure(containment, monkeypatch):
    repair, sql, _ = empty_preparation(containment)
    before = repair.inspect()
    real_cas, calls = recovery_dal._cas, []

    def fail_last(cursor, statement, *values):
        calls.append(statement)
        if len(calls) == 3:
            raise SourceConflict("Injected last reservation conflict")
        return real_cas(cursor, statement, *values)

    monkeypatch.setattr(recovery_dal, "_cas", fail_last)
    with pytest.raises(SourceConflict, match="last reservation"):
        repair.apply(
            approved_snapshot_sha256=before["snapshot_sha256"], actor="test", reason="Cancel"
        )
    assert repair.inspect() == before
    assert sql.execute("SELECT GenerationJson FROM #ExportPreparation").fetchval() is None


def test_real_new_stream_between_preview_and_transaction_prevents_release(containment, monkeypatch):
    repair, sql, original = empty_preparation(containment)
    report = repair.inspect()
    real_settle = repair.dal.settle

    def raced(target, expected, audit, **kwargs):
        columns = list(original)
        sql.execute(
            "INSERT INTO #ExportExecutionStream ("
            + ",".join(columns)
            + ") VALUES ("
            + ",".join("?" for _ in columns)
            + ")",
            *[original[k] for k in columns],
        )
        sql.commit()
        return real_settle(target, expected, audit, **kwargs)

    monkeypatch.setattr(repair.dal, "settle", raced)
    with pytest.raises(SourceConflict, match="Recovery raced"):
        repair.apply(
            approved_snapshot_sha256=report["snapshot_sha256"], actor="test", reason="Cancel"
        )
    assert sql.execute("SELECT State FROM #ExportPreparation").fetchval() == "uncertain"
    assert (
        sql.execute("SELECT COUNT(*) FROM #ExportResource WHERE OwnerID IS NOT NULL").fetchval()
        == 2
    )
