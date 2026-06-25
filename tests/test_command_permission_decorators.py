from __future__ import annotations

import asyncio
import inspect
from types import SimpleNamespace

from commands import admin_cmds, inventory_cmds, location_cmds, mge_cmds, stats_cmds, telemetry_cmds
import decoraters
from decoraters import admin_only, admin_or_leadership_in_allowed_channels, channel_only


class _Response:
    def __init__(self, *, done: bool = False):
        self._done = done
        self.messages: list[tuple[str, bool]] = []

    def is_done(self) -> bool:
        return self._done

    async def send_message(self, message: str, *, ephemeral: bool = True):
        self.messages.append((message, ephemeral))
        self._done = True


class _Followup:
    def __init__(self):
        self.messages: list[tuple[str, bool]] = []

    async def send(self, message: str, *, ephemeral: bool = True):
        self.messages.append((message, ephemeral))


class _Role:
    def __init__(self, role_id: int, name: str):
        self.id = role_id
        self.name = name


class _Ctx:
    def __init__(
        self,
        *,
        user_id: int = 42,
        channel_id: int = 100,
        parent_id: int | None = None,
        response_done: bool = False,
        roles: list[_Role] | None = None,
    ):
        self.user = SimpleNamespace(id=user_id, display_name=f"user-{user_id}")
        self.author = SimpleNamespace(id=user_id, roles=roles or [])
        self.channel = SimpleNamespace(id=channel_id, parent_id=parent_id)
        self.interaction = SimpleNamespace(
            user=self.user,
            channel=self.channel,
            guild=SimpleNamespace(id=1),
            response=_Response(done=response_done),
            followup=_Followup(),
        )
        self.followup = self.interaction.followup
        self.called = False


def test_admin_only_allows_admin(monkeypatch):
    monkeypatch.setattr(decoraters, "ADMIN_USER_ID", 1)
    ctx = _Ctx(user_id=1)

    @admin_only()
    async def handler(inner_ctx):
        inner_ctx.called = True

    asyncio.run(handler(ctx))

    assert ctx.called is True
    assert ctx.interaction.response.messages == []


def test_admin_only_denies_non_admin_before_defer(monkeypatch):
    monkeypatch.setattr(decoraters, "ADMIN_USER_ID", 1)
    ctx = _Ctx(user_id=2)

    @admin_only()
    async def handler(inner_ctx):
        inner_ctx.called = True

    asyncio.run(handler(ctx))

    assert ctx.called is False
    assert ctx.interaction.response.messages == [("❌ This command is restricted to admins.", True)]


def test_admin_only_denies_non_admin_after_defer(monkeypatch):
    monkeypatch.setattr(decoraters, "ADMIN_USER_ID", 1)
    ctx = _Ctx(user_id=2, response_done=True)

    @admin_only(denial_message="Nope.")
    async def handler(inner_ctx):
        inner_ctx.called = True

    asyncio.run(handler(ctx))

    assert ctx.called is False
    assert ctx.followup.messages == [("Nope.", True)]


def test_channel_only_handles_missing_config_before_admin_override(monkeypatch):
    monkeypatch.setattr(decoraters, "ADMIN_USER_ID", 1)
    ctx = _Ctx(user_id=1)

    @channel_only(None, missing_config_message="Missing channel.", admin_override=True)
    async def handler(inner_ctx):
        inner_ctx.called = True

    asyncio.run(handler(ctx))

    assert ctx.called is False
    assert ctx.interaction.response.messages == [("Missing channel.", True)]


def test_channel_only_treats_zero_channel_id_as_missing_config(monkeypatch):
    monkeypatch.setattr(decoraters, "ADMIN_USER_ID", 1)
    ctx = _Ctx(user_id=1)

    @channel_only(0, missing_config_message="Missing channel.", admin_override=True)
    async def handler(inner_ctx):
        inner_ctx.called = True

    asyncio.run(handler(ctx))

    assert ctx.called is False
    assert ctx.interaction.response.messages == [("Missing channel.", True)]


def test_channel_only_allows_thread_parent_and_admin_override(monkeypatch):
    monkeypatch.setattr(decoraters, "ADMIN_USER_ID", 1)
    thread_ctx = _Ctx(user_id=2, channel_id=999, parent_id=100)
    admin_ctx = _Ctx(user_id=1, channel_id=999)

    @channel_only(100, admin_override=True)
    async def handler(inner_ctx):
        inner_ctx.called = True

    asyncio.run(handler(thread_ctx))
    asyncio.run(handler(admin_ctx))

    assert thread_ctx.called is True
    assert admin_ctx.called is True


def test_admin_or_leadership_in_allowed_channels_checks_channel_first(monkeypatch):
    monkeypatch.setattr(decoraters, "ADMIN_USER_ID", 1)
    monkeypatch.setattr(decoraters, "_has_leadership_role", lambda _member: True)
    ctx = _Ctx(user_id=2, channel_id=999)

    @admin_or_leadership_in_allowed_channels({100})
    async def handler(inner_ctx):
        inner_ctx.called = True

    asyncio.run(handler(ctx))

    assert ctx.called is False
    assert ctx.interaction.response.messages == [
        ("🔒 This command can only be used in <#100>.", True)
    ]


def test_admin_or_leadership_in_allowed_channels_allows_admin_and_leadership(monkeypatch):
    monkeypatch.setattr(decoraters, "ADMIN_USER_ID", 1)
    monkeypatch.setattr(decoraters, "_has_leadership_role", lambda member: member is not None)
    admin_ctx = _Ctx(user_id=1, channel_id=100)
    leadership_ctx = _Ctx(user_id=2, channel_id=999, parent_id=100, roles=[_Role(5, "Lead")])

    @admin_or_leadership_in_allowed_channels({100})
    async def handler(inner_ctx):
        inner_ctx.called = True

    asyncio.run(handler(admin_ctx))
    asyncio.run(handler(leadership_ctx))

    assert admin_ctx.called is True
    assert leadership_ctx.called is True


def test_admin_or_leadership_in_allowed_channels_denies_non_leadership(monkeypatch):
    monkeypatch.setattr(decoraters, "ADMIN_USER_ID", 1)
    monkeypatch.setattr(decoraters, "_has_leadership_role", lambda _member: False)
    ctx = _Ctx(user_id=2, channel_id=100)

    @admin_or_leadership_in_allowed_channels({100})
    async def handler(inner_ctx):
        inner_ctx.called = True

    asyncio.run(handler(ctx))

    assert ctx.called is False
    assert ctx.interaction.response.messages == [
        ("❌ This command is restricted to Admin or Leadership.", True)
    ]


def test_active_command_modules_do_not_keep_inline_permission_gates():
    sources = "\n".join(
        inspect.getsource(module)
        for module in (
            admin_cmds,
            inventory_cmds,
            location_cmds,
            mge_cmds,
            stats_cmds,
            telemetry_cmds,
        )
    )

    assert "ctx.user.id != ADMIN_USER_ID" not in sources
    assert "if not _is_admin(ctx.user):" not in sources
    assert "if not _is_allowed_channel(ctx.channel):" not in sources
    assert "not is_admin_interaction(interaction)" not in sources
