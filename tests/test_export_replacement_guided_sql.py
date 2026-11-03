"""Admin decisions through real recovery, replacement and queue transactions."""

import hashlib
import os
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from services.export_coordination_dal import ExportCoordinationDAL
from services.export_replacement_activation import ReplacementActivationService
from services.export_replacement_activation_dal import ReplacementActivationDAL
from services.export_replacement_delivery import ReplacementDelivery
from services.export_replacement_delivery_dal import ReplacementDeliveryDAL
from services.export_replacement_verification import verification_plan
from services.export_replacement_workflow import ReplacementWorkflow
from services.export_snapshot_store import SnapshotReceipt
from services.recovery_service import RecoveryService
from tests import test_export_target_containment_sql as fixture_module
from tests.test_export_replacement_delivery_sql import recovery as recovery
from tests.test_export_replacement_verification_sql import (
    contained_job as contained_job,
    proposal_service as proposal_service,
    verification as verification,
)
from tests.test_guided_recovery import ACTOR
from tests.test_recovery_sql import store as store

pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1"
    or os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1",
    reason="Explicit temporary SQL opt-in",
)


@pytest.fixture
def guided(monkeypatch, request, store):
    rewrite = fixture_module.local_sql
    monkeypatch.setattr(
        fixture_module,
        "local_sql",
        lambda text: rewrite(text).replace("=ExportJob.", "=#ExportJob."),
    )
    monkeypatch.setattr(
        fixture_module,
        "TABLES",
        (
            *fixture_module.TABLES,
            "dbo.ExportReplacementActivation",
            "dbo.ExportReplacementDelivery",
            "KVK.SourceOutputFile",
            "dbo.ExportAttemptPart",
        ),
    )
    monkeypatch.setattr(
        fixture_module,
        "PROCEDURES",
        (*fixture_module.PROCEDURES, "dbo.usp_ExportReplacementActivate"),
    )
    r = request.getfixturevalue("verification")
    activation = ReplacementActivationService(
        dal=ReplacementActivationDAL(r.f.connect),
        proposals=r.service.proposals,
        verification=r.service,
        authority=r.service.authority,
    )
    spools = {"retained-input": r.f.original_payload}

    def put(raw):
        key = uuid4().hex
        spools[key] = raw
        return SnapshotReceipt(key, len(raw), hashlib.sha256(raw).hexdigest(), "disk")

    def read(receipt):
        raw = spools[receipt.key]
        assert len(raw) == receipt.byte_count and hashlib.sha256(raw).hexdigest() == receipt.sha256
        return raw

    coordinator = ExportCoordinationDAL(
        r.f.connect, preparations=True, output_operations=True, execution_evidence=True
    )
    continuation = ReplacementDelivery(
        dal=ReplacementDeliveryDAL(r.f.connect, coordinator),
        discovery=r.service.proposals.containment.discovery,
        store=SimpleNamespace(put=put, read=read),
        verify_delivery=Mock(),
    )

    def plan(proposal, key):
        result = verification_plan(
            r.service.proposals.registration,
            proposal,
            verification_id=key,
            manifest_hash=(b"m" * 32).hex(),
            profile_hash=r.plan.value()["credential_profile_sha256"],
            project_id="example",
        )
        r.runtime.plan = result
        return result

    # Temporary tables belong to one connection. Background lifecycle is tested
    # separately; here all real SQL/provider-journal transitions run in sequence.
    monkeypatch.setattr(r.service, "start", r.service.run)
    workflow = ReplacementWorkflow(
        proposals=r.service.proposals,
        verification=r.service,
        activation=activation,
        plan_factory=plan,
        continuation=continuation,
    )
    service = RecoveryService(store, {"export_job": workflow}, admin_id=1, guild_id=2, channel_id=3)
    r.recovery, r.workflow, r.spools = service, workflow, spools
    r.row = service.review_source(ACTOR, "export_job", r.f.job)
    return r


def apply(r, action):
    row = r.recovery.review(ACTOR, r.row["IncidentID"])
    return r.recovery.execute(
        ACTOR,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        action,
        "Admin confirmed displayed checks",
    )


def test_saved_admin_form_to_verified_activation_and_single_retained_queue(guided):
    r = guided
    row = r.row
    page = r.recovery.input_page(ACTOR, row["IncidentID"], "choose_replacements")
    assert len(page["fields"]) == 2
    r.recovery.save_input(
        ACTOR,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "choose_replacements",
        0,
        0,
        {
            "owner_email": "owner@example.com",
            "old-file": "https://docs.google.com/spreadsheets/d/guided-fresh-file/edit",
        },
    )
    restarted = RecoveryService(
        r.recovery.store, r.recovery.adapters, admin_id=1, guild_id=2, channel_id=3
    )
    preview = restarted.input_confirmation(ACTOR, row["IncidentID"], "choose_replacements")
    row = restarted.execute_input(
        ACTOR,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "choose_replacements",
        preview["draft_version"],
    )
    assert row["evidence"]["outcome"] == "verification_required" and not row["pending_action"]
    row = apply(r, "verify_replacements")
    assert row["evidence"]["outcome"] == "activation_required" and row["State"] == "open"
    assert len(r.runtime.sent) == 5
    row = apply(r, "activate_replacements")
    assert row["evidence"]["outcome"] == "publication_required" and not row["pending_action"]
    row = apply(r, "publish_replacement")
    assert row["evidence"]["outcome"] == "replacement_queued" and row["State"] == "open"
    assert not row["pending_action"]
    assert len(r.spools) == 2 and len(r.runtime.sent) == 5
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementDelivery").fetchval() == 1
    from tests.test_export_replacement_end_to_end import prepare_publication

    r.activated = r.workflow._state(r.f.job)["activation"]
    r.delivery = r.workflow.continuation
    prepare_publication(r)
    r.publish()
    settled = restarted.review(ACTOR, row["IncidentID"])
    assert settled["State"] == "resolved"
    assert settled["evidence"]["outcome"] == "replacement_delivered"
    assert not settled["pending_action"]
    assert r.provider.rows == dict(values=[["ID", "Value"], [1, "retained"]])
    assert (
        r.f.sql.execute("SELECT State FROM #ExportJob WHERE JobID=?", r.f.job).fetchval()
        == "uncertain"
    )
    r.http.request.assert_not_called()


def test_failed_file_check_offers_discard_then_fresh_check(guided):
    r = guided
    r.runtime.failure = "drive.files.get"
    row = apply(r, "verify_replacements")
    assert row["evidence"]["outcome"] == "checking_replacements" and not row["pending_action"]
    assert "discard_replacement_check" in row["evidence"]["actions"]
    assert "finish_replacement_check" not in row["evidence"]["actions"]
    row = apply(r, "discard_replacement_check")
    assert "verify_replacements" in row["evidence"]["actions"] and not row["pending_action"]
    r.runtime.failure = None
    row = apply(r, "verify_replacements")
    assert row["evidence"]["outcome"] == "activation_required"
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementVerification").fetchval() == 2
