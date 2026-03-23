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


@pytest.mark.asyncio
async def test_view_button_states_follow_action_payload() -> None:
    view = MGESimplifiedLeadershipView(
        event_id=77,
        action_state={
            "can_move_to_waitlist": False,
            "can_move_to_roster": True,
            "can_reject_signup": True,
            "can_reset_ranks": True,
        },
    )
    buttons = _button_map(view)

    assert buttons["mge_lead_move_waitlist"].disabled is True
    assert buttons["mge_lead_move_roster"].disabled is False
    assert buttons["mge_lead_reject"].disabled is False
    assert buttons["mge_lead_reset"].disabled is False


@pytest.mark.asyncio
async def test_row_three_buttons_are_wired_to_live_actions(monkeypatch: pytest.MonkeyPatch) -> None:
    sent = []

    async def _send_ephemeral(interaction, message, **kwargs):
        sent.append((message, kwargs))

    monkeypatch.setattr(
        "ui.views.mge_simplified_leadership_view.send_ephemeral",
        _send_ephemeral,
    )

    view = MGESimplifiedLeadershipView(event_id=88)
    buttons = _button_map(view)

    class _Response:
        def __init__(self):
            self.modal = None

        async def send_modal(self, modal):
            self.modal = modal

    class _User:
        id = 9001

    class _Interaction:
        def __init__(self):
            self.user = _User()
            self.client = object()
            self.response = _Response()

    interaction = _Interaction()

    monkeypatch.setattr(
        "ui.views.mge_simplified_leadership_view.is_admin_or_leadership_interaction",
        lambda interaction: True,
    )

    await buttons["mge_lead_generate_targets"].callback(interaction)
    assert interaction.response.modal is not None

    interaction = _Interaction()
    await buttons["mge_lead_override_targets"].callback(interaction)
    assert interaction.response.modal is not None

    interaction = _Interaction()
    await buttons["mge_lead_publish"].callback(interaction)
    assert "Confirm publish / republish" in sent[-1][0]

    interaction = _Interaction()
    await buttons["mge_lead_unpublish"].callback(interaction)
    assert "Confirm unpublish" in sent[-1][0]


@pytest.mark.asyncio
async def test_mode_switch_buttons_are_inline_and_admin_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent = []

    async def _send_ephemeral(interaction, message, **kwargs):
        sent.append((message, kwargs))

    monkeypatch.setattr(
        "ui.views.mge_simplified_leadership_view.send_ephemeral",
        _send_ephemeral,
    )

    class _Response:
        async def send_modal(self, modal):
            raise AssertionError("modal should not be used")

    class _User:
        id = 9001

    class _Interaction:
        def __init__(self):
            self.user = _User()
            self.client = object()
            self.response = _Response()

    monkeypatch.setattr(
        "ui.views.mge_simplified_leadership_view.is_admin_interaction", lambda i: True
    )

    view = MGESimplifiedLeadershipView(event_id=42)
    buttons = _button_map(view)

    await buttons["mge_lead_switch_open"].callback(_Interaction())
    assert "Confirm switch to open" in sent[-1][0]
    assert sent[-1][1]["view"].__class__.__name__ == "ConfirmSwitchOpenView"

    await buttons["mge_lead_switch_fixed"].callback(_Interaction())
    assert "Confirm switch to fixed" in sent[-1][0]
    assert sent[-1][1]["view"].__class__.__name__ == "ConfirmSwitchFixedView"


@pytest.mark.asyncio
async def test_publish_confirm_view_rejects_repeated_use(monkeypatch: pytest.MonkeyPatch) -> None:
    sent = []

    async def _send_ephemeral(interaction, message, **kwargs):
        sent.append(message)

    monkeypatch.setattr(
        "ui.views.mge_simplified_leadership_view.send_ephemeral",
        _send_ephemeral,
    )

    from ui.views.mge_simplified_leadership_view import _PublishConfirmView

    view = _PublishConfirmView(event_id=7)
    view._completed = True

    class _Response:
        def is_done(self):
            return False

    class _Interaction:
        def __init__(self):
            self.response = _Response()

    await view.children[0].callback(_Interaction())

    assert "already been used" in sent[-1]


@pytest.mark.asyncio
async def test_move_roster_opens_promote_modal(monkeypatch: pytest.MonkeyPatch) -> None:
    view = MGESimplifiedLeadershipView(event_id=88, action_state={"can_move_to_roster": True})
    buttons = _button_map(view)

    class _Response:
        def __init__(self):
            self.modal = None

        async def send_modal(self, modal):
            self.modal = modal

    class _User:
        id = 9001

    class _Interaction:
        def __init__(self):
            self.user = _User()
            self.client = object()
            self.response = _Response()

    monkeypatch.setattr(
        "ui.views.mge_simplified_leadership_view.is_admin_or_leadership_interaction",
        lambda interaction: True,
    )

    interaction = _Interaction()
    await buttons["mge_lead_move_roster"].callback(interaction)

    assert interaction.response.modal is not None
    assert interaction.response.modal.__class__.__name__ == "_PromoteWithOptionalDemoteModal"
