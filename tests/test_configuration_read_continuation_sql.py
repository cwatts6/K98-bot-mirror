"""Real SQL and guided decisions for configuration admission refusals, without provider calls."""

import json
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.configuration_read_continuation import ConfigurationReadContinuation
from services.configuration_read_continuation_dal import ConfigurationReadContinuationDAL
from services.producer_recovery_intent import current_intent
from services.recovery_release_policy import p0a_presentation
from tests.test_configuration_continuation_sql import commit_child, run, setup as prior_setup
from tests.test_guided_recovery import ACTOR
from tests.test_import_capture_recovery_sql import recovery as recovery

pytestmark = [
    pytest.mark.skipif(
        os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Disposable SQL opt-in required"
    ),
    pytest.mark.parametrize("recovery", ["configuration_continuation"], indirect=True),
]


def setup(r, runner=None, *, associated=True):
    prior, service = prior_setup(r)
    config = json.loads(r.runtime.configuration)
    request = dict(read_configuration=str(uuid4()))
    if associated:
        request["configuration_import"] = dict(
            producer=dict(kind="configuration_import", atomic_checkpoint=1, operation=str(uuid4())),
            sources=config["config"],
            outputs=config["scan_data"],
        )
    source = r.runtime.dal.request(
        account="a",
        consumer="config",
        kvk_no=None,
        request=request,
        storage_owner="disk-a",
        actor="system:configuration",
        reason="Read immutable configuration inputs",
    )
    r.runtime.dal.withdraw_unstarted(source)
    adapter = ConfigurationReadContinuation(
        ConfigurationReadContinuationDAL(r.runtime, r.outcomes),
        prior.producer,
        runner=runner or (lambda: None),
    )
    service.adapters[adapter.kind] = adapter
    service.presentation_policy = p0a_presentation
    return source, adapter, service


@pytest.mark.asyncio
async def test_private_review_keep_prior_and_complete_report(recovery, monkeypatch):
    from services.recovery_report import incident_report
    from ui.views import recovery_view as view

    source, adapter, service = setup(recovery)
    assert source in adapter.pending_recovery()
    row = service.review_source(ACTOR, adapter.kind, source)
    assert row["EvidenceHash"] == digest(adapter.dal.snapshot(source)).hex()
    assert set(row["evidence"]["actions"]) == {"retry_configuration", "keep_prior"}
    fields = adapter.review_details(source, "retry_configuration", row["EvidenceHash"])
    assert any(field.get("file_id") == "source_sheet" for field in fields)
    assert row["evidence"]["failure_context"]["original_read_id"] == source
    assert row["evidence"]["failure_context"]["sql_outcome"] == "not_started"
    original = recovery.runtime.dal.read(source)

    async def call(method, *args):
        return getattr(service, method)(*args)

    monkeypatch.setattr(view, "call", call)
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    await next(
        b for b in view.RecoveryIncidentView(row).children if b.label == "Keep prior configuration"
    ).callback(interaction)
    confirmation = interaction.followup.send.call_args.kwargs["view"]
    assert not service.store.actions
    await next(b for b in confirmation.children if b.label.startswith("Confirm")).callback(
        interaction
    )
    final = service.refresh(row["IncidentID"])
    assert final["State"] == "resolved" and not final["pending_action"]
    assert service.store.actions[0]["State"] == "verified"
    assert source not in adapter.pending_recovery()
    changed = recovery.runtime.dal.read(source)
    for key in ("RequestJson", "RequestHash", "OwnerID", "Fence", "State"):
        assert changed[key] == original[key]
    report = incident_report(service, final)
    assert report["diagnosis"]["outcome"] == "prior_configuration_retained"
    assert report["diagnosis"]["failure_context"]["original_read_id"] == source


def test_lost_dispatch_reconciles_without_rerunning_and_new_decision_is_fresh(recovery):
    calls = []

    def runner():
        calls.append(dict(current_intent()))
        raise TimeoutError("fresh read refused")

    source, adapter, service = setup(recovery, runner)
    row = service.review_source(ACTOR, adapter.kind, source)
    final = run(service, row, "retry_configuration")
    assert len(calls) == 1 and calls[0]["parent"] == source
    assert final["State"] == "open" and not final["pending_action"]
    service.adapters[adapter.kind] = ConfigurationReadContinuation(
        adapter.dal, adapter.producer, runner
    )
    final = service.refresh(row["IncidentID"])
    assert len(calls) == 1
    run(service, final, "retry_configuration")
    assert len(calls) == 2 and calls[0]["operation"] != calls[1]["operation"]


def test_confirmed_keep_prior_reconciles_after_restart_and_rejects_late_callback(recovery):
    source, adapter, service = setup(recovery)
    row = service.review_source(ACTOR, adapter.kind, source)
    action, _ = service.store.claim(
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "keep_prior",
        "discord:1",
        "Confirmed",
    )
    final = service.refresh(row["IncidentID"])
    assert final["State"] == "resolved"
    assert adapter.dal.snapshot(source)["child"] is None
    with pytest.raises(SourceConflict):
        adapter.execute(
            source, "keep_prior", row["EvidenceHash"], "recovery:" + action, "Late callback"
        )


@pytest.mark.parametrize(
    "change", ["hash", "scope", "fence", "membership", "typed_parent", "unknown_origin"]
)
def test_uncertain_or_unassociated_reads_cannot_be_adopted(recovery, change):
    r = recovery
    source, adapter, service = setup(r, associated=change != "unknown_origin")
    connection = r.connect()
    cursor = connection.cursor()
    if change == "hash":
        cursor.execute(
            "UPDATE dbo.ExportPreparation SET RequestHash=? WHERE PreparationID=?",
            b"x" * 32,
            source,
        )
    elif change == "scope":
        adapter.dal.storage_owner = "other-disk"
    elif change == "fence":
        cursor.execute("UPDATE dbo.ExportPreparation SET Fence=2 WHERE PreparationID=?", source)
    elif change == "membership":
        cursor.execute(
            "INSERT dbo.ExportPreparationResource(PreparationID,ResourceKey) VALUES (?,?)",
            source,
            "account:a",
        )
    elif change == "typed_parent":
        document = json.loads(r.runtime.dal.read(source)["RequestJson"])
        document["request"]["configuration_import"]["producer"]["parent"] = str(uuid4())
        cursor.execute(
            "UPDATE dbo.ExportPreparation SET RequestJson=?,RequestHash=? WHERE PreparationID=?",
            json.dumps(document),
            digest(document),
            source,
        )
    connection.commit()
    connection.close()
    with pytest.raises(SourceConflict):
        adapter.inspect(source)
    if change == "unknown_origin":
        assert source not in adapter.pending_recovery()


def test_stale_registration_and_wrong_admin_are_refused(recovery):
    from services.recovery_service import RecoveryActor

    calls = []
    source, adapter, service = setup(recovery, lambda: calls.append(1))
    row = service.review_source(ACTOR, adapter.kind, source)
    with pytest.raises(SourceConflict):
        service.review_source(RecoveryActor(99, 2, 3), adapter.kind, source)
    config = json.loads(recovery.runtime.configuration)
    config["config"]["destinations"] = ["changed_source"]
    recovery.runtime.configuration = json.dumps(config)
    with pytest.raises(SourceConflict):
        run(service, row, "retry_configuration")
    assert calls == []


@pytest.mark.parametrize("lost_reply", [False, True])
def test_fresh_publication_and_capture_are_verified_without_replaying(recovery, lost_reply):
    r = recovery
    generation = json.loads(r.outcomes.inspect(r.source)["preparation"]["GenerationJson"])
    calls = []

    def runner():
        calls.append(1)
        return commit_child(r, generation, lost_reply=lost_reply)

    source, adapter, service = setup(r, runner)
    row = service.review_source(ACTOR, adapter.kind, source)
    final = run(service, row, "retry_configuration")
    assert calls == [1]
    assert service.store.actions[0]["State"] == "verified"
    assert final["State"] == "open" and not final["evidence"]["actions"]
    child = adapter.dal.snapshot(source)["child"]["PreparationID"]
    assert final["evidence"]["recovery_links"][0]["source_id"] == child
    result = adapter.producer.inspect(child)
    adapter.producer.execute(
        child, "resume_capture", result[1], "recovery:" + str(uuid4()), "Capture committed output"
    )
    assert service.refresh(row["IncidentID"])["State"] == "resolved"
    run(service, row, "retry_configuration")
    assert calls == [1]


def test_busy_account_links_exact_owner_and_restores_retry_after_release(recovery):
    r = recovery
    source, adapter, service = setup(r)
    reader = r.runtime.dal.request(
        account="a",
        consumer="config",
        kvk_no=None,
        request={"read_configuration": str(uuid4())},
        storage_owner="disk-a",
        actor="test",
        reason="Busy read",
    )
    claim = r.runtime.dal.claim(
        reader, account="a", storage_owner="disk-a", stage="preflight", resource_keys=("account:a",)
    )
    row = service.review_source(ACTOR, adapter.kind, source)
    assert set(row["evidence"]["actions"]) == {"keep_prior"}
    assert row["evidence"]["recovery_links"] == [
        dict(label="Review blocking operation", kind="configuration_read", source_id=reader)
    ]
    r.runtime.dal.transition(claim, expected="preflight", state="completed", release=True)
    assert "retry_configuration" in service.refresh(row["IncidentID"])["evidence"]["actions"]


@pytest.mark.asyncio
async def test_fresh_read_button_requires_all_pages_and_separate_confirmation(
    recovery, monkeypatch
):
    from tests import test_configuration_continuation_sql as existing

    def current_setup(r, runner):
        source, adapter, service = setup(r, runner)
        r.source = source
        return adapter, service

    monkeypatch.setattr(existing, "setup", current_setup)
    await existing.test_retry_button_requires_all_review_pages_and_separate_confirmation(
        recovery, monkeypatch
    )
