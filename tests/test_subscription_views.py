# tests/test_subscription_views.py
import asyncio
import importlib
import sys
import types


class _DummyUser:
    def __init__(self, uid: int):
        self.id = uid
        self.mention = f"<@{uid}>"

    async def send(self, *args, **kwargs):
        return None


async def _noop_confirm(_interaction, _view):
    return None


async def _noop_unsub(_interaction, _view):
    return None


def _load_module(monkeypatch):
    constants_stub = types.ModuleType("constants")
    constants_stub.DEFAULT_REMINDER_TIMES = ["5m", "15m", "30m"]
    constants_stub.VALID_TYPES = ["ruins", "altars", "major", "fights", "all"]
    monkeypatch.setitem(sys.modules, "constants", constants_stub)

    utils_stub = types.ModuleType("utils")
    utils_stub.make_cid = lambda scope, uid: f"{scope}:{uid}:abc123"
    monkeypatch.setitem(sys.modules, "utils", utils_stub)

    if "ui.views.subscription_views" in sys.modules:
        del sys.modules["ui.views.subscription_views"]
    return importlib.import_module("ui.views.subscription_views")


def test_subscription_view_subscribe_mode_components_and_custom_ids(monkeypatch):
    m = _load_module(monkeypatch)

    async def _build():
        return m.SubscriptionView(
            user=_DummyUser(123),
            uid=123,
            username="user#0001",
            selected_types=[],
            selected_reminders=[],
            confirm_label="✅ Confirm",
            include_unsubscribe=False,
            reminder_min_values=1,
            cid_prefix="sub",
            on_confirm=_noop_confirm,
        )

    view = asyncio.run(_build())
    assert any(isinstance(c, m.DynamicEventSelect) for c in view.children)
    assert any(isinstance(c, m.ReminderSelect) for c in view.children)
    assert any(isinstance(c, m.ConfirmButton) for c in view.children)
    assert len(view.children) == 3

    assert view.event_select_id.startswith("sub:event:123:")
    assert view.reminder_select_id.startswith("sub:remind:123:")
    assert view.confirm_button_id.startswith("sub:confirm:123:")


def test_subscription_view_modify_mode_components_and_custom_ids(monkeypatch):
    m = _load_module(monkeypatch)

    async def _build():
        return m.SubscriptionView(
            user=_DummyUser(456),
            uid=456,
            username="user#0002",
            selected_types=["ruins"],
            selected_reminders=["5m"],
            confirm_label="✅ Update Preferences",
            include_unsubscribe=True,
            reminder_min_values=0,
            cid_prefix="modsub",
            on_confirm=_noop_confirm,
            on_unsubscribe=_noop_unsub,
        )

    view = asyncio.run(_build())
    assert any(isinstance(c, m.DynamicEventSelect) for c in view.children)
    assert any(isinstance(c, m.ReminderSelect) for c in view.children)
    assert any(isinstance(c, m.ConfirmButton) for c in view.children)
    assert len(view.children) == 4

    assert view.event_select_id.startswith("modsub:event:456:")
    assert view.reminder_select_id.startswith("modsub:remind:456:")
    assert view.confirm_button_id.startswith("modsub:confirm:456:")
    assert view.unsubscribe_button_id.startswith("modsub:unsubscribe:456:")
