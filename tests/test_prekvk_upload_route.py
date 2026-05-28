from __future__ import annotations

from datetime import UTC, datetime
import logging

import pytest

from upload_routes import prekvk_route as route


class _FakeAttachment:
    def __init__(self, filename: str, payload: bytes = b"xlsx"):
        self.filename = filename
        self._payload = payload

    async def read(self) -> bytes:
        return self._payload


class _FakeChannel:
    def __init__(self, channel_id: int, name: str = "pre-kvk"):
        self.id = channel_id
        self.name = name


class _FakeAuthor:
    id = 123456789

    def __str__(self) -> str:
        return "uploader"


class _FakeBot:
    pass


class _FakeMessage:
    def __init__(self, channel_id: int = 10, attachments=None):
        self.channel = _FakeChannel(channel_id)
        self.author = _FakeAuthor()
        self.attachments = (
            attachments if attachments is not None else [_FakeAttachment("1198_prekvk.xlsx")]
        )
        self.id = 987654321


def _message(channel_id: int = 10, attachments=None) -> _FakeMessage:
    return _FakeMessage(channel_id, attachments)


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

    async def run_blocking_in_thread(func, *args, **kwargs):
        return func(*args)

    def current_kvk_metadata():
        if "metadata" in overrides:
            return overrides["metadata"]
        return {"kvk_no": 15}

    async def offload_callable(func, *args, **kwargs):
        offloads.append((func, args, kwargs))
        if "offload_exception" in overrides:
            raise overrides["offload_exception"]
        return overrides.get("offload_result", (True, "Imported 3 rows as scan 9.", 3))

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

    deps = route.PreKvkRouteDeps(
        prekvk_channel_id=10,
        bot=overrides.get("bot", _FakeBot()),
        get_notify_channel=overrides.get("get_notify_channel", get_notify_channel),
        send_embed=send_embed,
        ensure_sql_headroom_or_notify=ensure_sql_headroom_or_notify,
        offload_callable=offload_callable,
        trigger_log_backup_background=trigger_log_backup_background,
        create_task=create_task,
        current_kvk_metadata=overrides.get("current_kvk_metadata", current_kvk_metadata),
        run_blocking_in_thread=overrides.get("run_blocking_in_thread", run_blocking_in_thread),
        send_stats_update_embed=overrides.get("send_stats_update_embed", send_stats_update_embed),
        now_utc=lambda: datetime(2026, 5, 16, 12, 30, tzinfo=UTC),
    )
    return deps, sent, offloads, created_tasks, stats_refreshes


@pytest.mark.asyncio
async def test_prekvk_route_ignores_other_channels():
    deps, sent, offloads, _created, _stats = _deps()

    handled = await route.handle_prekvk_upload(_message(channel_id=99), deps)

    assert handled is False
    assert sent == []
    assert offloads == []


@pytest.mark.asyncio
async def test_prekvk_route_ignores_empty_attachments():
    deps, sent, offloads, _created, _stats = _deps()

    handled = await route.handle_prekvk_upload(_message(attachments=[]), deps)

    assert handled is False
    assert sent == []
    assert offloads == []


@pytest.mark.asyncio
async def test_prekvk_route_no_matching_file_warns_and_handles():
    deps, sent, offloads, _created, _stats = _deps()

    handled = await route.handle_prekvk_upload(
        _message(attachments=[_FakeAttachment("unrelated.xlsx")]), deps
    )

    assert handled is True
    assert offloads == []
    _ch, title, fields, color, mention = sent[-1]
    assert title == "Pre-KVK Import ⚠️"
    assert fields["Info"] == "No matching file found."
    assert fields["Expected"] == "1198_prekvk.xlsx or PreKvK_Rankings_*.xlsx"
    assert color == 0xE67E22
    assert mention is None


@pytest.mark.asyncio
async def test_prekvk_route_sql_preflight_abort_skips_import():
    deps, sent, offloads, _created, _stats = _deps(sql_ok=False)

    handled = await route.handle_prekvk_upload(_message(), deps)

    assert handled is True
    assert sent == []
    assert offloads == []


@pytest.mark.asyncio
async def test_prekvk_route_kvk_lookup_failure_sends_existing_error():
    deps, sent, offloads, _created, _stats = _deps(metadata=None)

    handled = await route.handle_prekvk_upload(_message(), deps)

    assert handled is True
    assert offloads == []
    _ch, title, fields, color, _mention = sent[-1]
    assert title == "Pre-KVK Import ❌"
    assert fields["Error"] == "Could not determine current KVK number (kvk_no). Import aborted."
    assert fields["Filename"] == "1198_prekvk.xlsx"
    assert color == 0xE74C3C


@pytest.mark.asyncio
async def test_prekvk_route_success_preserves_import_contract_and_side_effects():
    deps, sent, offloads, created, stats = _deps()
    msg = _message(
        attachments=[_FakeAttachment("PreKvK_Rankings_C13164_2026-05-08.xlsx", b"xlsx-bytes")]
    )

    handled = await route.handle_prekvk_upload(msg, deps)

    assert handled is True
    assert len(offloads) == 1
    func, args, kwargs = offloads[0]
    assert func is route.import_prekvk_bytes
    assert args == (b"xlsx-bytes", "PreKvK_Rankings_C13164_2026-05-08.xlsx")
    assert kwargs["kvk_no"] == 15
    assert kwargs["uploader_discord_id"] == 123456789
    assert kwargs["channel_id"] == 10
    assert kwargs["message_id"] == 987654321
    assert kwargs["name"] == "import_prekvk_bytes"
    assert kwargs["prefer_process"] is True
    assert kwargs["meta"] == {
        "filename": "PreKvK_Rankings_C13164_2026-05-08.xlsx",
        "kvk_no": 15,
    }
    assert len(created) == 1
    assert len(stats) == 1
    stats_args, stats_kwargs = stats[0]
    assert stats_args[1] == "2026-05-16 12:30 UTC"
    assert stats_args[2] is True
    assert stats_kwargs == {"is_test": False}
    _ch, title, fields, color, _mention = sent[-1]
    assert title == "Pre-KVK Snapshot Imported ✅"
    assert fields["KVK"] == "15"
    assert fields["Rows"] == "3"
    assert fields["Note"] == "Imported 3 rows as scan 9."
    assert color == 0x2ECC71


@pytest.mark.asyncio
async def test_prekvk_route_duplicate_skip_preserves_embed_without_refresh_side_effects():
    deps, sent, offloads, created, stats = _deps(
        offload_result=(True, "Duplicate file skipped (hash match).", 0)
    )

    handled = await route.handle_prekvk_upload(_message(), deps)

    assert handled is True
    assert len(offloads) == 1
    assert created == []
    assert stats == []
    _ch, title, fields, color, _mention = sent[-1]
    assert title == "Pre-KVK Snapshot Skipped"
    assert fields["Rows"] == "0"
    assert fields["Note"] == "Duplicate file skipped (hash match)."
    assert color == 0xF1C40F


@pytest.mark.asyncio
async def test_prekvk_route_importer_failure_sends_existing_error():
    deps, sent, _offloads, created, stats = _deps(offload_result=(False, "bad workbook", 0))

    handled = await route.handle_prekvk_upload(_message(), deps)

    assert handled is True
    assert created == []
    assert stats == []
    _ch, title, fields, color, _mention = sent[-1]
    assert title == "Pre-KVK Import ❌"
    assert fields["Error"] == "bad workbook"
    assert color == 0xE74C3C


@pytest.mark.asyncio
async def test_prekvk_route_duplicate_governor_rejection_is_error():
    deps, sent, _offloads, created, stats = _deps(
        offload_result=(False, "Duplicate GovernorID(s) detected in file: 123.", 0)
    )

    handled = await route.handle_prekvk_upload(_message(), deps)

    assert handled is True
    assert created == []
    assert stats == []
    _ch, title, fields, color, _mention = sent[-1]
    assert title == "Pre-KVK Import ❌"
    assert fields["Error"] == "Duplicate GovernorID(s) detected in file: 123."
    assert "Info" not in fields
    assert color == 0xE74C3C


@pytest.mark.asyncio
async def test_prekvk_route_importer_exception_sends_existing_error():
    deps, sent, _offloads, created, stats = _deps(offload_exception=RuntimeError("boom"))

    handled = await route.handle_prekvk_upload(_message(), deps)

    assert handled is True
    assert created == []
    assert stats == []
    _ch, title, fields, color, _mention = sent[-1]
    assert title == "Pre-KVK Import ❌"
    assert fields["Error"] == "RuntimeError: boom"
    assert color == 0xE74C3C


@pytest.mark.asyncio
async def test_prekvk_route_stats_refresh_failure_is_best_effort(caplog):
    deps, sent, _offloads, created, stats = _deps(stats_exception=RuntimeError("stats down"))

    caplog.set_level(logging.DEBUG, logger=route.__name__)

    handled = await route.handle_prekvk_upload(_message(), deps)

    assert handled is True
    assert len(created) == 1
    assert len(stats) == 1
    _ch, title, _fields, color, _mention = sent[-1]
    assert title == "Pre-KVK Snapshot Imported ✅"
    assert color == 0x2ECC71
    assert "Failed to refresh stats embed after Pre-KVK import" in caplog.text
