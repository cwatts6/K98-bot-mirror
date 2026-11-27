# bot_startup_gate.py
import asyncio

_TASKS_STARTED = False
_LOCK = asyncio.Lock()


async def claim_startup_once() -> bool:
    """
    Returns True if this is the first caller to claim startup.
    Returns False on subsequent calls (e.g., after reconnects).
    """
    global _TASKS_STARTED
    async with _LOCK:
        if _TASKS_STARTED:
            return False
        _TASKS_STARTED = True
        return True
