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


def _make_interaction():
    """Build a minimal fake interaction that satisfies the view callbacks."""

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

    return _Interaction()


def _stub_load_board_payload(view):
    """Patch _load_board_payload on a view instance so it never hits the DB."""

    async def _stub(self=None):
        return {
            "actions": {
                "can_move_to_waitlist": False,
                "can_move_to_roster": False,
                "can_reject_signup": True,
                "can_reset_ranks": True,
            },
            "selection_data": {
                "roster_rows": [],
                "waitlist_rows": [],
            },
        }

    view._load_board_payload = _stub


# ---------------------------------------------------------------------------
# Button state — existing source uses _apply_action_state to disable buttons.
# The buttons ARE always present but may be disabled.
# ---------------------------------------------------------------------------


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

    # move_waitlist is disabled when can_move_to_waitlist=False
    assert buttons["mge_lead_move_waitlist"].disabled is True
    # move_roster is enabled when can_move_to_roster=True
    assert buttons["mge_lead_move_roster"].disabled is False
    assert buttons["mge_lead_reject"].disabled is False
    assert buttons["mge_lead_reset"].disabled is False


# ---------------------------------------------------------------------------
# Row 2 publish pipeline buttons — must NOT call _load_board_payload
# Stub it anyway to be safe; the real hang guard is the stub.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_row_three_buttons_are_wired_to_live_actions(monkeypatch: pytest.MonkeyPatch) -> None:
    sent = []

    async def _send_ephemeral(interaction, message, **kwargs):
        sent.append((message, kwargs))

    monkeypatch.setattr(
        "ui.views.mge_simplified_leadership_view.send_ephemeral",
        _send_ephemeral,
    )
    monkeypatch.setattr(
        "ui.views.mge_simplified_leadership_view.is_admin_or_leadership_interaction",
        lambda interaction: True,
    )

    view = MGESimplifiedLeadershipView(event_id=88)
    # Stub DB call on this instance to prevent any accidental blocking
    _stub_load_board_payload(view)
    buttons = _button_map(view)

    interaction = _make_interaction()
    await buttons["mge_lead_generate_targets"].callback(interaction)
    assert interaction.response.modal is not None

    # override_targets calls _load_board_payload then sends an ephemeral
    # selection view (not a modal).  The stub returns empty roster/waitlist
    # rows so the callback sends "⚠️ No active awards available to override."
    interaction = _make_interaction()
    await buttons["mge_lead_override_targets"].callback(interaction)
    assert any("No active awards" in m for m, _ in sent)

    interaction = _make_interaction()
    await buttons["mge_lead_publish"].callback(interaction)
    assert any("Confirm publish / republish" in m for m, _ in sent)

    interaction = _make_interaction()
    await buttons["mge_lead_unpublish"].callback(interaction)
    assert any("Confirm unpublish" in m for m, _ in sent)


# ---------------------------------------------------------------------------
# Mode switch buttons — existing source has BOTH switch_open and switch_fixed
# on the leadership view (custom_ids: mge_lead_switch_open, mge_lead_switch_fixed)
# ---------------------------------------------------------------------------


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
    monkeypatch.setattr(
        "ui.views.mge_simplified_leadership_view.is_admin_interaction", lambda i: True
    )

    view = MGESimplifiedLeadershipView(event_id=42)
    buttons = _button_map(view)

    await buttons["mge_lead_switch_open"].callback(_make_interaction())
    assert any("Confirm switch to open" in m for m, _ in sent)
    assert any(
        kw.get("view") is not None and kw["view"].__class__.__name__ == "ConfirmSwitchOpenView"
        for _, kw in sent
    )

    await buttons["mge_lead_switch_fixed"].callback(_make_interaction())
    assert any("Confirm switch to fixed" in m for m, _ in sent)
    assert any(
        kw.get("view") is not None and kw["view"].__class__.__name__ == "ConfirmSwitchFixedView"
        for _, kw in sent
    )


# ---------------------------------------------------------------------------
# Publish confirm view — repeated-use guard (source unchanged)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Move to Roster — existing source: button is always present, disabled when
# action_state disables it. Callback calls _load_board_payload — must stub.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_move_roster_opens_selection_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    sent = []

    async def _send_ephemeral(interaction, message, **kwargs):
        sent.append((message, kwargs))

    monkeypatch.setattr(
        "ui.views.mge_simplified_leadership_view.send_ephemeral",
        _send_ephemeral,
    )
    monkeypatch.setattr(
        "ui.views.mge_simplified_leadership_view.is_admin_or_leadership_interaction",
        lambda interaction: True,
    )

    view = MGESimplifiedLeadershipView(event_id=88, action_state={"can_move_to_roster": True})

    # Stub _load_board_payload to return roster rows without hitting DB
    async def _stub_payload():
        return {
            "actions": {"can_move_to_roster": True, "can_promote_with_swap": False},
            "selection_data": {
                "roster_rows": [],
                "waitlist_rows": [
                    {
                        "AwardId": 10,
                        "GovernorNameSnapshot": "WaitlistGov",
                        "SimplifiedStatus": "waitlist",
                        "WaitlistOrder": 1,
                        "ComputedWaitlistOrder": 1,
                    }
                ],
            },
        }

    view._load_board_payload = _stub_payload

    buttons = _button_map(view)
    assert "mge_lead_move_roster" in buttons

    interaction = _make_interaction()
    await buttons["mge_lead_move_roster"].callback(interaction)

    # Should have sent an ephemeral selection prompt (not a modal directly)
    assert len(sent) > 0
