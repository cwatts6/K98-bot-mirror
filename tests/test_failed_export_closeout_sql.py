"""Closeout CAS against authoritative tables in a disposable SQL session."""

import json
import os
from uuid import uuid4

import pytest
import test_export_target_containment_sql as fixture_module
from test_export_target_containment_sql import contained_job  # noqa: F401

from kvk.dal.new_source_import_dal import SourceConflict
from services.failed_export_closeout_dal import FailedExportCloseoutDAL

pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Explicit local temporary SQL opt-in"
)


@pytest.fixture(autouse=True)
def catalog_tables(monkeypatch):
    monkeypatch.setattr(
        fixture_module,
        "TABLES",
        (
            *fixture_module.TABLES,
            "dbo.ExportReplacementPlan",
            "dbo.ExportReplacementVerification",
            "dbo.ExportReplacementActivation",
            "dbo.ExportReconciliationProof",
        ),
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


@pytest.mark.parametrize("damage", ["missing", "corrupt"])
def test_retirement_receipt_is_discovered_and_guided_replica_restore_verifies(
    contained_job, tmp_path, damage  # noqa: F811
):
    from threading import RLock
    from types import SimpleNamespace
    from unittest.mock import Mock
    from uuid import UUID

    from core.export_execution_host import PrivateEvidenceStore
    from services.export_evidence_catalog_dal import EvidenceCatalogDAL
    from services.export_evidence_recovery import EvidenceRecovery, EvidenceRecoveryAdapter
    from services.recovery_service import RecoveryService
    from tests.test_guided_recovery import ACTOR, Store

    fixture = contained_job
    dal = prepare(fixture)
    private = PrivateEvidenceStore(
        tmp_path, "disk", protect=lambda b: b[::-1], unprotect=lambda b: b[::-1]
    )
    raw = b'{"kind":"failed_export_retirement/1","test":"exact retained bytes"}'
    saved = private.put(raw)
    reference = str(UUID(saved.key))
    dal.retire(dal.snapshot(fixture.job), dict(reference=reference, sha256=saved.sha256))
    catalog = EvidenceCatalogDAL(fixture.connect, "test-account")
    assert reference in catalog.page()
    assert catalog.get(reference)["kinds"] == ["failed export retirement"]
    with pytest.raises(SourceConflict):
        EvidenceCatalogDAL(fixture.connect, "foreign").get(reference)
    primary = tmp_path / saved.key
    if damage == "missing":
        primary.unlink()
    else:
        primary.write_bytes(b"corrupt")
    broker = SimpleNamespace(
        authority=SimpleNamespace(
            dal=SimpleNamespace(connect=fixture.connect), store=private, _lock=RLock()
        ),
        base_registration=SimpleNamespace(value=lambda: dict(account="test-account")),
        boundary=SimpleNamespace(recheck=Mock()),
    )

    def rpc(operation, **values):
        return EvidenceRecovery(broker).dispatch(
            dict(version=1, action="evidence_recovery", operation=operation, **values)
        )

    adapter = EvidenceRecoveryAdapter(SimpleNamespace(evidence_recovery=rpc))
    service = RecoveryService(
        Store(), {adapter.kind: adapter}, admin_id=1, guild_id=2, channel_id=3
    )
    row = service.review_source(ACTOR, adapter.kind, reference)
    assert "restore_evidence" in row["evidence"]["actions"]
    done = service.execute(
        ACTOR,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "restore_evidence",
        "Restore original decision",
    )
    assert done["State"] == "resolved" and private.read(saved) == raw
