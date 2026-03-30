from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from mge import mge_signup_service
from ui.views.mge_signup_view import _member_role_ids


def _event(mode="controlled", status="signup_open", close_offset_hours=1):
    return {
        "EventId": 1,
        "VariantName": "Infantry",
        "EventMode": mode,
        "Status": status,
        "SignupCloseUtc": datetime.now(UTC) + timedelta(hours=close_offset_hours),
    }


def test_signup_blocked_open_mode(monkeypatch):
    monkeypatch.setattr(
        "mge.dal.mge_signup_dal.fetch_event_signup_context",
        lambda event_id: _event(mode="open"),
    )
    result = mge_signup_service.create_signup(
        event_id=1,
        actor_discord_id=1,
        actor_role_ids=set(),
        admin_role_ids={999},
        governor_id=100,
        governor_name_snapshot="Gov",
        request_priority="High",
        preferred_rank_band="1-5",
        requested_commander_id=1,
        current_heads=100,
        kingdom_role=None,
        gear_text=None,
        armament_text=None,
    )
    assert not result.success


def test_signup_blocked_published(monkeypatch):
    monkeypatch.setattr(
        "mge.dal.mge_signup_dal.fetch_event_signup_context",
        lambda event_id: _event(status="published"),
    )
    result = mge_signup_service.create_signup(
        event_id=1,
        actor_discord_id=1,
        actor_role_ids=set(),
        admin_role_ids={999},
        governor_id=100,
        governor_name_snapshot="Gov",
        request_priority="High",
        preferred_rank_band="1-5",
        requested_commander_id=1,
        current_heads=100,
        kingdom_role=None,
        gear_text=None,
        armament_text=None,
    )
    assert not result.success


class _FakeRole:
    def __init__(self, role_id: int):
        self.id = role_id


class _FakeMember:
    def __init__(self, user_id: int, roles: list[_FakeRole]):
        self.id = user_id
        self.roles = roles


class _FakeGuild:
    def __init__(self, member):
        self._member = member

    def get_member(self, _user_id: int):
        return self._member


def test_member_role_ids_from_member_user(monkeypatch):
    import discord

    class FakeDiscordMember(discord.Member):  # pragma: no cover
        pass

    member = _FakeMember(1, [_FakeRole(10), _FakeRole(20)])
    interaction = SimpleNamespace(user=member, guild=None)

    monkeypatch.setattr("discord.Member", _FakeMember)
    role_ids = _member_role_ids(interaction)
    assert role_ids == {10, 20}


def test_member_role_ids_falls_back_to_guild_lookup(monkeypatch):
    user = SimpleNamespace(id=123)
    member = _FakeMember(123, [_FakeRole(5)])
    guild = _FakeGuild(member)
    interaction = SimpleNamespace(user=user, guild=guild)

    monkeypatch.setattr("discord.Member", _FakeMember)
    role_ids = _member_role_ids(interaction)
    assert role_ids == {5}


def test_member_role_ids_empty_when_no_member(monkeypatch):
    user = SimpleNamespace(id=123)
    guild = _FakeGuild(None)
    interaction = SimpleNamespace(user=user, guild=guild)

    monkeypatch.setattr("discord.Member", _FakeMember)
    role_ids = _member_role_ids(interaction)
    assert role_ids == set()
