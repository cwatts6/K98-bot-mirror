from __future__ import annotations

from types import SimpleNamespace

import pytest

from ui.views.mge_signup_view import MGESignupView


class _FakeRole:
    def __init__(self, role_id: int):
        self.id = role_id


class _FakeMember:
    def __init__(self, user_id: int, roles: list[int] | None = None):
        self.id = user_id
        self.roles = [_FakeRole(r) for r in (roles or [])]


class _FakeResponse:
    def __init__(self):
        self.modal = None
        self.sent_messages = []
        self._done = False

    async def send_modal(self, modal):
        self.modal = modal
        self._done = True

    async def send_message(self, message: str, *, ephemeral: bool = False, view=None):
        self.sent_messages.append({"message": message, "ephemeral": ephemeral, "view": view})
        self._done = True

    def is_done(self) -> bool:
        return self._done


class _FakeMessage:
    def __init__(self):
        self.edited_embed = None

    async def edit(self, *, embed=None, **kwargs):
        self.edited_embed = embed


class _FakeInteraction:
    def __init__(self, user_id: int, roles: list[int] | None = None):
        self.user = _FakeMember(user_id, roles)
        self.guild = None
        self.response = _FakeResponse()
        self.message = _FakeMessage()
        self.followup = SimpleNamespace(send=self._followup_send)
        self.followup_messages = []

    async def _followup_send(self, message: str, *, ephemeral: bool = False):
        self.followup_messages.append({"message": message, "ephemeral": ephemeral})


class _FakeAdminDeps:
    def __init__(self, is_admin_value: bool = False):
        self._is_admin_value = is_admin_value
        self.admin_role_ids = {9001}
        self.leadership_role_ids = {9002}
        self.refreshed_event_ids: list[int] = []

    def is_admin(self, interaction) -> bool:
        return self._is_admin_value

    def refresh_embed(self, event_id: int) -> None:
        self.refreshed_event_ids.append(int(event_id))


class _FakePrimaryModal:
    """Test double for MgeSignupPrimaryModal / MgeSignupModal alias."""

    def __init__(self, *, payload, commander_options, title, **kwargs):
        self.payload = payload
        self.commander_options = commander_options
        self.title = title
        self.kwargs = kwargs


@pytest.mark.asyncio
async def test_sign_up_no_linked_governors_sends_error(monkeypatch):
    sent: list[str] = []

    async def _fake_send_ephemeral(interaction, message: str, **kwargs):
        sent.append(message)

    monkeypatch.setattr("ui.views.mge_signup_view.send_ephemeral", _fake_send_ephemeral)
    monkeypatch.setattr(
        "ui.views.mge_signup_view.mge_signup_service.get_linked_governors_for_user",
        lambda user_id: [],
    )

    view = MGESignupView(event_id=101, admin_deps=_FakeAdminDeps(False))
    interaction = _FakeInteraction(user_id=123, roles=[])

    await view.sign_up.callback(interaction)

    assert sent
    assert "No linked governors" in sent[-1]


@pytest.mark.asyncio
async def test_sign_up_single_governor_opens_primary_modal(monkeypatch):
    sent: list[dict[str, object]] = []

    async def _fake_send_ephemeral(interaction, message: str, *, view=None, **kwargs):
        sent.append({"message": message, "view": view})

    monkeypatch.setattr("ui.views.mge_signup_view.send_ephemeral", _fake_send_ephemeral)
    monkeypatch.setattr("ui.views.mge_signup_view.MgeSignupPrimaryModal", _FakePrimaryModal)
    monkeypatch.setattr(
        "ui.views.mge_signup_view.mge_signup_service.get_linked_governors_for_user",
        lambda user_id: [{"GovernorID": "777", "GovernorName": "Gov777"}],
    )
    monkeypatch.setattr(
        "ui.views.mge_signup_view.mge_signup_dal.fetch_event_signup_context",
        lambda event_id: {"EventId": event_id, "VariantName": "Infantry"},
    )
    monkeypatch.setattr(
        "ui.views.mge_signup_view.get_commanders_for_variant",
        lambda variant_name: [{"CommanderId": 1, "CommanderName": "Alexander"}],
    )

    view = MGESignupView(event_id=101, admin_deps=_FakeAdminDeps(False))
    interaction = _FakeInteraction(user_id=123, roles=[])

    await view.sign_up.callback(interaction)

    assert interaction.response.modal is None
    assert sent
    assert sent[-1]["view"] is not None
    primary_view = sent[-1]["view"]
    assert primary_view.payload.event_id == 101
    assert primary_view.payload.governor_id == 777
    assert primary_view.payload.governor_name == "Gov777"
    assert primary_view.commander_options == {1: "Alexander"}
    assert "Signup" in sent[-1]["message"] or "Create" in sent[-1]["message"]
    assert primary_view.kwargs["is_edit"] is False


@pytest.mark.asyncio
async def test_sign_up_single_governor_cache_empty_sends_error(monkeypatch):
    sent: list[str] = []

    async def _fake_send_ephemeral(interaction, message: str, **kwargs):
        sent.append(message)

    monkeypatch.setattr("ui.views.mge_signup_view.send_ephemeral", _fake_send_ephemeral)
    monkeypatch.setattr(
        "ui.views.mge_signup_view.mge_signup_service.get_linked_governors_for_user",
        lambda user_id: [{"GovernorID": "777", "GovernorName": "Gov777"}],
    )
    monkeypatch.setattr(
        "ui.views.mge_signup_view.mge_signup_dal.fetch_event_signup_context",
        lambda event_id: {"EventId": event_id, "VariantName": "Infantry"},
    )
    monkeypatch.setattr(
        "ui.views.mge_signup_view.get_commanders_for_variant",
        lambda variant_name: [],
    )

    view = MGESignupView(event_id=101, admin_deps=_FakeAdminDeps(False))
    interaction = _FakeInteraction(user_id=123, roles=[])

    await view.sign_up.callback(interaction)

    assert sent
    assert "Commander cache is unavailable" in sent[-1]


@pytest.mark.asyncio
async def test_withdraw_no_active_signup_sends_error(monkeypatch):
    sent: list[str] = []

    async def _fake_send_ephemeral(interaction, message: str, **kwargs):
        sent.append(message)

    monkeypatch.setattr("ui.views.mge_signup_view.send_ephemeral", _fake_send_ephemeral)
    monkeypatch.setattr(
        "ui.views.mge_signup_view.mge_signup_dal.fetch_active_signup_by_event_discord",
        lambda event_id, discord_user_id: None,
    )

    view = MGESignupView(event_id=101, admin_deps=_FakeAdminDeps(False))
    interaction = _FakeInteraction(user_id=123, roles=[])

    await view.withdraw.callback(interaction)

    assert sent
    assert "No active signup found" in sent[-1]


@pytest.mark.asyncio
async def test_withdraw_active_signup_success(monkeypatch):
    sent: list[str] = []

    async def _fake_send_ephemeral(interaction, message: str, **kwargs):
        sent.append(message)

    monkeypatch.setattr("ui.views.mge_signup_view.send_ephemeral", _fake_send_ephemeral)
    monkeypatch.setattr(
        "ui.views.mge_signup_view.mge_signup_dal.fetch_active_signups_by_event_discord",
        lambda event_id, discord_user_id: [
            {
                "SignupId": 9,
                "EventId": event_id,
                "GovernorId": 777,
                "GovernorNameSnapshot": "Gov777",
            }
        ],
    )
    monkeypatch.setattr(
        "ui.views.mge_signup_view.mge_signup_service.withdraw_signup",
        lambda **kwargs: SimpleNamespace(success=True, message="Signup withdrawn."),
    )

    view = MGESignupView(event_id=101, admin_deps=_FakeAdminDeps(False))
    interaction = _FakeInteraction(user_id=123, roles=[])

    await view.withdraw.callback(interaction)

    assert sent
    assert sent[-1].startswith("✅")
    assert "Signup withdrawn." in sent[-1]


@pytest.mark.asyncio
async def test_edit_no_active_signup_sends_error(monkeypatch):
    sent: list[str] = []

    async def _fake_send_ephemeral(interaction, message: str, **kwargs):
        sent.append(message)

    monkeypatch.setattr("ui.views.mge_signup_view.send_ephemeral", _fake_send_ephemeral)
    monkeypatch.setattr(
        "ui.views.mge_signup_view.mge_signup_dal.fetch_active_signups_by_event_discord",
        lambda event_id, discord_user_id: [],
    )

    view = MGESignupView(event_id=101, admin_deps=_FakeAdminDeps(False))
    interaction = _FakeInteraction(user_id=123, roles=[])

    await view.edit.callback(interaction)

    assert sent
    assert "No active signup found" in sent[-1]


@pytest.mark.asyncio
async def test_edit_active_signup_opens_primary_modal(monkeypatch):
    sent: list[dict[str, object]] = []

    async def _fake_send_ephemeral(interaction, message: str, *, view=None, **kwargs):
        sent.append({"message": message, "view": view})

    monkeypatch.setattr("ui.views.mge_signup_view.send_ephemeral", _fake_send_ephemeral)
    monkeypatch.setattr("ui.views.mge_signup_view.MgeSignupPrimaryModal", _FakePrimaryModal)
    monkeypatch.setattr(
        "ui.views.mge_signup_view.mge_signup_dal.fetch_active_signups_by_event_discord",
        lambda event_id, discord_user_id: [
            {
                "SignupId": 42,
                "EventId": event_id,
                "GovernorId": 777,
                "GovernorNameSnapshot": "Gov777",
            }
        ],
    )
    monkeypatch.setattr(
        "ui.views.mge_signup_view.mge_signup_dal.fetch_event_signup_context",
        lambda event_id: {"EventId": event_id, "VariantName": "Infantry"},
    )
    monkeypatch.setattr(
        "ui.views.mge_signup_view.get_commanders_for_variant",
        lambda variant_name: [{"CommanderId": 2, "CommanderName": "YSG"}],
    )

    view = MGESignupView(event_id=101, admin_deps=_FakeAdminDeps(False))
    interaction = _FakeInteraction(user_id=123, roles=[])

    await view.edit.callback(interaction)

    assert interaction.response.modal is None
    assert sent
    assert sent[-1]["view"] is not None
    primary_view = sent[-1]["view"]
    assert primary_view.payload.signup_id == 42
    assert primary_view.payload.governor_id == 777
    assert primary_view.commander_options == {2: "YSG"}
    assert primary_view.kwargs["is_edit"] is True


@pytest.mark.asyncio
async def test_admin_button_denied_for_non_admin(monkeypatch):
    sent: list[str] = []

    async def _fake_send_ephemeral(interaction, message: str, **kwargs):
        sent.append(message)

    monkeypatch.setattr("ui.views.mge_signup_view.send_ephemeral", _fake_send_ephemeral)

    view = MGESignupView(event_id=101, admin_deps=_FakeAdminDeps(False))
    interaction = _FakeInteraction(user_id=123, roles=[])

    await view.refresh_embed_button.callback(interaction)

    assert sent
    assert sent[-1] == "❌ Admin only."


@pytest.mark.asyncio
async def test_refresh_embed_button_keeps_base_view_refresh_callable(monkeypatch):
    view = MGESignupView(event_id=101, admin_deps=_FakeAdminDeps(True))

    assert callable(view.refresh)
    assert view.refresh.__self__ is view


@pytest.mark.asyncio
async def test_admin_refresh_embed_button_updates_message(monkeypatch):
    sent: list[str] = []

    async def _fake_send_ephemeral(interaction, message: str, **kwargs):
        sent.append(message)

    monkeypatch.setattr("ui.views.mge_signup_view.send_ephemeral", _fake_send_ephemeral)

    monkeypatch.setattr(
        "mge.dal.mge_event_dal.fetch_event_for_embed",
        lambda event_id: {"EventId": event_id, "EventName": "Test MGE"},
    )
    monkeypatch.setattr(
        "mge.dal.mge_event_dal.fetch_public_signup_names",
        lambda event_id: ["Gov1", "Gov2"],
    )
    fake_embed = object()
    monkeypatch.setattr(
        "mge.mge_embed_manager.build_mge_signup_embed",
        lambda row, public_signup_names=None: fake_embed,
    )

    deps = _FakeAdminDeps(True)
    view = MGESignupView(event_id=101, admin_deps=deps)
    interaction = _FakeInteraction(user_id=123, roles=[9001])

    await view.refresh_embed_button.callback(interaction)

    assert deps.refreshed_event_ids == []
    assert interaction.message.edited_embed is fake_embed
    assert sent
    assert sent[-1] == "✅ Embed refreshed."
