from __future__ import annotations

from types import SimpleNamespace

import pytest

from core import leadership_player_permissions as permissions


class _Member:
    def __init__(self, user_id: int, roles=()) -> None:
        self.id = user_id
        self.roles = tuple(roles)


def _interaction(*, user, channel_id=200, parent_id=None, guild_id=98):
    channel = SimpleNamespace(id=channel_id, parent_id=parent_id, parent=None)
    guild = SimpleNamespace(id=guild_id) if guild_id is not None else None
    return SimpleNamespace(user=user, channel=channel, guild=guild)


def _configure(monkeypatch) -> None:
    monkeypatch.setattr(permissions, "ADMIN_USER_ID", 1)
    monkeypatch.setattr(permissions, "GUILD_ID", 98)
    monkeypatch.setattr(permissions, "LEADERSHIP_CHANNEL_ID", 200)
    monkeypatch.setattr(permissions, "NOTIFY_CHANNEL_ID", 300)
    monkeypatch.setattr(permissions, "LEADERSHIP_ROLE_IDS", [10, 11])
    monkeypatch.setattr(permissions.discord, "Member", _Member)


def test_leadership_role_id_is_allowed_only_in_leadership_channel_or_child(monkeypatch) -> None:
    _configure(monkeypatch)
    member = _Member(2, [SimpleNamespace(id=10, name="Anything")])

    channel = permissions.authorize_leadership_player_interaction(_interaction(user=member))
    child = permissions.authorize_leadership_player_interaction(
        _interaction(user=member, channel_id=201, parent_id=200)
    )
    notify = permissions.authorize_leadership_player_interaction(
        _interaction(user=member, channel_id=300)
    )

    assert channel.allowed and channel.basis == "LEADERSHIP_ROLE_ID" and channel.role_id == 10
    assert child.allowed
    assert not notify.allowed


def test_admin_is_allowed_in_leadership_and_notify_but_nowhere_else(monkeypatch) -> None:
    _configure(monkeypatch)
    admin = _Member(1)

    assert permissions.authorize_leadership_player_interaction(
        _interaction(user=admin, channel_id=300)
    ).allowed
    assert permissions.authorize_leadership_player_interaction(
        _interaction(user=admin, channel_id=301, parent_id=300)
    ).allowed
    denied = permissions.authorize_leadership_player_interaction(
        _interaction(user=admin, channel_id=400)
    )
    assert not denied.allowed
    assert denied.error_code == "ADMIN_CHANNEL_NOT_ALLOWED"


def test_role_name_only_dm_wrong_guild_and_other_channel_fail_closed(monkeypatch) -> None:
    _configure(monkeypatch)
    named_only = _Member(2, [SimpleNamespace(id=99, name="Kingdom Leadership")])

    role_denied = permissions.authorize_leadership_player_interaction(_interaction(user=named_only))
    dm_denied = permissions.authorize_leadership_player_interaction(
        _interaction(user=named_only, guild_id=None)
    )
    guild_denied = permissions.authorize_leadership_player_interaction(
        _interaction(user=named_only, guild_id=99)
    )
    channel_denied = permissions.authorize_leadership_player_interaction(
        _interaction(user=named_only, channel_id=400)
    )

    assert role_denied.error_code == "LEADERSHIP_ROLE_REQUIRED"
    assert dm_denied.error_code == "DM_NOT_ALLOWED"
    assert guild_denied.error_code == "GUILD_NOT_ALLOWED"
    assert channel_denied.error_code == "LEADERSHIP_CHANNEL_REQUIRED"


def test_permission_recheck_observes_role_removal(monkeypatch) -> None:
    _configure(monkeypatch)
    member = _Member(2, [SimpleNamespace(id=10)])
    interaction = _interaction(user=member)

    assert permissions.authorize_leadership_player_interaction(interaction).allowed
    member.roles = ()
    assert not permissions.authorize_leadership_player_interaction(interaction).allowed


@pytest.mark.asyncio
async def test_final_reauthorization_fetches_current_member_roles(monkeypatch) -> None:
    _configure(monkeypatch)
    stale_member = _Member(2, [SimpleNamespace(id=10)])
    current_member = _Member(2, [SimpleNamespace(id=11)])
    fetched: list[int] = []

    async def fetch_member(actor_id: int):
        fetched.append(actor_id)
        return current_member

    guild = SimpleNamespace(id=98, fetch_member=fetch_member)
    interaction = SimpleNamespace(
        user=stale_member,
        guild=guild,
        channel=SimpleNamespace(id=200, parent_id=None, parent=None),
    )

    result = await permissions.reauthorize_leadership_player_interaction(interaction)

    assert fetched == [2]
    assert result.allowed
    assert result.role_id == 11


@pytest.mark.asyncio
async def test_final_reauthorization_fails_closed_when_member_is_gone(monkeypatch) -> None:
    _configure(monkeypatch)
    stale_member = _Member(2, [SimpleNamespace(id=10)])

    async def fetch_member(_actor_id: int):
        return None

    guild = SimpleNamespace(id=98, fetch_member=fetch_member)
    interaction = SimpleNamespace(
        user=stale_member,
        guild=guild,
        channel=SimpleNamespace(id=200, parent_id=None, parent=None),
    )

    result = await permissions.reauthorize_leadership_player_interaction(interaction)

    assert not result.allowed
    assert result.error_code == "MEMBER_NO_LONGER_PRESENT"
