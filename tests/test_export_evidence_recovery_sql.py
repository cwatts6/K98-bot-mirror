"""Real inventory queries and guided repair of a completed activation receipt.

Only temporary SQL objects and simulated provider children are used. DPAPI is
replaced by reversible test encoding; OS peer authentication is not exercised.
"""

from datetime import datetime
import hashlib
import json
from uuid import UUID, uuid4

import pytest

from core.export_execution_host import PrivateEvidenceStore
from kvk.dal.new_source_import_dal import SourceConflict
from services.export_evidence_catalog_dal import EvidenceCatalogDAL
from services.export_evidence_recovery import EvidenceRecoveryAdapter
from services.export_evidence_storage import EvidenceCopies
from services.recovery_service import RecoveryService
from tests import test_export_target_containment_sql as fixture_module
from tests.test_export_replacement_rpc_sql import (
    contained_job as contained_job,
    guided as guided,
    guided_completion,
    proposal_service as proposal_service,
    pytestmark as pytestmark,
    recovery as recovery,
    rpc as rpc,
    store as store,
    verification as verification,
)
from tests.test_guided_recovery import ACTOR


@pytest.fixture(autouse=True)
def proof_catalogue(monkeypatch):
    monkeypatch.setattr(
        fixture_module, "TABLES", (*fixture_module.TABLES, "dbo.ExportReconciliationProof")
    )


def test_proof_audit_hex_key_is_discovered_and_scoped_to_its_account(rpc, tmp_path):
    r = rpc
    private = PrivateEvidenceStore(
        tmp_path, "disk", protect=lambda b: b[::-1], unprotect=lambda b: b[::-1]
    )
    raw = b'{"kind":"saved-reconciliation-audit"}'
    receipt = private.put(raw)
    reference = str(UUID(receipt.key))
    r.f.insert(
        "ExportReconciliationProof",
        dict(
            ProofID=str(uuid4()),
            SessionID=r.f.session,
            AccountKey="test-account",
            SnapshotHash=b"s" * 32,
            RegistrationHash=b"r" * 32,
            ProofKind="publication",
            Outcome="confirmed",
            MembershipHash=b"m" * 32,
            MembershipJson="[]",
            EvidenceJson=json.dumps(dict(evidence_id=receipt.key, evidence_hash=receipt.sha256)),
            CreatedUTC=datetime(2026, 10, 1),
        ),
    )
    r.f.sql.commit()
    catalog = EvidenceCatalogDAL(r.f.connect, "test-account")
    assert reference in catalog.page()
    assert catalog.get(reference)["kinds"] == ["reconciliation audit"]
    with pytest.raises(SourceConflict, match="outside"):
        EvidenceCatalogDAL(r.f.connect, "another-account").get(reference)
    r.broker.authority.store = private
    (tmp_path / receipt.key).unlink()
    adapter = EvidenceRecoveryAdapter(r.rpc_runtime.client)
    service = RecoveryService(
        r.recovery.store, {adapter.kind: adapter}, admin_id=1, guild_id=2, channel_id=3
    )
    row = service.review_source(ACTOR, adapter.kind, reference)
    done = service.execute(
        ACTOR,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "restore_evidence",
        "Confirm saved audit restoration",
    )
    assert done["State"] == "resolved" and private.read(receipt) == raw


@pytest.mark.parametrize("damage", ["missing", "corrupt"])
def test_sql_inventory_to_admin_restore_then_original_history_verification(rpc, tmp_path, damage):
    r = rpc
    guided_completion(r)
    private = PrivateEvidenceStore(
        tmp_path, "disk", protect=lambda b: b[::-1], unprotect=lambda b: b[::-1]
    )
    # Transfer the fixture's already-authored private documents without changing
    # their identities or bytes. This represents a pre-existing protected store.
    documents = r.docs
    for reference, raw in documents.items():
        key = UUID(str(reference)).hex
        (tmp_path / key).write_bytes(raw[::-1])
        EvidenceCopies(private).repair(reference, hashlib.sha256(raw).digest())
    r.broker.authority.store = private
    before = r.broker.replacements.current()
    saved = r.f.sql.execute(
        "SELECT ReceiptReference,ReceiptHash FROM #ExportReplacementActivation"
    ).fetchone()
    reference, expected = str(saved[0]).lower(), bytes(saved[1])
    catalog = EvidenceCatalogDAL(r.f.connect, "test-account")
    assert reference in catalog.page()
    assert catalog.get(reference) == dict(
        reference=reference, sha256=expected.hex(), kinds=["replacement activation"]
    )
    with pytest.raises(SourceConflict, match="outside"):
        EvidenceCatalogDAL(r.f.connect, "another-account").get(reference)
    path = tmp_path / UUID(reference).hex
    if damage == "missing":
        path.unlink()
    else:
        path.write_bytes(b"damaged")
    with pytest.raises(SourceConflict, match="Private replacement evidence"):
        r.broker.replacements.current()
    adapter = EvidenceRecoveryAdapter(r.rpc_runtime.client)
    service = RecoveryService(
        r.recovery.store, {adapter.kind: adapter}, admin_id=1, guild_id=2, channel_id=3
    )
    row = service.review_source(ACTOR, adapter.kind, reference)
    assert row["evidence"]["actions"]["restore_evidence"]["label"] == "Restore verified evidence"
    restarted = RecoveryService(
        service.store, service.adapters, admin_id=1, guild_id=2, channel_id=3
    )
    done = restarted.execute(
        ACTOR,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "restore_evidence",
        "Confirmed saved activation evidence",
    )
    assert done["State"] == "resolved" and not done["pending_action"]
    assert r.broker.replacements.current() == before
    assert (
        r.f.sql.execute("SELECT State FROM #ExportJob WHERE JobID=?", r.f.job).fetchval()
        == "uncertain"
    )
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementDelivery").fetchval() == 1
