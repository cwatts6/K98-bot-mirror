from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from core.command_lifecycle import build_command_signatures, run_ready_command_sync


def _command(name: str, *, description: str = "desc", version: str = "v1.0"):
    def callback():
        return None

    callback.__version__ = version
    return SimpleNamespace(name=name, description=description, callback=callback, subcommands=[])


class FakeBot:
    def __init__(self, commands):
        self.application_commands = commands
        self.sync_calls: list[list[int]] = []

    async def sync_commands(self, *, guild_ids):
        self.sync_calls.append(guild_ids)


def test_build_command_signatures_uses_flattened_inventory_names():
    subcommand = _command("status", description="Show status", version="v2.0")
    group = SimpleNamespace(name="ops", subcommands=[subcommand])

    signatures, signature_commands = build_command_signatures([group])

    assert signature_commands == [("ops status", subcommand)]
    assert signatures == [
        {
            "name": "ops status",
            "description": "Show status",
            "version": "v2.0",
        }
    ]


@pytest.mark.asyncio
async def test_run_ready_command_sync_skips_unchanged_signatures(tmp_path):
    command = _command("ping", description="Ping", version="v1.0")
    cache_file = tmp_path / "command_cache.json"
    cache_file.write_text(
        json.dumps([{"name": "ping", "description": "Ping", "version": "v1.0"}]),
        encoding="utf-8",
    )
    bot = FakeBot([command])

    result = await run_ready_command_sync(bot, cache_file=str(cache_file), guild_id_env="123")

    assert result.changed is False
    assert result.sync_attempted is False
    assert bot.sync_calls == []
    assert json.loads(cache_file.read_text(encoding="utf-8")) == result.signatures


@pytest.mark.asyncio
async def test_run_ready_command_sync_syncs_and_saves_changed_signatures(tmp_path):
    command = _command("ping", description="Ping", version="v2.0")
    cache_file = tmp_path / "command_cache.json"
    cache_file.write_text(
        json.dumps([{"name": "ping", "description": "Ping", "version": "v1.0"}]),
        encoding="utf-8",
    )
    bot = FakeBot([command])

    result = await run_ready_command_sync(bot, cache_file=str(cache_file), guild_id_env="123")

    assert result.changed is True
    assert result.sync_attempted is True
    assert result.sync_succeeded is True
    assert bot.sync_calls == [[123]]
    assert json.loads(cache_file.read_text(encoding="utf-8")) == result.signatures


@pytest.mark.asyncio
async def test_run_ready_command_sync_timeout_emits_telemetry_and_saves_cache(tmp_path):
    class TimeoutBot(FakeBot):
        async def sync_commands(self, *, guild_ids):
            self.sync_calls.append(guild_ids)
            raise TimeoutError

    command = _command("ping", description="Ping", version="v2.0")
    cache_file = tmp_path / "command_cache.json"
    cache_file.write_text("[]", encoding="utf-8")
    telemetry_events = []
    bot = TimeoutBot([command])

    result = await run_ready_command_sync(
        bot,
        cache_file=str(cache_file),
        guild_id_env="123",
        telemetry_emit=telemetry_events.append,
    )

    assert result.changed is True
    assert result.sync_attempted is True
    assert result.sync_timed_out is True
    assert bot.sync_calls == [[123]]
    assert telemetry_events == [
        {
            "event": "command_sync",
            "status": "timeout",
            "guild_id": 123,
            "orphaned_offload_possible": False,
        }
    ]
    assert json.loads(cache_file.read_text(encoding="utf-8")) == result.signatures


@pytest.mark.asyncio
async def test_run_ready_command_sync_invalid_guild_id_skips_sync_but_saves_cache(tmp_path):
    command = _command("ping", description="Ping", version="v2.0")
    cache_file = tmp_path / "command_cache.json"
    cache_file.write_text("[]", encoding="utf-8")
    bot = FakeBot([command])

    result = await run_ready_command_sync(bot, cache_file=str(cache_file), guild_id_env="abc")

    assert result.changed is True
    assert result.sync_attempted is False
    assert result.sync_skipped_reason == "invalid_guild_id"
    assert bot.sync_calls == []
    assert json.loads(cache_file.read_text(encoding="utf-8")) == result.signatures
