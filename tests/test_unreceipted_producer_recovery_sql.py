"""Legacy unknown outcomes stay unknown through exact scoped disposition and succession."""

import json
import os
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.configuration_producer_recovery import ConfigurationProducerRecovery
from services.legacy_configuration_continuation import (
    LegacyConfigurationContinuation,
    LegacyConfigurationContinuationDAL,
)
from services.recovery_release_policy import p0a_presentation
from services.recovery_service import RecoveryService
from services.unreceipted_producer_recovery import (
    MARKER,
    UnreceiptedProducerDAL,
    UnreceiptedProducerRecovery,
)
from tests.test_configuration_continuation_sql import commit_child, run
from tests.test_guided_recovery import ACTOR, Store
from tests.test_import_capture_recovery_sql import recovery as recovery

pytestmark = [
    pytest.mark.skipif(os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Local SQL opt-in"),
    pytest.mark.parametrize("recovery", ["configuration_continuation"], indirect=True),
]


def legacy(r):
    r.runtime.account = "a"
    config = json.loads(r.runtime.configuration)
    config["config"] = dict(consumer="config", destinations=["source_sheet"])
    r.runtime.configuration = json.dumps(config)
    prep = r.outcomes.inspect(r.source)["preparation"]
    request = json.loads(prep["RequestJson"])
    request["request"].pop("producer")
    r.owner.execute(
        r.rewrite(
            "UPDATE dbo.ExportPreparation SET RequestJson=?,RequestHash=?,GenerationJson=?,State='uncertain' WHERE PreparationID=?"
        ),
        json.dumps(request),
        digest(request),
        json.dumps({"historical_partial": "configuration step outcome unknown"}),
        r.source,
    )
    dal = UnreceiptedProducerDAL(r.connect, account="a", storage_owner="disk-a")
    return UnreceiptedProducerRecovery(dal, configuration=r.runtime.configuration)


def test_unknown_disposition_preserves_original_evidence_and_fences_only_exact_owner(recovery):
    r = recovery
    adapter = legacy(r)
    before = adapter.dal.inspect(r.source)
    assert r.source in adapter.pending_recovery()
    action_id = str(uuid4())
    adapter.execute(
        r.source,
        "retain_unknown",
        before["token"],
        "recovery:" + action_id,
        "Original result cannot be established",
    )
    evidence, _, resolved = adapter.inspect(r.source)
    assert resolved and evidence["outcome"] == "unknown_result_retained"
    after = adapter.dal.inspect(r.source)
    document = json.loads(after["preparation"]["GenerationJson"])
    assert document["historical_partial"] == "configuration step outcome unknown"
    assert document[MARKER]["request_sha256"] == bytes(before["preparation"]["RequestHash"]).hex()
    assert after["preparation"]["Fence"] == before["preparation"]["Fence"] + 1
    assert after["resources"] == [] and after["execution"] is None
    assert (
        adapter.reconcile(
            r.source,
            dict(
                ActionID=action_id,
                ActionKind="retain_unknown",
                EvidenceHash=before["token"],
                Reason="kept",
            ),
        )
        == "verified"
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "UPDATE dbo.ExportResource SET OwnerID=NEWID()",
        "UPDATE dbo.ExportResource SET Fence=Fence+1",
        "UPDATE dbo.ExportPreparation SET Version=Version+1",
    ],
)
def test_changed_or_foreign_ownership_and_stale_preview_cannot_close(recovery, mutation):
    r = recovery
    adapter = legacy(r)
    token = adapter.dal.inspect(r.source)["token"]
    r.owner.execute(r.rewrite(mutation))
    with pytest.raises(SourceConflict):
        adapter.execute(
            r.source, "retain_unknown", token, "recovery:" + str(uuid4()), "stale decision"
        )
    assert (
        r.owner.execute(
            r.rewrite(
                "SELECT COUNT(*) FROM dbo.ExportResource WHERE ActivePreparationID IS NOT NULL"
            )
        ).fetchval()
        == 1
    )


def test_live_producer_prevents_unknown_disposition(recovery):
    r = recovery
    adapter = legacy(r)
    token = adapter.dal.inspect(r.source)["token"]
    with r.service.dal.session(r.source):
        with pytest.raises(SourceConflict, match="still active"):
            adapter.execute(r.source, "retain_unknown", token, "recovery:" + str(uuid4()), "wait")


def test_fresh_configuration_is_separately_confirmed_and_original_stays_unknown(recovery):
    r = recovery
    generation = json.loads(r.outcomes.inspect(r.source)["preparation"]["GenerationJson"])
    original = legacy(r)
    token = original.dal.inspect(r.source)["token"]
    original.execute(
        r.source, "retain_unknown", token, "recovery:" + str(uuid4()), "retain unknown original"
    )
    producer = ConfigurationProducerRecovery(r.outcomes, r.service)
    calls = []

    def runner():
        calls.append(1)
        commit_child(r, generation, lost_reply=True)

    adapter = LegacyConfigurationContinuation(
        LegacyConfigurationContinuationDAL(r.runtime, r.outcomes), producer, runner
    )
    service = RecoveryService(
        Store(),
        {adapter.kind: adapter, producer.kind: producer},
        admin_id=1,
        guild_id=2,
        channel_id=3,
        presentation_policy=p0a_presentation,
    )
    row = service.review_source(ACTOR, adapter.kind, r.source)
    assert set(row["evidence"]["actions"]) == {"retry_configuration", "keep_prior"}
    assert "unknown" in row["evidence"]["explanation"]
    result = run(service, row, "retry_configuration")
    assert len(calls) == 1
    child = adapter.dal.snapshot(r.source)["child"]
    assert child and child["PreparationID"] != r.source
    assert (
        json.loads(child["RequestJson"])["request"]["producer"]["export_disposition"]
        == "configuration_only_v1"
    )
    service.refresh(row["IncidentID"])
    assert len(calls) == 1
    assert original.inspect(r.source)[0]["outcome"] == "unknown_result_retained"
    assert result["State"] == "open"  # The fresh child still needs its own capture receipt.
