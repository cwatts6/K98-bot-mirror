from __future__ import annotations

import inspect
from types import SimpleNamespace

import pytest


class _FakeGroup:
    def __init__(self, name, description=None, guild_ids=None):
        self.name = name
        self.description = description
        self.guild_ids = guild_ids
        self.commands = {}

    def command(self, *, name, description=None, guild_ids=None):
        def decorator(fn):
            self.commands[name] = fn
            return fn

        return decorator


def _unwrap(fn):
    while hasattr(fn, "__wrapped__"):
        fn = fn.__wrapped__
    return fn


def _register_kvk(monkeypatch):
    import commands.kvk_cmds as kvk_cmds

    created = {}

    def fake_group(*args, **kwargs):
        group = _FakeGroup(*args, **kwargs)
        created["group"] = group
        return group

    bot = SimpleNamespace(added=[])
    bot.add_application_command = lambda command: bot.added.append(command)
    monkeypatch.setattr(kvk_cmds.discord, "SlashCommandGroup", fake_group)

    kvk_cmds.register_kvk(bot)
    return kvk_cmds, created["group"], bot


def test_register_kvk_declares_player_group(monkeypatch):
    _module, group, bot = _register_kvk(monkeypatch)

    assert group.name == "kvk"
    assert set(group.commands) == {"stats", "targets", "history", "rankings"}
    assert bot.added == [group]


def test_kvk_rankings_type_option_is_required():
    import commands.kvk_cmds as kvk_cmds

    source = inspect.getsource(kvk_cmds.register_kvk)

    assert 'name="type"' in source
    assert "required=True" in source
    assert 'choices=["kvk", "honor", "prekvk"]' in source


@pytest.mark.asyncio
async def test_kvk_rankings_routes_all_modes(monkeypatch):
    kvk_cmds, group, _bot = _register_kvk(monkeypatch)
    handler = _unwrap(group.commands["rankings"])
    ctx = SimpleNamespace(responded=[])

    calls = []

    async def fake_kvk(ctx_arg):
        calls.append(("kvk", ctx_arg))

    async def fake_honor(ctx_arg):
        calls.append(("honor", ctx_arg))

    async def fake_defer(ctx_arg, *, ephemeral=False):
        calls.append(("defer", ephemeral, ctx_arg))

    async def fake_prekvk_report(**kwargs):
        calls.append(("prekvk", kwargs))

    async def fake_channel_guarded(ctx_arg, channel_id, *, admin_override, command_name, callback):
        calls.append(("guard", channel_id, admin_override, command_name, callback.__name__))
        await callback(ctx_arg)

    async def fake_tracked(ctx=None, *, command_name, callback):
        calls.append(("tracked", command_name, callback.__name__))
        await callback(ctx)

    async def fake_respond(message, *, ephemeral=False):
        ctx.responded.append((message, ephemeral))

    ctx.respond = fake_respond
    monkeypatch.setattr(kvk_cmds, "_send_kvk_rankings", fake_kvk)
    monkeypatch.setattr(kvk_cmds, "_send_honor_rankings", fake_honor)
    monkeypatch.setattr(kvk_cmds, "_run_channel_guarded", fake_channel_guarded)
    monkeypatch.setattr(kvk_cmds, "_run_tracked", fake_tracked)
    monkeypatch.setattr(kvk_cmds, "safe_defer", fake_defer)
    monkeypatch.setattr(kvk_cmds, "send_prekvk_report", fake_prekvk_report)
    monkeypatch.setattr(
        kvk_cmds.report_service,
        "parse_report_sort",
        lambda value: f"parsed:{value}",
    )

    await handler(ctx, "kvk")
    await handler(ctx, "honor")
    await handler(ctx, "prekvk")
    await handler(ctx, "bad")

    assert calls[0][0:4] == ("guard", kvk_cmds.KVK_PLAYER_STATS_CHANNEL_ID, True, "kvk rankings")
    assert calls[1] == ("kvk", ctx)
    assert calls[2][0:4] == (
        "guard",
        kvk_cmds.KVK_PLAYER_STATS_CHANNEL_ID,
        False,
        "kvk rankings",
    )
    assert calls[3] == ("honor", ctx)
    assert calls[4] == ("tracked", "kvk rankings", "_send_prekvk_rankings")
    assert calls[5] == ("defer", True, ctx)
    assert calls[6][0] == "prekvk"
    assert calls[6][1]["ctx"] is ctx
    assert calls[6][1]["sort_by"] == "parsed:Overall"
    assert calls[6][1]["limit"] == 10
    assert ctx.responded == [("Unknown ranking type.", True)]


@pytest.mark.asyncio
async def test_kvk_stats_multi_account_selector_uses_visual_card(monkeypatch):
    import commands.kvk_cmds as kvk_cmds

    async def fake_safe_defer(_ctx, *, ephemeral=False):
        return None

    async def fake_account_summary(_user_id):
        return kvk_cmds.governor_account_service.summarize_accounts(
            {
                "Main": {"GovernorID": "123", "GovernorName": "MainGov"},
                "Alt 1": {"GovernorID": "456", "GovernorName": "AltGov"},
            }
        )

    async def fake_last_kvk_map():
        return {}

    created = {}

    class StubMyKVKStatsSelectView:
        def __init__(
            self,
            *,
            ctx,
            accounts,
            author_id,
            use_visual_card=False,
        ):
            created["ctx"] = ctx
            created["accounts"] = accounts
            created["author_id"] = author_id
            created["use_visual_card"] = use_visual_card
            self._last_kvk_map = None

    class DummyInteraction:
        def __init__(self):
            self.edits = []

        async def edit_original_response(self, **kwargs):
            self.edits.append(kwargs)
            return SimpleNamespace(id="edited")

    ctx = SimpleNamespace(
        user=SimpleNamespace(id=42),
        interaction=DummyInteraction(),
        bot=SimpleNamespace(),
    )

    monkeypatch.setattr(kvk_cmds, "safe_defer", fake_safe_defer)
    monkeypatch.setattr(
        kvk_cmds.governor_account_service,
        "get_account_summary_for_user",
        fake_account_summary,
    )
    monkeypatch.setattr(kvk_cmds.kvk_personal_service, "load_last_kvk_map", fake_last_kvk_map)
    monkeypatch.setattr(kvk_cmds, "MyKVKStatsSelectView", StubMyKVKStatsSelectView)

    await kvk_cmds._send_personal_kvk_stats(ctx)

    assert created["use_visual_card"] is True
    assert ctx.interaction.edits[-1]["view"]._last_kvk_map == {}


@pytest.mark.asyncio
async def test_kvk_stats_single_account_keeps_error_when_post_fails(monkeypatch):
    import commands.kvk_cmds as kvk_cmds

    async def fake_safe_defer(_ctx, *, ephemeral=False):
        return None

    async def fake_account_summary(_user_id):
        return kvk_cmds.governor_account_service.summarize_accounts(
            {"Main": {"GovernorID": "123", "GovernorName": "MainGov"}}
        )

    async def fake_last_kvk_map():
        return {}

    async def fake_load_stats(governor_id):
        return {"GovernorID": governor_id, "GovernorName": "MainGov"}

    async def fake_post_stats_output(**_kwargs):
        return False, "none"

    class DummyInteraction:
        def __init__(self):
            self.edits = []

        async def edit_original_response(self, **kwargs):
            self.edits.append(kwargs)
            return SimpleNamespace(id="edited")

    ctx = SimpleNamespace(
        user=SimpleNamespace(id=42),
        interaction=DummyInteraction(),
        bot=SimpleNamespace(),
    )

    monkeypatch.setattr(kvk_cmds, "safe_defer", fake_safe_defer)
    monkeypatch.setattr(
        kvk_cmds.governor_account_service,
        "get_account_summary_for_user",
        fake_account_summary,
    )
    monkeypatch.setattr(kvk_cmds.kvk_personal_service, "load_last_kvk_map", fake_last_kvk_map)
    monkeypatch.setattr(
        kvk_cmds.kvk_personal_service,
        "load_kvk_personal_stats",
        fake_load_stats,
    )
    monkeypatch.setattr(kvk_cmds, "post_kvk_stats_output", fake_post_stats_output)

    await kvk_cmds._send_personal_kvk_stats(ctx)

    assert "Could not post your KVK stats publicly" in ctx.interaction.edits[-1]["content"]


@pytest.mark.asyncio
async def test_kvk_targets_manual_id_uses_modern_output(monkeypatch):
    import commands.kvk_cmds as kvk_cmds

    async def fake_safe_defer(_ctx, *, ephemeral=False):
        return None

    async def fake_last_kvk_map():
        return {}

    called = {}

    async def fake_post(interaction, governor_id, *, ephemeral):
        called["interaction"] = interaction
        called["governor_id"] = governor_id
        called["ephemeral"] = ephemeral

    class DummyInteraction:
        def __init__(self):
            self.edits = []

        async def edit_original_response(self, **kwargs):
            self.edits.append(kwargs)

    ctx = SimpleNamespace(
        user=SimpleNamespace(id=42),
        interaction=DummyInteraction(),
        followup=SimpleNamespace(),
    )

    monkeypatch.setattr(kvk_cmds, "safe_defer", fake_safe_defer)
    monkeypatch.setattr(kvk_cmds.kvk_personal_service, "load_last_kvk_map", fake_last_kvk_map)
    monkeypatch.setattr(kvk_cmds, "post_kvk_targets_output", fake_post)

    await kvk_cmds._send_personal_kvk_targets(ctx, "123", True)

    assert called == {
        "interaction": ctx.interaction,
        "governor_id": "123",
        "ephemeral": True,
    }
    assert ctx.interaction.edits[-1] == {"content": " ", "view": None}


@pytest.mark.asyncio
async def test_kvk_targets_single_account_uses_modern_output(monkeypatch):
    import commands.kvk_cmds as kvk_cmds

    async def fake_safe_defer(_ctx, *, ephemeral=False):
        return None

    async def fake_last_kvk_map():
        return {}

    async def fake_account_summary(_user_id):
        return kvk_cmds.governor_account_service.summarize_accounts(
            {"Main": {"GovernorID": "987", "GovernorName": "Only"}}
        )

    called = {}

    async def fake_post(_interaction, governor_id, *, ephemeral):
        called["governor_id"] = governor_id
        called["ephemeral"] = ephemeral

    class DummyInteraction:
        def __init__(self):
            self.edits = []

        async def edit_original_response(self, **kwargs):
            self.edits.append(kwargs)

    ctx = SimpleNamespace(
        user=SimpleNamespace(id=42),
        interaction=DummyInteraction(),
        followup=SimpleNamespace(),
    )

    monkeypatch.setattr(kvk_cmds, "safe_defer", fake_safe_defer)
    monkeypatch.setattr(kvk_cmds.kvk_personal_service, "load_last_kvk_map", fake_last_kvk_map)
    monkeypatch.setattr(
        kvk_cmds.governor_account_service,
        "get_account_summary_for_user",
        fake_account_summary,
    )
    monkeypatch.setattr(kvk_cmds, "post_kvk_targets_output", fake_post)

    await kvk_cmds._send_personal_kvk_targets(ctx, None, False)

    assert called == {"governor_id": "987", "ephemeral": False}
