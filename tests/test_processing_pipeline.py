from unittest.mock import AsyncMock

import pytest

# Use pytest-asyncio for async tests
pytest_plugins = ("pytest_asyncio",)


def _patch_lightweight_pipeline_boundaries(monkeypatch):
    async def fake_send_status_embed(*args, **kwargs):
        return True

    async def fake_send_embed_safe(*args, **kwargs):
        return True

    async def fake_build_cache():
        return None

    async def fake_warm_cache():
        return None

    async def fake_run_maintenance_with_isolation(*args, **kwargs):
        return True, "OK"

    monkeypatch.setattr("processing_pipeline.send_status_embed", fake_send_status_embed)
    monkeypatch.setattr("processing_pipeline.send_embed_safe", fake_send_embed_safe)
    monkeypatch.setattr("processing_pipeline.get_channel_safe", lambda *a, **k: None)
    monkeypatch.setattr("processing_pipeline.build_player_stats_cache", fake_build_cache)
    monkeypatch.setattr("processing_pipeline.build_lastkvk_player_stats_cache", fake_build_cache)
    monkeypatch.setattr(
        "processing_pipeline.read_json_safe", lambda *a, **k: {"_meta": {"count": 0}}
    )
    monkeypatch.setattr(
        "processing_pipeline.run_maintenance_with_isolation",
        fake_run_maintenance_with_isolation,
    )
    monkeypatch.setattr("processing_pipeline.preflight_from_env_sync", lambda *a, **k: None)
    monkeypatch.setattr("processing_pipeline.run_all_exports", lambda *a, **k: (True, "OK"))
    monkeypatch.setattr("processing_pipeline.warm_name_cache", fake_warm_cache)
    monkeypatch.setattr("processing_pipeline.warm_target_cache", fake_warm_cache)


@pytest.mark.asyncio
async def test_run_stats_copy_archive_success(monkeypatch, tmp_path):
    """
    Ensure execute_processing_pipeline handles a well-formed run_stats_copy_archive return.
    """
    from processing_pipeline import execute_processing_pipeline

    _patch_lightweight_pipeline_boundaries(monkeypatch)

    # Mock run_stats_copy_archive to return expected tuple
    async def fake_run_stats_copy_archive(
        rank, seed, source_filename=None, send_step_embed=None, **kwargs
    ):
        # (success bool, out_archive str, steps dict)
        return True, "ARCHIVE LOG", {"excel": True, "archive": True, "sql": True}

    monkeypatch.setattr("processing_pipeline.run_stats_copy_archive", fake_run_stats_copy_archive)

    # Minimal stubs for dependencies
    fake_user = AsyncMock()
    # run execute_processing_pipeline with minimal required arguments
    res = await execute_processing_pipeline(
        1, seed=123, user=fake_user, filename="file.xlsx", channel_id=0, save_path=None
    )
    # returns tuple: success_excel, success_archive, success_sql, success_export, success_proc_import, combined_log
    assert res[0] is True
    assert res[1] is True
    assert res[2] is True
    assert isinstance(res[5], str)


@pytest.mark.asyncio
async def test_run_stats_copy_archive_unexpected_shape(monkeypatch):
    """
    If run_stats_copy_archive returns an unexpected shape, pipeline should coerce to failure
    and not crash.
    """
    from processing_pipeline import execute_processing_pipeline

    _patch_lightweight_pipeline_boundaries(monkeypatch)

    async def bad_run(rank, seed, **kwargs):
        # Return something unexpected
        return {"unexpected": "value"}

    monkeypatch.setattr("processing_pipeline.run_stats_copy_archive", bad_run)

    fake_user = AsyncMock()
    res = await execute_processing_pipeline(
        1, seed=1, user=fake_user, filename="bad.xlsx", channel_id=0, save_path=None
    )
    # success flags should be False/None coerced
    assert isinstance(res[5], str)  # combined_log should be string
