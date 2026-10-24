"""Real SQL CAS/freeze/failure transitions in a disposable local database.

Private evidence and native termination are covered separately. Synthetic hashes
here are not represented as provider or production closure receipts.
"""

import os
from uuid import uuid4

import pytest
from test_export_target_containment_sql import contained_job  # noqa: F401
from test_legacy_export_closeout_sql import installed  # noqa: F401

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_coordination_dal import Claim, ExportCoordinationDAL
from services.export_execution_dal import ExportExecutionDAL
from services.legacy_export_closeout_dal import LegacyExportCloseoutDAL

pytestmark = pytest.mark.skipif(
    os.getenv("K98_LEGACY_CLOSEOUT_SQL") != "1", reason="Explicit disposable SQL opt-in"
)


def test_frozen_writer_then_uncertain_job_keeps_every_reservation(installed):  # noqa: F811
    f = installed
    # Match the installed direct-application profile only on the two tables
    # whose pre-existing Bot failure transition owns these writes.
    for table in ("ExportJob", "ExportResource"):
        f.owner.execute(f"REVOKE UPDATE ON dbo.{table} FROM ExportExecutionAuthority")
        f.owner.execute(f"GRANT UPDATE ON dbo.{table} TO ExportExecutionAuthority")
    f.owner.execute("DELETE dbo.ExportAttempt")
    f.owner.execute("UPDATE dbo.ExportJob SET State='running',Version=6")
    f.owner.execute("UPDATE dbo.ExportResource SET BlockedReason=NULL")
    f.owner.execute(
        "UPDATE dbo.ExportExecutionStream SET State='open',ActiveAccountKey=AccountKey,"
        "ClosedUTC=NULL,ClosureHash=NULL,ClosureReference=NULL,EventDigest=NULL"
    )
    dal = LegacyExportCloseoutDAL(f.connect, account="test-account", storage_owner="disk")
    initial = dal.snapshot(f.values["JobID"])
    job = initial["job"]
    stream = initial["streams"][0]
    execution = ExportExecutionDAL(f.connect)
    common = dict(
        SessionID=stream["SessionID"], StreamID=stream["StreamID"], AccountKey=job["AccountKey"]
    )
    frozen = execution.transition(
        "stream", **common, Action="freeze", ExpectedVersion=stream["Version"]
    )
    assert frozen["State"] == "frozen"
    closed = execution.transition(
        "stream",
        **common,
        Action="close",
        ExpectedVersion=frozen["Version"],
        ChildIdentity=stream["ChildIdentity"],
        ClosureHash=b"h" * 32,
        ClosureReference=str(uuid4()),
        EventDigest=b"d" * 32,
        LastSequence=stream["LastSequence"],
    )
    assert closed["State"] == "closed" and closed["ActiveAccountKey"] is None
    coordinator = ExportCoordinationDAL(
        f.connect, preparations=True, output_operations=True, execution_evidence=True
    )
    claim = Claim(
        job["JobID"],
        job["AccountKey"],
        job["OwnerID"],
        job["Fence"],
        job["Version"],
        tuple((r["ResourceKey"], r["Version"]) for r in initial["resources"]),
    )
    coordinator.fail(claim, retain_claims=True)
    after = dal.snapshot(job["JobID"])
    assert after["job"]["State"] == "uncertain" and after["job"]["Version"] == 7
    for field in (
        "InputHash",
        "SpoolKey",
        "SpoolBytes",
        "ProvenanceJson",
        "OwnerID",
        "Fence",
        "DestinationSetHash",
    ):
        assert after["job"][field] == initial["job"][field]
    assert after["membership"] == initial["membership"]
    assert all(
        r["ActiveJobID"] == job["JobID"] and r["BlockedReason"] == "Outcome requires reconciliation"
        for r in after["resources"]
    )
    with pytest.raises(SourceConflict):
        coordinator.fail(claim, retain_claims=True)
    assert dal.snapshot(job["JobID"]) == after
