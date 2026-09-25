import pytest

# Import the module under test
import processing_pipeline


@pytest.mark.asyncio
async def test_run_stats_copy_archive_awaits_send_step_embed(monkeypatch):
    """
    Ensure that a stats-module-style function which awaits the provided
    `send_step_embed(title, msg)` callback can successfully await the
    async helper `_local_send_step_embed` from processing_pipeline.

    Strategy:
    - Monkeypatch processing_pipeline.send_embed_safe with a lightweight async stub
      so we do not attempt any network/Discord calls during the test.
    - Define a fake `run_stats_copy_archive`-like coroutine that simply awaits
      the provided callback once (the real function awaits it too).
    - Pass in a lambda that calls processing_pipeline._local_send_step_embed and
      assert our stub was invoked (showing the await completed).
    """

    called = {}

    async def fake_send_embed_safe(
        destination, title, fields, color, bot=None, fallback_channel=None, **kwargs
    ):
        # record the call so we can assert the awaited callback executed
        called["destination"] = destination
        called["title"] = title
        called["fields"] = fields
        called["color"] = color
        return True

    # Replace the send_embed_safe used by _local_send_step_embed with our stub
    monkeypatch.setattr(processing_pipeline, "send_embed_safe", fake_send_embed_safe)

    # Simulated run_stats_copy_archive that awaits the send_step_embed callback
    async def fake_run_stats_copy_archive(rank, seed, source_filename=None, send_step_embed=None):
        # the real implementation awaits send_step_embed(title, msg)
        await send_step_embed("Step-TEST", "⏳ Running")
        return None, "archive-log", {"excel": True, "archive": True, "sql": True}

    # Call the fake pipeline with the processing_pipeline async helper as the callback.
    # Note: we pass a lambda which returns the coroutine from _local_send_step_embed,
    # matching how processing_pipeline wires the callback in real code.
    result = await fake_run_stats_copy_archive(
        1,
        42,
        source_filename=None,
        send_step_embed=lambda title, msg: processing_pipeline._local_send_step_embed(
            "TEST_DEST", title, msg
        ),
    )

    # Assertions: fake_send_embed_safe should have been invoked by _local_send_step_embed,
    # proving the callback was awaited by fake_run_stats_copy_archive.
    assert "title" in called, "send_embed_safe was not called"
    assert called["title"] == "Step-TEST"
    assert called["fields"] == {"Status": "⏳ Running"}
    assert result[2]["excel"] is True
