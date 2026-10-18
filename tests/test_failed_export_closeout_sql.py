"""Closeout CAS against authoritative tables in a disposable SQL session."""

import json
import os
from uuid import uuid4

import pytest
from test_export_target_containment_sql import contained_job  # noqa: F401

from kvk.dal.new_source_import_dal import SourceConflict
from services.failed_export_closeout_dal import FailedExportCloseoutDAL

pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Explicit local temporary SQL opt-in"
)


def prepare(fixture):
    fixture.sql.execute("UPDATE #ExportJob SET State='failed'")
    fixture.sql.execute("UPDATE #ExportResource SET ActiveJobID=NULL,OwnerID=NULL")
    return FailedExportCloseoutDAL(fixture.connect, account="test-account", storage_owner="disk")


def test_closeout_preserves_failed_history_and_resources(contained_job):  # noqa: F811
    fixture = contained_job
    dal = prepare(fixture)
    before = dal.snapshot(fixture.job)
    marker = dict(reference=str(uuid4()), sha256="a" * 64)
    dal.retire(before, marker)
    after = dal.snapshot(fixture.job)
    assert after["job"]["Version"] == before["job"]["Version"] + 1
    assert after["job"]["State"] == "failed"
    assert after["streams"] == before["streams"]
    assert not after["held"] and not after["attempts"]
    assert json.loads(after["job"]["ProvenanceJson"])["failed_export_retired"] == marker
    with pytest.raises(SourceConflict):
        dal.retire(before, marker)


def test_foreign_custody_and_changed_job_rejected(contained_job):  # noqa: F811
    fixture = contained_job
    dal = prepare(fixture)
    before = dal.snapshot(fixture.job)
    with pytest.raises(SourceConflict):
        FailedExportCloseoutDAL(fixture.connect, account="foreign", storage_owner="disk").snapshot(
            fixture.job
        )
    fixture.sql.execute("UPDATE #ExportJob SET Version=Version+1")
    fixture.sql.commit()
    with pytest.raises(SourceConflict):
        dal.retire(before, dict(reference=str(uuid4()), sha256="a" * 64))
    assert "failed_export_retired" not in json.loads(
        dal.snapshot(fixture.job)["job"]["ProvenanceJson"]
    )
