from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
import json
import logging
import os
from typing import Any

from constants import EXIT_CODE_FILE, RESTART_EXIT_CODE, RESTART_FLAG_PATH

logger = logging.getLogger(__name__)

RestartAuditWriter = Callable[[str, list[Any]], Awaitable[Any]]
AsyncStep = Callable[[], Awaitable[Any]]
FlushLogs = Callable[[], Any]
DEFAULT_BOT_CLOSE_TIMEOUT_SECONDS = 10.0


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _fsync_json(path: str, payload: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f)
        f.flush()
        os.fsync(f.fileno())


def _write_exit_code(path: str, exit_code: int) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(str(exit_code))
        f.flush()
        os.fsync(f.fileno())


async def write_restart_request(
    *,
    reason: str,
    user_id: str,
    append_csv_line: RestartAuditWriter | None = None,
    restart_flag_path: str = RESTART_FLAG_PATH,
    exit_code_file: str = EXIT_CODE_FILE,
    exit_code: int = RESTART_EXIT_CODE,
    timestamp: str | None = None,
) -> dict[str, str]:
    restart_flag = {
        "timestamp": timestamp or _utcnow_iso(),
        "reason": reason,
        "user_id": str(user_id),
    }
    _fsync_json(restart_flag_path, restart_flag)
    _write_exit_code(exit_code_file, exit_code)

    if append_csv_line is not None:
        try:
            await append_csv_line(
                "restart_log.csv",
                [
                    restart_flag["timestamp"],
                    restart_flag["reason"],
                    restart_flag["user_id"],
                    "success",
                    "",
                    "",
                    "",
                ],
            )
        except Exception:
            logger.exception("[RESTART] Failed to append restart audit log.")

    return restart_flag


async def run_cooperative_restart(
    *,
    reason: str,
    user_id: str,
    append_csv_line: RestartAuditWriter | None,
    graceful_teardown: AsyncStep,
    close_bot: AsyncStep,
    flush_logs: FlushLogs | None = None,
    response_delay_seconds: float = 0.25,
    close_timeout_seconds: float = DEFAULT_BOT_CLOSE_TIMEOUT_SECONDS,
) -> dict[str, str]:
    restart_flag = await write_restart_request(
        reason=reason,
        user_id=user_id,
        append_csv_line=append_csv_line,
    )
    if response_delay_seconds > 0:
        await asyncio.sleep(response_delay_seconds)
    await graceful_teardown()
    if flush_logs is not None:
        flush_logs()
    try:
        await asyncio.wait_for(close_bot(), timeout=close_timeout_seconds)
    except TimeoutError:
        logger.warning("[RESTART] bot.close() timed out after %.1fs", close_timeout_seconds)
    return restart_flag
