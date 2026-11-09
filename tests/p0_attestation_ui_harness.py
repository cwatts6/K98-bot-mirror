"""Actual Discord preview/confirmation callbacks around temporary SQL recovery."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

from tests.test_guided_recovery import ACTOR


async def confirm_through_view(monkeypatch, service, incident, action):
    from ui.views import recovery_view as view

    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))

    async def call(method, *args):
        return getattr(service, method)(*args)

    monkeypatch.setattr(view, "call", call)
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    button = next(
        b
        for b in view.RecoveryIncidentView(incident).children
        if b.label == incident["evidence"]["actions"][action]["label"]
    )
    await button.callback(interaction)
    preview = interaction.followup.send.call_args.kwargs
    assert preview["ephemeral"] is True
    assert isinstance(preview["view"], view.RecoveryConfirmView)
    assert not service.store.actions
    await preview["view"].children[0].callback(interaction)
    current = service.review(ACTOR, incident["IncidentID"])
    assert current["State"] == "resolved"
    # A recreated confirmation cannot dispatch a second repair.
    await view.RecoveryConfirmView(incident, action).children[0].callback(interaction)
    assert len(service.store.actions) == 1
    return current
