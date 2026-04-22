"""
Unit tests for gsheet_module.get_sheet_values.

These tests monkeypatch internal builders so no network or credentials are required.
"""

import types

import gsheet_module as gm


def test_get_sheet_values_success(monkeypatch):
    """Should return the rows list when the Sheets client returns values."""

    class FakeReq:
        def __init__(self, payload):
            self._payload = payload

        def execute(self, num_retries=0):
            return self._payload

    class FakeValues:
        def get(self, **kwargs):
            return FakeReq({"values": [["a", "b"], ["c", "d"]]})

    class FakeSheetsService:
        def spreadsheets(self):
            return types.SimpleNamespace(values=lambda: FakeValues())

    # monkeypatch the builder used by get_sheet_values
    monkeypatch.setattr(
        gm, "_build_sheets_with_timeout", lambda creds, timeout=None: FakeSheetsService()
    )

    rows = gm.get_sheet_values("FAKE_ID", "Sheet1!A1:B2", timeout=5)
    assert isinstance(rows, list)
    assert rows == [["a", "b"], ["c", "d"]]


def test_get_sheet_values_empty_range(monkeypatch):
    """Should return an empty list when the sheet range contains no values."""

    class FakeReq:
        def execute(self, num_retries=0):
            return {"values": []}

    class FakeValues:
        def get(self, **kwargs):
            return FakeReq()

    class FakeSheetsService:
        def spreadsheets(self):
            return types.SimpleNamespace(values=lambda: FakeValues())

    monkeypatch.setattr(
        gm, "_build_sheets_with_timeout", lambda creds, timeout=None: FakeSheetsService()
    )

    rows = gm.get_sheet_values("FAKE_ID", "Sheet1!A1:A", timeout=2)
    assert isinstance(rows, list)
    assert rows == []


def test_get_sheet_values_client_error_records_and_returns_none(monkeypatch):
    """
    If the sheets builder raises (e.g., missing credentials) or execute raises,
    get_sheet_values should return None and call _record_sheets_error.
    """
    called = {}

    def fake_record(kind, exc):
        called["called"] = (kind, exc)

    # Simulate builder raising
    def raise_builder(creds, timeout=None):
        raise RuntimeError("no client")

    monkeypatch.setattr(gm, "_build_sheets_with_timeout", raise_builder)
    monkeypatch.setattr(gm, "_record_sheets_error", fake_record)

    res = gm.get_sheet_values("ID", "RANGE")
    assert res is None
    assert "called" in called
    assert called["called"][0] in (
        "fetch_values",
        "credentials_unavailable",
        "credentials_load_failed",
        "credentials_missing",
    )
