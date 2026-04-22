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
            existing = sys.modules[mod]
            for attr, val in attrs.items():
                if not hasattr(existing, attr):
                    try:
                        setattr(existing, attr, val)
                    except Exception:
                        pass


_ensure_heavy_stubs()


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

    if (
        not inspect.iscoroutinefunction(fn)
        and callable(fn)
        and inspect.iscoroutinefunction(fn.__call__)
    ):
        fn = fn.__call__

    return fn


async def test_manual_governorid_triggers_run_target_lookup(monkeypatch):
    _ensure_heavy_stubs()
    import commands.telemetry_cmds as tc

    async def fake_load_last_kvk_map():
        return {}

    called = {}

    async def fake_run_target_lookup(interaction_or_ctx, governor_id, ephemeral=False):
        called["args"] = (
            getattr(interaction_or_ctx, "response", None) is not None,
            governor_id,
            ephemeral,
        )

    monkeypatch.setattr(tc, "run_target_lookup", fake_run_target_lookup)
    monkeypatch.setattr(
        tc, "safe_defer", lambda ctx, ephemeral=True: asyncio.sleep(0), raising=False
    )
    monkeypatch.setattr(tc, "load_last_kvk_map", fake_load_last_kvk_map)

    ctx = DummyCtx()
    handler = _get_registered_command_impl(tc, "mykvktargets")
    assert handler is not None

    await handler(ctx, governorid="123", only_me=False)
    assert called.get("args") is not None
    assert called["args"][1] == "123"


async def test_single_registered_account_auto_opens(monkeypatch):
    _ensure_heavy_stubs()
    import commands.telemetry_cmds as tc

    async def fake_load_last_kvk_map():
        return {}

    def fake_load_registry():
        return {str(99): {"accounts": {"Main": {"GovernorID": 999, "GovernorName": "X"}}}}

    called = {"run_target_lookup": 0}

    async def fake_run_target_lookup(interaction, gid, ephemeral=False):
        called["run_target_lookup"] += 1
        called["gid"] = gid

    monkeypatch.setattr(
        tc, "safe_defer", lambda ctx, ephemeral=True: asyncio.sleep(0), raising=False
    )
    monkeypatch.setattr(tc, "load_last_kvk_map", fake_load_last_kvk_map)

    async def fake_to_thread(fn, *a, **k):
        return fn(*a, **k)

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(tc, "load_registry", fake_load_registry)
    monkeypatch.setattr(tc, "run_target_lookup", fake_run_target_lookup)

    ctx = DummyCtx(user_id=99)
    handler = _get_registered_command_impl(tc, "mykvktargets")
    assert handler is not None

    await handler(ctx, governorid=None, only_me=False)
    assert called["run_target_lookup"] == 1
    assert str(called["gid"]) == "999"


async def test_multi_account_builds_selector(monkeypatch):
    _ensure_heavy_stubs()
    import commands.telemetry_cmds as tc

    async def fake_load_last_kvk_map():
        return {}

    def fake_load_registry():
        return {
            str(5): {
                "accounts": {
                    "Main": {"GovernorID": 1, "GovernorName": "A"},
                    "Alt 1": {"GovernorID": 2, "GovernorName": "B"},
                }
            }
        }

    async def fake_to_thread(fn, *a, **k):
        return fn(*a, **k)

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(tc, "load_registry", fake_load_registry)
    monkeypatch.setattr(tc, "load_last_kvk_map", fake_load_last_kvk_map)
    monkeypatch.setattr(
        tc, "safe_defer", lambda ctx, ephemeral=True: asyncio.sleep(0), raising=False
    )

    created = {}

    def fake_make_kvk_targets_view(ctx, options, on_select_governor, **kwargs):
        created["options"] = options
        created["on_select_callable"] = on_select_governor
        return "fake_view"

    monkeypatch.setattr(tc, "make_kvk_targets_view", fake_make_kvk_targets_view)

    ctx = DummyCtx(user_id=5)
    handler = _get_registered_command_impl(tc, "mykvktargets")
    assert handler is not None

    await handler(ctx, governorid=None, only_me=True)

    assert "options" in created
    assert isinstance(created["options"], list)
    assert ctx.followup.sent, "Expected a followup call to send the selector message"


async def test_no_registered_accounts_shows_hint_and_empty_picker(monkeypatch):
    _ensure_heavy_stubs()
    import commands.telemetry_cmds as tc

    async def fake_load_last_kvk_map():
        return {}

    def fake_load_registry():
        return {str(7): {"accounts": {}}}

    async def fake_to_thread(fn, *a, **k):
        return fn(*a, **k)

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(tc, "load_registry", fake_load_registry)
    monkeypatch.setattr(tc, "load_last_kvk_map", fake_load_last_kvk_map)
    monkeypatch.setattr(
        tc, "safe_defer", lambda ctx, ephemeral=True: asyncio.sleep(0), raising=False
    )

    captured = {}

    def fake_make_kvk_targets_view(ctx, options, on_select_governor, **kwargs):
        captured["options"] = options
        return "empty_view"

    monkeypatch.setattr(tc, "make_kvk_targets_view", fake_make_kvk_targets_view)

    ctx = DummyCtx(user_id=7)
    handler = _get_registered_command_impl(tc, "mykvktargets")
    assert handler is not None

    await handler(ctx, governorid=None, only_me=True)

    assert ctx.followup.sent, "Expected followup hint when no accounts"
    assert "options" in captured and captured["options"] == []
