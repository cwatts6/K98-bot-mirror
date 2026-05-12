from __future__ import annotations

import os
import sys
import types

sys.modules.setdefault("aiofiles", types.ModuleType("aiofiles"))
os.environ.setdefault("OUR_KINGDOM", "0")
if "dotenv" not in sys.modules:
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda *args, **kwargs: None
    sys.modules["dotenv"] = dotenv

import pytest

from ui.views.mge_simplified_leadership_view import MGESimplifiedLeadershipView


def _button_map(view):
    return {getattr(child, "custom_id", ""): child for child in view.children}


def _make_interaction(user_id: int = 9001):
    class _Response:
        def __init__(self):
            self.modal = None
            self.messages: list[str] = []

        async def send_modal(self, modal):
            self.modal = modal

        async def send_message(self, message: str, ephemeral: bool = False, **kwargs):
            self.messages.append(message)

    class _User:
        id = user_id

    class _Interaction:
        def __init__(self):
            self.user = _User()
            self.client = object()
            self.response = _Response()

    return _Interaction()


async def _fake_send_ephemeral(interaction, message: str, **kwargs):
    interaction.response.messages.append(message)


@pytest.mark.asyncio
async def test_leadership_view_has_admin_add_signup_button():
    """Verify that Admin Add Signup button exists on the leadership view."""
    view = MGESimplifiedLeadershipView(event_id=101)
    custom_ids = [getattr(child, "custom_id", "") for child in view.children]
    assert "mge_lead_admin_add_signup" in custom_ids


@pytest.mark.asyncio
async def test_leadership_view_has_all_expected_buttons():
    """Verify all expected buttons are present and none are missing."""
    view = MGESimplifiedLeadershipView(event_id=101)
    custom_ids = [getattr(child, "custom_id", "") for child in view.children]

    expected = [
        "mge_lead_edit_rules",
        "mge_lead_switch_open",
        "mge_lead_switch_fixed",
        "mge_lead_refresh",
        "mge_lead_admin_add_signup",
        "mge_lead_adjust_rank",
        "mge_lead_move_waitlist",
        "mge_lead_move_roster",
        "mge_lead_reject",
        "mge_lead_reset",
        "mge_lead_generate_targets",
        "mge_lead_override_targets",
        "mge_lead_publish",
        "mge_lead_unpublish",
    ]
    for eid in expected:
        assert eid in custom_ids, f"Missing expected button: {eid}"


@pytest.mark.asyncio
async def test_admin_add_signup_rejects_non_leadership(monkeypatch):
    """Admin Add Signup should reject non-leadership users."""
    monkeypatch.setattr(
        "ui.views.mge_simplified_leadership_view.is_admin_or_leadership_interaction",
        lambda interaction: False,
    )
    monkeypatch.setattr(
        "ui.views.mge_simplified_leadership_view.send_ephemeral",
        _fake_send_ephemeral,
    )

    view = MGESimplifiedLeadershipView(event_id=101)
    buttons = _button_map(view)
    interaction = _make_interaction()

    await buttons["mge_lead_admin_add_signup"].callback(interaction)

    assert interaction.response.messages[-1] == "❌ Leadership/admin only."
