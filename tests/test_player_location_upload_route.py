from __future__ import annotations

import pytest

from upload_routes import player_location_route as route


@pytest.fixture(autouse=True)
def _disable_location_audit(monkeypatch):
    async def _start(**_kwargs):
        return 123

    async def _record(_batch_ref, **_kwargs):
        return None

    async def _complete(_batch_ref, **_kwargs):
        return None

    async def _fail(_batch_ref, **_kwargs):
        return None

    monkeypatch.setattr(route, "start_location_audit_batch", _start)
    monkeypatch.setattr(route, "record_location_audit_phase", _record)
    monkeypatch.setattr(route, "complete_location_audit_batch", _complete)
    monkeypatch.setattr(route, "fail_location_audit_batch", _fail)


class _FakeAttachment:
    def __init__(self, filename: str, payload: bytes = b"csv"):
        self.filename = filename
        self._payload = payload

    async def read(self) -> bytes:
        return self._payload


class _FakeChannel:
    def __init__(self, channel_id: int, name: str = "location-upload"):
        self.id = channel_id
        self.name = name


class _FakeAuthor:
    id = 123

    def __str__(self) -> str:
        return "uploader"


class _FakeMessage:
    def __init__(self, channel_id: int, attachments):
        self.id = 555
        self.channel = _FakeChannel(channel_id)
        self.author = _FakeAuthor()
        self.attachments = attachments


def _message(channel_id: int = 10, attachments=None) -> _FakeMessage:
    if attachments is None:
        attachments = [_FakeAttachment("scan_1198.csv")]
    return _FakeMessage(channel_id, attachments)


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
        if "offload_result" in overrides:
            return overrides["offload_result"]
        return 3, 10

    async def trigger_log_backup_background():
        return None

    def create_task(coro):
        created_tasks.append(coro)
        coro.close()
        return None

    deps = route.PlayerLocationRouteDeps(
        player_location_channel_id=10,
        get_notify_channel=overrides.get("get_notify_channel", get_notify_channel),
        send_embed=send_embed,
        ensure_sql_headroom_or_notify=ensure_sql_headroom_or_notify,
        offload_callable=offload_callable,
        trigger_log_backup_background=trigger_log_backup_background,
        create_task=create_task,
        warm_profile_cache=overrides.get("warm_profile_cache", lambda: None),
    )
    return deps, sent, offloads, created_tasks


@pytest.mark.asyncio
async def test_player_location_route_ignores_other_channels():
    deps, sent, offloads, _created = _deps()

    handled = await route.handle_player_location_upload(_message(channel_id=99), deps)

    assert handled is False
    assert sent == []
    assert offloads == []


@pytest.mark.asyncio
async def test_player_location_route_ignores_other_filenames():
    deps, sent, offloads, _created = _deps()
    msg = _message(attachments=[_FakeAttachment("output.csv")])

    handled = await route.handle_player_location_upload(msg, deps)

    assert handled is False
    assert sent == []
    assert offloads == []


@pytest.mark.asyncio
async def test_player_location_route_ignores_empty_attachments():
    deps, sent, offloads, _created = _deps()

    handled = await route.handle_player_location_upload(_message(attachments=[]), deps)

    assert handled is False
    assert sent == []
    assert offloads == []


@pytest.mark.asyncio
async def test_player_location_route_empty_rows_sends_existing_warning(monkeypatch):
    monkeypatch.setattr(route, "parse_output_csv", lambda _bytes: [])
    deps, sent, offloads, _created = _deps()

    handled = await route.handle_player_location_upload(_message(), deps)

    assert handled is True
    assert offloads == []
    _ch, title, fields, color, mention = sent[-1]
    assert title == "Player Location Import"
    assert fields["Status"] == "No valid rows found in CSV."
    assert color == 0xE74C3C
    assert mention is None


@pytest.mark.asyncio
async def test_player_location_route_sql_preflight_abort_skips_offload(monkeypatch):
    monkeypatch.setattr(
        route, "parse_output_csv", lambda _bytes: [(1, "A", 0, 0, 1, "TAG", 10, 20)]
    )
    deps, sent, offloads, _created = _deps(sql_ok=False)

    handled = await route.handle_player_location_upload(_message(), deps)

    assert handled is True
    assert sent == []
    assert offloads == []


@pytest.mark.asyncio
async def test_player_location_route_success_preserves_outputs_and_side_effects(monkeypatch):
    rows = [(1, "A", 0, 0, 1, "TAG", 10, 20)]
    warmed = []
    signalled = []
    monkeypatch.setattr(route, "parse_output_csv", lambda _bytes: rows)
    monkeypatch.setattr(route, "signal_location_refresh_complete", lambda: signalled.append(True))
    deps, sent, offloads, created = _deps(warm_profile_cache=lambda: warmed.append(True))

    handled = await route.handle_player_location_upload(_message(), deps)

    assert handled is True
    assert len(offloads) == 1
    func, args, kwargs = offloads[0]
    assert func is route.load_staging_and_replace
    assert args == (rows,)
    assert kwargs["name"] == "load_staging_and_replace"
    assert kwargs["prefer_process"] is True
    assert warmed == [True]
    assert signalled == [True]
    assert len(created) == 1
    _ch, title, fields, color, mention = sent[-1]
    assert title == "Player Location Import ✅"
    assert fields["Imported Rows"] == "3"
    assert fields["Total Tracked"] == "10"
    assert fields["Uploaded By"] == "uploader (123)"
    assert color == 0x2ECC71
    assert mention is None


@pytest.mark.asyncio
async def test_player_location_route_records_replace_audit(monkeypatch):
    rows = [(1, "A", 0, 0, 1, "TAG", 10, 20)]
    audit_calls = []

    async def _start(**kwargs):
        audit_calls.append(("start", kwargs))
        return 987

    async def _record(batch_ref, **kwargs):
        audit_calls.append(("phase", batch_ref, kwargs))

    async def _complete(batch_ref, **kwargs):
        audit_calls.append(("complete", batch_ref, kwargs))

    monkeypatch.setattr(route, "parse_output_csv", lambda _bytes: rows)
    monkeypatch.setattr(route, "signal_location_refresh_complete", lambda: None)
    monkeypatch.setattr(route, "start_location_audit_batch", _start)
    monkeypatch.setattr(route, "record_location_audit_phase", _record)
    monkeypatch.setattr(route, "complete_location_audit_batch", _complete)
    deps, _sent, _offloads, _created = _deps()

    handled = await route.handle_player_location_upload(_message(), deps)

    assert handled is True
    assert audit_calls[0][0] == "start"
    context = audit_calls[0][1]["context"]
    assert context.entry_point == "location_auto_upload"
    assert context.sql_operation == "replace"
    assert context.source_filename == "scan_1198.csv"
    assert context.source_message_id == 555
    phase_names = [call[2]["phase_name"] for call in audit_calls if call[0] == "phase"]
    assert phase_names == [
        "location_csv_parse",
        "location_sql_replace",
        "location_post_import_refresh",
    ]
    assert audit_calls[-1][0] == "complete"
    assert audit_calls[-1][2]["rows_staged"] == 3
    assert audit_calls[-1][2]["rows_written"] == 3


@pytest.mark.asyncio
async def test_player_location_route_sends_to_resolved_notify_channel(monkeypatch):
    monkeypatch.setattr(
        route, "parse_output_csv", lambda _bytes: [(1, "A", 0, 0, 1, "TAG", 10, 20)]
    )
    notify_channel = _FakeChannel(20, "notify")
    deps, sent, _offloads, _created = _deps(notify_channel=notify_channel)

    handled = await route.handle_player_location_upload(_message(), deps)

    assert handled is True
    ch, _title, _fields, _color, _mention = sent[-1]
    assert ch is notify_channel


@pytest.mark.asyncio
async def test_player_location_route_falls_back_when_notify_resolution_fails(monkeypatch):
    monkeypatch.setattr(
        route, "parse_output_csv", lambda _bytes: [(1, "A", 0, 0, 1, "TAG", 10, 20)]
    )

    async def get_notify_channel():
        raise RuntimeError("notify unavailable")

    deps, sent, _offloads, _created = _deps(get_notify_channel=get_notify_channel)
    msg = _message()

    handled = await route.handle_player_location_upload(msg, deps)

    assert handled is True
    ch, _title, _fields, _color, _mention = sent[-1]
    assert ch is msg.channel


@pytest.mark.asyncio
async def test_player_location_route_importer_exception_sends_error(monkeypatch):
    monkeypatch.setattr(
        route, "parse_output_csv", lambda _bytes: [(1, "A", 0, 0, 1, "TAG", 10, 20)]
    )

    async def offload_raises(*_args, **_kwargs):
        raise RuntimeError("boom")

    deps, sent, _offloads, _created = _deps()
    deps = route.PlayerLocationRouteDeps(
        player_location_channel_id=deps.player_location_channel_id,
        get_notify_channel=deps.get_notify_channel,
        send_embed=deps.send_embed,
        ensure_sql_headroom_or_notify=deps.ensure_sql_headroom_or_notify,
        offload_callable=offload_raises,
        trigger_log_backup_background=deps.trigger_log_backup_background,
        create_task=deps.create_task,
        warm_profile_cache=deps.warm_profile_cache,
    )

    handled = await route.handle_player_location_upload(_message(), deps)

    assert handled is True
    _ch, title, fields, color, mention = sent[-1]
    assert title == "Player Location Import ❌"
    assert fields["Error"] == "RuntimeError: boom"
    assert color == 0xE74C3C
    assert mention is None
