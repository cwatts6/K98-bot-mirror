from __future__ import annotations

from datetime import UTC, datetime

import pytest

from upload_routes import weekly_activity_route as route


class _FakeAttachment:
    def __init__(self, filename: str, payload: bytes = b"xlsx"):
        self.filename = filename
        self._payload = payload
        self.reads = 0

    async def read(self) -> bytes:
        self.reads += 1
        return self._payload


class _FakeChannel:
    def __init__(self, channel_id: int = 10, name: str = "activity"):
        self.id = channel_id
        self.name = name


class _FakeAuthor:
    id = 123456789

    def __str__(self) -> str:
        return "uploader"


class _FakeMessage:
    def __init__(self, channel_id: int = 10, attachments=None):
        self.id = 987
        self.channel = _FakeChannel(channel_id)
        self.author = _FakeAuthor()
        self.attachments = (
            attachments
            if attachments is not None
            else [_FakeAttachment("1198_alliance_activity.xlsx")]
        )
        self.created_at = datetime(2026, 5, 26, 12, 30, tzinfo=UTC)


def _message(channel_id: int = 10, attachments=None) -> _FakeMessage:
    return _FakeMessage(channel_id, attachments)


def _deps(**overrides):
    sent = []
    offloads = []
    created_tasks = []
    preflight_channels = []

    async def get_notify_channel():
        if "notify_exception" in overrides:
            raise overrides["notify_exception"]
        return overrides.get("notify_channel")

    async def send_embed(ch, title, fields, color, mention=None):
        sent.append((ch, title, fields, color, mention))
        if "send_exception" in overrides:
            raise overrides["send_exception"]

    async def ensure_sql_headroom_or_notify(ch):
        preflight_channels.append(ch)
        return overrides.get("sql_ok", True)

    async def offload_callable(func, *args, **kwargs):
        offloads.append((func, args, kwargs))
        if "offload_exception" in overrides:
            raise overrides["offload_exception"]
        return overrides.get("offload_result", (42, 7))

    async def trigger_log_backup_background():
        return None

    def create_task(coro):
        created_tasks.append(coro)
        coro.close()
        return None

    deps = route.WeeklyActivityRouteDeps(
        activity_upload_channel_id=10,
        get_notify_channel=overrides.get("get_notify_channel", get_notify_channel),
        send_embed=send_embed,
        ensure_sql_headroom_or_notify=ensure_sql_headroom_or_notify,
        offload_callable=offload_callable,
        trigger_log_backup_background=trigger_log_backup_background,
        server="server",
        database="database",
        username="username",
        password="password",
        create_task=create_task,
    )
    return deps, sent, offloads, created_tasks, preflight_channels


@pytest.mark.asyncio
async def test_weekly_activity_route_ignores_other_channels():
    deps, sent, offloads, _created, _preflight = _deps()

    handled = await route.handle_weekly_activity_upload(_message(channel_id=99), deps)

    assert handled is False
    assert sent == []
    assert offloads == []


@pytest.mark.asyncio
async def test_weekly_activity_route_ignores_empty_attachments():
    deps, sent, offloads, _created, _preflight = _deps()

    handled = await route.handle_weekly_activity_upload(_message(attachments=[]), deps)

    assert handled is False
    assert sent == []
    assert offloads == []


@pytest.mark.asyncio
async def test_weekly_activity_route_ignores_non_matching_filename():
    deps, sent, offloads, _created, _preflight = _deps()

    handled = await route.handle_weekly_activity_upload(
        _message(attachments=[_FakeAttachment("activity.xlsx")]), deps
    )

    assert handled is False
    assert sent == []
    assert offloads == []


@pytest.mark.asyncio
async def test_weekly_activity_route_sql_preflight_abort_preserves_read_order():
    attachment = _FakeAttachment("1198_alliance_activity.xlsx")
    deps, sent, offloads, _created, preflight = _deps(sql_ok=False)

    handled = await route.handle_weekly_activity_upload(_message(attachments=[attachment]), deps)

    assert handled is True
    assert attachment.reads == 1
    assert len(preflight) == 1
    assert sent == []
    assert offloads == []


@pytest.mark.asyncio
async def test_weekly_activity_route_success_preserves_import_contract_and_embed():
    deps, sent, offloads, created, _preflight = _deps()

    handled = await route.handle_weekly_activity_upload(_message(), deps)

    assert handled is True
    assert len(offloads) == 1
    func, args, kwargs = offloads[0]
    assert func is route.ingest_weekly_activity_excel
    assert args == ()
    assert kwargs == {
        "content": b"xlsx",
        "snapshot_ts_utc": datetime(2026, 5, 26, 12, 30, tzinfo=UTC),
        "message_id": 987,
        "channel_id": 10,
        "server": "server",
        "database": "database",
        "username": "username",
        "password": "password",
        "source_filename": "1198_alliance_activity.xlsx",
        "name": "ingest_weekly_activity_excel",
        "prefer_process": True,
        "meta": {"filename": "1198_alliance_activity.xlsx"},
    }
    assert len(created) == 1
    _ch, title, fields, color, mention = sent[-1]
    assert title == "Alliance Activity Import \u2705"
    assert fields == {
        "SnapshotId": "42",
        "Rows": "7",
        "Filename": "1198_alliance_activity.xlsx",
        "Channel": "#activity (10)",
        "Uploader": "uploader (123456789)",
        "Note": "",
    }
    assert color == 0x2ECC71
    assert mention is None


@pytest.mark.asyncio
async def test_weekly_activity_route_duplicate_preserves_minimal_embed():
    deps, sent, _offloads, created, _preflight = _deps(offload_result=(0, 0))

    handled = await route.handle_weekly_activity_upload(_message(), deps)

    assert handled is True
    assert created == []
    _ch, title, fields, color, mention = sent[-1]
    assert title == "Alliance Activity Import"
    assert fields == {"Status": "Duplicate detected for this week. Skipped."}
    assert color == 0xF1C40F
    assert mention is None


@pytest.mark.asyncio
async def test_weekly_activity_route_import_exception_sends_existing_error():
    deps, sent, _offloads, created, _preflight = _deps(offload_exception=RuntimeError("boom"))

    handled = await route.handle_weekly_activity_upload(_message(), deps)

    assert handled is True
    assert created == []
    _ch, title, fields, color, mention = sent[-1]
    assert title == "Alliance Activity Import \u274c"
    assert fields["Error"] == "RuntimeError: boom"
    assert fields["Filename"] == "1198_alliance_activity.xlsx"
    assert fields["Channel"] == "#activity (10)"
    assert fields["Uploader"] == "uploader (123456789)"
    assert color == 0xE74C3C
    assert mention is None


@pytest.mark.asyncio
async def test_weekly_activity_route_error_embed_failure_is_swallowed():
    deps, sent, _offloads, created, _preflight = _deps(
        offload_exception=RuntimeError("boom"),
        send_exception=RuntimeError("discord down"),
    )

    handled = await route.handle_weekly_activity_upload(_message(), deps)

    assert handled is True
    assert created == []
    assert sent[-1][1] == "Alliance Activity Import \u274c"


@pytest.mark.asyncio
async def test_weekly_activity_route_notify_failure_falls_back_to_source_channel():
    deps, sent, _offloads, _created, preflight = _deps(notify_exception=RuntimeError("notify down"))
    message = _message()

    handled = await route.handle_weekly_activity_upload(message, deps)

    assert handled is True
    assert preflight == [message.channel]
    assert sent[-1][0] is message.channel
