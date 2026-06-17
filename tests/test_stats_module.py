# tests/test_stats_module.py
import asyncio
import csv

import pandas as pd
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


def test_process_excel_file_preserves_credit_before_updated_on(tmp_path, monkeypatch):
    source_path = tmp_path / "upload.xlsx"
    download_dir = tmp_path / "downloads"
    archive_dir = download_dir / "archive"
    download_dir.mkdir()

    pd.DataFrame(
        {
            "Governor ID": [123, 456],
            "Name": ["A", "B"],
            "Credit": [100, None],
        }
    ).to_excel(source_path, index=False)

    monkeypatch.setattr(stats_module, "DOWNLOAD_FOLDER", str(download_dir))
    monkeypatch.setattr(stats_module, "ARCHIVE_DIR_1", str(archive_dir))
    monkeypatch.setattr(stats_module, "CSV_FILE_PATH", str(download_dir / "stats.csv"))

    success, message, _ = stats_module.process_excel_file(str(source_path))

    assert success, message
    with open(stats_module.CSV_FILE_PATH, newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    assert float(rows[0]["Credit"]) == pytest.approx(100.0)
    assert rows[1]["Credit"] == ""
    assert list(rows[0]).index("Credit") < list(rows[0]).index("updated_on")


def test_process_excel_file_adds_blank_credit_for_legacy_upload(tmp_path, monkeypatch):
    source_path = tmp_path / "legacy.xlsx"
    download_dir = tmp_path / "downloads"
    archive_dir = download_dir / "archive"
    download_dir.mkdir()

    pd.DataFrame(
        {
            "Governor ID": [123],
            "Name": ["A"],
        }
    ).to_excel(source_path, index=False)

    monkeypatch.setattr(stats_module, "DOWNLOAD_FOLDER", str(download_dir))
    monkeypatch.setattr(stats_module, "ARCHIVE_DIR_1", str(archive_dir))
    monkeypatch.setattr(stats_module, "CSV_FILE_PATH", str(download_dir / "stats.csv"))

    success, message, _ = stats_module.process_excel_file(str(source_path))

    assert success, message
    with open(stats_module.CSV_FILE_PATH, newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    assert "Credit" in rows[0]
    assert rows[0]["Credit"] == ""
    assert list(rows[0]).index("Credit") < list(rows[0]).index("updated_on")
