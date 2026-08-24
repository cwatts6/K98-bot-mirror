import asyncio
import copy

import pytest

# Ensure pytest-asyncio is used for async tests
pytestmark = pytest.mark.asyncio


async def test_load_offload_and_preload(monkeypatch):
    """
    Ensure CrystalTechService.load uses the service-level offload helper path and
    preloads progress. We monkeypatch crystaltech_service._offload_sync_call so
    the service uses our fake offload which simulates latency then calls the
    underlying sync function.
    """
    from crystaltech_config import ValidationReport
    import crystaltech_service
    from crystaltech_service import CrystalTechService

    calls = {"offload": 0, "cfg_load": 0, "prog_load": 0}

    # Fake sync loader for config
    def fake_load_and_validate_config(path, assets_dir, fail_on_warn=False):
        calls["cfg_load"] += 1
        return ({"paths": []}, ValidationReport(ok=True, issues=[]))

    # Fake sync loader for progress file
    def fake_load_progress_file(path):
        calls["prog_load"] += 1
        return {"kvk_no": None, "updated_at_utc": None, "entries": []}

    # Fake offload helper: simulate latency and then invoke the callable
    async def fake_offload(func, *args, name=None, prefer_process=True, meta=None):
        calls["offload"] += 1
        # small sleep to emulate work
        await asyncio.sleep(0.01)
        # func is expected to be a callable (the sync functions we patched into crystaltech_service)
        return func(*args)

    # Patch the functions on the crystaltech_service module (where svc.load references them)
    monkeypatch.setattr(
        crystaltech_service, "load_and_validate_config", fake_load_and_validate_config
    )
    monkeypatch.setattr(crystaltech_service, "load_progress_file", fake_load_progress_file)
    # Patch the offload helper used by the service
    monkeypatch.setattr(crystaltech_service, "_offload_sync_call", fake_offload)

    svc = CrystalTechService()
    # Run load with a timeout to ensure we don't block the loop
    report = await asyncio.wait_for(svc.load(fail_on_warn=False), timeout=2.0)
    assert svc.cfg() == {"paths": []}
    assert isinstance(report, ValidationReport)
    assert calls["offload"] >= 1
    assert calls["cfg_load"] == 1
    assert calls["prog_load"] == 1


async def test_concurrent_save_progress_merges_updates(monkeypatch):
    """
    Run two concurrent save_progress calls for the same governor_id with disjoint
    newly_completed_uids and verify the merged saved entry contains the union.
    """
    import crystaltech_service
    from crystaltech_service import CrystalTechService

    persisted = []

    async def fake_offload(func, *args, name=None, prefer_process=True, meta=None):
        # capture persist attempts invoked via save_crystaltech_progress name
        if name == "save_crystaltech_progress":
            # args: (payload, path)
            payload = copy.deepcopy(args[0]) if args else None
            persisted.append(payload)
            return None
        # otherwise, attempt to call the function if possible
        try:
            return func(*args)
        except Exception:
            return None

    monkeypatch.setattr(crystaltech_service, "_offload_sync_call", fake_offload)

    svc = CrystalTechService()
    # Provide a minimal valid cfg so validate_path_id_or_hint won't error
    svc._cfg = {"paths": [{"path_id": "p1"}]}
    svc._progress_cache = {"kvk_no": 14, "updated_at_utc": None, "entries": []}

    async def do_save(uids):
        await svc.save_progress(
            governor_id="G1", path_id="p1", troop_type="infantry", newly_completed_uids=uids
        )

    await asyncio.gather(do_save(["a"]), do_save(["b"]))

    # Confirm in-memory entry merged both uids
    entries = svc._progress_cache["entries"]
    entry = next((e for e in entries if e.get("governor_id") == "G1"), None)
    assert entry is not None
    assert set(entry.get("steps_completed") or []) == {"a", "b"}
    assert persisted, "Persist calls not captured"


async def test_archive_and_reset_all_writes_archive_and_resets_cache(monkeypatch, tmp_path):
    """
    Ensure archive_and_reset_all invokes offload read/write and resets the in-memory cache.
    """
    import crystaltech_service
    from crystaltech_service import CrystalTechService

    calls = {"reads": [], "writes": [], "saves": []}

    async def fake_offload(func, *args, name=None, prefer_process=True, meta=None):
        if name == "read_crystaltech_progress_for_archive":
            calls["reads"].append(args)
            return {
                "kvk_no": 14,
                "updated_at_utc": None,
                "entries": [{"governor_id": "G1", "steps_completed": ["x"]}],
            }
        if name == "write_crystaltech_archive":
            calls["writes"].append(args)
            return None
        if name == "save_crystaltech_progress":
            calls["saves"].append(copy.deepcopy(args[0] if args else None))
            return None
        try:
            return func(*args)
        except Exception:
            return None

    monkeypatch.setattr(crystaltech_service, "_offload_sync_call", fake_offload)

    svc = CrystalTechService()
    svc._progress_cache = {
        "kvk_no": 14,
        "updated_at_utc": None,
        "entries": [{"governor_id": "G1", "steps_completed": ["x"]}],
    }

    # Await without assigning to unused local variable (fixes F841)
    await svc.archive_and_reset_all(next_kvk_no=15)

    # Confirm reset to next_kvk_no and entries cleared
    assert svc._progress_cache["kvk_no"] == 15
    assert svc._progress_cache["entries"] == []
    assert calls["reads"], "Archive read not recorded"
    assert calls["writes"], "Archive write not recorded"
