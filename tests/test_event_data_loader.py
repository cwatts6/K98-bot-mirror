import asyncio
from datetime import UTC, datetime, timedelta
import importlib
import logging
import threading
import time

import event_data_loader as edl
import gsheet_module as gm


def test_parse_dt_accepts_z_suffix_and_returns_aware_datetime():
    s = "2025-12-20T12:34:56Z"
    dt = edl._parse_dt_str_utc(s)
    assert isinstance(dt, datetime)
    assert dt.tzinfo is not None
    # Normalize to UTC for equality check
    assert dt.astimezone(UTC).isoformat().startswith("2025-12-20T12:34:56")


def test_fetch_values_emits_telemetry_on_client_error(monkeypatch):
    emitted = []

    def fake_get_values(spreadsheet_id, range_a1, timeout=None, **kwargs):
        raise RuntimeError("simulated sheets client failure")

    monkeypatch.setattr(gm, "get_sheet_values", fake_get_values)

    import file_utils

    monkeypatch.setattr(
        file_utils,
        "emit_telemetry_event",
        lambda payload, **kw: emitted.append(payload),
    )

    res = edl._fetch_values("RUINS_BOT_DATES!A2:A")
    assert res is None
    assert len(emitted) >= 1
    ev = emitted[-1]
    assert ev.get("event") == "sheets_fetch_failed"
    assert ev.get("range") == "RUINS_BOT_DATES!A2:A"


def test_fetch_values_emits_empty_range_telemetry_and_returns_empty(monkeypatch):
    emitted = []

    def fake_get_values(spreadsheet_id, range_a1, timeout=None, **kwargs):
        return []

    monkeypatch.setattr(gm, "get_sheet_values", fake_get_values)

    import file_utils

    monkeypatch.setattr(
        file_utils,
        "emit_telemetry_event",
        lambda payload, **kw: emitted.append(payload),
    )

    res = edl._fetch_values("RUINS_BOT_DATES!A2:A")
    assert res == []
    assert any(ev.get("event") == "sheets_fetch_empty" for ev in emitted)


def test_loader_normalizes_offload_return_shapes_and_receives_timeout(monkeypatch):
    """
    Ensure that when start_callable_offload returns (result, metadata), the loader
    returns the normalized result (not the metadata tuple) and that timeout param
    is propagated to the offload helper.
    """
    now = datetime.now(UTC).replace(microsecond=0)
    fake_events = [
        {
            "name": "FakeRuins",
            "type": "ruins",
            "start_time": now,
            "end_time": now + edl.timedelta(minutes=15),
        }
    ]

    received = {}

    async def fake_start_callable_offload(func, **kwargs):
        # capture kwargs for assertion
        received.update(kwargs)
        return (fake_events, {"meta": "ok"})

    monkeypatch.setattr(edl, "start_callable_offload", fake_start_callable_offload)

    # Call loader with an explicit timeout and assert the fake was called with timeout
    res = asyncio.run(edl.load_upcoming_ruins_events(timeout=5.0))
    assert isinstance(res, list)
    assert res == fake_events
    assert "timeout" in received
    assert received["timeout"] == 5.0


def test_concurrent_fetch_values_does_not_raise(monkeypatch):
    def fake_get_values(spreadsheet_id, range_a1, timeout=None, **kwargs):
        time.sleep(0.01)
        return [["2025-12-20T12:34:56Z", "Event"]]

    monkeypatch.setattr(gm, "get_sheet_values", fake_get_values)

    results = []
    errors = []

    def worker():
        try:
            r = edl._fetch_values("RUINS_BOT_DATES!A2:A")
            results.append(r)
        except Exception as e:
            errors.append(e)

    threads = []
    for _ in range(8):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    assert not errors, f"Exceptions occurred during concurrent fetch: {errors}"
    assert len(results) == 8
    assert all(isinstance(r, list) for r in results)


def test_fetch_values_http_error_transient(monkeypatch):
    """
    Simulate googleapiclient.errors.HttpError with a 500 status => transient True.
    """
    emitted = []

    class FakeResp:
        def __init__(self, status):
            self.status = status

    class FakeHttpError(Exception):
        def __init__(self, msg, resp=None):
            super().__init__(msg)
            self.resp = resp

    # Ensure the module's _GA_HTTP_ERROR is set to our fake class for isinstance checks
    monkeypatch.setattr(edl, "_GA_HTTP_ERROR", FakeHttpError)

    def fake_get_values_raise(spreadsheet_id, range_a1, timeout=None, **kwargs):
        raise FakeHttpError("Server error", resp=FakeResp(500))

    monkeypatch.setattr(gm, "get_sheet_values", fake_get_values_raise)

    # Capture telemetry
    import file_utils

    monkeypatch.setattr(
        file_utils,
        "emit_telemetry_event",
        lambda payload, **kw: emitted.append(payload),
    )

    res = edl._fetch_values("RUINS_BOT_DATES!A2:A")
    assert res is None
    assert len(emitted) >= 1
    ev = emitted[-1]
    assert ev.get("event") == "sheets_fetch_failed"
    assert ev.get("range") == "RUINS_BOT_DATES!A2:A"
    assert ev.get("transient") is True
    assert ev.get("error_type", "").startswith("HttpError")


def test_fetch_values_file_not_found_classified_permanent(monkeypatch):
    """
    Simulate a FileNotFoundError coming from credential loading / client factory.
    Ensure telemetry transient=False and error_type indicates FileNotFoundError.
    """
    emitted = []

    def fake_get_values_raise(spreadsheet_id, range_a1, timeout=None, **kwargs):
        raise FileNotFoundError("no creds")

    monkeypatch.setattr(gm, "get_sheet_values", fake_get_values_raise)

    import file_utils

    monkeypatch.setattr(
        file_utils,
        "emit_telemetry_event",
        lambda payload, **kw: emitted.append(payload),
    )

    res = edl._fetch_values("RUINS_BOT_DATES!A2:A")
    assert res is None
    assert len(emitted) >= 1
    ev = emitted[-1]
    assert ev.get("event") == "sheets_fetch_failed"
    assert ev.get("range") == "RUINS_BOT_DATES!A2:A"
    assert ev.get("transient") is False
    assert ev.get("error_type") == "FileNotFoundError"


def test_loaders_use_real_sync_helpers_no_placeholder(caplog, monkeypatch):
    """
    Ensure the async loader uses the real sync helper and does not emit the
    'internal sync loader missing' warning when the sync helper is present.
    """
    caplog.set_level(logging.WARNING)
    # Avoid network by making _fetch_values return empty list synchronously
    monkeypatch.setattr(edl, "_fetch_values", lambda rng: [])
    # Force direct to-thread execution path (no start_callable_offload/run_blocking_in_thread)
    monkeypatch.setattr(edl, "start_callable_offload", None)
    monkeypatch.setattr(edl, "run_blocking_in_thread", None)

    # Run the loader
    asyncio.run(edl.load_upcoming_ruins_events())

    # No placeholder warning should be emitted
    assert "internal sync loader" not in caplog.text.lower()


def test_timeline_durations_accepts_timedelta_override(monkeypatch):
    """
    Ensure that constants.TIMELINE_DURATIONS using timedelta values will override
    event_data_loader.DUR and be converted to integer minutes.
    """
    import constants

    # Provide timedeltas for overrides
    monkeypatch.setattr(
        constants,
        "TIMELINE_DURATIONS",
        {"ruins": timedelta(minutes=7), "major": timedelta(hours=2)},
    )

    # Reload module to pick up new constants at import-time
    importlib.reload(edl)

    assert edl.DUR["ruins"] == 7
    assert edl.DUR["major"] == 120
