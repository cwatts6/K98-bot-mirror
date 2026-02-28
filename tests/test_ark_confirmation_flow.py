from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from ark.confirmation_flow import ArkConfirmationController


class DummyResponse:
    def __init__(self) -> None:
        self.sent = []
        self.edits = []
        self.deferred = 0

    async def defer(self, ephemeral: bool = True):
        self.deferred += 1

    async def send_message(self, content: str | None = None, **kwargs):
        self.sent.append({"content": content, **kwargs})

    async def edit_message(self, content: str | None = None, view=None):
        self.edits.append({"content": content, "view": view})

    def is_done(self) -> bool:
        return False


class DummyFollowup:
    def __init__(self) -> None:
        self.sent = []

    async def send(self, content: str | None = None, **kwargs):
        self.sent.append({"content": content, **kwargs})


class DummyUser:
    def __init__(self, user_id: int) -> None:
        self.id = user_id


class DummyInteraction:
    def __init__(self, user_id: int = 999) -> None:
        self.user = DummyUser(user_id)
        self.response = DummyResponse()
        self.followup = DummyFollowup()
        self.client = object()


def _future_close() -> datetime:
    return datetime.now(UTC) + timedelta(hours=2)


@pytest.mark.asyncio
async def test_check_in_marks_signup(monkeypatch):
    controller = ArkConfirmationController(match_id=1, config={"PlayersCap": 30, "SubsCap": 15})
    interaction = DummyInteraction()

    async def _get_match(match_id):
        return {
            "MatchId": 1,
            "Alliance": "K98",
            "ArkWeekendDate": datetime(2026, 3, 7, tzinfo=UTC).date(),
            "MatchDay": "Sat",
            "MatchTimeUtc": datetime(2026, 3, 7, 11, 0, tzinfo=UTC).time(),
            "SignupCloseUtc": _future_close(),
            "Status": "Locked",
        }

    async def _get_roster(match_id):
        return [
            {
                "GovernorId": 2441482,
                "GovernorNameSnapshot": "Chrislos",
                "DiscordUserId": interaction.user.id,
                "SlotType": "Player",
            }
        ]

    called = {"check_in": None, "audit": False, "refresh": False}

    async def _mark_checked_in(match_id, governor_id, checked_in_at_utc):
        called["check_in"] = (match_id, governor_id, checked_in_at_utc)
        return True

    async def _audit(*_a, **_k):
        called["audit"] = True
        return 1

    async def _refresh(*_a, **_k):
        called["refresh"] = True
        return True

    monkeypatch.setattr("ark.confirmation_flow.get_match", _get_match)
    monkeypatch.setattr("ark.confirmation_flow.get_roster", _get_roster)
    monkeypatch.setattr("ark.confirmation_flow.mark_checked_in", _mark_checked_in)
    monkeypatch.setattr("ark.confirmation_flow.insert_audit_log", _audit)
    monkeypatch.setattr(controller, "refresh_confirmation_message", _refresh)

    await controller.check_in(interaction)

    assert called["check_in"] is not None
    assert called["audit"] is True
    assert called["refresh"] is True
    assert interaction.response.sent


@pytest.mark.asyncio
async def test_check_in_prompts_for_governor_selection(monkeypatch):
    controller = ArkConfirmationController(match_id=2, config={"PlayersCap": 30, "SubsCap": 15})
    interaction = DummyInteraction()

    async def _get_match(match_id):
        return {
            "MatchId": 2,
            "Alliance": "K98",
            "ArkWeekendDate": datetime(2026, 3, 7, tzinfo=UTC).date(),
            "MatchDay": "Sat",
            "MatchTimeUtc": datetime(2026, 3, 7, 11, 0, tzinfo=UTC).time(),
            "SignupCloseUtc": _future_close(),
            "Status": "Locked",
        }

    async def _get_roster(match_id):
        return [
            {
                "GovernorId": 2441482,
                "GovernorNameSnapshot": "Chrislos",
                "DiscordUserId": interaction.user.id,
                "SlotType": "Player",
            },
            {
                "GovernorId": 2510418,
                "GovernorNameSnapshot": "Scrooge M",
                "DiscordUserId": interaction.user.id,
                "SlotType": "Sub",
            },
        ]

    captured = {"view": None}

    class DummyGovSelectView:
        def __init__(self, *, author_id, options, on_select, timeout):
            captured["view"] = {"author_id": author_id, "options": options, "timeout": timeout}

    monkeypatch.setattr("ark.confirmation_flow.get_match", _get_match)
    monkeypatch.setattr("ark.confirmation_flow.get_roster", _get_roster)
    monkeypatch.setattr("ark.confirmation_flow.ArkGovernorSelectView", DummyGovSelectView)

    await controller.check_in(interaction)

    assert captured["view"] is not None
    assert len(captured["view"]["options"]) == 2
    assert interaction.response.sent
    assert "Select which governor to check in" in interaction.response.sent[-1]["content"]


@pytest.mark.asyncio
async def test_emergency_withdraw_triggers_promotion(monkeypatch):
    controller = ArkConfirmationController(match_id=3, config={"PlayersCap": 30, "SubsCap": 15})
    interaction = DummyInteraction()

    async def _get_match(match_id):
        return {
            "MatchId": 3,
            "Alliance": "K98",
            "ArkWeekendDate": datetime(2026, 3, 7, tzinfo=UTC).date(),
            "MatchDay": "Sat",
            "MatchTimeUtc": datetime(2026, 3, 7, 11, 0, tzinfo=UTC).time(),
            "SignupCloseUtc": _future_close(),
            "Status": "Locked",
        }

    async def _get_roster(match_id):
        return [
            {
                "GovernorId": 2441482,
                "GovernorNameSnapshot": "Chrislos",
                "DiscordUserId": interaction.user.id,
                "SlotType": "Player",
            }
        ]

    called = {"withdraw": None, "audit": False, "promote": False, "refresh": False}

    async def _withdraw(match_id, governor_id, actor_discord_id):
        called["withdraw"] = (match_id, governor_id, actor_discord_id)
        return True

    async def _audit(*_a, **_k):
        called["audit"] = True
        return 1

    async def _promote(*_a, **_k):
        called["promote"] = True

    async def _refresh(*_a, **_k):
        called["refresh"] = True
        return True

    monkeypatch.setattr("ark.confirmation_flow.get_match", _get_match)
    monkeypatch.setattr("ark.confirmation_flow.get_roster", _get_roster)
    monkeypatch.setattr("ark.confirmation_flow.mark_emergency_withdraw", _withdraw)
    monkeypatch.setattr("ark.confirmation_flow.insert_audit_log", _audit)
    monkeypatch.setattr(
        "ark.confirmation_flow.ArkRegistrationController._maybe_promote_sub", _promote
    )
    monkeypatch.setattr(controller, "refresh_confirmation_message", _refresh)

    await controller.emergency_withdraw(interaction)

    assert called["withdraw"] == (3, 2441482, interaction.user.id)
    assert called["audit"] is True
    assert called["promote"] is True
    assert called["refresh"] is True
    assert interaction.response.sent


@pytest.mark.asyncio
async def test_emergency_withdraw_updates_field(monkeypatch):
    controller = ArkConfirmationController(match_id=4, config={"PlayersCap": 30, "SubsCap": 15})
    interaction = DummyInteraction()

    async def _get_match(match_id):
        return {
            "MatchId": 4,
            "Alliance": "K98",
            "ArkWeekendDate": datetime(2026, 3, 7, tzinfo=UTC).date(),
            "MatchDay": "Sat",
            "MatchTimeUtc": datetime(2026, 3, 7, 11, 0, tzinfo=UTC).time(),
            "SignupCloseUtc": _future_close(),
            "Status": "Locked",
        }

    async def _get_roster(match_id):
        return [
            {
                "GovernorId": 2441482,
                "GovernorNameSnapshot": "Chrislos",
                "DiscordUserId": interaction.user.id,
                "SlotType": "Player",
            }
        ]

    async def _withdraw(match_id, governor_id, actor_discord_id):
        return True

    async def _audit(*_a, **_k):
        return 1

    async def _promote(*_a, **_k):
        return None

    captured = {"updates": None}

    async def _refresh(*_a, **_k):
        captured["updates"] = _k.get("updates")
        return True

    monkeypatch.setattr("ark.confirmation_flow.get_match", _get_match)
    monkeypatch.setattr("ark.confirmation_flow.get_roster", _get_roster)
    monkeypatch.setattr("ark.confirmation_flow.mark_emergency_withdraw", _withdraw)
    monkeypatch.setattr("ark.confirmation_flow.insert_audit_log", _audit)
    monkeypatch.setattr(
        "ark.confirmation_flow.ArkRegistrationController._maybe_promote_sub", _promote
    )
    monkeypatch.setattr(controller, "refresh_confirmation_message", _refresh)

    await controller.emergency_withdraw(interaction)

    assert captured["updates"] is not None
    assert "Emergency withdraw" in captured["updates"][0]


@pytest.mark.asyncio
async def test_emergency_withdraw_prompts_for_governor_selection(monkeypatch):
    controller = ArkConfirmationController(match_id=5, config={"PlayersCap": 30, "SubsCap": 15})
    interaction = DummyInteraction()

    async def _get_match(match_id):
        return {
            "MatchId": 5,
            "Alliance": "K98",
            "ArkWeekendDate": datetime(2026, 3, 7, tzinfo=UTC).date(),
            "MatchDay": "Sat",
            "MatchTimeUtc": datetime(2026, 3, 7, 11, 0, tzinfo=UTC).time(),
            "SignupCloseUtc": _future_close(),
            "Status": "Locked",
        }

    async def _get_roster(match_id):
        return [
            {
                "GovernorId": 2441482,
                "GovernorNameSnapshot": "Chrislos",
                "DiscordUserId": interaction.user.id,
                "SlotType": "Player",
            },
            {
                "GovernorId": 2510418,
                "GovernorNameSnapshot": "Scrooge M",
                "DiscordUserId": interaction.user.id,
                "SlotType": "Sub",
            },
        ]

    captured = {"view": None}

    class DummyGovSelectView:
        def __init__(self, *, author_id, options, on_select, timeout):
            captured["view"] = {"author_id": author_id, "options": options, "timeout": timeout}

    monkeypatch.setattr("ark.confirmation_flow.get_match", _get_match)
    monkeypatch.setattr("ark.confirmation_flow.get_roster", _get_roster)
    monkeypatch.setattr("ark.confirmation_flow.ArkGovernorSelectView", DummyGovSelectView)

    await controller.emergency_withdraw(interaction)

    assert captured["view"] is not None
    assert len(captured["view"]["options"]) == 2
    assert interaction.response.sent
    assert "Select which governor to withdraw" in interaction.response.sent[-1]["content"]
