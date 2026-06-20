from __future__ import annotations

import asyncio
import os
import sys
import types
from types import SimpleNamespace

sys.modules.setdefault("aiofiles", types.ModuleType("aiofiles"))
os.environ.setdefault("OUR_KINGDOM", "0")
if "dotenv" not in sys.modules:
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda *args, **kwargs: None
    sys.modules["dotenv"] = dotenv

from ui.views.mge_simplified_signup_view import MGESimplifiedSignupView


class _FakeAdminDeps:
    def __init__(self):
        self.admin_role_ids = {9001}
        self.leadership_role_ids = {9002}
        self.refreshed_event_ids: list[int] = []

    def is_admin(self, interaction) -> bool:
        return False

    def refresh_embed(self, event_id: int) -> None:
        self.refreshed_event_ids.append(int(event_id))


class _FakeResponse:
    def __init__(self):
        self.modal = None
        self.messages: list[str] = []

    async def send_modal(self, modal):
        self.modal = modal

    async def send_message(self, message: str, ephemeral: bool = False):
        self.messages.append(message)


class _FakeInteraction:
    def __init__(self, user_id: int = 1):
        self.user = SimpleNamespace(id=user_id)
        self.guild = None
        self.response = _FakeResponse()


def _build_view() -> MGESimplifiedSignupView:
    async def _make() -> MGESimplifiedSignupView:
        return MGESimplifiedSignupView(event_id=101, admin_deps=_FakeAdminDeps())

    return asyncio.run(_make())


def test_simplified_view_limits_public_buttons():
    view = _build_view()
    labels = [getattr(child, "label", "") for child in view.children]

    assert labels == ["Sign Up", "Withdraw", "Edit Sign Up"]
