from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from core.command_lifecycle import (
    build_command_signatures,
    command_cache_update,
    command_version_lines,
    run_ready_command_sync,
    sync_commands_for_guild,
    validate_command_cache,
)


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


def test_command_cache_update_writes_startup_signature_shape_atomically():
    command = _command("ping", description="Ping", version="v2.0")
    writes = []

    result = command_cache_update(
        [command],
        existing_signatures=[
            {
                "name": "ping",
                "description": "Ping",
                "version": "v1.0",
                "admin_only": True,
            }
        ],
        cache_file="cache.json",
        writer=lambda path, data: writes.append((path, data)),
    )

    assert result.updated_lines == ["/ping → `v1.0` ➜ `v2.0`"]
    assert result.signatures == [{"name": "ping", "description": "Ping", "version": "v2.0"}]
    assert writes == [("cache.json", result.signatures)]


def test_validate_command_cache_uses_shared_signature_model():
    command = _command("ping", description="Ping", version="v2.0")
    stale = {"name": "old", "description": "Old", "version": "v1.0"}

    result = validate_command_cache(
        [command],
        [
            {"name": "ping", "description": "Ping", "version": "v1.0"},
            stale,
        ],
    )

    assert result.issues == [
        "🔁 `/ping` version mismatch: cache=`v1.0`, code=`v2.0`",
        "➖ `/old` is in cache but not currently loaded",
    ]


def test_command_version_lines_use_flattened_group_names():
    subcommand = _command("run_sql_proc", description="Run SQL", version="v1.03")
    group = SimpleNamespace(name="ops", subcommands=[subcommand])

    assert command_version_lines([group]) == ["/ops run_sql_proc — `v1.03`"]


def test_command_cache_validation_uses_grouped_ark_names():
    subcommand = _command("reminder_prefs", description="Prefs", version="v1.02")
    group = SimpleNamespace(name="ark", subcommands=[subcommand])

    result = validate_command_cache(
        [group],
        [{"name": "ark_reminder_prefs", "description": "Prefs", "version": "v1.02"}],
    )

    assert result.signatures == [
        {"name": "ark reminder_prefs", "description": "Prefs", "version": "v1.02"}
    ]
    assert result.issues == [
        "➕ `/ark reminder_prefs` is **missing** from cache (code=`v1.02`)",
        "➖ `/ark_reminder_prefs` is in cache but not currently loaded",
    ]


@pytest.mark.asyncio
async def test_sync_commands_for_guild_reports_success():
    bot = FakeBot([])

    result = await sync_commands_for_guild(bot, guild_id=123, timeout_seconds=5.0)

    assert result.ok is True
    assert result.guild_id == 123
    assert bot.sync_calls == [[123]]


@pytest.mark.asyncio
async def test_sync_commands_for_guild_reports_timeout():
    class TimeoutBot(FakeBot):
        async def sync_commands(self, *, guild_ids):
            self.sync_calls.append(guild_ids)
            raise TimeoutError

    bot = TimeoutBot([])

    result = await sync_commands_for_guild(bot, guild_id=123, timeout_seconds=5.0)

    assert result.ok is False
    assert result.timed_out is True
    assert result.error is None
    assert bot.sync_calls == [[123]]


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
