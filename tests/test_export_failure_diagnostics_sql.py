"""Failure diagnostics persist with conservative settlement in disposable SQL."""

import json

import pytest

from services.export_coordination_dal import Claim
from services.export_failure_diagnostics import failure_record
from tests import test_export_recovery_sql as fixtures
from tests.test_export_skip_sql import setup

scoped_jobs = fixtures.scoped_jobs
pytestmark = fixtures.pytestmark


@pytest.mark.parametrize("retain", [False, True])
@pytest.mark.parametrize("history", ["new", "recorded", "historical_retry"])
def test_failure_keeps_original_and_settles_exact_ownership(scoped_jobs, retain, history):
    adapter, job_id, sql, _ = setup(scoped_jobs, state="running")
    original = failure_record(ValueError("secret input"), job_id=job_id, stage="snapshot")
    provenance = {"retained": "unchanged"}
    if history == "recorded":
        provenance["first_failure"] = original
    if history == "historical_retry":
        provenance["safe_retry_history"] = [{"retained": "prior retry"}]
    sql.execute(
        "UPDATE #ExportJob SET ProvenanceJson=? WHERE JobID=?", json.dumps(provenance), job_id
    )
    before = adapter.discovery.job(job_id)["job"]
    sql.execute(
        "UPDATE #ExportResource SET ActiveJobID=?,OwnerID=?,Fence=1,Version=2 "
        "WHERE ResourceKey IN (SELECT ResourceKey FROM #ExportJobResource WHERE JobID=?)",
        job_id,
        before["OwnerID"],
        job_id,
    )
    sql.commit()
    snapshot = adapter.discovery.job(job_id)
    claim = Claim(
        job_id,
        "account",
        before["OwnerID"],
        1,
        before["Version"],
        tuple((r["ResourceKey"], r["Version"]) for r in snapshot["resources"]),
    )
    latest = failure_record(RuntimeError("private URL"), job_id=job_id, stage="delivery")
    adapter.coordinator.fail(claim, retain_claims=retain, diagnostic=latest)
    after = adapter.discovery.job(job_id)
    observed = json.loads(after["job"]["ProvenanceJson"])
    assert observed["retained"] == "unchanged"
    assert observed["latest_failure"] == latest
    if history == "historical_retry":
        assert "first_failure" not in observed
    else:
        assert observed["first_failure"] == (original if history == "recorded" else latest)
    assert after["job"]["State"] == ("uncertain" if retain else "failed")
    assert after["job"]["Version"] == before["Version"] + 1
    assert all(bool(r["ActiveJobID"]) == retain for r in after["resources"])
    assert all(bool(r["BlockedReason"]) == retain for r in after["resources"])
    assert "secret input" not in json.dumps(observed) and "private URL" not in json.dumps(observed)
