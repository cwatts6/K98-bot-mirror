"""Disposable SQL and production policy for fresh report/cache decisions."""

import json
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.player_report_continuation import PlayerReportContinuation
from services.player_report_continuation_dal import PlayerReportContinuationDAL
from services.player_report_recovery_service import PlayerReportRecoveryAdapter
from services.producer_recovery_intent import current_intent
from services.recovery_release_policy import p0a_presentation
from services.recovery_service import RecoveryActor, RecoveryService
from tests.test_configuration_continuation_sql import commit_child
from tests.test_guided_recovery import ACTOR, Store
from tests.test_import_capture_recovery_sql import recovery as recovery
from tests.test_player_report_recovery_sql import uncommitted

pytestmark = [
    pytest.mark.skipif(
        os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Disposable SQL opt-in required"
    ),
    pytest.mark.parametrize("recovery", ["player_report_continuation"], indirect=True),
]


def setup(r, runner=None, cache=None):
    preview, _ = uncommitted(r)
    request = json.loads(preview["preparation"]["RequestJson"])
    request["request"]["producer"]["export_disposition"] = "cache_only_v1"
    r.owner.execute(
        r.rewrite(
            "UPDATE dbo.ExportPreparation SET RequestJson=?,RequestHash=? WHERE PreparationID=?"
        ),
        json.dumps(request),
        digest(request),
        r.source,
    )
    preview = r.outcomes.inspect(r.source)
    r.outcomes.cancel(r.source, preview["token"], "admin", "Verified rollback")
    r.runtime.account = "a"
    producer = PlayerReportRecoveryAdapter(r.outcomes, r.service)
    adapter = PlayerReportContinuation(
        PlayerReportContinuationDAL(r.runtime, r.outcomes),
        producer,
        runner=runner or Mock(),
        cache_runner=cache or Mock(),
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
    return adapter, service, row


def run(service, row, kind):
    return service.execute(
        ACTOR,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        kind,
        "Admin reviewed existing scans and current report settings",
    )


def test_keep_prior_has_separate_verified_decision_without_dispatch(recovery):
    adapter, service, row = setup(recovery)
    assert set(row["evidence"]["actions"]) == {"refresh_report", "keep_prior"}
    result = run(service, row, "keep_prior")
    assert result["State"] == "resolved"
    assert result["evidence"]["outcome"] == "prior_report_retained"
    assert recovery.source not in adapter.pending_recovery()
    adapter.runner.assert_not_called()
    adapter.cache_runner.assert_not_called()


def test_lost_report_dispatch_is_fenced_without_replaying(recovery):
    adapter, service, row = setup(recovery)
    action_id, _ = service.store.claim(
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "refresh_report",
        "discord:1",
        "Confirmed",
    )
    result = service.refresh(row["IncidentID"])
    assert "refresh_report" in result["evidence"]["actions"]
    assert service.store.actions[0]["State"] == "not_applied"
    assert adapter.dal.snapshot(recovery.source)["child"]["State"] == "unavailable"
    adapter.runner.assert_not_called()
    with pytest.raises(SourceConflict):
        adapter.execute(
            recovery.source,
            "refresh_report",
            row["EvidenceHash"],
            "recovery:" + action_id,
            "Late callback",
        )


def test_stale_registration_and_unauthorized_admin_cannot_refresh(recovery):
    adapter, service, row = setup(recovery)
    with pytest.raises(SourceConflict):
        service.execute(
            RecoveryActor(99, 2, 3),
            row["IncidentID"],
            row["Revision"],
            row["EvidenceHash"],
            "refresh_report",
            "No",
        )
    config = json.loads(recovery.runtime.configuration)
    config["scan_data"]["destinations"] = ["changed"]
    recovery.runtime.configuration = json.dumps(config)
    with pytest.raises(SourceConflict):
        run(service, row, "refresh_report")
    adapter.runner.assert_not_called()


@pytest.mark.parametrize("lost_reply", [False, True])
def test_fresh_report_then_cache_no_sql_replay_across_restart(recovery, lost_reply):
    r = recovery
    generation = json.loads(r.outcomes.inspect(r.source)["preparation"]["GenerationJson"])
    calls = []

    def runner():
        calls.append(dict(current_intent()))
        commit_child(r, generation, lost_reply=lost_reply)

    receipt = dict(
        sha256="a" * 64,
        verified_utc="2026-10-20T13:00:00+00:00",
        source_last_refresh="2026-09-29T14:44:00",
        source_kvk_no=16,
        source_row_count=415,
    )
    cache = Mock(return_value=receipt)
    adapter, service, row = setup(r, runner, cache)
    result = run(service, row, "refresh_report")
    assert len(calls) == 1 and calls[0]["export_disposition"] == "cache_only_v1"
    assert calls[0]["parent"] == r.source
    assert result["State"] == "open" and not result["evidence"]["actions"]
    child = adapter.dal.snapshot(r.source)["child"]["PreparationID"]
    preview, token, _ = adapter.producer.inspect(child)
    assert "resume_capture" in preview["actions"]
    adapter.producer.execute(child, "resume_capture", token, "recovery:" + str(uuid4()), "Capture")
    preview, token, _ = adapter.producer.inspect(child)
    adapter.producer.execute(
        child, "complete_cache_only", token, "recovery:" + str(uuid4()), "Verify no-export intent"
    )
    result = service.refresh(row["IncidentID"])
    assert set(result["evidence"]["actions"]) == {"refresh_cache"}
    adapter = PlayerReportContinuation(
        adapter.dal, adapter.producer, runner=runner, cache_runner=cache
    )
    service.adapters[adapter.kind] = adapter
    result = run(service, result, "refresh_cache")
    assert result["State"] == "resolved"
    assert result["evidence"]["cache_receipt"]["source_row_count"] == 415
    assert len(calls) == 1
    service.refresh(row["IncidentID"])
    cache.assert_called_once()
    assert r.source not in adapter.pending_recovery()


@pytest.mark.asyncio
async def test_actual_admin_confirmation_is_one_concise_decision(recovery, monkeypatch):
    from ui.views import recovery_view as view

    adapter, service, row = setup(recovery)

    async def call(method, *args):
        return getattr(service, method)(*args)

    monkeypatch.setattr(view, "call", call)
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    button = next(
        b
        for b in view.RecoveryIncidentView(row).children
        if b.label == "Keep prior report and cache"
    )
    await button.callback(interaction)
    assert not service.store.actions
    confirmation = interaction.followup.send.call_args.kwargs["view"]
    await next(b for b in confirmation.children if b.label.startswith("Confirm")).callback(
        interaction
    )
    assert service.refresh(row["IncidentID"])["State"] == "resolved"
    adapter.runner.assert_not_called()
