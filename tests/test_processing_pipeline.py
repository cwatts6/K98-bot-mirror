from unittest.mock import AsyncMock, Mock

import pytest

# Use pytest-asyncio for async tests
pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
@pytest.mark.parametrize("failed_stage", ["sql", "proc_config", None])
async def test_each_pipeline_outcome_emits_one_truthful_summary(monkeypatch, failed_stage):
    import processing_pipeline as pp

    _patch_lightweight_pipeline_boundaries(monkeypatch)
    monkeypatch.setattr(
        pp,
        "run_stats_copy_archive",
        AsyncMock(
            return_value=(
                True,
                "archive",
                {"excel": True, "archive": True, "sql": failed_stage != "sql"},
            )
        ),
    )
    monkeypatch.setattr(
        pp,
        "_run_proc_config_step",
        AsyncMock(return_value=(failed_stage != "proc_config", "config")),
    )
    monkeypatch.setattr(pp, "MAINT_WORKER_MODE", "thread")
    telemetry = Mock()
    monkeypatch.setattr(pp, "emit_telemetry_event", telemetry)
    result = await pp.execute_processing_pipeline(
        1, seed=1, user=AsyncMock(), filename="fixture.xlsx", channel_id=0
    )
    summaries = [
        c.args[0]
        for c in telemetry.call_args_list
        if c.args[0].get("event") == "processing_pipeline_summary"
    ]
    assert len(summaries) == 1
    summary = summaries[0]
    assert [summary[k] for k in ("excel", "archive", "sql", "export", "proc_import")] == list(
        result[:5]
    )
    assert summary["filename"] == "fixture.xlsx"
    assert summary["duration_seconds"] >= 0
    if failed_stage:
        assert summary["export"] is None
    if failed_stage == "sql":
        assert summary["proc_import"] is None


@pytest.mark.asyncio
async def test_pipeline_keeps_queued_export_distinct_from_completion(monkeypatch):
    import processing_pipeline as pp
    from services.export_submission import ExportSubmission

    _patch_lightweight_pipeline_boundaries(monkeypatch)

    async def archive(*a, **k):
        return True, "archive", {"excel": True, "archive": True, "sql": True}

    monkeypatch.setattr(pp, "run_stats_copy_archive", archive)
    monkeypatch.setattr(
        pp,
        "run_all_exports",
        lambda *a, **k: ExportSubmission("exact-job", "exact-preparation"),
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
    if sql_success:
        assert result[4] is True
        offload.assert_awaited_once()
        assert offload.call_args.kwargs["prefer_process"] is False
    else:
        assert result[3:5] == (None, None)
        offload.assert_not_awaited()
        isolated.assert_not_awaited()
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


@pytest.mark.asyncio
async def test_stats_ready_precedes_google_dependency_and_survives_its_failure(monkeypatch):
    from unittest.mock import Mock

    import processing_pipeline as pp
    from stats_alerts import processing_notifications as notifications

    _patch_lightweight_pipeline_boundaries(monkeypatch)
    stages = []
    cache = {"_meta": {"generated_at": "fresh"}}
    monkeypatch.setattr(
        pp,
        "run_stats_copy_archive",
        AsyncMock(return_value=(True, "SQL", {"excel": True, "archive": True, "sql": True})),
    )
    monkeypatch.setattr(pp, "build_player_stats_cache", AsyncMock(return_value=cache))

    async def ready(bot, run_id, output):
        assert output is cache
        stages.append("stats_ready")

    async def maintenance(kind, **kwargs):
        stages.append(kind)
        return (False, "Google unavailable") if kind == "proc_import" else (True, "OK")

    monkeypatch.setattr(notifications, "bot_data_ready", ready)
    monkeypatch.setattr(pp, "run_maintenance_with_isolation", maintenance)
    exporter = Mock(side_effect=AssertionError("dependent export must not run"))
    monkeypatch.setattr(pp, "run_all_exports", exporter)
    result = await pp.execute_processing_pipeline(
        1,
        seed=1,
        user=AsyncMock(),
        filename="fixture.xlsx",
        channel_id=0,
        notification_run_id="new-run",
    )
    assert stages.index("stats_ready") < stages.index("proc_import")
    assert result[2] is True and result[4] is False
    exporter.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("failure_stage", ["readiness", "after_enqueue"])
async def test_required_notification_failure_propagates_without_false_export_failure(
    monkeypatch, failure_stage
):
    import processing_pipeline as pp
    from services import processing_notification_service as core
    from services.export_submission import ExportSubmission
    from stats_alerts import processing_notifications as notifications

    _patch_lightweight_pipeline_boundaries(monkeypatch)
    monkeypatch.setattr(
        pp,
        "run_stats_copy_archive",
        AsyncMock(return_value=(True, "SQL", {"excel": True, "archive": True, "sql": True})),
    )
    monkeypatch.setattr(pp, "_run_proc_config_step", AsyncMock(return_value=(True, "config")))
    failure = core.NotificationTransitionFailed("journal")
    monkeypatch.setattr(
        notifications,
        "bot_data_ready",
        AsyncMock(side_effect=failure if failure_stage == "readiness" else None),
    )
    monkeypatch.setattr(core, "patch_run", AsyncMock(side_effect=failure))
    export = Mock(return_value=ExportSubmission("exact-job", "exact-preparation"))
    monkeypatch.setattr(pp, "run_all_exports", export)
    intervention, telemetry = AsyncMock(), Mock()
    monkeypatch.setattr(pp, "_notification_intervention", intervention)
    monkeypatch.setattr(pp, "emit_telemetry_event", telemetry)
    with pytest.raises(core.NotificationTransitionFailed):
        await pp.execute_processing_pipeline(
            1,
            seed=1,
            user="operator",
            filename="fixture.xlsx",
            channel_id=0,
            notification_run_id="exact-run",
        )
    intervention.assert_awaited_once()
    assert intervention.call_args.args[2] == "exact-run"
    assert export.call_count == (failure_stage == "after_enqueue")
    assert not any(
        c.args[0].get("event") == "run_all_exports" and c.args[0].get("status") == "failed"
        for c in telemetry.call_args_list
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("proc_success", [False, True])
async def test_target_cache_follows_proc_config_and_precedes_export(monkeypatch, proc_success):
    import processing_pipeline as pp
    from stats_alerts import processing_notifications as notifications

    _patch_lightweight_pipeline_boundaries(monkeypatch)
    stages = []
    monkeypatch.setattr(
        pp,
        "run_stats_copy_archive",
        AsyncMock(return_value=(True, "SQL", {"excel": True, "archive": True, "sql": True})),
    )

    async def ready(*args):
        stages.append("stats_ready")

    async def proc(*args):
        stages.append("proc_config")
        return proc_success, "config"

    async def targets():
        assert proc_success and stages[-1] == "proc_config"
        stages.append("targets")

    def export(*args, **kwargs):
        stages.append("export")
        return False, "Google unavailable"

    monkeypatch.setattr(notifications, "bot_data_ready", ready)
    monkeypatch.setattr(pp, "_run_proc_config_step", proc)
    monkeypatch.setattr(pp, "warm_target_cache", targets)
    monkeypatch.setattr(pp, "run_all_exports", export)
    result = await pp.execute_processing_pipeline(
        1,
        seed=1,
        user=AsyncMock(),
        filename="fixture.xlsx",
        channel_id=0,
        notification_run_id="exact-run",
    )
    assert stages == (
        ["stats_ready", "proc_config", "targets", "export"]
        if proc_success
        else ["stats_ready", "proc_config"]
    )
    assert result[2] is True and result[4] is proc_success
