"""Historical capture retirement through private buttons and disposable SQL receipts."""

import json
import os
from types import MethodType, SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from services.export_coordination_dal import ExportCoordinationDAL
from services.historical_import_recovery_service import ACTION
from services.import_recovery_service import ImportRecoveryAdapter
from services.legacy_export_snapshot_service import LegacyExportRuntime
from services.recovery_release_policy import p0a_presentation
from services.recovery_service import RecoveryActor, RecoveryService, SourceConflict
from tests.test_guided_recovery import ACTOR
from tests.test_import_capture_recovery_sql import recovery as recovery
from tests.test_recovery_sql import store as store

pytestmark = [
    pytest.mark.skipif(
        os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Disposable SQL opt-in"
    ),
    pytest.mark.parametrize("recovery", ["scan_data"], indirect=True),
]


@pytest.fixture
def historical(recovery, monkeypatch):
    r = recovery
    monkeypatch.setattr(
        r.runtime,
        "enqueue_snapshot",
        lambda *_: (_ for _ in ()).throw(TimeoutError("capture only")),
    )
    with pytest.raises(TimeoutError):
        r.service.run(r.source, r.outcomes.inspect(r.source)["token"], "original_capture")
    # Reconstruct a pre-receipt captured preparation in isolated temporary tables.
    r.owner.execute(r.rewrite("DELETE dbo.StatsImportExecution WHERE PreparationID=?"), r.source)
    r.runtime.account = "a"
    r.runtime.coordinator = ExportCoordinationDAL(r.connect, preparations=True)
    r.runtime.verified_snapshot = MethodType(LegacyExportRuntime.verified_snapshot, r.runtime)
    r.runtime.enqueue_snapshot = MethodType(LegacyExportRuntime.enqueue_snapshot, r.runtime)
    r.adapter = ImportRecoveryAdapter(r.outcomes, r.service)
    return r


@pytest.mark.asyncio
@pytest.mark.parametrize("lost_reply", [False, True])
async def test_private_review_confirm_restart_and_no_replay(
    historical, store, monkeypatch, lost_reply
):
    from services.recovery_report import incident_report
    from ui.views import recovery_review_view as review, recovery_view as view

    r = historical
    service = RecoveryService(
        store,
        {"stats_import": r.adapter},
        admin_id=1,
        guild_id=2,
        channel_id=3,
        presentation_policy=p0a_presentation,
    )
    row = service.review_source(ACTOR, "stats_import", r.source)
    assert set(row["evidence"]["actions"]) == {ACTION}
    assert row["evidence"]["outcome"] == "unproven"
    assert row["evidence"]["failure_context"]["input_file"].startswith("stats_")
    for actor in (RecoveryActor(9, 2, 3), RecoveryActor(1, 9, 3), RecoveryActor(1, 2, 9)):
        with pytest.raises(SourceConflict):
            service.review_details_page(
                actor, row["IncidentID"], ACTION, row["Revision"], row["EvidenceHash"]
            )

    async def call(name, *args):
        return getattr(service, name)(*args)

    for module in (view, review):
        monkeypatch.setattr(module, "actor_for", lambda _: ACTOR)
        monkeypatch.setattr(module, "safe_defer", AsyncMock(return_value=True))
        monkeypatch.setattr(module, "call", call)
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    button = next(
        b for b in view.RecoveryIncidentView(row).children if b.label == "Retire historical export"
    )
    before = r.outcomes.inspect(r.source)
    await button.callback(interaction)
    labels, text = [], []
    while True:
        payload = interaction.followup.send.call_args.kwargs
        assert payload["ephemeral"]
        labels.extend(f.name for f in payload["embed"].fields)
        text.extend(f.value for f in payload["embed"].fields)
        page = payload["view"]
        if page.next.disabled:
            break
        assert page.confirm.disabled
        await page.next.callback(interaction)
    assert {"Historical SQL outcome", "Original destination 1", "Current destination 1"} <= set(
        labels
    )
    assert "stats\\_" in "".join(text)
    assert r.outcomes.inspect(r.source) == before
    await page.confirm.callback(interaction)
    confirm = interaction.followup.send.call_args.kwargs["view"]
    execute = r.adapter.execute
    calls = []

    def interrupted(*args):
        calls.append(args)
        execute(*args)
        if lost_reply:
            raise TimeoutError("lost commit acknowledgement")

    monkeypatch.setattr(r.adapter, "execute", interrupted)
    await confirm.confirm.callback(interaction)
    restarted = RecoveryService(
        store,
        {"stats_import": ImportRecoveryAdapter(r.outcomes, r.service)},
        admin_id=1,
        guild_id=2,
        channel_id=3,
        presentation_policy=p0a_presentation,
    )
    final = restarted.review(ACTOR, row["IncidentID"])
    assert final["State"] == "resolved" and not final["pending_action"]
    assert final["evidence"]["outcome"] == "unproven"
    assert final["evidence"]["resolution"] == "historical_export_retired"
    report = incident_report(restarted, final)
    assert report["diagnosis"]["failure_context"]["sql_outcome"] == "unproven"
    await confirm.confirm.callback(interaction)
    assert len(calls) == 1
    after = r.outcomes.inspect(r.source)
    assert after["execution"] is None and not after["resources"]
    for key in ("SpoolKey", "SpoolHash", "SpoolBytes", "RequestJson", "OwnerID", "Fence"):
        assert after["preparation"][key] == before["preparation"][key]
    old = json.loads(before["preparation"]["GenerationJson"])
    new = json.loads(after["preparation"]["GenerationJson"])
    assert new.pop("historical_disposition")["sql_outcome"] == "unproven"
    assert new == old
    assert r.owner.execute(r.rewrite("SELECT COUNT(*) FROM dbo.ExportJob")).fetchval() == 0
    assert (
        r.owner.execute(r.rewrite("SELECT COUNT(*) FROM dbo.StatsImportExecution")).fetchval() == 0
    )
    assert r.source not in r.outcomes.pending_recovery()
    with pytest.raises(ValueError):
        r.runtime.enqueue_snapshot(r.source)


def test_changed_configuration_is_reviewable_without_adopting_it(historical):
    r = historical
    r.runtime.configuration = json.dumps(
        dict(scan_data=dict(consumer="scan_data", destinations=["changed_destination"]))
    )
    evidence, token, resolved = r.adapter.inspect(r.source)
    assert not resolved and ACTION in evidence["actions"]
    assert evidence["failure_context"]["registration_matches"] is False
    details = r.adapter.review_details(r.source, ACTION, token)
    assert {f.get("file_id") for f in details if "file_id" in f} == {
        "registered",
        "changed_destination",
    }


def test_stale_and_lost_dispatch_reconcile_without_business_execution(historical):
    r = historical
    _, token, _ = r.adapter.inspect(r.source)
    action = dict(
        ActionKind=ACTION,
        EvidenceHash=token,
        ActionID=str(uuid4()),
        Reason="Old export is obsolete",
    )
    # The persisted intent may precede a crash before dispatch. Same action can
    # safely perform only the version-bound metadata disposition.
    assert r.adapter.reconcile(r.source, action) == "verified"
    assert r.adapter.reconcile(r.source, action) == "verified"
    different = dict(action, ActionID=str(uuid4()))
    assert r.adapter.reconcile(r.source, different) == "not_applied"


@pytest.mark.parametrize(
    "change", ["version", "queued", "corrupt_spool", "typed", "generation", "held"]
)
def test_changed_or_conflicting_evidence_never_retires(historical, change):
    r = historical
    evidence, token, _ = r.adapter.inspect(r.source)
    assert ACTION in evidence["actions"]
    prep = r.outcomes.inspect(r.source)["preparation"]
    if change == "version":
        r.owner.execute(
            r.rewrite("UPDATE dbo.ExportPreparation SET Version=Version+1 WHERE PreparationID=?"),
            r.source,
        )
    elif change == "queued":
        r.runtime.enqueue_snapshot(r.source)
    elif change == "corrupt_spool":
        (r.runtime.store.root / prep["SpoolKey"]).write_bytes(b"corrupt")
    elif change == "typed":
        doc = json.loads(prep["RequestJson"])
        doc["request"]["producer"] = dict(kind="stats_import")
        r.owner.execute(
            r.rewrite("UPDATE dbo.ExportPreparation SET RequestJson=? WHERE PreparationID=?"),
            json.dumps(doc),
            r.source,
        )
    elif change == "generation":
        doc = json.loads(prep["GenerationJson"])
        doc["producer"]["completed_filename"] = "stats_" + "b" * 32 + ".ready.csv"
        r.owner.execute(
            r.rewrite("UPDATE dbo.ExportPreparation SET GenerationJson=? WHERE PreparationID=?"),
            json.dumps(doc),
            r.source,
        )
    else:
        r.owner.execute(
            r.rewrite(
                "UPDATE dbo.ExportResource SET ActivePreparationID=?,OwnerID=?,Fence=? WHERE ResourceKey='sql_snapshot:legacy_outputs'"
            ),
            r.source,
            prep["OwnerID"],
            prep["Fence"],
        )
    with pytest.raises((SourceConflict, ValueError)):
        r.adapter.execute(
            r.source, ACTION, token, "recovery:" + str(uuid4()), "Old export is obsolete"
        )
    assert "historical_disposition" not in json.loads(
        r.outcomes.inspect(r.source)["preparation"]["GenerationJson"]
    )


def test_live_producer_guard_prevents_retirement(historical):
    r = historical
    _, token, _ = r.adapter.inspect(r.source)
    guard = r.connect()
    guard.autocommit = True
    try:
        guard.cursor().execute(
            "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=?,@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0; SELECT @r",
            "k98-legacy-output-snapshot",
        )
        with pytest.raises(SourceConflict, match="active"):
            r.adapter.execute(
                r.source, ACTION, token, "recovery:" + str(uuid4()), "Old export is obsolete"
            )
    finally:
        guard.cursor().execute(
            "EXEC sys.sp_releaseapplock @Resource=?,@LockOwner='Session'",
            "k98-legacy-output-snapshot",
        )
        guard.close()
