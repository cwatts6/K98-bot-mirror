import json
import os
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.producer_refusal_recovery import ProducerRefusalRecovery
from services.recovery_service import RecoveryService
from tests.test_export_target_containment_sql import contained_job as contained_job
from tests.test_guided_recovery import ACTOR, execute
from tests.test_producer_refusal_sql import refused as refused, setup, unblock

pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Explicit temporary SQL opt-in"
)


@pytest.mark.parametrize("lost_reply", [False, True])
def test_cancel_retains_input_and_other_owner_then_verifies_after_restart(
    refused, monkeypatch, lost_reply
):
    r = refused
    adapter, store, service, row = setup(r)
    before = r.runtime.dal.read(r.source)
    if lost_reply:
        cancel = r.dal.cancel_saved_stage

        def lose(*args):
            cancel(*args)
            raise TimeoutError("reply lost")

        monkeypatch.setattr(r.dal, "cancel_saved_stage", lose)
    result = execute(service, row, action="cancel_saved_stage")
    assert result["State"] == "resolved"
    assert result["evidence"]["outcome"] == "saved_stage_cancelled"
    assert store.actions[0]["State"] == "verified"
    after = r.runtime.dal.read(r.source)
    assert after["RequestJson"] == before["RequestJson"]
    assert after["Fence"] == before["Fence"] + 1
    assert (
        r.f.sql.execute(
            "SELECT ActiveJobID FROM #ExportResource WHERE ResourceKey='account:test-account'"
        )
        .fetchval()
        .lower()
        == r.f.job
    )
    restarted = RecoveryService(
        store,
        {adapter.kind: ProducerRefusalRecovery(r.dal, adapter.imports, adapter.runner)},
        admin_id=1,
        guild_id=2,
        channel_id=3,
    )
    assert restarted.review(ACTOR, row["IncidentID"])["State"] == "resolved"
    with r.dal.serialized(r.source), pytest.raises(SourceConflict, match="permanently cancelled"):
        r.dal.reserve(r.source, str(uuid4()))
    adapter.runner.assert_not_called()


def test_active_child_prevents_cancel_and_stale_admin_decision(refused):
    r = refused
    unblock(r)
    adapter, _, service, row = setup(r)
    with r.dal.serialized(r.source):
        r.dal.reserve(r.source, str(uuid4()))
    with pytest.raises(SourceConflict):
        execute(service, row, action="cancel_saved_stage")
    assert "cancel_saved_stage" not in adapter.inspect(r.source)[0]["actions"]
    adapter.runner.assert_not_called()


def test_cancel_after_closed_original_and_unused_continuation(refused):
    from tests.test_producer_admission_recovery_sql import unstarted

    r = refused
    unstarted(r, "preflight")
    _, store, service, row = setup(r)
    row = execute(service, row, action="close_unstarted_admission")
    with r.dal.serialized(r.source):
        action = str(uuid4())
        r.dal.reserve(r.source, action)
        r.dal.close_unused(r.source, action)
    row = service.review(ACTOR, row["IncidentID"])
    result = execute(service, row, action="cancel_saved_stage")
    assert result["State"] == "resolved"
    assert all(a["State"] == "verified" for a in store.actions)
    assert json.loads(r.runtime.dal.read(r.source)["GenerationJson"])["producer_stage_cancelled"][
        "prior"
    ]


def test_guided_summary_identifies_original_input_and_configuration(refused):
    _, _, service, row = setup(refused)
    summary = service.review_decision_summary(
        ACTOR, row["IncidentID"], "cancel_saved_stage", row["Revision"], row["EvidenceHash"]
    )
    text = str(summary["fields"])
    assert "scan.xlsx" in text and refused.inputs["completed_filename"] in text
    assert "settings match" in text and "no longer needed" in text


def test_lost_approval_ack_verifies_without_new_dispatch(refused):
    from kvk.dal.new_source_import_dal import UncertainCommit

    adapter, store, service, row = setup(refused)
    store.lose_claim_ack = True
    with pytest.raises(UncertainCommit):
        execute(service, row, action="cancel_saved_stage")
    service.refresh(row["IncidentID"])
    result = service.refresh(row["IncidentID"])
    assert result["State"] == "resolved"
    assert len(store.actions) == 1 and store.actions[0]["State"] == "verified"
    adapter.runner.assert_not_called()


def test_mutated_cancellation_marker_cannot_claim_success(refused):
    _, _, service, row = setup(refused)
    execute(service, row, action="cancel_saved_stage")
    refused.f.sql.execute(
        "UPDATE #ExportPreparation SET GenerationJson=JSON_MODIFY(GenerationJson,'$.producer_stage_cancelled.version',99) WHERE PreparationID=?",
        refused.source,
    )
    with pytest.raises(SourceConflict, match="receipt differs"):
        service.refresh(row["IncidentID"])


def test_sql_registered_original_cannot_be_cancelled(refused):
    from services.stats_import_outcome_dal import StatsImportOutcomeDAL
    from tests.test_producer_admission_recovery_sql import unstarted

    r = refused
    claim = unstarted(r, "writing")
    StatsImportOutcomeDAL(r.f.connect, account=r.runtime.account, storage_owner="disk").prepare(
        claim, r.inputs["completed_filename"]
    )
    adapter, _, _, row = setup(r)
    assert "cancel_saved_stage" not in row["evidence"]["actions"]
    with r.dal.serialized(r.source), pytest.raises(SourceConflict):
        r.dal.cancel_saved_stage(r.source, row["EvidenceHash"], str(uuid4()))
    adapter.runner.assert_not_called()
