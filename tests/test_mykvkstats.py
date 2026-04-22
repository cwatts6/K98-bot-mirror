import asyncio
import inspect
import os
import sys
import types

import pytest

pytestmark = pytest.mark.asyncio

os.environ.setdefault("OUR_KINGDOM", "1234")


def _ensure_heavy_stubs():
    """Ensure heavy/unavailable dependencies are stubbed in sys.modules."""
    stubs = {
        "gspread": {},
        "gspread.exceptions": {"APIError": Exception, "SpreadsheetNotFound": Exception},
        "pyodbc": {},
        "google": {},
        "google.auth": {},
        "google.auth.transport": {},
        "google.auth.transport.requests": {"AuthorizedSession": object},
        "google.oauth2": {},
        "google.oauth2.service_account": {"Credentials": object},
        "googleapiclient": {},
        "googleapiclient.discovery": {"build": lambda *a, **k: None},
        "googleapiclient.errors": {"HttpError": Exception},
        "rapidfuzz": {},
        "rapidfuzz.fuzz": {"WRatio": lambda *a, **k: 0, "token_sort_ratio": lambda *a, **k: 0},
        "rapidfuzz.process": {"extract": lambda *a, **k: []},
        "unidecode": {"unidecode": lambda s: s},
        "pandas": {"Series": object, "DataFrame": object, "isna": lambda *a, **k: False, "read_csv": lambda *a, **k: None},
        "pandas.api": {},
        "pandas.api.types": {"is_numeric_dtype": lambda *a, **k: False},
        "sqlalchemy": {"create_engine": lambda *a, **k: None},
        "tenacity": {
            "retry": lambda *a, **k: (lambda f: f),
            "stop_after_attempt": lambda n: None,
            "wait_fixed": lambda n: None,
            "retry_if_exception": lambda f: None,
            "retry_if_exception_type": lambda t: None,
            "TryAgain": Exception,
            "RetryError": Exception,
        },
    }
    for mod, attrs in stubs.items():
        if mod not in sys.modules:
            m = types.ModuleType(mod)
            for attr, val in attrs.items():
                setattr(m, attr, val)
            sys.modules[mod] = m
        else:
            # ensure required attrs are present even if module was pre-loaded
            existing = sys.modules[mod]
            for attr, val in attrs.items():
                if not hasattr(existing, attr):
                    try:
                        setattr(existing, attr, val)
                    except Exception:
                        pass


_ensure_heavy_stubs()


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

    # Call register_stats to populate the fake bot
    if hasattr(module, "register_stats"):
        module.register_stats(fake_bot)

    fn = fake_bot.registered.get(command_name)
    if fn is None:
        return None

    try:
        while hasattr(fn, "__wrapped__"):
            fn = fn.__wrapped__
    except Exception:
        pass

    if (
        not inspect.iscoroutinefunction(fn)
        and callable(fn)
        and inspect.iscoroutinefunction(fn.__call__)
    ):
        fn = fn.__call__

    return fn


async def test_no_registered_accounts_shows_registration_prompt(monkeypatch):
    _ensure_heavy_stubs()
    import commands.stats_cmds as sc

    async def fake_load_last_kvk_map():
        return {}

    def fake_load_registry():
        return {str(10): {"accounts": {}}}

    async def fake_to_thread(fn, *a, **k):
        return fn(*a, **k)

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(sc, "load_registry", fake_load_registry)
    monkeypatch.setattr(sc, "load_last_kvk_map", fake_load_last_kvk_map, raising=False)
    monkeypatch.setattr(
        sc, "safe_defer", lambda ctx, ephemeral=True: asyncio.sleep(0), raising=False
    )

    class StubMyRegsActionView:
        def __init__(self, *, author_id, has_regs, timeout=120):
            self.author_id = author_id
            self.has_regs = has_regs
            self._message = None

        def set_message_ref(self, message):
            self._message = message

    monkeypatch.setattr(sc, "MyRegsActionView", StubMyRegsActionView)

    ctx = DummyCtx(user_id=10)
    handler = _get_registered_command_impl(sc, "mykvkstats")
    assert handler is not None, "mykvkstats command not registered"

    await handler(ctx)
    assert ctx.interaction.edited, "Expected edit_original_response to be called in no-accounts path"


async def test_single_account_sends_public_embed(monkeypatch):
    _ensure_heavy_stubs()
    import commands.stats_cmds as sc

    async def fake_load_last_kvk_map():
        return {}

    def fake_load_registry():
        return {str(11): {"accounts": {"Main": {"GovernorID": "123", "GovernorName": "X"}}}}

    async def fake_to_thread(fn, *a, **k):
        return fn(*a, **k)

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(sc, "load_registry", fake_load_registry)
    monkeypatch.setattr(sc, "load_last_kvk_map", fake_load_last_kvk_map, raising=False)
    monkeypatch.setattr(sc, "normalize_governor_id", lambda v: str(v))
    monkeypatch.setattr(sc, "load_stat_row", lambda gid: {"GovernorID": gid, "val": 1})
    monkeypatch.setattr(sc, "build_stats_embed", lambda row, user: ("embed_obj", "file_obj"))
    monkeypatch.setattr(
        sc, "safe_defer", lambda ctx, ephemeral=True: asyncio.sleep(0), raising=False
    )

    ctx = DummyCtx(user_id=11)
    handler = _get_registered_command_impl(sc, "mykvkstats")
    assert handler is not None

    await handler(ctx)
    assert ctx.channel.sent, "Expected channel.send to be called for single-account public path"


async def test_multi_account_builds_selector(monkeypatch):
    _ensure_heavy_stubs()
    import commands.stats_cmds as sc

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
    monkeypatch.setattr(sc, "load_registry", fake_load_registry)
    monkeypatch.setattr(sc, "load_last_kvk_map", fake_load_last_kvk_map, raising=False)
    monkeypatch.setattr(
        sc, "safe_defer", lambda ctx, ephemeral=True: asyncio.sleep(0), raising=False
    )

    created = {}

    class StubMyKVKStatsSelectView:
        def __init__(self, ctx=None, accounts=None, author_id=None, timeout=300):
            created["ctx"] = ctx
            created["accounts"] = accounts
            created["author_id"] = author_id

    monkeypatch.setattr(sc, "MyKVKStatsSelectView", StubMyKVKStatsSelectView)

    ctx = DummyCtx(user_id=12)
    handler = _get_registered_command_impl(sc, "mykvkstats")
    assert handler is not None

    await handler(ctx)
    assert created.get("accounts"), "Expected MyKVKStatsSelectView to be initialized with accounts"
    assert ctx.interaction.edited, "Expected edit_original_response to be called for multi-account path"
