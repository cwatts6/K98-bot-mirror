"""Cache-only closeout uses real temporary SQL rows and durable action receipts."""

import json
import os
from unittest.mock import Mock

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.configuration_producer_recovery import ConfigurationProducerRecovery
from services.legacy_export_snapshot_service import SnapshotUnavailable
from services.player_report_recovery_service import PlayerReportRecoveryAdapter
from services.recovery_release_policy import p0a_presentation
from services.recovery_service import RecoveryService
from tests import test_import_capture_recovery_sql as capture_fixtures
from tests.test_guided_recovery import ACTOR, Store

recovery = capture_fixtures.recovery

pytestmark = pytest.mark.skipif(
    os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Disposable SQL opt-in required"
)


def adapter_type(r):
    return (
        ConfigurationProducerRecovery
        if r.outcomes.producer_kind == "configuration_import"
        else PlayerReportRecoveryAdapter
    )


def no_export_intent(r):
    return (
        "configuration_only_v1"
        if r.outcomes.producer_kind == "configuration_import"
        else "cache_only_v1"
    )


def captured(r, monkeypatch, disposition):
    prep = r.outcomes.inspect(r.source)["preparation"]
    request = json.loads(prep["RequestJson"])
    if disposition:
        request["request"]["producer"]["export_disposition"] = disposition
        r.owner.execute(
            r.rewrite(
                "UPDATE dbo.ExportPreparation SET RequestJson=?,RequestHash=? WHERE PreparationID=?"
            ),
            json.dumps(request),
            digest(request),
            r.source,
        )
    # Stop after durable capture, before any queue admission, as the cache does.
    enqueue = Mock(side_effect=TimeoutError("no queue requested"))
    monkeypatch.setattr(r.runtime, "enqueue_snapshot", enqueue)
    with pytest.raises(TimeoutError):
        r.service.run(r.source, r.outcomes.inspect(r.source)["token"], "fixture")
    enqueue.reset_mock()
    return enqueue


def discover(r):
    r.owner.execute(
        r.rewrite(
            "UPDATE dbo.ExportPreparation SET UpdatedUTC=DATEADD(second,-180,SYSUTCDATETIME()) "
            "WHERE PreparationID=?"
        ),
        r.source,
    )
    return r.outcomes.pending_recovery()


@pytest.mark.parametrize("recovery", ["player_report", "configuration_producer"], indirect=True)
@pytest.mark.parametrize("lost_reply", [None, "approval", "closeout"])
def test_automatic_closeout_survives_restart_and_never_queues(recovery, monkeypatch, lost_reply):
    r = recovery
    enqueue = captured(r, monkeypatch, no_export_intent(r))
    before = r.outcomes.inspect(r.source)["preparation"]
    adapter, store = adapter_type(r)(r.outcomes, r.service), Store()
    service = RecoveryService(
        store,
        {adapter.kind: adapter},
        admin_id=1,
        guild_id=2,
        channel_id=3,
        presentation_policy=p0a_presentation,
    )
    row = service.review_source(ACTOR, adapter.kind, r.source)
    assert r.source in discover(r)
    assert set(row["evidence"]["actions"]) == {adapter.automatic_action}
    from services.recovery_report import incident_report

    report = incident_report(service, row)
    assert "automatically" in report["next_step"]
    assert no_export_intent(r) in json.dumps(report)
    if lost_reply == "approval":
        store.lose_claim_ack = True
    if lost_reply == "closeout":
        conclude = r.service.dal.conclude

        def lose_ack(*args, **kwargs):
            conclude(*args, **kwargs)
            monkeypatch.setattr(r.service.dal, "conclude", conclude)
            raise TimeoutError("lost closeout reply")

        monkeypatch.setattr(r.service.dal, "conclude", lose_ack)
    try:
        service.recover_automatic(row["IncidentID"])
    except Exception:
        assert lost_reply
    if lost_reply != "approval":
        # Even a lost closeout reply must not rediscover completed cache history.
        # The persisted incident below still reconciles the same saved action.
        assert r.source not in discover(r)
    restarted = adapter_type(r)(r.outcomes, type(r.service)(r.runtime, r.outcomes))
    service = RecoveryService(
        store,
        {adapter.kind: restarted},
        admin_id=1,
        guild_id=2,
        channel_id=3,
        presentation_policy=p0a_presentation,
    )
    result = service.recover_automatic(row["IncidentID"])
    assert result["State"] == "resolved", (result, store.actions)
    assert result["evidence"]["outcome"] == adapter.no_export_outcome
    assert store.actions[0]["State"] == "verified" and len(store.actions) == 1
    after = r.outcomes.inspect(r.source)
    assert after["preparation"]["JobID"] is None and not after["resources"]
    assert r.source not in discover(r)
    for field in ("SpoolKey", "SpoolHash", "SpoolBytes", "RequestJson"):
        assert after["preparation"][field] == before[field]
    enqueue.assert_not_called()


@pytest.mark.parametrize("recovery", ["player_report", "configuration_producer"], indirect=True)
@pytest.mark.parametrize(
    "state,marker",
    [
        ("unavailable", None),
        ("unavailable", {"actor": "fixture"}),
        ("unavailable", {"token": "0" * 64}),
        ("captured", {"actor": "fixture", "token": "0" * 64}),
    ],
)
def test_unavailable_without_complete_closeout_receipt_remains_discoverable(
    recovery, monkeypatch, state, marker
):
    r = recovery
    captured(r, monkeypatch, no_export_intent(r))
    generation = json.loads(r.outcomes.inspect(r.source)["preparation"]["GenerationJson"])
    if marker is not None:
        generation["capture_abandoned"] = marker
    r.owner.execute(
        r.rewrite(
            "UPDATE dbo.ExportPreparation SET State=?,GenerationJson=? " "WHERE PreparationID=?"
        ),
        state,
        json.dumps(generation),
        r.source,
    )
    assert r.source in discover(r)


@pytest.mark.parametrize("recovery", ["player_report", "configuration_producer"], indirect=True)
@pytest.mark.parametrize("disposition", [None, "pipeline_export_v1"])
def test_historical_and_pipeline_output_require_admin_decision(recovery, monkeypatch, disposition):
    r = recovery
    captured(r, monkeypatch, disposition)
    adapter = adapter_type(r)(r.outcomes, r.service)
    evidence, _, resolved = adapter.inspect(r.source)
    assert not resolved and adapter.automatic_action not in evidence["actions"]
    assert "queue_capture" in evidence["actions"]


@pytest.mark.parametrize("recovery", ["player_report", "configuration_producer"], indirect=True)
@pytest.mark.parametrize("failure", [FileNotFoundError, SnapshotUnavailable, PermissionError])
def test_missing_capture_does_not_authorize_automatic_closeout(recovery, monkeypatch, failure):
    r = recovery
    captured(r, monkeypatch, no_export_intent(r))
    monkeypatch.setattr(r.runtime, "verified_snapshot", Mock(side_effect=failure()))
    adapter = adapter_type(r)(r.outcomes, r.service)
    evidence, token, resolved = adapter.inspect(r.source)
    assert not resolved and adapter.automatic_action not in evidence["actions"]
    with pytest.raises(failure):
        adapter.execute(r.source, adapter.automatic_action, token, "test", "verify")
    assert r.outcomes.inspect(r.source)["preparation"]["State"] == "captured"


@pytest.mark.parametrize("recovery", ["player_report", "configuration_producer"], indirect=True)
@pytest.mark.parametrize("obstacle", ["active", "stale", "provider", "foreign", "intent"])
def test_automatic_closeout_rejects_live_or_changed_evidence(recovery, monkeypatch, obstacle):
    r = recovery
    enqueue = captured(r, monkeypatch, no_export_intent(r))
    adapter = adapter_type(r)(r.outcomes, r.service)
    preview = r.outcomes.inspect(r.source)
    token, prep = preview["token"], preview["preparation"]
    held = None
    if obstacle == "active":
        held = r.parameter("k98-legacy-output-snapshot")
        r.owner.execute(
            "EXEC sys.sp_getapplock @Resource=?,@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0",
            held,
        )
    elif obstacle == "stale":
        token = "0" * 64
    elif obstacle == "foreign":
        r.owner.execute(
            r.rewrite(
                "UPDATE dbo.ExportPreparation SET StorageOwner='foreign' WHERE PreparationID=?"
            ),
            r.source,
        )
    elif obstacle == "intent":
        request = json.loads(prep["RequestJson"])
        request["request"]["producer"]["export_disposition"] = "pipeline_export_v1"
        r.owner.execute(
            r.rewrite(
                "UPDATE dbo.ExportPreparation SET RequestJson=?,RequestHash=? WHERE PreparationID=?"
            ),
            json.dumps(request),
            digest(request),
            r.source,
        )
        token = r.outcomes.inspect(r.source)["token"]
    else:
        r.owner.execute(
            r.rewrite(
                """INSERT dbo.ExportExecutionStream
            (StreamID,SessionID,AccountKey,ActiveAccountKey,PreparationID,OwnerID,Fence,ClaimVersion,
             RegistrationHash,SnapshotHash,ScopeJson,Purpose,State,Version,LastSequence,ChildIdentity,CreatedUTC)
            VALUES (NEWID(),NEWID(),?,?,?, ?,?,?,0x01,0x02,N'{}','probe','open',1,0,NEWID(),SYSUTCDATETIME())"""
            ),
            prep["AccountKey"],
            prep["AccountKey"],
            r.source,
            prep["OwnerID"],
            prep["Fence"],
            prep["Version"],
        )
    try:
        with pytest.raises(SourceConflict):
            adapter.execute(r.source, adapter.automatic_action, token, "fixture", "verify")
    finally:
        if held:
            r.owner.execute("EXEC sys.sp_releaseapplock @Resource=?,@LockOwner='Session'", held)
    row = r.owner.execute(
        r.rewrite("SELECT State,GenerationJson FROM dbo.ExportPreparation WHERE PreparationID=?"),
        r.source,
    ).fetchone()
    assert row[0] == "captured" and "capture_abandoned" not in json.loads(row[1])
    enqueue.assert_not_called()
