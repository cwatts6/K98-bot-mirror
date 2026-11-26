"""Authority proposal receipts against the actual temporary SQL transaction."""

import os
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, UncertainCommit
from services.export_replacement_dal import ExportReplacementDAL
from services.export_replacement_service import ExportReplacementService
from tests import (
    test_export_target_containment as authority_fixture,
    test_export_target_containment_sql as fixture_module,
)

contained_job = fixture_module.contained_job
recovery = authority_fixture.recovery
pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Explicit temporary SQL opt-in"
)


@pytest.fixture
def proposal_service(monkeypatch, request):
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
        (*fixture_module.PROCEDURES, "dbo.usp_ExportReplacementPlanCreate"),
    )
    containment, f, docs = request.getfixturevalue("recovery")
    original = containment.inspect(f.job)
    containment.apply(
        f.job, token=original["token"], actor="recovery:" + str(uuid4()), reason="Retire old output"
    )
    service = ExportReplacementService(
        dal=ExportReplacementDAL(f.connect),
        containment=containment,
        registration=containment.registration,
        store=containment.store,
    )
    args = dict(
        token=original["token"],
        replacements={
            old: "fresh-file" if old == "old-file" else "fresh-" + old
            for old in original["targets"]
        },
        actor="recovery:" + str(uuid4()),
        reason="Verify fresh output",
    )
    return service, f, docs, args


def test_original_proposal_survives_restart_without_asserting_verification(proposal_service):
    service, f, docs, args = proposal_service
    result = service.propose(f.job, **args)
    assert result["outcome"] == "verification_required"
    assert (
        result["business_resolved"]
        is result["registration_activated"]
        is result["files_verified"]
        is False
    )
    assert len(docs) == 2  # Original containment and immutable replacement proposal.
    restarted = ExportReplacementService(
        dal=ExportReplacementDAL(f.connect),
        containment=service.containment,
        registration=service.registration,
        store=service.store,
    )
    assert restarted.propose(f.job, **args) == result
    assert restarted.inspect(result["replacement_id"]) == result
    assert len(docs) == 2


def test_lost_proposal_commit_acknowledgement_never_rewrites_receipt(proposal_service, monkeypatch):
    service, f, docs, args = proposal_service
    original = service.dal.create
    calls = []

    def lost(**kwargs):
        calls.append(kwargs)
        original(**kwargs)
        raise UncertainCommit("Test reply lost after commit")

    monkeypatch.setattr(service.dal, "create", lost)
    with pytest.raises(UncertainCommit):
        service.propose(f.job, **args)
    result = service.propose(f.job, **args)
    assert result["outcome"] == "verification_required"
    assert len(calls) == 1 and len(docs) == 2


@pytest.mark.parametrize("damage", ["token", "mapping", "reason", "job"])
def test_replayed_action_cannot_change_the_admin_proposal(proposal_service, damage):
    service, f, docs, args = proposal_service
    service.propose(f.job, **args)
    job = f.job
    if damage == "token":
        args["token"] = "0" * 64
    elif damage == "mapping":
        args["replacements"] = {"old-file": "another-fresh"}
    elif damage == "reason":
        args["reason"] = "Changed decision"
    else:
        job = str(uuid4())
    with pytest.raises(SourceConflict, match="Another proposal"):
        service.propose(job, **args)
    assert len(docs) == 2


@pytest.mark.parametrize("damage", ["receipt", "target", "base", "actor", "isolation"])
def test_corrupt_private_or_durable_evidence_cannot_verify(proposal_service, damage):
    service, f, docs, args = proposal_service
    result = service.propose(f.job, **args)
    if damage == "receipt":
        record = service.dal.read(result["replacement_id"], account="test-account")
        docs[record["plan"]["ReceiptReference"]] += b" "
    elif damage == "target":
        f.sql.execute("UPDATE #ExportReplacementTarget SET NewFileID='changed-file'")
    elif damage == "base":
        f.sql.execute(
            "UPDATE #ExportReplacementPlan SET BaseRegistrationHash=CAST(? AS binary(32))",
            b"x" * 32,
        )
    elif damage == "actor":
        f.sql.execute("UPDATE #ExportReplacementPlan SET Actor='recovery:other'")
    else:
        f.sql.execute("DELETE FROM #ExportContainedTarget")
    f.sql.commit()
    with pytest.raises((SourceConflict, ValueError)):
        service.inspect(result["replacement_id"])


def test_stale_confirmation_creates_no_proposal_or_new_private_receipt(proposal_service):
    service, f, docs, args = proposal_service
    args["token"] = "0" * 64
    with pytest.raises(SourceConflict, match="exact reviewed"):
        service.propose(f.job, **args)
    assert len(docs) == 1
    assert f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementPlan").fetchval() == 0
