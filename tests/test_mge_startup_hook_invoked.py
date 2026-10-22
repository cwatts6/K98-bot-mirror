from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_start_mge_tasks_when_ready_registers_task_when_ready():
    # Adjust import path if your bot singleton/module path differs.
    import bot_instance as bi

    # Mock wait_for_events -> ready
    with patch.object(bi, "wait_for_events", new=AsyncMock(return_value=True)):
        # Mock task monitor behavior
        with patch.object(bi.task_monitor, "is_running", return_value=False) as mock_running:
            with patch.object(bi.task_monitor, "create") as mock_create:
                await bi._start_mge_tasks_when_ready(max_wait_seconds=123)

                mock_running.assert_called_once_with("mge_lifecycle")
                mock_create.assert_called_once()
                args, kwargs = mock_create.call_args
                assert args[0] == "mge_lifecycle"
                assert callable(args[1])
                assert kwargs.get("replace") is False


@pytest.mark.asyncio
async def test_start_mge_tasks_when_ready_skips_when_not_ready():
    import bot_instance as bi

    with patch.object(bi, "wait_for_events", new=AsyncMock(return_value=False)):
        with patch.object(bi.task_monitor, "is_running", return_value=False):
            with patch.object(bi.task_monitor, "create") as mock_create:
                await bi._start_mge_tasks_when_ready(max_wait_seconds=5)
                mock_create.assert_not_called()
