# tests/test_pr5_telemetry_and_embed.py
import json
import types

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


@pytest.mark.asyncio
async def test_send_status_embed_calls_send_embed_safe(monkeypatch):
    """
    Verify that processing_pipeline._send_status_embed calls send_embed_safe with expected color and fields,
    and emits telemetry via file_utils.emit_telemetry_event.
    """
    import processing_pipeline as pp

    captured = {}

    async def fake_send_embed_safe(dest, title, fields, color, **kwargs):
        captured["dest"] = dest
        captured["title"] = title
        captured["fields"] = fields
        captured["color"] = color
        return True

    monkeypatch.setattr(pp, "send_embed_safe", fake_send_embed_safe)

    recorded = []

    def fake_emit(payload, *, max_snippet=2000):
        recorded.append(payload)

    # IMPORTANT: processing_pipeline imported emit_telemetry_event directly at module import time.
    # We must monkeypatch the name in the processing_pipeline module so _send_status_embed will call our fake.
    monkeypatch.setattr(pp, "emit_telemetry_event", fake_emit)

    # call helper
    user = types.SimpleNamespace(id=1111)
    notify = None
    await pp._send_status_embed(
        "Test Title",
        {"Key": "Val", "Log": "L" * 50},
        True,
        user,
        notify,
        context_field={"Context": "ctx"},
    )

    assert captured["title"] == "Test Title"
    assert "Context" in captured["fields"]
    assert captured["fields"]["Context"] == "ctx"
    assert captured["color"] == 0x2ECC71
    # telemetry emitted (our fake appends a payload dict)
    assert recorded and recorded[0].get("title") == "Test Title"
