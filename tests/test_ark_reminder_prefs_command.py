from __future__ import annotations

import pytest

from commands import ark_cmds


class DummyInteraction:
    def __init__(self):
        self.edits = []

    async def edit_original_response(self, *, content=None, view=None):
        self.edits.append({"content": content, "view": view})


class DummyCtx:
    def __init__(self, user_id: int = 123):
        self.user = type("U", (), {"id": user_id})()
        self.interaction = DummyInteraction()


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
