from __future__ import annotations

import argparse

import pytest

from scripts import retry_phase52_stats_import as recovery

COMPLETED_FILENAME = "stats_0123456789abcdef0123456789abcdef.ready.csv"


def _args(**overrides) -> argparse.Namespace:
    values = {
        "completed_filename": COMPLETED_FILENAME,
        "timeout_seconds": 600,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


@pytest.mark.asyncio
async def test_recovery_reuses_exact_manifest_identity(tmp_path, monkeypatch, capsys):
    ready_file = tmp_path / COMPLETED_FILENAME
    ready_file.write_text("Governor ID,Name\n1,Example\n", encoding="utf-8")
    metadata = {
        "completed_filename": COMPLETED_FILENAME,
        "publication_state": "sql_owned",
        "rank": 1184.0,
        "seed": "B",
    }
    calls = []

    async def run_sql_procedure(**kwargs):
        calls.append(kwargs)
        return True, "[SUCCESS] Counter reached 913.", None

    async def run_post_sql_stages(completed_filename):
        assert completed_filename == COMPLETED_FILENAME
        return True, "post-SQL stages completed"

    monkeypatch.setattr(recovery.stats_module, "READY_DIR", str(tmp_path))
    monkeypatch.setattr(recovery.stats_module, "_load_import_metadata", lambda: metadata)
    monkeypatch.setattr(
        recovery.stats_module,
        "_resolve_completed_filename",
        lambda value: value["completed_filename"],
    )
    monkeypatch.setattr(recovery.stats_module, "run_sql_procedure", run_sql_procedure)
    monkeypatch.setattr(recovery, "_run_required_post_sql_stages", run_post_sql_stages)

    assert await recovery._run(_args()) == 0
    assert calls == [
        {
            "rank": 1184.0,
            "seed": "B",
            "completed_filename": COMPLETED_FILENAME,
            "timeout_seconds": 600,
            "import_metadata": metadata,
        }
    ]
    assert "PHASE52_STATS_IMPORT_RECOVERY_COMPLETE" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_recovery_refuses_identity_other_than_manifest(monkeypatch, capsys):
    metadata = {
        "completed_filename": COMPLETED_FILENAME,
        "publication_state": "sql_owned",
        "rank": 1184.0,
        "seed": "B",
    }
    monkeypatch.setattr(recovery.stats_module, "_load_import_metadata", lambda: metadata)
    monkeypatch.setattr(
        recovery.stats_module,
        "_resolve_completed_filename",
        lambda value: value["completed_filename"],
    )

    assert await recovery._run(_args(completed_filename="stats_" + "a" * 32 + ".ready.csv")) == 2
    assert "RECOVERY REFUSED" in capsys.readouterr().err


@pytest.mark.asyncio
async def test_recovery_refuses_manifest_without_original_parameters(tmp_path, monkeypatch, capsys):
    ready_file = tmp_path / COMPLETED_FILENAME
    ready_file.write_text("Governor ID,Name\n1,Example\n", encoding="utf-8")
    metadata = {"completed_filename": COMPLETED_FILENAME, "publication_state": "sql_owned"}
    monkeypatch.setattr(recovery.stats_module, "READY_DIR", str(tmp_path))
    monkeypatch.setattr(recovery.stats_module, "_load_import_metadata", lambda: metadata)
    monkeypatch.setattr(
        recovery.stats_module,
        "_resolve_completed_filename",
        lambda value: value["completed_filename"],
    )

    assert await recovery._run(_args()) == 2
    assert "no original rank" in capsys.readouterr().err


@pytest.mark.asyncio
async def test_recovery_does_not_report_complete_when_post_sql_stage_fails(
    tmp_path, monkeypatch, capsys
):
    ready_file = tmp_path / COMPLETED_FILENAME
    ready_file.write_text("Governor ID,Name\n1,Example\n", encoding="utf-8")
    metadata = {
        "completed_filename": COMPLETED_FILENAME,
        "publication_state": "sql_owned",
        "rank": 1184,
        "seed": "B",
    }

    async def run_sql_procedure(**_kwargs):
        return True, "[SUCCESS] Counter reached 913.", None

    async def fail_post_sql_stages(_completed_filename):
        return False, "required post_stats maintenance failed"

    monkeypatch.setattr(recovery.stats_module, "READY_DIR", str(tmp_path))
    monkeypatch.setattr(recovery.stats_module, "_load_import_metadata", lambda: metadata)
    monkeypatch.setattr(
        recovery.stats_module,
        "_resolve_completed_filename",
        lambda value: value["completed_filename"],
    )
    monkeypatch.setattr(recovery.stats_module, "run_sql_procedure", run_sql_procedure)
    monkeypatch.setattr(recovery, "_run_required_post_sql_stages", fail_post_sql_stages)

    assert await recovery._run(_args()) == 1
    output = capsys.readouterr()
    assert "PHASE52_STATS_IMPORT_RECOVERY_COMPLETE" not in output.out
    assert "RECOVERY INCOMPLETE" in output.err


@pytest.mark.asyncio
async def test_required_post_sql_stages_rebuild_caches_and_run_maintenance(monkeypatch):
    calls = []

    async def build_player_cache():
        calls.append("player_cache")

    async def build_lastkvk_cache():
        calls.append("lastkvk_cache")

    async def run_maintenance(command, **kwargs):
        calls.append((command, kwargs))
        return True, "maintenance complete"

    monkeypatch.setattr(recovery, "build_player_stats_cache", build_player_cache)
    monkeypatch.setattr(recovery, "build_lastkvk_player_stats_cache", build_lastkvk_cache)
    monkeypatch.setattr(recovery, "run_maintenance_with_isolation", run_maintenance)

    success, message = await recovery._run_required_post_sql_stages(COMPLETED_FILENAME)

    assert success is True
    assert message == "maintenance complete"
    assert calls[:2] == ["player_cache", "lastkvk_cache"]
    assert calls[2][0] == recovery.POST_STATS_WORKER_SPEC
    assert "kwargs" not in calls[2][1]
    assert calls[2][1]["meta"] == {
        "completed_filename": COMPLETED_FILENAME,
        "recovery": True,
    }


def test_post_stats_wrapper_does_not_forward_configured_credentials(monkeypatch):
    calls = []
    monkeypatch.setattr(
        recovery,
        "run_post_import_stats_update",
        lambda *args: calls.append(args),
    )

    recovery._run_post_stats_without_argv_credentials()

    assert calls == [(recovery.SERVER, recovery.DATABASE, "", "")]


def test_post_stats_worker_spec_is_importable_outside_main_module():
    module_name, function_name = recovery.POST_STATS_WORKER_SPEC.split(":", 1)

    assert module_name == "scripts.retry_phase52_stats_import"
    assert getattr(__import__(module_name, fromlist=[function_name]), function_name) is not None
