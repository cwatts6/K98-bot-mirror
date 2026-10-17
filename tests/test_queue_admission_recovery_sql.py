import os

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.queue_admission_recovery import QueueAdmissionRecovery
from services.queue_admission_recovery_dal import QueueAdmissionDAL
from services.recovery_service import RecoveryService
from tests.test_export_target_containment_sql import contained_job as contained_job
from tests.test_guided_recovery import ACTOR, Store, execute
from tests.test_producer_admission_recovery_sql import unstarted
from tests.test_producer_refusal_sql import refused as refused

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
    unstarted(r, "pending")
    adapter, store, service, row = service_for(r)
    assert adapter.pending_recovery() == [r.source]
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
def test_admitted_or_uncertain_work_requires_domain_recovery(refused, stage):
    r = refused
    unstarted(r, stage)
    _, _, _, row = service_for(r)
    assert not row["evidence"]["actions"]
    assert row["evidence"]["recovery_links"][0]["kind"] == "producer_refusal"
    assert r.runtime.dal.read(r.source)["State"] == stage


def test_admission_race_does_not_release_new_owner(refused):
    r = refused
    unstarted(r, "pending")
    adapter, store, service, row = service_for(r)
    r.runtime.dal.claim(
        r.source,
        account=r.runtime.account,
        storage_owner="disk",
        stage="preflight",
        resource_keys=("account:" + r.runtime.account,),
    )
    result = execute(service, row, action="withdraw_queued")
    assert result["evidence"]["outcome"] == "execution_review_required"
    assert not store.actions
    assert r.runtime.dal.read(r.source)["State"] == "preflight"


def test_lost_withdrawal_reply_reconciles_without_repeating(refused, monkeypatch):
    r = refused
    unstarted(r, "pending")
    adapter, store, service, row = service_for(r)
    withdraw = adapter.dal.withdraw

    def lost(*args):
        withdraw(*args)
        raise TimeoutError("lost response")

    monkeypatch.setattr(adapter.dal, "withdraw", lost)
    result = execute(service, row, action="withdraw_queued")
    assert result["State"] == "resolved"
    assert store.actions[0]["State"] == "verified"
