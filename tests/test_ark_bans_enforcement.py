from datetime import UTC, datetime

import pytest

from ark.registration_flow import ArkRegistrationController


class DummyResp:
    def __init__(self):
        self.sent = []

    def is_done(self):
        return False

    async def send_message(self, content=None, ephemeral=False, **kwargs):
        self.sent.append({"content": content, "ephemeral": ephemeral, **kwargs})


class DummyFollowup:
    def __init__(self):
        self.sent = []

    async def send(self, content=None, ephemeral=False, **kwargs):
        self.sent.append({"content": content, "ephemeral": ephemeral, **kwargs})


class DummyUser:
    id = 111


class DummyInteraction:
    def __init__(self):
        self.user = DummyUser()
        self.response = DummyResp()
        self.followup = DummyFollowup()
        self.client = object()
        self.guild = None


@pytest.mark.asyncio
async def test_admin_add_blocked_by_ban_when_override_off(monkeypatch):
    controller = ArkRegistrationController(
        match_id=1,
        config={"PlayersCap": 30, "SubsCap": 15, "AdminOverrideBanRule": 0},
    )
    interaction = DummyInteraction()

    async def _get_match(_):
        return {
            "MatchId": 1,
            "Alliance": "K98",
            "ArkWeekendDate": datetime(2026, 3, 7, tzinfo=UTC).date(),
            "Status": "Scheduled",
        }

    async def _active_ban(**_kwargs):
        return {"BanId": 900, "Reason": "Test reason"}

    monkeypatch.setattr(controller, "_is_admin_or_leadership", lambda *_a, **_k: True)
    monkeypatch.setattr("ark.registration_flow.get_match", _get_match)
    monkeypatch.setattr("ark.registration_flow.get_active_ban_for", _active_ban)

    await controller._apply_admin_add(interaction, "12345", "Gov Name", slot_type="Player")

    assert interaction.response.sent
    assert "active Ark ban applies".lower() in interaction.response.sent[-1]["content"].lower()


@pytest.mark.asyncio
async def test_admin_add_allows_when_override_on(monkeypatch):
    controller = ArkRegistrationController(
        match_id=1,
        config={"PlayersCap": 30, "SubsCap": 15, "AdminOverrideBanRule": 1},
    )
    interaction = DummyInteraction()

    async def _get_match(_):
        return {
            "MatchId": 1,
            "Alliance": "K98",
            "ArkWeekendDate": datetime(2026, 3, 7, tzinfo=UTC).date(),
            "Status": "Scheduled",
        }

    async def _active_ban(**_kwargs):
        return {"BanId": 901, "Reason": "Test reason"}

    async def _noop(*_a, **_k):
        return True

    monkeypatch.setattr(controller, "_is_admin_or_leadership", lambda *_a, **_k: True)
    monkeypatch.setattr("ark.registration_flow.get_match", _get_match)
    monkeypatch.setattr("ark.registration_flow.get_active_ban_for", _active_ban)
    monkeypatch.setattr("ark.registration_flow.add_signup", _noop)
    monkeypatch.setattr("ark.registration_flow.insert_audit_log", _noop)
    monkeypatch.setattr(controller, "refresh_registration_message", _noop)

    await controller._apply_admin_add(interaction, "12345", "Gov Name", slot_type="Player")

    # override warning should be emitted
    assert any(
        "Ban override is enabled" in (m.get("content") or "") for m in interaction.followup.sent
    )
