# tests/test_ui_imports.py
import asyncio
import importlib
import os
import sys
import types


def test_import_all_ui_view_modules_and_instantiate_core_views(monkeypatch, tmp_path):
    # Avoid optional dependency/env failures in test env.
    monkeypatch.setitem(sys.modules, "aiofiles", types.SimpleNamespace(open=None))
    os.environ.setdefault("OUR_KINGDOM", "0")

    # Stub heavy deps so events_views can import without full runtime environment.
    import discord

    class _StubLocalTimeToggleView(discord.ui.View):
        def __init__(self, events, prefix="default", timeout=None):
            super().__init__(timeout=timeout)
            self.events = events
            self.prefix = prefix
            self.add_item(discord.ui.Button(label="local", custom_id=f"{prefix}_local_time_toggle"))

    embed_stub = types.ModuleType("embed_utils")
    embed_stub.LocalTimeToggleView = _StubLocalTimeToggleView
    embed_stub.format_event_embed = lambda rows: {"rows": list(rows)}
    embed_stub.format_fight_embed = lambda rows: {"rows": list(rows)}
    embed_stub.build_stats_embed = lambda *args, **kwargs: {}

    gov_stub = types.ModuleType("governor_registry")

    class _DummyView(discord.ui.View):
        def __init__(self, *args, **kwargs):
            super().__init__(timeout=10)

    gov_stub.ConfirmRemoveView = _DummyView
    gov_stub.ModifyGovernorView = _DummyView
    gov_stub.RegisterGovernorView = _DummyView
    monkeypatch.setitem(sys.modules, "governor_registry", gov_stub)

    utils_stub = types.ModuleType("utils")
    utils_stub.get_next_fights = lambda n: []
    utils_stub.get_next_events = lambda limit=5: []
    utils_stub.normalize_governor_id = lambda v: str(v).strip()
    utils_stub.make_cid = lambda scope, uid: f"{scope}:{uid}:abc123"
    utils_stub.fmt_short = lambda v: str(v)

    const_stub = types.ModuleType("constants")
    const_stub.DEFAULT_REMINDER_TIMES = ["5m", "15m"]
    const_stub.VALID_TYPES = ["ruins", "altars", "major", "fights", "all"]

    monkeypatch.setitem(sys.modules, "embed_utils", embed_stub)
    monkeypatch.setitem(sys.modules, "utils", utils_stub)
    monkeypatch.setitem(sys.modules, "constants", const_stub)

    modules = [
        "ui.views.admin_views",
        "ui.views.location_views",
        "ui.views.registry_views",
        "ui.views.stats_views",
        "ui.views.events_views",
        "ui.views.subscription_views",
    ]

    loaded = [importlib.import_module(m) for m in modules]
    assert len(loaded) == len(modules)

    # registry view module must not import command module directly
    assert "Commands" not in sys.modules

    admin = importlib.import_module("ui.views.admin_views")
    loc = importlib.import_module("ui.views.location_views")

    # Instantiate moved views inside a running loop for discord.ui.View.
    async def _make():
        logf = tmp_path / "log.txt"
        logf.write_text("INFO hello\nERROR boom\n", encoding="utf-8")
        v1 = admin.LogTailView(ctx=None, src_path=str(logf), title="Logs")
        v2 = loc.OpenFullSizeView(url="https://example.com")
        v3 = loc.ProfileLinksView(card_url="https://example.com/card")
        return v1, v2, v3

    v1, v2, v3 = asyncio.run(_make())
    assert v1.title == "Logs"
    assert len(v2.children) == 1
    assert len(v3.children) == 1
