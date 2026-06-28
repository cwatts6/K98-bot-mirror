# tests/test_stats_module.py
import asyncio
import csv

import pandas as pd
import pytest

import file_utils
import stats_module


def _full_upload_row(**overrides):
    row = {
        "Governor ID": 123,
        "Name": "A",
        "Power": 1000,
        "Alliance": "K98",
        "T1-Kills": 1,
        "T2-Kills": 2,
        "T3-Kills": 3,
        "T4-Kills": 4,
        "T5-Kills": 5,
        "Total Kill Points": 999,
        "Dead Troops": 10,
        "Healed Troops": 20,
        "Rss Assistance": 30,
        "Alliance Helps": 40,
        "Rss Gathered": 50,
        "City Hall": 25,
        "Troops Power": 60,
        "Tech Power": 70,
        "Building Power": 80,
        "Commander Power": 90,
        "Civilization": "Britain",
        "Autarch Times": 2,
        "Ranged Points": 77,
        "KvK Played": 3,
        "Most KvK Kill": 100,
        "Most KvK Dead": 200,
        "Most KvK Heal": 300,
        "Acclaim": 400,
        "Highest Acclaim": 500,
        "AOO Joined": 6,
        "AOO Won": 7,
        "AOO Avg Kill": 8,
        "AOO Avg Dead": 9,
        "AOO Avg Heal": 10,
    }
    row.update(overrides)
    return row


@pytest.mark.asyncio
async def test_run_stats_copy_archive_contract_monkeypatched(monkeypatch):
    """
    Ensure run_stats_copy_archive returns the canonical (bool, str, dict) contract
    even when internals are monkeypatched to avoid DB/file IO.
    """

    # Monkeypatch internal functions to avoid heavy IO / DB calls
    async def fake_run_sql_procedure(
        rank=None, seed=None, timeout_seconds=600, import_metadata=None
    ):
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


@pytest.mark.asyncio
async def test_run_stats_copy_archive_passes_only_current_import_metadata(monkeypatch):
    metadata_seen = []
    metadata_path = "stats_import_metadata.json"

    def fake_process_excel_file(path):
        return True, "[INFO] fake excel", None

    async def fake_run_sql_procedure(
        rank=None, seed=None, timeout_seconds=600, import_metadata=None
    ):
        metadata_seen.append(import_metadata)
        await asyncio.sleep(0)
        return True, "[SUCCESS] fake sql", None

    monkeypatch.setattr(stats_module, "process_excel_file", fake_process_excel_file)
    monkeypatch.setattr(stats_module, "archive_second_file", lambda: (True, "[INFO] archive", None))
    monkeypatch.setattr(stats_module, "run_sql_procedure", fake_run_sql_procedure)
    monkeypatch.setattr(
        stats_module,
        "_load_import_metadata",
        lambda: {"source_type": "full_fallback_snapshot", "source_filename": metadata_path},
    )

    success, _combined_log, _steps = await stats_module.run_stats_copy_archive(
        source_filename="upload.xlsx"
    )

    assert success is True
    assert metadata_seen == [
        {"source_type": "full_fallback_snapshot", "source_filename": metadata_path}
    ]


@pytest.mark.asyncio
async def test_run_stats_copy_archive_sql_only_does_not_reuse_stale_metadata(monkeypatch):
    metadata_seen = []

    async def fake_run_sql_procedure(
        rank=None, seed=None, timeout_seconds=600, import_metadata=None
    ):
        metadata_seen.append(import_metadata)
        await asyncio.sleep(0)
        return True, "[SUCCESS] fake sql", None

    monkeypatch.setattr(stats_module, "run_sql_procedure", fake_run_sql_procedure)
    monkeypatch.setattr(
        stats_module,
        "_load_import_metadata",
        lambda: {"source_type": "interim_auto_partial_snapshot"},
    )

    success, _combined_log, _steps = await stats_module.run_stats_copy_archive()

    assert success is True
    assert metadata_seen == [{}]


def test_process_excel_file_preserves_credit_before_updated_on(tmp_path, monkeypatch):
    source_path = tmp_path / "upload.xlsx"
    download_dir = tmp_path / "downloads"
    archive_dir = download_dir / "archive"
    download_dir.mkdir()

    pd.DataFrame(
        [
            _full_upload_row(**{"Governor ID": 123, "Name": "A", "Credit": 100}),
            _full_upload_row(**{"Governor ID": 456, "Name": "B", "Credit": None}),
        ]
    ).to_excel(source_path, index=False)

    monkeypatch.setattr(stats_module, "DOWNLOAD_FOLDER", str(download_dir))
    monkeypatch.setattr(stats_module, "ARCHIVE_DIR_1", str(archive_dir))
    monkeypatch.setattr(stats_module, "CSV_FILE_PATH", str(download_dir / "stats.csv"))
    monkeypatch.setattr(
        stats_module, "IMPORT_METADATA_FILE_PATH", str(download_dir / "stats_import_metadata.json")
    )

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

    pd.DataFrame([_full_upload_row()]).to_excel(source_path, index=False)

    monkeypatch.setattr(stats_module, "DOWNLOAD_FOLDER", str(download_dir))
    monkeypatch.setattr(stats_module, "ARCHIVE_DIR_1", str(archive_dir))
    monkeypatch.setattr(stats_module, "CSV_FILE_PATH", str(download_dir / "stats.csv"))
    monkeypatch.setattr(
        stats_module, "IMPORT_METADATA_FILE_PATH", str(download_dir / "stats_import_metadata.json")
    )

    success, message, _ = stats_module.process_excel_file(str(source_path))

    assert success, message
    with open(stats_module.CSV_FILE_PATH, newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    assert "Credit" in rows[0]
    assert rows[0]["Credit"] == ""
    assert list(rows[0]).index("Credit") < list(rows[0]).index("updated_on")


def test_process_excel_file_maps_conduct_score_to_credit(tmp_path, monkeypatch):
    source_path = tmp_path / "conduct.xlsx"
    download_dir = tmp_path / "downloads"
    archive_dir = download_dir / "archive"
    download_dir.mkdir()

    pd.DataFrame([_full_upload_row(**{"Conduct Score": 91.25})]).to_excel(source_path, index=False)

    monkeypatch.setattr(stats_module, "DOWNLOAD_FOLDER", str(download_dir))
    monkeypatch.setattr(stats_module, "ARCHIVE_DIR_1", str(archive_dir))
    monkeypatch.setattr(stats_module, "CSV_FILE_PATH", str(download_dir / "stats.csv"))
    monkeypatch.setattr(
        stats_module, "IMPORT_METADATA_FILE_PATH", str(download_dir / "stats_import_metadata.json")
    )

    success, message, _ = stats_module.process_excel_file(str(source_path))

    assert success, message
    with open(stats_module.CSV_FILE_PATH, newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    assert "Conduct Score" not in rows[0]
    assert float(rows[0]["Credit"]) == pytest.approx(91.25)
