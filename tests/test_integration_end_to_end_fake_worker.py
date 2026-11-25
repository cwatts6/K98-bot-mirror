import pytest

from file_utils import list_offloads, run_callable_subprocess

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_run_callable_subprocess_and_parse_result():
    """
    Run an async callable through run_callable_subprocess and assert structured output parsing.
    Uses tests.test_worker_module.async_long_sleep for a short sleep.
    """
    ok, out = await run_callable_subprocess(
        module="tests.test_worker_module",
        function="async_long_sleep",
        args=["0.05"],
        timeout=5.0,
        name="test_callable_async",
        meta={"test": "e2e"},
    )
    assert ok is True
    # Ensure output contains the expected return marker
    assert isinstance(out, str)
    assert "async_slept" in out or "slept" in out
    # Check registry entry exists for the most recent offload
    offs = list_offloads()
    assert isinstance(offs, list)
    assert len(offs) > 0
