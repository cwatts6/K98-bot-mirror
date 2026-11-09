"""Large guided replacement membership on temporary SQL, with no remote requests."""

import json
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import digest
from services.export_enrollment_service import enrollment_scope
from services.export_recovery_dal import ExportRecoveryDAL
from services.export_runtime_composition import RuntimeRegistration
from services.legacy_export_snapshot_service import configuration_digest
from tests import test_export_target_containment as authority_fixture
from tests.test_export_replacement_verification_sql import (
    contained_job as contained_job,
    proposal_service as proposal_service,
    pytestmark as pytestmark,
    verification as verification,
)


@pytest.fixture
def recovery(contained_job):
    service, f, docs = authority_fixture.recovery.__wrapped__(contained_job)
    files = ["old-file", *(f"old{i:04}" for i in range(699))]
    config = service.registration.value()
    config["legacy_configuration"]["scan_data"]["destinations"] = files
    config["protected_file_ids"] = sorted(set(config["protected_file_ids"]) | set(files))
    service.registration = RuntimeRegistration(config)
    service.discovery = ExportRecoveryDAL(f.connect, registration=service.registration)
    resource = f.sql.execute(
        "SELECT * FROM #ExportResource WHERE ResourceKey='destination:old-file'"
    )
    original = dict(zip((d[0] for d in resource.description), resource.fetchone(), strict=True))
    for file in files[1:]:
        f.insert("ExportResource", dict(original, ResourceKey="destination:" + file))
        f.insert("ExportJobResource", dict(JobID=f.job, ResourceKey="destination:" + file))
    scope = json.loads(f.sql.execute("SELECT ScopeJson FROM #ExportExecutionStream").fetchval())
    scope["resources"] = [
        dict(key=key, version=3)
        for key in sorted(["account:test-account", *("destination:" + file for file in files)])
    ]
    f.sql.execute(
        "UPDATE #ExportExecutionStream SET ScopeJson=?,RegistrationHash=CAST(? AS binary(32))",
        json.dumps(scope),
        bytes.fromhex(configuration_digest(config["legacy_configuration"]["scan_data"])),
    )
    f.sql.execute(
        "UPDATE #ExportJob SET DestinationSetHash=CAST(? AS binary(32))", digest(sorted(files))
    )
    return service, f, docs


def test_large_verification_admits_complete_membership_and_guided_discard(verification):
    r = verification
    assert len(r.plan.sql_json.encode("utf-16-le")) > 65536
    admitted = r.service._admit(
        r.plan,
        actor="recovery:" + r.plan.value()["plan_id"],
        reason="Check complete large output group",
    )
    worker, claim = admitted
    stream_id = str(uuid4())
    scope = enrollment_scope(r.plan, claim)
    assert len(scope["ScopeJson"].encode("utf-16-le")) > 65536
    worker.open_stream(stream_id=stream_id, scope=scope)
    state = r.service.inspect(r.plan.value()["plan_id"])
    assert state["files_total"] == 700 and state["files_requested"] == 0
    assert (
        r.f.sql.execute(
            "SELECT COUNT(*) FROM #ExportPreparationResource WHERE PreparationID=?",
            r.plan.value()["plan_id"],
        ).fetchval()
        == 701
    )
    discarded = r.service.discard(
        r.plan.value()["plan_id"],
        token=state["token"],
        actor="recovery:" + str(uuid4()),
        reason="Admin cancelled this read-only check",
    )
    assert discarded["state"] == "discarded"
    assert not r.runtime.sent
    assert (
        r.f.sql.execute(
            "SELECT COUNT(*) FROM #ExportResource WHERE ActivePreparationID IS NOT NULL"
        ).fetchval()
        == 0
    )
