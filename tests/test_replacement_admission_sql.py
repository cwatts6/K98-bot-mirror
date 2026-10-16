"""Guided waiting, exact owner links and continuation on disposable SQL."""

from datetime import datetime
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.recovery_service import RecoveryService
from services.replacement_admission_dal import admission_blocker
from tests import test_export_target_containment_sql as fixture_module
from tests.test_export_replacement_guided_sql import (
    contained_job as contained_job,
    guided as guided,
    proposal_service as proposal_service,
    pytestmark as pytestmark,
    recovery as recovery,
    store as store,
    verification as verification,
)
from tests.test_guided_recovery import ACTOR


@pytest.fixture(autouse=True)
def import_receipt_table(monkeypatch):
    monkeypatch.setattr(
        fixture_module, "TABLES", (*fixture_module.TABLES, "dbo.StatsImportExecution")
    )


def pending(r, *, consumer="config", producer=None, account="test-account"):
    key = str(uuid4())
    document = dict(request=dict(operation=key, producer=dict(kind=producer)))
    r.f.insert(
        "ExportPreparation",
        dict(
            PreparationID=key,
            AccountKey=account,
            ConsumerKind=consumer,
            KVK_NO=1 if consumer == "all_kvk" else None,
            RequestHash=digest(document),
            EnqueueSequence=20,
            State="pending",
            Fence=0,
            Version=1,
            StorageOwner="disk",
            RequestJson=json.dumps(document),
            Actor="test",
            Reason="Disposable admission test",
            CreatedUTC=datetime(2026, 10, 1),
            UpdatedUTC=datetime(2026, 10, 1),
        ),
    )
    return key


@pytest.mark.parametrize(
    "consumer,producer,route",
    [
        ("config", None, "configuration_read"),
        ("all_kvk", None, "all_kvk_capture"),
        ("scan_data", "stats_import", "producer_refusal"),
        ("scan_data", "player_stats_report", "player_report"),
    ],
)
def test_queued_owner_routes_without_claim_and_stale_verify_cannot_dispatch(
    guided, consumer, producer, route
):
    r = guided
    before = r.recovery.review(ACTOR, r.row["IncidentID"])
    key = pending(r, consumer=consumer, producer=producer)
    with pytest.raises(SourceConflict, match="evidence changed"):
        r.recovery.execute(
            ACTOR,
            before["IncidentID"],
            before["Revision"],
            before["EvidenceHash"],
            "verify_replacements",
            "stale confirmation",
        )
    row = r.recovery.review(ACTOR, r.row["IncidentID"])
    assert row["evidence"]["outcome"] == "replacement_waiting_for_access"
    assert row["evidence"]["recovery_links"] == [
        dict(label="Review blocking operation", kind=route, source_id=key)
    ]
    assert "verify_replacements" not in row["evidence"]["actions"]
    assert not r.runtime.sent
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementVerification").fetchval() == 0


@pytest.mark.asyncio
async def test_restart_then_guided_button_verifies_after_blocker_settles(guided, monkeypatch):
    from ui.views import recovery_view as view

    r = guided
    key = pending(r)
    waiting = r.recovery.review(ACTOR, r.row["IncidentID"])
    assert "Review blocking operation" in {
        b.label for b in view.RecoveryIncidentView(waiting).children
    }
    # This fixture models a separately verified read settlement, not a repair
    # issued by replacement admission. The admission implementation is read-only.
    r.f.sql.execute(
        "UPDATE #ExportPreparation SET State='completed',OwnerID=?,Fence=1,Version=2 WHERE PreparationID=?",
        key,
        key,
    )
    restarted = RecoveryService(
        r.recovery.store, r.recovery.adapters, admin_id=1, guild_id=2, channel_id=3
    )
    row = restarted.review(ACTOR, r.row["IncidentID"])
    assert "verify_replacements" in row["evidence"]["actions"]
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))

    async def call(method, *args):
        return getattr(restarted, method)(*args)

    monkeypatch.setattr(view, "call", call)
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    button = next(
        b for b in view.RecoveryIncidentView(row).children if b.label == "Check replacement files"
    )
    await button.callback(interaction)
    preview = interaction.followup.send.call_args.kwargs
    assert preview["ephemeral"] and isinstance(preview["view"], view.RecoveryConfirmView)
    await preview["view"].children[0].callback(interaction)
    result = interaction.followup.send.call_args.kwargs["view"].row
    assert result["evidence"]["outcome"] == "activation_required"
    assert len(r.runtime.sent) == 5
    assert (
        r.f.sql.execute("SELECT State FROM #ExportJob WHERE JobID=?", r.f.job).fetchval()
        == "uncertain"
    )


def test_foreign_account_reservation_does_not_leak_owner_or_enable_verification(guided):
    r = guided
    key = pending(r, account="another-account")
    r.f.sql.execute(
        "UPDATE #ExportResource SET ActivePreparationID=?,OwnerID=?,Fence=3,Version=Version+1 WHERE ResourceKey='account:test-account'",
        key,
        key,
    )
    row = r.recovery.review(ACTOR, r.row["IncidentID"])
    assert row["evidence"]["outcome"] == "replacement_waiting_for_access"
    assert "recovery_links" not in row["evidence"]
    assert key not in json.dumps(row["evidence"])
    assert "verify_replacements" not in row["evidence"]["actions"]
    with pytest.raises(SourceConflict):
        admission_blocker(
            r.f.connect, account="another-account", replacement_id=r.plan.value()["replacement_id"]
        )


def test_blocking_replacement_check_routes_to_original_job(guided):
    r = guided
    r.begin()
    blocker = admission_blocker(
        r.f.connect, account="test-account", replacement_id=r.plan.value()["replacement_id"]
    )
    assert blocker["reason"] == "reserved"
    assert blocker["owner"]["kind"] == "export_job"
    assert blocker["owner"]["source_id"] == r.f.job


@pytest.mark.parametrize("held", [False, True])
@pytest.mark.parametrize("kind", ["job", "rollover"])
def test_queued_or_held_job_and_rollover_have_exact_links(guided, held, kind):
    r = guided
    key = str(uuid4())
    if kind == "job":
        cursor = r.f.sql.execute("SELECT * FROM #ExportJob WHERE JobID=?", r.f.job)
        data = dict(zip((c[0] for c in cursor.description), cursor.fetchone(), strict=True))
        data.update(
            JobID=key,
            InputHash=digest(key),
            EnqueueSequence=20,
            State="uncertain" if held else "ready",
            OwnerID=r.f.owner if held else None,
            Fence=2 if held else 0,
        )
        r.f.insert("ExportJob", data)
        column = "ActiveJobID"
    else:
        pool = str(uuid4())
        r.f.insert(
            "SourceOutputOperation",
            dict(
                OperationID=key,
                PoolID=pool,
                AccountKey="test-account",
                SourceKey="snapshot_report_v1",
                OldKVK=7,
                OldChoiceID=str(uuid4()),
                NewKVK=8,
                NewChoiceID=str(uuid4()),
                OldEpoch=4,
                TargetEpoch=5,
                PlanHash=digest({}),
                PlanJson="{}",
                ConfirmedBy="test",
                GuildID="1",
                ChannelID="2",
                Reason="Synthetic blocker",
                ConfirmedUTC=datetime(2026, 10, 1),
                EnqueueSequence=20,
                State="uncertain",
                ActivePoolID=pool,
                OwnerID=r.f.owner,
                Fence=2,
                Version=7,
                Phase="uncertain",
                ProgressJson="{}",
                UpdatedUTC=datetime(2026, 10, 1),
            ),
        )
        column = "ActiveOutputOperationID"
    if held:
        r.f.sql.execute(
            f"UPDATE #ExportResource SET {column}=?,OwnerID=?,Fence=2,Version=Version+1 WHERE ResourceKey='account:test-account'",
            key,
            r.f.owner,
        )
    row = r.recovery.review(ACTOR, r.row["IncidentID"])
    assert row["evidence"]["recovery_links"][0] == dict(
        label="Review blocking operation", kind="export_" + kind, source_id=key
    )
    assert "verify_replacements" not in row["evidence"]["actions"]
    assert not r.runtime.sent
