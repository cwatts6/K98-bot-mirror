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


def test_register_governor_confirm_defers_writes_and_edits_prompt(monkeypatch):
    rv = _load_registry_views(monkeypatch)
    calls = []

    def _register_account(**kwargs):
        calls.append(kwargs)
        return True, None

    monkeypatch.setattr(rv, "register_account", _register_account)

    async def _run():
        view = rv.RegisterGovernorView(_User(1), "Main", "123", "Alice")
        interaction = _FakeInteraction(_User(1))

        await _button(view, "✅ Confirm").callback(interaction)

        assert interaction.response.deferred_ephemeral is True
        assert calls == [
            {
                "discord_id": "1",
                "discord_name": "User(1)",
                "account_type": "Main",
                "governor_id": "123",
                "governor_name": "Alice",
            }
        ]
        assert interaction.original_edits[-1]["view"] is None
        assert "Registered `Main`" in interaction.original_edits[-1]["content"]

    asyncio.run(_run())


def test_modify_governor_confirm_defers_writes_and_edits_prompt(monkeypatch):
    rv = _load_registry_views(monkeypatch)
    calls = []

    def _register_account(**kwargs):
        calls.append(kwargs)
        return True, None

    monkeypatch.setattr(rv, "register_account", _register_account)

    async def _run():
        view = rv.ModifyGovernorView(_User(1), "Alt 1", "456", "Bob")
        interaction = _FakeInteraction(_User(1))

        await _button(view, "✅ Confirm Change").callback(interaction)

        assert interaction.response.deferred_ephemeral is True
        assert calls == [
            {
                "discord_id": "1",
                "discord_name": "User(1)",
                "account_type": "Alt 1",
                "governor_id": "456",
                "governor_name": "Bob",
            }
        ]
        assert interaction.original_edits[-1]["view"] is None
        assert "`Alt 1` updated" in interaction.original_edits[-1]["content"]

    asyncio.run(_run())


def test_remove_governor_confirm_defers_write_and_clears_prompt(monkeypatch):
    rv = _load_registry_views(monkeypatch)
    calls = []

    def _remove_governor(**kwargs):
        calls.append(kwargs)
        return True, None

    monkeypatch.setattr(rv, "remove_governor", _remove_governor)

    async def _run():
        view = rv.ConfirmRemoveView(_User(1), "Farm 1")
        interaction = _FakeInteraction(_User(1))

        await _button(view, "✅ Confirm Remove").callback(interaction)

        assert interaction.response.deferred_ephemeral is True
        assert calls == [
            {
                "discord_user_id": 1,
                "account_type": "Farm 1",
                "removed_by": 1,
            }
        ]
        assert interaction.original_edits[-1]["view"] is None
        assert "`Farm 1` has been removed" in interaction.original_edits[-1]["content"]

    asyncio.run(_run())


def test_confirmation_cancel_callbacks_clear_prompt(monkeypatch):
    rv = _load_registry_views(monkeypatch)

    async def _run():
        view = rv.RegisterGovernorView(_User(1), "Main", "123", "Alice")
        interaction = _FakeInteraction(_User(1))

        await _button(view, "❌ Cancel").callback(interaction)

        assert interaction.response.edits[-1]["view"] is None
        assert "cancelled" in interaction.response.edits[-1]["content"]

    asyncio.run(_run())


def _button(view, label: str):
    return next(child for child in view.children if getattr(child, "label", "") == label)


class _User:
    def __init__(self, user_id: int):
        self.id = user_id

    def __str__(self) -> str:
        return f"User({self.id})"


class _FakeResponse:
    def __init__(self):
        self.deferred_ephemeral = None
        self.done = False
        self.edits = []
        self.messages = []

    def is_done(self):
        return self.done

    async def defer(self, *, ephemeral=False):
        self.done = True
        self.deferred_ephemeral = ephemeral

    async def send_message(self, content=None, *, ephemeral=False, **kwargs):
        self.done = True
        self.messages.append({"content": content, "ephemeral": ephemeral, **kwargs})

    async def edit_message(self, content=None, *, view=None, **kwargs):
        self.done = True
        self.edits.append({"content": content, "view": view, **kwargs})


class _FakeFollowup:
    def __init__(self):
        self.messages = []

    async def send(self, content=None, *, ephemeral=False, **kwargs):
        self.messages.append({"content": content, "ephemeral": ephemeral, **kwargs})


class _FakeInteraction:
    def __init__(self, user):
        self.user = user
        self.response = _FakeResponse()
        self.followup = _FakeFollowup()
        self.original_edits = []

    async def edit_original_response(self, content=None, *, view=None, **kwargs):
        self.original_edits.append({"content": content, "view": view, **kwargs})
