"""
Focused tests for the deprecated /my_stats_export redirect.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest


class DummyFollowup:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send(self, *args, **kwargs):
        self.sent.append({"args": args, "kwargs": kwargs})
        return SimpleNamespace(id="msg")


class DummyCtx:
    def __init__(self) -> None:
        self.user = SimpleNamespace(id=123, display_name="Tester", name="Tester")
        self.author = self.user
        self.followup = DummyFollowup()


def _get_stats_export_handler():
    import commands.stats_cmds as commands_module

    fake_bot = SimpleNamespace(registered={})

    def slash_command(*, name=None, description=None, guild_ids=None):
        def decorator(fn):
            fake_bot.registered[name] = fn
            return fn

        return decorator

    fake_bot.slash_command = slash_command
    fake_bot.add_application_command = lambda _command: None
    commands_module.register_stats(fake_bot)
    fn = fake_bot.registered["my_stats_export"]
    while hasattr(fn, "__wrapped__"):
        fn = fn.__wrapped__
    return commands_module, fn


@pytest.mark.asyncio
async def test_my_stats_export_redirects_to_me_exports(monkeypatch):
    commands_module, handler = _get_stats_export_handler()
    defer_calls: list[bool] = []

    async def fake_defer(_ctx, *, ephemeral=True):
        defer_calls.append(ephemeral)

    monkeypatch.setattr(commands_module, "safe_defer", fake_defer)

    ctx = DummyCtx()
    await handler(ctx, format="CSV", days=30)

    assert defer_calls == [True]
    assert ctx.followup.sent[0]["kwargs"]["ephemeral"] is True
    message = ctx.followup.sent[0]["args"][0]
    assert "/my_stats_export" in message
    assert "/me exports" in message
