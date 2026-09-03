# tests/test_admin_views_smoke.py
import asyncio
import importlib
import sys
import types

import pytest

from core.discord_embed_limits import require_valid_embed_payload


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


@pytest.mark.asyncio
async def test_log_tail_view_replaces_attachment_and_redacts_complete_page(tmp_path, monkeypatch):
    m = _load_admin_views(monkeypatch)
    path = tmp_path / "operator.log"
    path.write_text(
        "\n".join(["normal line " + ("X" * 100)] * 400 + ["Authorization: Bearer secret-token"]),
        encoding="utf-8",
    )

    class FakeFile:
        def __init__(self, fp, filename):
            fp.seek(0)
            self.filename = filename
            self.content = fp.read()

    class Interaction:
        attachment_size_limit = 1_000_000

        def __init__(self):
            self.response = types.SimpleNamespace(is_done=lambda: True)
            self.kwargs = None

        async def edit_original_response(self, **kwargs):
            self.kwargs = kwargs

    monkeypatch.setattr(m.discord, "File", FakeFile)
    interaction = Interaction()
    view = m.LogTailView(None, str(path), "Operator Log", page_size=200)

    await view.render(interaction)

    assert interaction.kwargs["attachments"] == []
    assert len(interaction.kwargs["files"]) == 1
    attachment_text = interaction.kwargs["files"][0].content.decode("utf-8")
    assert "secret-token" not in attachment_text
    assert "[REDACTED]" in attachment_text
    require_valid_embed_payload(interaction.kwargs["embed"])


@pytest.mark.asyncio
async def test_log_tail_view_reports_destination_limit_without_partial_file(tmp_path):
    m = _load_admin_views(None)
    path = tmp_path / "operator.log"
    path.write_text("\n".join("X" * 100 for _ in range(200)), encoding="utf-8")

    class Interaction:
        attachment_size_limit = 50

        def __init__(self):
            self.response = types.SimpleNamespace(is_done=lambda: True)
            self.kwargs = None

        async def edit_original_response(self, **kwargs):
            self.kwargs = kwargs

    interaction = Interaction()
    view = m.LogTailView(None, str(path), "Operator Log", page_size=200)

    await view.render(interaction)

    assert interaction.kwargs["attachments"] == []
    embed = interaction.kwargs["embed"]
    assert any("above this destination" in field.value for field in embed.fields)
    require_valid_embed_payload(embed)
