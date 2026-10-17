"""Actual transaction tests using session-local tables only."""

import os
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from services.export_execution_authority import ExecutionUncertain, ExportExecutionAuthority
from services.export_execution_dal import ExportExecutionDAL
from services.export_execution_protocol import ProviderRequest
from services.export_replacement_verification import ReplacementVerificationPlan
from services.export_replacement_verification_dal import ReplacementVerificationDAL
from services.export_replacement_verification_service import ReplacementVerificationService
from tests import test_export_target_containment_sql as fixture_module
from tests.test_export_enrollment_service import FakeChild
from tests.test_export_manual_enrollment import responses
from tests.test_export_replacement_service import (
    contained_job as contained_job,
    proposal_service as proposal_service,
    recovery as recovery,
)
from tests.test_export_replacement_verification import value

pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Explicit temporary SQL opt-in"
)


@pytest.fixture
def verification(monkeypatch, request):
    monkeypatch.setattr(
        fixture_module, "TABLES", (*fixture_module.TABLES, "dbo.ExportReplacementVerification")
    )
    monkeypatch.setattr(
        fixture_module,
        "PROCEDURES",
        (*fixture_module.PROCEDURES, "dbo.usp_ExportReplacementVerificationTransition"),
    )
    proposals, f, docs, args = request.getfixturevalue("proposal_service")
    proposal = proposals.propose(f.job, **args)
    v = value() | dict(
        account="test-account",
        storage_owner="disk",
        manifest_sha256=(b"m" * 32).hex(),
        replacement_id=proposal["replacement_id"],
    )
    v.update(editor_email="editor@example.iam.gserviceaccount.com", project_id="example")
    v["files"] = [
        dict(file_id=target, audience="private", editors=[v["editor_email"]])
        for target in sorted(proposal["mapping"].values())
    ]
    v["file_count"] = len(v["files"])
    v["owner_email"] = proposal["owner_email"]
    plan = ReplacementVerificationPlan(v)
    runtime = SimpleNamespace(failure=None, sent=[], plan=plan)

    class Child(FakeChild):
        def execute(self, message):
            typed = ProviderRequest.parse(message, enrollment=True)
            runtime.sent.append(typed)
            if runtime.failure == typed.operation:
                raise TimeoutError("Injected lost read reply")
            grid = dict(file_id=typed.target, sheet_id=42, title="Sheet1", rows=1000, columns=26)
            data = responses(runtime.plan, grid)
            return data[
                {
                    "drive.files.get": 0,
                    "drive.permissions.list": 1,
                    "sheets.get": 2,
                    "sheets.values.batchGet": 3,
                }[typed.operation]
            ]

    authority = ExportExecutionAuthority(
        session_id=f.session,
        store=proposals.store,
        dal=ExportExecutionDAL(f.connect),
        host=SimpleNamespace(create_suspended=lambda identifier: Child(identifier, runtime)),
        budget_factory=lambda account: Mock(),
    )
    dal = ReplacementVerificationDAL(f.connect)
    service = ReplacementVerificationService(dal=dal, authority=authority, proposals=proposals)

    def begin(p=plan):
        dal.transition(
            verification_id=p.value()["plan_id"],
            replacement_id=proposal["replacement_id"],
            session_id=f.session,
            account="test-account",
            action="begin",
            plan=p,
            actor="recovery:" + p.value()["plan_id"],
            reason="Verify replacement",
        )

    return SimpleNamespace(
        service=service, dal=dal, f=f, docs=docs, plan=plan, begin=begin, runtime=runtime
    )


def test_abandoned_before_stream_has_guided_verified_discard(verification):
    r = verification
    r.begin()
    key = r.plan.value()["plan_id"]
    checking = r.service.inspect(key)
    assert checking["state"] == "checking"
    result = r.service.discard(
        key, token=checking["token"], actor="recovery:" + str(uuid4()), reason="Discard unused read"
    )
    assert result["state"] == "discarded" and result["files"] == []
    assert (
        r.f.sql.execute(
            "SELECT COUNT(*) FROM #ExportResource WHERE ActivePreparationID IS NOT NULL"
        ).fetchval()
        == 0
    )
    assert (
        r.f.sql.execute("SELECT State FROM #ExportJob WHERE JobID=?", r.f.job).fetchval()
        == "uncertain"
    )
    restarted = ReplacementVerificationService(
        dal=r.dal, authority=r.service.authority, proposals=r.service.proposals
    )
    assert restarted.inspect(key) == result
    assert (
        restarted.discard(
            key, token=checking["token"], actor=result["actor"], reason=result["reason"]
        )
        == result
    )
    v = r.plan.value() | dict(plan_id=str(uuid4()))
    r.begin(ReplacementVerificationPlan(v))
    assert r.service.inspect(v["plan_id"])["state"] == "checking"


@pytest.mark.parametrize(
    "damage", ["wrong_file", "wrong_count", "missing_id", "healthy_job", "duplicate"]
)
def test_verification_cannot_bypass_membership_or_healthy_work(verification, damage):
    import pyodbc

    r = verification
    if damage == "duplicate":
        r.begin()
    elif damage == "healthy_job":
        r.f.sql.execute("DELETE FROM #ExportContainedTarget")
    v = r.plan.value()
    if damage == "wrong_file":
        v["files"][0]["file_id"] = "other-file"
    elif damage == "wrong_count":
        v["file_count"] = 2
    elif damage == "missing_id":
        del v["replacement_id"]
    import json

    forged = SimpleNamespace(value=lambda: v, sql_json=json.dumps(v))
    with pytest.raises(pyodbc.Error):
        r.begin(forged)


def test_complete_provider_journal_replays_after_restart_without_provider_dispatch(verification):
    r = verification
    key = r.plan.value()["plan_id"]
    result = r.service.run(r.plan, actor="recovery:" + key, reason="Verify replacements")
    assert result["state"] == "verified" and result["files"][0]["sheet_id"] == 42
    assert len(r.runtime.sent) == 5 and not any(req.mutation for req in r.runtime.sent)
    restarted = ReplacementVerificationService(
        dal=r.dal, authority=r.service.authority, proposals=r.service.proposals
    )
    assert restarted.inspect(key) == result
    assert restarted.run(r.plan, actor="recovery:" + key, reason="Verify replacements") == result
    assert len(r.runtime.sent) == 5


@pytest.mark.parametrize("settled", ["verified", "discarded"])
def test_new_proposal_can_recheck_same_unused_files_after_settled_read(verification, settled):
    from services.export_replacement_verification import verification_plan

    r = verification
    if settled == "verified":
        r.service.run(r.plan, actor="recovery:" + r.plan.value()["plan_id"], reason="First check")
    else:
        r.begin()
        first = r.service.inspect(r.plan.value()["plan_id"])
        r.service.discard(
            first["verification_id"],
            token=first["token"],
            actor="recovery:" + str(uuid4()),
            reason="Discard earlier check",
        )
    original = r.service.proposals.inspect(r.plan.value()["replacement_id"])
    proposal = r.service.proposals.propose(
        r.f.job,
        token=original["containment_token"],
        replacements=original["mapping"],
        owner_email=original["owner_email"],
        actor="recovery:" + str(uuid4()),
        reason="Refresh choices after registration review",
    )
    plan = verification_plan(
        r.service.proposals.registration,
        proposal,
        verification_id=str(uuid4()),
        manifest_hash=r.plan.value()["manifest_sha256"],
        profile_hash=r.plan.value()["credential_profile_sha256"],
        project_id=r.plan.value()["project_id"],
    )
    r.runtime.plan = plan
    result = r.service.run(plan, actor="recovery:" + plan.value()["plan_id"], reason="Fresh check")
    assert result["state"] == "verified"
    assert result["replacement_id"] == proposal["replacement_id"]
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementPlan").fetchval() == 2


def test_refresh_proposal_cannot_reuse_an_active_read(verification):
    import pyodbc

    r = verification
    r.begin()
    original = r.service.proposals.inspect(r.plan.value()["replacement_id"])
    with pytest.raises(pyodbc.Error, match="existing"):
        r.service.proposals.propose(
            r.f.job,
            token=original["containment_token"],
            replacements=original["mapping"],
            owner_email=original["owner_email"],
            actor="recovery:" + str(uuid4()),
            reason="Attempt to reuse an active check",
        )


def test_unknown_read_is_discarded_then_new_attempt_verifies(verification):
    r = verification
    r.runtime.failure = "drive.files.get"
    key = r.plan.value()["plan_id"]
    with pytest.raises(ExecutionUncertain):
        r.service.run(r.plan, actor="recovery:" + key, reason="Verify replacements")
    checking = r.service.inspect(key)
    sent = len(r.runtime.sent)
    assert (
        r.service.run(r.plan, actor="recovery:" + key, reason="Verify replacements")["state"]
        == "checking"
    )
    assert len(r.runtime.sent) == sent
    result = r.service.discard(
        key, token=checking["token"], actor="recovery:" + str(uuid4()), reason="Discard failed read"
    )
    assert result["state"] == "discarded"
    from services.export_reconciliation_service import ClosedStreamVerifier

    stream = r.service._snapshot(key)[0]["streams"][0]
    proof = ClosedStreamVerifier(
        dal=r.service.authority.dal, store=r.service.authority.store
    ).verify(
        stream["StreamID"],
        account="test-account",
        registration_hash=r.plan.digest,
        require_observation=False,
        allow_failed_reads=True,
    )
    assert proof.dispatched_mutations == proof.successful_reads == 0
    assert r.service.authority.drain()
    assert (
        r.f.sql.execute(
            "SELECT State FROM #ExportExecutionStream WHERE StreamID=?", stream["StreamID"]
        ).fetchval()
        == "read_contained"
    )
    # A separate authority lifecycle admits the new check.
    r.service.authority._closed = False
    r.runtime.failure = None
    new_plan = ReplacementVerificationPlan(r.plan.value() | dict(plan_id=str(uuid4())))
    assert (
        r.service.run(
            new_plan, actor="recovery:" + new_plan.value()["plan_id"], reason="Fresh check"
        )["state"]
        == "verified"
    )
