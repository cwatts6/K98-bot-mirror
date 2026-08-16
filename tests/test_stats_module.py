# tests/test_stats_module.py
import asyncio
import csv
from pathlib import Path

import pandas as pd
import pytest

import file_utils
from stats.dal.immutable_import_dal import ImmutableImportOutcome
import stats_module

COMPLETED_FILENAME = "stats_0123456789abcdef0123456789abcdef.ready.csv"


def _published_metadata(**values):
    return {
        "publication_manifest_version": 1,
        "completed_filename": COMPLETED_FILENAME,
        "publication_state": "published",
        **values,
    }


@pytest.fixture(autouse=True)
def _disable_import_audit(monkeypatch):
    monkeypatch.setattr(
        stats_module.import_audit_service,
        "start_batch_best_effort",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        stats_module.import_audit_service,
        "record_phase_best_effort",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        stats_module.import_audit_service,
        "complete_batch_best_effort",
        lambda *args, **kwargs: False,
    )
    monkeypatch.setattr(
        stats_module.import_audit_service,
        "fail_batch_best_effort",
        lambda *args, **kwargs: False,
    )


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


def test_fallback_archive_configuration_separates_original_and_normalized_workbooks():
    assert Path(stats_module.ARCHIVE_DIR_2) == Path(stats_module.ARCHIVE_DIR_1) / "Normalized"
    assert "Import_Archive" not in Path(stats_module.ARCHIVE_DIR_2).parts


@pytest.mark.asyncio
async def test_run_stats_copy_archive_contract_monkeypatched(monkeypatch):
    """
    Ensure run_stats_copy_archive returns the canonical (bool, str, dict) contract
    even when internals are monkeypatched to avoid DB/file IO.
    """

    # Monkeypatch internal functions to avoid heavy IO / DB calls
    async def fake_run_sql_procedure(
        rank=None, seed=None, timeout_seconds=600, import_metadata=None, **kwargs
    ):
        import_metadata["_fallback_import_control_id"] = 456
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
    monkeypatch.setattr(stats_module, "_load_import_metadata", _published_metadata)

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
        rank=None, seed=None, timeout_seconds=600, import_metadata=None, **kwargs
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
        lambda: _published_metadata(
            source_type="full_fallback_snapshot", source_filename=metadata_path
        ),
    )

    success, _combined_log, _steps = await stats_module.run_stats_copy_archive(
        source_filename="upload.xlsx"
    )

    assert success is True
    assert metadata_seen == [
        _published_metadata(source_type="full_fallback_snapshot", source_filename=metadata_path)
    ]


@pytest.mark.asyncio
async def test_run_stats_copy_archive_sql_only_fails_closed_for_stale_metadata(monkeypatch):
    metadata_seen = []

    async def fake_run_sql_procedure(
        rank=None, seed=None, timeout_seconds=600, import_metadata=None, **kwargs
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

    assert success is False
    assert metadata_seen == []


@pytest.mark.asyncio
async def test_run_stats_copy_archive_records_best_effort_audit(monkeypatch):
    audit_calls = []

    def fake_start(**kwargs):
        audit_calls.append(("start", kwargs))
        return 123

    def fake_phase(batch_ref, **kwargs):
        audit_calls.append(("phase", batch_ref, kwargs))
        return 1

    def fake_complete(batch_ref, **kwargs):
        audit_calls.append(("complete", batch_ref, kwargs))
        return True

    def fake_fail(batch_ref, **kwargs):
        audit_calls.append(("fail", batch_ref, kwargs))
        return True

    def fake_process_excel_file(path):
        return True, "[INFO] fake excel", None

    async def fake_run_sql_procedure(
        rank=None, seed=None, timeout_seconds=600, import_metadata=None, **kwargs
    ):
        import_metadata["_fallback_import_control_id"] = 456
        await asyncio.sleep(0)
        return True, "[SUCCESS] fake sql", None

    monkeypatch.setattr(stats_module.import_audit_service, "start_batch_best_effort", fake_start)
    monkeypatch.setattr(stats_module.import_audit_service, "record_phase_best_effort", fake_phase)
    monkeypatch.setattr(
        stats_module.import_audit_service, "complete_batch_best_effort", fake_complete
    )
    monkeypatch.setattr(stats_module.import_audit_service, "fail_batch_best_effort", fake_fail)
    monkeypatch.setattr(stats_module, "process_excel_file", fake_process_excel_file)
    monkeypatch.setattr(stats_module, "archive_second_file", lambda: (True, "[INFO] archive", None))
    monkeypatch.setattr(stats_module, "run_sql_procedure", fake_run_sql_procedure)
    monkeypatch.setattr(
        stats_module,
        "_load_import_metadata",
        lambda: _published_metadata(
            source_type="full_fallback_snapshot", rows_in_source=3, rows_written=3
        ),
    )

    success, _combined_log, steps = await stats_module.run_stats_copy_archive(
        rank=1, seed=2, source_filename="upload.xlsx"
    )

    assert success is True
    assert steps == {"excel": True, "archive": True, "sql": True}
    assert audit_calls[0][0] == "start"
    phase_names = [call[2]["phase_name"] for call in audit_calls if call[0] == "phase"]
    assert phase_names == [
        "fallback_file_prepare",
        "fallback_secondary_archive",
        "fallback_update_all2",
    ]
    assert audit_calls[-1][0] == "complete"
    assert audit_calls[-1][2]["rows_in_source"] == 3
    assert audit_calls[-1][2]["external_batch_table"] == "dbo.FallbackImportBatchControl"
    assert audit_calls[-1][2]["external_batch_id"] == "456"
    assert not any(call[0] == "fail" for call in audit_calls)


@pytest.mark.asyncio
async def test_run_stats_copy_archive_uses_stdout_failure_message(monkeypatch):
    audit_calls = []
    monkeypatch.setattr(stats_module, "_load_import_metadata", _published_metadata)

    monkeypatch.setattr(
        stats_module.import_audit_service,
        "start_batch_best_effort",
        lambda **kwargs: 123,
    )
    monkeypatch.setattr(
        stats_module.import_audit_service,
        "record_phase_best_effort",
        lambda batch_ref, **kwargs: audit_calls.append(("phase", kwargs)),
    )
    monkeypatch.setattr(
        stats_module.import_audit_service,
        "fail_batch_best_effort",
        lambda batch_ref, **kwargs: audit_calls.append(("fail", kwargs)),
    )

    async def fake_run_sql_procedure(
        rank=None, seed=None, timeout_seconds=600, import_metadata=None, **kwargs
    ):
        await asyncio.sleep(0)
        return False, "[TIMEOUT] fake timeout", None

    monkeypatch.setattr(stats_module, "run_sql_procedure", fake_run_sql_procedure)

    success, combined_log, _steps = await stats_module.run_stats_copy_archive()

    assert success is False
    assert "[TIMEOUT] fake timeout" in combined_log
    sql_phase = next(
        call[1]
        for call in audit_calls
        if call[0] == "phase" and call[1]["phase_name"] == "fallback_update_all2"
    )
    assert sql_phase["details"]["message"] == "[TIMEOUT] fake timeout"
    assert audit_calls[-1][0] == "fail"
    assert "[TIMEOUT] fake timeout" in audit_calls[-1][1]["error_text"]


@pytest.mark.asyncio
async def test_run_stats_copy_archive_records_update_all2_subphase_audit(monkeypatch):
    audit_calls = []
    offload_metas = []
    monkeypatch.setattr(stats_module, "_load_import_metadata", _published_metadata)

    monkeypatch.setattr(
        stats_module.import_audit_service,
        "start_batch_best_effort",
        lambda **kwargs: 123,
    )
    monkeypatch.setattr(
        stats_module.import_audit_service,
        "record_phase_best_effort",
        lambda batch_ref, **kwargs: audit_calls.append(("phase", kwargs)),
    )
    monkeypatch.setattr(
        stats_module.import_audit_service,
        "complete_batch_best_effort",
        lambda batch_ref, **kwargs: audit_calls.append(("complete", kwargs)),
    )

    async def direct_offload(fn, *args, name=None, meta=None):
        offload_metas.append((name, meta))
        return fn(*args)

    monkeypatch.setattr(stats_module, "_offload_callable_py", direct_offload)

    async def fake_run_sql_procedure(
        rank=None, seed=None, timeout_seconds=600, import_metadata=None, **kwargs
    ):
        import_metadata["_update_all2_phase_results"] = [
            {
                "phase_name": b"update_all2_create_averages",
                "phase_status": "completed",
                "duration_ms": 42,
                "details_json": '{"procedure": "CREATE_THE_AVERAGES"}',
            }
        ]
        await asyncio.sleep(0)
        return True, "[SUCCESS] fake sql", None

    monkeypatch.setattr(stats_module, "run_sql_procedure", fake_run_sql_procedure)

    success, _combined_log, _steps = await stats_module.run_stats_copy_archive()

    assert success is True
    phase_calls = [call[1] for call in audit_calls if call[0] == "phase"]
    phase_names = [call["phase_name"] for call in phase_calls]
    assert "fallback_update_all2" in phase_names
    assert "b'update_all2_create_averages'" in phase_names
    subphase = next(
        call for call in phase_calls if call["phase_name"] == "b'update_all2_create_averages'"
    )
    assert subphase["duration_ms"] == 42
    assert subphase["details"]["sql_phase"] == "b'update_all2_create_averages'"
    assert subphase["details"]["sql_details"] == {"procedure": "CREATE_THE_AVERAGES"}
    subphase_meta = next(
        meta for name, meta in offload_metas if name == "import_audit_update_all2_phase"
    )
    assert subphase_meta["phase"] == "b'update_all2_create_averages'"
    assert isinstance(subphase_meta["phase"], str)
    complete = next(call[1] for call in audit_calls if call[0] == "complete")
    assert "_update_all2_phase_results" not in complete["details"]


@pytest.mark.asyncio
async def test_run_stats_copy_archive_marks_audit_cancelled(monkeypatch):
    audit_calls = []
    monkeypatch.setattr(stats_module, "_load_import_metadata", _published_metadata)

    monkeypatch.setattr(
        stats_module.import_audit_service,
        "start_batch_best_effort",
        lambda **kwargs: 123,
    )
    monkeypatch.setattr(
        stats_module.import_audit_service,
        "record_phase_best_effort",
        lambda batch_ref, **kwargs: audit_calls.append(("phase", kwargs)),
    )
    monkeypatch.setattr(
        stats_module.import_audit_service,
        "fail_batch_best_effort",
        lambda batch_ref, **kwargs: audit_calls.append(("fail", kwargs)),
    )

    async def fake_run_sql_procedure(
        rank=None, seed=None, timeout_seconds=600, import_metadata=None, **kwargs
    ):
        await asyncio.sleep(0)
        raise asyncio.CancelledError

    monkeypatch.setattr(stats_module, "run_sql_procedure", fake_run_sql_procedure)

    with pytest.raises(asyncio.CancelledError):
        await stats_module.run_stats_copy_archive()

    assert audit_calls[-1][0] == "fail"
    assert audit_calls[-1][1]["status"] == "cancelled"
    assert audit_calls[-1][1]["error_type"] == "FallbackImportCancelled"


@pytest.mark.asyncio
async def test_run_sql_procedure_does_not_publish_uncommitted_control_id(monkeypatch):
    class FakeCursor:
        timeout = 0

    class FakeConnection:
        autocommit = False

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def cursor(self):
            return FakeCursor()

    async def direct_offload(fn, *args, **kwargs):
        return fn(*args)

    def failing_update_all2(cur, param1=None, param2=None, **kwargs):
        raise RuntimeError("update failed")

    metadata = {"source_type": "full_fallback_snapshot"}

    monkeypatch.setattr(stats_module, "_offload_callable_py", direct_offload)
    monkeypatch.setattr(stats_module, "_conn_trusted", lambda: FakeConnection())
    monkeypatch.setattr(stats_module, "fetch_update_all2_last_counter", lambda cur, task: 0)
    monkeypatch.setattr(stats_module, "_record_fallback_import_control", lambda cur, meta: 456)
    monkeypatch.setattr(stats_module, "_set_import_metadata_state", lambda meta, state: None)
    monkeypatch.setattr(stats_module, "_fetch_immutable_import_outcome", lambda name: None)
    monkeypatch.setattr(
        stats_module,
        "execute_update_all2_with_log_management",
        failing_update_all2,
    )

    success, message, _extra = await stats_module.run_sql_procedure(
        completed_filename=COMPLETED_FILENAME,
        import_metadata=metadata,
    )

    assert success is False
    assert "update failed" in message
    assert "_fallback_import_control_id" not in metadata


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("outcome", "message_fragment"),
    [
        (
            ImmutableImportOutcome(
                completed_filename=COMPLETED_FILENAME,
                claim_status="duplicate_archived",
                file_digest_hex="AA" * 32,
                scan_order=None,
                archive_status=None,
            ),
            "duplicate content",
        ),
        (
            ImmutableImportOutcome(
                completed_filename=COMPLETED_FILENAME,
                claim_status="archived",
                file_digest_hex="BB" * 32,
                scan_order=42,
                archive_status="archived",
            ),
            "archived terminal state",
        ),
    ],
)
async def test_run_sql_procedure_reconciles_terminal_identity_without_retry(
    monkeypatch, outcome, message_fragment
):
    deleted = []

    class FakeCursor:
        timeout = 0

    class FakeConnection:
        autocommit = False

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def cursor(self):
            return FakeCursor()

    async def direct_offload(fn, *args, **kwargs):
        return fn(*args)

    monkeypatch.setattr(stats_module, "_offload_callable_py", direct_offload)
    monkeypatch.setattr(stats_module, "_conn_trusted", lambda: FakeConnection())
    monkeypatch.setattr(stats_module, "fetch_update_all2_last_counter", lambda cur, task: 0)
    monkeypatch.setattr(stats_module, "_record_fallback_import_control", lambda cur, meta: 456)
    monkeypatch.setattr(
        stats_module,
        "execute_update_all2_with_log_management",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("connection lost")),
    )
    monkeypatch.setattr(stats_module, "_fetch_immutable_import_outcome", lambda name: outcome)
    monkeypatch.setattr(stats_module, "_delete_import_metadata", lambda: deleted.append(True))

    success, message, _extra = await stats_module.run_sql_procedure(
        completed_filename=COMPLETED_FILENAME,
        import_metadata=_published_metadata(),
    )

    assert success is False
    assert message_fragment in message
    assert deleted == [True]


@pytest.mark.asyncio
async def test_run_sql_procedure_binds_exact_completed_filename_and_consumes_manifest(monkeypatch):
    wrapper_calls = []
    deleted = []

    class FakeCursor:
        timeout = 0

        def fetchall(self):
            return []

        def nextset(self):
            return False

    class FakeConnection:
        autocommit = False

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def cursor(self):
            return FakeCursor()

        def commit(self):
            return None

    async def direct_offload(fn, *args, **kwargs):
        return fn(*args)

    def execute_wrapper(cur, *, param1, param2, completed_filename):
        wrapper_calls.append((param1, param2, completed_filename))
        return {
            "success": True,
            "phase_results": [],
            "trigger_results": {},
            "log_before": 1.0,
            "log_after": 1.0,
        }

    metadata = _published_metadata(source_type="full_fallback_snapshot")
    monkeypatch.setattr(stats_module, "_offload_callable_py", direct_offload)
    monkeypatch.setattr(stats_module, "_conn_trusted", lambda: FakeConnection())
    monkeypatch.setattr(stats_module, "fetch_update_all2_last_counter", lambda cur, task: 7)
    monkeypatch.setattr(stats_module, "_record_fallback_import_control", lambda cur, meta: 456)
    monkeypatch.setattr(stats_module, "execute_update_all2_with_log_management", execute_wrapper)
    monkeypatch.setattr(stats_module, "_set_import_metadata_state", lambda meta, state: None)
    monkeypatch.setattr(stats_module, "_delete_import_metadata", lambda: deleted.append(True))
    monkeypatch.setattr(
        stats_module,
        "fetch_update_all2_status",
        lambda conn_factory, task: {"LastRunCounter": 8, "DurationSeconds": 1},
    )
    monkeypatch.setattr(stats_module, "WAIT_SECONDS", 0)
    monkeypatch.setattr(stats_module, "MAX_RETRIES", 1)

    success, message, _extra = await stats_module.run_sql_procedure(
        rank=1,
        seed="A",
        completed_filename=COMPLETED_FILENAME,
        import_metadata=metadata,
    )

    assert success is True
    assert "Counter reached 8" in message
    assert wrapper_calls == [(1, "A", COMPLETED_FILENAME)]
    assert deleted == [True]
    assert metadata["_fallback_import_control_id"] == 456


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
    monkeypatch.setattr(stats_module, "READY_DIR", str(download_dir / "Import_Ready"))
    monkeypatch.setattr(
        stats_module, "IMPORT_METADATA_FILE_PATH", str(download_dir / "stats_import_metadata.json")
    )

    success, message, _ = stats_module.process_excel_file(str(source_path))

    assert success, message
    manifest = stats_module._load_import_metadata()
    with open(
        Path(stats_module.READY_DIR) / manifest["completed_filename"],
        newline="",
        encoding="utf-8-sig",
    ) as handle:
        rows = list(csv.DictReader(handle))

    assert float(rows[0]["Credit"]) == pytest.approx(100.0)
    assert rows[1]["Credit"] == ""
    assert list(rows[0]).index("Credit") < list(rows[0]).index("updated_on")


def test_process_excel_file_adds_blank_credit_when_score_column_missing(tmp_path, monkeypatch):
    source_path = tmp_path / "legacy.xlsx"
    download_dir = tmp_path / "downloads"
    archive_dir = download_dir / "archive"
    download_dir.mkdir()

    pd.DataFrame([_full_upload_row()]).to_excel(source_path, index=False)

    monkeypatch.setattr(stats_module, "DOWNLOAD_FOLDER", str(download_dir))
    monkeypatch.setattr(stats_module, "ARCHIVE_DIR_1", str(archive_dir))
    monkeypatch.setattr(stats_module, "READY_DIR", str(download_dir / "Import_Ready"))
    monkeypatch.setattr(
        stats_module, "IMPORT_METADATA_FILE_PATH", str(download_dir / "stats_import_metadata.json")
    )

    success, message, _ = stats_module.process_excel_file(str(source_path))

    assert success, message
    manifest = stats_module._load_import_metadata()
    with open(
        Path(stats_module.READY_DIR) / manifest["completed_filename"],
        newline="",
        encoding="utf-8-sig",
    ) as handle:
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
    monkeypatch.setattr(stats_module, "READY_DIR", str(download_dir / "Import_Ready"))
    monkeypatch.setattr(
        stats_module, "IMPORT_METADATA_FILE_PATH", str(download_dir / "stats_import_metadata.json")
    )

    success, message, _ = stats_module.process_excel_file(str(source_path))

    assert success, message
    manifest = stats_module._load_import_metadata()
    with open(
        Path(stats_module.READY_DIR) / manifest["completed_filename"],
        newline="",
        encoding="utf-8-sig",
    ) as handle:
        rows = list(csv.DictReader(handle))

    assert "Conduct Score" not in rows[0]
    assert float(rows[0]["Credit"]) == pytest.approx(91.25)


def test_process_excel_file_preserves_unicode_names_in_csv(tmp_path, monkeypatch):
    source_path = tmp_path / "unicode.xlsx"
    download_dir = tmp_path / "downloads"
    archive_dir = download_dir / "archive"
    download_dir.mkdir()

    pd.DataFrame(
        [
            _full_upload_row(
                **{
                    "Governor ID": 123,
                    "Name": "義Vìper義",
                    "Alliance": "K98한",
                    "Civilization": "한국",
                    "Credit": 100,
                }
            )
        ]
    ).to_excel(source_path, index=False)

    monkeypatch.setattr(stats_module, "DOWNLOAD_FOLDER", str(download_dir))
    monkeypatch.setattr(stats_module, "ARCHIVE_DIR_1", str(archive_dir))
    monkeypatch.setattr(stats_module, "READY_DIR", str(download_dir / "Import_Ready"))
    monkeypatch.setattr(
        stats_module, "IMPORT_METADATA_FILE_PATH", str(download_dir / "stats_import_metadata.json")
    )

    success, message, _ = stats_module.process_excel_file(str(source_path))

    assert success, message
    manifest = stats_module._load_import_metadata()
    with open(
        Path(stats_module.READY_DIR) / manifest["completed_filename"],
        newline="",
        encoding="utf-8-sig",
    ) as handle:
        rows = list(csv.DictReader(handle))

    assert rows[0]["Name"] == "義Vìper義"
    assert rows[0]["Alliance"] == "K98한"
    assert rows[0]["Civilization"] == "한국"
