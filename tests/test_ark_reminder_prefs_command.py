from __future__ import annotations

import pytest

from commands import ark_cmds


class DummyResponse:
    def is_done(self):
        return True


class DummyFollowup:
    def __init__(self):
        self.sent = []

    async def send(self, content=None, **kwargs):
        self.sent.append({"content": content, **kwargs})


class DummyInteraction:
    def __init__(self, user_id: int = 123):
        self.user = type("U", (), {"id": user_id})()
        self.edits = []
        self.client = object()
        self.response = DummyResponse()
        self.followup = DummyFollowup()

    async def edit_original_response(self, *, content=None, view=None):
        self.edits.append({"content": content, "view": view})


class DummyCtx:
    def __init__(self, user_id: int = 123):
        self.user = type("U", (), {"id": user_id})()
        self.interaction = DummyInteraction(user_id=user_id)
        self.guild_id = 987


class DummyBot:
    def __init__(self):
        self.registered = {}

    def slash_command(self, name, description, guild_ids):
        def deco(fn):
            self.registered[name] = fn
            return fn

        return deco


@pytest.mark.asyncio
async def test_ark_reminder_prefs_command_seeds_defaults(monkeypatch):
    bot = DummyBot()
    ark_cmds.register_ark(bot)
    cmd = bot.registered["ark_reminder_prefs"]

    async def _safe_defer(_ctx, ephemeral=True):
        return None

    captured = {"upsert": None}

    async def _get_prefs(_uid):
        return None

    async def _upsert(uid, **kwargs):
        captured["upsert"] = (uid, kwargs)
        return True

    monkeypatch.setattr("commands.ark_cmds.safe_defer", _safe_defer)
    monkeypatch.setattr("commands.ark_cmds.get_reminder_prefs", _get_prefs)
    monkeypatch.setattr("commands.ark_cmds.upsert_reminder_prefs", _upsert)

    ctx = DummyCtx(user_id=777)
    await cmd(ctx)

    assert captured["upsert"] is not None
    uid, kwargs = captured["upsert"]
    assert uid == 777
    assert kwargs["opt_out_all"] == 0
    assert kwargs["opt_out_24h"] == 0
    assert kwargs["opt_out_4h"] == 0
    assert kwargs["opt_out_1h"] == 0
    assert kwargs["opt_out_start"] == 0
    assert kwargs["opt_out_checkin_12h"] == 0
    assert ctx.interaction.edits


@pytest.mark.asyncio
async def test_ark_force_announce_opens_active_match_dropdown(monkeypatch):
    from datetime import date, time

    bot = DummyBot()
    ark_cmds.register_ark(bot)
    cmd = bot.registered["ark_force_announce"]
    while hasattr(cmd, "__wrapped__"):
        cmd = cmd.__wrapped__

    async def _safe_defer(_ctx, ephemeral=True):
        return None

    async def _get_config():
        return {"PlayersCap": 30, "SubsCap": 15}

    async def _list_open_matches():
        return [
            {
                "MatchId": 44,
                "Alliance": "k98A",
                "ArkWeekendDate": date(2026, 5, 30),
                "MatchDay": "Sat",
                "MatchTimeUtc": time(20, 0),
            }
        ]

    monkeypatch.setattr("commands.ark_cmds.safe_defer", _safe_defer)
    monkeypatch.setattr("commands.ark_cmds.get_config", _get_config)
    monkeypatch.setattr("commands.ark_cmds.list_open_matches", _list_open_matches)

    ctx = DummyCtx(user_id=777)
    await cmd(ctx)

    assert ctx.interaction.edits
    view = ctx.interaction.edits[-1]["view"]
    assert view is not None
    assert view.match_select.options[0].value == "44"


@pytest.mark.asyncio
async def test_ark_force_announce_manual_match_id_bypasses_dropdown(monkeypatch):
    bot = DummyBot()
    ark_cmds.register_ark(bot)
    cmd = bot.registered["ark_force_announce"]
    while hasattr(cmd, "__wrapped__"):
        cmd = cmd.__wrapped__

    async def _safe_defer(_ctx, ephemeral=True):
        return None

    async def _get_config():
        return {"PlayersCap": 30, "SubsCap": 15}

    async def _list_open_matches():
        raise AssertionError("manual match_id path should not load dropdown matches")

    async def _get_match(match_id):
        return {
            "MatchId": match_id,
            "Status": "Scheduled",
            "RegistrationChannelId": 123,
        }

    async def _audit(**_kwargs):
        return 1

    class _Controller:
        def __init__(self, *, match_id, config):
            self.match_id = match_id
            self.config = config

        async def ensure_registration_message(self, **kwargs):
            assert kwargs["announce"] is True
            assert kwargs["force_repost"] is True
            return type("Ref", (), {"channel_id": 123, "message_id": 456})()

    monkeypatch.setattr("commands.ark_cmds.safe_defer", _safe_defer)
    monkeypatch.setattr("commands.ark_cmds.get_config", _get_config)
    monkeypatch.setattr("commands.ark_cmds.list_open_matches", _list_open_matches)
    monkeypatch.setattr("commands.ark_cmds.get_match", _get_match)
    monkeypatch.setattr("commands.ark_cmds.insert_audit_log", _audit)
    monkeypatch.setattr("commands.ark_cmds.ArkRegistrationController", _Controller)

    ctx = DummyCtx(user_id=777)
    await cmd(ctx, match_id=99)

    assert not ctx.interaction.edits
    assert ctx.interaction.followup.sent
    assert "announcement reposted" in ctx.interaction.followup.sent[-1]["content"]
