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
