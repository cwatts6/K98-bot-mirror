# tests/test_offload_monitor_once.py
import pytest

from offload_monitor_lib import monitor_once_coro

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_monitor_once_runs_and_returns_summary(tmp_path, monkeypatch):
    """
    Run the monitor once (in-process) and assert it returns the expected summary shape.
    This exercises stale-check + rotation integration in a safe unit test.
    """
    # Ensure DATA_DIR points to a temporary dir for test isolation
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    # The monitor reads constants.DATA_DIR via import; if offload registry path is needed,
    # the functions will create file if absent.
    res = await monitor_once_coro(rotate_days=1, max_entries=100)
    assert isinstance(res, dict)
    assert "stale_marked" in res
    assert "stats" in res
    assert "rotate" in res
