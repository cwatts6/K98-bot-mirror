from datetime import datetime

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

    result = mgr.execute_update_all2_with_log_management(cursor)

    assert result["success"] is True
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
