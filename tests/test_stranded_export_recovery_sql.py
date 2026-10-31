"""Real SQL CAS/freeze/failure transitions in a disposable local database.

Private evidence and native termination are covered separately. Synthetic hashes
here are not represented as provider or production closure receipts.
"""

import os
from pathlib import Path
from uuid import uuid4

import pytest
from test_export_target_containment_sql import contained_job  # noqa: F401
from test_legacy_export_closeout_sql import installed  # noqa: F401

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_coordination_dal import Claim, ExportCoordinationDAL
from services.export_execution_dal import ExportExecutionDAL
from services.legacy_export_closeout_dal import LegacyExportCloseoutDAL
from services.stranded_export_recovery_dal import StrandedExportRecoveryDAL

pytestmark = pytest.mark.skipif(
    os.getenv("K98_LEGACY_CLOSEOUT_SQL") != "1", reason="Explicit disposable SQL opt-in"
)


def test_frozen_writer_then_uncertain_job_keeps_every_reservation(installed):  # noqa: F811
    f = installed
    # Match the installed direct-application profile only on the two tables
    # whose pre-existing Bot failure transition owns these writes.
    source = (
        Path(os.environ["K98_LEGACY_CLOSEOUT_SQL_SOURCE"])
        / "sql_schema/dbo.ExportAttemptPart.Table.sql"
    )
    f.owner.execute(source.read_text(encoding="utf-8-sig"))
    f.owner.execute(
        "GRANT SELECT,INSERT,UPDATE ON dbo.ExportAttemptPart TO ExportExecutionAuthority"
    )
    f.owner.execute("REVOKE INSERT ON dbo.ExportAttempt FROM ExportExecutionAuthority")
    f.owner.execute("GRANT INSERT ON dbo.ExportAttempt TO ExportExecutionAuthority")
    for table in ("ExportJob", "ExportResource", "ExportAttempt"):
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
    coordinator = StrandedExportRecoveryDAL(dal)
    initial = coordinator.snapshot(f.values["JobID"])
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
    claim = Claim(
        job["JobID"],
        job["AccountKey"],
        job["OwnerID"],
        job["Fence"],
        job["Version"],
        tuple((r["ResourceKey"], r["Version"]) for r in initial["resources"]),
    )
    original_dal = ExportCoordinationDAL(
        f.connect, preparations=True, output_operations=True, execution_evidence=True
    )
    destinations = [
        key.removeprefix("destination:")
        for key in initial["membership"]
        if key.startswith("destination:")
    ]
    parts = [
        dict(file_id=file_id, role="output", manifest_hash="ab" * 32, grids=1, rows=1, cells=1)
        for file_id in destinations
    ]
    original_dal.begin_attempt(claim, dict(export_key=job["InputHash"]), parts)
    reviewed = coordinator.snapshot(job["JobID"])
    # Any changed part must abort before the existing fail transition can mutate anything.
    f.owner.execute("UPDATE dbo.ExportAttemptPart SET CellCount=CellCount+1")
    changed = coordinator.snapshot(job["JobID"])
    with pytest.raises(SourceConflict, match="history changed"):
        coordinator.fail_reviewed(claim, reviewed)
    assert coordinator.snapshot(job["JobID"]) == changed
    f.owner.execute("UPDATE dbo.ExportAttemptPart SET CellCount=CellCount-1")
    coordinator.fail_reviewed(claim, reviewed)
    after = coordinator.snapshot(job["JobID"])
    assert len(after["attempts"]) == len(reviewed["attempts"]) == 1
    for before_attempt, after_attempt in zip(reviewed["attempts"], after["attempts"], strict=True):
        assert (
            after_attempt["Phase"] == "uncertain"
            and after_attempt["Version"] == before_attempt["Version"] + 1
        )
        assert {
            k: v for k, v in after_attempt.items() if k not in {"Phase", "Version", "UpdatedUTC"}
        } == {
            k: v for k, v in before_attempt.items() if k not in {"Phase", "Version", "UpdatedUTC"}
        }
    assert [p["FileID"] for p in after["attempt_parts"]] == destinations
    assert all(
        p["QuarantineState"] == "quarantined" and p["Version"] == 2 for p in after["attempt_parts"]
    )
    for before_part, after_part in zip(
        reviewed["attempt_parts"], after["attempt_parts"], strict=True
    ):
        mutable = {"Version", "QuarantineState", "QuarantinedUTC", "QuarantineReason"}
        assert {k: v for k, v in before_part.items() if k not in mutable} == {
            k: v for k, v in after_part.items() if k not in mutable
        }
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
        coordinator.fail_reviewed(claim, reviewed)
    assert coordinator.snapshot(job["JobID"]) == after
