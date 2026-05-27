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
from file_utils import emit_telemetry_event

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


def build_command_signatures(commands: Sequence[Any]) -> tuple[list[dict[str, Any]], list[tuple[str, Any]]]:
    signature_commands = list(flatten_application_commands(commands))
    current_signatures = [
        sig
        for name, cmd in signature_commands
        if (sig := get_command_signature(cmd, name=name)) is not None
    ]
    return current_signatures, signature_commands


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
