# tests/test_events_views.py
import asyncio
import importlib
import sys
import types

import discord


class _StubLocalTimeToggleView(discord.ui.View):
    def __init__(self, events, prefix="default", timeout=None):
        super().__init__(timeout=timeout)
        self.events = events
        self.prefix = prefix
        self.add_item(
            discord.ui.Button(
                label="Show in my local time",
                custom_id=f"{self.prefix}_local_time_toggle",
            )
        )


def _load_module_with_stubs(monkeypatch):
    embed_stub = types.ModuleType("embed_utils")
    embed_stub.LocalTimeToggleView = _StubLocalTimeToggleView
    embed_stub.format_event_embed = lambda rows: {"rows": list(rows)}
    embed_stub.format_fight_embed = lambda rows: {"rows": list(rows)}

    utils_stub = types.ModuleType("utils")
    utils_stub.get_next_fights = lambda n: []
    utils_stub.get_next_events = lambda limit=5: []

    monkeypatch.setitem(sys.modules, "embed_utils", embed_stub)
    monkeypatch.setitem(sys.modules, "utils", utils_stub)

    if "ui.views.events_views" in sys.modules:
        del sys.modules["ui.views.events_views"]
    return importlib.import_module("ui.views.events_views")


class _FakeResponse:
    def __init__(self):
        self.edits = []
        self.deferred = 0

    async def edit_message(self, **kwargs):
        self.edits.append(kwargs)

    async def defer(self):
        self.deferred += 1


class _FakeInteraction:
    def __init__(self):
        self.response = _FakeResponse()


def test_nextfight_custom_id_prefix_no_drift(monkeypatch):
    ev = _load_module_with_stubs(monkeypatch)
    monkeypatch.setattr(ev, "get_next_fights", lambda n: [{"name": "A", "start_time": 1}])

    async def _case():
        view = ev.NextFightView(initial_limit=1, prefix="nextfight")
        custom_ids = [getattr(c, "custom_id", "") for c in view.children]
        assert "nextfight_local_time_toggle" in custom_ids

    asyncio.run(_case())


def test_nextevent_custom_id_prefix_no_drift(monkeypatch):
    ev = _load_module_with_stubs(monkeypatch)
    preloaded = [{"name": "A", "start_time": 1}]

    async def _case():
        view = ev.NextEventView(initial_limit=1, prefix="nextevent", preloaded=preloaded)
        custom_ids = [getattr(c, "custom_id", "") for c in view.children]
        assert "nextevent_local_time_toggle" in custom_ids

    asyncio.run(_case())


def test_nextfight_button_callback_executes(monkeypatch):
    ev = _load_module_with_stubs(monkeypatch)
    fights = [
        {"name": "F1", "start_time": 1},
        {"name": "F2", "start_time": 2},
        {"name": "F3", "start_time": 3},
    ]
    monkeypatch.setattr(ev, "get_next_fights", lambda n: fights)

    async def _case():
        view = ev.NextFightView(initial_limit=1, prefix="nextfight")
        interaction = _FakeInteraction()
        btn = next(c for c in view.children if getattr(c, "label", "").startswith("Next 3"))
        await btn.callback(interaction)

        assert view.limit > 1
        assert len(view.fights) == 3
        assert interaction.response.edits, "button callback should edit interaction message"

    asyncio.run(_case())


def test_nextevent_button_callback_executes(monkeypatch):
    ev = _load_module_with_stubs(monkeypatch)
    events = [
        {"name": "E1", "start_time": 1},
        {"name": "E2", "start_time": 2},
        {"name": "E3", "start_time": 3},
        {"name": "E4", "start_time": 4},
        {"name": "E5", "start_time": 5},
    ]
    monkeypatch.setattr(ev, "get_next_events", lambda limit=5: events)

    async def _case():
        view = ev.NextEventView(initial_limit=1, prefix="nextevent", preloaded=events)
        interaction = _FakeInteraction()
        btn = next(c for c in view.children if getattr(c, "label", "").startswith("Next 5"))
        await btn.callback(interaction)

        assert view.limit > 1
        assert len(view.events) == 5
        assert interaction.response.edits, "button callback should edit interaction message"

    asyncio.run(_case())
