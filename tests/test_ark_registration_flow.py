from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from ark.registration_flow import ArkRegistrationController


class DummyResponse:
    def __init__(self) -> None:
        self.deferred = 0
        self.sent = []
        self.edits = []

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
async def test_join_player_adds_signup(monkeypatch):
    controller = ArkRegistrationController(match_id=1, config={"PlayersCap": 30, "SubsCap": 15})
    interaction = DummyInteraction()

    async def _prompt(interaction, *, accounts, on_select, heading, only_governor_ids=None):
        if only_governor_ids:
            await on_select(interaction, next(iter(only_governor_ids)))
        else:
            await on_select(interaction, "2441482")

    async def _validate(interaction, governor_id):
        return True

    async def _get_match(match_id):
        return {
            "MatchId": 1,
            "Alliance": "K98",
            "ArkWeekendDate": datetime(2026, 3, 7, tzinfo=UTC).date(),
            "MatchDay": "Sat",
            "MatchTimeUtc": datetime(2026, 3, 7, 11, 0, tzinfo=UTC).time(),
            "SignupCloseUtc": _future_close(),
            "Status": "Scheduled",
        }

    async def _get_roster(match_id):
        return []

    called = {"add": False, "audit": False, "refresh": False}

    async def _add_signup(**kwargs):
        called["add"] = True
        return 123

    async def _audit(*_a, **_k):
        called["audit"] = True
        return 1

    async def _refresh(*_a, **_k):
        called["refresh"] = True

    monkeypatch.setattr(controller, "_prompt_governor_selection", _prompt)
    monkeypatch.setattr(controller, "_validate_governor", _validate)
    monkeypatch.setattr("ark.registration_flow.get_match", _get_match)
    monkeypatch.setattr("ark.registration_flow.get_roster", _get_roster)
    monkeypatch.setattr("ark.registration_flow.add_signup", _add_signup)
    monkeypatch.setattr("ark.registration_flow.insert_audit_log", _audit)
    monkeypatch.setattr(controller, "refresh_registration_message", _refresh)

    monkeypatch.setattr(
        "ark.registration_flow._get_user_accounts",
        lambda _user_id: {"Main": {"GovernorID": "2441482", "GovernorName": "Chrislos"}},
    )

    await controller.join_player(interaction)

    assert called["add"] is True
    assert called["audit"] is True
    assert called["refresh"] is True
    assert interaction.response.edits


@pytest.mark.asyncio
async def test_leave_marks_withdrawn(monkeypatch):
    controller = ArkRegistrationController(match_id=2, config={"PlayersCap": 30, "SubsCap": 15})
    interaction = DummyInteraction()

    async def _prompt(interaction, *, accounts, on_select, heading, only_governor_ids=None):
        await on_select(interaction, "2441482")

    monkeypatch.setattr(controller, "_prompt_governor_selection", _prompt)

    monkeypatch.setattr(
        "ark.registration_flow._get_user_accounts",
        lambda _user_id: {"Main": {"GovernorID": "2441482", "GovernorName": "Chrislos"}},
    )

    async def _get_match(match_id):
        return {
            "MatchId": 2,
            "Alliance": "K98",
            "ArkWeekendDate": datetime(2026, 3, 7, tzinfo=UTC).date(),
            "MatchDay": "Sat",
            "MatchTimeUtc": datetime(2026, 3, 7, 11, 0, tzinfo=UTC).time(),
            "SignupCloseUtc": _future_close(),
            "Status": "Scheduled",
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

    called = {"remove": None, "audit": False, "refresh": False}

    async def _remove_signup(match_id, governor_id, status, actor_discord_id):
        called["remove"] = (match_id, governor_id, status, actor_discord_id)
        return True

    async def _audit(*_a, **_k):
        called["audit"] = True
        return 1

    async def _refresh(*_a, **_k):
        called["refresh"] = True

    monkeypatch.setattr("ark.registration_flow.get_match", _get_match)
    monkeypatch.setattr("ark.registration_flow.get_roster", _get_roster)
    monkeypatch.setattr("ark.registration_flow.remove_signup", _remove_signup)
    monkeypatch.setattr("ark.registration_flow.insert_audit_log", _audit)
    monkeypatch.setattr(controller, "refresh_registration_message", _refresh)

    await controller.leave(interaction)

    assert called["remove"] == (2, 2441482, "Withdrawn", interaction.user.id)
    assert called["audit"] is True
    assert called["refresh"] is True


@pytest.mark.asyncio
async def test_switch_updates_governor(monkeypatch):
    controller = ArkRegistrationController(match_id=3, config={"PlayersCap": 30, "SubsCap": 15})
    interaction = DummyInteraction()

    async def _prompt(interaction, *, accounts, on_select, heading, only_governor_ids=None):
        if only_governor_ids:
            await on_select(interaction, next(iter(only_governor_ids)))
        else:
            await on_select(interaction, "2510418")

    async def _validate(interaction, governor_id):
        return True

    async def _get_match(match_id):
        return {
            "MatchId": 3,
            "Alliance": "K98",
            "ArkWeekendDate": datetime(2026, 3, 7, tzinfo=UTC).date(),
            "MatchDay": "Sat",
            "MatchTimeUtc": datetime(2026, 3, 7, 11, 0, tzinfo=UTC).time(),
            "SignupCloseUtc": _future_close(),
            "Status": "Scheduled",
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

    async def _no_conflict(*_a, **_k):
        return None

    called = {"switch": None, "audit": False, "refresh": False}

    async def _switch(
        match_id, old_governor_id, new_governor_id, new_governor_name, discord_user_id
    ):
        called["switch"] = (
            match_id,
            old_governor_id,
            new_governor_id,
            new_governor_name,
            discord_user_id,
        )
        return True

    async def _audit(*_a, **_k):
        called["audit"] = True
        return 1

    async def _refresh(*_a, **_k):
        called["refresh"] = True

    monkeypatch.setattr(controller, "_prompt_governor_selection", _prompt)
    monkeypatch.setattr(controller, "_validate_governor", _validate)
    monkeypatch.setattr("ark.registration_flow.get_match", _get_match)
    monkeypatch.setattr("ark.registration_flow.get_roster", _get_roster)
    monkeypatch.setattr("ark.registration_flow.find_active_signup_for_weekend", _no_conflict)
    monkeypatch.setattr("ark.registration_flow.switch_signup_governor", _switch)
    monkeypatch.setattr("ark.registration_flow.insert_audit_log", _audit)
    monkeypatch.setattr(controller, "refresh_registration_message", _refresh)

    monkeypatch.setattr(
        "ark.registration_flow._get_user_accounts",
        lambda _user_id: {
            "Main": {"GovernorID": "2441482", "GovernorName": "Chrislos"},
            "Alt 2": {"GovernorID": "2510418", "GovernorName": "Scrooge M"},
        },
    )

    await controller.switch(interaction)

    assert called["switch"] == (3, 2441482, 2510418, "Scrooge M", interaction.user.id)
    assert called["audit"] is True
    assert called["refresh"] is True


@pytest.mark.asyncio
async def test_join_player_blocks_when_signup_closed(monkeypatch):
    controller = ArkRegistrationController(match_id=10, config={"PlayersCap": 30, "SubsCap": 15})
    interaction = DummyInteraction()

    past = datetime.now(UTC) - timedelta(hours=1)

    async def _get_match(match_id):
        return {
            "MatchId": 10,
            "Alliance": "K98",
            "ArkWeekendDate": datetime(2026, 3, 7, tzinfo=UTC).date(),
            "MatchDay": "Sat",
            "MatchTimeUtc": datetime(2026, 3, 7, 11, 0, tzinfo=UTC).time(),
            "SignupCloseUtc": past,
            "Status": "Scheduled",
        }

    async def _get_roster(match_id):
        return []

    called = {"prompt": False}

    async def _prompt(*_a, **_k):
        called["prompt"] = True

    monkeypatch.setattr("ark.registration_flow.get_match", _get_match)
    monkeypatch.setattr("ark.registration_flow.get_roster", _get_roster)
    monkeypatch.setattr(controller, "_prompt_governor_selection", _prompt)

    await controller.join_player(interaction)

    assert called["prompt"] is False
    assert interaction.followup.sent
    assert "Signups are closed" in interaction.followup.sent[-1]["content"]


@pytest.mark.asyncio
async def test_join_player_blocks_when_player_cap_full(monkeypatch):
    controller = ArkRegistrationController(match_id=11, config={"PlayersCap": 2, "SubsCap": 15})
    interaction = DummyInteraction()

    async def _get_match(match_id):
        return {
            "MatchId": 11,
            "Alliance": "K98",
            "ArkWeekendDate": datetime(2026, 3, 7, tzinfo=UTC).date(),
            "MatchDay": "Sat",
            "MatchTimeUtc": datetime(2026, 3, 7, 11, 0, tzinfo=UTC).time(),
            "SignupCloseUtc": _future_close(),
            "Status": "Scheduled",
        }

    async def _get_roster(match_id):
        return [
            {"SlotType": "Player"},
            {"SlotType": "Player"},
        ]

    called = {"prompt": False}

    async def _prompt(*_a, **_k):
        called["prompt"] = True

    monkeypatch.setattr("ark.registration_flow.get_match", _get_match)
    monkeypatch.setattr("ark.registration_flow.get_roster", _get_roster)
    monkeypatch.setattr(controller, "_prompt_governor_selection", _prompt)

    await controller.join_player(interaction)

    assert called["prompt"] is False
    assert interaction.followup.sent
    assert "Player slots are full" in interaction.followup.sent[-1]["content"]


@pytest.mark.asyncio
async def test_join_sub_blocks_when_sub_cap_full(monkeypatch):
    controller = ArkRegistrationController(match_id=12, config={"PlayersCap": 2, "SubsCap": 1})
    interaction = DummyInteraction()

    async def _get_match(match_id):
        return {
            "MatchId": 12,
            "Alliance": "K98",
            "ArkWeekendDate": datetime(2026, 3, 7, tzinfo=UTC).date(),
            "MatchDay": "Sat",
            "MatchTimeUtc": datetime(2026, 3, 7, 11, 0, tzinfo=UTC).time(),
            "SignupCloseUtc": _future_close(),
            "Status": "Scheduled",
        }

    async def _get_roster(match_id):
        return [
            {"SlotType": "Player"},
            {"SlotType": "Player"},
            {"SlotType": "Sub"},
        ]

    called = {"prompt": False}

    async def _prompt(*_a, **_k):
        called["prompt"] = True

    monkeypatch.setattr("ark.registration_flow.get_match", _get_match)
    monkeypatch.setattr("ark.registration_flow.get_roster", _get_roster)
    monkeypatch.setattr(controller, "_prompt_governor_selection", _prompt)

    await controller.join_sub(interaction)

    assert called["prompt"] is False
    assert interaction.followup.sent
    assert "Sub slots are full" in interaction.followup.sent[-1]["content"]


@pytest.mark.asyncio
async def test_join_player_blocks_duplicate_weekend_governor(monkeypatch):
    controller = ArkRegistrationController(match_id=13, config={"PlayersCap": 30, "SubsCap": 15})
    interaction = DummyInteraction()

    async def _prompt(interaction, *, accounts, on_select, heading, only_governor_ids=None):
        if only_governor_ids:
            await on_select(interaction, next(iter(only_governor_ids)))
        else:
            await on_select(interaction, "2441482")

    async def _validate(self, interaction, governor_id):
        return True

    async def _get_match(match_id):
        return {
            "MatchId": 13,
            "Alliance": "K98",
            "ArkWeekendDate": datetime(2026, 3, 7, tzinfo=UTC).date(),
            "MatchDay": "Sat",
            "MatchTimeUtc": datetime(2026, 3, 7, 11, 0, tzinfo=UTC).time(),
            "SignupCloseUtc": _future_close(),
            "Status": "Scheduled",
        }

    async def _get_roster(match_id):
        return []

    async def _conflict(*_a, **_k):
        return {"MatchId": 99, "Alliance": "OTHER"}

    called = {"add": False}

    async def _add_signup(**_k):
        called["add"] = True
        return 1

    monkeypatch.setattr(controller, "_prompt_governor_selection", _prompt)
    monkeypatch.setattr(controller, "_validate_governor", _validate)
    monkeypatch.setattr("ark.registration_flow.get_match", _get_match)
    monkeypatch.setattr("ark.registration_flow.get_roster", _get_roster)
    monkeypatch.setattr("ark.registration_flow.find_active_signup_for_weekend", _conflict)
    monkeypatch.setattr("ark.registration_flow.add_signup", _add_signup)

    monkeypatch.setattr(
        "ark.registration_flow._get_user_accounts",
        lambda _user_id: {"Main": {"GovernorID": "2441482", "GovernorName": "Chrislos"}},
    )

    await controller.join_player(interaction)

    assert called["add"] is False
    assert interaction.response.sent
    assert "another match this Ark weekend" in interaction.response.sent[-1]["content"]


@pytest.mark.asyncio
async def test_join_sub_blocks_when_players_not_full(monkeypatch):
    controller = ArkRegistrationController(match_id=14, config={"PlayersCap": 2, "SubsCap": 1})
    interaction = DummyInteraction()

    async def _get_match(match_id):
        return {
            "MatchId": 14,
            "Alliance": "K98",
            "ArkWeekendDate": datetime(2026, 3, 7, tzinfo=UTC).date(),
            "MatchDay": "Sat",
            "MatchTimeUtc": datetime(2026, 3, 7, 11, 0, tzinfo=UTC).time(),
            "SignupCloseUtc": _future_close(),
            "Status": "Scheduled",
        }

    async def _get_roster(match_id):
        return [
            {"SlotType": "Player"},
        ]

    called = {"prompt": False}

    async def _prompt(*_a, **_k):
        called["prompt"] = True

    monkeypatch.setattr("ark.registration_flow.get_match", _get_match)
    monkeypatch.setattr("ark.registration_flow.get_roster", _get_roster)
    monkeypatch.setattr(controller, "_prompt_governor_selection", _prompt)

    await controller.join_sub(interaction)

    assert called["prompt"] is False
    assert interaction.followup.sent
    assert (
        "Sub slots are only available once player slots are full"
        in interaction.followup.sent[-1]["content"]
    )


@pytest.mark.asyncio
async def test_switch_blocks_when_governor_already_signed(monkeypatch):
    controller = ArkRegistrationController(match_id=15, config={"PlayersCap": 30, "SubsCap": 15})
    interaction = DummyInteraction()

    match = {
        "MatchId": 15,
        "Alliance": "K98",
        "ArkWeekendDate": datetime(2026, 3, 7, tzinfo=UTC).date(),
        "MatchDay": "Sat",
        "MatchTimeUtc": datetime(2026, 3, 7, 11, 0, tzinfo=UTC).time(),
        "SignupCloseUtc": _future_close(),
        "Status": "Scheduled",
    }

    roster = [
        {
            "GovernorId": 2441482,
            "GovernorNameSnapshot": "Chrislos",
            "DiscordUserId": interaction.user.id,
            "SlotType": "Player",
        },
        {
            "GovernorId": 2510418,
            "GovernorNameSnapshot": "Scrooge M",
            "DiscordUserId": 123,
            "SlotType": "Player",
        },
    ]

    monkeypatch.setattr(controller, "_validate_governor", lambda *_a, **_k: True)
    monkeypatch.setattr(
        "ark.registration_flow.find_active_signup_for_weekend", lambda *_a, **_k: None
    )

    await controller._apply_switch(interaction, match, roster, {}, "2441482", "2510418")

    assert interaction.response.sent
    assert "already active in this match" in interaction.response.sent[-1]["content"]


@pytest.mark.asyncio
async def test_switch_blocks_when_same_governor_selected(monkeypatch):
    controller = ArkRegistrationController(match_id=16, config={"PlayersCap": 30, "SubsCap": 15})
    interaction = DummyInteraction()

    match = {
        "MatchId": 16,
        "Alliance": "K98",
        "ArkWeekendDate": datetime(2026, 3, 7, tzinfo=UTC).date(),
        "MatchDay": "Sat",
        "MatchTimeUtc": datetime(2026, 3, 7, 11, 0, tzinfo=UTC).time(),
        "SignupCloseUtc": _future_close(),
        "Status": "Scheduled",
    }

    roster = [
        {
            "GovernorId": 2441482,
            "GovernorNameSnapshot": "Chrislos",
            "DiscordUserId": interaction.user.id,
            "SlotType": "Player",
        }
    ]

    monkeypatch.setattr(controller, "_validate_governor", lambda *_a, **_k: True)

    await controller._apply_switch(interaction, match, roster, {}, "2441482", "2441482")

    assert interaction.response.sent
    assert "already signed up with that governor" in interaction.response.sent[-1]["content"]


@pytest.mark.asyncio
async def test_join_blocks_when_user_already_signed_up(monkeypatch):
    controller = ArkRegistrationController(match_id=17, config={"PlayersCap": 30, "SubsCap": 15})
    interaction = DummyInteraction()

    async def _get_match(match_id):
        return {
            "MatchId": 17,
            "Alliance": "K98",
            "ArkWeekendDate": datetime(2026, 3, 7, tzinfo=UTC).date(),
            "MatchDay": "Sat",
            "MatchTimeUtc": datetime(2026, 3, 7, 11, 0, tzinfo=UTC).time(),
            "SignupCloseUtc": _future_close(),
            "Status": "Scheduled",
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

    called = {"prompt": False}

    async def _prompt(interaction, *, accounts, on_select, heading, only_governor_ids=None):
        called["prompt"] = True
        await on_select(interaction, "2441482")

    monkeypatch.setattr("ark.registration_flow.get_match", _get_match)
    monkeypatch.setattr("ark.registration_flow.get_roster", _get_roster)
    monkeypatch.setattr(controller, "_prompt_governor_selection", _prompt)

    await controller.join_player(interaction)

    assert called["prompt"] is True
    assert interaction.response.sent
    assert "already signed up" in interaction.response.sent[-1]["content"]
