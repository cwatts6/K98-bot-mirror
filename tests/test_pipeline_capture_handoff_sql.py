"""The lineage query runs under a real restricted login against isolated schema."""

from datetime import datetime
import json
import os
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.pipeline_capture_handoff_dal import PipelineCaptureHandoffDAL
from tests.test_import_capture_recovery_sql import recovery as recovery
from tests.test_pipeline_decision_restricted_sql import pipeline as pipeline
from tests.test_processing_pipeline_recovery_sql import pipeline as pipeline_base  # noqa: F401

pytestmark = [
    pytest.mark.skipif(
        os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Local isolated SQL opt-in"
    ),
    pytest.mark.parametrize("recovery", ["scan_data"], indirect=True),
]


def seed(p):
    cursor = p.owner.execute("SELECT * FROM dbo.ExportPreparation")
    source = dict(zip([c[0] for c in cursor.description], cursor.fetchone(), strict=True))
    stages = p.dal.snapshot(p.run_id)["stages"]
    request = json.loads(source["RequestJson"])
    request["request"]["producer"] = dict(
        kind="stats_import", operation=str(stages["import"]["OperationID"]).lower()
    )
    p.owner.execute(
        "UPDATE dbo.ExportPreparation SET RequestJson=? WHERE PreparationID=?",
        json.dumps(request),
        source["PreparationID"],
    )
    source["RequestJson"] = json.dumps(request)
    job_id, target_id = str(uuid4()), str(uuid4())
    request["request"]["producer"] = dict(
        kind="configuration_import", operation=str(stages["configuration"]["OperationID"]).lower()
    )
    target = dict(
        source,
        PreparationID=target_id,
        RequestJson=json.dumps(request),
        RequestHash=digest(request),
        State="materialized",
        JobID=job_id,
        SpoolKey="synthetic-retained",
        SpoolBytes=123,
        SpoolHash=b"h" * 32,
        GenerationJson="{}",
    )
    # Existing valid committed generation is retained; this fixture isolates the
    # real lineage query, while byte-validation callbacks have separate tests.
    scope = json.loads(p.runtime.configuration)["scan_data"]
    now = datetime(2026, 10, 24)
    job = dict(
        JobID=job_id,
        ConsumerKind="scan_data",
        AccountKey="a",
        DestinationSetHash=digest(tuple(sorted(scope["destinations"]))),
        InputHash=b"h" * 32,
        SpoolKey="synthetic-retained",
        SpoolBytes=123,
        StorageOwner="disk-a",
        EnqueueSequence=1,
        State="uncertain",
        OwnerID=str(uuid4()),
        Fence=1,
        Version=1,
        CreatedUTC=now,
        UpdatedUTC=now,
        Actor="synthetic",
        Reason="lineage validation",
        ProvenanceJson="{}",
    )
    for table, row in (("ExportJob", job), ("ExportPreparation", target)):
        columns = list(row)
        p.owner.execute(
            f"INSERT dbo.{table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
            *row.values(),
        )
    p.owner.execute(
        "UPDATE dbo.ProcessingPipelineStage SET State='observed',EvidenceJson=? WHERE RunID=? AND Stage='export'",
        json.dumps(dict(outcome="queued", preparation_id=target_id, job_id=job_id)),
        p.run_id,
    )
    p.runtime.verified_snapshot = lambda identifier: (target, None, {})
    return source, target, job_id


def test_restricted_lineage_query_follows_existing_uncertain_job_without_writes(pipeline):
    p = pipeline
    source, target, job_id = seed(p)
    before = p.owner.execute("SELECT COUNT(*),SUM(Version) FROM dbo.ExportPreparation").fetchone()
    link = PipelineCaptureHandoffDAL(p.runtime).inspect(source)
    assert link == dict(pipeline_id=p.run_id, job_id=job_id)
    assert tuple(
        p.owner.execute("SELECT COUNT(*),SUM(Version) FROM dbo.ExportPreparation").fetchone()
    ) == tuple(before)
    assert (
        p.owner.execute("SELECT State FROM dbo.ExportJob WHERE JobID=?", job_id).fetchval()
        == "uncertain"
    )


def test_restricted_lineage_rejects_job_from_another_configuration_operation(pipeline):
    p = pipeline
    source, target, _ = seed(p)
    request = json.loads(target["RequestJson"])
    request["request"]["producer"]["operation"] = str(uuid4())
    p.owner.execute(
        "UPDATE dbo.ExportPreparation SET RequestJson=? WHERE PreparationID=?",
        json.dumps(request),
        target["PreparationID"],
    )
    with pytest.raises(SourceConflict, match="linkage"):
        PipelineCaptureHandoffDAL(p.runtime).inspect(source)
