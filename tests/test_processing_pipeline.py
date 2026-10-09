from unittest.mock import AsyncMock

import pytest

# Use pytest-asyncio for async tests
pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_pipeline_keeps_queued_export_distinct_from_completion(monkeypatch):
    import processing_pipeline as pp

    _patch_lightweight_pipeline_boundaries(monkeypatch)

    async def archive(*a, **k):
        return True, "archive", {"excel": True, "archive": True, "sql": True}

    monkeypatch.setattr(pp, "run_stats_copy_archive", archive)
    monkeypatch.setattr(
        pp,
        "run_all_exports",
        lambda *a, **k: (False, "Queued export job exact-job; provider completion is pending."),
    )
    sent = AsyncMock()
    monkeypatch.setattr(pp, "send_status_embed", sent)
    result = await pp.execute_processing_pipeline(
        1, seed=1, user=AsyncMock(), filename="test.xlsx", channel_id=0, save_path=None
    )
    assert result[3] == "pending"
    assert any(call.args[1].get("Status") == "Queued" for call in sent.call_args_list)
    assert (
        next(call.args[2] for call in sent.call_args_list if call.args[1].get("Status") == "Queued")
        is None
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("sql_success", [True, False])
async def test_both_proc_config_branches_keep_runtime_in_thread(monkeypatch, sql_success):
    import proc_config_import
    import processing_pipeline as pp
    from services import legacy_export_snapshot_service as snapshots

    _patch_lightweight_pipeline_boundaries(monkeypatch)
    monkeypatch.setattr(pp, "MAINT_WORKER_MODE", "process")
    monkeypatch.setattr(snapshots, "_writer_runtime", lambda: object())
    offload = AsyncMock(return_value=(True, "config captured"))
    monkeypatch.setattr(proc_config_import, "run_proc_config_import_offload", offload)
    isolated = AsyncMock(return_value=(True, "OK"))
    monkeypatch.setattr(pp, "run_maintenance_with_isolation", isolated)

    async def archive(*a, **k):
        return True, "archive", {"excel": True, "archive": True, "sql": sql_success}

    monkeypatch.setattr(pp, "run_stats_copy_archive", archive)
    result = await pp.execute_processing_pipeline(
        1, seed=1, user=AsyncMock(), filename="test.xlsx", channel_id=0, save_path=None
    )
    assert result[4] is True
    offload.assert_awaited_once()
    assert offload.call_args.kwargs["prefer_process"] is False
    assert all(call.args[0] != "proc_import" for call in isolated.call_args_list)


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
async def test_handler_preserves_pending_export_in_live_queue_and_summary(monkeypatch):
    import asyncio
    from types import SimpleNamespace

    import processing_pipeline as pp

    _patch_lightweight_pipeline_boundaries(monkeypatch)
    message = SimpleNamespace(channel=SimpleNamespace(id=-1), author="fixture-operator")
    queue = {"jobs": [{"filename": "fixture.xlsx", "user": str(message.author)}]}
    monkeypatch.setattr(pp, "live_queue", queue)
    monkeypatch.setattr(pp, "live_queue_lock", asyncio.Lock())
    monkeypatch.setattr(pp, "update_live_queue_embed", AsyncMock())
    monkeypatch.setattr(pp, "prompt_admin_inputs", AsyncMock(return_value=(1, 1)))
    monkeypatch.setattr(pp, "load_cached_input", lambda: {})
    monkeypatch.setattr(
        pp,
        "execute_processing_pipeline",
        AsyncMock(return_value=(True, True, True, "pending", True, "queued job")),
    )
    log = AsyncMock()
    monkeypatch.setattr(pp, "log_processing_result", log)
    await pp.handle_file_processing(AsyncMock(), message, "fixture.xlsx", None)
    assert log.call_args.args[10] == "pending"
    assert queue["jobs"][0]["status"].startswith("⏳ Export pending")


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
