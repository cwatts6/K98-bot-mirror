from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Awaitable, Callable
import csv
from datetime import UTC, datetime
import json
import logging
import os
from typing import Any

from constants import (
    BASE_DIR,
    EXIT_CODE_FILE,
    RESTART_EXIT_CODE,
    RESTART_FLAG_PATH,
    RESTART_LOG_FILE,
)

logger = logging.getLogger(__name__)

RestartAuditWriter = Callable[[str, list[Any]], Awaitable[Any]]
AsyncStep = Callable[[], Awaitable[Any]]
FlushLogs = Callable[[], Any]
ForceExit = Callable[[int], Any]
DEFAULT_BOT_CLOSE_TIMEOUT_SECONDS = 10.0


def read_restart_history(count: int = 5) -> list[dict[str, str]]:
    """Read legacy history followed by the writable runtime log; never migrate on read."""
    recent = deque(maxlen=max(1, min(int(count or 5), 20)))
    legacy = os.path.join(BASE_DIR, "restart_log.csv")
    paths = dict.fromkeys(os.path.abspath(path) for path in (legacy, RESTART_LOG_FILE))
    for path in paths:
        try:
            with open(path, encoding="utf-8-sig", newline="") as stream:
                recent.extend(csv.DictReader(stream))
        except FileNotFoundError:
            continue
    return list(recent)


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
                RESTART_LOG_FILE,
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
    force_exit: ForceExit | None = os._exit,
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
        if flush_logs is not None:
            flush_logs()
        if force_exit is not None:
            logger.warning("[RESTART] Forcing process exit after bot.close() timeout.")
            force_exit(RESTART_EXIT_CODE)
    return restart_flag
