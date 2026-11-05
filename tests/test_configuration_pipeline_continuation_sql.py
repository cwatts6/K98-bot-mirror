"""Real SQL receipts and production action policy for unfinished configuration."""

import json
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.configuration_continuation import PIPELINE_ACTION
from services.producer_recovery_intent import configuration_import_intent, current_intent
from services.recovery_release_policy import p0a_presentation
from tests.test_configuration_continuation_sql import commit_child, run, setup
from tests.test_configuration_read_continuation_sql import setup as read_setup
from tests.test_guided_recovery import ACTOR
from tests.test_import_capture_recovery_sql import recovery as recovery

pytestmark = [
    pytest.mark.skipif(
        os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Disposable SQL opt-in required"
    ),
    pytest.mark.parametrize("recovery", ["configuration_continuation"], indirect=True),
]


def pipeline_setup(r, runner, read):
    if read:
        return read_setup(r, runner, disposition="pipeline_export_v1")
    prep = r.outcomes.inspect(r.source)["preparation"]
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
    adapter, service = setup(r, runner)
    service.presentation_policy = p0a_presentation
    return r.source, adapter, service


@pytest.mark.parametrize("read", [False, True])
@pytest.mark.parametrize("choice", [PIPELINE_ACTION, "retry_configuration"])
def test_pipeline_follows_only_the_saved_configuration_successor(recovery, read, choice):
    from services.processing_pipeline_receipt_dal import PipelineReceiptDAL
    from services.processing_pipeline_receipts import producer_evidence

    r = recovery
    generation = json.loads(r.outcomes.inspect(r.source)["preparation"]["GenerationJson"])

    @configuration_import_intent
    def runner():
        return commit_child(r, generation)

    source, adapter, service = pipeline_setup(r, runner, read)
    state = adapter.dal.snapshot(source)
    inner = json.loads(state["root"]["RequestJson"])["request"]
    original_operation = (inner["configuration_import"]["producer"] if read else inner["producer"])[
        "operation"
    ]
    row = service.review_source(ACTOR, adapter.kind, source)
    run(service, row, choice)
    expected = adapter.dal.snapshot(source)["child"]
    pipeline = PipelineReceiptDAL(r.runtime)
    actual = pipeline.configuration_result(original_operation)
    assert actual["PreparationID"] == expected["PreparationID"]
    proof, verified = producer_evidence(pipeline, "configuration", original_operation)
    assert verified and proof["preparation_id"] == expected["PreparationID"]
    assert json.loads(actual["RequestJson"])["request"]["producer"]["export_disposition"] == (
        "pipeline_export_v1" if choice == PIPELINE_ACTION else "configuration_only_v1"
    )


@pytest.mark.parametrize("read", [False, True])
@pytest.mark.parametrize("lost_reply", [False, True])
def test_pipeline_configuration_commit_capture_and_queue_survive_restart(
    recovery, read, lost_reply
):
    r = recovery
    generation = json.loads(r.outcomes.inspect(r.source)["preparation"]["GenerationJson"])
    calls = []

    @configuration_import_intent
    def runner():
        calls.append(dict(current_intent()))
        return commit_child(r, generation, lost_reply=lost_reply)

    source, adapter, service = pipeline_setup(r, runner, read)
    row = service.review_source(ACTOR, adapter.kind, source)
    assert PIPELINE_ACTION in row["evidence"]["actions"]
    final = run(service, row, PIPELINE_ACTION)
    assert len(calls) == 1
    assert calls[0]["export_disposition"] == "pipeline_export_v1"
    assert final["State"] == "open"
    child = adapter.dal.snapshot(source)["child"]
    identifier = child["PreparationID"]
    assert not r.outcomes.inspect(identifier)["execution"]
    restarted = type(adapter)(
        adapter.dal, adapter.producer, Mock(side_effect=AssertionError("No producer replay"))
    )
    service.adapters[adapter.kind] = restarted
    service.refresh(row["IncidentID"])
    evidence, token, resolved = adapter.producer.inspect(identifier)
    assert not resolved
    r.state.fail = "queue"
    actor = "recovery:" + str(uuid4())
    with pytest.raises(TimeoutError, match="queue acknowledgement"):
        adapter.producer.execute(
            identifier, "resume_capture", token, actor, "Retain output and queue once"
        )
    first_job = r.outcomes.inspect(identifier)["preparation"]["JobID"]
    assert first_job
    assert service.refresh(row["IncidentID"])["State"] == "resolved"
    run(service, row, PIPELINE_ACTION)
    assert r.outcomes.inspect(identifier)["preparation"]["JobID"] == first_job
    assert len(calls) == 1
    restarted.runner.assert_not_called()


@pytest.mark.parametrize("read", [False, True])
def test_lost_dispatch_and_failed_attempt_require_new_confirmation(recovery, read):
    calls = []
    source, adapter, service = pipeline_setup(recovery, lambda: calls.append(1), read)
    row = service.review_source(ACTOR, adapter.kind, source)
    service.store.claim(
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        PIPELINE_ACTION,
        "discord:1",
        "Confirmed",
    )
    refreshed = service.refresh(row["IncidentID"])
    state = adapter.dal.snapshot(source)
    assert state["marker"]["export_disposition"] == "pipeline_export_v1"
    assert state["child"]["State"] == "unavailable"
    assert not recovery.outcomes.inspect(state["child"]["PreparationID"])["resources"]
    assert refreshed["State"] == "open"
    assert calls == []
    run(service, refreshed, PIPELINE_ACTION)
    assert calls == [1]
    assert service.refresh(row["IncidentID"])["State"] == "open"


@pytest.mark.parametrize("read", [False, True])
def test_changed_config_or_live_dispatch_cannot_continue(recovery, read):
    calls = []
    source, adapter, service = pipeline_setup(recovery, lambda: calls.append(1), read)
    row = service.review_source(ACTOR, adapter.kind, source)
    with adapter.dal.serialized(source):
        with pytest.raises(SourceConflict):
            run(service, row, PIPELINE_ACTION)
    config = json.loads(recovery.runtime.configuration)
    config["scan_data"]["destinations"] = ["changed"]
    recovery.runtime.configuration = json.dumps(config)
    with pytest.raises(SourceConflict):
        adapter.execute(
            source, PIPELINE_ACTION, row["EvidenceHash"], "recovery:" + str(uuid4()), "Stale"
        )
    assert calls == []


@pytest.mark.parametrize("read", [False, True])
@pytest.mark.asyncio
async def test_pipeline_button_reviews_every_page_then_confirms(recovery, monkeypatch, read):
    from services.recovery_service import RecoveryActor
    from ui.views import recovery_review_view as review, recovery_view as view

    calls = []
    source, adapter, service = pipeline_setup(recovery, lambda: calls.append(1), read)
    row = service.review_source(ACTOR, adapter.kind, source)
    with pytest.raises(SourceConflict):
        service.execute(
            RecoveryActor(9, 2, 3),
            row["IncidentID"],
            row["Revision"],
            row["EvidenceHash"],
            PIPELINE_ACTION,
            "Unauthorised",
        )

    async def call(method, *args):
        return getattr(service, method)(*args)

    for module in (view, review):
        monkeypatch.setattr(module, "call", call)
        monkeypatch.setattr(module, "actor_for", lambda _: ACTOR)
        monkeypatch.setattr(module, "safe_defer", AsyncMock(return_value=True))
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    await next(
        b
        for b in view.RecoveryIncidentView(row).children
        if b.label == "Continue config for export"
    ).callback(interaction)
    pages = 0
    while True:
        pages += 1
        current = interaction.followup.send.call_args.kwargs["view"]
        assert not calls
        forward = next(b for b in current.children if b.label == "Next checks")
        confirm = next(b for b in current.children if b.label == "Continue to confirmation")
        if forward.disabled:
            assert not confirm.disabled
            await confirm.callback(interaction)
            break
        assert confirm.disabled
        await forward.callback(interaction)
    assert pages > 1 and not calls
    confirmation = interaction.followup.send.call_args.kwargs["view"]
    await next(b for b in confirmation.children if b.label.startswith("Confirm")).callback(
        interaction
    )
    assert calls == [1]
    assert service.store.actions[0]["State"] == "not_applied"


@pytest.mark.parametrize("read", [False, True])
def test_pipeline_blocker_navigation_returns_to_original_choice(recovery, read):
    source, adapter, service = pipeline_setup(recovery, lambda: None, read)
    reader = recovery.runtime.dal.request(
        account="a",
        consumer="config",
        kvk_no=None,
        request={"read_configuration": str(uuid4())},
        storage_owner="disk-a",
        actor="test",
        reason="Other owner",
    )
    claim = recovery.runtime.dal.claim(
        reader, account="a", storage_owner="disk-a", stage="preflight", resource_keys=("account:a",)
    )
    row = service.review_source(ACTOR, adapter.kind, source)
    assert PIPELINE_ACTION not in row["evidence"]["actions"]
    assert row["evidence"]["recovery_links"][0]["source_id"] == reader
    recovery.runtime.dal.transition(claim, expected="preflight", state="completed", release=True)
    assert PIPELINE_ACTION in service.refresh(row["IncidentID"])["evidence"]["actions"]
