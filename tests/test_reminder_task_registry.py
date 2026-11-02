import asyncio

import pytest

# The test assumes reminder_task_registry.py from the previous changeset is present
from reminder_task_registry import (
    active_task_count,
    cancel_and_wait_user_tasks,
    schedule_for_user,
    user_task_snapshot,
)


async def _never_finish():
    # Wait on an event that is never set; respond to cancellation normally.
    ev = asyncio.Event()
    try:
        await ev.wait()
    except asyncio.CancelledError:
        # allow cancellation to bubble up
        raise


@pytest.mark.asyncio
async def test_schedule_and_cancel_user_task():
    user_id = "test-user-123"
    event_id = "test:event:2025-11-17T00:00:00Z"
    delta_seconds = 60

    # Schedule the long-running task with metadata (event_id + delta_seconds)
    schedule_for_user(
        user_id,
        _never_finish(),
        meta={"event_id": event_id, "delta_seconds": delta_seconds},
        name="test_never_finish",
    )

    # Give the loop a tick for the registry registration to run
    await asyncio.sleep(0)

    # Assert active task count for user is 1
    assert active_task_count(user_id) == 1

    # Cancel and wait for the user's tasks to finish (should cancel our task)
    cancelled = await cancel_and_wait_user_tasks(user_id, timeout=2.0)
    assert cancelled >= 1

    # allow cleanup callbacks to run
    await asyncio.sleep(0.05)

    # Verify there are no active tasks left for this user
    assert active_task_count(user_id) == 0

    # Snapshot should contain an empty list for this user
    snap = user_task_snapshot(user_id)
    # snapshot returns {uid: [metas...]}
    assert isinstance(snap, dict)
    assert all(not v for v in snap.get(str(user_id), []))
