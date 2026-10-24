from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

import bot_helpers


class _SingleMessageQueue:
    def __init__(self, message) -> None:
        self._message = message
        self._served = False
        self.task_done_calls = 0

    async def get(self):
        if not self._served:
            self._served = True
            return self._message
        raise asyncio.CancelledError

    def task_done(self) -> None:
        self.task_done_calls += 1


@pytest.mark.asyncio
async def test_admin_user_fetch_completes_before_fallback_processing_lock(
    monkeypatch,
    tmp_path: Path,
) -> None:
    channel_id = 987654
    processing_lock = asyncio.Lock()
    admin_user = object()
    events: list[tuple[str, bool]] = []

    class _Bot:
        def get_user(self, user_id: int):
            assert user_id == bot_helpers.ADMIN_USER_ID
            events.append(("cache_lookup", processing_lock.locked()))
            return None

        async def fetch_user(self, user_id: int):
            assert user_id == bot_helpers.ADMIN_USER_ID
            events.append(("fetch_user", processing_lock.locked()))
            return admin_user

    async def stage_and_process(
        _attachment,
        *,
        processing_lock,
        process_attachment,
        **_kwargs,
    ) -> bool:
        events.append(("stage", processing_lock.locked()))
        staged_path = tmp_path / "stats.csv"
        staged_path.write_text("payload", encoding="utf-8")
        async with processing_lock:
            events.append(("process_callback", processing_lock.locked()))
            await process_attachment("stats.csv", str(staged_path))
        return True

    async def append_csv_line(*_args, **_kwargs) -> None:
        return None

    async def handle_file_processing(user, *_args, **_kwargs) -> None:
        assert user is admin_user
        events.append(("handle_file_processing", processing_lock.locked()))

    message = SimpleNamespace(
        attachments=[SimpleNamespace(filename="stats.csv")],
        channel=SimpleNamespace(name="uploads"),
        author=SimpleNamespace(__str__=lambda _self: "uploader"),
    )
    queue = _SingleMessageQueue(message)

    monkeypatch.setattr(bot_helpers, "bot", _Bot())
    monkeypatch.setattr(bot_helpers, "processing_lock", processing_lock)
    monkeypatch.setattr(bot_helpers, "channel_queues", {channel_id: queue})
    monkeypatch.setattr(bot_helpers, "active_jobs", set())
    monkeypatch.setattr(bot_helpers, "active_jobs_lock", asyncio.Lock())
    monkeypatch.setattr(
        bot_helpers,
        "stage_and_process_fallback_attachment",
        stage_and_process,
    )
    monkeypatch.setattr(bot_helpers, "append_csv_line", append_csv_line)
    monkeypatch.setattr(bot_helpers, "handle_file_processing", handle_file_processing)

    await bot_helpers.queue_worker(channel_id)

    assert events == [
        ("cache_lookup", False),
        ("fetch_user", False),
        ("stage", False),
        ("process_callback", True),
        ("handle_file_processing", True),
    ]
    assert queue.task_done_calls == 1
