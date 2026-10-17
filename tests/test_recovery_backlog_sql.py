import os
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.recovery_backlog_dal import RecoveryBacklogDAL
from services.recovery_backlog_service import EvidenceBatchAdapter
from services.recovery_dal import RecoveryDAL
from tests.test_export_evidence_recovery import damage, recovery as recovery
from tests.test_recovery_sql import store as store

pytestmark = pytest.mark.skipif(
    os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Explicit local disposable SQL opt-in"
)


def evidence(store, token="a" * 64):
    return store.observe(
        "private_evidence",
        str(uuid4()),
        dict(
            title="Private recovery evidence",
            outcome="recoverable",
            explanation="Exact copy",
            copies=dict(primary="verified", replica="missing"),
            actions=dict(
                protect_evidence=dict(
                    label="Protect verified evidence",
                    check="Verify original",
                    effect="Restore exact bytes",
                )
            ),
        ),
        token,
    )


def test_group_approval_persists_every_member_and_survives_restart(store):
    first, second = evidence(store), evidence(store)
    dal = RecoveryBacklogDAL(store)
    preview = dal.preview()
    assert preview["count"] == 2
    group = dal.approve(preview, "discord:1")
    assert dal.preview()["count"] == 0
    restarted = RecoveryBacklogDAL(
        RecoveryDAL(store.connect, account="test-account", storage_owner="test-disk", guild_id=2)
    )
    assert set(restarted.pending_repairs()) == {first["IncidentID"], second["IncidentID"]}
    adapter = EvidenceBatchAdapter(store)
    assert adapter.inspect(group)[0]["pending_count"] == 2
    for row, outcome in ((first, "verified"), (second, "not_applied")):
        action = store.pending_actions(row["IncidentID"])[0]
        assert action["Actor"] == "discord:1"
        assert action["EvidenceHash"] == row["EvidenceHash"]
        store.finish(row["IncidentID"], action["ActionID"], outcome, {"verification": outcome})
    final, _, completed = adapter.inspect(group)
    assert completed and final["outcome"] == "completed_with_exceptions"
    assert final["verified_count"] == 1 and final["changed_count"] == 1


def test_stale_group_and_duplicate_confirmation_dispatch_nothing(store):
    row = evidence(store)
    dal = RecoveryBacklogDAL(store)
    preview = dal.preview()
    store.check_failed(row["IncidentID"], "TimeoutError")
    with pytest.raises(SourceConflict, match="group changed"):
        dal.approve(preview, "discord:1")
    assert not store.pending_actions(row["IncidentID"])
    assert not dal.pending_groups()
    row = store.observe("private_evidence", row["SourceID"], row["evidence"], "b" * 64)
    preview = dal.preview()
    dal.approve(preview, "discord:1")
    with pytest.raises(SourceConflict, match="group changed"):
        dal.approve(preview, "discord:1")
    assert len(store.pending_actions(row["IncidentID"])) == 1


def test_other_scope_and_unknown_writes_are_never_grouped(store):
    evidence(store)
    store.observe("stats_import", str(uuid4()), dict(outcome="unproven", actions={}), "a" * 64)
    foreign = RecoveryDAL(store.connect, account="foreign", storage_owner="test-disk", guild_id=2)
    evidence(foreign)
    assert RecoveryBacklogDAL(store).preview()["count"] == 1
    group = RecoveryBacklogDAL(store).approve(RecoveryBacklogDAL(store).preview(), "discord:1")
    with pytest.raises(SourceConflict):
        RecoveryBacklogDAL(foreign).group_progress(group)


def test_quiet_overview_replaces_per_incident_notifications(store):
    for _ in range(30):
        evidence(store)
    assert store.alerts_due() == []
    overview = store.observe(
        "recovery_overview", str(uuid4()), dict(actions={}, outcome="attention"), "a" * 64
    )
    assert store.alerts_due() == [overview["IncidentID"]]
    store.alert_sent(overview["IncidentID"], 1, 2, 3)
    assert store.alerts_due() == []
    assert overview["IncidentID"] not in {r["IncidentID"] for r in store.list_open()}
    store.observe(
        "recovery_overview", overview["SourceID"], dict(actions={}, outcome="changed"), "b" * 64
    )
    assert store.alerts_due() == []  # Changed summaries are coalesced for five minutes.


def test_group_reconciles_exact_private_copy_after_restart(store, recovery):
    from services.recovery_service import RecoveryService
    from tests.test_guided_recovery import ACTOR

    r = recovery
    damage(r)
    service = RecoveryService(
        store, {"private_evidence": r.adapter}, admin_id=1, guild_id=2, channel_id=3
    )
    row = service.review_source(ACTOR, "private_evidence", r.reference)
    dal = RecoveryBacklogDAL(store)
    group = dal.approve(dal.preview(), "discord:1")
    # No filesystem write occurs until the restarted service reconciles the
    # individually persisted approval through the real protected-copy adapter.
    assert not (r.tmp_path / r.receipt.key).exists()
    restarted = RecoveryService(
        store, {"private_evidence": r.adapter}, admin_id=1, guild_id=2, channel_id=3
    )
    result = restarted.refresh(row["IncidentID"])
    assert result["State"] == "resolved" and not result["pending_action"]
    assert r.private.read(r.receipt) == r.raw
    final, _, complete = EvidenceBatchAdapter(store).inspect(group)
    assert complete and final["verified_count"] == 1
