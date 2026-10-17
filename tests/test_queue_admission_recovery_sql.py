import json
import os
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.queue_admission_recovery import QueueAdmissionRecovery
from services.queue_admission_recovery_dal import QueueAdmissionDAL
from services.recovery_service import RecoveryService
from tests.test_export_target_containment_sql import contained_job as contained_job
from tests.test_guided_recovery import ACTOR, Store, execute
from tests.test_producer_admission_recovery_sql import unstarted
from tests.test_producer_refusal_sql import refused as refused, unblock


def legacy_unstarted(r):
    unblock(r)
    request = json.loads(r.runtime.dal.read(r.source)["RequestJson"])["request"]
    request.pop("producer")
    request["operation"] = str(uuid4())
    r.source = r.runtime.dal.request(
        account=r.runtime.account,
        consumer="scan_data",
        kvk_no=None,
        request=request,
        storage_owner="disk",
        actor="test",
        reason="Legacy queued request",
    )


pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Explicit local disposable SQL opt-in"
)


def service_for(r):
    adapter = QueueAdmissionRecovery(QueueAdmissionDAL(r.runtime))
    store = Store()
    service = RecoveryService(store, {adapter.kind: adapter}, admin_id=1, guild_id=2, channel_id=3)
    row = service.review_source(ACTOR, adapter.kind, r.source)
    return adapter, store, service, row


def test_cancel_initial_queue_entry_fences_late_worker_and_verifies(refused):
    r = refused
    legacy_unstarted(r)
    adapter, store, service, row = service_for(r)
    assert r.source in adapter.pending_recovery()
    assert "withdraw_queued" in row["evidence"]["actions"]
    result = execute(service, row, action="withdraw_queued")
    assert result["State"] == "resolved" and store.actions[0]["State"] == "verified"
    assert r.runtime.dal.read(r.source)["State"] == "unavailable"
    with pytest.raises(SourceConflict):
        r.runtime.dal.claim(
            r.source,
            account=r.runtime.account,
            storage_owner="disk",
            stage="preflight",
            resource_keys=("account:" + r.runtime.account,),
        )


@pytest.mark.parametrize("stage", ["preflight", "sql_pending", "writing", "uncertain"])
@pytest.mark.asyncio
async def test_admitted_or_uncertain_work_requires_domain_recovery(refused, stage):
    from ui.views.recovery_view import RecoveryIncidentView

    r = refused
    unstarted(r, stage)
    _, _, _, row = service_for(r)
    assert not row["evidence"]["actions"]
    assert row["State"] == "open"
    assert row["evidence"]["recovery_links"][0]["kind"] == "producer_refusal"
    view = RecoveryIncidentView(row)
    assert "Review execution and ownership" in [item.label for item in view.children]
    assert r.runtime.dal.read(r.source)["State"] == stage


def test_admission_race_does_not_release_new_owner(refused):
    r = refused
    legacy_unstarted(r)
    adapter, store, service, row = service_for(r)
    r.runtime.dal.claim(
        r.source,
        account=r.runtime.account,
        storage_owner="disk",
        stage="preflight",
        resource_keys=("account:" + r.runtime.account,),
    )
    with pytest.raises(SourceConflict, match="evidence changed"):
        execute(service, row, action="withdraw_queued")
    result = service.review(ACTOR, row["IncidentID"])
    assert result["evidence"]["outcome"] == "execution_review_required"
    assert result["State"] == "open"
    assert not store.actions
    assert r.runtime.dal.read(r.source)["State"] == "preflight"


def test_lost_withdrawal_reply_reconciles_without_repeating(refused, monkeypatch):
    r = refused
    legacy_unstarted(r)
    adapter, store, service, row = service_for(r)
    withdraw = adapter.dal.withdraw

    def lost(*args):
        withdraw(*args)
        raise TimeoutError("lost response")

    monkeypatch.setattr(adapter.dal, "withdraw", lost)
    result = execute(service, row, action="withdraw_queued")
    assert result["State"] == "resolved"
    assert store.actions[0]["State"] == "verified"


def test_typed_queue_routes_to_domain_close_and_saved_continuation(refused):
    from tests.test_producer_refusal_sql import setup

    r = refused
    unstarted(r, "pending")
    adapter, _, _, row = service_for(r)
    assert not row["evidence"]["actions"]
    assert row["evidence"]["recovery_links"][0]["kind"] == "producer_refusal"
    with pytest.raises(SourceConflict):
        adapter.dal.withdraw(r.source, row["EvidenceHash"], str(uuid4()))
    producer, store, service, row = setup(r)
    closed = execute(service, row, action="close_unstarted_admission")
    assert store.actions[0]["State"] == "verified"
    assert closed["evidence"]["actions"].keys() == {"resume_sql_stage"}
    execute(service, closed, action="resume_sql_stage")
    producer.runner.assert_called_once_with(r.inputs)


@pytest.mark.parametrize(
    "producer_kind,linked_kind",
    [
        ("configuration_import", "configuration_producer"),
        ("player_stats_report", "player_report"),
    ],
)
def test_other_typed_producers_preserve_domain_cancellation(refused, producer_kind, linked_kind):
    r = refused
    unblock(r)
    request = json.loads(r.runtime.dal.read(r.source)["RequestJson"])["request"]
    request["operation"] = str(uuid4())
    request["producer"]["kind"] = producer_kind
    r.source = r.runtime.dal.request(
        account=r.runtime.account,
        consumer="scan_data",
        kvk_no=None,
        request=request,
        storage_owner="disk",
        actor="test",
        reason="Typed queued request",
    )
    adapter, _, _, row = service_for(r)
    assert not row["evidence"]["actions"]
    assert row["evidence"]["recovery_links"][0]["kind"] == linked_kind
    with pytest.raises(SourceConflict):
        adapter.dal.withdraw(r.source, row["EvidenceHash"], str(uuid4()))
    assert r.runtime.dal.read(r.source)["State"] == "pending"


def test_queue_discovery_covers_more_than_one_page_and_wraps(refused):
    r = refused
    expected = set()
    for _ in range(45):
        unstarted(r, "pending")
        expected.add(r.source)
    dal = QueueAdmissionDAL(r.runtime)
    first = dal.pending()
    second = dal.pending(first[-1])
    third = dal.pending(second[-1])
    assert len(first) == len(second) == len(third) == 20
    assert not set(first) & set(second)
    assert set(first + second + third) == expected
    assert set(first) & set(third)  # cyclic continuation, with rows still pending
    # The cursor is an ordering boundary, not a row lookup: deletion/state change
    # of that preparation must not restart discovery at the first page.
    r.f.sql.execute(
        "UPDATE #ExportPreparation SET State='unavailable',OwnerID=?,Fence=1,Version=2 WHERE PreparationID=?",
        str(uuid4()),
        first[-1],
    )
    assert dal.pending(first[-1]) == second


@pytest.mark.parametrize("verified", [False, True])
def test_terminal_queue_state_requires_owning_domain_verification(refused, verified):
    from unittest.mock import Mock

    r = refused
    unstarted(r, "pending")
    r.f.sql.execute(
        "UPDATE #ExportPreparation SET State='unavailable',OwnerID=?,Fence=1,Version=2 WHERE PreparationID=?",
        str(uuid4()),
        r.source,
    )
    dal = QueueAdmissionDAL(r.runtime)
    assert QueueAdmissionRecovery(dal).inspect(r.source)[2] is False
    domain = Mock()
    domain.inspect.return_value = ({}, "d" * 64, verified)
    adapter = QueueAdmissionRecovery(dal, {"producer_refusal": domain})
    evidence, _, resolved = adapter.inspect(r.source)
    assert resolved is verified
    assert not evidence["actions"]
    assert evidence["outcome"] == (
        "domain_recovery_verified" if verified else "execution_review_required"
    )
    domain.inspect.assert_called_once_with(r.source)
    domain.inspect.side_effect = TimeoutError("verification unavailable")
    with pytest.raises(TimeoutError):
        adapter.inspect(r.source)
