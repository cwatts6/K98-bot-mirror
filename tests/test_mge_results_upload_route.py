from __future__ import annotations

import pytest

from upload_routes import mge_results_route as route


class _FakeAttachment:
    def __init__(self, filename: str, payload: bytes = b"xlsx"):
        self.filename = filename
        self._payload = payload

    async def read(self) -> bytes:
        return self._payload


class _FakeChannel:
    def __init__(self, channel_id: int, name: str = "mge-data"):
        self.id = channel_id
        self.name = name


class _FakeAuthor:
    id = 123456789

    def __str__(self) -> str:
        return "uploader"


class _FakeMessage:
    def __init__(self, channel_id: int = 10, attachments=None):
        self.channel = _FakeChannel(channel_id)
        self.author = _FakeAuthor()
        self.attachments = (
            attachments
            if attachments is not None
            else [_FakeAttachment("mge_rankings_kd1198_20260311.xlsx")]
        )


def _message(channel_id: int = 10, attachments=None) -> _FakeMessage:
    return _FakeMessage(channel_id, attachments)


def _success_result(**overrides):
    result = {
        "event_id": 42,
        "event_mode": "open",
        "rows": 3,
        "import_id": 77,
        "report": {"type": "open_top15"},
    }
    result.update(overrides)
    return result


def _deps(**overrides):
    sent = []
    offloads = []
    created_tasks = []

    async def get_notify_channel():
        return overrides.get("notify_channel")

    async def send_embed(ch, title, fields, color, mention=None):
        sent.append((ch, title, fields, color, mention))

    async def ensure_sql_headroom_or_notify(ch):
        return overrides.get("sql_ok", True)

    async def offload_callable(func, *args, **kwargs):
        offloads.append((func, args, kwargs))
        if "offload_exception" in overrides:
            raise overrides["offload_exception"]
        return overrides.get("offload_result", _success_result())

    async def trigger_log_backup_background():
        return None

    def create_task(coro):
        created_tasks.append(coro)
        coro.close()
        return None

    deps = route.MgeResultsRouteDeps(
        mge_data_channel_id=10,
        get_notify_channel=overrides.get("get_notify_channel", get_notify_channel),
        send_embed=send_embed,
        ensure_sql_headroom_or_notify=ensure_sql_headroom_or_notify,
        offload_callable=offload_callable,
        trigger_log_backup_background=trigger_log_backup_background,
        create_task=create_task,
    )
    return deps, sent, offloads, created_tasks


@pytest.mark.asyncio
async def test_mge_results_route_ignores_other_channels():
    deps, sent, offloads, _created = _deps()

    handled = await route.handle_mge_results_upload(_message(channel_id=99), deps)

    assert handled is False
    assert sent == []
    assert offloads == []


@pytest.mark.asyncio
async def test_mge_results_route_ignores_empty_attachments():
    deps, sent, offloads, _created = _deps()

    handled = await route.handle_mge_results_upload(_message(attachments=[]), deps)

    assert handled is False
    assert sent == []
    assert offloads == []


@pytest.mark.asyncio
async def test_mge_results_route_no_xlsx_warns_and_handles():
    deps, sent, offloads, _created = _deps()

    handled = await route.handle_mge_results_upload(
        _message(attachments=[_FakeAttachment("notes.txt")]), deps
    )

    assert handled is True
    assert offloads == []
    _ch, title, fields, color, mention = sent[-1]
    assert title == "MGE Results Import \u26a0\ufe0f"
    assert fields["Info"] == "No .xlsx file found."
    assert fields["Expected"] == "mge_rankings_kd####_YYYYMMDD.xlsx"
    assert fields["Channel"] == "#mge-data (10)"
    assert fields["Uploader"] == "uploader (123456789)"
    assert color == 0xE67E22
    assert mention is None


@pytest.mark.asyncio
async def test_mge_results_route_sql_preflight_abort_skips_import():
    deps, sent, offloads, _created = _deps(sql_ok=False)

    handled = await route.handle_mge_results_upload(_message(), deps)

    assert handled is True
    assert sent == []
    assert offloads == []


@pytest.mark.asyncio
async def test_mge_results_route_success_preserves_import_contract_and_side_effects():
    deps, sent, offloads, created = _deps()

    handled = await route.handle_mge_results_upload(_message(), deps)

    assert handled is True
    assert len(offloads) == 1
    func, args, kwargs = offloads[0]
    assert func is route.import_results_auto
    assert args == (b"xlsx", "mge_rankings_kd1198_20260311.xlsx", 123456789)
    assert kwargs["name"] == "import_results_auto"
    assert kwargs["prefer_process"] is True
    assert kwargs["meta"] == {
        "filename": "mge_rankings_kd1198_20260311.xlsx",
        "channel_id": 10,
    }
    assert len(created) == 1
    _ch, title, fields, color, mention = sent[-1]
    assert title == "MGE Results Import \u2705"
    assert fields["EventId"] == "42"
    assert fields["Mode"] == "open"
    assert fields["Rows"] == "3"
    assert fields["ImportId"] == "77"
    assert fields["File"] == "mge_rankings_kd1198_20260311.xlsx"
    assert fields["Report"] == "Open Top-15 generated"
    assert color == 0x2ECC71
    assert mention is None


@pytest.mark.asyncio
async def test_mge_results_route_controlled_report_preserves_summary_fields():
    deps, sent, _offloads, _created = _deps(
        offload_result=_success_result(
            event_mode="fixed",
            report={
                "type": "controlled_awarded_vs_actual",
                "awarded_total": 7,
                "matched_actual_total": 5,
            },
        )
    )

    handled = await route.handle_mge_results_upload(_message(), deps)

    assert handled is True
    _ch, _title, fields, _color, _mention = sent[-1]
    assert fields["Awarded"] == "7"
    assert fields["Matched"] == "5"


@pytest.mark.asyncio
async def test_mge_results_route_importer_exception_sends_existing_error():
    deps, sent, _offloads, created = _deps(offload_exception=RuntimeError("boom"))

    handled = await route.handle_mge_results_upload(_message(), deps)

    assert handled is True
    assert created == []
    _ch, title, fields, color, mention = sent[-1]
    assert title == "MGE Results Import \u274c"
    assert fields["Error"] == "RuntimeError: boom"
    assert fields["File"] == "mge_rankings_kd1198_20260311.xlsx"
    assert fields["Channel"] == "#mge-data (10)"
    assert fields["Uploader"] == "uploader (123456789)"
    assert color == 0xE74C3C
    assert mention is None
