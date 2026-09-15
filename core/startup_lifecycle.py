from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StartupPhase:
    name: str
    run: Callable[[], Awaitable[Any]]


async def run_startup_phases(phases: list[StartupPhase]) -> None:
    """Run startup phases in order while making lifecycle ownership explicit."""
    for phase in phases:
        logger.info("[STARTUP] phase started: %s", phase.name)
        try:
            await phase.run()
        except Exception:
            logger.exception("[STARTUP] phase failed: %s", phase.name)
            raise
        logger.info("[STARTUP] phase completed: %s", phase.name)
