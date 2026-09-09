from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from dataclasses import dataclass
import logging
import os
from typing import Any

from bot_helpers import (
    commands_changed,
    get_command_signature,
    load_command_signatures,
    save_command_signatures,
)
from commands.command_inventory import flatten_application_commands
from constants import COMMAND_CACHE_FILE
from file_utils import atomic_json_write, emit_telemetry_event

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CommandSyncLifecycleResult:
    changed: bool
    signatures: list[dict[str, Any]]
    loaded_commands: Sequence[tuple[str, Any]]
    sync_attempted: bool = False
    sync_succeeded: bool = False
    sync_timed_out: bool = False
    sync_skipped_reason: str | None = None


@dataclass(frozen=True)
class ManualCommandSyncResult:
    guild_id: int
    timed_out: bool = False
    error: Exception | None = None

    @property
    def ok(self) -> bool:
        return not self.timed_out and self.error is None


@dataclass(frozen=True)
class CommandCacheUpdateResult:
    signatures: list[dict[str, Any]]
    updated_lines: list[str]


@dataclass(frozen=True)
class CommandCacheValidationResult:
    issues: list[str]
    signatures: list[dict[str, Any]]


def build_command_signatures(
    commands: Sequence[Any],
) -> tuple[list[dict[str, Any]], list[tuple[str, Any]]]:
    signature_commands = list(flatten_application_commands(commands))
    current_signatures = [
        sig
        for name, cmd in signature_commands
        if (sig := get_command_signature(cmd, name=name)) is not None
    ]
    return current_signatures, signature_commands


def sorted_command_signatures(commands: Sequence[Any]) -> list[dict[str, Any]]:
    signatures, _signature_commands = build_command_signatures(commands)
    return sorted(signatures, key=lambda sig: str(sig.get("name", "")).lower())


def command_version_lines(commands: Sequence[Any]) -> list[str]:
    return [
        f"/{signature['name']} — `{signature.get('version', 'N/A')}`"
        for signature in sorted_command_signatures(commands)
    ]


def command_cache_update(
    commands: Sequence[Any],
    *,
    existing_signatures: Sequence[dict[str, Any]] | None = None,
    cache_file: str = COMMAND_CACHE_FILE,
    writer: Callable[[str, list[dict[str, Any]]], Any] = atomic_json_write,
) -> CommandCacheUpdateResult:
    old_cache = {
        str(cmd.get("name", "")): cmd
        for cmd in (existing_signatures or [])
        if isinstance(cmd, dict) and cmd.get("name")
    }
    signatures = sorted_command_signatures(commands)
    updated_lines = []
    for signature in signatures:
        name = str(signature.get("name", ""))
        version = signature.get("version", "N/A")
        cached_version = old_cache.get(name, {}).get("version")
        if cached_version != version:
            updated_lines.append(f"/{name} → `{cached_version}` ➜ `{version}`")

    writer(cache_file, signatures)
    return CommandCacheUpdateResult(signatures=signatures, updated_lines=updated_lines)


def validate_command_cache(
    commands: Sequence[Any],
    cached_signatures: Sequence[dict[str, Any]],
) -> CommandCacheValidationResult:
    signatures = sorted_command_signatures(commands)
    cache = {
        str(entry.get("name", "")): entry.get("version", "N/A")
        for entry in cached_signatures
        if isinstance(entry, dict) and entry.get("name")
    }
    loaded_names = {str(signature.get("name", "")) for signature in signatures}
    cache_names = set(cache)
    issues = []

    for signature in signatures:
        name = str(signature.get("name", ""))
        version = signature.get("version", "N/A")
        cached = cache.get(name)
        if cached is None:
            issues.append(f"➕ `/{name}` is **missing** from cache (code=`{version}`)")
        elif cached != version:
            issues.append(f"🔁 `/{name}` version mismatch: cache=`{cached}`, code=`{version}`")

    for name in sorted(cache_names - loaded_names):
        issues.append(f"➖ `/{name}` is in cache but not currently loaded")

    return CommandCacheValidationResult(issues=issues, signatures=signatures)


async def sync_commands_for_guild(
    bot: Any,
    *,
    guild_id: int,
    timeout_seconds: float,
) -> ManualCommandSyncResult:
    try:
        await asyncio.wait_for(bot.sync_commands(guild_ids=[guild_id]), timeout=timeout_seconds)
        return ManualCommandSyncResult(guild_id=guild_id)
    except TimeoutError:
        return ManualCommandSyncResult(guild_id=guild_id, timed_out=True)
    except Exception as exc:
        return ManualCommandSyncResult(guild_id=guild_id, error=exc)


def log_loaded_slash_commands(signature_commands: Sequence[tuple[str, Any]]) -> None:
    logger.warning("📋 Loaded slash commands:")
    for name, cmd in signature_commands:
        logger.warning(f" - /{name} – {cmd.description}")


async def run_ready_command_sync(
    bot: Any,
    *,
    cache_file: str = COMMAND_CACHE_FILE,
    guild_id_env: str | None = None,
    sync_timeout_seconds: float = 10.0,
    telemetry_emit: Callable[[dict[str, Any]], Any] = emit_telemetry_event,
) -> CommandSyncLifecycleResult:
    commands = list(bot.application_commands)
    current_signatures, signature_commands = build_command_signatures(commands)

    logger.info("🧪 Reading command cache file...")
    saved_signatures = load_command_signatures(filepath=cache_file)
    logger.info("✅ Command cache loaded")

    try:
        result = commands_changed(current_signatures, saved_signatures)
        logger.info(f"✅ commands_changed result: {result}")
    except Exception:
        logger.exception("💥 Exception in commands_changed")
        result = False

    changed = bool(result)
    sync_attempted = False
    sync_succeeded = False
    sync_timed_out = False
    sync_skipped_reason = None

    if changed:
        gid_env = guild_id_env if guild_id_env is not None else os.getenv("GUILD_ID")
        logger.info(f"[DEBUG] Slash commands changed — syncing to GUILD_ID={gid_env}")
        try:
            if gid_env:
                gid = int(gid_env)
                sync_attempted = True
                try:
                    await asyncio.wait_for(
                        bot.sync_commands(guild_ids=[gid]),
                        timeout=sync_timeout_seconds,
                    )
                    sync_succeeded = True
                    logger.info("[DEBUG] Commands synced successfully")
                except TimeoutError:
                    sync_timed_out = True
                    logger.warning("[WARN] Command sync timed out — skipping for now.")
                    try:
                        telemetry_emit(
                            {
                                "event": "command_sync",
                                "status": "timeout",
                                "guild_id": gid,
                                "orphaned_offload_possible": False,
                            }
                        )
                    except Exception:
                        logger.debug(
                            "[TELEMETRY] Failed to emit command_sync timeout telemetry",
                            exc_info=True,
                        )
                except Exception as e:
                    logger.warning(f"[WARN] Command sync failed: {e}")
            else:
                sync_skipped_reason = "missing_guild_id"
                logger.warning("[WARN] GUILD_ID not set; skipping scoped sync.")
        except ValueError:
            sync_skipped_reason = "invalid_guild_id"
            logger.warning("[WARN] GUILD_ID is not an integer; skipping scoped sync.")
        except Exception as e:
            logger.warning(f"[WARN] Command sync failed: {e}")

        save_command_signatures(current_signatures, filepath=cache_file)
        logger.warning("🔁 Slash commands changed — updated cache")
    else:
        logger.warning("⏩ Slash commands unchanged — skipping sync and update.")

    log_loaded_slash_commands(signature_commands)
    return CommandSyncLifecycleResult(
        changed=changed,
        signatures=current_signatures,
        loaded_commands=signature_commands,
        sync_attempted=sync_attempted,
        sync_succeeded=sync_succeeded,
        sync_timed_out=sync_timed_out,
        sync_skipped_reason=sync_skipped_reason,
    )
