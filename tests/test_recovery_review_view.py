"""Complete private review pages, current authorization and stale confirmation rejection."""

from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.producer_refusal_recovery import ProducerRefusalRecovery
from services.recovery_service import RecoveryActor, RecoveryService
from tests.test_guided_recovery import ACTOR, Store


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["user", "guild_id", "channel_id"])
async def test_closed_configuration_handoff_keeps_private_authorization(monkeypatch, field):
    import bot_config
    from ui.views import recovery_view as view

    for key, value in (("ADMIN_USER_ID", 1), ("GUILD_ID", 2), ("NOTIFY_CHANNEL_ID", 3)):
        monkeypatch.setattr(bot_config, key, value)
    call = AsyncMock()
    error = AsyncMock()
    monkeypatch.setattr(view, "call", call)
    monkeypatch.setattr(view, "report_error", error)
    row = dict(
        State="resolved",
        evidence=dict(
            actions={},
            recovery_links=[
                dict(
                    label="Continue configuration",
                    kind="configuration_continuation",
                    source_id="root",
                ),
                dict(label="Old export", kind="export_job", source_id="old"),
            ],
        ),
    )
    incident = view.RecoveryIncidentView(row)
    assert [b.label for b in incident.children] == ["Recheck", "Continue configuration"]
    interaction = SimpleNamespace(user=SimpleNamespace(id=1), guild_id=2, channel_id=3)
    setattr(interaction, field, SimpleNamespace(id=9) if field == "user" else 9)
    await next(b for b in incident.children if b.label == "Continue configuration").callback(
        interaction
    )
    call.assert_not_called()
    assert isinstance(error.call_args.args[1], SourceConflict)


def review_fixture():
    original = dict(consumer="scan_data", outputs=["old-output"], destinations=["original-file"])
    state = dict(
        attempts=[],
        attempt_count=0,
        original_phase="refused",
        blockers=[],
        preparation=dict(RequestJson=json.dumps(dict(request=dict(config=original)))),
        current_registration=dict(
            consumer="scan_data",
            outputs=["current-output"],
            destinations=[f"current-file-{i}" for i in range(37)],
        ),
        producer=dict(
            inputs=dict(
                completed_filename="scan.ready.csv",
                rank="A",
                seed=2,
                metadata=dict(source_filename="scan.xlsx", columns_present=["x"] * 900),
            )
        ),
    )
    dal = Mock()
    dal.snapshot.side_effect = lambda *_: deepcopy(state)
    adapter = ProducerRefusalRecovery(dal, Mock())
    service = RecoveryService(
        Store(), {adapter.kind: adapter}, admin_id=1, guild_id=2, channel_id=3
    )
    row = service.review_source(ACTOR, adapter.kind, "original")
    return service, row, state, dal


def page(service, row, number=0, actor=ACTOR):
    return service.review_details_page(
        actor,
        row["IncidentID"],
        "resume_current_registration",
        row["Revision"],
        row["EvidenceHash"],
        number,
    )


def test_complete_pages_survive_restart_without_public_alert_disclosure():
    service, row, state, _ = review_fixture()
    first = page(service, row)
    assert first["pages"] > 8
    restarted = RecoveryService(
        service.store, service.adapters, admin_id=1, guild_id=2, channel_id=3
    )
    fields = [field for n in range(first["pages"]) for field in page(restarted, row, n)["fields"]]
    assert [f["file_id"] for f in fields if "file_id" in f] == [
        "original-file",
        *state["current_registration"]["destinations"],
    ]
    retained = "".join(f["text"] for f in fields if f["label"].startswith("Retained scan inputs"))
    assert json.loads(retained) == state["producer"]["inputs"]
    assert all(len(f.get("text", "")) <= 400 for f in fields)
    alert = json.dumps(row["evidence"])
    assert "scan.xlsx" not in alert and "current-file-" not in alert


@pytest.mark.parametrize(
    "actor", [RecoveryActor(9, 2, 3), RecoveryActor(1, 9, 3), RecoveryActor(1, 2, 9)]
)
def test_review_rechecks_actor_before_private_reads(actor):
    service, row, _, dal = review_fixture()
    dal.snapshot.reset_mock()
    with pytest.raises(SourceConflict):
        page(service, row, actor=actor)
    dal.snapshot.assert_not_called()


def test_changed_registration_invalidates_every_saved_page():
    service, row, state, _ = review_fixture()
    state["current_registration"]["destinations"].append("later-output")
    with pytest.raises(SourceConflict, match="changed"):
        page(service, row)


@pytest.mark.parametrize("number", [-1, True, 99999])
def test_invalid_pages_do_not_hide_or_wrap_checks(number):
    service, row, _, _ = review_fixture()
    with pytest.raises(SourceConflict):
        page(service, row, number)


@pytest.mark.asyncio
async def test_actual_button_pages_lead_to_separate_confirmation(monkeypatch):
    from ui.views import recovery_review_view as pages, recovery_view as view

    service, row, _, _ = review_fixture()

    async def call(method, *args):
        return getattr(service, method)(*args)

    for module in (view, pages):
        monkeypatch.setattr(module, "actor_for", lambda _: ACTOR)
        monkeypatch.setattr(module, "safe_defer", AsyncMock(return_value=True))
        monkeypatch.setattr(module, "call", call)
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    button = next(
        b
        for b in view.RecoveryIncidentView(row).children
        if b.label == "Continue with current destinations"
    )
    await button.callback(interaction)
    result = interaction.followup.send.call_args.kwargs
    assert result["ephemeral"] and isinstance(result["view"], pages.RecoveryReviewView)
    while not result["view"].next.disabled:
        assert result["view"].confirm.disabled
        assert all(len(f.value) <= 1024 for f in result["embed"].fields)
        await result["view"].next.callback(interaction)
        result = interaction.followup.send.call_args.kwargs
        assert result["ephemeral"]
    assert not service.store.actions
    await result["view"].confirm.callback(interaction)
    confirmation = interaction.followup.send.call_args.kwargs
    assert confirmation["ephemeral"] and isinstance(confirmation["view"], view.RecoveryConfirmView)
    assert confirmation["view"].action == "resume_current_registration"
    assert not service.store.actions


@pytest.mark.asyncio
async def test_saved_last_page_cannot_confirm_after_registration_change(monkeypatch):
    from ui.views import recovery_review_view as pages

    service, row, state, _ = review_fixture()
    initial = page(service, row)
    last = page(service, row, initial["pages"] - 1)
    state["current_registration"]["outputs"] = ["changed-later"]

    async def call(method, *args):
        return getattr(service, method)(*args)

    monkeypatch.setattr(pages, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(pages, "safe_defer", AsyncMock(return_value=True))
    monkeypatch.setattr(pages, "call", call)
    monkeypatch.setattr(pages, "report_error", AsyncMock())
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    await pages.RecoveryReviewView(last).confirm.callback(interaction)
    interaction.followup.send.assert_not_called()
    pages.report_error.assert_awaited_once()
    assert not service.store.actions
