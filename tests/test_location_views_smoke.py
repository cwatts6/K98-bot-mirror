# tests/test_location_views_smoke.py
import asyncio
import importlib


class _DummyResp:
    async def send_message(self, *args, **kwargs):
        return None

    async def defer(self, *args, **kwargs):
        return None


class _DummyFollow:
    async def send(self, *args, **kwargs):
        return None


class _DummyChannel:
    async def send(self, *args, **kwargs):
        return None


class _DummyMessage:
    async def edit(self, *args, **kwargs):
        return None


class _DummyUser:
    def __init__(self, uid):
        self.id = uid


class _DummyInteraction:
    def __init__(self, uid=1):
        self.user = _DummyUser(uid)
        self.response = _DummyResp()
        self.followup = _DummyFollow()
        self.channel = _DummyChannel()
        self.message = _DummyMessage()
        self.guild = None


async def _embed_for(_gid):
    import discord

    return discord.Embed(title="ok")


def test_location_views_instantiate_and_build_options():
    lv = importlib.import_module("ui.views.location_views")

    async def _run():
        async def _on_profile(_interaction, _gid, _ephemeral):
            return None

        async def _request_refresh(_interaction):
            return True, "OK"

        async def _wait(_timeout):
            return True

        async def _guard(coro):
            await coro()

        async def _timeout(_interaction):
            return None

        lv.configure_location_views(
            on_profile_selected=_on_profile,
            on_request_refresh=_request_refresh,
            on_wait_for_refresh=_wait,
            build_refreshed_location_embed=_embed_for,
            check_refresh_permission=lambda _i: True,
            is_refresh_running=lambda: False,
            is_refresh_rate_limited=lambda: (False, 0),
            mark_refresh_started=lambda: None,
            run_refresh_guarded=_guard,
            on_refresh_timeout=_timeout,
        )

        v1 = lv.LocationSelectView(
            matches=[("Alice", 123456), {"GovernorName": "Bob", "GovernorID": 654321}],
            ephemeral=True,
            author_id=1,
        )
        assert len(v1.children) == 1

        select = v1.children[0]
        assert len(select.options) >= 2

        v2 = lv.RefreshLocationView(target_id=123456, ephemeral=True)
        assert len(v2.children) == 1

    asyncio.run(_run())
