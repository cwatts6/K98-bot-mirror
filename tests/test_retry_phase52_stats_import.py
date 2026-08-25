from __future__ import annotations

import argparse

import pytest

from scripts import retry_phase52_stats_import as recovery

COMPLETED_FILENAME = "stats_0123456789abcdef0123456789abcdef.ready.csv"


def _args(**overrides) -> argparse.Namespace:
    values = {
        "completed_filename": COMPLETED_FILENAME,
        "rank": 1184.0,
        "seed": "B",
        "timeout_seconds": 600,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


@pytest.mark.asyncio
async def test_recovery_reuses_exact_manifest_identity(tmp_path, monkeypatch, capsys):
    ready_file = tmp_path / COMPLETED_FILENAME
    ready_file.write_text("Governor ID,Name\n1,Example\n", encoding="utf-8")
    metadata = {"completed_filename": COMPLETED_FILENAME, "publication_state": "sql_owned"}
    calls = []

    async def run_sql_procedure(**kwargs):
        calls.append(kwargs)
        return True, "[SUCCESS] Counter reached 913.", None

    monkeypatch.setattr(recovery.stats_module, "READY_DIR", str(tmp_path))
    monkeypatch.setattr(recovery.stats_module, "_load_import_metadata", lambda: metadata)
    monkeypatch.setattr(
        recovery.stats_module,
        "_resolve_completed_filename",
        lambda value: value["completed_filename"],
    )
    monkeypatch.setattr(recovery.stats_module, "run_sql_procedure", run_sql_procedure)

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
    metadata = {"completed_filename": COMPLETED_FILENAME, "publication_state": "sql_owned"}
    monkeypatch.setattr(recovery.stats_module, "_load_import_metadata", lambda: metadata)
    monkeypatch.setattr(
        recovery.stats_module,
        "_resolve_completed_filename",
        lambda value: value["completed_filename"],
    )

    assert await recovery._run(_args(completed_filename="stats_" + "a" * 32 + ".ready.csv")) == 2
    assert "RECOVERY REFUSED" in capsys.readouterr().err
