from datetime import UTC, datetime, timedelta

import pytest

from services import location_import_service as svc


@pytest.fixture(autouse=True)
def _disable_location_audit(monkeypatch):
    monkeypatch.setattr(svc.import_audit_service, "start_batch_best_effort", lambda **_kwargs: 123)
    monkeypatch.setattr(
        svc.import_audit_service,
        "record_phase_best_effort",
        lambda _batch_ref, **_kwargs: 1,
    )
    monkeypatch.setattr(
        svc.import_audit_service,
        "complete_batch_best_effort",
        lambda _batch_ref, **_kwargs: True,
    )
    monkeypatch.setattr(
        svc.import_audit_service,
        "fail_batch_best_effort",
        lambda _batch_ref, **_kwargs: True,
    )


def test_validate_location_csv_attachment_rejects_non_csv():
    result = svc.validate_location_csv_attachment(filename="output.txt", size=10)

    assert result.ok is False
    assert (
        result.message
        == "❌ `output.txt` isn’t a CSV file. Please upload a `.csv` (e.g., `output.csv`)."
    )


def test_validate_location_csv_attachment_rejects_oversize_csv():
    result = svc.validate_location_csv_attachment(
        filename="output.csv", size=svc.MAX_LOCATION_CSV_BYTES + 1
    )

    assert result.ok is False
    assert result.message == "❌ File too large (10.0 MB). Please keep CSV under **10 MB**."


@pytest.mark.asyncio
async def test_import_location_csv_bytes_returns_parse_failure():
    def _parser(_csv_bytes):
        raise ValueError("bad csv")

    result = await svc.import_location_csv_bytes(
        b"bad",
        filename="output.csv",
        parser=_parser,
    )

    assert result.ok is False
    assert result.message == "❌ Failed to parse CSV: `ValueError: bad csv`"


@pytest.mark.asyncio
async def test_import_location_csv_bytes_returns_empty_rows_message():
    result = await svc.import_location_csv_bytes(
        b"header",
        filename="output.csv",
        parser=lambda _csv_bytes: [],
    )

    assert result.ok is False
    assert result.message == "⚠️ No valid rows found in the CSV."


@pytest.mark.asyncio
async def test_import_location_csv_bytes_returns_merge_failure():
    async def _thread_runner(func, rows):
        return func(rows)

    def _merge(_rows):
        raise RuntimeError("db unavailable")

    result = await svc.import_location_csv_bytes(
        b"csv",
        filename="output.csv",
        parser=lambda _csv_bytes: [(1, "A", 2, 3, 4, "K98", 10, 20)],
        merge_rows=_merge,
        thread_runner=_thread_runner,
    )

    assert result.ok is False
    assert result.rows_parsed == 1
    assert result.message == "❌ Failed to import rows: `RuntimeError: db unavailable`"


@pytest.mark.asyncio
async def test_import_location_csv_bytes_formats_success_and_signals_refresh():
    started = datetime.now(UTC) - timedelta(seconds=1.24)
    signal_calls = []

    async def _thread_runner(func, rows):
        return func(rows)

    result = await svc.import_location_csv_bytes(
        b"csv",
        filename="output.csv",
        parser=lambda _csv_bytes: [(1, "A", 2, 3, 4, "K98", 10, 20)],
        merge_rows=lambda _rows: (1, 42),
        thread_runner=_thread_runner,
        on_success=lambda: signal_calls.append("called"),
        started_at_utc=started,
    )

    assert result.ok is True
    assert result.rows_parsed == 1
    assert result.staging_rows == 1
    assert result.total_tracked == 42
    assert result.message.startswith("✅ Imported **1** row. Total tracked now **42**. ⏱ ")
    assert signal_calls == ["called"]


@pytest.mark.asyncio
async def test_import_location_csv_bytes_records_merge_audit(monkeypatch):
    calls = []
    runner_functions = []

    def _start(**kwargs):
        calls.append(("start", kwargs))
        return 321

    def _phase(batch_ref, **kwargs):
        calls.append(("phase", batch_ref, kwargs))
        return 1

    def _complete(batch_ref, **kwargs):
        calls.append(("complete", batch_ref, kwargs))
        return True

    async def _runner(func, *args, **kwargs):
        runner_functions.append(func.__name__)
        return func(*args, **kwargs)

    async def _thread_runner(func, rows):
        return func(rows)

    monkeypatch.setattr(svc.import_audit_service, "start_batch_best_effort", _start)
    monkeypatch.setattr(svc.import_audit_service, "record_phase_best_effort", _phase)
    monkeypatch.setattr(svc.import_audit_service, "complete_batch_best_effort", _complete)

    result = await svc.import_location_csv_bytes(
        b"csv",
        filename="output.csv",
        parser=lambda _csv_bytes: [(1, "A", 2, 3, 4, "K98", 10, 20)],
        merge_rows=lambda _rows: (1, 42),
        thread_runner=_thread_runner,
        audit_runner=_runner,
        audit_context=svc.LocationImportAuditContext(
            source_filename="output.csv",
            source_channel_id=10,
            actor_discord_id=123,
            entry_point="location_command_import",
            sql_operation="merge",
        ),
    )

    assert result.ok is True
    assert runner_functions[0] == "_start_location_audit_batch_sync"
    assert calls[0][0] == "start"
    assert calls[0][1]["import_kind"] == "player_location"
    assert calls[0][1]["source_type"] == "discord_upload_csv"
    assert calls[0][1]["source_filename"] == "output.csv"
    phase_names = [call[2]["phase_name"] for call in calls if call[0] == "phase"]
    assert phase_names == [
        "location_csv_parse",
        "location_sql_merge",
        "location_post_import_refresh",
    ]
    assert calls[-1][0] == "complete"
    assert calls[-1][2]["rows_in_source"] == 1
    assert calls[-1][2]["rows_staged"] == 1
    assert calls[-1][2]["rows_written"] == 1


@pytest.mark.asyncio
async def test_import_location_csv_bytes_preserves_success_when_audit_fails(monkeypatch):
    async def _thread_runner(func, rows):
        return func(rows)

    def _raise(**_kwargs):
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr(svc.import_audit_service, "start_batch_best_effort", _raise)

    result = await svc.import_location_csv_bytes(
        b"csv",
        filename="output.csv",
        parser=lambda _csv_bytes: [(1, "A", 2, 3, 4, "K98", 10, 20)],
        merge_rows=lambda _rows: (1, 42),
        thread_runner=_thread_runner,
    )

    assert result.ok is True
    assert result.staging_rows == 1


@pytest.mark.asyncio
async def test_import_location_csv_bytes_preserves_success_when_refresh_signal_fails(monkeypatch):
    complete_calls = []

    def _complete(batch_ref, **kwargs):
        complete_calls.append((batch_ref, kwargs))
        return True

    async def _audit_runner(func, *args, **kwargs):
        return func(*args, **kwargs)

    async def _thread_runner(func, rows):
        return func(rows)

    def _signal():
        raise RuntimeError("signal failed")

    monkeypatch.setattr(svc.import_audit_service, "complete_batch_best_effort", _complete)

    result = await svc.import_location_csv_bytes(
        b"csv",
        filename="output.csv",
        parser=lambda _csv_bytes: [(1, "A", 2, 3, 4, "K98", 10, 20)],
        merge_rows=lambda _rows: (2, 50),
        thread_runner=_thread_runner,
        on_success=_signal,
        audit_runner=_audit_runner,
    )

    assert result.ok is True
    assert "Imported **2** rows." in result.message
    assert complete_calls[-1][1]["status"] == "failed"
    assert complete_calls[-1][1]["rows_in_source"] == 1


def test_parse_output_csv_skips_bad_rows_and_keeps_valid_rows():
    csv_bytes = (
        b"player_id,player_name,player_power,player_kills,player_ch,player_alliance,x,y\n"
        b"123,Alice,1000,20,25,K98,10,20\n"
        b"bad,Broken,1000,20,25,K98,10,20\n"
    )

    rows = svc.parse_output_csv(csv_bytes)

    assert rows == [(123, "Alice", 1000, 20, 25, "K98", 10, 20, None, None)]


def test_parse_output_csv_maps_shield_time_left_to_raw_and_utc():
    csv_bytes = (
        b"player_id,player_name,player_power,player_kills,player_ch,player_alliance,x,y,shield_time_left\n"
        b"123,Alice,1000,20,25,K98,10,20,1782483442\n"
    )

    rows = svc.parse_output_csv(csv_bytes)

    assert rows == [
        (
            123,
            "Alice",
            1000,
            20,
            25,
            "K98",
            10,
            20,
            1782483442,
            datetime(2026, 6, 26, 14, 17, 22),
        )
    ]


def test_parse_output_csv_zero_shield_keeps_raw_zero_and_null_utc():
    csv_bytes = (
        b"player_id,player_name,player_power,player_kills,player_ch,player_alliance,x,y,shield_time_left\n"
        b"123,Alice,1000,20,25,K98,10,20,0\n"
    )

    rows = svc.parse_output_csv(csv_bytes)

    assert rows == [(123, "Alice", 1000, 20, 25, "K98", 10, 20, 0, None)]


def test_parse_output_csv_maps_max_sql_datetime2_shield_epoch():
    csv_bytes = (
        b"player_id,player_name,player_power,player_kills,player_ch,player_alliance,x,y,shield_time_left\n"
        b"123,Alice,1000,20,25,K98,10,20,253402300799\n"
    )

    rows = svc.parse_output_csv(csv_bytes)

    assert rows == [
        (
            123,
            "Alice",
            1000,
            20,
            25,
            "K98",
            10,
            20,
            253402300799,
            datetime(9999, 12, 31, 23, 59, 59),
        )
    ]


def test_parse_output_csv_treats_whitespace_optional_numbers_as_zero():
    csv_bytes = (
        b"player_id,player_name,player_power,player_kills,player_ch,player_alliance,x,y\n"
        b"123,Alice, , , ,K98,10,20\n"
    )

    rows = svc.parse_output_csv(csv_bytes)

    assert rows == [(123, "Alice", 0, 0, 0, "K98", 10, 20, None, None)]


def test_parse_output_csv_skips_invalid_shield_row():
    csv_bytes = (
        b"player_id,player_name,player_power,player_kills,player_ch,player_alliance,x,y,shield_time_left\n"
        b"123,Alice,1000,20,25,K98,10,20,not-a-number\n"
    )

    rows = svc.parse_output_csv(csv_bytes)

    assert rows == []
