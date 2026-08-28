from __future__ import annotations

import inspect
from types import SimpleNamespace

import discord
import pytest

from ui.views import kvk_targets_views


async def _on_select(*_args):
    return None


def _option(governor_id: str = "2441482") -> discord.SelectOption:
    return discord.SelectOption(label="Governor", value=governor_id, description="Main")


@pytest.mark.asyncio
async def test_targets_view_keeps_controls_without_legacy_last_kvk_state():
    signature = inspect.signature(kvk_targets_views.make_kvk_targets_view)
    ctx = SimpleNamespace(user=SimpleNamespace(id=1))

    view = kvk_targets_views.make_kvk_targets_view(ctx, [_option()], _on_select)

    assert "last_kvk_map" not in signature.parameters
    assert not hasattr(view, "_last_kvk_map")
    assert isinstance(view.children[0], discord.ui.Select)
    assert view.children[0].placeholder == "Choose an account to view…"
    assert [child.label for child in view.children[1:]] == [
        "Look up Governor ID",
        "Register New Account",
        "Refresh",
    ]


@pytest.mark.asyncio
async def test_targets_view_refresh_rebuilds_equivalent_view(monkeypatch):
    async def fake_summary(_discord_id):
        from services.governor_account_service import summarize_accounts

        return summarize_accounts({"Main": {"GovernorID": "99", "GovernorName": "Refreshed"}})

    monkeypatch.setattr(
        "services.governor_account_service.get_account_summary_for_user",
        fake_summary,
    )

    class _Response:
        edited = None

        async def edit_message(self, **kwargs):
            self.edited = kwargs

    response = _Response()
    ctx = SimpleNamespace(user=SimpleNamespace(id=1))
    view = kvk_targets_views.make_kvk_targets_view(
        ctx,
        [_option()],
        _on_select,
        show_register_btn=False,
        ephemeral=False,
    )
    refresh = next(child for child in view.children if getattr(child, "label", None) == "Refresh")

    await refresh.callback(SimpleNamespace(response=response))

    refreshed = response.edited["view"]
    assert response.edited["content"] == "Select an account to view its KVK targets:"
    assert not hasattr(refreshed, "_last_kvk_map")
    assert refreshed.ephemeral is False
    assert refreshed.children[0].options[0].value == "99"
    assert [child.label for child in refreshed.children[1:]] == [
        "Look up Governor ID",
        "Refresh",
    ]


@pytest.mark.asyncio
async def test_targets_view_timeout_disables_old_controls_and_reopens(monkeypatch):
    async def fake_summary(_discord_id):
        from services.governor_account_service import summarize_accounts

        return summarize_accounts({"Main": {"GovernorID": "99", "GovernorName": "Refreshed"}})

    monkeypatch.setattr(
        "services.governor_account_service.get_account_summary_for_user",
        fake_summary,
    )

    class _Followup:
        sent = None

        async def send(self, content, **kwargs):
            self.sent = (content, kwargs)

    followup = _Followup()
    ctx = SimpleNamespace(user=SimpleNamespace(id=1), followup=followup)
    view = kvk_targets_views.make_kvk_targets_view(
        ctx,
        [_option()],
        _on_select,
        show_register_btn=False,
        ephemeral=False,
    )

    await view.on_timeout()

    assert all(child.disabled for child in view.children)
    content, kwargs = followup.sent
    assert content.startswith("⌛ Selector expired.")
    assert kwargs["ephemeral"] is False
    assert not hasattr(kwargs["view"], "_last_kvk_map")
    assert kwargs["view"].children[0].options[0].value == "99"
