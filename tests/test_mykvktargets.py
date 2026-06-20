import asyncio
import inspect
import types

import pytest

pytestmark = pytest.mark.asyncio


class DummyUser:
    def __init__(self, uid):
        self.id = uid


class DummyFollowup:
    def __init__(self):
        self.sent = []

    async def send(self, content=None, *, embed=None, view=None, ephemeral=False, files=None):
        self.sent.append({"content": content, "embed": embed, "view": view, "ephemeral": ephemeral})
        return types.SimpleNamespace(id="followup_msg")


class DummyInteraction:
    def __init__(self):
        self.followup = DummyFollowup()

    async def edit_original_response(self, content=None, view=None):
        return types.SimpleNamespace(id="edited", content=content, view=view)


class DummyCtx:
    def __init__(self, user_id=42):
        self.user = DummyUser(user_id)
        self.interaction = DummyInteraction()
        self.followup = self.interaction.followup


def _get_registered_command_impl(module, command_name: str):
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
    fake_bot.tree = types.SimpleNamespace()
    fake_bot.tree.command = lambda **kw: lambda f: f

    if hasattr(module, "register_commands"):
        module.register_commands(fake_bot)

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

    return fn


async def test_mykvktargets_sends_deprecation_redirect(monkeypatch):
    import commands.telemetry_cmds as C

    defer_calls = []

    async def fake_safe_defer(ctx, ephemeral=True):
        defer_calls.append(ephemeral)

    monkeypatch.setattr(C, "safe_defer", fake_safe_defer, raising=False)
    monkeypatch.setattr(
        C,
        "run_target_lookup",
        lambda *_args, **_kwargs: pytest.fail("deprecated command should not load targets"),
    )
    monkeypatch.setattr(
        C,
        "get_account_summary_for_user",
        lambda _user_id: pytest.fail("deprecated command should not load accounts"),
    )

    ctx = DummyCtx(user_id=99)
    handler = _get_registered_command_impl(C, "mykvktargets")
    assert handler is not None

    await handler(ctx, governorid="123", only_me=False)

    assert defer_calls == [True]
    assert ctx.followup.sent
    message = ctx.followup.sent[0]["content"]
    assert "deprecated" in message
    assert "/kvk targets" in message
    assert ctx.followup.sent[0]["ephemeral"] is True


async def test_crystaltech_single_registered_account_auto_opens(monkeypatch):
    import commands.telemetry_cmds as C
    from services.governor_account_service import summarize_accounts

    async def fake_get_account_summary_for_user(user_id):
        assert user_id == 33
        return summarize_accounts({"Main": {"GovernorID": "333", "GovernorName": "Crystal"}})

    called = {}

    async def fake_run_crystaltech_flow(interaction, gid, ephemeral=False):
        called["gid"] = gid
        called["ephemeral"] = ephemeral

    monkeypatch.setattr(
        C, "safe_defer", lambda ctx, ephemeral=True: asyncio.sleep(0), raising=False
    )
    monkeypatch.setattr(C, "get_account_summary_for_user", fake_get_account_summary_for_user)
    monkeypatch.setattr(C, "run_crystaltech_flow_service", fake_run_crystaltech_flow)

    ctx = DummyCtx(user_id=33)
    handler = _get_registered_command_impl(C, "mykvkcrystaltech")
    assert handler is not None

    await handler(ctx, governorid=None, only_me=True)

    assert called == {"gid": "333", "ephemeral": True}


async def test_crystaltech_multi_account_builds_summary_selector(monkeypatch):
    import commands.telemetry_cmds as C
    from services.governor_account_service import AccountResolutionSummary, summarize_accounts

    async def fake_get_account_summary_for_user(user_id):
        assert user_id == 44
        return summarize_accounts(
            {
                "Main": {"GovernorID": "444", "GovernorName": "Main"},
                "Alt 1": {"GovernorID": "445", "GovernorName": "Alt"},
            }
        )

    captured = {}

    def fake_picker_view(ctx, options, on_select_governor, **kwargs):
        captured["options"] = options
        captured["heading"] = kwargs.get("heading")
        return types.SimpleNamespace(heading=kwargs.get("heading"))

    def fake_options(summary):
        assert isinstance(summary, AccountResolutionSummary)
        return [types.SimpleNamespace(value="444"), types.SimpleNamespace(value="445")]

    monkeypatch.setattr(
        C, "safe_defer", lambda ctx, ephemeral=True: asyncio.sleep(0), raising=False
    )
    monkeypatch.setattr(C, "get_account_summary_for_user", fake_get_account_summary_for_user)
    monkeypatch.setattr(C, "safe_build_unique_gov_options", fake_options)
    monkeypatch.setattr(C, "AccountPickerView", fake_picker_view)

    ctx = DummyCtx(user_id=44)
    handler = _get_registered_command_impl(C, "mykvkcrystaltech")
    assert handler is not None

    await handler(ctx, governorid=None, only_me=True)

    assert len(captured["options"]) == 2
    assert captured["heading"] == "Select an account to manage its Crystal Tech:"
