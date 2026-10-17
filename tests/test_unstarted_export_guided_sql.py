"""Actual admin callbacks, durable recovery actions and temporary export SQL."""

import json
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from services.export_recovery_service import ExportRecoveryAdapter
from services.recovery_dal import RecoveryDAL
from services.recovery_release_policy import p0a_presentation
from services.recovery_service import RecoveryActor, RecoveryService, SourceConflict
from tests.test_export_skip_sql import scoped_jobs as scoped_jobs, setup
from tests.test_guided_recovery import ACTOR
from tests.test_recovery_sql import store as store

pytestmark = pytest.mark.skipif(
    os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Explicit temporary SQL opt-in"
)


def service_for(store, adapter):
    scoped_store = RecoveryDAL(store.connect, account="account", storage_owner="disk", guild_id=2)
    return RecoveryService(
        scoped_store,
        {adapter.kind: adapter},
        admin_id=1,
        guild_id=2,
        channel_id=3,
        presentation_policy=p0a_presentation,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("consumer", ["scan_data", "all_kvk"])
@pytest.mark.parametrize("action", ["retry_unstarted", "skip_unstarted"])
async def test_guided_buttons_commit_once_then_verify_after_lost_reply(
    scoped_jobs, store, monkeypatch, consumer, action
):
    from ui.views import recovery_view as view

    adapter, job_id, sql, _ = setup(scoped_jobs, consumer=consumer)
    service = service_for(store, adapter)
    row = service.review_source(ACTOR, "export_job", job_id)
    before = adapter.discovery.job(job_id)["job"]
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))

    async def call(name, *args):
        return getattr(service, name)(*args)

    monkeypatch.setattr(view, "call", call)
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    button = next(
        item
        for item in view.RecoveryIncidentView(row).children
        if item.label == row["evidence"]["actions"][action]["label"]
    )
    await button.callback(interaction)
    preview = interaction.followup.send.call_args.kwargs
    assert preview["ephemeral"]
    assert [f.name for f in preview["embed"].fields] == [
        "Check before confirming",
        "What the bot will do",
        "Verification",
    ]
    assert not service.store.pending_actions(row["IncidentID"])
    assert adapter.discovery.job(job_id)["job"] == before

    original = getattr(
        adapter.coordinator,
        "request_safe_retry" if action == "retry_unstarted" else "skip_unstarted",
    )
    calls = []

    def lost_reply(*args, **kwargs):
        calls.append(kwargs)
        original(*args, **kwargs)
        raise TimeoutError("commit reply lost")

    monkeypatch.setattr(adapter.coordinator, original.__name__, lost_reply)
    await preview["view"].children[0].callback(interaction)
    assert interaction.followup.send.call_args.kwargs["ephemeral"]
    # Recreate service and adapter: read back actual durable action/domain receipts.
    restarted = service_for(
        store, ExportRecoveryAdapter(adapter.discovery, adapter.coordinator, None)
    )
    current = restarted.review(ACTOR, row["IncidentID"])
    assert current["State"] == "resolved" and current["pending_action"] is None
    assert not restarted.store.pending_actions(row["IncidentID"])
    await preview["view"].children[0].callback(interaction)  # duplicate Discord delivery
    assert len(calls) == 1
    after = adapter.discovery.job(job_id)["job"]
    for field in (
        "JobID",
        "InputHash",
        "SpoolKey",
        "SpoolBytes",
        "EnqueueSequence",
        "OwnerID",
        "Fence",
    ):
        assert after[field] == before[field]
    assert after["Version"] == before["Version"] + 1
    assert sql.execute("SELECT COUNT(*) FROM #ExportAttempt").fetchval() == 0
    assert sql.execute("SELECT COUNT(*) FROM #ExportExecutionStream").fetchval() == 0
    if action == "retry_unstarted":
        assert "does not yet confirm delivery" in current["evidence"]["explanation"]
        # Retry admission consumes its request with a new fence; no duplicate export job.
        claim = adapter.coordinator.claim_next("account", storage_owner="disk")
        assert claim.job_id == job_id and claim.fence > before["Fence"]
    else:
        assert current["evidence"]["outcome"] == "export_skipped"
    assert sql.execute("SELECT COUNT(*) FROM #ExportJob").fetchval() == 5


@pytest.mark.parametrize("action", ["retry_unstarted", "skip_unstarted"])
def test_restart_after_lost_intent_ack_uses_same_durable_action(
    scoped_jobs, store, monkeypatch, action
):
    adapter, job_id, _, _ = setup(scoped_jobs)
    service = service_for(store, adapter)
    row = service.review_source(ACTOR, "export_job", job_id)
    claim = service.store.claim

    def lost_intent(*args, **kwargs):
        claim(*args, **kwargs)
        raise TimeoutError("intent reply lost")

    monkeypatch.setattr(service.store, "claim", lost_intent)
    with pytest.raises(TimeoutError):
        service.execute(
            ACTOR, row["IncidentID"], row["Revision"], row["EvidenceHash"], action, "Reviewed"
        )
    pending = service.store.pending_actions(row["IncidentID"])
    assert len(pending) == 1
    restarted = service_for(store, adapter)
    restarted.review(ACTOR, row["IncidentID"])
    current = restarted.review(ACTOR, row["IncidentID"])
    assert current["State"] == "resolved" and current["pending_action"] is None
    provenance = json.loads(adapter.discovery.job(job_id)["job"]["ProvenanceJson"])
    receipt = (
        provenance["safe_retry_history"][0]
        if action == "retry_unstarted"
        else provenance["export_skipped"]
    )
    assert receipt["actor"] == "recovery:" + pending[0]["ActionID"]


@pytest.mark.parametrize("action", ["retry_unstarted", "skip_unstarted"])
@pytest.mark.parametrize("bad", ["actor", "guild", "channel", "version"])
def test_confirmation_refuses_changed_authority_or_evidence(scoped_jobs, store, action, bad):
    adapter, job_id, sql, _ = setup(scoped_jobs)
    service = service_for(store, adapter)
    row = service.review_source(ACTOR, "export_job", job_id)
    actor = {
        "actor": RecoveryActor(9, 2, 3),
        "guild": RecoveryActor(1, 9, 3),
        "channel": RecoveryActor(1, 2, 9),
    }.get(bad, ACTOR)
    if bad == "version":
        sql.execute("UPDATE #ExportJob SET Version=Version+1 WHERE JobID=?", job_id)
        sql.commit()
    with pytest.raises(SourceConflict):
        service.execute(
            actor, row["IncidentID"], row["Revision"], row["EvidenceHash"], action, "Reviewed"
        )
    assert not service.store.pending_actions(row["IncidentID"])
    assert adapter.discovery.job(job_id)["job"]["ProvenanceJson"] == "{}"


def test_retry_dal_refuses_stream_even_when_caller_supplies_current_version(scoped_jobs):
    adapter, job_id, sql, _ = setup(scoped_jobs)
    job = adapter.discovery.job(job_id)["job"]
    sql.execute(
        "INSERT #ExportExecutionStream(StreamID,SessionID,AccountKey,ActiveAccountKey,JobID,OwnerID,Fence,ClaimVersion,RegistrationHash,SnapshotHash,ScopeJson,Purpose,State,Version,LastSequence,ChildIdentity,CreatedUTC) "
        "VALUES (?,?,'account','account',?,?,1,1,CONVERT(binary(32),0),CONVERT(binary(32),0),'{}','probe','open',1,0,?,SYSUTCDATETIME())",
        str(uuid4()),
        str(uuid4()),
        job_id,
        job["OwnerID"],
        str(uuid4()),
    )
    sql.commit()
    with pytest.raises(SourceConflict, match="Execution evidence"):
        adapter.coordinator.request_safe_retry(
            job_id,
            "account",
            expected_version=job["Version"],
            expected_epoch=None,
            actor="admin",
            reason="Reviewed",
        )
    assert adapter.discovery.job(job_id)["job"]["ProvenanceJson"] == "{}"


@pytest.mark.parametrize("season_state", ["open", "closing", "closed"])
def test_registered_source_retry_preserves_scope_and_rechecks_season(scoped_jobs, season_state):
    adapter, _, sql, ids = setup(scoped_jobs)
    job_id = ids["registered"]
    job = adapter.discovery.job(job_id)["job"]
    sql.execute("UPDATE #SeasonSource SET SeasonState=?", season_state)
    sql.commit()
    arguments = dict(
        expected_version=job["Version"],
        expected_epoch=job["PoolEpoch"],
        actor="admin",
        reason="Reviewed",
    )
    if season_state == "open":
        adapter.coordinator.request_safe_retry(job_id, "account", **arguments)
        after = adapter.discovery.job(job_id)["job"]
        assert json.loads(after["ProvenanceJson"])["safe_retry"]["requested"]
        assert after["PoolEpoch"] == job["PoolEpoch"]
        assert after["InputHash"] == job["InputHash"]
    else:
        with pytest.raises(SourceConflict, match="lifecycle"):
            adapter.coordinator.request_safe_retry(job_id, "account", **arguments)
        assert adapter.discovery.job(job_id)["job"]["ProvenanceJson"] == "{}"
