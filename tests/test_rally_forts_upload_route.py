from __future__ import annotations

import os

import pytest

from upload_routes import rally_forts_route as route


class _FakeAttachment:
    def __init__(
        self,
        filename: str,
        payload: bytes = b"xlsx",
        *,
        save_exception: Exception | None = None,
    ):
        self.filename = filename
        self.payload = payload
        self.save_exception = save_exception
        self.saved_paths: list[str] = []

    async def save(self, path: str) -> None:
        self.saved_paths.append(path)
        if self.save_exception is not None:
            raise self.save_exception


class _FakeChannel:
    def __init__(self, channel_id: int, name: str = "rally"):
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
            else [_FakeAttachment("Rally_data_26-05-2026.xlsx")]
        )


def _message(channel_id: int = 10, attachments=None) -> _FakeMessage:
    return _FakeMessage(channel_id, attachments)


def _fake_daily_importer(*_args, **_kwargs):
    raise AssertionError("offload test double should not call daily importer directly")


def _fake_alltime_importer(*_args, **_kwargs):
    raise AssertionError("offload test double should not call all-time importer directly")


def _deps(tmp_path, **overrides):
    sent = []
    offloads = []
    created_tasks = []
    preflight_channels = []
    audit_calls = overrides.get("audit_calls", [])

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
        return overrides.get("offload_result", {"status": "success", "rows": 7})

    async def trigger_log_backup_background():
        return None

    def create_task(coro):
        if "create_task_exception" in overrides:
            raise overrides["create_task_exception"]
        created_tasks.append(coro)
        coro.close()
        return None

    def importer_loader():
        if "importer_exception" in overrides:
            raise overrides["importer_exception"]
        return (
            overrides.get("alltime_importer", _fake_alltime_importer),
            overrides.get("daily_importer", _fake_daily_importer),
        )

    async def start_audit_batch(**kwargs):
        audit_calls.append(("start", kwargs))
        return overrides.get("audit_ref", "audit-ref")

    async def record_audit_phase(batch_ref, **kwargs):
        audit_calls.append(("phase", batch_ref, kwargs))

    async def complete_audit_batch(batch_ref, **kwargs):
        audit_calls.append(("complete", batch_ref, kwargs))

    async def fail_audit_batch(batch_ref, **kwargs):
        audit_calls.append(("fail", batch_ref, kwargs))

    deps = route.RallyFortsRouteDeps(
        fort_rally_channel_id=overrides.get("fort_rally_channel_id", 10),
        log_dir=str(tmp_path),
        get_notify_channel=overrides.get("get_notify_channel", get_notify_channel),
        send_embed=send_embed,
        ensure_sql_headroom_or_notify=ensure_sql_headroom_or_notify,
        offload_callable=offload_callable,
        trigger_log_backup_background=trigger_log_backup_background,
        create_task=create_task,
        importer_loader=overrides.get("importer_loader", importer_loader),
        start_audit_batch=overrides.get("start_audit_batch", start_audit_batch),
        record_audit_phase=overrides.get("record_audit_phase", record_audit_phase),
        complete_audit_batch=overrides.get("complete_audit_batch", complete_audit_batch),
        fail_audit_batch=overrides.get("fail_audit_batch", fail_audit_batch),
    )
    return deps, sent, offloads, created_tasks, preflight_channels


def test_rally_filename_matching_preserves_patterns():
    assert route.is_rally_daily("Rally_data_26-05-2026.xlsx")
    assert route.is_rally_daily("rally_data_26-05-2026.xlsx")
    assert not route.is_rally_daily("Rally_data_All_Time.xlsx")

    assert route.is_rally_alltime("Rally_data_All_Time.xlsx")
    assert route.is_rally_alltime("Rally data all time May.xlsx")
    assert route.is_rally_alltime("rally_data_anything_all_time_report.xlsx")
    assert not route.is_rally_alltime("Rally_data_26-05-2026.xlsx")


@pytest.mark.asyncio
async def test_rally_route_ignores_other_channels(tmp_path):
    deps, sent, offloads, _created, _preflight = _deps(tmp_path)

    handled = await route.handle_rally_forts_upload(_message(channel_id=99), deps)

    assert handled is False
    assert sent == []
    assert offloads == []


@pytest.mark.asyncio
async def test_rally_route_ignores_empty_attachments(tmp_path):
    deps, sent, offloads, _created, _preflight = _deps(tmp_path)

    handled = await route.handle_rally_forts_upload(_message(attachments=[]), deps)

    assert handled is False
    assert sent == []
    assert offloads == []


@pytest.mark.asyncio
async def test_rally_route_no_xlsx_warns_and_handles(tmp_path):
    deps, sent, offloads, _created, _preflight = _deps(tmp_path)

    handled = await route.handle_rally_forts_upload(
        _message(attachments=[_FakeAttachment("notes.txt")]), deps
    )

    assert handled is True
    assert offloads == []
    _ch, title, fields, color, mention = sent[-1]
    assert title == "Rally Forts Import \u26a0\ufe0f"
    assert fields == {
        "Info": "No rally .xlsx attachments matched expected patterns.",
        "Expected Daily": "Rally_data_DD-MM-YYYY.xlsx",
        "Expected All-Time": "Rally_data_All_Time*.xlsx",
    }
    assert color == 0xE67E22
    assert mention is None


@pytest.mark.asyncio
async def test_rally_route_importer_load_failure_sends_existing_error(tmp_path):
    deps, sent, offloads, _created, _preflight = _deps(
        tmp_path, importer_exception=RuntimeError("missing dep")
    )

    handled = await route.handle_rally_forts_upload(_message(), deps)

    assert handled is True
    assert offloads == []
    _ch, title, fields, color, _mention = sent[-1]
    assert title == "Rally Forts Import \u274c"
    assert fields["Error"] == "Import failure: RuntimeError: missing dep"
    assert "forts_ingest.py" in fields["Hint"]
    assert color == 0xE74C3C


@pytest.mark.asyncio
async def test_rally_daily_success_preserves_save_offload_and_embed_contract(tmp_path):
    attachment = _FakeAttachment("Rally_data_26-05-2026.xlsx")
    deps, sent, offloads, created, preflight = _deps(
        tmp_path,
        offload_result={"status": "success", "rows": 7, "as_of": "2026-05-26"},
    )
    message = _message(attachments=[attachment])

    handled = await route.handle_rally_forts_upload(message, deps)

    assert handled is True
    expected_path = os.path.join(str(tmp_path), "downloads", "Rally_data_26-05-2026.xlsx")
    assert attachment.saved_paths == [expected_path]
    assert preflight == [message.channel]
    assert len(offloads) == 1
    func, args, kwargs = offloads[0]
    assert func is _fake_daily_importer
    assert args == (expected_path,)
    assert kwargs == {
        "name": "import_rally_daily_xlsx",
        "prefer_process": True,
        "meta": {"path": expected_path},
    }
    assert len(created) == 1
    _ch, title, fields, color, mention = sent[-1]
    assert title == "Rally Forts Import \u2705"
    assert fields == {
        "Source Channel": "#rally (10)",
        "Uploaded By": "uploader (123456789)",
        "\u2705 Rally_data_26-05-2026.xlsx": "rows=7; as_of=2026-05-26",
    }
    assert color == 0x2ECC71
    assert mention is None


@pytest.mark.asyncio
async def test_rally_daily_success_records_completed_audit_with_ingestion_correlation(tmp_path):
    audit_calls = []
    deps, _sent, _offloads, _created, _preflight = _deps(
        tmp_path,
        audit_calls=audit_calls,
        offload_result={
            "status": "success",
            "rows": 7,
            "as_of": "2026-05-26",
            "ingestion_id": 42,
        },
    )

    handled = await route.handle_rally_forts_upload(
        _message(attachments=[_FakeAttachment("Rally_data_26-05-2026.xlsx")]),
        deps,
    )

    assert handled is True
    assert audit_calls[0][0] == "start"
    start_kwargs = audit_calls[0][1]
    assert start_kwargs["context"].source_filename == "Rally_data_26-05-2026.xlsx"
    assert start_kwargs["local_path"] == os.path.join(
        str(tmp_path),
        "downloads",
        "Rally_data_26-05-2026.xlsx",
    )
    phase_names = [call[2]["phase_name"] for call in audit_calls if call[0] == "phase"]
    assert phase_names == [
        route.RALLY_FORTS_AUDIT_ATTACHMENT_SAVE_PHASE,
        route.RALLY_FORTS_AUDIT_FILE_CLASSIFY_PHASE,
        route.RALLY_FORTS_AUDIT_SQL_PREFLIGHT_PHASE,
        route.RALLY_FORTS_AUDIT_DAILY_INGEST_PHASE,
        route.RALLY_FORTS_AUDIT_BACKUP_PHASE,
    ]
    complete_call = [call for call in audit_calls if call[0] == "complete"][-1]
    assert complete_call[2]["status"] == "completed"
    assert complete_call[2]["rows_in_source"] == 7
    assert complete_call[2]["rows_staged"] == 7
    assert complete_call[2]["rows_written"] == 7
    assert complete_call[2]["rows_skipped"] == 0
    assert complete_call[2]["external_batch_id"] == "42"
    assert complete_call[2]["details"]["ingestion_id"] == 42
    assert complete_call[2]["details"]["as_of"] == "2026-05-26"


@pytest.mark.asyncio
async def test_rally_alltime_success_preserves_import_contract(tmp_path):
    deps, sent, offloads, created, _preflight = _deps(
        tmp_path, offload_result={"status": "success", "rows": 4}
    )

    handled = await route.handle_rally_forts_upload(
        _message(attachments=[_FakeAttachment("Rally_data_All_Time.xlsx")]), deps
    )

    assert handled is True
    assert len(offloads) == 1
    func, args, kwargs = offloads[0]
    expected_path = os.path.join(str(tmp_path), "downloads", "Rally_data_All_Time.xlsx")
    assert func is _fake_alltime_importer
    assert args == (expected_path,)
    assert kwargs["name"] == "import_rally_alltime_xlsx"
    assert kwargs["prefer_process"] is True
    assert kwargs["meta"] == {"path": expected_path}
    assert len(created) == 1
    assert sent[-1][1] == "Rally Forts Import \u2705"
    assert sent[-1][2]["\u2705 Rally_data_All_Time.xlsx"] == "rows=4"


@pytest.mark.asyncio
async def test_rally_duplicate_skip_records_skipped_audit_without_external_correlation(tmp_path):
    audit_calls = []
    deps, sent, _offloads, created, _preflight = _deps(
        tmp_path,
        audit_calls=audit_calls,
        offload_result={"status": "skipped", "reason": "duplicate filename"},
    )

    handled = await route.handle_rally_forts_upload(
        _message(attachments=[_FakeAttachment("Rally_data_All_Time.xlsx")]),
        deps,
    )

    assert handled is True
    assert len(created) == 1
    assert sent[-1][1] == "Rally Forts Import \u2705"
    ingest_phase = next(
        call
        for call in audit_calls
        if call[0] == "phase"
        and call[2]["phase_name"] == route.RALLY_FORTS_AUDIT_ALLTIME_INGEST_PHASE
    )
    assert ingest_phase[2]["phase_status"] == "skipped"
    complete_call = [call for call in audit_calls if call[0] == "complete"][-1]
    assert complete_call[2]["status"] == "skipped"
    assert complete_call[2]["external_batch_id"] is None
    assert complete_call[2]["rows_staged"] == 0
    assert complete_call[2]["rows_written"] == 0
    assert complete_call[2]["details"]["reason"] == "duplicate filename"


@pytest.mark.asyncio
async def test_rally_alltime_backup_schedule_failure_records_no_rows_out(tmp_path):
    audit_calls = []
    deps, sent, _offloads, created, _preflight = _deps(
        tmp_path,
        audit_calls=audit_calls,
        create_task_exception=RuntimeError("scheduler down"),
        offload_result={"status": "success", "rows": 4, "ingestion_id": 99},
    )

    handled = await route.handle_rally_forts_upload(
        _message(attachments=[_FakeAttachment("Rally_data_All_Time.xlsx")]),
        deps,
    )

    assert handled is True
    assert created == []
    assert sent[-1][1] == "Rally Forts Import \u2705"
    backup_phase = next(
        call
        for call in audit_calls
        if call[0] == "phase"
        and call[2]["phase_name"] == route.RALLY_FORTS_AUDIT_BACKUP_PHASE
    )
    assert backup_phase[2]["phase_status"] == "failed"
    assert backup_phase[2]["rows_in"] == 4
    assert backup_phase[2]["rows_out"] is None
    assert backup_phase[2]["error_type"] == "RuntimeError"


@pytest.mark.asyncio
async def test_rally_daily_backup_schedule_failure_records_no_rows_out(tmp_path):
    audit_calls = []
    deps, sent, _offloads, created, _preflight = _deps(
        tmp_path,
        audit_calls=audit_calls,
        create_task_exception=RuntimeError("scheduler down"),
        offload_result={
            "status": "success",
            "rows": 7,
            "as_of": "2026-05-26",
            "ingestion_id": 42,
        },
    )

    handled = await route.handle_rally_forts_upload(
        _message(attachments=[_FakeAttachment("Rally_data_26-05-2026.xlsx")]),
        deps,
    )

    assert handled is True
    assert created == []
    assert sent[-1][1] == "Rally Forts Import \u2705"
    backup_phase = next(
        call
        for call in audit_calls
        if call[0] == "phase"
        and call[2]["phase_name"] == route.RALLY_FORTS_AUDIT_BACKUP_PHASE
    )
    assert backup_phase[2]["phase_status"] == "failed"
    assert backup_phase[2]["rows_in"] == 7
    assert backup_phase[2]["rows_out"] is None
    assert backup_phase[2]["error_type"] == "RuntimeError"


@pytest.mark.asyncio
async def test_rally_sql_preflight_abort_happens_after_save_before_offload(tmp_path):
    attachment = _FakeAttachment("Rally_data_26-05-2026.xlsx")
    deps, sent, offloads, created, preflight = _deps(tmp_path, sql_ok=False)
    message = _message(attachments=[attachment])

    handled = await route.handle_rally_forts_upload(message, deps)

    assert handled is True
    assert attachment.saved_paths == [
        os.path.join(str(tmp_path), "downloads", "Rally_data_26-05-2026.xlsx")
    ]
    assert preflight == [message.channel]
    assert offloads == []
    assert created == []
    _ch, title, fields, color, _mention = sent[-1]
    assert title == "Rally Forts Import \u274c"
    assert fields["\u274c Rally_data_26-05-2026.xlsx"] == ("Aborted: SQL log headroom insufficient")
    assert color == 0xE74C3C


@pytest.mark.asyncio
async def test_rally_sql_preflight_abort_records_failed_uncorrelated_audit(tmp_path):
    audit_calls = []
    deps, _sent, offloads, created, _preflight = _deps(
        tmp_path,
        audit_calls=audit_calls,
        sql_ok=False,
    )

    handled = await route.handle_rally_forts_upload(_message(), deps)

    assert handled is True
    assert offloads == []
    assert created == []
    preflight_phase = next(
        call
        for call in audit_calls
        if call[0] == "phase"
        and call[2]["phase_name"] == route.RALLY_FORTS_AUDIT_SQL_PREFLIGHT_PHASE
    )
    assert preflight_phase[2]["phase_status"] == "failed"
    fail_call = [call for call in audit_calls if call[0] == "fail"][-1]
    assert fail_call[2]["error_type"] == "SqlHeadroomInsufficient"
    assert fail_call[2].get("external_batch_id") is None
    assert fail_call[2]["rows_written"] == 0


@pytest.mark.asyncio
async def test_rally_unrecognized_xlsx_is_saved_and_reported_as_skip(tmp_path):
    attachment = _FakeAttachment("rally_notes.xlsx")
    deps, sent, offloads, created, _preflight = _deps(tmp_path)

    handled = await route.handle_rally_forts_upload(_message(attachments=[attachment]), deps)

    assert handled is True
    assert attachment.saved_paths == [os.path.join(str(tmp_path), "downloads", "rally_notes.xlsx")]
    assert offloads == []
    assert created == []
    _ch, title, fields, color, _mention = sent[-1]
    assert title == "Rally Forts Import \u274c"
    assert fields["\u23ed\ufe0f rally_notes.xlsx"] == "Unrecognized rally filename"
    assert color == 0xE74C3C


@pytest.mark.asyncio
async def test_rally_unrecognized_xlsx_records_skipped_uncorrelated_audit(tmp_path):
    audit_calls = []
    deps, _sent, offloads, created, _preflight = _deps(tmp_path, audit_calls=audit_calls)

    handled = await route.handle_rally_forts_upload(
        _message(attachments=[_FakeAttachment("rally_notes.xlsx")]),
        deps,
    )

    assert handled is True
    assert offloads == []
    assert created == []
    complete_call = [call for call in audit_calls if call[0] == "complete"][-1]
    assert complete_call[2]["status"] == "skipped"
    assert complete_call[2].get("external_batch_id") is None
    assert complete_call[2]["details"]["reason"] == "Unrecognized rally filename"


@pytest.mark.asyncio
async def test_rally_per_attachment_exception_is_aggregated(tmp_path):
    deps, sent, offloads, created, _preflight = _deps(tmp_path)

    handled = await route.handle_rally_forts_upload(
        _message(
            attachments=[
                _FakeAttachment(
                    "Rally_data_26-05-2026.xlsx",
                    save_exception=RuntimeError("disk full"),
                )
            ]
        ),
        deps,
    )

    assert handled is True
    assert offloads == []
    assert created == []
    _ch, title, fields, color, _mention = sent[-1]
    assert title == "Rally Forts Import \u274c"
    assert fields["\u274c Rally_data_26-05-2026.xlsx"] == "RuntimeError: disk full"
    assert color == 0xE74C3C


@pytest.mark.asyncio
async def test_rally_offload_exception_records_failed_ingest_audit(tmp_path):
    audit_calls = []
    deps, _sent, offloads, created, _preflight = _deps(
        tmp_path,
        audit_calls=audit_calls,
        offload_exception=RuntimeError("import exploded"),
    )

    handled = await route.handle_rally_forts_upload(_message(), deps)

    assert handled is True
    assert len(offloads) == 1
    assert created == []
    ingest_phase = next(
        call
        for call in audit_calls
        if call[0] == "phase"
        and call[2]["phase_name"] == route.RALLY_FORTS_AUDIT_DAILY_INGEST_PHASE
    )
    assert ingest_phase[2]["phase_status"] == "failed"
    fail_call = [call for call in audit_calls if call[0] == "fail"][-1]
    assert fail_call[2]["error_type"] == "RuntimeError"
    assert fail_call[2].get("external_batch_id") is None


@pytest.mark.asyncio
async def test_rally_mixed_success_and_error_uses_warning_embed(tmp_path):
    deps, sent, offloads, created, _preflight = _deps(tmp_path)

    handled = await route.handle_rally_forts_upload(
        _message(
            attachments=[
                _FakeAttachment("Rally_data_26-05-2026.xlsx"),
                _FakeAttachment(
                    "Rally_data_27-05-2026.xlsx",
                    save_exception=RuntimeError("disk full"),
                ),
            ]
        ),
        deps,
    )

    assert handled is True
    assert len(offloads) == 1
    assert len(created) == 1
    _ch, title, fields, color, _mention = sent[-1]
    assert title == "Rally Forts Import \u26a0\ufe0f"
    assert "\u2705 Rally_data_26-05-2026.xlsx" in fields
    assert fields["\u274c Rally_data_27-05-2026.xlsx"] == "RuntimeError: disk full"
    assert color == 0xE67E22


@pytest.mark.asyncio
async def test_rally_final_embed_failure_is_swallowed(tmp_path):
    deps, sent, _offloads, created, _preflight = _deps(
        tmp_path, send_exception=RuntimeError("discord down")
    )

    handled = await route.handle_rally_forts_upload(_message(), deps)

    assert handled is True
    assert len(created) == 1
    assert sent[-1][1] == "Rally Forts Import \u2705"


@pytest.mark.asyncio
async def test_rally_notify_failure_falls_back_to_source_channel(tmp_path):
    deps, sent, _offloads, _created, preflight = _deps(
        tmp_path, notify_exception=RuntimeError("notify down")
    )
    message = _message()

    handled = await route.handle_rally_forts_upload(message, deps)

    assert handled is True
    assert preflight == [message.channel]
    assert sent[-1][0] is message.channel


@pytest.mark.asyncio
async def test_rally_fort_rally_channel_id_zero_disables_route(tmp_path):
    deps, sent, offloads, _created, _preflight = _deps(tmp_path, fort_rally_channel_id=0)

    handled = await route.handle_rally_forts_upload(_message(), deps)

    assert handled is False
    assert sent == []
    assert offloads == []


@pytest.mark.asyncio
async def test_rally_rejects_path_traversal_filenames(tmp_path):
    """Filenames with path separators must be rejected to prevent path traversal."""
    deps, sent, offloads, _created, _preflight = _deps(tmp_path)

    # Attempt path traversal with directory separators
    handled = await route.handle_rally_forts_upload(
        _message(attachments=[_FakeAttachment("../../etc/Rally_data_26-05-2026.xlsx")]),
        deps,
    )

    assert handled is True
    assert offloads == []
    _ch, title, fields, color, _mention = sent[-1]
    assert title == "Rally Forts Import \u274c"
    assert "\u274c ../../etc/Rally_data_26-05-2026.xlsx" in fields
    assert "path separators not allowed" in fields["\u274c ../../etc/Rally_data_26-05-2026.xlsx"]
    assert color == 0xE74C3C


@pytest.mark.asyncio
async def test_rally_rejects_path_traversal_records_failed_uncorrelated_audit(tmp_path):
    audit_calls = []
    deps, _sent, offloads, _created, _preflight = _deps(tmp_path, audit_calls=audit_calls)

    handled = await route.handle_rally_forts_upload(
        _message(attachments=[_FakeAttachment("../../etc/Rally_data_26-05-2026.xlsx")]),
        deps,
    )

    assert handled is True
    assert offloads == []
    start_call = next(call for call in audit_calls if call[0] == "start")
    assert start_call[1]["context"].source_filename == "Rally_data_26-05-2026.xlsx"
    assert "local_path" not in start_call[1]
    fail_call = [call for call in audit_calls if call[0] == "fail"][-1]
    assert fail_call[2]["error_type"] == "UnsafeFilename"
    assert fail_call[2].get("external_batch_id") is None


@pytest.mark.asyncio
async def test_rally_rejects_backslash_path_traversal(tmp_path):
    """Filenames with backslash separators must be rejected on all platforms."""
    deps, sent, offloads, _created, _preflight = _deps(tmp_path)

    handled = await route.handle_rally_forts_upload(
        _message(attachments=[_FakeAttachment("..\\..\\Rally_data_26-05-2026.xlsx")]),
        deps,
    )

    assert handled is True
    assert offloads == []
    _ch, title, fields, color, _mention = sent[-1]
    assert title == "Rally Forts Import \u274c"
    assert "\u274c ..\\..\\Rally_data_26-05-2026.xlsx" in fields
    assert color == 0xE74C3C
