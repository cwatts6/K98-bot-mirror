# tests/conftest.py
# Ensure the repository root is on sys.path during pytest collection so tests can `import event_utils` etc.
# This is a small, safe helper used only for the test environment.
import asyncio
import os
import sys
import types

import pytest

# Determine repository root (one directory up from tests/)
_THIS_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, ".."))

if REPO_ROOT not in sys.path:
    # Insert at front so local package modules shadow installed packages with same names.
    sys.path.insert(0, REPO_ROOT)


# ----------------------------
# Optional: lightweight fake heavy deps (opt-in)
# ----------------------------
# Set environment variable TEST_FAKE_HEAVY_DEPS=1 to enable injection of minimal
# stub modules for heavy imports like pandas/pyodbc/openpyxl. This is intentionally
# opt-in so CI or local dev environments that actually install these deps are not masked.
if os.getenv("TEST_FAKE_HEAVY_DEPS", "0") == "1":
    for _mod in ("pyodbc", "pandas", "openpyxl"):
        if _mod not in sys.modules:
            sys.modules[_mod] = types.ModuleType(_mod)


# ----------------------------
# Test helpers / fixtures
# ----------------------------
@pytest.fixture
def async_return_factory():
    """
    Return a factory that wraps a value into an async function that returns that value.
    Usage:
        async_stub = async_return_factory((True, "ok"))
        monkeypatch.setattr(..., async_stub)
    """

    def make_async_return(value):
        async def _inner(*args, **kwargs):
            # ensure we yield to the loop so behaviour resembles a real coroutine
            await asyncio.sleep(0)
            return value

        return _inner

    return make_async_return


@pytest.fixture
def async_noop():
    """
    Return an async no-op that yields and returns a benign tuple (True, 'ok').
    Useful for monkeypatching async functions like run_maintenance_with_isolation.
    """

    async def _noop(*args, **kwargs):
        await asyncio.sleep(0)
        return True, "ok"

    return _noop
