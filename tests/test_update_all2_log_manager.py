from datetime import datetime
from unittest.mock import Mock

import pytest

import update_all2_log_manager as mgr


class _FakeCursor:
    def __init__(self, result_sets):
        self.result_sets = list(result_sets)
        self.index = 0
        self.executed = []

    @property
    def description(self):
        if self.index >= len(self.result_sets):
            return None
        columns, _rows = self.result_sets[self.index]
        if columns is None:
            return None
        return [(column,) for column in columns]

    def execute(self, sql, *params):
        self.executed.append((sql, params))

    def fetchall(self):
        if self.index >= len(self.result_sets):
            return []
        _columns, rows = self.result_sets[self.index]
        return rows

    def nextset(self):
        self.index += 1
        return self.index < len(self.result_sets)


def test_execute_update_all2_parses_internal_phase_result_set(monkeypatch):
    phase_started = datetime(2026, 7, 9, 12, 0, 0)
    phase_completed = datetime(2026, 7, 9, 12, 0, 1)
    second_phase_started = datetime(2026, 7, 9, 12, 0, 2)
    second_phase_completed = datetime(2026, 7, 9, 12, 0, 3)
    cursor = _FakeCursor(
        [
            (
                ["PhaseName", "PhaseStatus", "StartedAtUtc", "CompletedAtUtc", "DurationMs"],
                [
                    (
                        "update_all2_create_averages",
                        "completed",
                        phase_started,
                        phase_completed,
                        1000,
                    )
                ],
            ),
            (
                ["PhaseName", "PhaseStatus", "StartedAtUtc", "CompletedAtUtc", "DurationMs"],
                [
                    (
                        "update_all2_rebuild_excel_dashboard",
                        "completed",
                        second_phase_started,
                        second_phase_completed,
                        1000,
                    )
                ],
            ),
            (
                [
                    "RowsInsertedKS5",
                    "RowsInsertedKS4",
                    "DurationSeconds",
                    "PhaseBDurationMS",
                    "LogUsedPctBefore",
                    "LogUsedPctAfter",
                    "LogBackupTriggered",
                    "Status",
                ],
                [(10, 10, 5, 3000, 12.5, 13.0, False, "SUCCESS")],
            ),
        ]
    )

    monkeypatch.setattr(mgr, "get_log_space_usage", lambda _cursor: None)
    monkeypatch.setattr(
        mgr,
        "process_log_backup_triggers",
        lambda _cursor, max_triggers=5: {
            "triggers_found": 0,
            "triggers_processed": 0,
            "backups_triggered": 0,
            "errors": [],
        },
    )

    completed_filename = "stats_0123456789abcdef0123456789abcdef.ready.csv"
    result = mgr.execute_update_all2_with_log_management(
        cursor,
        completed_filename=completed_filename,
    )

    assert result["success"] is True
    assert cursor.executed[0] == (
        "EXEC dbo.UPDATE_ALL2 @param1 = ?, @param2 = ?, @CompletedFileName = ?",
        (None, None, completed_filename),
    )
    assert result["sp_result"]["status"] == "SUCCESS"
    assert result["phase_results"] == [
        {
            "phase_name": "update_all2_create_averages",
            "phase_status": "completed",
            "started_at_utc": phase_started,
            "completed_at_utc": phase_completed,
            "duration_ms": 1000,
            "rows_in": None,
            "rows_out": None,
            "details_json": None,
            "error_type": None,
            "error_text": None,
        },
        {
            "phase_name": "update_all2_rebuild_excel_dashboard",
            "phase_status": "completed",
            "started_at_utc": second_phase_started,
            "completed_at_utc": second_phase_completed,
            "duration_ms": 1000,
            "rows_in": None,
            "rows_out": None,
            "details_json": None,
            "error_type": None,
            "error_text": None,
        },
    ]


def test_execute_update_all2_rejects_noncanonical_completed_filename(monkeypatch):
    cursor = _FakeCursor([])
    monkeypatch.setattr(mgr, "get_log_space_usage", lambda _cursor: None)

    with pytest.raises(ValueError, match="canonical immutable completed filename"):
        mgr.execute_update_all2_with_log_management(
            cursor,
            completed_filename="stats.csv",
        )
    assert cursor.executed == []


SUMMARY = (
    [
        "RowsInsertedKS5",
        "RowsInsertedKS4",
        "DurationSeconds",
        "PhaseBDurationMS",
        "LogUsedPctBefore",
        "LogUsedPctAfter",
        "LogBackupTriggered",
        "Status",
    ],
    [(415, 415, 17, 1000, 1, 2, False, "SUCCESS")],
)
PHASE_A = (["a", "b", "c", "d", "e", "ArchivedFilePath"], [(1, 415, 415, 0, 415, "archive")])


@pytest.fixture
def isolated_wrapper(monkeypatch):
    usage = Mock(return_value=None)
    triggers = Mock(
        return_value={
            "triggers_found": 0,
            "triggers_processed": 0,
            "backups_triggered": 0,
            "errors": [],
        }
    )
    telemetry = Mock()
    monkeypatch.setattr(mgr, "get_log_space_usage", usage)
    monkeypatch.setattr(mgr, "process_log_backup_triggers", triggers)
    monkeypatch.setattr(mgr, "_safe_emit_telemetry", telemetry)
    return usage, triggers, telemetry


@pytest.mark.parametrize("method", ["fetchall", "nextset"])
def test_driver_error_is_preserved_and_never_reported_as_success(isolated_wrapper, method, caplog):
    import pyodbc

    cursor = _FakeCursor([PHASE_A])
    error = pyodbc.ProgrammingError("42000", "Synthetic reporting refusal (51961)")
    setattr(cursor, method, Mock(side_effect=error))
    with pytest.raises(pyodbc.ProgrammingError) as caught:
        mgr.execute_update_all2_with_log_management(
            cursor, completed_filename="stats_0123456789abcdef0123456789abcdef.ready.csv"
        )
    assert caught.value is error
    usage, triggers, telemetry = isolated_wrapper
    assert usage.call_count == 1
    triggers.assert_not_called()
    assert telemetry.call_args.args[0]["status"] == "failed"
    assert "completed successfully" not in caplog.text


def test_rowcount_only_results_are_skipped_without_fetching(isolated_wrapper):
    cursor = _FakeCursor([(None, []), PHASE_A, (None, []), SUMMARY])
    fetch = cursor.fetchall

    def checked_fetch():
        assert cursor.description is not None
        return fetch()

    cursor.fetchall = checked_fetch
    result = mgr.execute_update_all2_with_log_management(
        cursor, completed_filename="stats_0123456789abcdef0123456789abcdef.ready.csv"
    )
    assert result["success"]
    assert result["sp_result"]["rows_inserted_ks4"] == 415


@pytest.mark.parametrize("sets", [[], [PHASE_A], [(["PhaseName"] * 10, [tuple(range(10))])]])
def test_incomplete_stream_never_becomes_success(isolated_wrapper, sets):
    with pytest.raises(RuntimeError, match="final reporting success summary"):
        mgr.execute_update_all2_with_log_management(
            _FakeCursor(sets), completed_filename="stats_0123456789abcdef0123456789abcdef.ready.csv"
        )
    isolated_wrapper[1].assert_not_called()
