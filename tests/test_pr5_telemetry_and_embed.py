# tests/test_pr5_telemetry_and_embed.py
import json

import pytest

pytest_plugins = ("pytest_asyncio",)


def test_emit_telemetry_event_trims(monkeypatch):
    """
    Verify file_utils.emit_telemetry_event trims long 'traceback' and 'detail' fields.
    """
    import file_utils

    events = []

    def fake_info(s):
        events.append(s)

    monkeypatch.setattr(file_utils.telemetry_logger, "info", fake_info)

    long_text = "X" * 5000
    payload = {"event": "test", "traceback": long_text, "detail": long_text, "ok": True}
    max_snip = 200
    file_utils.emit_telemetry_event(payload, max_snippet=max_snip)

    assert events, "telemetry_logger.info not called"
    # It's JSON string; parse and assert trimmed
    parsed = json.loads(events[0])
    assert "traceback" in parsed and parsed["traceback"].endswith("...(truncated)")
    # Allow exact upper bound equal to max_snippet + suffix length
    suffix = "...(truncated)"
    assert len(parsed["traceback"]) <= (
        max_snip + len(suffix)
    ), f"traceback length {len(parsed['traceback'])} exceeds expected {(max_snip + len(suffix))}"
    assert "detail" in parsed and parsed["detail"].endswith("...(truncated)")
