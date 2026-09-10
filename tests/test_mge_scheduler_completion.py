from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from mge.mge_scheduler import schedule_mge_lifecycle


@pytest.mark.asyncio
async def test_scheduler_runs_completion_sweep_once() -> None:
    class _FakeBot:
        pass

    fake_result = SimpleNamespace(scanned=1, created=0, existing=1, skipped=0, errors=0)

    with (
        patch(
            "mge.mge_scheduler.resolve_public_signup_channel_id",
            return_value=(12345, 12345, "primary"),
        ),
        patch(
            "mge.mge_scheduler.sync_mge_events_from_calendar",
            return_value=(fake_result, [101]),
        ),
        patch(
            "mge.mge_scheduler.sync_event_signup_embed",
            new_callable=AsyncMock,
        ),
        patch(
            "mge.mge_completion_service.auto_complete_due_events",
            return_value={"ok": True, "due_count": 1, "completed_count": 1},
        ) as mock_complete,
        patch("mge.mge_scheduler._INTERVAL_SECONDS", 1),
    ):
        task = asyncio.create_task(schedule_mge_lifecycle(_FakeBot()))
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        assert mock_complete.call_count >= 1
