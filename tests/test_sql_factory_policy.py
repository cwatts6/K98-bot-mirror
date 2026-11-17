"""Connection retries retain the identity selected before the first attempt."""

import asyncio
import builtins
from types import SimpleNamespace
from unittest.mock import Mock

import pyodbc
import pytest
import tenacity

import constants
import file_utils
import honor_importer
import prekvk_importer
import proc_config_import
from services import legacy_export_snapshot_service as legacy
from stats import profile_cache_repository


@pytest.fixture
def inert_connections(monkeypatch):
    # Only synthetic factories are reachable; never enable the integration flag.
    old = Mock(return_value=object())
    dedicated = Mock(return_value=object())
    monkeypatch.setattr(constants, "_conn", old)
    monkeypatch.setattr(file_utils, "_conn", old)
    monkeypatch.setattr(proc_config_import, "_conn_import", old)
    monkeypatch.setattr(file_utils, "_is_pytest_unit_mode", lambda: False)
    monkeypatch.setattr(file_utils, "emit_telemetry_event", Mock())
    monkeypatch.setattr(file_utils.time, "sleep", Mock())
    monkeypatch.setattr(tenacity.wait_fixed, "__call__", lambda *args: 0)
    active = [True]
    monkeypatch.setattr(legacy, "has_runtime_context", lambda: active[0])
    monkeypatch.setattr(
        legacy, "require_runtime", lambda: SimpleNamespace(dal=SimpleNamespace(connect=dedicated))
    )
    return old, dedicated, active


@pytest.mark.parametrize("initial_active", [False, True])
@pytest.mark.parametrize("import_config", [False, True])
def test_retry_retains_selected_factory_after_context_changes(
    inert_connections, initial_active, import_config
):
    old, dedicated, active = inert_connections
    active[0] = initial_active
    selected, other = (dedicated, old) if initial_active else (old, dedicated)
    connected = object()

    def attempt():
        active[0] = not initial_active
        if selected.call_count == 1:
            raise pyodbc.OperationalError("08001", "synthetic refused connection")
        return connected

    selected.side_effect = attempt
    result = (
        proc_config_import._get_import_connection_with_retry()
        if import_config
        else file_utils.get_conn_with_retries(retries=2, backoff_base=0)
    )
    assert result is connected
    assert selected.call_count == 2
    other.assert_not_called()


def test_explicit_operational_connection_keeps_legacy_factory(inert_connections):
    old, dedicated, _ = inert_connections
    assert file_utils.get_conn_with_retries(operational=True) is old.return_value
    old.assert_called_once_with()
    dedicated.assert_not_called()


@pytest.mark.parametrize("import_config", [False, True])
def test_selection_failure_cannot_trigger_connection_retry(
    inert_connections, monkeypatch, import_config
):
    old, dedicated, _ = inert_connections
    error = pyodbc.OperationalError("08001", "runtime selection unavailable")
    select = Mock(side_effect=error)
    monkeypatch.setattr(legacy, "require_runtime", select)
    with pytest.raises(pyodbc.OperationalError) as caught:
        if import_config:
            proc_config_import._get_import_connection_with_retry()
        else:
            file_utils.get_conn_with_retries()
    assert caught.value is error
    select.assert_called_once_with()
    dedicated.assert_not_called()
    old.assert_not_called()


@pytest.mark.parametrize("import_config,attempts", [(False, 3), (True, 5)])
def test_retry_exhaustion_preserves_original_error_and_factory(
    inert_connections, import_config, attempts
):
    old, dedicated, _ = inert_connections
    error = pyodbc.OperationalError("08001", "synthetic refused connection")
    dedicated.side_effect = error
    with pytest.raises(pyodbc.OperationalError) as caught:
        if import_config:
            proc_config_import._get_import_connection_with_retry()
        else:
            file_utils.get_conn_with_retries(retries=attempts, backoff_base=0)
    assert caught.value is error
    assert dedicated.call_count == attempts
    old.assert_not_called()


@pytest.mark.parametrize("import_config", [False, True])
@pytest.mark.parametrize("error", [ValueError("refused"), asyncio.CancelledError()])
def test_nontransient_failure_or_cancellation_is_not_retried(
    inert_connections, import_config, error
):
    old, dedicated, _ = inert_connections
    dedicated.side_effect = error
    with pytest.raises(type(error)) as caught:
        if import_config:
            proc_config_import._get_import_connection_with_retry()
        else:
            file_utils.get_conn_with_retries()
    assert caught.value is error
    dedicated.assert_called_once_with()
    old.assert_not_called()


@pytest.mark.parametrize(
    "entry", [profile_cache_repository._connect, prekvk_importer._conn, honor_importer._conn]
)
def test_adapter_preserves_selected_helper_error_without_fallback(monkeypatch, entry):
    error = RuntimeError("selected connection refused")
    old = Mock(return_value=object())
    helper = Mock(side_effect=error)
    monkeypatch.setattr(constants, "_conn", old)
    # The old profile implementation captured this import at module load.
    monkeypatch.setattr(profile_cache_repository, "_conn", old, raising=False)
    monkeypatch.setattr(file_utils, "get_conn_with_retries", helper)
    with pytest.raises(RuntimeError) as caught:
        entry()
    assert caught.value is error
    helper.assert_called_once_with()
    old.assert_not_called()


@pytest.mark.parametrize(
    "entry", [profile_cache_repository._connect, prekvk_importer._conn, honor_importer._conn]
)
def test_missing_connection_helper_fails_closed(monkeypatch, entry):
    original_import = builtins.__import__
    error = ImportError("connection policy unavailable")
    old = Mock(return_value=object())

    def import_module(name, *args, **kwargs):
        if name == "file_utils":
            raise error
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(constants, "_conn", old)
    monkeypatch.setattr(profile_cache_repository, "_conn", old, raising=False)
    monkeypatch.setattr(builtins, "__import__", import_module)
    with pytest.raises(ImportError) as caught:
        entry()
    assert caught.value is error
    old.assert_not_called()
