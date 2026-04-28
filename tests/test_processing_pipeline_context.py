# tests/test_processing_pipeline_context.py
import asyncio

import pytest

import processing_pipeline


@pytest.mark.asyncio
async def test_execute_processing_pipeline_embeds_include_context(monkeypatch):
    """
    Ensure that processing_pipeline emits embed(s) that include a standardized
    "Context" field containing filename, rank and seed.
    We monkeypatch external dependencies so the orchestration runs fast and
    deterministically.
    """

    sent_calls = []

    async def mock_send_embed_safe(destination, title, fields, color, **kwargs):
        # record minimal call info
        sent_calls.append(
            {"destination": destination, "title": title, "fields": dict(fields), "color": color}
        )
        return True

    # Patch the embed sender used by processing_pipeline (it was imported at module import time)
    monkeypatch.setattr(processing_pipeline, "send_embed_safe", mock_send_embed_safe)

    # Also intercept send_status_embed — this is where Context is merged into the fields dict
    # via {**context_field, **status_map}. Capture those calls so we can assert Context is present.
    status_embed_calls = []

    async def mock_send_status_embed(
        title, status_map, ok, user, notify_channel, *, context_field=None, **kwargs
    ):
        status_embed_calls.append(
            {
                "title": title,
                "status_map": dict(status_map),
                "ok": ok,
                "context_field": dict(context_field) if context_field else {},
            }
        )

    monkeypatch.setattr(processing_pipeline, "send_status_embed", mock_send_status_embed)

    # Mock run_stats_copy_archive to return success quickly and include excel/archive/sql flags
    async def mock_run_stats_copy_archive(
        rank, seed, source_filename=None, send_step_embed=None
    ):
        await asyncio.sleep(0)  # yield control to event loop
        return None, "ARCHIVE_LOG", {"excel": True, "archive": True, "sql": True}

    monkeypatch.setattr(processing_pipeline, "run_stats_copy_archive", mock_run_stats_copy_archive)

    # Mock the player stats cache rebuild to be a no-op
    async def mock_build_player_stats_cache():
        await asyncio.sleep(0)

    monkeypatch.setattr(
        processing_pipeline, "build_player_stats_cache", mock_build_player_stats_cache
    )

    # Mock maintenance wrapper to immediately succeed
    async def mock_run_maintenance_with_isolation(
        command, args=None, kwargs=None, timeout=None, name=None, meta=None, prefer_process=None
    ):
        await asyncio.sleep(0)
        return True, "OK"

    monkeypatch.setattr(
        processing_pipeline, "run_maintenance_with_isolation", mock_run_maintenance_with_isolation
    )

    # Mock run_step to handle run_stats_copy_archive, run_all_exports, and read_json_safe centrally
    async def mock_run_step(
        func, *args, offload_sync_to_thread=False, name=None, **kwargs
    ):
        # run_stats_copy_archive → return canonical 3-tuple (success, log, steps).
        # Check the explicit `name` kwarg first (most reliable), then fall back to func.__name__.
        func_name = name or getattr(func, "__name__", "")
        if func_name.endswith("run_stats_copy_archive"):
            return True, "ARCHIVE_LOG", {"excel": True, "archive": True, "sql": True}
        # run_all_exports → success
        if func_name == "run_all_exports" or func is processing_pipeline.run_all_exports:
            return True, "EXPORT_LOG"
        # read_json_safe -> return empty dict
        if func_name == "read_json_safe" or func is processing_pipeline.read_json_safe:
            return {}
        # preflight or other helpers: no-op
        return None

    monkeypatch.setattr(processing_pipeline, "run_step", mock_run_step)

    # Mock warm caches to be no-ops
    async def mock_warm_name_cache():
        await asyncio.sleep(0)

    async def mock_warm_target_cache():
        await asyncio.sleep(0)

    monkeypatch.setattr(processing_pipeline, "warm_name_cache", mock_warm_name_cache)
    monkeypatch.setattr(processing_pipeline, "warm_target_cache", mock_warm_target_cache)

    # Prepare a dummy "user" destination object (send_embed_safe is mocked so it won't be used)
    class DummyUser:
        id = 1234

        def __str__(self):
            return "<DummyUser>"

    dummy_user = DummyUser()

    # Run the pipeline with a sample filename/rank/seed
    filename = "sample_report.xlsx"
    rank = 5
    seed = 99
    # Use channel_id that is unlikely to resolve to an actual saved file
    channel_id = 0

    result = await processing_pipeline.execute_processing_pipeline(
        rank, seed=seed, user=dummy_user, filename=filename, channel_id=channel_id, save_path=None
    )

    # Ensure function returned the expected tuple shape (we don't assert specific booleans here)
    assert isinstance(result, tuple) and len(result) == 6

    # At least one embed send should have occurred
    assert sent_calls, "No embeds were sent during pipeline run"

    # Context is merged into fields by send_status_embed (via {**context_field, **status_map}).
    # We verify those calls include a "Context" field with the expected filename, rank and seed.
    context_values = [
        str(call["context_field"].get("Context", ""))
        for call in status_embed_calls
        if call.get("context_field") and "Context" in call["context_field"]
    ]
    assert context_values, 'No send_status_embed call included the expected "Context" field'
    assert any(
        # Discord/embed_utils may markdown-escape underscores in filenames (e.g. _ → \_),
        # so accept either the original or the escaped form.
        (filename in context or filename.replace("_", r"\_") in context)
        and str(rank) in context
        and str(seed) in context
        for context in context_values
    ), (
        'No embed "Context" field contained the expected filename, rank, and seed: '
        f"{context_values}"
    )
