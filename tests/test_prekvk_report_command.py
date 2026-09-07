import inspect
import types

import pytest

from commands.prekvk_cmds import register_prekvk


def test_prekvk_report_command_is_public_read_only_surface():
    source = inspect.getsource(register_prekvk)

    assert "SlashCommandGroup" in source
    assert '"prekvk"' in source
    assert 'name="report"' in source
    assert "@safe_command" in source
    assert "@track_usage()" in source
    assert "safe_defer(ctx, ephemeral=True)" in source
    assert "safe_defer(ctx, ephemeral=False)" not in source
    assert "@is_admin_and_notify_channel()" not in source
    assert "import_prekvk_bytes" not in source
    assert "handle_prekvk_upload" not in source
    assert "report_service" not in source
    assert "send_prekvk_report" not in source


@pytest.mark.asyncio
async def test_prekvk_report_sends_deprecation_redirect(monkeypatch):
    import commands.prekvk_cmds as C

    class DummyFollowup:
        def __init__(self):
            self.sent = []

        async def send(self, content=None, *, ephemeral=False, **_kwargs):
            self.sent.append({"content": content, "ephemeral": ephemeral})

    class DummyCtx:
        def __init__(self):
            self.user = types.SimpleNamespace(id=123)
            self.followup = DummyFollowup()

    class FakeGroup:
        def __init__(self, *_args, **_kwargs):
            self.commands = {}

        def command(self, *, name=None, **_kwargs):
            def decorator(fn):
                self.commands[name] = fn
                return fn

            return decorator

    fake_group = None

    def fake_group_factory(*args, **kwargs):
        nonlocal fake_group
        fake_group = FakeGroup(*args, **kwargs)
        return fake_group

    fake_bot = types.SimpleNamespace()
    fake_bot.add_application_command = lambda _group: None

    defer_calls = []

    async def fake_safe_defer(ctx, ephemeral=True):
        defer_calls.append(ephemeral)

    monkeypatch.setattr(C.discord, "SlashCommandGroup", fake_group_factory)
    monkeypatch.setattr(C, "safe_defer", fake_safe_defer)

    C.register_prekvk(fake_bot)
    assert fake_group is not None
    handler = fake_group.commands["report"]
    while hasattr(handler, "__wrapped__"):
        handler = handler.__wrapped__

    ctx = DummyCtx()
    await handler(ctx)

    assert defer_calls == [True]
    assert ctx.followup.sent
    assert "deprecated" in ctx.followup.sent[0]["content"]
    assert "/kvk rankings type:prekvk" in ctx.followup.sent[0]["content"]
    assert "Run it in <#" in ctx.followup.sent[0]["content"]
    assert ctx.followup.sent[0]["ephemeral"] is True
