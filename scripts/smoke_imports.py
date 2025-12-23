#!/usr/bin/env python3
"""
Import-only smoke test: verifies top-level modules import without side effects.
Safe: does not require Discord token or network.
"""
from __future__ import annotations

import os

# --- Make repo imports work even when running via path ---
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# --- Environment flags to appease guards & skip side-effects ---
# Satisfy watchdog/run guards and block runtime tasks
os.environ.setdefault("WATCHDOG_RUN", "1")
os.environ.setdefault("SMOKE_IMPORTS", "1")
os.environ.setdefault("NO_DISCORD_LOGIN", "1")
os.environ.setdefault("DISABLE_STARTUP_TASKS", "1")
# Stop file logging / rotation during smoke
os.environ.setdefault("DISABLE_FILE_LOGGING", "1")

# --- Neuter file logging just in case env flags aren't respected ---
import logging
import logging.handlers

logger = logging.getLogger(__name__)


class _NullHandler(logging.Handler):
    def emit(self, record):  # pragma: no cover
        pass


# Force root logger to a no-op handler to prevent basicConfig/rollovers
logger.basicConfig(handlers=[_NullHandler()], level=logging.CRITICAL, force=True)


# Replace file-based handlers with no-op versions
class _DummyFileHandler(_NullHandler):
    def __init__(self, *a, **kw):
        super().__init__()


logger.FileHandler = _DummyFileHandler  # type: ignore[attr-defined]
logger.handlers.RotatingFileHandler = _DummyFileHandler  # type: ignore[attr-defined]
logger.handlers.TimedRotatingFileHandler = _DummyFileHandler  # type: ignore[attr-defined]

# --- Now do the imports ---
import importlib

MODULES = [
    # Keep this list lean; add more over time
    "bot_config",
    "logging_setup",
    "utils",
    "bot_helpers",
    "embed_utils",
    "embed_player_profile",
    "event_cache",
    "event_scheduler",
    "event_embed_manager",
    "target_utils",
    "stats_alert_utils",
    "Commands",
]


def main() -> int:
    failed = []
    for name in MODULES:
        try:
            importlib.import_module(name)
        except Exception as e:
            failed.append(f"{name}: {type(e).__name__}: {e}")
    if failed:
        print("❌ Import smoke failed:\n" + "\n".join(f"- {x}" for x in failed))
        return 1
    print("✅ Import smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
