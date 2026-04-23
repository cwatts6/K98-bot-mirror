"""
Unit tests for gsheet_module.get_sheet_values and retry helpers.

These tests monkeypatch internal builders so no network or credentials are required.
"""

import types

from gspread.exceptions import SpreadsheetNotFound

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


# ---------------------------------------------------------------------------
# Tests for _is_retryable_gspread_details — SpreadsheetNotFound + 2xx logic
# ---------------------------------------------------------------------------

def test_is_retryable_spreadsheet_not_found_no_status_code():
    """SpreadsheetNotFound with no HTTP status code (None) is a Drive pagination miss → retryable."""
    details = {
        "repr": "SpreadsheetNotFound: <Response [200]>",
        "status_code": None,
        "status": None,
    }
    assert gm._is_retryable_gspread_details(details) is True


def test_is_retryable_spreadsheet_not_found_200():
    """SpreadsheetNotFound with HTTP 200 is a Drive pagination miss → retryable."""
    details = {
        "repr": "SpreadsheetNotFound: some message",
        "status_code": 200,
        "status": None,
    }
    assert gm._is_retryable_gspread_details(details) is True


def test_is_retryable_spreadsheet_not_found_404_not_retryable():
    """SpreadsheetNotFound with HTTP 404 means the sheet genuinely doesn't exist → not retryable."""
    details = {
        "repr": "SpreadsheetNotFound",
        "status_code": 404,
        "status": None,
    }
    assert gm._is_retryable_gspread_details(details) is False


def test_is_retryable_regular_200_not_retryable():
    """A non-SpreadsheetNotFound error with HTTP 200 is not retryable."""
    details = {
        "repr": "SomeOtherError: something went wrong",
        "status_code": 200,
        "status": None,
    }
    assert gm._is_retryable_gspread_details(details) is False


def test_is_retryable_server_error_500():
    """HTTP 500 errors are always retryable."""
    details = {"repr": "SomeError", "status_code": 500, "status": None}
    assert gm._is_retryable_gspread_details(details) is True


# ---------------------------------------------------------------------------
# Tests for _retry_gspread_call — SpreadsheetNotFound retried correctly
# ---------------------------------------------------------------------------

def test_retry_gspread_call_retries_spreadsheet_not_found_2xx(monkeypatch):
    """
    _retry_gspread_call must retry SpreadsheetNotFound when the response status
    is 2xx (Drive listing pagination miss), rather than giving up immediately.
    """
    call_count = {"n": 0}
    slept = {"total": 0.0}

    def fake_sleep(s):
        slept["total"] += s

    monkeypatch.setattr(gm.time, "sleep", fake_sleep)

    # Build a fake SpreadsheetNotFound with a 200 response
    exc = SpreadsheetNotFound()
    fake_resp = types.SimpleNamespace(status_code=200)
    exc.response = fake_resp

    def flaky_fn():
        call_count["n"] += 1
        if call_count["n"] < 3:
            raise exc
        return "ok"

    result = gm._retry_gspread_call(flaky_fn, retries=5)
    assert result == "ok"
    assert call_count["n"] == 3


def test_retry_gspread_call_retries_spreadsheet_not_found_no_response(monkeypatch):
    """
    _retry_gspread_call must retry SpreadsheetNotFound when there is no response
    attribute at all (status_code=None), which also signals a pagination miss.
    """
    call_count = {"n": 0}

    monkeypatch.setattr(gm.time, "sleep", lambda s: None)

    exc = SpreadsheetNotFound()
    # No response attribute set

    def flaky_fn():
        call_count["n"] += 1
        if call_count["n"] < 2:
            raise exc
        return "success"

    result = gm._retry_gspread_call(flaky_fn, retries=5)
    assert result == "success"
    assert call_count["n"] == 2
