from __future__ import annotations

from datetime import UTC, datetime

import pytest

from upload_routes import kvk_all_route as route


class _FakeAttachment:
    def __init__(self, filename: str, payload: bytes = b"xlsx", size: int = 4):
        self.filename = filename
        self._payload = payload
        self.size = size

    async def read(self) -> bytes:
        return self._payload


class _FakeEmbed:
    def __init__(self, *, title: str, color: int):
        self.title = title
        self.color = color
        self.fields: list[tuple[str, str, bool]] = []
        self.thumbnail_url: str | None = None

    def add_field(self, *, name: str, value: str, inline: bool) -> None:
        self.fields.append((name, value, inline))

    def set_thumbnail(self, *, url: str) -> None:
        self.thumbnail_url = url

    def field_dict(self) -> dict[str, str]:
        return {name: value for name, value, _inline in self.fields}


class _FakeButton:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class _FakeView:
    def __init__(self):
        self.items = []

    def add_item(self, item) -> None:
        self.items.append(item)


class _FakeChannel:
    def __init__(self, channel_id: int, name: str = "prokingdom"):
        self.id = channel_id
        self.name = name
        self.sent = []

    async def send(self, **kwargs) -> None:
        self.sent.append(kwargs)


class _FailingSendChannel(_FakeChannel):
    async def send(self, **kwargs) -> None:
        raise RuntimeError("discord send failed")


class _FakeAuthor:
    id = 123456789

    def __str__(self) -> str:
        return "uploader"


class _FakeBot:
    loop = object()


class _FakeMessage:
    def __init__(self, channel_id: int = 10, attachments=None):
        self.channel = _FakeChannel(channel_id)
        self.author = _FakeAuthor()
        self.attachments = (
            attachments if attachments is not None else [_FakeAttachment("kvk_all.xlsx")]
        )
        self.id = 987654321
        self.created_at = datetime(2026, 5, 24, 10, 30, tzinfo=UTC)


def _message(channel_id: int = 10, attachments=None) -> _FakeMessage:
    return _FakeMessage(channel_id, attachments)


def _success_result(**overrides):
    result = {
        "kvk_no": 13,
        "scan_id": 2,
        "row_count": 10,
        "negatives": 0,
        "duration_s": 1.25,
        "staged_rows": 10,
        "proc_ms": 250.0,
        "recompute_ms": 125.0,
        "sheet": "Full Data",
        "success": True,
    }
    result.update(overrides)
    return result


def _deps(**overrides):
    sent_embeds = []
    offloads = []
    created_tasks = []
    scheduled_exports = []
    audit_events = overrides.get("audit_events", [])
    notify_channel = overrides.get("notify_channel")

    async def get_notify_channel():
        return notify_channel

    async def send_embed(ch, title, fields, color, mention=None):
        sent_embeds.append((ch, title, fields, color, mention))

    sql_results = list(overrides.get("sql_results", [overrides.get("sql_ok", True)]))

    async def ensure_sql_headroom_or_notify(ch):
        if sql_results:
            return sql_results.pop(0)
        return True

    offload_results = list(overrides.get("offload_results", []))

    async def offload_callable(func, *args, **kwargs):
        offloads.append((func, args, kwargs))
        if "offload_exception" in overrides:
            raise overrides["offload_exception"]
        if offload_results:
            result = offload_results.pop(0)
            if isinstance(result, Exception):
                raise result
            return result
        return overrides.get("offload_result", _success_result())

    def auto_export_scheduler(kvk_no, notify_ch, bot_loop):
        scheduled_exports.append((kvk_no, notify_ch, bot_loop))

        async def _noop():
            return None

        return _noop()

    def create_task(coro):
        created_tasks.append(coro)
        coro.close()
        return None

    async def start_audit_batch(**kwargs):
        audit_events.append(("start", kwargs))
        return overrides.get("audit_ref", "audit-ref")

    async def record_audit_phase(batch_ref, **kwargs):
        audit_events.append(("phase", batch_ref, kwargs))

    async def complete_audit_batch(batch_ref, **kwargs):
        audit_events.append(("complete", batch_ref, kwargs))

    async def fail_audit_batch(batch_ref, **kwargs):
        audit_events.append(("fail", batch_ref, kwargs))

    deps = route.KvkAllRouteDeps(
        prokingdom_channel_id=10,
        bot=overrides.get("bot", _FakeBot()),
        get_notify_channel=overrides.get("get_notify_channel", get_notify_channel),
        send_embed=send_embed,
        ensure_sql_headroom_or_notify=ensure_sql_headroom_or_notify,
        offload_callable=offload_callable,
        auto_export_enabled=overrides.get("auto_export_enabled", False),
        auto_export_scheduler=overrides.get("auto_export_scheduler", auto_export_scheduler),
        create_task=create_task,
        get_sheet_id=overrides.get("get_sheet_id", lambda: None),
        embed_factory=_FakeEmbed,
        view_factory=_FakeView,
        button_factory=_FakeButton,
        button_style_link="link",
        custom_avatar_url=overrides.get("custom_avatar_url", ""),
        start_audit_batch=overrides.get("start_audit_batch", start_audit_batch),
        record_audit_phase=overrides.get("record_audit_phase", record_audit_phase),
        complete_audit_batch=overrides.get("complete_audit_batch", complete_audit_batch),
        fail_audit_batch=overrides.get("fail_audit_batch", fail_audit_batch),
    )
    return deps, sent_embeds, offloads, created_tasks, scheduled_exports


@pytest.mark.asyncio
async def test_kvk_all_route_ignores_other_channels():
    deps, sent, offloads, _created, _exports = _deps()

    handled = await route.handle_kvk_all_upload(_message(channel_id=99), deps)

    assert handled is False
    assert sent == []
    assert offloads == []


@pytest.mark.asyncio
async def test_kvk_all_route_ignores_empty_attachments():
    deps, sent, offloads, _created, _exports = _deps()

    handled = await route.handle_kvk_all_upload(_message(attachments=[]), deps)

    assert handled is False
    assert sent == []
    assert offloads == []


@pytest.mark.asyncio
async def test_kvk_all_route_no_matching_file_warns_and_handles():
    deps, sent, offloads, _created, _exports = _deps()

    handled = await route.handle_kvk_all_upload(
        _message(attachments=[_FakeAttachment("notes.txt")]), deps
    )

    assert handled is True
    assert offloads == []
    _ch, title, fields, color, mention = sent[-1]
    assert title == "KVK All-Kingdom Import \u26a0\ufe0f"
    assert fields["Info"] == "No .xlsx/.xls/.csv attachment found."
    assert color == 0xE67E22
    assert mention is None


@pytest.mark.asyncio
@pytest.mark.parametrize("filename", ["kvk.xlsx", "kvk.xls", "kvk.csv"])
async def test_kvk_all_route_accepts_existing_extensions(filename: str):
    deps, _sent, offloads, _created, _exports = _deps()

    handled = await route.handle_kvk_all_upload(
        _message(attachments=[_FakeAttachment(filename, b"payload")]), deps
    )

    assert handled is True
    assert len(offloads) == 1
    func, _args, kwargs = offloads[0]
    assert func is route.ingest_kvk_all_excel
    assert kwargs["content"] == b"payload"
    assert kwargs["source_filename"] == filename
    assert kwargs["name"] == "ingest_kvk_all_excel"
    assert kwargs["prefer_process"] is True
    assert kwargs["meta"] == {"filename": filename}


@pytest.mark.asyncio
async def test_kvk_all_route_sql_preflight_abort_skips_only_current_attachment():
    audit_events = []
    deps, sent, offloads, _created, _exports = _deps(
        sql_results=[False, True],
        offload_result=_success_result(scan_id=3),
        audit_events=audit_events,
    )

    msg = _message(attachments=[_FakeAttachment("first.xlsx"), _FakeAttachment("second.xlsx")])

    handled = await route.handle_kvk_all_upload(msg, deps)

    assert handled is True
    assert len(offloads) == 1
    assert offloads[0][2]["source_filename"] == "second.xlsx"
    assert sent == []
    assert msg.channel.sent[0]["embed"].field_dict()["ScanID"] == "3"
    fail_events = [event for event in audit_events if event[0] == "fail"]
    assert fail_events[0][2]["error_type"] == "SqlHeadroomInsufficient"
    complete_events = [event for event in audit_events if event[0] == "complete"]
    assert complete_events[-1][2]["external_batch_id"] == "13:3"


@pytest.mark.asyncio
async def test_kvk_all_route_structured_failure_sends_existing_error_and_continues():
    audit_events = []
    deps, sent, offloads, _created, _exports = _deps(
        offload_results=[
            {
                "success": False,
                "error": "missing Full Data",
                "sheet": "Basic Data",
                "validation_error": {"code": "missing_full_data_sheet"},
            },
            _success_result(scan_id=4),
        ],
        audit_events=audit_events,
    )
    msg = _message(attachments=[_FakeAttachment("bad.xlsx"), _FakeAttachment("good.xlsx")])

    handled = await route.handle_kvk_all_upload(msg, deps)

    assert handled is True
    assert len(offloads) == 2
    _ch, title, fields, color, _mention = sent[-1]
    assert title == "KVK All-Kingdom Import \u274c"
    assert fields["Filename"] == "bad.xlsx"
    assert fields["Error"] == "missing Full Data"
    assert fields["Sheet"] == "Basic Data"
    assert color == 0xE74C3C
    assert len(msg.channel.sent) == 1
    assert msg.channel.sent[0]["embed"].field_dict()["ScanID"] == "4"
    fail_events = [event for event in audit_events if event[0] == "fail"]
    assert fail_events[0][2]["error_type"] == "missing_full_data_sheet"
    assert fail_events[0][2]["external_batch_id"] is None
    assert [event[0] for event in audit_events].count("complete") == 1


@pytest.mark.asyncio
async def test_kvk_all_route_structured_failure_preserves_zero_staged_rows():
    audit_events = []
    deps, sent, _offloads, _created, _exports = _deps(
        offload_result={
            "success": False,
            "error": "No rows found in uploaded file.",
            "sheet": "Full Data",
            "schema_version": "kvk_all_full_data_v2",
            "staged_rows": 0,
            "row_count": 7,
            "validation_error": {"code": "no_rows_found"},
        },
        audit_events=audit_events,
    )

    handled = await route.handle_kvk_all_upload(_message(), deps)

    assert handled is True
    _ch, title, fields, _color, _mention = sent[-1]
    assert title == "KVK All-Kingdom Import \u274c"
    assert fields["Error"] == "No rows found in uploaded file."
    fail_events = [event for event in audit_events if event[0] == "fail"]
    assert fail_events[-1][2]["rows_in_source"] == 0
    assert fail_events[-1][2]["rows_staged"] == 0
    assert fail_events[-1][2]["rows_skipped"] == 0


@pytest.mark.asyncio
async def test_kvk_all_route_success_without_negatives_preserves_embed_and_link_button():
    audit_events = []
    deps, _sent, offloads, created, exports = _deps(
        auto_export_enabled=True,
        custom_avatar_url="https://example.invalid/avatar.png",
        get_sheet_id=lambda: "sheet123",
        offload_result=_success_result(),
        audit_events=audit_events,
    )
    msg = _message()

    handled = await route.handle_kvk_all_upload(msg, deps)

    assert handled is True
    assert len(offloads) == 1
    assert len(msg.channel.sent) == 1
    payload = msg.channel.sent[0]
    embed = payload["embed"]
    assert embed.title == "KVK All-Kingdom Import \u2705"
    assert embed.color == 0x2ECC71
    assert embed.thumbnail_url == "https://example.invalid/avatar.png"
    fields = embed.field_dict()
    assert fields["KVK"] == "13"
    assert fields["ScanID"] == "2"
    assert fields["Rows"] == "10"
    assert fields["Staged"] == "10"
    assert fields["Negative Corrections"] == "0"
    assert fields["Duration"] == "1.25s"
    assert fields["Health"] == "proc `250ms` \u2022 I/O `1000ms` \u2022 recompute `125ms`"
    assert fields["File"] == "kvk_all.xlsx"
    assert fields["Sheet"] == "Full Data"
    view = payload["view"]
    assert view.items[0].kwargs["label"] == "\U0001f4c4 Open KVK_ALLPLAYER_OUTPUT"
    assert view.items[0].kwargs["url"] == "https://docs.google.com/spreadsheets/d/sheet123"
    assert len(created) == 1
    assert exports == [(13, msg.channel, deps.bot.loop)]
    phase_names = [event[2]["phase_name"] for event in audit_events if event[0] == "phase"]
    assert route.KVK_ALL_AUDIT_PARSE_PHASE in phase_names
    assert route.KVK_ALL_AUDIT_STAGE_PHASE in phase_names
    assert route.KVK_ALL_AUDIT_INGEST_PHASE in phase_names
    assert route.KVK_ALL_AUDIT_RECOMPUTE_PHASE in phase_names
    assert route.KVK_ALL_AUDIT_NEGATIVE_PHASE in phase_names
    assert route.KVK_ALL_AUDIT_AUTO_EXPORT_PHASE in phase_names
    complete_events = [event for event in audit_events if event[0] == "complete"]
    assert complete_events[-1][2]["external_batch_id"] == "13:2"
    assert complete_events[-1][2]["rows_in_source"] == 10
    assert complete_events[-1][2]["rows_written"] == 10


@pytest.mark.asyncio
async def test_kvk_all_route_kvk_details_rejection_correlates_diagnostic_id():
    audit_events = []
    deps, sent, _offloads, _created, _exports = _deps(
        offload_result={
            "success": False,
            "error": "Scan timestamp outside KVK_Details ranges.",
            "sheet": "Full Data",
            "schema_version": "kvk_all_full_data_v2",
            "diagnostic_id": 42,
            "staged_rows": 7,
            "prepare_ms": 3.0,
            "stage_insert_ms": 4.0,
            "precheck_ms": 5.0,
        },
        audit_events=audit_events,
    )

    handled = await route.handle_kvk_all_upload(_message(), deps)

    assert handled is True
    _ch, title, fields, _color, _mention = sent[-1]
    assert title == "KVK All-Kingdom Import \u274c"
    assert fields["Error"] == "Scan timestamp outside KVK_Details ranges."
    fail_events = [event for event in audit_events if event[0] == "fail"]
    assert fail_events[-1][2]["error_type"] == "KvkDetailsTimestampRejected"
    assert fail_events[-1][2]["external_batch_table"] == route.KVK_ALL_AUDIT_DIAGNOSTIC_TABLE
    assert fail_events[-1][2]["external_batch_id"] == "42"
    assert fail_events[-1][2]["rows_staged"] == 7


@pytest.mark.asyncio
async def test_kvk_all_route_exception_diagnostic_id_records_kvk_details_rejection():
    audit_events = []
    exc = RuntimeError("Scan timestamp outside KVK_Details ranges.")
    exc.kvk_diagnostic_id = 42
    exc.kvk_staged_rows = 7
    deps, sent, _offloads, _created, _exports = _deps(
        offload_results=[exc],
        audit_events=audit_events,
    )

    handled = await route.handle_kvk_all_upload(_message(), deps)

    assert handled is True
    _ch, title, fields, _color, _mention = sent[-1]
    assert title == "KVK All-Kingdom Import \u274c"
    assert fields["Error"] == "RuntimeError: Scan timestamp outside KVK_Details ranges."
    fail_events = [event for event in audit_events if event[0] == "fail"]
    assert fail_events[-1][2]["error_type"] == "KvkDetailsTimestampRejected"
    assert fail_events[-1][2]["external_batch_table"] == route.KVK_ALL_AUDIT_DIAGNOSTIC_TABLE
    assert fail_events[-1][2]["external_batch_id"] == "42"
    assert fail_events[-1][2]["rows_staged"] == 7


@pytest.mark.asyncio
async def test_kvk_all_route_success_with_negative_corrections_uses_warning_embed():
    deps, _sent, _offloads, _created, _exports = _deps(
        offload_result=_success_result(negatives=2, recompute_ms=0.0)
    )
    msg = _message()

    handled = await route.handle_kvk_all_upload(msg, deps)

    assert handled is True
    embed = msg.channel.sent[0]["embed"]
    fields = embed.field_dict()
    assert embed.title == "KVK All-Kingdom Import \u26a0\ufe0f"
    assert embed.color == 0xE67E22
    assert fields["Negative Corrections"] == "2 \u26a0\ufe0f"
    assert fields["Health"] == "proc `250ms` \u2022 I/O `1000ms`"


@pytest.mark.asyncio
async def test_kvk_all_route_link_button_is_best_effort():
    def broken_sheet_id():
        raise RuntimeError("bad sheet config")

    deps, _sent, _offloads, _created, _exports = _deps(get_sheet_id=broken_sheet_id)
    msg = _message()

    handled = await route.handle_kvk_all_upload(msg, deps)

    assert handled is True
    assert msg.channel.sent[0]["embed"].field_dict()["KVK"] == "13"
    assert msg.channel.sent[0]["view"] is None


@pytest.mark.asyncio
async def test_kvk_all_route_unexpected_exception_renders_error_and_continues():
    audit_events = []
    deps, sent, offloads, _created, _exports = _deps(
        offload_results=[RuntimeError("boom"), _success_result(scan_id=5)],
        audit_events=audit_events,
    )
    msg = _message(attachments=[_FakeAttachment("bad.xlsx"), _FakeAttachment("good.xlsx")])

    handled = await route.handle_kvk_all_upload(msg, deps)

    assert handled is True
    assert len(offloads) == 2
    _ch, title, fields, color, _mention = sent[-1]
    assert title == "KVK All-Kingdom Import \u274c"
    assert fields["Error"] == "RuntimeError: boom"
    assert fields["File"] == "bad.xlsx"
    assert color == 0xE74C3C
    assert msg.channel.sent[0]["embed"].field_dict()["ScanID"] == "5"
    fail_events = [event for event in audit_events if event[0] == "fail"]
    assert fail_events[0][2]["error_type"] == "RuntimeError"
    complete_events = [event for event in audit_events if event[0] == "complete"]
    assert complete_events[-1][2]["external_batch_id"] == "13:5"


@pytest.mark.asyncio
async def test_kvk_all_route_post_ingest_send_failure_completes_import_audit():
    audit_events = []
    deps, sent, _offloads, _created, _exports = _deps(
        offload_result=_success_result(scan_id=6),
        audit_events=audit_events,
    )
    msg = _message()
    msg.channel = _FailingSendChannel(10)

    handled = await route.handle_kvk_all_upload(msg, deps)

    assert handled is True
    _ch, title, fields, _color, _mention = sent[-1]
    assert title == "KVK All-Kingdom Import \u274c"
    assert fields["Error"] == "RuntimeError: discord send failed"
    assert [event for event in audit_events if event[0] == "fail"] == []
    complete_events = [event for event in audit_events if event[0] == "complete"]
    assert complete_events[-1][2]["external_batch_id"] == "13:6"
    assert complete_events[-1][2]["rows_written"] == 10
