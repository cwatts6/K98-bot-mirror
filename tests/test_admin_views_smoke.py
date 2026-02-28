# tests/test_admin_views_smoke.py
import asyncio
import importlib
import sys
import types


def _load_admin_views(monkeypatch):
    bot_cfg = types.ModuleType("bot_config")
    bot_cfg.ADMIN_USER_ID = 123
    monkeypatch.setitem(sys.modules, "bot_config", bot_cfg)

    const = types.ModuleType("constants")
    const.RESTART_EXIT_CODE = 17
    const.RESTART_FLAG_PATH = "/tmp/restart.flag"
    monkeypatch.setitem(sys.modules, "constants", const)

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


class _DummyCtx:
    def __init__(self):
        self.interaction = types.SimpleNamespace(original_response=self._orig)

    async def _orig(self):
        return types.SimpleNamespace(edit=self._async_noop)

    async def _async_noop(self, *args, **kwargs):
        return None


class _DummyBot:
    def get_channel(self, _cid):
        return types.SimpleNamespace(send=self._async_noop)

    async def _async_noop(self, *args, **kwargs):
        return None


def test_confirm_views_instantiate_and_callbacks_exist(monkeypatch):
    m = _load_admin_views(monkeypatch)

    async def _run():
        restart_view = m.ConfirmRestartView(_DummyCtx(), bot=_DummyBot(), notify_channel_id=1)
        import_view = m.ConfirmImportView(
            author_id=123, on_confirm_apply=lambda _i: _DummyInteraction()._async_noop()
        )

        assert len(restart_view.children) >= 2
        assert len(import_view.children) >= 2

        # buttons exist with callbacks
        assert callable(restart_view.children[0].callback)
        assert callable(import_view.children[0].callback)

        # interaction_check gating works
        ok = await import_view.interaction_check(_DummyInteraction(uid=123))
        bad = await import_view.interaction_check(_DummyInteraction(uid=999))
        assert ok is True
        assert bad is False

    asyncio.run(_run())
