"""Production-policy publication decisions with temporary SQL and private journals.

The provider child, host boundary and Discord transport are simulated. The
publication, proof producer/consumer, recovery action and ownership SQL are real.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest

from services.recovery_release_policy import p0a_presentation
from services.recovery_service import RecoveryService
from tests import test_export_target_containment_sql as fixture
from tests.test_export_replacement_source_sql import (
    activation as activation,
    contained_job as contained_job,
    proposal_service as proposal_service,
    pytestmark as pytestmark,
    recovery as recovery,
    source_delivery as source_delivery,
    verification as verification,
)
from tests.test_guided_recovery import ACTOR
from tests.test_recovery_sql import store as store


@pytest.fixture
def publication(request, monkeypatch, store):
    from core.export_execution_host import DeploymentBoundary
    from scripts.run_export_authority import AuthorityBroker
    from services.export_reconciliation_service import TrustedProofIssuer
    from services.export_recovery_dal import ExportRecoveryDAL
    from services.export_recovery_service import ExportRecoveryAdapter
    from services.export_runtime_composition import AuthorityReconciler, LocalAuthorityClient

    monkeypatch.setattr(fixture, "TABLES", (*fixture.TABLES, "dbo.ExportReconciliationProof"))
    monkeypatch.setattr(
        fixture, "PROCEDURES", (*fixture.PROCEDURES, "dbo.usp_ExportReconciliationProofIssue")
    )
    r = request.getfixturevalue("source_delivery")
    scenario = getattr(request, "param", None)
    evidence_store = r.service.authority.store
    evidence_store.read = lambda receipt: evidence_store.read_reference(
        str(UUID(receipt.key)), bytes.fromhex(receipt.sha256)
    )
    if scenario == "unknown_write":
        from services.export_execution_authority import ExecutionUncertain

        r.provider.failure = "sheets.values.update"
        with pytest.raises(ExecutionUncertain):
            r.publish()
    elif scenario == "absent":
        begin = r.coordinator.begin_attempt

        def stop_before_write(*args, **kwargs):
            begin(*args, **kwargs)
            raise RuntimeError("Stopped after attempt creation, before mutation")

        with monkeypatch.context() as stopped:
            stopped.setattr(r.coordinator, "begin_attempt", stop_before_write)
            with pytest.raises(RuntimeError, match="before mutation"):
                r.publish()
        assert not any(item.mutation for item in r.provider.sent)
    elif scenario == "damaged":
        r.publish()
        # Simulate a later external edit to a generation, retaining its index.
        generation_file = r.f.sql.execute(
            "SELECT TOP 1 p.FileID FROM #ExportAttemptPart p JOIN #ExportAttempt a "
            "ON a.AttemptID=p.AttemptID WHERE a.JobID=? AND p.Role='generation'",
            r.claim.job_id,
        ).fetchval()
        rows = next(
            rows
            for (file_id, tab), rows in r.api.values.items()
            if file_id == generation_file and not tab.endswith("DIRECTORY") and len(rows) > 1
        )
        rows[1][0] = "Externally changed retained generation"
    else:
        confirm = r.coordinator.confirm
        with monkeypatch.context() as lost:
            lost.setattr(
                r.coordinator, "confirm", Mock(side_effect=TimeoutError("Final SQL not entered"))
            )
            with pytest.raises(TimeoutError, match="Final SQL not entered"):
                r.publish()
        assert r.coordinator.confirm == confirm
    if scenario != "damaged":
        r.coordinator.fail(r.claim, retain_claims=True)
    registration = r.runtime.registration
    boundary = DeploymentBoundary.__new__(DeploymentBoundary)
    boundary._raw = b"disposable host boundary; no native-host verification"
    boundary.recheck = Mock(return_value=boundary.fingerprint)
    boundary._manifest = dict(
        deployment_boundary=dict(
            host=dict(
                hostname=r.f.sql.execute(
                    "SELECT HostIdentity FROM #ExportExecutionSession WHERE SessionID=?",
                    r.service.authority.session_id,
                )
                .fetchval()
                .lower()
            )
        )
    )
    broker = AuthorityBroker(r.service.authority, registration, boundary=boundary)
    client = LocalAuthorityClient(broker)
    broker.issuer = TrustedProofIssuer(
        authority=r.service.authority,
        boundary=boundary,
        registration=registration,
        coordinator=r.coordinator,
        pools=r.runtime.pools,
        client=client,
    )
    discovery = ExportRecoveryDAL(r.f.connect, registration=registration)
    reconciler = AuthorityReconciler(client)
    from kvk.services.new_source_admin_service import SourceAccess
    from kvk.services.source_export_operator_service import SourceExportOperatorService

    operator = SourceExportOperatorService(
        access_factory=lambda: SourceAccess(True, 2, 3, 1, frozenset(), frozenset({3})),
        pools=r.runtime.pools,
        coordinator=r.coordinator,
        rollover=None,
        generation_loader=r.runtime.load_generation,
        reconciler=reconciler,
    )
    adapter = ExportRecoveryAdapter(
        discovery,
        r.coordinator,
        reconciler,
        rebuild_plan=lambda job_id, reason: operator.prepare_rebuild(ACTOR, job_id, reason=reason),
    )
    errors = []
    execute = adapter.execute

    def capture_error(*args, **kwargs):
        try:
            return execute(*args, **kwargs)
        except Exception as exc:
            import traceback

            errors.append("".join(traceback.format_exception(exc)))
            raise

    monkeypatch.setattr(adapter, "execute", capture_error)
    service = RecoveryService(
        store,
        {"export_job": adapter},
        admin_id=1,
        guild_id=2,
        channel_id=3,
        presentation_policy=p0a_presentation,
    )
    row = service.review_source(ACTOR, "export_job", r.claim.job_id)
    return SimpleNamespace(r=r, service=service, row=row, errors=errors)


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["confirmed", "stale", "lost_commit_reply"])
async def test_publication_confirmation_reads_existing_output_and_settles_exact_owner(
    publication, monkeypatch, case
):
    from ui.views import recovery_view as view

    p = publication
    assert "verify_publication" in p.row["evidence"]["actions"]
    before = tuple(p.r.provider.sent)
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))

    async def call(method, *args):
        return getattr(p.service, method)(*args)

    monkeypatch.setattr(view, "call", call)
    interaction = SimpleNamespace(
        followup=SimpleNamespace(send=AsyncMock()), response=SimpleNamespace(is_done=lambda: True)
    )
    item = view.RecoveryIncidentView(p.row)
    button = next(b for b in item.children if b.label == "Verify & settle publication")
    await button.callback(interaction)
    assert tuple(p.r.provider.sent) == before
    confirmation = interaction.followup.send.call_args.kwargs["view"]
    if case == "stale":
        p.r.f.sql.execute("UPDATE #ExportJob SET Version=Version+1 WHERE JobID=?", p.r.claim.job_id)
        p.r.f.sql.commit()
    elif case == "lost_commit_reply":
        from kvk.dal.new_source_import_dal import UncertainCommit

        settle = p.r.coordinator.reconcile_operator

        def lost(*args, **kwargs):
            settle(*args, **kwargs)
            raise UncertainCommit("Exact settlement committed; reply lost")

        monkeypatch.setattr(p.r.coordinator, "reconcile_operator", lost)
    await confirmation.children[0].callback(interaction)
    assert interaction.followup.send.call_args.kwargs["ephemeral"] is True
    # Reconstruct service as after restart, retaining only its durable SQL state.
    p.service = RecoveryService(
        p.service.store,
        p.service.adapters,
        admin_id=1,
        guild_id=2,
        channel_id=3,
        presentation_policy=p0a_presentation,
    )
    result = p.service.review(ACTOR, p.row["IncidentID"])
    if case == "stale":
        assert result["State"] == "open" and not result["pending_action"]
        assert tuple(p.r.provider.sent) == before
        assert p.r.f.sql.execute("SELECT COUNT(*) FROM #ExportReconciliationProof").fetchval() == 0
        return
    if p.errors:
        print("\n".join(p.errors))
    assert result["State"] == "resolved", p.errors
    assert result["evidence"]["outcome"] == "confirmed"
    assert not result["pending_action"]
    assert all(not request.mutation for request in p.r.provider.sent[len(before) :])
    assert (
        p.r.f.sql.execute(
            "SELECT COUNT(*) FROM #ExportResource WHERE ActiveJobID=?", p.r.claim.job_id
        ).fetchval()
        == 0
    )
    assert (
        p.r.f.sql.execute("SELECT State FROM #ExportJob WHERE JobID=?", p.r.f.job).fetchval()
        == "uncertain"
    )
    after = tuple(p.r.provider.sent)
    await confirmation.children[0].callback(interaction)
    assert tuple(p.r.provider.sent) == after
    assert p.r.f.sql.execute("SELECT COUNT(*) FROM #ExportReconciliationProof").fetchval() == 1


@pytest.mark.parametrize("publication", ["damaged"], indirect=True)
def test_last_publication_remains_discoverable_until_newer_publication_confirms(
    publication, monkeypatch
):
    from kvk.dal.new_source_import_dal import SourceConflict

    p = publication
    original, newer = p.r.claim.job_id, str(uuid4())
    adapter = p.service.adapters["export_job"]
    _, original_token, _ = adapter.inspect(original)
    sql = p.r.f.sql
    sql.execute(
        "INSERT INTO #ExportJob "
        "(JobID,ConsumerKind,SourceKey,IntentID,AccountKey,DestinationSetHash,InputHash,"
        "KVK_NO,PoolEpoch,RepairID,EnqueueSequence,State,OwnerID,Fence,Version,"
        "CreatedUTC,UpdatedUTC,Actor,Reason,ProvenanceJson) "
        "SELECT ?,ConsumerKind,SourceKey,IntentID,AccountKey,DestinationSetHash,InputHash,"
        "KVK_NO,PoolEpoch,NEWID(),EnqueueSequence+1,'waiting',NULL,0,1,"
        "DATEADD(second,1,CreatedUTC),DATEADD(second,1,UpdatedUTC),Actor,Reason,ProvenanceJson "
        "FROM #ExportJob WHERE JobID=?",
        newer,
        original,
    )
    sql.commit()
    before = tuple(p.r.provider.sent)
    for state in ("waiting", "ready", "running", "failed", "uncertain", "cancelled", "coalesced"):
        owned = state in {"running", "failed", "uncertain"}
        sql.execute(
            "UPDATE #ExportJob SET State=?,OwnerID=?,Fence=?,SupersededByJobID=? WHERE JobID=?",
            state,
            str(uuid4()) if owned else None,
            1 if owned else 0,
            original if state == "coalesced" else None,
            newer,
        )
        sql.commit()
        listed = p.service.published_outputs(ACTOR)
        assert original in [item["JobID"] for item in listed], state
        assert newer not in [item["JobID"] for item in listed], state
    sql.execute(
        "UPDATE #ExportJob SET State='confirmed',OwnerID=NEWID(),Fence=1,"
        "SupersededByJobID=NULL WHERE JobID=?",
        newer,
    )
    sql.commit()
    listed = p.service.published_outputs(ACTOR)
    assert original not in [item["JobID"] for item in listed]
    assert newer in [item["JobID"] for item in listed]
    with pytest.raises(SourceConflict, match="evidence changed"):
        adapter.execute(original, "verify_publication", original_token, "admin", "Check output")
    evidence, _, _ = adapter.inspect(original)
    assert "verify_publication" not in evidence["actions"]
    assert any(link["source_id"] == newer for link in evidence["recovery_links"])
    with pytest.raises(SourceConflict, match="newer publication"):
        adapter.discovery.registered_publication(original, p.r.coordinator)
    # The final transaction repeats the guard even if a newer publication
    # commits after the admin token and provider proof were checked.
    snapshot = p.r.coordinator.operator_snapshot(original)
    with pytest.raises(SourceConflict, match="newer publication"):
        p.r.coordinator.reconcile_operator(snapshot, {}, actor="admin")
    with pytest.raises(SourceConflict, match="newer publication"):
        p.r.coordinator.admit_repair(
            str(uuid4()), {"snapshot": snapshot, "proof": {}, "reason": "Restore output"}
        )
    assert sql.execute("SELECT COUNT(*) FROM #ExportReconciliationProof").fetchval() == 0
    assert tuple(p.r.provider.sent) == before


@pytest.mark.parametrize("publication", ["unknown_write"], indirect=True)
def test_publication_verification_cannot_settle_an_unknown_dispatched_write(publication):
    p = publication
    before = tuple(p.r.provider.sent)
    row = p.row
    p.service.execute(
        ACTOR,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "verify_publication",
        "Check retained publication",
    )
    result = p.service.store.get(row["IncidentID"])
    assert result["State"] == "open"
    assert not p.service.store.pending_actions(row["IncidentID"])
    assert tuple(p.r.provider.sent) == before
    assert p.r.f.sql.execute("SELECT COUNT(*) FROM #ExportReconciliationProof").fetchval() == 0
    assert (
        p.r.f.sql.execute(
            "SELECT COUNT(*) FROM #ExportResource WHERE ActiveJobID=?", p.r.claim.job_id
        ).fetchval()
        > 0
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("publication", ["absent", "damaged"], indirect=True)
@pytest.mark.parametrize("case", ["normal", "lost_admission_reply", "failed_successor", "denied"])
async def test_verified_publication_repair_queues_separate_job_and_verifies_delivery(
    publication, monkeypatch, case
):
    from ui.views import recovery_view as view

    p = publication
    original = p.r.claim.job_id
    if "verify_publication" in p.row["evidence"]["actions"]:
        row = p.row
        if row["State"] == "resolved":
            # Current confirmed publications are discoverable without a job ID
            # or a manual reconciliation command. SQL discovery makes no I/O.
            before_check = tuple(p.r.provider.sent)
            listed = p.service.published_outputs(ACTOR)
            assert row["SourceID"] in [item["JobID"] for item in listed]
            assert tuple(p.r.provider.sent) == before_check
        monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
        monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))

        async def check_call(method, *args):
            return getattr(p.service, method)(*args)

        monkeypatch.setattr(view, "call", check_call)
        interaction = SimpleNamespace(
            followup=SimpleNamespace(send=AsyncMock()),
            response=SimpleNamespace(is_done=lambda: True),
        )
        check = next(
            b
            for b in view.RecoveryIncidentView(row).children
            if b.label == row["evidence"]["actions"]["verify_publication"]["label"]
        )
        await check.callback(interaction)
        confirm_check = interaction.followup.send.call_args.kwargs["view"]
        await confirm_check.children[0].callback(interaction)
    row = p.service.review(ACTOR, p.row["IncidentID"])
    assert row["State"] == "open"
    actions = row["evidence"]["actions"]
    action = "retry_absent" if "retry_absent" in actions else "rebuild_damaged"
    assert action in actions
    before = tuple(p.r.provider.sent)
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))

    async def call(method, *args):
        return getattr(p.service, method)(*args)

    monkeypatch.setattr(view, "call", call)
    interaction = SimpleNamespace(
        followup=SimpleNamespace(send=AsyncMock()), response=SimpleNamespace(is_done=lambda: True)
    )
    item = view.RecoveryIncidentView(row)
    button = next(b for b in item.children if b.label == actions[action]["label"])
    await button.callback(interaction)
    confirmation = interaction.followup.send.call_args.kwargs["view"]
    assert tuple(p.r.provider.sent) == before
    if case == "denied":
        from services.recovery_service import RecoveryActor

        monkeypatch.setattr(view, "actor_for", lambda _: RecoveryActor(999, 2, 3))
    elif case == "lost_admission_reply":
        from kvk.dal.new_source_import_dal import UncertainCommit

        admit = p.r.coordinator.admit_repair

        def lost(*args, **kwargs):
            admit(*args, **kwargs)
            raise UncertainCommit("Repair admitted; reply lost")

        monkeypatch.setattr(p.r.coordinator, "admit_repair", lost)
    await confirmation.children[0].callback(interaction)
    if case == "denied":
        assert (
            p.r.f.sql.execute(
                "SELECT COUNT(*) FROM #ExportJob WHERE RepairID IS NOT NULL"
            ).fetchval()
            == 0
        )
        assert tuple(p.r.provider.sent) == before
        return
    assert (
        p.r.f.sql.execute("SELECT COUNT(*) FROM #ExportJob WHERE RepairID IS NOT NULL").fetchval()
        == 1
    ), p.errors
    assert all(not request.mutation for request in p.r.provider.sent[len(before) :])
    waiting = p.service.review(ACTOR, p.row["IncidentID"])
    assert waiting["State"] == "open"
    assert waiting["evidence"]["recovery_links"][0]["label"] == "Review repair export"
    after = tuple(p.r.provider.sent)
    p.service = RecoveryService(
        p.service.store,
        p.service.adapters,
        admin_id=1,
        guild_id=2,
        channel_id=3,
        presentation_policy=p0a_presentation,
    )
    await confirmation.children[0].callback(interaction)
    assert tuple(p.r.provider.sent) == after
    # The normal worker refreshes capacity after quarantine changes the pool.
    from kvk.services.source_output_pool_service import SourceOutputPlanner
    from services.export_coordination_service import ExportRegistration

    planner = SourceOutputPlanner(p.r.runtime.pools, p.r.runtime.load_generation)
    for job in p.r.coordinator.pending_source_jobs("test-account"):
        registration = ExportRegistration(
            job["KVK_NO"], job["AccountKey"], job["PoolEpoch"], job["destinations"]
        )
        proof = planner(job["IntentID"], bytes(job["InputHash"]), registration)
        p.r.coordinator.refresh_output_preflight(job["JobID"], job["Version"], proof)
    p.r.prepare_publication(p.r.activated)
    assert p.r.claim.job_id != original
    if case == "failed_successor":
        from services.export_execution_authority import ExecutionUncertain

        p.r.provider.failure = "sheets.values.update"
        with pytest.raises(ExecutionUncertain):
            p.r.publish()
        p.r.coordinator.fail(p.r.claim, retain_claims=True)
        waiting = p.service.review(ACTOR, p.row["IncidentID"])
        assert waiting["State"] == "open"
        link = next(
            b
            for b in view.RecoveryIncidentView(waiting).children
            if b.label == "Review repair export"
        )
        await link.callback(interaction)
        child = interaction.followup.send.call_args.kwargs["view"]
        assert child.row["State"] == "open"
        back = next(b for b in child.children if b.label == "Return to original export")
        await back.callback(interaction)
        assert (
            interaction.followup.send.call_args.kwargs["view"].row["IncidentID"]
            == p.row["IncidentID"]
        )
        return
    p.r.publish()
    final = p.service.review_source(ACTOR, "export_job", p.r.claim.job_id)
    assert final["State"] == "resolved" and final["evidence"]["outcome"] == "confirmed"
    assert p.service.review(ACTOR, p.row["IncidentID"])["State"] == "resolved"
    p.r.weights.assert_not_called()
    assert (
        p.r.f.sql.execute("SELECT COUNT(*) FROM #ExportJob WHERE RepairID IS NOT NULL").fetchval()
        == 1
    )
    assert (
        p.r.f.sql.execute("SELECT State FROM #ExportJob WHERE JobID=?", p.r.f.job).fetchval()
        == "uncertain"
    )
