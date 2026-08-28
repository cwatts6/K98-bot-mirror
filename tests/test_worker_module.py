# A tiny module used by integration tests to exercise callable_worker.
import asyncio
import time


def long_sleep(seconds: float):
    """Blocking sleep used by start_callable_offload tests."""
    time.sleep(float(seconds))
    return f"slept:{seconds}"


async def async_long_sleep(seconds: float):
    await asyncio.sleep(float(seconds))
    return f"async_slept:{seconds}"
