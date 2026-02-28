from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ark.registration_flow import ArkRegistrationController


class DummyResponse:
    def __init__(self) -> None:
        self.sent = []
        self.edits = []

    async def send_message(self, content: str, ephemeral: bool = False, **kwargs):
        self.sent.append({"content": content, "ephemeral": ephemeral})

    async def edit_message(self, content: str | None = None, view=None):
        self.edits.append({"content": content, "view": view})


class DummyFollowup:
    def __init__(self) -> None:
        self.sent = []

    async def send(self, content: str, ephemeral: bool = False, **kwargs):
        self.sent.append({"content": content, "ephemeral": ephemeral})


class DummyUser:
    def __init__(self, user_id: int) -> None:
        self.id = user_id


class DummyInteraction:
    def __init__(self, user_id: int = 999) -> None:
        self.user = DummyUser(user_id)
        self.response = DummyResponse()
        self.followup = DummyFollowup()
        self.client = object()


@pytest.mark.asyncio
async def test_admin_add_blocks_sub_when_players_not_full(monkeypatch):
    controller = ArkRegistrationController(
        match_id=1,
        config={"PlayersCap": 2, "SubsCap": 1, "AdminOverrideSubRule": 0},
    )
    interaction = DummyInteraction()

    async def _get_match(_match_id):
        return {
            "MatchId": 1,
            "Alliance": "K98",
            "ArkWeekendDate": datetime(2026, 3, 7, tzinfo=UTC).date(),
            "MatchDay": "Sat",
            "MatchTimeUtc": datetime(2026, 3, 7, 11, 0, tzinfo=UTC).time(),
            "Status": "Scheduled",
        }

    async def _get_roster(_match_id):
        return [{"SlotType": "Player", "GovernorId": 1}]

    called = {"add": False}

    async def _add_signup(**_k):
        called["add"] = True
        return 1

    monkeypatch.setattr("ark.registration_flow.get_match", _get_match)
    monkeypatch.setattr("ark.registration_flow.get_roster", _get_roster)
    monkeypatch.setattr(
        "ark.registration_flow.find_active_signup_for_weekend", lambda *_a, **_k: None
    )
    monkeypatch.setattr(controller, "_validate_governor", lambda *_a, **_k: True)
    monkeypatch.setattr("ark.registration_flow.get_signup", lambda *_a, **_k: None)
    monkeypatch.setattr("ark.registration_flow.add_signup", _add_signup)
    monkeypatch.setattr(controller, "_is_admin_or_leadership", lambda *_a, **_k: True)

    await controller._apply_admin_add(interaction, "123", "Gov Name", slot_type="Sub")

    assert called["add"] is False
    assert interaction.response.sent
    assert "Sub slots are only available" in interaction.response.sent[-1]["content"]


@pytest.mark.asyncio
async def test_auto_promotion_moves_first_sub(monkeypatch):
    controller = ArkRegistrationController(
        match_id=2,
        config={"PlayersCap": 2, "SubsCap": 2, "AdminOverrideSubRule": 0},
    )
    interaction = DummyInteraction()

    match = {
        "MatchId": 2,
        "Alliance": "K98",
        "ArkWeekendDate": datetime(2026, 3, 7, tzinfo=UTC).date(),
        "MatchDay": "Sat",
        "MatchTimeUtc": datetime(2026, 3, 7, 11, 0, tzinfo=UTC).time(),
        "Status": "Scheduled",
    }

    roster = [
        {"GovernorId": 11, "SlotType": "Player"},
        {"GovernorId": 22, "SlotType": "Sub", "DiscordUserId": 123},
    ]

    called = {"move": False, "audit": False}

    async def _move_signup_slot(match_id, governor_id, slot_type, actor_discord_id):
        called["move"] = (match_id, governor_id, slot_type)
        return True

    async def _audit(*_a, **_k):
        called["audit"] = True
        return 1

    async def _send_dm(*_a, **_k):
        return None

    monkeypatch.setattr("ark.registration_flow.move_signup_slot", _move_signup_slot)
    monkeypatch.setattr("ark.registration_flow.insert_audit_log", _audit)
    monkeypatch.setattr(controller, "_send_promotion_dm", _send_dm)

    await controller._maybe_promote_sub(interaction, match, roster)

    assert called["move"] == (2, 22, "Player")
    assert called["audit"] is True


@pytest.mark.asyncio
async def test_admin_add_denies_non_admin(monkeypatch):
    controller = ArkRegistrationController(
        match_id=1,
        config={"PlayersCap": 2, "SubsCap": 1, "AdminOverrideSubRule": 0},
    )
    interaction = DummyInteraction()

    monkeypatch.setattr(controller, "_is_admin_or_leadership", lambda *_a, **_k: False)

    await controller._apply_admin_add(interaction, "123", "Gov Name", slot_type="Player")

    assert interaction.response.sent
    assert "Admin/Leadership only" in interaction.response.sent[-1]["content"]


@pytest.mark.asyncio
async def test_admin_remove_calls_dal(monkeypatch):
    controller = ArkRegistrationController(
        match_id=1,
        config={"PlayersCap": 2, "SubsCap": 1, "AdminOverrideSubRule": 0},
    )
    interaction = DummyInteraction()

    async def _get_match(_match_id):
        return {
            "MatchId": 1,
            "Alliance": "K98",
            "ArkWeekendDate": datetime(2026, 3, 7, tzinfo=UTC).date(),
            "MatchDay": "Sat",
            "MatchTimeUtc": datetime(2026, 3, 7, 11, 0, tzinfo=UTC).time(),
            "Status": "Scheduled",
        }

    async def _get_roster(_match_id):
        return [
            {
                "GovernorId": 99,
                "GovernorNameSnapshot": "RemoveMe",
                "SlotType": "Player",
                "DiscordUserId": 123,
            }
        ]

    called = {"remove": False, "audit": False}

    async def _remove_signup(match_id, governor_id, status, actor_discord_id):
        called["remove"] = (match_id, governor_id, status, actor_discord_id)
        return True

    async def _audit(*_a, **_k):
        called["audit"] = True
        return 1

    async def _refresh(*_a, **_k):
        return None

    monkeypatch.setattr(controller, "_is_admin_or_leadership", lambda *_a, **_k: True)
    monkeypatch.setattr("ark.registration_flow.get_match", _get_match)
    monkeypatch.setattr("ark.registration_flow.get_roster", _get_roster)
    monkeypatch.setattr("ark.registration_flow.remove_signup", _remove_signup)
    monkeypatch.setattr("ark.registration_flow.insert_audit_log", _audit)
    monkeypatch.setattr(controller, "refresh_registration_message", _refresh)

    await controller._apply_admin_remove(interaction, "99")

    assert called["remove"] == (1, 99, "Removed", interaction.user.id)
    assert called["audit"] is True


@pytest.mark.asyncio
async def test_admin_move_blocks_player_when_full(monkeypatch):
    controller = ArkRegistrationController(
        match_id=1,
        config={"PlayersCap": 1, "SubsCap": 1, "AdminOverrideSubRule": 0},
    )
    interaction = DummyInteraction()

    async def _get_match(_match_id):
        return {
            "MatchId": 1,
            "Alliance": "K98",
            "ArkWeekendDate": datetime(2026, 3, 7, tzinfo=UTC).date(),
            "MatchDay": "Sat",
            "MatchTimeUtc": datetime(2026, 3, 7, 11, 0, tzinfo=UTC).time(),
            "Status": "Scheduled",
        }

    async def _get_roster(_match_id):
        return [
            {"GovernorId": 1, "GovernorNameSnapshot": "FullPlayer", "SlotType": "Player"},
            {"GovernorId": 2, "GovernorNameSnapshot": "SubToMove", "SlotType": "Sub"},
        ]

    monkeypatch.setattr(controller, "_is_admin_or_leadership", lambda *_a, **_k: True)
    monkeypatch.setattr("ark.registration_flow.get_match", _get_match)
    monkeypatch.setattr("ark.registration_flow.get_roster", _get_roster)

    await controller._apply_admin_move(interaction, "2", slot_type="Player")

    assert interaction.response.sent
    assert "Player slots are full" in interaction.response.sent[-1]["content"]
