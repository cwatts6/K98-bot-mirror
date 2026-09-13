from __future__ import annotations

import logging
import sys

import pytest


def test_caplog_still_captures_expected_negative_path_logs(caplog: pytest.LogCaptureFixture):
    logger = logging.getLogger("tests.expected_negative_path")

    with caplog.at_level(logging.ERROR, logger=logger.name):
        logger.error("expected negative path")

    assert any(record.message == "expected negative path" for record in caplog.records)


def test_pytest_logging_mode_uses_null_listener(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("K98_TEST_MODE", "1")
    import logging_setup

    handlers = logging_setup._build_listener_handlers()

    assert len(handlers) == 1
    assert isinstance(handlers[0], logging.NullHandler)
    assert logging_setup.should_redirect_stdio_to_logging() is False
    assert not isinstance(sys.stdout, logging_setup.StreamToLogger)
    assert not isinstance(sys.stderr, logging_setup.StreamToLogger)


def test_production_logging_mode_builds_file_handlers(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setenv("K98_TEST_MODE", "1")
    import logging_setup

    monkeypatch.setattr(logging_setup, "ERROR_LOG_PATH", str(tmp_path / "error_log.txt"))
    monkeypatch.setattr(logging_setup, "FULL_LOG_PATH", str(tmp_path / "log.txt"))
    monkeypatch.setattr(logging_setup, "CRASH_LOG_PATH", str(tmp_path / "crash.log"))
    monkeypatch.setattr(logging_setup, "TELEMETRY_LOG_PATH", str(tmp_path / "telemetry_log.jsonl"))

    monkeypatch.delenv("K98_TEST_MODE", raising=False)
    monkeypatch.delenv("PYTEST_RUNNING", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    handlers = logging_setup._build_listener_handlers(max_bytes=1024, backup_count=1)

    try:
        assert logging_setup.should_redirect_stdio_to_logging() is True
        assert len(handlers) == 4
        assert all(isinstance(handler, logging.FileHandler) for handler in handlers)
    finally:
        for handler in handlers:
            handler.close()


def test_db_retry_guard_fails_fast_in_unit_tests(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("K98_TEST_MODE", "1")
    monkeypatch.delenv("RUN_DB_TESTS", raising=False)
    import file_utils

    with pytest.raises(
        file_utils.UnitTestLiveDbAccessError, match="Unit test attempted live DB access"
    ):
        file_utils.get_conn_with_retries()


def test_db_retry_guard_allows_explicit_integration_mode(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("K98_TEST_MODE", "1")
    monkeypatch.setenv("RUN_DB_TESTS", "1")
    import file_utils

    class Sentinel(Exception):
        pass

    monkeypatch.setattr(file_utils, "_conn", lambda: (_ for _ in ()).throw(Sentinel("boom")))

    with pytest.raises(Sentinel):
        file_utils.get_conn_with_retries()
