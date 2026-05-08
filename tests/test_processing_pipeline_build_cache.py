# tests/test_processing_pipeline_build_cache.py
import time
import types

import pytest

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_build_player_stats_cache_offloaded_and_completes(monkeypatch):
    """
    Verify build_player_stats_cache is run via run_step (offloaded) and completes within timeout.
    """
    import processing_pipeline as pp

    # Ensure module-level timeout is set for this test (monkeypatch the module constant)
    monkeypatch.setattr(pp, "BUILD_CACHE_TIMEOUT", 2.0)

    called = {"ran": False}

    # Replace heavy functions used by pipeline so execute_processing_pipeline is lightweight
    async def fake_send_embed_safe(*args, **kwargs):
        return True

    monkeypatch.setattr(pp, "send_embed_safe", fake_send_embed_safe)
    monkeypatch.setattr(pp, "run_all_exports", lambda *a, **k: (True, "OK"))
    monkeypatch.setattr(pp, "run_maintenance_with_isolation", lambda *a, **k: (True, "OK"))

    # warm_name_cache / warm_target_cache must be async (processing_pipeline awaits them)
    async def fake_warm_name_cache():
        return None

    async def fake_warm_target_cache():
        return None

    monkeypatch.setattr(pp, "warm_name_cache", fake_warm_name_cache)
    monkeypatch.setattr(pp, "warm_target_cache", fake_warm_target_cache)
    monkeypatch.setattr(pp, "get_channel_safe", lambda *a, **k: None)

    # Replace run_stats_copy_archive with a stub that indicates SQL ran successfully
    def fake_run_stats_copy_archive(rank, seed, **kwargs):
        # shape: (_, out_archive, steps)
        return (None, "FAKE_ARCHIVE", {"excel": True, "archive": True, "sql": True})

    monkeypatch.setattr(pp, "run_stats_copy_archive", fake_run_stats_copy_archive)

    # Replace build_player_stats_cache with a sync function that marks called and sleeps a bit
    def fake_build_cache():
        called["ran"] = True
        # Sleep a short time to simulate work
        time.sleep(0.05)
        return None

    monkeypatch.setattr(pp, "build_player_stats_cache", fake_build_cache)

    # Patch log_processing_result to avoid network calls in tests (bot.fetch_user / DM)
    async def fake_log_processing_result(*args, **kwargs):
        return None

    monkeypatch.setattr(pp, "log_processing_result", fake_log_processing_result)

    # Prepare fake user and message objects required by handle_file_processing
    class FakeAuthor:
        id = 999
        name = "Fake#0001"  # ensure .name exists

        def __str__(self):
            return "Fake#0001"

    class FakeChannel:
        id = 0
        name = "test"

    class FakeMessage:
        def __init__(self):
            self.channel = FakeChannel()
            self.author = FakeAuthor()
            self.id = 1

        async def delete(self):
            pass

    # Monkeypatch prompt_admin_inputs to return rank/seed as an async function
    async def fake_prompt_admin_inputs(bot, user, admin_id):
        return (1, 42)

    monkeypatch.setattr(pp, "prompt_admin_inputs", fake_prompt_admin_inputs)

    # Monkeypatch load_cached_input to return minimal cache
    monkeypatch.setattr(
        pp, "load_cached_input", lambda *a, **k: {"date": pp.utcnow().date().isoformat()}
    )

    fake_user = types.SimpleNamespace(id=1234)
    fake_msg = FakeMessage()

    # Run handle_file_processing -> it will call execute_processing_pipeline which should offload build cache
    await pp.handle_file_processing(fake_user, fake_msg, "dummy.xlsx", save_path=None)

    assert called["ran"] is True


@pytest.mark.asyncio
async def test_build_player_stats_cache_timeout_handled(monkeypatch):
    """
    Validate pipeline handles build_player_stats_cache timeouts gracefully (does not raise),
    and telemetry_logger gets an entry about timeout.
    """
    import processing_pipeline as pp

    # Set tiny build timeout so the await will Timeout (monkeypatch the module constant)
    monkeypatch.setattr(pp, "BUILD_CACHE_TIMEOUT", 0.05)

    # Setup: heavy mocks to keep pipeline light
    async def fake_send_embed_safe(*a, **k):
        return True

    monkeypatch.setattr(pp, "send_embed_safe", fake_send_embed_safe)
    monkeypatch.setattr(pp, "run_all_exports", lambda *a, **k: (True, "OK"))
    monkeypatch.setattr(pp, "run_maintenance_with_isolation", lambda *a, **k: (True, "OK"))

    async def fake_warm_name_cache():
        return None

    async def fake_warm_target_cache():
        return None

    monkeypatch.setattr(pp, "warm_name_cache", fake_warm_name_cache)
    monkeypatch.setattr(pp, "warm_target_cache", fake_warm_target_cache)
    monkeypatch.setattr(pp, "get_channel_safe", lambda *a, **k: None)

    # Ensure the pipeline thinks SQL ran so cache build code executes
    def fake_run_stats_copy_archive(rank, seed, **kwargs):
        return (None, "FAKE_ARCHIVE", {"excel": True, "archive": True, "sql": True})

    monkeypatch.setattr(pp, "run_stats_copy_archive", fake_run_stats_copy_archive)

    # build_player_stats_cache will sleep longer than timeout (sync function)
    def slow_build():
        time.sleep(0.5)
        return None

    monkeypatch.setattr(pp, "build_player_stats_cache", slow_build)

    # Capture telemetry_logger.info calls
    calls = []

    def fake_telemetry_info(arg):
        calls.append(arg)

    monkeypatch.setattr(pp.telemetry_logger, "info", fake_telemetry_info)

    # Minimal pipeline invocation via handle_file_processing with mocked dependencies further
    async def fake_prompt_admin_inputs(bot, user, admin_id):
        return (1, 42)

    monkeypatch.setattr(pp, "prompt_admin_inputs", fake_prompt_admin_inputs)
    monkeypatch.setattr(pp, "load_cached_input", lambda *a, **k: None)

    # Patch log_processing_result to avoid network calls in tests (bot.fetch_user / DM)
    async def fake_log_processing_result(*args, **kwargs):
        return None

    monkeypatch.setattr(pp, "log_processing_result", fake_log_processing_result)

    fake_user = types.SimpleNamespace(id=1234)

    # Build a minimal fake message/channel used by handle_file_processing
    class FakeAuthor:
        id = 999
        name = "Fake#0001"

        def __str__(self):
            return "Fake#0001"

    class FakeChannel:
        id = 0
        name = "test"

    class FakeMessage:
        def __init__(self):
            self.channel = FakeChannel()
            self.author = FakeAuthor()
            self.id = 1

        async def delete(self):
            pass

    fake_msg = FakeMessage()

    # Run the pipeline; it should not raise despite the build timeout
    await pp.handle_file_processing(fake_user, fake_msg, "dummy2.xlsx", save_path=None)

    # Assert telemetry_logger.info was called with cache_build_timeout or cache_build_failed marker
    found = any("cache_build_timeout" in str(c) or "cache_build_failed" in str(c) for c in calls)
    assert found, f"Expected telemetry about cache build timeout/failure, got calls: {calls}"
