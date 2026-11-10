from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services.recovery_service import SourceConflict
from tests.test_guided_recovery import ACTOR
from ui.views import recovery_publication_view as view
from ui.views.recovery_view import RecoveryEntryView


@pytest.mark.asyncio
@pytest.mark.parametrize("denied", [False, True])
async def test_publication_list_is_private_and_authorizes_before_loading(monkeypatch, denied):
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))

    def actor(_):
        if denied:
            raise SourceConflict("Admin access revoked")
        return ACTOR

    monkeypatch.setattr(view, "actor_for", actor)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))
    monkeypatch.setattr(view, "call", AsyncMock(return_value=[]))
    monkeypatch.setattr(view, "report_error", AsyncMock())
    await view.show_publications(interaction)
    if denied:
        view.call.assert_not_called()
        interaction.followup.send.assert_not_called()
    else:
        view.call.assert_awaited_once_with("published_outputs", ACTOR, None)
        assert interaction.followup.send.call_args.kwargs["ephemeral"]


@pytest.mark.asyncio
async def test_entry_preserves_review_first_and_persistent_publication_route():
    entry = RecoveryEntryView()
    assert entry.children[0].label == "Review & fix"
    assert any(b.custom_id == "k98:recovery:publications:v1" for b in entry.children)


@pytest.mark.asyncio
async def test_confirmation_explains_wait_before_entering_long_check(monkeypatch):
    from tests.test_guided_recovery import setup
    from ui.views import recovery_view as module

    _, _, _, row = setup()
    row["SourceKind"] = "export_job"
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    monkeypatch.setattr(module, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(module, "safe_defer", AsyncMock(return_value=True))
    events = []

    async def send(*args, **kwargs):
        assert kwargs["ephemeral"] and not kwargs["allowed_mentions"].everyone
        events.append("progress" if args else "result")

    async def execute(*args):
        assert events == ["progress"]
        events.append("execute")
        return row

    interaction.followup.send.side_effect = send
    monkeypatch.setattr(module, "call", execute)
    confirmation = module.RecoveryConfirmView(row, "verify_publication")
    await confirmation.confirm.callback(interaction)
    assert events == ["progress", "execute", "result"]
    assert confirmation.confirm.disabled


@pytest.mark.asyncio
async def test_rejected_confirmation_never_announces_an_accepted_check(monkeypatch):
    from tests.test_guided_recovery import setup
    from ui.views import recovery_view as module

    _, _, _, row = setup()
    row["SourceKind"] = "export_job"
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    monkeypatch.setattr(module, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(module, "safe_defer", AsyncMock(return_value=True))
    monkeypatch.setattr(module, "call", AsyncMock(side_effect=SourceConflict("Stale confirmation")))
    monkeypatch.setattr(module, "report_error", AsyncMock())
    confirmation = module.RecoveryConfirmView(row, "verify_publication")
    await confirmation.confirm.callback(interaction)
    text = interaction.followup.send.call_args.args[0]
    assert "Acceptance is not yet established" in text
    assert "verification requested" not in text
    module.report_error.assert_awaited_once()
    assert not confirmation.confirm.disabled


def test_running_publication_embed_explains_elapsed_time_and_receipt_boundary():
    from tests.test_guided_recovery import setup
    from ui.views.recovery_view import incident_embed

    _, _, _, row = setup()
    row["pending_action"] = dict(kind="verify_publication", state="dispatched")
    row["execution_progress"] = dict(state="in_progress", elapsed_seconds=124)
    field = next(f for f in incident_embed(row).fields if f.name == "Publication check in progress")
    assert "124 seconds" in field.value and "final saved receipt" in field.value
