from collections.abc import Awaitable, Callable
import inspect
import types
from typing import Any, cast

import pytest


class DummyUser:
    def __init__(self, uid):
        self.id = uid


class DummyFollowup:
    def __init__(self):
        self.sent = []

    async def send(self, *args, **kwargs):
        self.sent.append({"args": args, "kwargs": kwargs})
        return types.SimpleNamespace(id="followup_msg")


class DummyInteraction:
    def __init__(self):
        self.followup = DummyFollowup()

    async def edit_original_response(self, content=None, view=None):
        return types.SimpleNamespace(id="edited", content=content, view=view)


class DummyCtx:
    def __init__(self, user_id=1):
        self.user = DummyUser(user_id)
        self.interaction = DummyInteraction()
        self.followup = self.interaction.followup


def _get_registered_command_impl(module, command_name: str) -> Callable[..., Awaitable[Any]] | None:
    fake_bot = types.SimpleNamespace()
    fake_bot.registered = {}

    def add_listener(fn, name=None):
        fake_bot.registered.setdefault("_listeners", []).append((name, fn))

    def slash_command(*, name=None, description=None, guild_ids=None):
        def decorator(fn):
            nm = name or getattr(fn, "__name__", None) or "unnamed"
            fake_bot.registered[nm] = fn
            return fn

        return decorator

    fake_bot.add_listener = add_listener
    fake_bot.slash_command = slash_command
    fake_bot.add_application_command = lambda _command: None
    fake_bot.tree = types.SimpleNamespace()
    fake_bot.tree.command = lambda **kw: lambda f: f

    if hasattr(module, "register_commands"):
        module.register_commands(fake_bot)
    elif hasattr(module, "register_stats"):
        module.register_stats(fake_bot)

    fn = fake_bot.registered.get(command_name)
    if fn is None:
        return None

    while hasattr(fn, "__wrapped__"):
        fn = fn.__wrapped__

    if (
        not inspect.iscoroutinefunction(fn)
        and callable(fn)
        and inspect.iscoroutinefunction(fn.__call__)
    ):
        fn = fn.__call__

    return cast(Callable[..., Awaitable[Any]], fn)


@pytest.mark.parametrize(
    ("command_name", "replacement", "ephemeral"),
    [
        ("mykvkstats", "/kvk stats", True),
        ("mykvkhistory", "/kvk history", True),
        ("kvk_rankings", "/kvk rankings type:kvk", False),
        ("honor_rankings", "/kvk rankings type:honor", False),
    ],
)
@pytest.mark.asyncio
async def test_legacy_stats_commands_send_deprecation_redirect(
    monkeypatch, command_name, replacement, ephemeral
):
    import commands.stats_cmds as C

    defer_calls = []

    async def fake_safe_defer(ctx, ephemeral=True):
        defer_calls.append(ephemeral)

    monkeypatch.setattr(C, "safe_defer", fake_safe_defer, raising=False)
    monkeypatch.setattr(
        C.governor_account_service,
        "get_account_summary_for_user",
        lambda _user_id: pytest.fail("deprecated command should not load accounts"),
    )

    ctx = DummyCtx(user_id=10)
    handler = _get_registered_command_impl(C, command_name)
    assert handler is not None

    await handler(ctx)

    assert defer_calls == [ephemeral]
    assert ctx.followup.sent
    message = ctx.followup.sent[0]["args"][0]
    assert "deprecated" in message
    assert replacement in message
    assert ctx.followup.sent[0]["kwargs"]["ephemeral"] is ephemeral


def test_deprecated_stats_commands_do_not_keep_inline_legacy_dependencies():
    import commands.stats_cmds as C

    source = inspect.getsource(C.register_stats)

    assert "load_stat_cache" not in source
    assert "build_honor_rankings_payload" not in source
    assert "MyKVKStatsSelectView" not in source
    assert "KVKRankingView" not in source
