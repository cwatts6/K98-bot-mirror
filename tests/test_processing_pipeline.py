# tests/test_processing_pipeline.py
import asyncio

import pytest

import processing_pipeline


@pytest.mark.asyncio
async def test_execute_processing_pipeline_trusts_stats_contract(monkeypatch):
    """
    Ensure execute_processing_pipeline can consume the standardized stats_module return
    when stats_module.run_stats_copy_archive returns the (success, combined_log, steps) tuple.
    We monkeypatch heavy external dependencies to keep the test deterministic.
    """

    # Stub run_stats_copy_archive to return canonical shape (async)
    async def fake_stats_copy_archive(
        rank, seed, source_filename=None, send_step_embed=None, **kwargs
    ):
        # simulate some awaitable behavior
        await asyncio.sleep(0)
        return True, "ARCHIVE LOG", {"excel": True, "archive": True, "sql": False}

    # Replace heavy / network bound functions with async no-ops or benign returns
    async def async_noop(*args, **kwargs):
        await asyncio.sleep(0)
        return True, "ok"

    async def async_noop_export(*args, **kwargs):
        await asyncio.sleep(0)
        return True, "export ok"

    async def async_build_cache(*args, **kwargs):
        await asyncio.sleep(0)
        return None

    async def async_send_embed_safe(*args, **kwargs):
        await asyncio.sleep(0)
        return True

    # Patch dependencies on the processing_pipeline module
    monkeypatch.setattr(processing_pipeline, "run_stats_copy_archive", fake_stats_copy_archive)
    monkeypatch.setattr(processing_pipeline, "get_channel_safe", lambda *a, **k: None)
    monkeypatch.setattr(processing_pipeline, "send_embed_safe", async_send_embed_safe)
    # Leave run_step as-is (use real helper); instead patch run_all_exports and run_maintenance_with_isolation
    monkeypatch.setattr(processing_pipeline, "build_player_stats_cache", async_build_cache)
    monkeypatch.setattr(processing_pipeline, "run_maintenance_with_isolation", async_noop)
    monkeypatch.setattr(processing_pipeline, "run_all_exports", async_noop_export)
    monkeypatch.setattr(processing_pipeline, "warm_name_cache", async_noop)
    monkeypatch.setattr(processing_pipeline, "warm_target_cache", async_noop)

    # Call execute_processing_pipeline with minimal parameters
    result = await processing_pipeline.execute_processing_pipeline(
        1, seed=42, user=None, filename="f.xlsx", channel_id=0, save_path=None
    )

    # Expect tuple shape with booleans in the first five entries and a string last
    assert isinstance(result, tuple)
    assert len(result) == 6
    (
        success_excel,
        success_archive,
        success_sql,
        success_export,
        success_proc_import,
        combined_log,
    ) = result

    assert isinstance(success_excel, bool)
    assert isinstance(success_archive, bool)
    assert isinstance(success_sql, bool)
    assert isinstance(success_export, bool)
    # success_proc_import may be None or bool depending on path
    assert isinstance(success_proc_import, bool) or success_proc_import is None
    assert isinstance(combined_log, str)
    # The combined_log should contain the ARCHIVE LOG snippet returned by our stub
    assert "ARCHIVE LOG" in combined_log
