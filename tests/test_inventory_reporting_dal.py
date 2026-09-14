from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from inventory.dal import inventory_reporting_dal


class _Cursor:
    description: ClassVar[list[tuple[str]]] = [
        ("ImportBatchID",),
        ("GovernorID",),
        ("ScanUtc",),
        ("ResourceType",),
        ("FromItemsValue",),
        ("TotalResourcesValue",),
    ]

    def __init__(self) -> None:
        self.calls = []

    def execute(self, sql, params):
        self.calls.append((sql, tuple(params)))

    def fetchall(self):
        scan = datetime(2026, 7, 14, tzinfo=UTC)
        return [(1, 111, scan, "food", 10, 100)]


class _Connection:
    def __init__(self) -> None:
        self.cursor_instance = _Cursor()
        self.closed = False

    def cursor(self):
        return self.cursor_instance

    def close(self):
        self.closed = True


def test_latest_resource_bulk_read_is_set_based_and_approved(monkeypatch) -> None:
    connection = _Connection()
    monkeypatch.setattr(inventory_reporting_dal, "_get_conn", lambda: connection)

    rows = inventory_reporting_dal.fetch_latest_resource_rows_bulk((111, 222, 111))

    assert rows[0]["GovernorID"] == 111
    assert len(connection.cursor_instance.calls) == 1
    sql, params = connection.cursor_instance.calls[0]
    assert params == (111, 222)
    assert "PARTITION BY b.GovernorID" in sql
    assert "b.Status = N'approved'" in sql
    assert "b.ImportType = N'resources'" in sql
    assert connection.closed is True
