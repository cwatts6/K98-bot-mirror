# tests/test_registry_views_smoke.py
import asyncio
import importlib
import os
import sys
import types


def _load_registry_views(monkeypatch):
    os.environ.setdefault("OUR_KINGDOM", "0")
    monkeypatch.setitem(sys.modules, "aiofiles", types.SimpleNamespace(open=None))

    # Stub the facade dependency used by registry_views without importing SQL-backed code.
    gov_stub = types.ModuleType("registry.governor_registry")
    gov_stub.load_registry = lambda: {}
    gov_stub.register_account = lambda **_kw: (True, None)
    monkeypatch.setitem(sys.modules, "registry.governor_registry", gov_stub)

    # Stub registry_service so any import from it doesn't attempt a SQL connection.
    svc_stub = types.ModuleType("registry.registry_service")
    svc_stub.VALID_ACCOUNT_TYPES = frozenset(
        {
            "Main",
            *[f"Alt {i}" for i in range(1, 6)],
            *[f"Farm {i}" for i in range(1, 21)],
        }
    )
    svc_stub.check_governor_claimed_by_other = lambda governor_id, owner_discord_id: False
    svc_stub.get_user_accounts = lambda uid: {}
    svc_stub.remove_governor = lambda **_kw: (True, None)
    monkeypatch.setitem(sys.modules, "registry.registry_service", svc_stub)

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
        v5 = rv.RegisterGovernorView(_User(1), "Main", "1", "A")
        v6 = rv.ModifyGovernorView(_User(1), "Main", "2", "B")
        v7 = rv.ConfirmRemoveView(_User(1), "Main")
        assert v1.author_id == 1
        assert m1.author_id == 1
        assert len(v2.children) == 1
        assert len(v3.children) == 1
        assert m2.account_type == "Main"
        assert len(v4.children) == 1
        assert v5.governor_id == "1"
        assert v6.new_gov_id == "2"
        assert v7.account_type == "Main"

    asyncio.run(_run())


class _User:
    def __init__(self, user_id: int):
        self.id = user_id

    def __str__(self) -> str:
        return f"User({self.id})"
