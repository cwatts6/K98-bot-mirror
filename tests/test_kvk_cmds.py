from __future__ import annotations

import inspect
from io import BytesIO
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
    assert 'choices=["kvk", "honor", "prekvk", "records"]' in source


def test_kvk_history_keeps_governor_id_option_without_ephemeral_option(monkeypatch):
    _module, group, _bot = _register_kvk(monkeypatch)
    handler = _unwrap(group.commands["history"])

    params = inspect.signature(handler).parameters

    assert "governor_id" in params
    assert "ephemeral" not in params


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

    async def fake_prekvk(ctx_arg):
        calls.append(("prekvk", ctx_arg))

    async def fake_records(ctx_arg):
        calls.append(("records", ctx_arg))

    async def fake_channel_guarded(ctx_arg, channel_id, *, admin_override, _command_name, callback):
        calls.append(("guard", channel_id, admin_override, _command_name, callback.__name__))
        await callback(ctx_arg)

    async def fake_respond(message, *, ephemeral=False):
        ctx.responded.append((message, ephemeral))

    ctx.respond = fake_respond
    monkeypatch.setattr(kvk_cmds, "_send_kvk_rankings", fake_kvk)
    monkeypatch.setattr(kvk_cmds, "_send_honor_rankings", fake_honor)
    monkeypatch.setattr(kvk_cmds, "_send_prekvk_rankings", fake_prekvk)
    monkeypatch.setattr(kvk_cmds, "_send_hall_of_fame_rankings", fake_records)
    monkeypatch.setattr(kvk_cmds, "_run_channel_guarded", fake_channel_guarded)

    await handler(ctx, "kvk")
    await handler(ctx, "honor")
    await handler(ctx, "prekvk")
    await handler(ctx, "records")
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
    assert calls[4] == ("prekvk", ctx)
    assert calls[5][0:4] == (
        "guard",
        kvk_cmds.KVK_PLAYER_STATS_CHANNEL_ID,
        True,
        "kvk rankings",
    )
    assert calls[6] == ("records", ctx)
    assert ctx.responded == [("Unknown ranking type.", True)]


@pytest.mark.asyncio
async def test_current_rankings_sends_unified_browser(monkeypatch):
    import commands.kvk_cmds as kvk_cmds

    created = {}
    sent_message = object()

    async def fake_safe_defer(_ctx, *, ephemeral=False):
        created["defer"] = ephemeral

    async def fake_payload(**kwargs):
        created["payload_kwargs"] = kwargs
        return SimpleNamespace(
            mode="prekvk",
            metric="overall",
            limit=10,
        )

    class StubView:
        def __init__(self, *, mode, metric, limit):
            self.mode = mode
            self.metric = metric
            self.limit = limit
            self.message = None
            created["view"] = self

    class Followup:
        async def send(self, **kwargs):
            created["send_kwargs"] = kwargs
            return sent_message

    ctx = SimpleNamespace(followup=Followup())

    monkeypatch.setattr(kvk_cmds, "safe_defer", fake_safe_defer)
    monkeypatch.setattr(
        kvk_cmds.kvk_rankings_service,
        "build_current_rankings_payload",
        fake_payload,
    )
    monkeypatch.setattr(kvk_cmds, "CurrentRankingsBrowserView", StubView)
    monkeypatch.setattr(kvk_cmds, "build_current_rankings_embed", lambda payload: "embed")
    monkeypatch.setattr(kvk_cmds, "render_kvk_rankings_top10_card", lambda _payload: None)

    await kvk_cmds._send_current_rankings(ctx, mode="prekvk")

    assert created["defer"] is False
    assert created["payload_kwargs"] == {"mode": "prekvk", "metric": None, "limit": 10}
    assert created["send_kwargs"]["embed"] == "embed"
    assert created["send_kwargs"]["view"] is created["view"]
    assert created["send_kwargs"]["ephemeral"] is False
    assert created["view"].message is sent_message


@pytest.mark.asyncio
async def test_current_rankings_sends_kvk_top10_visual_card_when_available(monkeypatch):
    import commands.kvk_cmds as kvk_cmds

    created = {}
    sent_message = object()

    async def fake_safe_defer(_ctx, *, ephemeral=False):
        created["defer"] = ephemeral

    async def fake_payload(**kwargs):
        created["payload_kwargs"] = kwargs
        return SimpleNamespace(
            mode="kvk",
            metric="kills",
            limit=10,
        )

    class StubView:
        def __init__(self, *, mode, metric, limit):
            self.mode = mode
            self.metric = metric
            self.limit = limit
            self.message = None
            created["view"] = self

    class Followup:
        async def send(self, **kwargs):
            created["send_kwargs"] = kwargs
            return sent_message

    rendered = SimpleNamespace(
        filename="kvk_rankings_top10_kills.png",
        image_bytes=BytesIO(b"fake-png"),
    )
    ctx = SimpleNamespace(followup=Followup())

    monkeypatch.setattr(kvk_cmds, "safe_defer", fake_safe_defer)
    monkeypatch.setattr(
        kvk_cmds.kvk_rankings_service,
        "build_current_rankings_payload",
        fake_payload,
    )
    monkeypatch.setattr(kvk_cmds, "CurrentRankingsBrowserView", StubView)
    monkeypatch.setattr(kvk_cmds, "build_current_rankings_embed", lambda payload: "embed")
    monkeypatch.setattr(
        kvk_cmds,
        "render_kvk_rankings_top10_card",
        lambda _payload: rendered,
    )

    await kvk_cmds._send_current_rankings(ctx, mode="kvk")

    assert created["defer"] is False
    assert created["payload_kwargs"] == {"mode": "kvk", "metric": None, "limit": 10}
    assert created["send_kwargs"]["file"].filename == "kvk_rankings_top10_kills.png"
    assert "embed" not in created["send_kwargs"]
    assert created["send_kwargs"]["view"] is created["view"]
    assert created["send_kwargs"]["ephemeral"] is False
    assert created["view"].message is sent_message


@pytest.mark.asyncio
async def test_current_rankings_falls_back_to_embed_when_card_send_fails(monkeypatch):
    import commands.kvk_cmds as kvk_cmds

    created = {"sends": []}
    sent_message = object()

    async def fake_safe_defer(_ctx, *, ephemeral=False):
        created["defer"] = ephemeral

    async def fake_payload(**_kwargs):
        return SimpleNamespace(mode="kvk", metric="kills", limit=10)

    class StubView:
        def __init__(self, *, mode, metric, limit):
            self.mode = mode
            self.metric = metric
            self.limit = limit
            self.message = None
            created["view"] = self

    class Followup:
        async def send(self, **kwargs):
            created["sends"].append(kwargs)
            if "file" in kwargs:
                raise RuntimeError("discord upload failed")
            return sent_message

    rendered = SimpleNamespace(
        filename="kvk_rankings_top10_kills.png",
        image_bytes=BytesIO(b"fake-png"),
    )
    ctx = SimpleNamespace(followup=Followup())

    monkeypatch.setattr(kvk_cmds, "safe_defer", fake_safe_defer)
    monkeypatch.setattr(
        kvk_cmds.kvk_rankings_service,
        "build_current_rankings_payload",
        fake_payload,
    )
    monkeypatch.setattr(kvk_cmds, "CurrentRankingsBrowserView", StubView)
    monkeypatch.setattr(kvk_cmds, "build_current_rankings_embed", lambda payload: "embed")
    monkeypatch.setattr(
        kvk_cmds,
        "render_kvk_rankings_top10_card",
        lambda _payload: rendered,
    )

    await kvk_cmds._send_current_rankings(ctx, mode="kvk")

    assert "file" in created["sends"][0]
    assert created["sends"][1]["embed"] == "embed"
    assert created["sends"][1]["view"] is created["view"]
    assert created["view"].message is sent_message


@pytest.mark.asyncio
async def test_hall_of_fame_rankings_binds_view_to_followup_message(monkeypatch):
    import commands.kvk_cmds as kvk_cmds

    sent_message = object()
    original_response = object()
    created = {}

    async def fake_safe_defer(_ctx, *, ephemeral=False):
        created["defer"] = ephemeral

    async def fake_payload(**kwargs):
        created["payload_kwargs"] = kwargs
        return SimpleNamespace(limit=10)

    class StubView:
        def __init__(self, *, metric, limit):
            self.metric = metric
            self.limit = limit
            self.message = None
            created["view"] = self

    class Followup:
        async def send(self, **kwargs):
            created["send_kwargs"] = kwargs
            return sent_message

    class Interaction:
        async def original_response(self):
            return original_response

    ctx = SimpleNamespace(followup=Followup(), interaction=Interaction())

    monkeypatch.setattr(kvk_cmds, "safe_defer", fake_safe_defer)
    monkeypatch.setattr(
        kvk_cmds.kvk_rankings_service,
        "build_hall_of_fame_payload",
        fake_payload,
    )
    monkeypatch.setattr(kvk_cmds, "HallOfFameRecordsView", StubView)
    monkeypatch.setattr(kvk_cmds, "build_hall_of_fame_embed", lambda payload: "embed")

    await kvk_cmds._send_hall_of_fame_rankings(ctx)

    assert created["defer"] is False
    assert created["send_kwargs"]["view"] is created["view"]
    assert created["send_kwargs"]["ephemeral"] is False
    assert created["view"].message is sent_message
    assert created["view"].message is not original_response


@pytest.mark.asyncio
async def test_hall_of_fame_rankings_reports_payload_failure(monkeypatch):
    import commands.kvk_cmds as kvk_cmds

    created = {}

    async def fake_safe_defer(_ctx, *, ephemeral=False):
        created["defer"] = ephemeral

    async def fake_payload(**_kwargs):
        raise RuntimeError("sql unavailable")

    class Followup:
        async def send(self, content=None, **kwargs):
            created["content"] = content
            created["send_kwargs"] = kwargs
            return object()

    ctx = SimpleNamespace(followup=Followup())

    monkeypatch.setattr(kvk_cmds, "safe_defer", fake_safe_defer)
    monkeypatch.setattr(
        kvk_cmds.kvk_rankings_service,
        "build_hall_of_fame_payload",
        fake_payload,
    )
    monkeypatch.setattr(
        kvk_cmds,
        "HallOfFameRecordsView",
        lambda **_kwargs: pytest.fail("view should not be created on payload failure"),
    )
    monkeypatch.setattr(
        kvk_cmds,
        "build_hall_of_fame_embed",
        lambda _payload: pytest.fail("embed should not be built on payload failure"),
    )

    await kvk_cmds._send_hall_of_fame_rankings(ctx)

    assert created["defer"] is False
    assert "Hall of Fame rankings are temporarily unavailable" in created["content"]
    assert created["send_kwargs"] == {"ephemeral": False}


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


@pytest.mark.asyncio
async def test_kvk_history_multi_account_uses_private_account_picker_and_public_card(monkeypatch):
    import commands.kvk_cmds as kvk_cmds

    async def fake_safe_defer(_ctx, *, ephemeral=False):
        calls["defer"] = ephemeral

    async def fake_account_summary(_user_id):
        return kvk_cmds.governor_account_service.summarize_accounts(
            {
                "Main": {"GovernorID": "123", "GovernorName": "MainGov"},
                "Alt 1": {"GovernorID": "456", "GovernorName": "AltGov"},
            }
        )

    created = {}
    calls = {}

    class StubAccountPickerView:
        def __init__(self, **kwargs):
            created.update(kwargs)

    class DummyFollowup:
        def __init__(self):
            self.sent = []

        async def send(self, **kwargs):
            self.sent.append(kwargs)

    ctx = SimpleNamespace(
        user=SimpleNamespace(id=42),
        followup=DummyFollowup(),
    )

    async def fake_post(target, *, user, governor_id, ephemeral):
        calls["target"] = target
        calls["user"] = user
        calls["governor_id"] = governor_id
        calls["ephemeral"] = ephemeral

    monkeypatch.setattr(kvk_cmds, "safe_defer", fake_safe_defer)
    monkeypatch.setattr(
        kvk_cmds.governor_account_service,
        "get_account_summary_for_user",
        fake_account_summary,
    )
    monkeypatch.setattr(kvk_cmds, "AccountPickerView", StubAccountPickerView)
    monkeypatch.setattr(kvk_cmds, "post_kvk_history_output", fake_post)

    await kvk_cmds._send_kvk_history(ctx, governor_id=None)

    assert calls["defer"] is True
    assert created["heading"] == "Select an account to view its KVK history:"
    assert created["ephemeral"] is True
    assert len(created["options"]) == 2
    assert ctx.followup.sent[-1]["view"].__class__ is StubAccountPickerView

    interaction = SimpleNamespace(user=SimpleNamespace(id=42))
    await created["on_select_governor"](interaction, "456", True)

    assert calls["target"] is interaction
    assert calls["user"] is interaction.user
    assert calls["governor_id"] == "456"
    assert calls["ephemeral"] is False


@pytest.mark.asyncio
async def test_kvk_history_no_accounts_picker_matches_ephemeral_message(monkeypatch):
    import commands.kvk_cmds as kvk_cmds

    async def fake_safe_defer(_ctx, *, ephemeral=False):
        calls["defer"] = ephemeral

    async def fake_account_summary(_user_id):
        return SimpleNamespace(ok=True, error=None, ordered_accounts={})

    created = {}
    calls = {}

    class StubAccountPickerView:
        def __init__(self, **kwargs):
            created.update(kwargs)

    class DummyFollowup:
        def __init__(self):
            self.sent = []

        async def send(self, **kwargs):
            self.sent.append(kwargs)

    ctx = SimpleNamespace(
        user=SimpleNamespace(id=42),
        followup=DummyFollowup(),
    )

    monkeypatch.setattr(kvk_cmds, "safe_defer", fake_safe_defer)
    monkeypatch.setattr(
        kvk_cmds.governor_account_service,
        "get_account_summary_for_user",
        fake_account_summary,
    )
    monkeypatch.setattr(kvk_cmds, "AccountPickerView", StubAccountPickerView)

    await kvk_cmds._send_kvk_history(ctx, governor_id=None)

    assert calls["defer"] is True
    assert created["ephemeral"] is True
    assert ctx.followup.sent[-1]["ephemeral"] is True


@pytest.mark.asyncio
async def test_kvk_history_registry_unavailable_defers_privately(monkeypatch):
    import commands.kvk_cmds as kvk_cmds

    calls = {}

    async def fake_safe_defer(_ctx, *, ephemeral=False):
        calls["defer"] = ephemeral

    async def fake_account_summary(_user_id):
        return SimpleNamespace(ok=False, error="down", ordered_accounts={})

    class DummyFollowup:
        def __init__(self):
            self.sent = []

        async def send(self, *args, **kwargs):
            self.sent.append((args, kwargs))

    ctx = SimpleNamespace(
        user=SimpleNamespace(id=42),
        followup=DummyFollowup(),
    )

    monkeypatch.setattr(kvk_cmds, "safe_defer", fake_safe_defer)
    monkeypatch.setattr(
        kvk_cmds.governor_account_service,
        "get_account_summary_for_user",
        fake_account_summary,
    )

    await kvk_cmds._send_kvk_history(ctx, governor_id=None)

    assert calls["defer"] is True
    assert ctx.followup.sent[-1][1]["ephemeral"] is True


@pytest.mark.asyncio
async def test_kvk_history_single_account_defers_publicly(monkeypatch):
    import commands.kvk_cmds as kvk_cmds

    calls = {}

    async def fake_safe_defer(_ctx, *, ephemeral=False):
        calls["defer"] = ephemeral

    async def fake_account_summary(_user_id):
        return kvk_cmds.governor_account_service.summarize_accounts(
            {"Main": {"GovernorID": "123", "GovernorName": "MainGov"}}
        )

    async def fake_post(target, *, user, governor_id, ephemeral):
        calls["target"] = target
        calls["user"] = user
        calls["governor_id"] = governor_id
        calls["ephemeral"] = ephemeral

    ctx = SimpleNamespace(
        user=SimpleNamespace(id=42),
        followup=SimpleNamespace(),
    )

    monkeypatch.setattr(kvk_cmds, "safe_defer", fake_safe_defer)
    monkeypatch.setattr(
        kvk_cmds.governor_account_service,
        "get_account_summary_for_user",
        fake_account_summary,
    )
    monkeypatch.setattr(kvk_cmds, "post_kvk_history_output", fake_post)

    await kvk_cmds._send_kvk_history(ctx, governor_id=None)

    assert calls["defer"] is False
    assert calls["target"] is ctx
    assert calls["user"] is ctx.user
    assert calls["governor_id"] == "123"
    assert calls["ephemeral"] is False


@pytest.mark.asyncio
async def test_kvk_history_explicit_governor_uses_modern_history_output(monkeypatch):
    import commands.kvk_cmds as kvk_cmds

    async def fake_safe_defer(_ctx, *, ephemeral=False):
        calls["defer"] = ephemeral

    async def fake_account_summary(_user_id):
        raise AssertionError("explicit governor_id should not require registry lookup")

    class DummyFollowup:
        async def send(self, **_kwargs):
            return None

    ctx = SimpleNamespace(
        user=SimpleNamespace(id=42),
        followup=DummyFollowup(),
    )

    calls = {}

    async def fake_post(target, *, user, governor_id, ephemeral):
        calls["target"] = target
        calls["user"] = user
        calls["governor_id"] = governor_id
        calls["ephemeral"] = ephemeral

    monkeypatch.setattr(kvk_cmds, "safe_defer", fake_safe_defer)
    monkeypatch.setattr(
        kvk_cmds.governor_account_service,
        "get_account_summary_for_user",
        fake_account_summary,
    )
    monkeypatch.setattr(kvk_cmds, "post_kvk_history_output", fake_post)

    await kvk_cmds._send_kvk_history(ctx, governor_id=789)

    assert calls == {
        "defer": False,
        "target": ctx,
        "user": ctx.user,
        "governor_id": "789",
        "ephemeral": False,
    }
