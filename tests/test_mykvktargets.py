import asyncio
import inspect
import types

import pytest

pytestmark = pytest.mark.asyncio


class DummyUser:
    def __init__(self, uid):
        self.id = uid


class DummyResponse:
    def __init__(self):
        self._done = False

    async def defer(self, ephemeral=True):
        self._done = True

    def is_done(self):
        return self._done


class DummyFollowup:
    def __init__(self):
        self.sent = []

    async def send(self, content=None, *, embed=None, view=None, ephemeral=False, files=None):
        self.sent.append({"content": content, "embed": embed, "view": view, "ephemeral": ephemeral})
        return types.SimpleNamespace(id="followup_msg")


class DummyChannel:
    def __init__(self):
        self.sent = []

    async def send(self, *args, **kwargs):
        self.sent.append((args, kwargs))
        return types.SimpleNamespace(id="channel_msg")


class DummyInteraction:
    def __init__(self):
        self.response = DummyResponse()
        self.followup = DummyFollowup()

    async def edit_original_response(self, content=None, view=None):
        return types.SimpleNamespace(id="edited")


class DummyCtx:
    def __init__(self, user_id=42):
        self.user = DummyUser(user_id)
        self.interaction = DummyInteraction()
        self.followup = self.interaction.followup
        self.channel = DummyChannel()


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

    try:
        while hasattr(fn, "__wrapped__"):
            fn = fn.__wrapped__
    except Exception:
        pass

    # Use callable(...) check per B004 recommendation and inspect the object's __call__
    if (
        not inspect.iscoroutinefunction(fn)
        and callable(fn)
        and inspect.iscoroutinefunction(fn.__call__)
    ):
        fn = fn.__call__

    return fn


async def test_manual_governorid_triggers_run_target_lookup(monkeypatch):
    import commands.telemetry_cmds as C

    async def fake_load_last_kvk_map():
        return {}

    called = {}

    async def fake_run_target_lookup(interaction_or_ctx, governor_id, ephemeral=False):
        called["args"] = (
            getattr(interaction_or_ctx, "response", None) is not None,
            governor_id,
            ephemeral,
        )

    monkeypatch.setattr(C, "run_target_lookup", fake_run_target_lookup)
    monkeypatch.setattr(
        C, "safe_defer", lambda ctx, ephemeral=True: asyncio.sleep(0), raising=False
    )
    monkeypatch.setattr(C, "load_last_kvk_map", fake_load_last_kvk_map)

    ctx = DummyCtx()
    handler = _get_registered_command_impl(C, "mykvktargets")
    assert handler is not None

    await handler(ctx, governorid="123", only_me=False)
    assert called.get("args") is not None
    assert called["args"][1] == "123"


async def test_single_registered_account_auto_opens(monkeypatch):
    import commands.telemetry_cmds as C
    from services.governor_account_service import summarize_accounts

    async def fake_load_last_kvk_map():
        return {}

    async def fake_get_account_summary_for_user(user_id):
        assert user_id == 99
        return summarize_accounts({"Main": {"GovernorID": "999", "GovernorName": "X"}})

    called = {"run_target_lookup": 0}

    async def fake_run_target_lookup(interaction, gid, ephemeral=False):
        called["run_target_lookup"] += 1
        called["gid"] = gid

    monkeypatch.setattr(
        C, "safe_defer", lambda ctx, ephemeral=True: asyncio.sleep(0), raising=False
    )
    monkeypatch.setattr(C, "load_last_kvk_map", fake_load_last_kvk_map)

    async def fake_to_thread(fn, *a, **k):
        return fn(*a, **k)

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(C, "get_account_summary_for_user", fake_get_account_summary_for_user)
    monkeypatch.setattr(C, "run_target_lookup", fake_run_target_lookup)

    ctx = DummyCtx(user_id=99)
    handler = _get_registered_command_impl(C, "mykvktargets")
    assert handler is not None

    await handler(ctx, governorid=None, only_me=False)
    assert called["run_target_lookup"] == 1
    assert str(called["gid"]) == "999"


async def test_multi_account_builds_selector(monkeypatch):
    import commands.telemetry_cmds as C
    from services.governor_account_service import summarize_accounts

    async def fake_load_last_kvk_map():
        return {}

    async def fake_get_account_summary_for_user(user_id):
        assert user_id == 5
        return summarize_accounts(
            {
                "Main": {"GovernorID": "1", "GovernorName": "A"},
                "Alt 1": {"GovernorID": "2", "GovernorName": "B"},
            },
        )

    async def fake_to_thread(fn, *a, **k):
        return fn(*a, **k)

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(C, "get_account_summary_for_user", fake_get_account_summary_for_user)
    monkeypatch.setattr(C, "load_last_kvk_map", fake_load_last_kvk_map)
    monkeypatch.setattr(
        C, "safe_defer", lambda ctx, ephemeral=True: asyncio.sleep(0), raising=False
    )

    created = {}

    def fake_make_kvk_targets_view(ctx, options, on_select_governor, **kwargs):
        created["options"] = options
        created["on_select_callable"] = on_select_governor
        return "fake_view"

    monkeypatch.setattr(C, "make_kvk_targets_view", fake_make_kvk_targets_view)

    ctx = DummyCtx(user_id=5)
    handler = _get_registered_command_impl(C, "mykvktargets")
    assert handler is not None

    await handler(ctx, governorid=None, only_me=True)

    assert "options" in created
    assert isinstance(created["options"], list)
    assert ctx.followup.sent, "Expected a followup call to send the selector message"


async def test_no_registered_accounts_shows_hint_and_empty_picker(monkeypatch):
    import commands.telemetry_cmds as C
    from services.governor_account_service import summarize_accounts

    async def fake_load_last_kvk_map():
        return {}

    async def fake_get_account_summary_for_user(user_id):
        assert user_id == 7
        return summarize_accounts({})

    async def fake_to_thread(fn, *a, **k):
        return fn(*a, **k)

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(C, "get_account_summary_for_user", fake_get_account_summary_for_user)
    monkeypatch.setattr(C, "load_last_kvk_map", fake_load_last_kvk_map)
    monkeypatch.setattr(
        C, "safe_defer", lambda ctx, ephemeral=True: asyncio.sleep(0), raising=False
    )

    captured = {}

    def fake_make_kvk_targets_view(ctx, options, on_select_governor, **kwargs):
        captured["options"] = options
        return "empty_view"

    monkeypatch.setattr(C, "make_kvk_targets_view", fake_make_kvk_targets_view)

    ctx = DummyCtx(user_id=7)
    handler = _get_registered_command_impl(C, "mykvktargets")
    assert handler is not None

    await handler(ctx, governorid=None, only_me=True)

    assert ctx.followup.sent, "Expected followup hint when no accounts"
    assert "options" in captured and captured["options"] == []


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
