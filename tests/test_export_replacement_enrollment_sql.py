"""Replacement verification admission cannot bypass healthy work or old fences."""

import json
import os
from types import SimpleNamespace
from uuid import uuid4

import pytest

from tests import test_export_target_containment_sql as fixture_module
from tests.test_export_manual_enrollment import manual_value

contained_job = fixture_module.contained_job
pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Explicit temporary SQL opt-in"
)


@pytest.fixture
def replacement_enrollment(monkeypatch, request):
    monkeypatch.setattr(
        fixture_module,
        "TABLES",
        (
            *fixture_module.TABLES,
            "dbo.ExportReplacementPlan",
            "dbo.ExportReplacementTarget",
            "dbo.ExportReplacementVerification",
            "dbo.ExportReplacementActivation",
        ),
    )
    monkeypatch.setattr(
        fixture_module,
        "PROCEDURES",
        (
            *fixture_module.PROCEDURES,
            "dbo.usp_ExportReplacementPlanCreate",
            "dbo.usp_ExportManualOutputEnrollmentTransition",
        ),
    )
    f = request.getfixturevalue("contained_job")
    pool, old_slots = fixture_module.pool_job(f)
    f.apply(PoolID=pool, PoolVersion=9, StorageOwner=None, ResourcesJson=json.dumps(f.resources))
    replacement_id = str(uuid4())
    mapping = [
        dict(old=old, new=f"fresh-file-{i}")
        for i, old in enumerate(["old-file", "old-slot-1", "old-slot-2"])
    ]
    f.sql.execute("BEGIN TRANSACTION")
    f.sql.execute(
        "EXEC #usp_ExportReplacementPlanCreate @ReplacementID=?,@ContainmentID=?,@AccountKey='test-account',"
        "@BaseRegistrationHash=?,@ProjectedRegistrationHash=?,@ReceiptHash=?,@ReceiptReference=?,"
        "@MappingJson=?,@Actor='test',@Reason='Verify replacements'",
        replacement_id,
        f.arguments["ContainmentID"],
        b"a" * 32,
        b"b" * 32,
        b"r" * 32,
        str(uuid4()),
        json.dumps(mapping),
    ).fetchone()
    f.sql.execute("COMMIT")
    value = manual_value() | dict(
        account="test-account",
        owner_email="owner@example.test",
        plan_id=replacement_id,
        manifest_sha256=(b"m" * 32).hex(),
    )
    for file, binding in zip(value["files"], mapping, strict=True):
        file["file_id"] = binding["new"]

    def begin(plan=None):
        plan = plan or value
        return f.sql.execute(
            "EXEC #usp_ExportManualOutputEnrollmentTransition @SessionID=?,@PreparationID=?,"
            "@Action='begin',@ExpectedVersion=0,@AccountKey=?,@OwnerID=?,"
            "@PlanJson=?,@Actor='test',@Reason='Verify fresh outputs'",
            f.session,
            str(uuid4()),
            plan["account"],
            str(uuid4()),
            json.dumps(plan),
        ).fetchone()

    return SimpleNamespace(f=f, pool=pool, old_slots=old_slots, plan=value, begin=begin)


def test_explicit_replacement_can_verify_while_original_isolated_job_stays_uncertain(
    replacement_enrollment,
):
    r = replacement_enrollment
    result = r.begin()
    assert result.State == "preflight"
    assert (
        r.f.sql.execute("SELECT State FROM #ExportJob WHERE JobID=?", r.f.job).fetchval()
        == "uncertain"
    )
    assert [
        tuple(row) for row in r.f.sql.execute("SELECT * FROM #SourceOutputSlot ORDER BY SlotNo")
    ] == r.old_slots
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportContainedTarget").fetchval() == 3
    assert (
        r.f.sql.execute(
            "SELECT COUNT(*) FROM #ExportManualFileOrigin WHERE Stage='registered'"
        ).fetchval()
        == 3
    )
    assert (
        r.f.sql.execute(
            "SELECT COUNT(*) FROM #ExportManualFileOrigin WHERE Stage='eligible'"
        ).fetchval()
        == 0
    )


@pytest.mark.parametrize("damage", ["ordinary", "owner", "order", "missing", "foreign", "audience"])
def test_only_exact_replacement_plan_gets_the_admission_exception(replacement_enrollment, damage):
    import pyodbc

    r = replacement_enrollment
    plan = json.loads(json.dumps(r.plan))
    if damage == "ordinary":
        plan["plan_id"] = str(uuid4())
    elif damage == "owner":
        plan["owner_email"] = "different@example.test"
    elif damage == "order":
        plan["files"][1], plan["files"][2] = plan["files"][2], plan["files"][1]
    elif damage == "missing":
        plan["files"].pop()
    elif damage == "foreign":
        plan["files"][1]["file_id"] = "unapproved-file"
    else:
        plan.update(version=3, access_policy="public_viewer_link_v1")
    with pytest.raises(pyodbc.Error):
        r.begin(plan)
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportPreparation").fetchval() == 0
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportManualFileOrigin").fetchval() == 0


def test_ordinary_manual_enrollment_remains_available_for_an_uncontested_account(
    replacement_enrollment,
):
    r = replacement_enrollment
    plan = r.plan | dict(plan_id=str(uuid4()), account="uncontested-account")
    assert r.begin(plan).State == "preflight"
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementPlan").fetchval() == 1
    assert (
        r.f.sql.execute("SELECT State FROM #ExportJob WHERE JobID=?", r.f.job).fetchval()
        == "uncertain"
    )
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportManualFileOrigin").fetchval() == 3


def test_healthy_queued_work_keeps_priority_over_replacement_verification(replacement_enrollment):
    import pyodbc

    r = replacement_enrollment
    r.f.sql.execute(
        "INSERT #ExportJob(JobID,ConsumerKind,AccountKey,DestinationSetHash,InputHash,SpoolKey,SpoolBytes,StorageOwner,EnqueueSequence,State,Fence,Version,CreatedUTC,UpdatedUTC,Actor,Reason,ProvenanceJson) "
        "SELECT ?, 'scan_data',AccountKey,DestinationSetHash,InputHash,'retained',10,'disk',2,'ready',0,1,CreatedUTC,UpdatedUTC,Actor,Reason,ProvenanceJson FROM #ExportJob WHERE JobID=?",
        str(uuid4()),
        r.f.job,
    )
    with pytest.raises(pyodbc.Error, match="Existing work"):
        r.begin()
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportPreparation").fetchval() == 0
