from __future__ import annotations

from datetime import UTC, datetime
import logging

import pytest

from upload_routes import honor_route as route


class _FakeAttachment:
    def __init__(self, filename: str, payload: bytes = b"xlsx"):
        self.filename = filename
        self._payload = payload

    async def read(self) -> bytes:
        return self._payload


class _FakeChannel:
    def __init__(self, channel_id: int, name: str = "honor"):
        self.id = channel_id
        self.name = name


class _FakeAuthor:
    id = 123456789

    def __str__(self) -> str:
        return "uploader"


class _FakeBot:
    pass


class _FakeParsedHonor:
    def __len__(self) -> int:
        return 4


class _FakeMessage:
    def __init__(self, channel_id: int = 10, attachments=None, content: str = ""):
        self.channel = _FakeChannel(channel_id)
        self.author = _FakeAuthor()
        self.attachments = (
            attachments if attachments is not None else [_FakeAttachment("1198_honor.xlsx")]
        )
        self.content = content
        self.created_at = datetime(2026, 5, 24, 10, 30, tzinfo=UTC)


def _message(channel_id: int = 10, attachments=None, content: str = "") -> _FakeMessage:
    return _FakeMessage(channel_id, attachments, content)


def _deps(**overrides):
    sent = []
    offloads = []
    created_tasks = []
    stats_refreshes = []

    async def get_notify_channel():
        return overrides.get("notify_channel")

    async def send_embed(ch, title, fields, color, mention=None):
        sent.append((ch, title, fields, color, mention))

    async def ensure_sql_headroom_or_notify(ch):
        return overrides.get("sql_ok", True)

    async def offload_callable(func, *args, **kwargs):
        offloads.append((func, args, kwargs))
        if func is route.parse_honor_xlsx:
            if "parse_exception" in overrides:
                raise overrides["parse_exception"]
            return overrides.get("parse_result", _FakeParsedHonor())
        if "ingest_exception" in overrides:
            raise overrides["ingest_exception"]
        return overrides.get("ingest_result", (15, 9))

    async def trigger_log_backup_background():
        return None

    def create_task(coro):
        created_tasks.append(coro)
        coro.close()
        return None

    async def send_stats_update_embed(*args, **kwargs):
        stats_refreshes.append((args, kwargs))
        if "stats_exception" in overrides:
            raise overrides["stats_exception"]

    deps = route.HonorRouteDeps(
        honor_channel_id=10,
        bot=overrides.get("bot", _FakeBot()),
        get_notify_channel=overrides.get("get_notify_channel", get_notify_channel),
        send_embed=send_embed,
        ensure_sql_headroom_or_notify=ensure_sql_headroom_or_notify,
        offload_callable=offload_callable,
        trigger_log_backup_background=trigger_log_backup_background,
        create_task=create_task,
        send_stats_update_embed=overrides.get("send_stats_update_embed", send_stats_update_embed),
        now_utc=lambda: datetime(2026, 5, 24, 12, 45, tzinfo=UTC),
        sql_conn_str_factory=lambda: "conn",
    )
    return deps, sent, offloads, created_tasks, stats_refreshes


@pytest.mark.asyncio
async def test_honor_route_ignores_other_channels():
    deps, sent, offloads, _created, _stats = _deps()

    handled = await route.handle_honor_upload(_message(channel_id=99), deps)

    assert handled is False
    assert sent == []
    assert offloads == []


@pytest.mark.asyncio
async def test_honor_route_ignores_empty_attachments():
    deps, sent, offloads, _created, _stats = _deps()

    handled = await route.handle_honor_upload(_message(attachments=[]), deps)

    assert handled is False
    assert sent == []
    assert offloads == []


@pytest.mark.asyncio
async def test_honor_route_no_matching_file_warns_and_handles():
    deps, sent, offloads, _created, _stats = _deps()

    handled = await route.handle_honor_upload(
        _message(attachments=[_FakeAttachment("unrelated.xlsx")]), deps
    )

    assert handled is True
    assert offloads == []
    _ch, title, fields, color, mention = sent[-1]
    assert title == "KVK Honor Import \u26a0\ufe0f"
    assert fields["Info"] == "No matching file found."
    assert fields["Expected"] == (
        "1198_honor.xlsx  \u2022 also accepts *1198_honor*.xlsx with optional "
        "TEST_/DEMO_/SAMPLE_ prefix"
    )
    assert fields["Channel"] == "#honor (10)"
    assert fields["Uploader"] == "uploader (123456789)"
    assert color == 0xE67E22
    assert mention is None


@pytest.mark.asyncio
async def test_honor_route_sql_preflight_abort_skips_ingest():
    deps, sent, offloads, _created, _stats = _deps(sql_ok=False)

    handled = await route.handle_honor_upload(_message(), deps)

    assert handled is True
    assert sent == []
    assert offloads == []


@pytest.mark.asyncio
async def test_honor_route_success_preserves_import_contract_and_side_effects():
    deps, sent, offloads, created, stats = _deps()

    handled = await route.handle_honor_upload(_message(), deps)

    assert handled is True
    assert len(offloads) == 2
    parse_func, parse_args, parse_kwargs = offloads[0]
    assert parse_func is route.parse_honor_xlsx
    assert parse_args == (b"xlsx",)
    assert parse_kwargs["name"] == "parse_honor_xlsx"
    assert parse_kwargs["prefer_process"] is True
    assert parse_kwargs["meta"] == {"filename": "1198_honor.xlsx"}
    ingest_func, ingest_args, ingest_kwargs = offloads[1]
    assert ingest_func is route.ingest_honor_snapshot
    assert ingest_args == (b"xlsx",)
    assert ingest_kwargs["source_filename"] == "1198_honor.xlsx"
    assert ingest_kwargs["scan_ts_utc"] == datetime(2026, 5, 24, 10, 30, tzinfo=UTC)
    assert ingest_kwargs["name"] == "ingest_honor_snapshot"
    assert ingest_kwargs["prefer_process"] is True
    assert ingest_kwargs["meta"] == {"filename": "1198_honor.xlsx"}
    assert len(created) == 1
    assert len(stats) == 1
    stats_args, stats_kwargs = stats[0]
    assert stats_args == (deps.bot, "2026-05-24 12:45 UTC", True, "conn")
    assert stats_kwargs == {"is_test": False}
    _ch, title, fields, color, mention = sent[-1]
    assert title == "KVK Honor Import \u2705"
    assert fields["KVK"] == "15"
    assert fields["ScanID"] == "9"
    assert fields["Rows"] == "4"
    assert fields["Filename"] == "1198_honor.xlsx"
    assert color == 0x2ECC71
    assert mention is None


@pytest.mark.asyncio
async def test_honor_route_test_mode_preserved_for_prefixed_filename():
    deps, sent, _offloads, _created, stats = _deps()

    handled = await route.handle_honor_upload(
        _message(attachments=[_FakeAttachment("test_1198_honor.xlsx")]), deps
    )

    assert handled is True
    assert sent[-1][1] == "KVK Honor Import \u2705 (TEST)"
    assert stats[-1][1] == {"is_test": True}


@pytest.mark.asyncio
async def test_honor_route_parse_failure_preserves_zero_row_count():
    deps, sent, offloads, _created, _stats = _deps(parse_exception=ValueError("bad sheet"))

    handled = await route.handle_honor_upload(_message(), deps)

    assert handled is True
    assert len(offloads) == 2
    _ch, _title, fields, _color, _mention = sent[-1]
    assert fields["Rows"] == "0"


@pytest.mark.asyncio
async def test_honor_route_ingest_exception_sends_existing_error():
    deps, sent, _offloads, created, stats = _deps(ingest_exception=RuntimeError("boom"))

    handled = await route.handle_honor_upload(_message(), deps)

    assert handled is True
    assert created == []
    assert stats == []
    _ch, title, fields, color, mention = sent[-1]
    assert title == "KVK Honor Import \u274c"
    assert fields["Error"] == "RuntimeError: boom"
    assert fields["Filename"] == "1198_honor.xlsx"
    assert fields["Channel"] == "#honor (10)"
    assert fields["Uploader"] == "uploader (123456789)"
    assert color == 0xE74C3C
    assert mention is None


@pytest.mark.asyncio
async def test_honor_route_stats_refresh_failure_is_best_effort(caplog):
    deps, sent, _offloads, created, stats = _deps(stats_exception=RuntimeError("stats down"))
    caplog.set_level(logging.DEBUG, logger=route.__name__)

    handled = await route.handle_honor_upload(_message(), deps)

    assert handled is True
    assert len(created) == 1
    assert len(stats) == 1
    assert sent[-1][1] == "KVK Honor Import \u2705"
    assert "Failed to refresh stats embed after KVK Honor import" in caplog.text
