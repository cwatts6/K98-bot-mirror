# tests/test_registry_views_smoke.py
import asyncio
import importlib
import os
import sys
import types

import discord


def _load_registry_views(monkeypatch):
    os.environ.setdefault("OUR_KINGDOM", "0")
    monkeypatch.setitem(sys.modules, "aiofiles", types.SimpleNamespace(open=None))

    gov_stub = types.ModuleType("governor_registry")

    class _DummyView(discord.ui.View):
        def __init__(self, *args, **kwargs):
            super().__init__(timeout=10)

    gov_stub.ConfirmRemoveView = _DummyView
    gov_stub.ModifyGovernorView = _DummyView
    gov_stub.RegisterGovernorView = _DummyView
    monkeypatch.setitem(sys.modules, "governor_registry", gov_stub)

    utils_stub = types.ModuleType("utils")
    utils_stub.normalize_governor_id = lambda v: str(v).strip()
    monkeypatch.setitem(sys.modules, "utils", utils_stub)

    if "ui.views.registry_views" in sys.modules:
        del sys.modules["ui.views.registry_views"]
    return importlib.import_module("ui.views.registry_views")


def test_registry_views_instantiate(monkeypatch):
    rv = _load_registry_views(monkeypatch)

    async def _run():
        async def _async_load_registry():
            return {}

        async def _lookup(_name):
            return {"status": "not_found", "message": "No results found."}

        async def _send_profile(*_a, **_k):
            return None

        rv.configure_registry_views(
            async_load_registry=_async_load_registry,
            lookup_governor_id=_lookup,
            target_lookup_view_factory=None,
            name_cache_getter=lambda: {"rows": []},
            send_profile_to_channel=_send_profile,
            account_order_getter=lambda: ["Main", "Alt 1"],
        )
        v1 = rv.MyRegsActionView(author_id=1, has_regs=True)
        m1 = rv.GovNameModal(author_id=1)
        v2 = rv.RegisterStartView(author_id=1, free_slots=["Main"])
        v3 = rv.ModifyStartView(
            author_id=1, accounts={"Main": {"GovernorID": "1", "GovernorName": "A"}}
        )
        m2 = rv.EnterGovernorIDModal(author_id=1, mode="register", account_type="Main")
        v4 = rv.GovernorSelectView([("A", 1)], author_id=1)
        assert v1.author_id == 1
        assert m1.author_id == 1
        assert len(v2.children) == 1
        assert len(v3.children) == 1
        assert m2.account_type == "Main"
        assert len(v4.children) == 1

    asyncio.run(_run())
