# tests/test_stats_module.py
import asyncio

import pytest

import file_utils
import stats_module


@pytest.mark.asyncio
async def test_run_stats_copy_archive_contract_monkeypatched(monkeypatch):
    """
    Ensure run_stats_copy_archive returns the canonical (bool, str, dict) contract
    even when internals are monkeypatched to avoid DB/file IO.
    """

    # Monkeypatch internal functions to avoid heavy IO / DB calls
    async def fake_run_sql_procedure(rank=None, seed=None, timeout_seconds=600):
        await asyncio.sleep(0)
        return True, "[SUCCESS] fake sql", None

    def fake_process_excel_file(path):
        return True, "[INFO] fake excel", None

    def fake_archive_second_file():
        return True, "[INFO] fake archive2", None

    async def fake_run_blocking_in_thread(func, *args, **kwargs):
        # For test simplicity: call the underlying sync function directly (sync) but keep async signature
        await asyncio.sleep(0)
        return func(*args, **kwargs)

    monkeypatch.setattr(stats_module, "run_sql_procedure", fake_run_sql_procedure)
    monkeypatch.setattr(stats_module, "process_excel_file", fake_process_excel_file)
    monkeypatch.setattr(stats_module, "archive_second_file", fake_archive_second_file)
    monkeypatch.setattr(file_utils, "run_blocking_in_thread", fake_run_blocking_in_thread)

    # Call with a fake source filename so the excel branch executes
    success, combined_log, steps = await stats_module.run_stats_copy_archive(
        rank=1, seed=2, source_filename="fake.xlsx"
    )

    assert isinstance(success, bool)
    assert isinstance(combined_log, str)
    assert isinstance(steps, dict)

    # Expect canonical keys to exist
    assert "excel" in steps and "archive" in steps and "sql" in steps
