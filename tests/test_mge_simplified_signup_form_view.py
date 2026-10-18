"""Tests for MgeSimplifiedSignupFormView — no modal, no DM follow-up."""

from __future__ import annotations

import asyncio
import os
import sys
import types
from types import SimpleNamespace

sys.modules.setdefault("aiofiles", types.ModuleType("aiofiles"))
os.environ.setdefault("OUR_KINGDOM", "0")
if "dotenv" not in sys.modules:
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda *args, **kwargs: None
    sys.modules["dotenv"] = dotenv

import pytest

from ui.views.mge_signup_modal import MgeSignupModalPayload
from ui.views.mge_simplified_signup_form_view import (
    MgeSimplifiedSignupFormView,
    build_simplified_signup_form_view,
)


def _make_payload(signup_id: int | None = None) -> MgeSignupModalPayload:
    return MgeSignupModalPayload(
        event_id=42,
        governor_id=100,
        governor_name="TestGov",
        actor_role_ids={1},
        admin_role_ids={9001},
        signup_id=signup_id,
        on_success_refresh=None,
    )


def _make_commander_options() -> dict[int, str]:
    return {1: "Commander Alpha", 2: "Commander Beta"}


class _FakeResponse:
    def __init__(self) -> None:
        self.sent_messages: list[str] = []
        self.modal = None
        self._done = False

    async def send_message(self, message: str, *, ephemeral: bool = False, **kwargs) -> None:
        self.sent_messages.append(message)
        self._done = True

    async def send_modal(self, modal) -> None:
        self.modal = modal
        self._done = True

    async def defer(self) -> None:
        self._done = True

    def is_done(self) -> bool:
        return self._done


class _FakeInteraction:
    def __init__(self, user_id: int = 1) -> None:
        self.user = SimpleNamespace(id=user_id)
        self.guild = None
        self.response = _FakeResponse()
        self.followup_messages: list[str] = []
        self.followup = SimpleNamespace(
            send=self._followup_send,
        )

    async def _followup_send(self, message: str, *, ephemeral: bool = False) -> None:
        self.followup_messages.append(message)


def _build_view(*, signup_id: int | None = None) -> MgeSimplifiedSignupFormView:
    async def _make() -> MgeSimplifiedSignupFormView:
        return MgeSimplifiedSignupFormView(
            payload=_make_payload(signup_id=signup_id),
            commander_options=_make_commander_options(),
        )

    return asyncio.run(_make())


# --- Structure ---


def test_view_instantiates_without_error() -> None:
    view = _build_view()
    assert view is not None


def test_priority_rank_dropdown_has_four_options() -> None:
    view = _build_view()
    # Find the priority-rank select
    from ui.views.mge_simplified_signup_form_view import _PriorityRankSelect

    selects = [c for c in view.children if isinstance(c, _PriorityRankSelect)]
    assert len(selects) == 1
    assert len(selects[0].options) == 4


def test_commander_dropdown_populated_from_options() -> None:
    view = _build_view()
    from ui.views.mge_simplified_signup_form_view import _CommanderSelect

    selects = [c for c in view.children if isinstance(c, _CommanderSelect)]
    assert len(selects) == 1
    assert len(selects[0].options) == 2


def test_view_has_sign_up_button() -> None:
    view = _build_view()
    custom_ids = [getattr(c, "custom_id", "") for c in view.children]
    assert "mge_simplified_signup_submit" in custom_ids


# --- Validation: submit without selections ---


@pytest.mark.asyncio
async def test_submit_without_priority_rank_is_rejected() -> None:
    sent: list[str] = []

    async def _fake_send_ephemeral(interaction, message: str, **kwargs) -> None:
        sent.append(message)

    import ui.views.mge_simplified_signup_form_view as mod

    original = mod.send_ephemeral
    mod.send_ephemeral = _fake_send_ephemeral  # type: ignore[assignment]
    try:
        view = MgeSimplifiedSignupFormView(
            payload=_make_payload(),
            commander_options=_make_commander_options(),
        )
        view.selected_priority_rank_value = None
        view.selected_commander_id = 1
        interaction = _FakeInteraction()
        await view.submit_btn.callback(interaction)
    finally:
        mod.send_ephemeral = original  # type: ignore[assignment]

    assert any("Priority" in m for m in sent)


@pytest.mark.asyncio
async def test_submit_without_commander_is_rejected() -> None:
    sent: list[str] = []

    async def _fake_send_ephemeral(interaction, message: str, **kwargs) -> None:
        sent.append(message)

    import ui.views.mge_simplified_signup_form_view as mod

    original = mod.send_ephemeral
    mod.send_ephemeral = _fake_send_ephemeral  # type: ignore[assignment]
    try:
        view = MgeSimplifiedSignupFormView(
            payload=_make_payload(),
            commander_options=_make_commander_options(),
        )
        view.selected_priority_rank_value = "high_1_5"
        view.selected_commander_id = None
        interaction = _FakeInteraction()
        await view.submit_btn.callback(interaction)
    finally:
        mod.send_ephemeral = original  # type: ignore[assignment]

    assert any("Commander" in m for m in sent)


# --- Submit calls service and does NOT open modal or DM ---


@pytest.mark.asyncio
async def test_submit_with_valid_selection_calls_create_signup(monkeypatch) -> None:
    from mge import mge_signup_service

    calls: list[dict] = []

    def _fake_create(**kwargs) -> object:
        calls.append(kwargs)
        return SimpleNamespace(success=True, message="Signup created.", signup_id=99)

    monkeypatch.setattr(mge_signup_service, "create_signup", _fake_create)

    view = MgeSimplifiedSignupFormView(
        payload=_make_payload(),
        commander_options=_make_commander_options(),
    )
    view.selected_priority_rank_value = "high_1_5"
    view.selected_commander_id = 1
    interaction = _FakeInteraction()

    await view.submit_btn.callback(interaction)

    assert len(calls) == 1
    assert calls[0]["request_priority"] == "High"
    assert calls[0]["preferred_rank_band"] == "1-5"
    assert calls[0]["requested_commander_id"] == 1
    assert calls[0]["current_heads"] == 0
    assert calls[0]["kingdom_role"] is None
    assert calls[0]["gear_text"] is None
    assert calls[0]["armament_text"] is None


@pytest.mark.asyncio
async def test_no_modal_is_opened_on_submit(monkeypatch) -> None:
    from mge import mge_signup_service

    monkeypatch.setattr(
        mge_signup_service,
        "create_signup",
        lambda **kw: SimpleNamespace(success=True, message="ok", signup_id=1),
    )

    view = MgeSimplifiedSignupFormView(
        payload=_make_payload(),
        commander_options=_make_commander_options(),
    )
    view.selected_priority_rank_value = "medium_6_10"
    view.selected_commander_id = 1
    interaction = _FakeInteraction()

    await view.submit_btn.callback(interaction)

    # Modal must NOT have been sent
    assert interaction.response.modal is None
    # Response should have been a message (success/failure text)
    assert len(interaction.response.sent_messages) == 1


@pytest.mark.asyncio
async def test_no_dm_followup_triggered_on_submit(monkeypatch) -> None:
    """DM follow-up must NOT be triggered by the simplified form view."""
    from mge import mge_dm_followup, mge_signup_service

    monkeypatch.setattr(
        mge_signup_service,
        "create_signup",
        lambda **kw: SimpleNamespace(success=True, message="ok", signup_id=1),
    )

    dm_calls: list[int] = []

    async def _fake_open_dm(**kwargs):
        dm_calls.append(1)
        return (True, "dm sent")

    monkeypatch.setattr(mge_dm_followup, "open_dm_followup", _fake_open_dm)

    view = MgeSimplifiedSignupFormView(
        payload=_make_payload(),
        commander_options=_make_commander_options(),
    )
    view.selected_priority_rank_value = "low_11_15"
    view.selected_commander_id = 1
    interaction = _FakeInteraction()

    await view.submit_btn.callback(interaction)

    assert len(dm_calls) == 0, "DM follow-up must not be triggered in simplified flow"


# --- Edit prefill ---


def test_edit_prefill_resolves_legacy_priority_and_rank_band() -> None:
    """build_simplified_signup_form_view should map legacy fields to combined option."""
    existing_row = {
        "RequestPriority": "Medium",
        "PreferredRankBand": "6-10",
        "RequestedCommanderId": 2,
    }

    async def _make():
        return build_simplified_signup_form_view(
            payload=_make_payload(signup_id=55),
            commander_options=_make_commander_options(),
            is_edit=True,
            existing_signup_row=existing_row,
        )

    view = asyncio.run(_make())
    assert view.selected_priority_rank_value == "medium_6_10"
    assert view.selected_commander_id == 2


def test_edit_prefill_falls_back_to_no_preference_for_unknown_legacy_combination() -> None:
    """Unknown legacy priority+rank_band should fall back to no_preference."""
    existing_row = {
        "RequestPriority": "OldCustomPriority",
        "PreferredRankBand": "legacy_band",
        "RequestedCommanderId": 1,
    }

    async def _make():
        return build_simplified_signup_form_view(
            payload=_make_payload(signup_id=56),
            commander_options=_make_commander_options(),
            is_edit=True,
            existing_signup_row=existing_row,
        )

    view = asyncio.run(_make())
    assert view.selected_priority_rank_value == "no_preference"


def test_edit_prefill_without_existing_row_leaves_none() -> None:
    async def _make():
        return build_simplified_signup_form_view(
            payload=_make_payload(signup_id=57),
            commander_options=_make_commander_options(),
            is_edit=True,
            existing_signup_row=None,
        )

    view = asyncio.run(_make())
    assert view.selected_priority_rank_value is None
    assert view.selected_commander_id is None
