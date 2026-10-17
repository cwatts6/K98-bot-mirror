from __future__ import annotations

from commands import register_all as _register_all
from commands.telemetry_cmds import *  # noqa: F403
from commands.telemetry_cmds import ACCOUNT_ORDER as _TELEMETRY_ACCOUNT_ORDER
from logging_setup import CRASH_LOG_PATH, ERROR_LOG_PATH, FULL_LOG_PATH

# Keep these shim-level symbols physically present in Commands.py for compatibility/tests.
ACCOUNT_ORDER = _TELEMETRY_ACCOUNT_ORDER

# IMPORTANT: keep this assignment AFTER star imports so legacy telemetry symbol
# `register_commands` cannot overwrite the authoritative package-wide registrar.
register_commands = _register_all


def _pick_log_source(source: str):
    s = (source or "general").lower()
    if s.startswith("err"):
        return ERROR_LOG_PATH
    if s.startswith("cr"):
        return CRASH_LOG_PATH
    return FULL_LOG_PATH
