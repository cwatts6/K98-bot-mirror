from __future__ import annotations

import discord

from decoraters import _has_leadership_role


class _Role:
    def __init__(self, rid: int, name: str):
        self.id = rid
        self.name = name


def test_leadership_role_true(monkeypatch):
    class FakeMember:
        def __init__(self, roles):
            self.roles = roles

    monkeypatch.setattr(discord, "Member", FakeMember)
    monkeypatch.setattr("decoraters.LEADERSHIP_ROLE_IDS", [123])

    m = FakeMember([_Role(123, "x")])
    assert _has_leadership_role(m) is True


def test_leadership_role_false(monkeypatch):
    class FakeMember:
        def __init__(self, roles):
            self.roles = roles

    monkeypatch.setattr(discord, "Member", FakeMember)
    monkeypatch.setattr("decoraters.LEADERSHIP_ROLE_IDS", [123])

    m = FakeMember([_Role(999, "x")])
    assert _has_leadership_role(m) is False
