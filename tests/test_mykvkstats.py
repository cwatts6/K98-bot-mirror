import asyncio
import inspect
import types

import pytest

pytestmark = pytest.mark.asyncio


# Lightweight fakes used in multiple tests
class DummyUser:
    def __init__(self, uid):
        self.id = uid


class DummyFollowup:
    def __init__(self):
        self.sent = []

    async def send(self, *args, **kwargs):
        self.sent.append({"args": args, "kwargs": kwargs})
        return types.SimpleNamespace(id="followup_msg")


class DummyChannel:
    def __init__(self):
        self.sent = []

    async def send(self, *args, **kwargs):
        self.sent.append({"args": args, "kwargs": kwargs})
        return types.SimpleNamespace(id="channel_msg")


class DummyInteraction:
    def __init__(self):
        self.response = types.SimpleNamespace(is_done=lambda: False)
        self.followup = DummyFollowup()
        self.edited = []

    async def edit_original_response(self, content=None, view=None):
        self.edited.append({"content": content, "view": view})
        return types.SimpleNamespace(id="edited")


class DummyCtx:
    def __init__(self, user_id=1):
        self.user = DummyUser(user_id)
        self.interaction = DummyInteraction()
        self.followup = self.interaction.followup
        self.channel = DummyChannel()


def _get_registered_command_impl(module, command_name: str):
    """
    Register the commands into a fake bot and return the unwrapped inner coroutine
    implementation for the given command_name.
    """
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

    # Call register_commands to populate the fake bot
    if hasattr(module, "register_commands"):
        module.register_commands(fake_bot)

    fn = fake_bot.registered.get(command_name)
    if fn is None:
        return None

    # Unwrap decorators to reach the innermost async implementation
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


async def test_no_registered_accounts_shows_registration_prompt(monkeypatch):
    import Commands as C

    # Fake load_last_kvk_map as async (the real code awaits it)
    async def fake_load_last_kvk_map():
        return {}

    # Fake load_registry as synchronous but invoked through asyncio.to_thread below
    def fake_load_registry():
        return {str(10): {"accounts": {}}}

    # Provide an async-to-thread shim so `await asyncio.to_thread(load_registry)` works
    async def fake_to_thread(fn, *a, **k):
        return fn(*a, **k)

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(C, "load_registry", fake_load_registry)
    monkeypatch.setattr(C, "load_last_kvk_map", fake_load_last_kvk_map)
    monkeypatch.setattr(
        C, "safe_defer", lambda ctx, ephemeral=True: asyncio.sleep(0), raising=False
    )

    # Replace MyRegsActionView with a minimal stub that records set_message_ref calls
    class StubMyRegsActionView:
        def __init__(self, *, author_id, has_regs, timeout=120):
            self.author_id = author_id
            self.has_regs = has_regs
            self._message = None

        def set_message_ref(self, message):
            self._message = message

    monkeypatch.setattr(C, "MyRegsActionView", StubMyRegsActionView)

    ctx = DummyCtx(user_id=10)
    handler = _get_registered_command_impl(C, "mykvkstats")
    assert (
        handler is not None
    ), "mykvkstats command not registered; ensure register_commands was called"

    # The inner function expects ctx only
    await handler(ctx)
    assert (
        ctx.interaction.edited
    ), "Expected edit_original_response to be called in no-accounts path"


async def test_single_account_sends_public_embed(monkeypatch):
    import Commands as C

    async def fake_load_last_kvk_map():
        return {}

    def fake_load_registry():
        return {str(11): {"accounts": {"Main": {"GovernorID": "123", "GovernorName": "X"}}}}

    async def fake_to_thread(fn, *a, **k):
        return fn(*a, **k)

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(C, "load_registry", fake_load_registry)
    monkeypatch.setattr(C, "load_last_kvk_map", fake_load_last_kvk_map)
    monkeypatch.setattr(C, "normalize_governor_id", lambda v: str(v))
    # Make load_stat_row sync but called via await asyncio.to_thread inside handler
    monkeypatch.setattr(C, "load_stat_row", lambda gid: {"GovernorID": gid, "val": 1})
    monkeypatch.setattr(C, "build_stats_embed", lambda row, user: ("embed_obj", "file_obj"))
    monkeypatch.setattr(
        C, "safe_defer", lambda ctx, ephemeral=True: asyncio.sleep(0), raising=False
    )

    ctx = DummyCtx(user_id=11)
    handler = _get_registered_command_impl(C, "mykvkstats")
    assert handler is not None

    await handler(ctx)
    assert ctx.channel.sent, "Expected channel.send to be called for single-account public path"


async def test_multi_account_builds_selector(monkeypatch):
    import Commands as C

    async def fake_load_last_kvk_map():
        return {}

    def fake_load_registry():
        return {
            str(12): {
                "accounts": {
                    "Main": {"GovernorID": 1, "GovernorName": "A"},
                    "Alt 1": {"GovernorID": 2, "GovernorName": "B"},
                }
            }
        }

    async def fake_to_thread(fn, *a, **k):
        return fn(*a, **k)

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(C, "load_registry", fake_load_registry)
    monkeypatch.setattr(C, "load_last_kvk_map", fake_load_last_kvk_map)
    monkeypatch.setattr(
        C, "safe_defer", lambda ctx, ephemeral=True: asyncio.sleep(0), raising=False
    )

    created = {}

    class StubMyKVKStatsSelectView:
        def __init__(self, ctx=None, accounts=None, author_id=None, timeout=300):
            created["ctx"] = ctx
            created["accounts"] = accounts
            created["author_id"] = author_id

    monkeypatch.setattr(C, "MyKVKStatsSelectView", StubMyKVKStatsSelectView)

    ctx = DummyCtx(user_id=12)
    handler = _get_registered_command_impl(C, "mykvkstats")
    assert handler is not None

    await handler(ctx)
    assert created.get("accounts"), "Expected MyKVKStatsSelectView to be initialized with accounts"
    assert (
        ctx.interaction.edited
    ), "Expected edit_original_response to be called for multi-account path"
