"""Missing activation receipts use independently verified dependency witnesses."""

import json
import os
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID

import pytest

from core.export_execution_host import PrivateEvidenceStore
from kvk.dal.new_source_import_dal import SourceConflict
from scripts.run_export_authority import AuthorityBroker
from services.export_evidence_recovery import EvidenceRecoveryAdapter
from services.export_replacement_authority import ReplacementAuthority
from services.export_runtime_composition import LocalAuthorityClient
from services.recovery_release_policy import p0a_presentation
from services.recovery_service import RecoveryActor, RecoveryService
from tests.test_export_replacement_activation_sql import activation as activation
from tests.test_export_replacement_verification_sql import (
    contained_job as contained_job,
    proposal_service as proposal_service,
    recovery as recovery,
    verification as verification,
)
from tests.test_guided_recovery import ACTOR, Store

pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Local SQL opt-in"
)


@pytest.fixture
def guided(activation, tmp_path, monkeypatch):
    r = activation
    expected = r.apply()
    private = PrivateEvidenceStore(
        tmp_path, "disk", protect=lambda b: b[::-1], unprotect=lambda b: b[::-1]
    )
    for key, raw in r.docs.items():
        for name in (UUID(key).hex, "replica_" + UUID(key).hex):
            (tmp_path / name).write_bytes(raw[::-1])
    r.service.authority.store = r.service.proposals.store = (
        r.service.proposals.containment.store
    ) = private
    row = r.activation.dal.chain("test-account")[0]
    reference = str(UUID(row["ReceiptReference"]))
    for name in (UUID(reference).hex, "replica_" + UUID(reference).hex):
        (tmp_path / name).unlink()
    # Inventory is separately qualified; all dependency, journal, authority and
    # mutation paths in this fixture use actual services and temporary SQL.
    binding = dict(reference=reference, sha256=row["ReceiptHash"], kinds=["replacement activation"])
    monkeypatch.setattr(
        "services.export_evidence_recovery.EvidenceCatalogDAL",
        lambda *_: SimpleNamespace(get=lambda key: binding),
    )
    broker = AuthorityBroker(
        r.service.authority,
        r.service.proposals.registration,
        boundary=SimpleNamespace(fingerprint="a" * 64, recheck=Mock()),
    )
    broker.replacements = ReplacementAuthority(broker)
    client = LocalAuthorityClient(broker)
    journal = Store()

    def restart():
        return RecoveryService(
            journal,
            {"private_evidence": EvidenceRecoveryAdapter(client)},
            admin_id=1,
            guild_id=2,
            channel_id=3,
            presentation_policy=p0a_presentation,
        )

    service = restart()
    return SimpleNamespace(**locals())


def confirm(g, incident, actor=ACTOR):
    return g.service.execute(
        actor,
        incident["IncidentID"],
        incident["Revision"],
        incident["EvidenceHash"],
        "attest_registration",
        "Verify independent registration dependencies",
    )


@pytest.mark.asyncio
async def test_registration_attestation_real_admin_confirmation(guided, monkeypatch):
    from tests.p0_attestation_ui_harness import confirm_through_view

    row = guided.service.review_source(ACTOR, "private_evidence", guided.reference)
    current = await confirm_through_view(monkeypatch, guided.service, row, "attest_registration")
    assert current["evidence"]["original_receipt_verified"] is False


def test_registration_recovery_is_confirmed_and_survives_lost_reply_restart(guided, monkeypatch):
    g = guided
    with pytest.raises(SourceConflict):
        g.broker.replacements.current()
    before = g.r.activation.dal.chain("test-account")
    requests = len(g.r.runtime.sent)
    incident = g.service.review_source(ACTOR, "private_evidence", g.reference)
    assert set(incident["evidence"]["actions"]) == {"attest_registration"}
    with pytest.raises(SourceConflict, match="configured admin"):
        confirm(g, incident, RecoveryActor(9, 2, 3))
    dispatch = g.client.evidence_recovery
    attempts = []

    def lost(operation, **kwargs):
        result = dispatch(operation, **kwargs)
        if operation == "attest_registration":
            attempts.append(operation)
            raise TimeoutError("Lost acknowledged registration attestation")
        return result

    monkeypatch.setattr(g.client, "evidence_recovery", lost)
    result = confirm(g, incident)
    assert result["State"] == "resolved"
    assert result["evidence"]["original_receipt_verified"] is False
    g.service = g.restart()
    assert confirm(g, incident)["State"] == "resolved"
    assert len(attempts) == len(g.journal.actions) == 1
    assert g.journal.actions[0]["State"] == "verified"
    assert g.broker.replacements.current()["registration"] == g.expected["registration"]
    assert g.r.activation.dal.chain("test-account") == before
    assert len(g.r.runtime.sent) == requests
    assert not (g.tmp_path / UUID(g.reference).hex).exists()
    assert (
        g.r.f.sql.execute("SELECT State FROM #ExportJob WHERE JobID=?", g.r.f.job).fetchval()
        == "uncertain"
    )


@pytest.mark.parametrize("damage", ["configuration", "proposal", "read_journal", "account"])
def test_registration_cannot_be_reconstructed_from_sql_or_admin_assertions(guided, damage):
    g = guided
    incident = g.service.review_source(ACTOR, "private_evidence", g.reference)
    if damage == "configuration":
        forged = json.loads(g.row["RegistrationJson"])
        forged["legacy_configuration"]["scan_data"]["destinations"] = ["foreign-file"]
        g.r.f.sql.execute(
            "UPDATE #ExportReplacementActivation SET RegistrationJson=?", json.dumps(forged)
        )
    elif damage == "account":
        g.r.f.sql.execute("UPDATE #ExportReplacementActivation SET AccountKey='foreign'")
    else:
        sql = (
            "SELECT ReceiptReference FROM #ExportReplacementPlan"
            if damage == "proposal"
            else "SELECT TOP(1) r.PayloadReference FROM #ExportProviderRequest r JOIN #ExportExecutionStream s ON s.StreamID=r.StreamID WHERE s.PreparationID IS NOT NULL AND r.PayloadReference IS NOT NULL"
        )
        reference = g.r.f.sql.execute(sql).fetchval()
        for name in (UUID(reference).hex, "replica_" + UUID(reference).hex):
            (g.tmp_path / name).unlink()
    with pytest.raises((SourceConflict, KeyError)):
        confirm(g, incident)
    assert g.r.f.sql.execute("SELECT COUNT(*) FROM #ExportRegistrationAttestation").fetchval() == 0
    if damage == "account":
        assert g.broker.replacements.current()["registration"] == g.broker.base_registration.value()
    else:
        with pytest.raises((SourceConflict, KeyError)):
            g.broker.replacements.current()


def test_loss_of_new_witness_requires_another_separate_confirmation(guided):
    g = guided
    incident = g.service.review_source(ACTOR, "private_evidence", g.reference)
    assert confirm(g, incident)["State"] == "resolved"
    reference = g.r.f.sql.execute(
        "SELECT ReceiptReference FROM #ExportRegistrationAttestation"
    ).fetchval()
    for name in (UUID(reference).hex, "replica_" + UUID(reference).hex):
        (g.tmp_path / name).unlink()
    current = g.service.review(ACTOR, incident["IncidentID"])
    assert current["State"] == "open"
    assert set(current["evidence"]["actions"]) == {"attest_registration"}
    assert confirm(g, current)["State"] == "resolved"
    assert g.r.f.sql.execute("SELECT COUNT(*) FROM #ExportRegistrationAttestation").fetchval() == 2
