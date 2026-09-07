from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest


class FakeBot:
    def __init__(self) -> None:
        self.registered: dict[str, object] = {}
        self.descriptions: dict[str, str] = {}
        self.application_commands: list[object] = []

    def slash_command(self, *, name=None, description=None, guild_ids=None):
        def decorator(fn):
            self.registered[name] = fn
            self.descriptions[name] = description or ""
            return fn

        return decorator

    def add_application_command(self, command) -> None:
        self.application_commands.append(command)

    def add_listener(self, *_args, **_kwargs) -> None:
        return None


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


def _unwrap(fn):
    while hasattr(fn, "__wrapped__"):
        fn = fn.__wrapped__
    return fn


@pytest.mark.parametrize(
    ("module_name", "register_name", "command_name", "kwargs", "new_path"),
    [
        ("commands.subscriptions_cmds", "register_subscriptions", "subscribe", {}, "/me reminders"),
        (
            "commands.subscriptions_cmds",
            "register_subscriptions",
            "modify_subscription",
            {},
            "/me reminders",
        ),
        (
            "commands.subscriptions_cmds",
            "register_subscriptions",
            "unsubscribe",
            {},
            "/me reminders",
        ),
        (
            "commands.calendar_cmds",
            "register_calendar",
            "calendar_reminder_config",
            {},
            "/me reminders",
        ),
        (
            "commands.registry_cmds",
            "register_registry",
            "register_governor",
            {},
            "/me accounts",
        ),
        (
            "commands.registry_cmds",
            "register_registry",
            "modify_registration",
            {},
            "/me accounts",
        ),
        (
            "commands.registry_cmds",
            "register_registry",
            "my_registrations",
            {},
            "/me accounts",
        ),
        (
            "commands.telemetry_cmds",
            "register_telemetry",
            "mygovernorid",
            {},
            "/me accounts",
        ),
    ],
)
@pytest.mark.asyncio
async def test_approved_legacy_self_service_commands_send_private_redirect(
    monkeypatch,
    module_name: str,
    register_name: str,
    command_name: str,
    kwargs: dict,
    new_path: str,
) -> None:
    commands_module = importlib.import_module(module_name)
    fake_bot = FakeBot()
    getattr(commands_module, register_name)(fake_bot)
    description = fake_bot.descriptions[command_name]
    handler = _unwrap(fake_bot.registered[command_name])
    defer_calls: list[bool] = []

    async def fake_defer(_ctx, *, ephemeral=True):
        defer_calls.append(ephemeral)

    monkeypatch.setattr(commands_module, "safe_defer", fake_defer)

    ctx = DummyCtx()
    await handler(ctx, **kwargs)

    assert "Deprecated:" in description
    assert new_path in description
    assert defer_calls == [True]
    assert ctx.followup.sent[0]["kwargs"]["ephemeral"] is True
    message = ctx.followup.sent[0]["args"][0]
    assert f"/{command_name}" in message
    assert new_path in message
