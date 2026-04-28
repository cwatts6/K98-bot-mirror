import asyncio

import pytest

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_run_step_with_sync_and_async(monkeypatch):
    """
    Validate run_step handles both sync and async functions consistently.
    Also validate execute_processing_pipeline's normalization path by mocking run_stats_copy_archive
    to return both tuple and dict shapes.
    """
    import processing_pipeline as pp

    # 1) sync function
    def sync_fn(a, b):
        return ("ok", "ARCHIVE_TEXT", {"excel": True, "archive": True, "sql": True})

    res_sync = await pp.run_step(sync_fn, 1, 2, offload_sync_to_thread=True, name="sync_fn")
    assert isinstance(res_sync, tuple)
    assert res_sync[1] == "ARCHIVE_TEXT"
    assert res_sync[2]["sql"] is True

    # 2) async function
    async def async_fn(a, b):
        await asyncio.sleep(0)
        return ("ok_async", "ARCHIVE2", {"excel": False, "archive": True, "sql": False})

    res_async = await pp.run_step(async_fn, 1, 2, name="async_fn")
    assert isinstance(res_async, tuple)
    assert res_async[1] == "ARCHIVE2"
    assert res_async[2]["archive"] is True

    # Now validate execute_processing_pipeline normalization for different shapes.
    # We'll monkeypatch many internals to keep the pipeline light-weight.
    async def fake_build_player_stats_cache():
        return None

    async def fake_warm_name_cache():
        return None

    async def fake_warm_target_cache():
        return None

    async def fake_run_all_exports(*args, **kwargs):
        return True, "EXPORT_OK"

    async def fake_run_maintenance_with_isolation(*args, **kwargs):
        return True, "MAINT_OK"

    # Replace heavy functions with fakes
    monkeypatch.setattr(pp, "build_player_stats_cache", fake_build_player_stats_cache)
    monkeypatch.setattr(pp, "warm_name_cache", fake_warm_name_cache)
    monkeypatch.setattr(pp, "warm_target_cache", fake_warm_target_cache)
    monkeypatch.setattr(pp, "run_all_exports", fake_run_all_exports)
    monkeypatch.setattr(pp, "run_maintenance_with_isolation", fake_run_maintenance_with_isolation)

    # monkeypatch send_embed_safe to a no-op to avoid discord usage
    async def fake_send_embed_safe(*args, **kwargs):
        return True

    monkeypatch.setattr(pp, "send_embed_safe", fake_send_embed_safe)

    # monkeypatch get_channel_safe to return None safely
    monkeypatch.setattr(pp, "get_channel_safe", lambda *a, **k: None)

    # create a fake user object for send_embed callbacks
    class FakeUser:
        id = 1234

        def __str__(self):
            return "FakeUser#0001"

    fake_user = FakeUser()

    # 3) Case: run_stats_copy_archive is sync and returns tuple
    def stats_sync_tuple(rank, seed, **kwargs):
        # emulate the tuple shape used earlier
        return ("ignored", "ARCHIVE-TEXT-SYNC", {"excel": True, "archive": False, "sql": True})

    monkeypatch.setattr(pp, "run_stats_copy_archive", stats_sync_tuple)

    # Execute pipeline with minimal params. Many things are mocked to be no-ops.
    result = await pp.execute_processing_pipeline(
        1, seed=42, user=fake_user, filename="f.xlsx", channel_id=0, save_path=None
    )
    # result is (success_excel, success_archive, success_sql, success_export, success_proc_import, combined_log)
    assert isinstance(result, tuple)
    assert result[0] is True  # excel per steps
    assert result[1] is False
    assert result[2] is True

    # 4) Case: run_stats_copy_archive returns dict-form
    def stats_sync_dict(rank, seed, **kwargs):
        return {"archive": "ARCHIVE-DICT", "steps": {"excel": False, "archive": True, "sql": False}}

    monkeypatch.setattr(pp, "run_stats_copy_archive", stats_sync_dict)
    result2 = await pp.execute_processing_pipeline(
        1, seed=42, user=fake_user, filename="f2.xlsx", channel_id=0, save_path=None
    )
    assert isinstance(result2, tuple)
    assert result2[0] is False
    assert result2[1] is True
    assert result2[2] is False
