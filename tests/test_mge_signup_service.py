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


def _patch_signup_happy_path(monkeypatch):
    monkeypatch.setattr(
        "mge.dal.mge_signup_dal.fetch_event_signup_context",
        lambda event_id: _event(),
    )
    monkeypatch.setattr(
        "mge.dal.mge_signup_dal.fetch_active_signup_by_event_governor",
        lambda event_id, governor_id: None,
    )
    monkeypatch.setattr(
        "mge.mge_signup_service._commander_options_for_event_variant",
        lambda variant_name: {1: "Cmdr"},
    )
    monkeypatch.setattr(
        "mge.dal.mge_signup_dal.insert_signup_audit",
        lambda **kwargs: None,
    )


def test_admin_signup_resolves_discord_identity_from_registry(monkeypatch):
    _patch_signup_happy_path(monkeypatch)
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "mge.mge_signup_service.get_discord_user_for_governor",
        lambda governor_id: {"DiscordUserID": 777777, "DiscordName": "Player"},
    )
    monkeypatch.setattr(
        "mge.dal.mge_signup_dal.insert_signup",
        lambda **kwargs: captured.update(kwargs) or 42,
    )

    result = mge_signup_service.create_signup(
        event_id=1,
        actor_discord_id=123,
        actor_role_ids={999},
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

    assert result.success
    assert captured["discord_user_id"] == 777777


def test_admin_signup_leaves_discord_identity_null_when_registry_missing(monkeypatch):
    _patch_signup_happy_path(monkeypatch)
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "mge.mge_signup_service.get_discord_user_for_governor",
        lambda governor_id: None,
    )
    monkeypatch.setattr(
        "mge.dal.mge_signup_dal.insert_signup",
        lambda **kwargs: captured.update(kwargs) or 42,
    )

    result = mge_signup_service.create_signup(
        event_id=1,
        actor_discord_id=123,
        actor_role_ids={999},
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

    assert result.success
    assert captured["discord_user_id"] is None


def test_self_signup_keeps_actor_discord_identity(monkeypatch):
    _patch_signup_happy_path(monkeypatch)
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "mge.mge_signup_service._is_governor_linked_to_user",
        lambda discord_user_id, governor_id: True,
    )
    monkeypatch.setattr(
        "mge.mge_signup_service.get_discord_user_for_governor",
        lambda governor_id: {"DiscordUserID": 777777, "DiscordName": "Someone else"},
    )
    monkeypatch.setattr(
        "mge.dal.mge_signup_dal.insert_signup",
        lambda **kwargs: captured.update(kwargs) or 42,
    )

    result = mge_signup_service.create_signup(
        event_id=1,
        actor_discord_id=123,
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

    assert result.success
    assert captured["discord_user_id"] == 123


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


# --- Priority (Rank) ordering integration tests ---


def test_signup_ordering_with_priority_rank_mapping_produces_correct_sort_weight_sequence(
    monkeypatch,
):
    """
    Create signups with each Priority(Rank) combination and verify that the sort_weight
    sequence produced by signup_auto_sort_key matches the expected order:
    High(1-5) < Medium(6-10) < Low(11-15) < Low(no_preference) < legacy/unknown.
    """
    from datetime import UTC, datetime

    from mge.mge_simplified_flow_service import signup_auto_sort_key

    rows = [
        {
            "SignupId": 5,
            "RequestPriority": "OldLegacy",
            "PreferredRankBand": "custom",
            "LatestKVKRank": 1,
            "SignupCreatedUtc": datetime(2026, 4, 1, tzinfo=UTC),
        },
        {
            "SignupId": 4,
            "RequestPriority": "Low",
            "PreferredRankBand": "no_preference",
            "LatestKVKRank": 1,
            "SignupCreatedUtc": datetime(2026, 4, 1, tzinfo=UTC),
        },
        {
            "SignupId": 3,
            "RequestPriority": "Low",
            "PreferredRankBand": "11-15",
            "LatestKVKRank": 1,
            "SignupCreatedUtc": datetime(2026, 4, 1, tzinfo=UTC),
        },
        {
            "SignupId": 2,
            "RequestPriority": "Medium",
            "PreferredRankBand": "6-10",
            "LatestKVKRank": 1,
            "SignupCreatedUtc": datetime(2026, 4, 1, tzinfo=UTC),
        },
        {
            "SignupId": 1,
            "RequestPriority": "High",
            "PreferredRankBand": "1-5",
            "LatestKVKRank": 1,
            "SignupCreatedUtc": datetime(2026, 4, 1, tzinfo=UTC),
        },
    ]

    sorted_rows = sorted(rows, key=signup_auto_sort_key)
    assert [r["SignupId"] for r in sorted_rows] == [1, 2, 3, 4, 5]


def test_legacy_signup_row_with_old_fields_remains_readable(monkeypatch):
    """
    A legacy signup row containing CurrentHeads, KingdomRole, GearText etc.
    must still be sortable and renderable without errors.
    """
    from datetime import UTC, datetime

    from mge.mge_simplified_flow_service import signup_auto_sort_key

    legacy_row = {
        "SignupId": 7,
        "RequestPriority": "High",
        "PreferredRankBand": "1-5",
        "CurrentHeads": 450,
        "KingdomRole": "Knight",
        "GearText": "T5 full",
        "ArmamentText": "maxed",
        "LatestKVKRank": 3,
        "SignupCreatedUtc": datetime(2026, 4, 1, tzinfo=UTC),
    }

    key = signup_auto_sort_key(legacy_row)
    # sort_weight for High/1-5 is 1
    assert key[0] == 1
