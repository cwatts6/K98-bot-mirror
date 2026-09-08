from __future__ import annotations

from asyncio import QueueFull
from datetime import UTC, datetime

import pytest

from upload_routes import fallback_queue_route as route


class _FakeAttachment:
    def __init__(self, filename: str):
        self.filename = filename


class _FakeChannel:
    def __init__(self, channel_id: int = 10, name: str = "uploads"):
        self.id = channel_id
        self.name = name


class _FakeAuthor:
    def __str__(self) -> str:
        return "uploader"


class _FakeMessage:
    def __init__(self, channel_id: int = 10, attachments=None):
        self.id = 987654321
        self.channel = _FakeChannel(channel_id)
        self.author = _FakeAuthor()
        self.attachments = (
            attachments if attachments is not None else [_FakeAttachment("stats.xlsx")]
        )


class _FakeQueue:
    def __init__(self, *, full: bool = False):
        self.full = full
        self.items = []

    def put_nowait(self, item):
        if self.full:
            raise QueueFull
        self.items.append(item)


class _FakeLock:
    def __init__(self, *, enter_exception: Exception | None = None):
        self.enter_exception = enter_exception
        self.entered = 0

    async def __aenter__(self):
        self.entered += 1
        if self.enter_exception is not None:
            raise self.enter_exception
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _message(channel_id: int = 10, attachments=None) -> _FakeMessage:
    return _FakeMessage(channel_id, attachments)


def _deps(**overrides):
    live_queue = overrides.get("live_queue", {"jobs": []})
    queue = overrides.get("queue", _FakeQueue())
    channel_queues = overrides.get("channel_queues", {10: queue})
    updated = []
    created = []

    async def update_live_queue_embed(bot, notify_channel_id):
        updated.append((bot, notify_channel_id))
        if "update_exception" in overrides:
            raise overrides["update_exception"]

    async def trigger_log_backup_background():
        return None

    def create_task(coro):
        created.append(coro)
        if "create_task_exception" in overrides:
            raise overrides["create_task_exception"]
        coro.close()
        return None

    deps = route.FallbackQueueRouteDeps(
        channel_ids=overrides.get("channel_ids", [10]),
        channel_queues=channel_queues,
        live_queue=live_queue,
        live_queue_lock=overrides.get("live_queue_lock", _FakeLock()),
        bot=overrides.get("bot", object()),
        notify_channel_id=overrides.get("notify_channel_id", 99),
        update_live_queue_embed=update_live_queue_embed,
        trigger_log_backup_background=overrides.get(
            "trigger_log_backup_background", trigger_log_backup_background
        ),
        utcnow=overrides.get(
            "utcnow",
            lambda: datetime(2026, 5, 26, 12, 30, tzinfo=UTC),
        ),
        create_task=create_task,
    )
    return deps, queue, live_queue, updated, created


@pytest.mark.asyncio
async def test_fallback_route_ignores_unmonitored_channel():
    deps, queue, live_queue, updated, created = _deps()

    handled = await route.handle_fallback_queue_upload(_message(channel_id=99), deps)

    assert handled is False
    assert queue.items == []
    assert live_queue["jobs"] == []
    assert updated == []
    assert created == []


@pytest.mark.asyncio
async def test_fallback_route_ignores_unsupported_attachments_but_handles_channel():
    deps, queue, live_queue, updated, created = _deps()

    handled = await route.handle_fallback_queue_upload(
        _message(attachments=[_FakeAttachment("notes.txt")]), deps
    )

    assert handled is True
    assert queue.items == []
    assert live_queue["jobs"] == []
    assert updated == []
    assert created == []


@pytest.mark.asyncio
@pytest.mark.parametrize("filename", ["stats.xlsx", "stats.xls", "stats.csv"])
async def test_fallback_route_accepts_existing_extensions(filename: str):
    deps, queue, live_queue, updated, created = _deps()
    message = _message(attachments=[_FakeAttachment(filename)])

    handled = await route.handle_fallback_queue_upload(message, deps)

    assert handled is True
    assert queue.items == [message]
    assert live_queue["jobs"] == [
        {
            "filename": filename,
            "user": "uploader",
            "channel": "uploads",
            "uploaded": "2026-05-26T12:30:00+00:00",
            "status": "🕐 Queued",
        }
    ]
    assert len(updated) == 1
    assert len(created) == 1


@pytest.mark.asyncio
async def test_fallback_route_missing_queue_does_not_append_or_update():
    deps, _queue, live_queue, updated, created = _deps(channel_queues={})

    handled = await route.handle_fallback_queue_upload(_message(), deps)

    assert handled is True
    assert live_queue["jobs"] == []
    assert updated == []
    assert created == []


@pytest.mark.asyncio
async def test_fallback_route_queue_full_drops_without_side_effects():
    deps, queue, live_queue, updated, created = _deps(queue=_FakeQueue(full=True))

    handled = await route.handle_fallback_queue_upload(_message(), deps)

    assert handled is True
    assert queue.items == []
    assert live_queue["jobs"] == []
    assert updated == []
    assert created == []


@pytest.mark.asyncio
async def test_fallback_route_live_queue_append_failure_is_non_fatal():
    deps, queue, live_queue, updated, created = _deps(
        live_queue_lock=_FakeLock(enter_exception=RuntimeError("lock failed"))
    )
    message = _message()

    handled = await route.handle_fallback_queue_upload(message, deps)

    assert handled is True
    assert queue.items == [message]
    assert live_queue["jobs"] == []
    assert len(updated) == 1
    assert len(created) == 1


@pytest.mark.asyncio
async def test_fallback_route_embed_update_failure_is_non_fatal():
    deps, queue, live_queue, updated, created = _deps(update_exception=RuntimeError("discord down"))
    message = _message()

    handled = await route.handle_fallback_queue_upload(message, deps)

    assert handled is True
    assert queue.items == [message]
    assert len(live_queue["jobs"]) == 1
    assert len(updated) == 1
    assert len(created) == 1


@pytest.mark.asyncio
async def test_fallback_route_backup_scheduling_failure_is_non_fatal():
    deps, queue, live_queue, updated, created = _deps(
        create_task_exception=RuntimeError("scheduler down")
    )
    message = _message()

    handled = await route.handle_fallback_queue_upload(message, deps)

    assert handled is True
    assert queue.items == [message]
    assert len(live_queue["jobs"]) == 1
    assert len(updated) == 1
    assert len(created) == 1


@pytest.mark.asyncio
async def test_fallback_route_backup_awaitable_construction_failure_is_non_fatal():
    def trigger_log_backup_background():
        raise RuntimeError("factory down")

    deps, queue, live_queue, updated, created = _deps(
        trigger_log_backup_background=trigger_log_backup_background
    )
    message = _message()

    handled = await route.handle_fallback_queue_upload(message, deps)

    assert handled is True
    assert queue.items == [message]
    assert len(live_queue["jobs"]) == 1
    assert len(updated) == 1
    assert created == []


@pytest.mark.asyncio
async def test_fallback_route_preserves_enqueue_per_accepted_attachment_behavior():
    deps, queue, live_queue, updated, created = _deps()
    message = _message(
        attachments=[
            _FakeAttachment("first.xlsx"),
            _FakeAttachment("skip.txt"),
            _FakeAttachment("second.csv"),
        ]
    )

    handled = await route.handle_fallback_queue_upload(message, deps)

    assert handled is True
    assert queue.items == [message, message]
    assert [job["filename"] for job in live_queue["jobs"]] == ["first.xlsx", "second.csv"]
    assert len(updated) == 2
    assert len(created) == 2
