# tests/test_admin_views_smoke.py
import asyncio
import importlib
import sys
import types


def _load_admin_views(monkeypatch):
    if "ui.views.admin_views" in sys.modules:
        del sys.modules["ui.views.admin_views"]
    return importlib.import_module("ui.views.admin_views")


class _DummyInteraction:
    def __init__(self, uid=123):
        self.user = types.SimpleNamespace(id=uid)
        self.response = types.SimpleNamespace(
            send_message=self._async_noop,
            edit_message=self._async_noop,
        )
        self.followup = types.SimpleNamespace(send=self._async_noop)

    async def _async_noop(self, *args, **kwargs):
        return None


def test_confirm_views_instantiate_and_callbacks_exist(monkeypatch):
    m = _load_admin_views(monkeypatch)

    async def _run():
        import_view = m.ConfirmImportView(
            author_id=123, on_confirm_apply=lambda _i: _DummyInteraction()._async_noop()
        )

        assert len(import_view.children) >= 2

        # buttons exist with callbacks
        assert callable(import_view.children[0].callback)

        # interaction_check gating works
        ok = await import_view.interaction_check(_DummyInteraction(uid=123))
        bad = await import_view.interaction_check(_DummyInteraction(uid=999))
        assert ok is True
        assert bad is False

    asyncio.run(_run())
