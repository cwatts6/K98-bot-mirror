"""Nested cleanup uncertainty cannot return a connection to its driver's pool."""

from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from core import sql_connection_custody as custody
from services.import_capture_recovery_dal import ImportCaptureRecoveryDAL, capture_transaction
from services.player_report_sql import player_connection, player_report_cursor
from tests.test_legacy_export_snapshot import producer_runtime


@pytest.mark.parametrize("wrapped", [False, True])
def test_retention_matches_only_the_exact_connection(wrapped):
    connection, other = Mock(), Mock()
    held = SimpleNamespace(connection=connection, cursor=Mock()) if wrapped else connection
    error = OSError("cleanup")
    custody.retain_connection(held, effect="unknown", first_failure=error, cleanup_error=error)
    assert custody.connection_retained(connection)
    assert not custody.connection_retained(other)


@pytest.mark.parametrize("phase", ["cursor", "rollback"])
@pytest.mark.parametrize("failure_type", [OSError, KeyboardInterrupt])
def test_nested_player_cleanup_retains_handles_before_outer_close(monkeypatch, phase, failure_type):
    cn = Mock(timeout=15)
    first = failure_type("cleanup")
    monkeypatch.setattr("file_utils.get_conn_with_retries", lambda **_: cn)
    if phase == "cursor":
        cn.cursor.return_value.close.side_effect = first
    else:
        cn.rollback.side_effect = first
    with pytest.raises(BaseException) as caught:
        with player_connection(operation="guided_player_report"):
            with player_report_cursor(cn, requested=15):
                pass
    error = caught.value
    while error.__cause__ is not None:
        error = error.__cause__
    assert error is first
    cn.close.assert_not_called()
    if phase == "cursor":
        cn.rollback.assert_not_called()
    assert custody.connection_retained(cn)
    with pytest.raises(custody.SqlCleanupUnknown):
        custody.require_sql_admission()


@pytest.mark.parametrize("phase", ["session_cursor", "transaction_cursor", "rollback"])
def test_capture_inner_cleanup_fences_outer_session(monkeypatch, phase):
    cn = Mock()
    session, transaction = Mock(), Mock()
    cn.cursor.side_effect = [session, transaction]
    monkeypatch.setattr(
        "services.import_capture_recovery_dal.one", lambda _: {"LockResult": 0, "Mode": "NoLock"}
    )
    first = OSError("cleanup")
    if phase == "session_cursor":
        session.close.side_effect = first
    elif phase == "transaction_cursor":
        transaction.close.side_effect = first
    else:
        transaction.execute.side_effect = [None, first]
    dal = ImportCaptureRecoveryDAL(SimpleNamespace(connect=lambda: cn))
    with pytest.raises(custody.SqlCleanupUnknown):
        with dal.session(str(uuid4())):
            with capture_transaction(cn):
                if phase == "rollback":
                    raise ValueError("body")
    cn.close.assert_not_called()
    assert custody.connection_retained(cn)
    if phase != "session_cursor":
        session.close.assert_not_called()
        assert not any("sp_releaseapplock" in c.args[0] for c in session.execute.call_args_list)
        assert next(iter(custody._holds.values())).retained_connection.resource is session


@pytest.mark.parametrize("entry", [True, False])
def test_writer_guard_failure_does_not_return_connection_to_pool(tmp_path, entry):
    runtime, dal = producer_runtime(tmp_path)
    guard = Mock()
    dal.session.return_value = guard
    first = OSError("guard cleanup")
    # Mock does not supply context protocol methods unless assigned explicitly.
    guard.__enter__ = Mock()
    guard.__exit__ = Mock()
    if entry:

        def fail():
            custody.retain_connection(
                dal.connect.return_value, effect="unknown", first_failure=first, cleanup_error=first
            )
            raise first

        guard.__enter__.side_effect = fail
    else:
        guard.__exit__.side_effect = first
    with pytest.raises(OSError) as caught:
        owner = runtime.begin_writer("all_kvk")
        runtime._close_writer(owner)
    assert caught.value is first
    dal.connect.return_value.close.assert_not_called()
    assert custody.connection_retained(dal.connect.return_value)


def test_writer_honors_an_inner_diagnostic_hold(tmp_path):
    runtime, dal = producer_runtime(tmp_path)
    owner = runtime.begin_writer("all_kvk")
    error = OSError("cursor")
    custody.retain_connection(
        SimpleNamespace(connection=owner.connection, cursor=Mock()),
        effect="unknown",
        first_failure=error,
        cleanup_error=error,
    )
    with pytest.raises(custody.SqlCleanupUnknown):
        runtime._close_writer(owner)
    dal.connect.return_value.close.assert_not_called()
    assert custody.custody_snapshot()["unconfirmed"] == 1
    assert next(iter(custody._holds.values())).retained_connection.resource is owner


def test_attached_resource_survives_collection_without_changing_first_evidence():
    import gc
    import weakref

    class Resource:
        pass

    cn, cursor = Resource(), Resource()
    error = ValueError("first")
    custody.retain_connection(cn, effect="unknown", first_failure=error, cleanup_error=error)
    outcome = next(iter(custody._holds.values()))
    evidence = outcome.public()
    reference = weakref.ref(cursor)
    assert custody.retain_connection_resource(cn, cursor)
    del cursor
    gc.collect()
    assert reference() is not None
    assert outcome.public() == evidence
    assert custody.custody_snapshot()["unconfirmed"] == 1
    assert not custody.retain_connection_resource(Resource(), reference())


@pytest.mark.parametrize("phase", ["rollback", "close"])
def test_player_unknown_commit_remains_primary_when_outer_cleanup_fails(monkeypatch, phase):
    from kvk.dal.new_source_import_dal import UncertainCommit

    cn = Mock()
    first = UncertainCommit("commit outcome unknown")
    getattr(cn, phase).side_effect = OSError("cleanup")
    monkeypatch.setattr("file_utils.get_conn_with_retries", lambda **_: cn)
    with pytest.raises(UncertainCommit) as caught:
        with player_connection(operation="guided_player_report"):
            raise first
    assert caught.value is first
    assert custody.connection_retained(cn)


def test_player_inner_raw_connection_hold_retains_cursor_without_closing(monkeypatch):
    cn = Mock(timeout=15)
    first = OSError("rollback")
    monkeypatch.setattr("file_utils.get_conn_with_retries", lambda **_: cn)
    with pytest.raises(OSError) as caught:
        with player_connection(operation="guided_player_report"):
            with player_report_cursor(cn, requested=15) as (cursor, _):
                custody.retain_connection(
                    cn, effect="unknown", first_failure=first, cleanup_error=first
                )
                raise first
    assert caught.value is first
    cursor.close.assert_not_called()
    cn.rollback.assert_not_called()
    cn.close.assert_not_called()
    assert next(iter(custody._holds.values())).retained_connection.resource is cursor
