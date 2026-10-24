import pytest

import proc_config_import as pci


@pytest.mark.asyncio
@pytest.mark.parametrize("success", [False, True])
async def test_process_envelope_preserves_import_status(monkeypatch, success):
    calls = []

    def importer(dry_run):
        calls.append(dry_run)
        return success, {"success": success, "tables": {"fixture": "x" * 2000}}

    async def isolation(fn, args, **kwargs):
        result = fn(*args)
        return list(result), {"result": list(result)}

    monkeypatch.setattr(pci, "run_proc_config_import", importer)
    monkeypatch.setattr(pci, "run_maintenance_with_isolation", isolation, raising=False)
    ok, report = await pci.run_proc_config_import_offload(dry_run=True)
    assert ok is success
    assert report["success"] is success
    assert report["report_summary"] is True
    assert calls == [True]


@pytest.mark.asyncio
async def test_unknown_worker_outcome_does_not_retry(monkeypatch):
    calls = []

    async def isolation(*args, **kwargs):
        calls.append(1)
        return True, "truncated output"

    monkeypatch.setattr(pci, "run_maintenance_with_isolation", isolation, raising=False)
    ok, report = await pci.run_proc_config_import_offload()
    assert ok is False
    assert report["errors"]
    assert calls == [1]
