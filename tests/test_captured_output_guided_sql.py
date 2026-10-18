"""Actual private buttons, retained files, SQL queue/disposition and durable receipts."""

import json
import os
from types import MethodType, SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services.export_coordination_dal import ExportCoordinationDAL
from services.import_recovery_service import ImportRecoveryAdapter
from services.legacy_export_snapshot_service import LegacyExportRuntime
from services.player_report_recovery_service import PlayerReportRecoveryAdapter
from services.recovery_release_policy import p0a_presentation
from services.recovery_service import RecoveryActor, RecoveryService, SourceConflict
from tests.test_guided_recovery import ACTOR
from tests.test_import_capture_recovery_sql import recovery as recovery
from tests.test_recovery_sql import store as store

pytestmark = [
    pytest.mark.skipif(
        os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Disposable SQL opt-in"
    ),
    pytest.mark.parametrize("recovery", ["scan_data", "player_report"], indirect=True),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("action", ["queue_capture", "abandon_capture"])
@pytest.mark.parametrize("lost_reply", [False, True])
async def test_review_confirm_verify_retained_output(
    recovery, store, monkeypatch, action, lost_reply
):
    from ui.views import recovery_review_view as review, recovery_view as view

    r = recovery
    before = r.outcomes.inspect(r.source)
    if before["execution"]:
        generation = r.service.generation(before["preparation"], before["execution"])
        generation["producer"] = dict(
            procedure="dbo.UPDATE_ALL2",
            completed_filename=before["execution"]["CompletedFileName"],
            phases=[],
        )
        r.owner.execute(
            r.rewrite("UPDATE dbo.ExportPreparation SET GenerationJson=? WHERE PreparationID=?"),
            json.dumps(generation),
            r.source,
        )
    monkeypatch.setattr(
        r.runtime,
        "enqueue_snapshot",
        lambda *_: (_ for _ in ()).throw(TimeoutError("queue not yet called")),
    )
    with pytest.raises(TimeoutError):
        r.service.run(r.source, r.outcomes.inspect(r.source)["token"], "original_capture")
    captured = r.outcomes.inspect(r.source)
    assert captured["captured"] and not captured["preparation"]["JobID"]
    r.runtime.account = "a"
    r.runtime.coordinator = ExportCoordinationDAL(r.connect, preparations=True)
    r.runtime.verified_snapshot = MethodType(LegacyExportRuntime.verified_snapshot, r.runtime)
    r.runtime.enqueue_snapshot = MethodType(LegacyExportRuntime.enqueue_snapshot, r.runtime)
    adapter_type = ImportRecoveryAdapter if before["execution"] else PlayerReportRecoveryAdapter
    adapter = adapter_type(r.outcomes, r.service)
    service = RecoveryService(
        store,
        {adapter.kind: adapter},
        admin_id=1,
        guild_id=2,
        channel_id=3,
        presentation_policy=p0a_presentation,
    )
    row = service.review_source(ACTOR, adapter.kind, r.source)
    assert set(row["evidence"]["actions"]) == {"queue_capture", "abandon_capture"}
    for actor in (RecoveryActor(9, 2, 3), RecoveryActor(1, 9, 3), RecoveryActor(1, 2, 9)):
        with pytest.raises(SourceConflict):
            service.review_details_page(
                actor, row["IncidentID"], action, row["Revision"], row["EvidenceHash"]
            )

    async def call(name, *args):
        return getattr(service, name)(*args)

    for module in (view, review):
        monkeypatch.setattr(module, "actor_for", lambda _: ACTOR)
        monkeypatch.setattr(module, "safe_defer", AsyncMock(return_value=True))
        monkeypatch.setattr(module, "call", call)
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    button = next(
        b
        for b in view.RecoveryIncidentView(row).children
        if b.label == row["evidence"]["actions"][action]["label"]
    )
    await button.callback(interaction)
    checked_labels = []
    while True:
        payload = interaction.followup.send.call_args.kwargs
        assert payload["ephemeral"]
        checked_labels.extend(f.name for f in payload["embed"].fields)
        page = payload["view"]
        if page.next.disabled:
            break
        assert page.confirm.disabled
        await page.next.callback(interaction)
    assert "Original failure evidence" in checked_labels
    assert "Original destination 1" in checked_labels
    assert "Current destination 1" in checked_labels
    assert r.outcomes.inspect(r.source)["preparation"] == captured["preparation"]
    assert not store.pending_actions(row["IncidentID"])
    await page.confirm.callback(interaction)
    confirm = interaction.followup.send.call_args.kwargs["view"]
    original = adapter.execute
    executions = []

    def execute(*args):
        executions.append(args)
        original(*args)
        if lost_reply:
            raise TimeoutError("domain commit acknowledged late")

    monkeypatch.setattr(adapter, "execute", execute)
    await confirm.confirm.callback(interaction)
    restarted = RecoveryService(
        store,
        {adapter.kind: adapter_type(r.outcomes, type(r.service)(r.runtime, r.outcomes))},
        admin_id=1,
        guild_id=2,
        channel_id=3,
        presentation_policy=p0a_presentation,
    )
    final = restarted.review(ACTOR, row["IncidentID"])
    assert final["State"] == "resolved" and not final["pending_action"]
    await confirm.confirm.callback(interaction)
    assert len(executions) == 1
    after = r.outcomes.inspect(r.source)
    assert after["execution"] == captured["execution"]
    assert not after["resources"]
    for key in ("SpoolKey", "SpoolHash", "SpoolBytes", "RequestJson", "OwnerID", "Fence"):
        assert after["preparation"][key] == captured["preparation"][key]
    assert r.owner.execute(r.rewrite("SELECT COUNT(*) FROM dbo.ExportJob")).fetchval() == int(
        action == "queue_capture"
    )
    if action == "queue_capture":
        job = r.owner.execute(
            r.rewrite(
                "SELECT EnqueueSequence,SpoolHash FROM dbo.ExportPreparation WHERE PreparationID=?"
            ),
            r.source,
        ).fetchone()
        assert job[0] == captured["preparation"]["EnqueueSequence"]
        assert r.runtime.enqueue_snapshot(r.source) == str(after["preparation"]["JobID"]).lower()
    else:
        assert final["evidence"]["outcome"] == "export_skipped"
        context = final["evidence"]["failure_context"]
        assert context["current_blocker"] is None
        assert "skip this export" in context["summary"]
        assert context["original_fault"] == "not_recorded"
