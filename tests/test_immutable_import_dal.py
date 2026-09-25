from __future__ import annotations

import pytest

from stats.dal.immutable_import_dal import fetch_immutable_import_outcome

COMPLETED = "stats_0123456789abcdef0123456789abcdef.ready.csv"


class _Cursor:
    def __init__(self, row):
        self.row = row
        self.executed = None

    def execute(self, sql, *params):
        self.executed = (sql, params)

    def fetchone(self):
        return self.row


def test_fetch_immutable_import_outcome_maps_terminal_receipt() -> None:
    cursor = _Cursor((COMPLETED, "archived", "ABCD", 1021, "archived"))

    outcome = fetch_immutable_import_outcome(cursor, COMPLETED)

    assert outcome is not None
    assert outcome.is_terminal is True
    assert outcome.is_duplicate is False
    assert outcome.scan_order == 1021
    assert cursor.executed is not None
    sql, params = cursor.executed
    assert "WHERE claim.CompletedFileName = ?" in sql
    assert params == (COMPLETED,)


def test_duplicate_archived_is_terminal_without_allocating_scan() -> None:
    cursor = _Cursor((COMPLETED, "duplicate_archived", "ABCD", 1020, "archived"))

    outcome = fetch_immutable_import_outcome(cursor, COMPLETED)

    assert outcome is not None
    assert outcome.is_terminal is True
    assert outcome.is_duplicate is True


def test_nonterminal_claim_remains_recoverable() -> None:
    cursor = _Cursor((COMPLETED, "claimed", "ABCD", None, None))

    outcome = fetch_immutable_import_outcome(cursor, COMPLETED)

    assert outcome is not None
    assert outcome.is_terminal is False


def test_invalid_completed_filename_is_rejected_before_sql() -> None:
    cursor = _Cursor(None)

    with pytest.raises(ValueError):
        fetch_immutable_import_outcome(cursor, "stats.csv")

    assert cursor.executed is None
